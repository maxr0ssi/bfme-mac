/* R5 parallel framework — shared worker pool for the RotWK in-memory patch DLL (research
 * prototype; not wired into gamepatch/). Persistent workers, spin-then-park, a parallel_for with
 * chunking and a serial fallback, x87+MXCSR propagation, and SEH exception safety so a fault in a
 * worker falls back to serial instead of hanging the game.
 *
 * Design contract (see parallel/DESIGN.md):
 *   - The MAIN thread is the only one that calls par_for(). Workers never call par_for (no nesting);
 *     a nested call runs serially on the caller. par_for is NOT reentrant across threads.
 *   - The job fn must be pure w.r.t. shared game state: it may touch only per-worker-redirected
 *     scratch (see the function cloner) and its own [begin,end) slice. Side effects (D3D, list
 *     pushes, allocations) are recorded and replayed by the main thread (see the deferred recorder).
 *   - FPU: the pool snapshots the main thread's x87 control word (the game sets PC_24 at 0x440809)
 *     and MXCSR at par_init(), and every worker loads that snapshot before each job.
 */
#ifndef PARALLEL_H
#define PARALLEL_H
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* A job: process items [begin,end) for chunk. ctx is the caller's shared read-only context;
 * worker is 0..nworkers (0 = the main thread running its own chunk). */
typedef void (*par_fn)(int begin, int end, void *ctx, int worker);

/* Start the pool: nworkers persistent threads (0 => auto = perf_cores-1). Captures the calling
 * (main) thread's x87 CW + MXCSR. Returns the worker count actually started. Idempotent. */
int  par_init(int nworkers);
void par_shutdown(void);

/* Run fn over [0,n) split into chunks of ~grain items, on the pool + the calling thread.
 * If n < grain*2 or the pool is unavailable or a nested call, runs serially on the caller.
 * Returns 0 on a fully parallel/serial success, or the number of chunks that faulted (their
 * items were retried serially on the main thread, so results are always complete). */
int  par_for(int n, int grain, par_fn fn, void *ctx);

/* Frame hooks: wake workers ahead of a parallel region; park them at its end (e.g. at Present). */
void par_prewake(void);
void par_park_now(void);

/* Re-snapshot the FPU state (call if the game changed the CW/MXCSR mid-frame; cheap). */
void par_refresh_fpu(void);

/* Tuning (env overrides read in par_init: PAR_IDLE_US, PAR_WORKERS). */
typedef struct {
    int      nworkers;
    uint32_t reserved;
    uint32_t idle_park_us;   /* keep spinning this long after last job, then park (default 200);
                                env PAR_IDLE_US. 0 = park immediately. */
    int      pin_priority;   /* SetThreadPriority level for workers (default ABOVE_NORMAL) */
} par_config;
extern par_config par_cfg;

/* Stats for the verification/logging harness. */
typedef struct {
    uint64_t jobs;           /* par_for calls */
    uint64_t serial_jobs;    /* ran serially (below threshold / nested / no pool) */
    uint64_t chunks;         /* chunks dispatched to workers */
    uint64_t wakes;          /* times a worker was parked and had to be woken (kernel wait) */
    uint64_t faults;         /* worker SEH faults caught */
    double   dispatch_us_sum;/* sum of fork/join wall time for parallel jobs */
} par_stats;
const par_stats *par_get_stats(void);

/* Calling thread's participant slot: 0 = main, 1..n = pool workers, -1 = another thread. */
int par_slot(void);

#ifdef __cplusplus
}
#endif
#endif
