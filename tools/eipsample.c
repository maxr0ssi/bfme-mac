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
 *   WINE_BUILD=w10 . ./env.sh && wine build/eipsample.exe [seconds] [interval_ms] [exe] [thread]
 *   defaults: 20 s, 5 ms, lotrbfme2ep1.exe, scout
 *   thread: "scout" suspends every thread ~130 times over 3 s to find the busy one (it has
 *   crashed the game: don't use it on a game you care about); "main" samples the
 *   process's first thread (the game's main thread) and touches no other; a number is a thread id.
 *
 * Library time (memcpy, heap, ntdll) is attributed to its caller by scanning the top of
 * the stack for the first return address inside a non-system module ("owner"). That is
 * a heuristic - a stale value can occasionally win - so leaf and owner are both reported.
 *
 * Stack section (for inclusive / call-tree profiles): every sample also reads the stack from ESP up
 * to the thread's stack top (at most EIPSAMPLE_STACK_KB, default 64 KB) and keeps every dword that is
 * a plausible return address into the target exe's code section: it points just after a CALL
 * (E8 rel32 into the code, or FF /2 in any addressing form), checked against the code as mapped in
 * the process. Those are printed per sample ("R" lines) for tools/callstacks.py, which maps them to
 * functions, drops stale values that do not chain, and reports inclusive time and a call tree.
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

/* Stack return sites into the exe. */
#define MAXRET 160                    /* per sample */
#define RETPOOL (8 * 1024 * 1024)
static DWORD *r_pool;                 /* pairs: stack slot (dwords above ESP), address */
static int r_used, s_rfirst[MAXSAMP], s_rcount[MAXSAMP];
static DWORD s_depth[MAXSAMP];
static int exe_mod = -1;
static BYTE *code;                    /* copy of the exe's code section */
static DWORD code_lo, code_hi;        /* VA range of that section */
static DWORD stack_top, stack_max = 64 * 1024;

static int in_code(DWORD a) { return a >= code_lo && a < code_hi; }

/* Is a a return address: does it follow a CALL instruction? */
static int is_ret(DWORD a)
{
    if (a < code_lo + 7 || a >= code_hi) return 0;
    const BYTE *p = code + (a - code_lo);
    if (p[-5] == 0xE8) {
        DWORD t = a + *(const DWORD *)(p - 4);
        if (in_code(t)) return 1;
    }
    /* FF /2: modrm reg field 2; lengths 2 (reg / [reg]), 3 (disp8 or sib), 4 (sib+disp8),
     * 6 (disp32 or [abs32]), 7 (sib+disp32). */
    BYTE m;
    m = p[-1]; if (p[-2] == 0xFF && (m & 0x38) == 0x10 && ((m >> 6) == 3 || ((m >> 6) == 0 && (m & 7) != 4 && (m & 7) != 5))) return 1;
    m = p[-2]; if (p[-3] == 0xFF && (m & 0x38) == 0x10 && (((m >> 6) == 1 && (m & 7) != 4) || ((m >> 6) == 0 && (m & 7) == 4 && (p[-1] & 7) != 5))) return 1;
    m = p[-3]; if (p[-4] == 0xFF && (m & 0x38) == 0x10 && (m >> 6) == 1 && (m & 7) == 4) return 1;
    m = p[-5]; if (p[-6] == 0xFF && (m & 0x38) == 0x10 && (((m >> 6) == 2 && (m & 7) != 4) || ((m >> 6) == 0 && (m & 7) == 5))) return 1;
    m = p[-6]; if (p[-7] == 0xFF && (m & 0x38) == 0x10 && (((m >> 6) == 2 && (m & 7) == 4) || ((m >> 6) == 0 && (m & 7) == 4 && (p[-5] & 7) == 5))) return 1;
    return 0;
}

/* Copy the exe's first executable section out of the process (the in-memory code is what runs). */
static void load_code(HANDLE proc, const char *target)
{
    for (int i = 0; i < nmods; i++) if (!_stricmp(mods[i].name, target)) exe_mod = i;
    if (exe_mod < 0) return;
    DWORD base = mods[exe_mod].base; BYTE hdr[4096]; SIZE_T got = 0;
    if (!ReadProcessMemory(proc, (LPCVOID)(ULONG_PTR)base, hdr, sizeof hdr, &got) || got < sizeof hdr) return;
    IMAGE_NT_HEADERS32 *nt = (IMAGE_NT_HEADERS32 *)(hdr + ((IMAGE_DOS_HEADER *)hdr)->e_lfanew);
    IMAGE_SECTION_HEADER *sec = IMAGE_FIRST_SECTION(nt);
    for (int i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
        if (!(sec->Characteristics & IMAGE_SCN_MEM_EXECUTE)) continue;
        DWORD n = sec->Misc.VirtualSize;
        code = malloc(n);
        if (!code || !ReadProcessMemory(proc, (LPCVOID)(ULONG_PTR)(base + sec->VirtualAddress), code, n, &got) || got != n) {
            free(code); code = NULL; return;
        }
        code_lo = base + sec->VirtualAddress; code_hi = code_lo + n;
        r_pool = malloc(RETPOOL * sizeof *r_pool);
        if (!r_pool) { free(code); code = NULL; }
        return;
    }
}

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

static int sample_thread(HANDLE proc, DWORD tid, int secs, int ms);
static void stack_report(int n);

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
    const char *kb = getenv("EIPSAMPLE_STACK_KB");
    if (kb && atoi(kb) > 0) stack_max = (DWORD)atoi(kb) * 1024;
    load_code(proc, target);
    if (code) printf("stack scan: code 0x%08lx-0x%08lx, up to %lu KB of stack per sample\n",
                     (unsigned long)code_lo, (unsigned long)code_hi, (unsigned long)(stack_max / 1024));

    /* Pick the busy thread. Under Wine on macOS, GetThreadTimes on another process's
     * threads returns zeros, so CPU time can't be used. Instead scout every thread for
     * 3 s at a low rate: a running thread's EIP moves between samples, a blocked one sits
     * at the same syscall return address every time. This works even if the busy
     * thread spends its time inside a system DLL such as memcpy. */
    const char *pick = argc > 4 ? argv[4] : "scout";
    DWORD tids[1024]; int ntid = 0;
    snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    THREADENTRY32 te; te.dwSize = sizeof te;
    for (BOOL ok = Thread32First(snap, &te); ok && ntid < 1024; ok = Thread32Next(snap, &te))
        if (te.th32OwnerProcessID == pid) tids[ntid++] = te.th32ThreadID;
    CloseHandle(snap);

    if (strcmp(pick, "scout")) {
        DWORD want = !strcmp(pick, "main") ? (ntid ? tids[0] : 0) : (DWORD)strtoul(pick, NULL, 0);
        printf("thread %lu chosen without scouting (%s)\n", (unsigned long)want, pick);
        return sample_thread(proc, want, secs, ms);
    }
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

    return sample_thread(proc, tids[busiest], secs, ms);
}

static int sample_thread(HANDLE proc, DWORD tid, int secs, int ms)
{
    HANDLE t = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT, FALSE, tid);
    if (!t) { fprintf(stderr, "eipsample: OpenThread failed (%lu)\n", GetLastError()); return 1; }
    printf("sampling tid %lu for %d s every %d ms\n", (unsigned long)tid, secs, ms);

    int n = 0;
    LARGE_INTEGER qf, q0, q1; double susp_sum = 0, susp_max = 0;   /* how long the thread is held */
    QueryPerformanceFrequency(&qf);
    static DWORD deep[256 * 1024 / 4];
    if (stack_max > sizeof deep) stack_max = sizeof deep;
    DWORD end = GetTickCount() + (DWORD)secs * 1000;
    while (GetTickCount() < end && n < MAXSAMP) {
        QueryPerformanceCounter(&q0);
        if (SuspendThread(t) == (DWORD)-1) break;
        CONTEXT ctx; memset(&ctx, 0, sizeof ctx);
        ctx.ContextFlags = CONTEXT_CONTROL;
        BOOL ok = GetThreadContext(t, &ctx);
        DWORD stack[STACKDW]; SIZE_T got = 0, sgot = 0, want = 0;
        if (ok) ReadProcessMemory(proc, (LPCVOID)(ULONG_PTR)ctx.Esp, stack, sizeof stack, &got);
        if (ok && code) {
            if (!stack_top) {   /* end of the committed region holding ESP = the stack's top */
                MEMORY_BASIC_INFORMATION mbi;
                if (VirtualQueryEx(proc, (LPCVOID)(ULONG_PTR)ctx.Esp, &mbi, sizeof mbi))
                    stack_top = (DWORD)(ULONG_PTR)mbi.BaseAddress + (DWORD)mbi.RegionSize;
            }
            want = ctx.Esp < stack_top ? stack_top - ctx.Esp : 0;
            if (want > stack_max) want = stack_max;
            if (want && !ReadProcessMemory(proc, (LPCVOID)(ULONG_PTR)ctx.Esp, deep, want, &sgot)) sgot = 0;
        }
        ResumeThread(t);
        QueryPerformanceCounter(&q1);
        double us = (q1.QuadPart - q0.QuadPart) * 1e6 / qf.QuadPart;
        susp_sum += us; if (us > susp_max) susp_max = us;
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
            s_rfirst[n] = r_used; s_rcount[n] = 0; s_depth[n] = (DWORD)sgot;
            for (SIZE_T i = 0; i < sgot / 4 && s_rcount[n] < MAXRET && r_used + 2 <= RETPOOL; i++)
                if (is_ret(deep[i])) { r_pool[r_used++] = (DWORD)i; r_pool[r_used++] = deep[i]; s_rcount[n]++; }
            n++;
        }
        Sleep(ms);
    }
    CloseHandle(t);
    printf("%d samples; thread held suspended %.0f us mean, %.0f us max per sample\n",
           n, n ? susp_sum / n : 0.0, susp_max);
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
    if (code) stack_report(n);
    return 0;
}

/* Return sites present anywhere on the stack (a site counts once per sample), then the raw
 * per-sample lines for tools/callstacks.py:  R <eip> <stack bytes read> <slot>:<address> ...
 * (slot = dword index above ESP, nearest first). */
static void stack_report(int n)
{
    static DWORD keys[MAXSAMP * 8]; static Hit hits[MAXSAMP * 8];
    int m = 0; double depth = 0;
    for (int i = 0; i < n; i++) {
        depth += s_depth[i];
        DWORD *r = r_pool + s_rfirst[i];
        for (int j = 0; j < s_rcount[i] && m < MAXSAMP * 8; j++) {
            int dup = 0;
            for (int k = 0; k < j; k++) if (r[2 * k + 1] == r[2 * j + 1]) dup = 1;
            if (!dup) keys[m++] = r[2 * j + 1];
        }
    }
    printf("\n== stack scan: %d return sites kept, mean %.0f bytes of stack read per sample ==\n",
           r_used / 2, depth / n);
    int h = tally(keys, m, hits);
    printf("\n== return sites on the stack (share of samples containing the site; stale values included) ==\n");
    for (int i = 0; i < h && i < 40; i++) {
        printf("  %6.2f%%  %6d  ", 100.0 * hits[i].count / n, hits[i].count);
        print_addr(hits[i].key); printf("\n");
    }
    printf("\n== raw stacks (R eip bytes slot:ret...) ==\n");
    for (int i = 0; i < n; i++) {
        printf("R %08lx %lu", (unsigned long)s_eip[i], (unsigned long)s_depth[i]);
        DWORD *r = r_pool + s_rfirst[i];
        for (int j = 0; j < s_rcount[i]; j++)
            printf(" %lx:%lx", (unsigned long)r[2 * j], (unsigned long)r[2 * j + 1]);
        printf("\n");
    }
}
