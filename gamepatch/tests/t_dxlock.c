/* t_dxlock: the game's own DirectX-lock functions (acquire 0x51eec0, try 0x51ef50, owns 0x51efa0,
 * release 0x5208d0), copied from the exe to their original addresses with their data and IAT
 * slots, run twice: A = original (Win32 mutex), B = after gp_patch_dxlock() rewrote the four call
 * sites exactly as in the game. The same scenario script runs in both and every observable result
 * (return values, the game's owner/count words, who holds the lock) is recorded; the transcripts
 * must be identical. The one known difference (a thread exiting while it holds the lock) is run
 * last and reported separately. Run it with and without WINEMSYNC=1.
 * usage: t_dxlock.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define OWNER (*(volatile DWORD *)0xdd34c8)
#define COUNT (*(volatile LONG *)0xdd34cc)
#define MUTEX (*(HANDLE *)0xdd1fd8)
#define GAMECS ((CRITICAL_SECTION *)0xdd1f80)
typedef void (*acquire_t)(void);
typedef char (*try_t)(DWORD ms);
typedef char (*release_t)(void);
typedef int (*owns_t)(void);
/* code runs at its original address + OFF (Wine maps sortdefault.nls over 0x400000 in a test
 * process); its rel32 calls move with it, its absolute data and IAT operands stay where they are */
static uint32_t OFF;
static acquire_t acquire; static try_t try_; static release_t release; static owns_t owns;

static char out[2][8192]; static int cfg;
static DWORD main_tid;
static CRITICAL_SECTION rec_cs;
static void rec(const char *fmt, ...)   /* threads record too; the scenarios order them by joins */
{
    char l[256]; va_list ap; va_start(ap, fmt); vsnprintf(l, sizeof l, fmt, ap); va_end(ap);
    EnterCriticalSection(&rec_cs);
    strcat(out[cfg], l); strcat(out[cfg], "\n");
    LeaveCriticalSection(&rec_cs);
}
static const char *who(DWORD t) { return t == 0 ? "none" : t == main_tid ? "main" : "other"; }
static void state(const char *tag) { rec("%s: count=%ld owner=%s", tag, COUNT, who(OWNER)); }

/* run fn(arg) on a new thread and wait for it */
typedef struct { void (*fn)(void *); void *arg; } job_t;
static DWORD WINAPI job_main(LPVOID p) { job_t *j = p; j->fn(j->arg); return 0; }
static HANDLE start(void (*fn)(void *), void *arg)
{
    job_t *j = malloc(sizeof *j); j->fn = fn; j->arg = arg;
    return CreateThread(NULL, 0, job_main, j, 0, NULL);
}
static void join(HANDLE h) { WaitForSingleObject(h, INFINITE); CloseHandle(h); }

static void t_try1(void *p) { char r = try_(1); rec("%s: try(1) = %d", (char *)p, r); if (r) rec("%s: release = %d", (char *)p, release()); }
static void t_try1_keep(void *p) { rec("%s: try(1) = %d", (char *)p, try_(1)); }
static void t_try300(void *p) { rec("%s: try(300) = %d", (char *)p, try_(300)); rec("%s: release = %d", (char *)p, release()); }
static void t_release(void *p) { rec("%s: release = %d", (char *)p, release()); state((char *)p); }
static void t_acquire_timeout(void *p)
{
    DWORD t0 = GetTickCount(); acquire(); DWORD el = GetTickCount() - t0;
    rec("%s: acquire returned after %s", (char *)p, el >= 250 ? ">=250 ms (timed out, runs unlocked)" : "<250 ms");
    rec("%s: count=%ld owner=%s", (char *)p, COUNT, OWNER == GetCurrentThreadId() ? "self" : who(OWNER));
    rec("%s: release = %d", (char *)p, release());
    rec("%s: count=%ld owner=%s", (char *)p, COUNT, OWNER == GetCurrentThreadId() ? "self" : who(OWNER));
}
static void t_acquire_exit(void *p) { acquire(); rec("%s: acquired, thread exits holding it", (char *)p); }

static volatile LONG inside, violations, done_iters;
static void t_stress(void *p)
{
    unsigned seed = (unsigned)(uintptr_t)p;
    for (int i = 0; i < 4000; i++) {
        seed = seed * 1103515245 + 12345;
        int use_try = (seed >> 16) % 4 == 0;
        if (use_try) { if (!try_(1)) continue; } else acquire();
        if (InterlockedIncrement(&inside) != 1) InterlockedIncrement(&violations);
        int depth = (seed >> 20) % 3;
        for (int k = 0; k < depth; k++) acquire();
        if (!owns()) InterlockedIncrement(&violations);
        for (int k = 0; k < depth; k++) release();
        InterlockedDecrement(&inside);
        release();
        InterlockedIncrement(&done_iters);
    }
}

static void script(void)
{
    char r;
    /* T1 recursion on one thread */
    acquire(); acquire(); acquire();
    rec("T1 owns=%d", owns()); state("T1 after 3 acquires");
    r = release(); rec("T1 release = %d", r); r = release(); rec("T1 release = %d", r);
    r = release(); rec("T1 release = %d", r); state("T1 after 3 releases"); rec("T1 owns=%d", owns());
    /* T2 mutual exclusion, 8 threads, nested, mixed with try(1) */
    inside = violations = done_iters = 0;
    HANDLE h[8];
    for (int i = 0; i < 8; i++) h[i] = start(t_stress, (void *)(uintptr_t)(i * 7919 + 1));
    for (int i = 0; i < 8; i++) join(h[i]);
    rec("T2 8 threads: exclusion violations=%ld, all iterations finished=%s", violations, done_iters > 0 ? "yes" : "no");
    state("T2 end");
    /* T3 try(1) while another thread holds it, then after release */
    acquire();
    join(start(t_try1, "T3 B"));
    release();
    join(start(t_try1, "T3 C"));
    state("T3 end");
    /* T4 try(300) waits for a release 50 ms later */
    acquire();
    HANDLE b = start(t_try300, "T4 B"); Sleep(50); r = release(); join(b); rec("T4 main release = %d", r);
    state("T4 end");
    /* T5 release by a thread that does not hold it */
    acquire();
    join(start(t_release, "T5 B (non-owner)"));
    join(start(t_try1_keep, "T5 C"));
    rec("T5 main release = %d", release()); state("T5 after main release");
    join(start(t_try1, "T5 D"));
    COUNT = 0; OWNER = 0;
    /* T6 release without acquire */
    rec("T6 release = %d", release()); state("T6"); COUNT = 0; OWNER = 0;
    /* T7 the timeout path of acquire (20 s in the game, 300 ms here) */
    static const uint8_t imm300[4] = {0x2c, 0x01, 0, 0}, imm20000[4] = {0x20, 0x4e, 0, 0};
    memcpy((void *)(0x51eec6 + OFF), imm300, 4);
    acquire();
    join(start(t_acquire_timeout, "T7 B"));
    rec("T7 main release = %d", release()); state("T7 after main release");
    join(start(t_try1, "T7 D"));
    memcpy((void *)(0x51eec6 + OFF), imm20000, 4);
    COUNT = 0; OWNER = 0;
    /* T9 before Init: no handle yet */
    HANDLE m = MUTEX; MUTEX = NULL;
    acquire(); state("T9 no handle, after acquire"); rec("T9 release = %d", release()); state("T9");
    MUTEX = m; COUNT = 0; OWNER = 0;
}

static void known_difference(void)
{
    join(start(t_acquire_exit, "T8 E"));
    rec("T8 main try(1) after the holder exited = %d", try_(1));
}

static void reset(void)
{
    memset((void *)0xdd1f80, 0, 0x60);
    InitializeCriticalSection(GAMECS);
    MUTEX = CreateMutexA(NULL, FALSE, NULL);
    COUNT = 0; OWNER = 0;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    main_tid = GetCurrentThreadId();
    InitializeCriticalSection(&rec_cs);
    if (orig_map_at(0xbd0000, 0x1000, 0) || orig_map_at(0xdc6000, 0x1000, 0) || orig_map_at(0xdd1000, 0x4000, 0))
        return 2;
    if (!(OFF = orig_reserve_image())) return 2;
    if (orig_map_at(0x51e000, 0x3000, OFF) || orig_map_at(0x525000, 0x1000, OFF) ||
        orig_map_at(0xa24000, 0x1000, OFF) || orig_map_at(0x438000, 0x1000, OFF))
        return 2;
    acquire = (acquire_t)(0x51eec0 + OFF); try_ = (try_t)(0x51ef50 + OFF);
    release = (release_t)(0x5208d0 + OFF); owns = (owns_t)(0x51efa0 + OFF);
    gp_va_offset = OFF;
    memset((void *)0xdd1000, 0, 0x4000);
    memcpy((void *)(0x4380f0 + OFF), "\x31\xc0\xc3", 3);    /* debug reporting off: xor eax,eax; ret */
    HMODULE k = GetModuleHandleA("kernel32.dll");
    *(void **)0xbd0200 = GetProcAddress(k, "EnterCriticalSection");
    *(void **)0xbd0204 = GetProcAddress(k, "LeaveCriticalSection");
    *(void **)0xbd0224 = GetProcAddress(k, "ReleaseMutex");
    *(void **)0xbd022c = GetProcAddress(k, "GetCurrentThreadId");
    *(void **)0xbd0234 = GetProcAddress(k, "WaitForSingleObject");
    char msync[8] = "";
    GetEnvironmentVariableA("WINEMSYNC", msync, sizeof msync);
    printf("WINEMSYNC=%s\n", msync[0] ? msync : "(unset)");

    char k8[2][512];
    for (cfg = 0; cfg < 2; cfg++) {
        reset();
        if (cfg == 1 && !gp_patch_dxlock()) { printf("gp_patch_dxlock refused the original bytes\n"); return 2; }
        uint64_t t0 = now_us();
        script();
        printf("config %s: scenario took %.2f s\n", cfg ? "B (patched)" : "A (original)", (now_us() - t0) / 1e6);
        /* the known difference last: afterwards the lock may be unusable */
        size_t mark = strlen(out[cfg]);
        known_difference();
        snprintf(k8[cfg], sizeof k8[cfg], "%s", out[cfg] + mark);
        out[cfg][mark] = 0;
    }
    int same = strcmp(out[0], out[1]) == 0;
    printf("---- transcript A (original) ----\n%s", out[0]);
    if (!same) printf("---- transcript B (patched) DIFFERS ----\n%s", out[1]);
    else printf("---- transcript B (patched): identical ----\n");
    printf("---- known difference (a thread exits holding the lock) ----\nA: %sB: %s", k8[0], k8[1]);
    printf("%s\n", same ? "PASS" : "FAIL");
    return !same;
}
