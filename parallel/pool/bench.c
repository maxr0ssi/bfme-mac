/* R5 worker-pool bench + verification (standalone; runs under Wine in the research prefix).
 *   forkjoin  - fork/join round-trip cost, N workers, empty job (hybrid must not hang)
 *   grain     - par_for overhead vs grain size on a synthetic compute workload
 *   verify    - serial vs parallel byte-for-byte output comparison + FPU propagation check
 * Usage: bench.exe [forkjoin|grain|verify|all] [nworkers]
 */
#include "parallel.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static double now_us(void)
{
    static LARGE_INTEGER f; LARGE_INTEGER t;
    if (!f.QuadPart) QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&t);
    return t.QuadPart * 1e6 / f.QuadPart;
}
static int cmpd(const void *a, const void *b)
{ double x = *(const double *)a, y = *(const double *)b; return x < y ? -1 : x > y; }

/* ---- a synthetic per-item workload resembling the shadow geometry math (invsqrt + a few muls) */
typedef struct { const float *in; float *out; int flops; } work_ctx;
static void work_fn(int begin, int end, void *ctx, int worker)
{
    (void)worker;
    work_ctx *w = (work_ctx *)ctx;
    for (int i = begin; i < end; i++) {
        float x = w->in[i];
        for (int k = 0; k < w->flops; k++) {
            float r; __asm__("rsqrtss %1,%0" : "=x"(r) : "x"(x + (float)k));
            x = x * 0.5f + r;
        }
        w->out[i] = x;
    }
}

/* an empty job for pure fork/join cost */
static void nop_fn(int begin, int end, void *ctx, int worker) { (void)begin;(void)end;(void)ctx;(void)worker; }

static double pct(double *t, int R, double q) { return t[(int)(R * q) < R ? (int)(R * q) : R - 1]; }

/* fork/join: one chunk per participant (true round trip), hot vs first-after-park */
static void bench_forkjoin(int nw)
{
    par_init(nw);
    int R = 4000, P1 = nw + 1;
    static double hot[4000], cold[400]; int nh = 0, nc = 0;
    for (int warm = 0; warm < 200; warm++) par_for(P1, 1, nop_fn, NULL);
    for (int r = 0; r < R; r++) {
        int after_park = (r % 10) == 0;
        if (after_park) Sleep(2);                      /* > idle budget: workers park */
        double a = now_us();
        par_for(P1, 1, nop_fn, NULL);
        double d = now_us() - a;
        if (after_park) cold[nc++] = d; else hot[nh++] = d;
    }
    qsort(hot, nh, sizeof hot[0], cmpd); qsort(cold, nc, sizeof cold[0], cmpd);
    printf("forkjoin  workers=%d hot   median %6.2f us  p90 %6.2f  p99 %6.2f  max %7.2f\n",
           nw, pct(hot,nh,.5), pct(hot,nh,.9), pct(hot,nh,.99), hot[nh-1]);
    printf("forkjoin  workers=%d parked median %6.2f us  p90 %6.2f  p99 %6.2f  max %7.2f  (wakes %llu)\n",
           nw, pct(cold,nc,.5), pct(cold,nc,.9), pct(cold,nc,.99), cold[nc-1],
           (unsigned long long)par_get_stats()->wakes);
    /* 64 tiny chunks: claim contention */
    static double t[2000];
    for (int r = 0; r < 2000; r++) { double a = now_us(); par_for(64, 1, nop_fn, NULL); t[r] = now_us() - a; }
    qsort(t, 2000, sizeof t[0], cmpd);
    printf("forkjoin  workers=%d 64 chunks median %6.2f us  p99 %6.2f  (per-chunk claim %.2f us)\n",
           nw, t[1000], t[1980], t[1000] / 64);
    par_shutdown();
}

/* CPU burned per simulated 30 ms frame: 4 bursts of 1 ms parallel work in the first 8 ms */
static void bench_budget(int nw)
{
    int budgets[] = { 0, 200, 2000, 1000000, -2000 };   /* -2000: 2000 + prewake + park_now */
    int N = 1 << 14;
    float *in = malloc(N * sizeof(float)), *out = malloc(N * sizeof(float));
    for (int i = 0; i < N; i++) in[i] = 1.0f + i * 1e-4f;
    for (unsigned b = 0; b < sizeof budgets / sizeof budgets[0]; b++) {
        int hooks = budgets[b] < 0, bud = hooks ? -budgets[b] : budgets[b];
        char v[16]; sprintf(v, "%d", bud); SetEnvironmentVariableA("PAR_IDLE_US", v);
        uint64_t wk0 = par_get_stats()->wakes;
        par_init(nw);
        work_ctx w = { in, out, 24 };
        FILETIME c, e, k0, u0, k1, u1;
        GetProcessTimes(GetCurrentProcess(), &c, &e, &k0, &u0);
        double wall0 = now_us(), burst = 0; int frames = 60;
        for (int f = 0; f < frames; f++) {
            double fs = now_us();
            if (hooks) { par_prewake(); double p0 = now_us(); while (now_us() - p0 < 1000) YieldProcessor(); }
            for (int s = 0; s < 4; s++) {
                double a = now_us(); par_for(N, 256, work_fn, &w); burst += now_us() - a;
                while (now_us() - a < 2000) YieldProcessor();   /* serial main-thread work */
            }
            if (hooks) par_park_now();
            while (now_us() - fs < 30000) Sleep(1);             /* rest of the frame (render etc.) */
        }
        GetProcessTimes(GetCurrentProcess(), &c, &e, &k1, &u1);
        double wall = now_us() - wall0;
        double cpu = ((((uint64_t)u1.dwHighDateTime << 32) | u1.dwLowDateTime) -
                      (((uint64_t)u0.dwHighDateTime << 32) | u0.dwLowDateTime) +
                      (((uint64_t)k1.dwHighDateTime << 32) | k1.dwLowDateTime) -
                      (((uint64_t)k0.dwHighDateTime << 32) | k0.dwLowDateTime)) / 10.0;
        printf("budget    idle_park_us=%7d%s  cpu %.2f cores avg  parallel time %.0f us/frame (4 bursts)  wakes/frame %.1f\n",
               bud, hooks ? " +prewake+park_now" : "                  ", cpu / wall, burst / frames,
               (double)(par_get_stats()->wakes - wk0) / frames);
        par_shutdown();
    }
    SetEnvironmentVariableA("PAR_IDLE_US", NULL);
    free(in); free(out);
}

/* fault safety + nesting */
static volatile int fault_at = -1;
static void faulty_fn(int begin, int end, void *ctx, int worker)
{
    int *out = (int *)ctx;
    for (int i = begin; i < end; i++) {
        if (i == fault_at && worker != 0) *(volatile int *)0 = 1;   /* faults only on a worker */
        out[i] = i * 3;
    }
}
static void nested_fn(int begin, int end, void *ctx, int worker)
{
    (void)worker;
    int *out = (int *)ctx;
    for (int i = begin; i < end; i++) { int x = 0; par_for(8, 1, nop_fn, NULL); out[i] = i + x; }
}
static void bench_safety(int nw)
{
    par_init(nw);
    static int out[20000];
    int bad = 0, faults_total = 0;
    for (int r = 0; r < 50; r++) {
        memset(out, 0, sizeof out);
        fault_at = (r * 397) % 20000;
        faults_total += par_for(20000, 100, faulty_fn, out);
        for (int i = 0; i < 20000; i++) if (out[i] != i * 3) bad++;
    }
    printf("safety    50 jobs with a NULL write on a worker: faults caught %d (VEH count %llu), "
           "wrong items after serial retry %d\n", faults_total,
           (unsigned long long)par_get_stats()->faults, bad);
    memset(out, 0, sizeof out);
    uint64_t ser0 = par_get_stats()->serial_jobs;
    par_for(20000, 100, nested_fn, out);
    bad = 0; for (int i = 0; i < 20000; i++) if (out[i] != i) bad++;
    printf("nesting   par_for inside a job: ran serially %llu times, wrong items %d (no deadlock)\n",
           (unsigned long long)(par_get_stats()->serial_jobs - ser0), bad);
    double a = now_us(); LARGE_INTEGER q; for (int i = 0; i < 100000; i++) QueryPerformanceCounter(&q);
    printf("qpc       QueryPerformanceCounter %.3f us/call\n", (now_us() - a) / 100000);
    par_shutdown();
}

static void bench_grain(int nw)
{
    par_init(nw);
    int N = 1 << 16;
    float *in = malloc(N * sizeof(float)), *out = malloc(N * sizeof(float));
    for (int i = 0; i < N; i++) in[i] = 1.0f + (i & 1023) * 0.01f;
    int flopset[] = { 4, 16, 64 };   /* per-item cost: light .. heavy */
    printf("grain     workers=%d  N=%d   (median us over 400 iters; speedup vs serial)\n", nw, N);
    for (unsigned fi = 0; fi < sizeof flopset/sizeof flopset[0]; fi++) {
        work_ctx w = { in, out, flopset[fi] };
        /* serial baseline */
        double ser = 1e30;
        for (int r = 0; r < 80; r++) { double a = now_us(); work_fn(0, N, &w, 0); double d = now_us()-a; if (d<ser) ser=d; }
        printf("  flops/item=%2d  serial %.1f us\n", flopset[fi], ser);
        int grains[] = { 64, 256, 1024, 4096, 16384 };
        for (unsigned gi = 0; gi < sizeof grains/sizeof grains[0]; gi++) {
            int g = grains[gi];
            static double t[500]; int R = 400;
            for (int warm=0; warm<40; warm++) par_for(N, g, work_fn, &w);
            for (int r = 0; r < R; r++) { double a = now_us(); par_for(N, g, work_fn, &w); t[r]=now_us()-a;
                if ((r&63)==63) Sleep(1); }
            qsort(t, R, sizeof t[0], cmpd);
            printf("    grain %5d (%3d chunks)  median %.1f us  speedup %.2fx\n",
                   g, (N+g-1)/g, t[R/2], ser / t[R/2]);
        }
    }
    free(in); free(out); par_shutdown();
}

static void bench_verify(int nw)
{
    par_init(nw);
    int N = 40000;
    float *in = malloc(N*sizeof(float)), *a = malloc(N*sizeof(float)), *b = malloc(N*sizeof(float));
    for (int i=0;i<N;i++) in[i]=0.5f + (i%777)*0.013f;
    /* set an unusual x87 CW (PC_24 / round-to-nearest, like the game's 0x440809) and MXCSR (FTZ) */
    unsigned short cw = 0x003f & ~0x0300;  /* PC=00 => 24-bit precision */
    __asm__ __volatile__("fldcw %0"::"m"(cw));
    _mm_setcsr(_mm_getcsr() | 0x8040);     /* FTZ|DAZ */
    par_refresh_fpu();
    work_ctx w1={in,a,32}, w2={in,b,32};
    work_fn(0,N,&w1,0);                    /* serial reference */
    int faults = par_for(N, 512, work_fn, &w2);   /* parallel */
    int diff = memcmp(a,b,N*sizeof(float));
    printf("verify    workers=%d  N=%d  faults=%d  serial==parallel: %s\n",
           nw, N, faults, diff==0 ? "YES (byte-for-byte)" : "NO -- MISMATCH");
    if (diff) { for (int i=0;i<N;i++) if (a[i]!=b[i]) { printf("  first diff at %d: %a vs %a\n",i,a[i],b[i]); break; } }
    /* nested-call guard: par_for from inside a job must run serially, not deadlock */
    free(in); free(a); free(b); par_shutdown();
}

int main(int argc, char **argv)
{
    setbuf(stdout, NULL);
    fprintf(stderr, "[bench] start mode=%s\n", argc>1?argv[1]:"all"); fflush(stderr);
    const char *mode = argc > 1 ? argv[1] : "all";
    int nw = argc > 2 ? atoi(argv[2]) : 0;
    int workers[] = { 3, 7 };
    if (!strcmp(mode,"forkjoin")||!strcmp(mode,"all"))
        for (unsigned i=0;i<sizeof workers/sizeof workers[0];i++) bench_forkjoin(nw?nw:workers[i]);
    if (!strcmp(mode,"grain")||!strcmp(mode,"all"))  bench_grain(nw?nw:8);
    if (!strcmp(mode,"verify")||!strcmp(mode,"all")) bench_verify(nw?nw:8);
    if (!strcmp(mode,"budget")||!strcmp(mode,"all")) bench_budget(nw?nw:7);
    if (!strcmp(mode,"safety")||!strcmp(mode,"all")) bench_safety(nw?nw:7);
    fflush(stdout);
    fprintf(stderr, "[bench] main returning\n"); fflush(stderr);
    return 0;
}
