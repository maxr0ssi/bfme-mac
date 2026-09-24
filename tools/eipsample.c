/* eipsample - in-guest sampling profiler for a 32-bit game running under Wine.
 *
 * Why: macOS's `sample` only sees Rosetta-translated code at addresses above 4 GB, so
 * the game's own code and wined3d.dll (both 32-bit PE) are indistinguishable there.
 * From inside Wine, SuspendThread + GetThreadContext return the *guest* x86 registers,
 * so each sample's EIP maps to the real module and offset - the offsets open directly
 * in Ghidra (game.dat) or name a function we have source for (wined3d.dll).
 *
 * This is not a debugger attach (that kills the game): it only pauses one thread for
 * a few microseconds, reads EIP/ESP and the top of its stack, and resumes it.
 *
 *   i686-w64-mingw32-gcc -O2 -o build/eipsample.exe tools/eipsample.c
 *   WINE_BUILD=w10 . ./env.sh && wine build/eipsample.exe [seconds] [interval_ms] [exe]
 *   defaults: 20 s, 5 ms, lotrbfme2ep1.exe
 *
 * Library time (memcpy, heap, ntdll) is attributed to its caller by scanning the top of
 * the stack for the first return address inside a non-system module ("owner"). That is
 * a heuristic - a stale value can occasionally win - so leaf and owner are both reported.
 */
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXMODS 512
#define MAXSAMP 40000
#define STACKDW 96

typedef struct { char name[64]; DWORD base, size; int system; } Mod;
static Mod mods[MAXMODS];
static int nmods;

static const char *SYSTEM_DLLS[] = {
    "ntdll.dll", "kernel32.dll", "kernelbase.dll", "msvcrt.dll", "ucrtbase.dll",
    "win32u.dll", "user32.dll", "gdi32.dll", "advapi32.dll", "msvcr71.dll",
    "msvcr80.dll", "msvcp71.dll", "msvcp80.dll", "sechost.dll", "rpcrt4.dll", NULL
};

static int modof(DWORD a)
{
    for (int i = 0; i < nmods; i++)
        if (a >= mods[i].base && a - mods[i].base < mods[i].size) return i;
    return -1;
}

static DWORD s_eip[MAXSAMP], s_owner_addr[MAXSAMP];
static int s_leaf[MAXSAMP], s_owner[MAXSAMP];

static int cmp_dword(const void *a, const void *b)
{
    DWORD x = *(const DWORD *)a, y = *(const DWORD *)b;
    return x < y ? -1 : x > y;
}

typedef struct { DWORD key; int count; } Hit;
static int cmp_hit(const void *a, const void *b)
{ return ((const Hit *)b)->count - ((const Hit *)a)->count; }

/* Count equal keys in a sorted array into hits[], return number of distinct keys. */
static int tally(DWORD *keys, int n, Hit *hits)
{
    qsort(keys, n, sizeof *keys, cmp_dword);
    int h = 0;
    for (int i = 0; i < n; ) {
        int j = i;
        while (j < n && keys[j] == keys[i]) j++;
        hits[h].key = keys[i]; hits[h].count = j - i; h++;
        i = j;
    }
    qsort(hits, h, sizeof *hits, cmp_hit);
    return h;
}

static void print_addr(DWORD a)
{
    int m = modof(a);
    if (m < 0) printf("<unmapped>+%08lx", (unsigned long)a);
    else printf("%s+0x%lx", mods[m].name, (unsigned long)(a - mods[m].base));
}

static void module_histogram(const char *title, const int *idx, int n)
{
    static int count[MAXMODS + 1];
    memset(count, 0, sizeof count);
    for (int i = 0; i < n; i++) count[idx[i] < 0 ? MAXMODS : idx[i]]++;
    printf("\n== %s ==\n", title);
    for (;;) {
        int best = -1;
        for (int i = 0; i <= MAXMODS; i++)
            if (count[i] > 0 && (best < 0 || count[i] > count[best])) best = i;
        if (best < 0) break;
        printf("  %6.2f%%  %6d  %s\n", 100.0 * count[best] / n, count[best],
               best == MAXMODS ? "<unmapped>" : mods[best].name);
        count[best] = 0;
    }
}

int main(int argc, char **argv)
{
    int secs = argc > 1 ? atoi(argv[1]) : 20;
    int ms = argc > 2 ? atoi(argv[2]) : 5;
    const char *target = argc > 3 ? argv[3] : "lotrbfme2ep1.exe";

    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    PROCESSENTRY32 pe; pe.dwSize = sizeof pe;
    DWORD pid = 0;
    for (BOOL ok = Process32First(snap, &pe); ok; ok = Process32Next(snap, &pe))
        if (!_stricmp(pe.szExeFile, target)) { pid = pe.th32ProcessID; break; }
    CloseHandle(snap);
    if (!pid) { fprintf(stderr, "eipsample: %s is not running\n", target); return 1; }

    HANDLE proc = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (!proc) { fprintf(stderr, "eipsample: OpenProcess failed (%lu)\n", GetLastError()); return 1; }

    snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
    MODULEENTRY32 me; me.dwSize = sizeof me;
    for (BOOL ok = Module32First(snap, &me); ok && nmods < MAXMODS; ok = Module32Next(snap, &me)) {
        Mod *m = &mods[nmods++];
        strncpy(m->name, me.szModule, sizeof m->name - 1);
        m->base = (DWORD)(ULONG_PTR)me.modBaseAddr;
        m->size = me.modBaseSize;
        for (int k = 0; SYSTEM_DLLS[k]; k++)
            if (!_stricmp(m->name, SYSTEM_DLLS[k])) m->system = 1;
    }
    CloseHandle(snap);
    printf("target %s pid %lu, %d modules\n", target, (unsigned long)pid, nmods);

    /* Pick the busy thread. Under Wine on macOS, GetThreadTimes on another process's
     * threads returns zeros, so CPU time can't be used. Instead scout every thread for
     * 3 s at a low rate: a running thread's EIP moves between samples, a blocked one sits
     * at the same syscall return address every time. This works even if the busy
     * thread spends its time inside a system DLL such as memcpy. */
    DWORD tids[1024]; int ntid = 0;
    snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    THREADENTRY32 te; te.dwSize = sizeof te;
    for (BOOL ok = Thread32First(snap, &te); ok && ntid < 1024; ok = Thread32Next(snap, &te))
        if (te.th32OwnerProcessID == pid) tids[ntid++] = te.th32ThreadID;
    CloseHandle(snap);

    static HANDLE th[1024]; static DWORD last[1024]; static int moved[1024], seen[1024];
    for (int i = 0; i < ntid; i++)
        th[i] = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT, FALSE, tids[i]);
    DWORD scout_end = GetTickCount() + 3000;
    while (GetTickCount() < scout_end) {
        for (int i = 0; i < ntid; i++) {
            if (!th[i] || SuspendThread(th[i]) == (DWORD)-1) continue;
            CONTEXT ctx; memset(&ctx, 0, sizeof ctx);
            ctx.ContextFlags = CONTEXT_CONTROL;
            BOOL ok = GetThreadContext(th[i], &ctx);
            ResumeThread(th[i]);
            if (!ok) continue;
            if (seen[i] && ctx.Eip != last[i]) moved[i]++;
            last[i] = ctx.Eip; seen[i]++;
        }
        Sleep(20);
    }
    int busiest = -1;
    printf("\n== scout: samples where EIP moved, per thread (3 s) ==\n");
    for (int i = 0; i < ntid; i++) {
        if (seen[i] > 1 && moved[i] * 10 >= seen[i]) {
            printf("  tid %5lu  moved %3d / %3d  last at ", (unsigned long)tids[i], moved[i], seen[i]);
            print_addr(last[i]); printf("\n");
        }
        if (seen[i] > 1 && (busiest < 0 || moved[i] > moved[busiest])) busiest = i;
    }
    for (int i = 0; i < ntid; i++) if (th[i]) CloseHandle(th[i]);
    if (busiest < 0 || moved[busiest] == 0) { fprintf(stderr, "eipsample: no running thread found\n"); return 1; }

    HANDLE t = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT, FALSE, tids[busiest]);
    if (!t) { fprintf(stderr, "eipsample: OpenThread failed (%lu)\n", GetLastError()); return 1; }
    printf("sampling tid %lu for %d s every %d ms\n", (unsigned long)tids[busiest], secs, ms);

    int n = 0;
    DWORD end = GetTickCount() + (DWORD)secs * 1000;
    while (GetTickCount() < end && n < MAXSAMP) {
        if (SuspendThread(t) == (DWORD)-1) break;
        CONTEXT ctx; memset(&ctx, 0, sizeof ctx);
        ctx.ContextFlags = CONTEXT_CONTROL;
        BOOL ok = GetThreadContext(t, &ctx);
        DWORD stack[STACKDW]; SIZE_T got = 0;
        if (ok) ReadProcessMemory(proc, (LPCVOID)(ULONG_PTR)ctx.Esp, stack, sizeof stack, &got);
        ResumeThread(t);
        if (ok) {
            int leaf = modof(ctx.Eip);
            int owner = -1; DWORD oaddr = ctx.Eip;
            if (leaf >= 0 && !mods[leaf].system) owner = leaf;
            else {
                for (SIZE_T i = 0; i < got / 4; i++) {
                    int m = modof(stack[i]);
                    if (m >= 0 && !mods[m].system) { owner = m; oaddr = stack[i]; break; }
                }
            }
            s_eip[n] = ctx.Eip; s_leaf[n] = leaf; s_owner[n] = owner; s_owner_addr[n] = oaddr;
            n++;
        }
        Sleep(ms);
    }
    CloseHandle(t);
    printf("%d samples\n", n);
    if (!n) return 1;

    module_histogram("leaf module (where the instruction pointer was)", s_leaf, n);
    module_histogram("owner module (library time charged to its caller)", s_owner, n);

    static DWORD keys[MAXSAMP]; static Hit hits[MAXSAMP];
    int h;

    for (int i = 0; i < n; i++) keys[i] = s_eip[i] & ~0xFFu;
    h = tally(keys, n, hits);
    printf("\n== hottest 256-byte code regions (leaf) ==\n");
    for (int i = 0; i < h && i < 25; i++) {
        printf("  %6.2f%%  %6d  ", 100.0 * hits[i].count / n, hits[i].count);
        print_addr(hits[i].key); printf("\n");
    }

    for (int i = 0; i < n; i++) keys[i] = s_eip[i];
    h = tally(keys, n, hits);
    printf("\n== hottest exact instructions (leaf) ==\n");
    for (int i = 0; i < h && i < 15; i++) {
        printf("  %6.2f%%  %6d  ", 100.0 * hits[i].count / n, hits[i].count);
        print_addr(hits[i].key); printf("\n");
    }

    int m = 0;
    for (int i = 0; i < n; i++)
        if (s_leaf[i] < 0 || mods[s_leaf[i]].system) keys[m++] = s_owner_addr[i];
    if (m) {
        h = tally(keys, m, hits);
        printf("\n== call sites into system libraries (owner return addresses, %d samples) ==\n", m);
        for (int i = 0; i < h && i < 15; i++) {
            printf("  %6.2f%%  %6d  ", 100.0 * hits[i].count / n, hits[i].count);
            print_addr(hits[i].key); printf("\n");
        }
    }

    printf("\n== modules with samples ==\n");
    for (int i = 0; i < nmods; i++) {
        int c = 0;
        for (int j = 0; j < n; j++) if (s_leaf[j] == i || s_owner[j] == i) { c = 1; break; }
        if (c) printf("  %-24s base 0x%08lx size 0x%lx%s\n", mods[i].name,
                      (unsigned long)mods[i].base, (unsigned long)mods[i].size,
                      mods[i].system ? "  (system)" : "");
    }
    return 0;
}
