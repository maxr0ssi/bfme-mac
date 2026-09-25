/* R5 worker pool implementation. See parallel.h and parallel/DESIGN.md.
 * Build (mingw): i686-w64-mingw32-gcc -O2 -msse2 -mfpmath=sse -c parallel.c
 *
 * Single producer (the game's main thread) fans a job out to persistent workers.
 *  - Publication: job fields are written, then the claim word, then gen (release order).
 *  - Claims: one CAS word {gen:16 | next index:16}. A straggler that still holds an older gen
 *    fails the gen check and can never claim (or count down) a chunk of a newer job. This is the
 *    fix for the hang: resetting next/remaining while a late worker was still inside drain() let
 *    its decrement be overwritten, so remaining never reached 0.
 *  - Parking: arm-then-recheck with a per-worker auto-reset event. If the worker disarms too late
 *    (main already swapped arm to 0 and will SetEvent), it consumes that signal so no stale wake
 *    is left behind.
 *  - Idle budget: a worker spins (PAUSE) for par_cfg.idle_park_us after its last job, then parks,
 *    so workers stay hot through a frame's parallel sections and sleep between frames.
 * No __thread: TLS via __thread makes the exe fail to load under this Wine (WoW64), so per-thread
 * state is a Win32 TLS slot index into static arrays. */
#include "parallel.h"
#include <windows.h>
#include <string.h>
#include <stdlib.h>
#include <setjmp.h>
#include <xmmintrin.h>

par_config par_cfg = { 0, 0, 200, THREAD_PRIORITY_ABOVE_NORMAL };
static par_stats g_stats;

#define MAXW 32
#define MAXCHUNKS 4096
typedef struct { int begin, end; } chunk_t;

static struct {
    int            n;
    HANDLE         th[MAXW];
    HANDLE         ev[MAXW];
    volatile LONG  arm[MAXW];
    volatile LONG  gen;
    volatile LONG  quit;
    par_fn         fn;
    void          *ctx;
    int            nchunks;
    volatile LONG  claim;        /* (gen & 0xffff) << 16 | next chunk index */
    volatile LONG  remaining;
    HANDLE         alldone;
    uint16_t       x87cw;
    uint32_t       mxcsr;
    volatile LONG  in_par;
    volatile LONG  park_gen;     /* bumped by par_park_now(): spinning workers park at once */
    int            inited;
    double         qpc_per_us;
} P;

static chunk_t       s_chunks[MAXCHUNKS];
static volatile LONG s_fault[MAXCHUNKS];
static DWORD         g_tls = TLS_OUT_OF_INDEXES;  /* participant slot + 1 */
static jmp_buf       g_jb[MAXW + 1];              /* slot 0 = main, 1..n = workers */
static volatile int  g_in_job[MAXW + 1];
static PVOID         g_veh;

static int slot_of_thread(void) { return (int)(INT_PTR)TlsGetValue(g_tls) - 1; }
static inline int64_t qpc(void) { LARGE_INTEGER t; QueryPerformanceCounter(&t); return t.QuadPart; }

/* ---- FPU state propagation ---------------------------------------------------------------- */
static void fpu_capture(void)
{
    uint16_t cw;
    __asm__ __volatile__("fnstcw %0" : "=m"(cw));
    P.x87cw = cw;
    P.mxcsr = _mm_getcsr();
}
static inline void fpu_load(void)
{
    __asm__ __volatile__("fldcw %0" : : "m"(P.x87cw));
    _mm_setcsr(P.mxcsr);
}

/* ---- fault guard: VEH + setjmp (mingw GCC has no __try) ----------------------------------- */
static LONG CALLBACK par_veh(EXCEPTION_POINTERS *ep)
{
    DWORD code = ep->ExceptionRecord->ExceptionCode;
    int slot = slot_of_thread();
    if (slot >= 0 && slot <= MAXW && g_in_job[slot] && (code & 0xC0000000u) == 0xC0000000u) {
        g_in_job[slot] = 0;
        longjmp(g_jb[slot], 1);
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

static void *seh_head(void) { void *p; __asm__ __volatile__("movl %%fs:0, %0" : "=r"(p)); return p; }
static void seh_set(void *p) { __asm__ __volatile__("movl %0, %%fs:0" : : "r"(p) : "memory"); }
static void *g_seh[MAXW + 1];

static int run_chunk_guarded(int b, int e, int slot)
{
    g_seh[slot] = seh_head();       /* game code may push MSVC EH frames; a longjmp skips their pops */
    if (setjmp(g_jb[slot])) { seh_set(g_seh[slot]); g_in_job[slot] = 0; return 1; }
    g_in_job[slot] = 1;
    P.fn(b, e, P.ctx, slot);
    g_in_job[slot] = 0;
    return 0;
}

/* claim chunks of generation g until none are left */
static void drain(int slot, LONG g)
{
    LONG tag = (g & 0xffff) << 16;
    for (;;) {
        LONG cur = P.claim;
        if ((LONG)(cur & 0xffff0000) != tag) return;             /* a newer (or no) job: stop */
        LONG idx = cur & 0xffff;
        if (idx >= P.nchunks) return;
        if (InterlockedCompareExchange(&P.claim, cur + 1, cur) != cur) continue;
        if (run_chunk_guarded(s_chunks[idx].begin, s_chunks[idx].end, slot)) {
            s_fault[idx] = 1;
            InterlockedIncrement((volatile LONG *)&g_stats.faults);
        }
        if (InterlockedDecrement(&P.remaining) == 0) SetEvent(P.alldone);
    }
}

static DWORD WINAPI worker_main(LPVOID pv)
{
    int id = (int)(INT_PTR)pv;
    TlsSetValue(g_tls, (LPVOID)(INT_PTR)(id + 2));          /* slot id+1 */
    LONG seen = 0;
    int64_t budget = (int64_t)(par_cfg.idle_park_us * P.qpc_per_us);
    for (;;) {
        /* spin for the idle budget */
        int64_t t0 = qpc();
        unsigned k = 0;
        LONG pg = P.park_gen;
        while (P.gen == seen && !P.quit && P.park_gen == pg) {
            YieldProcessor();
            if ((++k & 63) == 0 && qpc() - t0 > budget) break;
        }
        /* park: arm, recheck, wait */
        if (P.gen == seen && !P.quit) {
            InterlockedExchange(&P.arm[id], 1);
            if (P.gen == seen && !P.quit) {
                WaitForSingleObject(P.ev[id], INFINITE);
                InterlockedIncrement((volatile LONG *)&g_stats.wakes);
            } else if (InterlockedExchange(&P.arm[id], 0) == 0) {
                WaitForSingleObject(P.ev[id], INFINITE);    /* main took the arm: eat its signal */
            }
        }
        if (P.quit) return 0;
        seen = P.gen;
        fpu_load();
        drain(id + 1, seen);
    }
}

int par_init(int nworkers)
{
    char v[32];
    if (P.inited) return P.n;
    if (g_tls == TLS_OUT_OF_INDEXES) g_tls = TlsAlloc();
    TlsSetValue(g_tls, (LPVOID)(INT_PTR)1);                 /* main thread = slot 0 */
    if (GetEnvironmentVariableA("PAR_IDLE_US", v, sizeof v)) par_cfg.idle_park_us = (uint32_t)atoi(v);
    if (GetEnvironmentVariableA("PAR_WORKERS", v, sizeof v)) nworkers = atoi(v);
    if (nworkers <= 0) nworkers = par_cfg.nworkers;
    if (nworkers <= 0) {
        SYSTEM_INFO si; GetSystemInfo(&si);
        nworkers = (int)si.dwNumberOfProcessors - 1;
        if (nworkers > 7) nworkers = 7;       /* 8 participants incl. main; 12 P-cores on M3 Max */
        if (nworkers < 1) nworkers = 1;
    }
    if (nworkers > MAXW) nworkers = MAXW;
    LARGE_INTEGER f; QueryPerformanceFrequency(&f);
    P.qpc_per_us = f.QuadPart / 1e6;
    P.n = nworkers;
    P.alldone = CreateEventA(NULL, FALSE, FALSE, NULL);
    if (!g_veh) g_veh = AddVectoredExceptionHandler(1, par_veh);
    fpu_capture();
    for (int i = 0; i < P.n; i++) {
        P.ev[i] = CreateEventA(NULL, FALSE, FALSE, NULL);
        P.th[i] = CreateThread(NULL, 256 * 1024, worker_main, (LPVOID)(INT_PTR)i, 0, NULL);
        SetThreadPriority(P.th[i], par_cfg.pin_priority);
    }
    P.inited = 1;
    return P.n;
}

void par_refresh_fpu(void) { fpu_capture(); }

/* Wake parked workers ahead of a parallel region so the kernel wake (12-30 us) overlaps the main
 * thread's serial work; they then spin for the idle budget. A woken worker with no job just spins. */
void par_prewake(void)
{
    if (!P.inited) return;
    for (int i = 0; i < P.n; i++)
        if (InterlockedExchange(&P.arm[i], 0)) SetEvent(P.ev[i]);
}

/* End of the frame's parallel region (e.g. before Present): spinning workers park immediately. */
void par_park_now(void)
{
    if (P.inited) InterlockedIncrement(&P.park_gen);
}

void par_shutdown(void)
{
    if (!P.inited) return;
    P.quit = 1;
    InterlockedIncrement(&P.gen);
    for (int i = 0; i < P.n; i++) SetEvent(P.ev[i]);
    WaitForMultipleObjects(P.n, P.th, TRUE, 2000);
    for (int i = 0; i < P.n; i++) { CloseHandle(P.th[i]); CloseHandle(P.ev[i]); }
    CloseHandle(P.alldone);
    if (g_veh) { RemoveVectoredExceptionHandler(g_veh); g_veh = NULL; }
    memset(&P, 0, sizeof P);
}

int par_for(int n, int grain, par_fn fn, void *ctx)
{
    g_stats.jobs++;
    if (n <= 0) return 0;
    if (grain < 1) grain = 1;
    /* serial fallback: no pool, called from a worker (nesting), too small, or reentered */
    if (!P.inited || slot_of_thread() != 0 || n < grain * 2 ||
        InterlockedCompareExchange(&P.in_par, 1, 0) != 0) {
        g_stats.serial_jobs++;
        fn(0, n, ctx, 0);
        return 0;
    }
    int nch = (n + grain - 1) / grain;
    if (nch > MAXCHUNKS) { grain = (n + MAXCHUNKS - 1) / MAXCHUNKS; nch = (n + grain - 1) / grain; }
    for (int i = 0; i < nch; i++) {
        s_chunks[i].begin = i * grain;
        s_chunks[i].end = (i + 1) * grain < n ? (i + 1) * grain : n;
        s_fault[i] = 0;
    }
    int64_t t0 = qpc();
    LONG g = P.gen + 1;
    if ((g & 0xffff) == 0) g++;                   /* tag 0 never names a live job */
    P.fn = fn; P.ctx = ctx; P.nchunks = nch;
    P.remaining = nch;
    g_stats.chunks += nch;
    fpu_capture();                                /* the job runs with the caller's FPU state */
    P.claim = (g & 0xffff) << 16;
    MemoryBarrier();
    InterlockedExchange(&P.gen, g);               /* publish */
    for (int i = 0; i < P.n; i++)
        if (InterlockedExchange(&P.arm[i], 0)) SetEvent(P.ev[i]);

    drain(0, g);                                  /* main pitches in */
    while (P.remaining > 0) {
        int64_t s0 = qpc();
        while (P.remaining > 0 && qpc() - s0 < (int64_t)(50 * P.qpc_per_us)) YieldProcessor();
        if (P.remaining > 0) WaitForSingleObject(P.alldone, 1);
    }
    g_stats.dispatch_us_sum += (qpc() - t0) / P.qpc_per_us;

    int faults = 0;
    for (int i = 0; i < nch; i++)
        if (s_fault[i]) { fn(s_chunks[i].begin, s_chunks[i].end, ctx, 0); faults++; }  /* serial retry */
    InterlockedExchange(&P.in_par, 0);
    return faults;
}

const par_stats *par_get_stats(void) { return &g_stats; }

int par_slot(void) { return g_tls == TLS_OUT_OF_INDEXES ? 0 : slot_of_thread(); }
