/* memwatch - read-only address-space monitor for the game's 32-bit process under Wine.
 *
 * Why: the game has 2 GB of address space (4 GB with the large-address-aware flag), and a
 * 32-bit process runs out of memory when no free block is big enough for an allocation, usually
 * well before the total is used up (fragmentation). The art mod's texture budget is set against
 * how close real matches get. Every N seconds this walks the target's address space with
 * VirtualQueryEx and prints one CSV row: committed / reserved / free, the largest free block (the
 * out-of-memory predictor), the number of free blocks over 16 MB, and committed memory by type.
 *
 *   i686-w64-mingw32-gcc -O2 -Wl,--large-address-aware -o build/memwatch.exe tools/memwatch.c -lpsapi
 *   wine build/memwatch.exe [interval_s] [exe[,exe...]] [max_samples] [duty_pct]
 *   defaults: 2 s; game.dat,lotrbfme2ep1.exe,lotrbfme2.exe (the match with most threads); 0 = until
 *   the target exits; 2 %. scripts/memwatch.sh runs it beside the game and adds the macOS figures.
 *
 * Read-only: the process is opened with PROCESS_QUERY_INFORMATION | PROCESS_VM_READ; nothing is
 * written or suspended. But a query is not free for the target. In Wine a cross-process
 * VirtualQueryEx is a system APC that a thread of the target runs (dlls/ntdll/unix/virtual.c,
 * server/thread.c queue_apc), and on the w10 engine with msync it is always the first thread - the
 * game's main thread - interrupted with SIGUSR1 (the mechanism SuspendThread uses), ~50 us each,
 * measured 2026-09-27 with a busy dummy in a throwaway prefix (a thread in an alertable wait did not
 * take them). So the cost is kept down three ways: images are stepped over whole from the module
 * list (read with ReadProcessMemory, which the wineserver does with mach_vm_read, no APC); queries
 * go in bursts of BURST with a sleep between, so no frame loses more than a few ms; and the interval
 * stretches so the time spent in queries stays under duty_pct of wall time. queries and query_ms
 * record the cost of each sample; query_ms is roughly what the game's main thread lost.
 *
 * GetProcessMemoryInfo on another process is answered by the wineserver from /proc (Linux) or
 * procstat (BSD); on macOS its figures are 0. The script records the macOS side instead.
 */
#include <windows.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define GRAN   0x10000u                        /* allocation granularity: VirtualAlloc bases */
#define BIGBLK (16u << 20)
#define BURST  32                              /* queries between sleeps: ~1.6 ms of the target's time */
#define REST   15                              /* ms between bursts */
#define MAXMOD 1024

typedef struct {
    unsigned regions, queries, free16;
    double query_ms;
    ULONGLONG commit, reserve, freeb, largest, image, mapped, priv;
    DWORD largest_at;
} Walk;

static double mb(ULONGLONG b) { return (double)b / 1048576.0; }

/* Is name one of the comma-separated exe names in list (case-insensitive)? */
static int listed(const char *list, const char *name)
{
    size_t n = strlen(name);
    for (const char *p = list; *p; ) {
        const char *e = strchr(p, ',');
        size_t len = e ? (size_t)(e - p) : strlen(p);
        if (len == n && !_strnicmp(p, name, n)) return 1;
        if (!e) break;
        p = e + 1;
    }
    return 0;
}

/* The running process named in list with the most threads (the game, not a launcher stub). */
static DWORD find_target(const char *list, char *name, size_t namesz, DWORD *threads)
{
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    PROCESSENTRY32 pe = {sizeof(pe)};
    DWORD pid = 0, best = 0;
    if (snap == INVALID_HANDLE_VALUE) return 0;
    for (BOOL ok = Process32First(snap, &pe); ok; ok = Process32Next(snap, &pe))
        if (pe.th32ProcessID != GetCurrentProcessId() && listed(list, pe.szExeFile)
            && pe.cntThreads > best) {
            best = pe.cntThreads; pid = pe.th32ProcessID;
            snprintf(name, namesz, "%s", pe.szExeFile);
        }
    CloseHandle(snap);
    *threads = best;
    return pid;
}

/* Loaded images (base, SizeOfImage) from the loader list: an image is committed whole, so the walk
 * adds it in one step instead of one query per section. */
static DWORD mod_base[MAXMOD], mod_size[MAXMOD];
static int nmod;

/* Whether the target's exe has the large-address-aware flag (its header, read from its memory). */
static int target_laa(HANDLE proc)
{
    HMODULE mod; DWORD need; IMAGE_DOS_HEADER dos; IMAGE_NT_HEADERS32 nt; SIZE_T got;
    if (!EnumProcessModules(proc, &mod, sizeof(mod), &need)) return 0;
    if (!ReadProcessMemory(proc, mod, &dos, sizeof(dos), &got) || dos.e_magic != IMAGE_DOS_SIGNATURE) return 0;
    if (!ReadProcessMemory(proc, (BYTE *)mod + dos.e_lfanew, &nt, sizeof(nt), &got)) return 0;
    return nt.Signature == IMAGE_NT_SIGNATURE && (nt.FileHeader.Characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE);
}

static void load_modules(DWORD pid)
{
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
    MODULEENTRY32 me = {sizeof(me)};
    nmod = 0;
    if (snap == INVALID_HANDLE_VALUE) return;
    for (BOOL ok = Module32First(snap, &me); ok && nmod < MAXMOD; ok = Module32Next(snap, &me)) {
        mod_base[nmod] = (DWORD)(ULONG_PTR)me.modBaseAddr;
        mod_size[nmod++] = me.modBaseSize;
    }
    CloseHandle(snap);
}

static DWORD image_end(DWORD alloc_base)
{
    for (int i = 0; i < nmod; i++)
        if (mod_base[i] == alloc_base) return mod_base[i] + mod_size[i];
    return 0;
}

/* Walk [lo, hi). Returns 0, or -1 if the first query fails (process gone or no access). */
static int walk(HANDLE proc, DWORD lo, DWORD hi, Walk *w, int skip_images)
{
    MEMORY_BASIC_INFORMATION m;
    LARGE_INTEGER f, q0, q1;
    DWORD a = lo;
    memset(w, 0, sizeof(*w));
    QueryPerformanceFrequency(&f);
    while (a < hi) {
        if (w->queries && w->queries % BURST == 0) Sleep(REST);
        QueryPerformanceCounter(&q0);
        SIZE_T got = VirtualQueryEx(proc, (void *)(ULONG_PTR)a, &m, sizeof(m));
        QueryPerformanceCounter(&q1);
        w->queries++;
        w->query_ms += (q1.QuadPart - q0.QuadPart) * 1000.0 / f.QuadPart;
        if (got != sizeof(m)) return a == lo ? -1 : 0;
        DWORD base = (DWORD)(ULONG_PTR)m.BaseAddress;
        ULONGLONG end = (ULONGLONG)base + m.RegionSize;
        if (m.State == MEM_COMMIT && m.Type == MEM_IMAGE && skip_images) {
            DWORD e = image_end((DWORD)(ULONG_PTR)m.AllocationBase);
            if (e > end) end = e;
        }
        if (end > hi) end = hi;
        if (end <= a) break;                      /* no progress: stop rather than spin */
        ULONGLONG size = end - a;
        w->regions++;
        if (m.State == MEM_COMMIT) {
            w->commit += size;
            if (m.Type == MEM_IMAGE) w->image += size;
            else if (m.Type == MEM_MAPPED) w->mapped += size;
            else w->priv += size;
        } else if (m.State == MEM_RESERVE) {
            w->reserve += size;
        } else {
            w->freeb += size;
            /* what VirtualAlloc could actually get: the block from the next 64 KB boundary */
            ULONGLONG start = ((ULONGLONG)a + GRAN - 1) & ~(ULONGLONG)(GRAN - 1);
            ULONGLONG usable = end > start ? end - start : 0;
            if (usable > w->largest) { w->largest = usable; w->largest_at = (DWORD)start; }
            if (usable >= BIGBLK) w->free16++;
        }
        a = (DWORD)end;
        if (end >= hi) break;
    }
    return 0;
}

int main(int argc, char **argv)
{
    int interval = argc > 1 ? atoi(argv[1]) : 2;
    const char *list = argc > 2 && *argv[2] ? argv[2] : "game.dat,lotrbfme2ep1.exe,lotrbfme2.exe";
    int max = argc > 3 ? atoi(argv[3]) : 0;
    double duty = argc > 4 ? atof(argv[4]) : 2.0;
    int skip = !getenv("MEMWATCH_FULL");          /* MEMWATCH_FULL=1: query image sections too (checks) */
    char name[MAX_PATH] = "";
    DWORD threads, pid, t0, n = 0, code;
    SYSTEM_INFO si;
    HANDLE proc;

    if (interval < 1) interval = 1;
    if (duty <= 0) duty = 2.0;
    setvbuf(stdout, NULL, _IONBF, 0);
    if (!(pid = find_target(list, name, sizeof(name), &threads))) {
        fprintf(stderr, "memwatch: none of %s is running\n", list);
        return 1;
    }
    proc = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (!proc) {
        fprintf(stderr, "memwatch: OpenProcess(%lu) failed: %lu\n", pid, GetLastError());
        return 1;
    }
    /* A 32-bit caller sees the target up to its own limit: memwatch is built large-address aware
     * (4 GB), and the span is cut to the game's own limit, 2 GB unless its exe has the flag
     * (RotWK since 2026-09-27, docs/MEMORY-4GB.md). */
    GetSystemInfo(&si);
    DWORD lo = (DWORD)(ULONG_PTR)si.lpMinimumApplicationAddress;
    DWORD hi = (DWORD)(ULONG_PTR)si.lpMaximumApplicationAddress + 1;
    int laa = target_laa(proc);
    if (!laa && hi > 0x7fff0000u) hi = 0x7fff0000u;

    printf("# memwatch target=%s winpid=%lu threads=%lu interval=%d duty=%.1f%% images=%s laa=%s "
           "span=0x%08lx-0x%08lx (%.0f MB)\n", name, pid, threads, interval, duty,
           skip ? "whole" : "queried", laa ? "on" : "off", lo, hi, mb(hi - lo));
    printf("time,t_s,queries,query_ms,walk_ms,committed_mb,reserved_mb,free_mb,largest_free_mb,"
           "largest_free_at,free_blocks_16mb,image_mb,mapped_mb,private_mb,modules,"
           "pmi_private_mb,pmi_ws_mb,pmi_peak_ws_mb\n");
    t0 = GetTickCount();
    for (;;) {
        DWORD w0 = GetTickCount(), took;
        PROCESS_MEMORY_COUNTERS_EX pmc = {sizeof(pmc)};
        SYSTEMTIME st;
        Walk w;

        if (!GetExitCodeProcess(proc, &code) || code != STILL_ACTIVE) break;
        if (skip) load_modules(pid);
        if (walk(proc, lo, hi, &w, skip)) {
            if (GetExitCodeProcess(proc, &code) && code == STILL_ACTIVE)
                printf("# VirtualQueryEx failed: %lu\n", GetLastError());
            break;
        }
        took = GetTickCount() - w0;
        if (!GetProcessMemoryInfo(proc, (PROCESS_MEMORY_COUNTERS *)&pmc, sizeof(pmc)))
            memset(&pmc, 0, sizeof(pmc));
        GetLocalTime(&st);
        printf("%02u:%02u:%02u,%.1f,%u,%.1f,%lu,%.1f,%.1f,%.1f,%.1f,0x%08lx,%u,%.1f,%.1f,%.1f,%d,"
               "%.1f,%.1f,%.1f\n",
               st.wHour, st.wMinute, st.wSecond, (w0 - t0) / 1000.0, w.queries, w.query_ms, took,
               mb(w.commit), mb(w.reserve), mb(w.freeb), mb(w.largest), w.largest_at, w.free16,
               mb(w.image), mb(w.mapped), mb(w.priv), skip ? nmod : 0,
               mb(pmc.PrivateUsage), mb(pmc.WorkingSetSize), mb(pmc.PeakWorkingSetSize));
        if (max && ++n >= (DWORD)max) { CloseHandle(proc); return 0; }
        /* next sample after the interval, or later if that keeps query time under duty % */
        double want = interval * 1000.0, cap = w.query_ms * 100.0 / duty;
        if (cap > want) want = cap;
        DWORD spent = GetTickCount() - w0;
        if (spent < want) Sleep((DWORD)want - spent);
    }
    printf("# target exited\n");
    CloseHandle(proc);
    return 0;
}
