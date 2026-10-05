/* t_lmath2: the second batch of logic-math replacements (p_lmath2.c/.S).
 * crtsqrt against Wine's builtin msvcr71 sqrt, the function the exe's IAT entry 0xbd06a0 holds in
 * the game (this test runs under the same Wine build):
 *   [0] the installer accepts Wine's msvcr71 (builtin marker, self-test) and rewrites the IAT
 *       entry, checked against its original value (the exe's import page mapped at 0xbd0000)
 *   [1] all 2^32 floats as double arguments (the exe's callers pass float expressions)
 *   [2] random doubles: any positive exponent incl. subnormals; exact 24-bit ties (y*y with y a
 *       25-bit odd integer times a power of two, so sqrt lands exactly halfway) and their
 *       neighbours one double ulp either side; specials (zeros, negatives, inf, NaN, extremes)
 *   [3] full machine state through lm_harness.h: every general register, xmm0-7, x87 state,
 *       MXCSR control, argument slots, canaries, esp
 *   [4] seven other FPU modes: every call runs Wine's sqrt, identical
 *   [5] time per call
 * Compared in [1]/[2]: st0 (80 bits), eax, ecx, edx, xmm0 (128 bits), the x87 stack depth.
 * octile 0x7658c3 against an untouched copy of the original (its CRT fabs calls go through the
 * exe's thunk 0xa3cf8a and IAT entry 0xbd06a8 = Wine's fabs, as in the game):
 *   [6] the patch applies to the original bytes (relocated copy of the code pages)
 *   [7] random segments through lm_harness.h (full machine state, both argument slots) plus the
 *       two points' memory: map coordinates, cell centres, equal |dx| and |dy|, any bit pattern,
 *       wide exponents (overflow and underflow), specials (zeros, inf, NaN, subnormals)
 *   [8] the seven other FPU modes: every call runs the x87 original, identical
 *   [9] time per call
 * usage: t_lmath2.exe <path to lotrbfme2ep1.exe 2.02> [millions] [threads] [fraction of [1]] */
#include "orig.h"
#include "gp_logic.h"
#include "lm_harness.h"
#include <stdlib.h>
#include <stdarg.h>
#include <math.h>

static int fails, quiet;
static void verdict(int bad, const char *fmt, ...) __attribute__((format(printf, 2, 3)));
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap;
    if (bad || !quiet) { va_start(ap, fmt); vprintf(fmt, ap); va_end(ap); }
    fails += bad != 0;
}

/* one call from a fixed state in FPU mode (cw, mx); out: st0 80 bits, eax ecx edx, xmm0, x87 depth */
typedef struct { uint8_t st[10]; uint16_t depth; uint32_t r[3]; uint8_t x0[16]; } out_t;
__asm__(".text\n_one:\n"
"  pushl %ebp\n  movl %esp, %ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n  subl $24, %esp\n"
"  fnstcw 16(%esp)\n  stmxcsr 20(%esp)\n  fninit\n  fldcw 24(%ebp)\n  ldmxcsr 28(%ebp)\n"
"  movl 16(%ebp), %eax\n  movl 12(%ebp), %ecx\n  movl %eax, 4(%esp)\n  movl %ecx, (%esp)\n"
"  movl $0x5a5a5a5a, %eax\n  movl $0x6b6b6b6b, %ecx\n  movl $0x7c7c7c7c, %edx\n"
"  movd %eax, %xmm0\n  pshufd $0x1b, %xmm0, %xmm0\n  movl $0x3c3c3c3c, %esi\n  movl $0x4d4d4d4d, %edi\n"
"  call *8(%ebp)\n"
"  movl 20(%ebp), %ebx\n  movl %eax, 12(%ebx)\n  movl %ecx, 16(%ebx)\n  movl %edx, 20(%ebx)\n"
"  movups %xmm0, 24(%ebx)\n  fstpt (%ebx)\n  fnstsw %ax\n  movw %ax, 10(%ebx)\n"
"  cmpl $0x3c3c3c3c, %esi\n  jne 1f\n  cmpl $0x4d4d4d4d, %edi\n  jne 1f\n  fldcw 16(%esp)\n  ldmxcsr 20(%esp)\n"
"  addl $24, %esp\n  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n"
"1: int3\n");
void one(void *fn, uint32_t lo, uint32_t hi, out_t *o, uint32_t cw, uint32_t mx);

static void *wine_sqrt;
static int same(uint32_t lo, uint32_t hi, uint32_t cw, uint32_t mx)
{
    out_t a, b;
    memset(&a, 0, sizeof a); memset(&b, 0, sizeof b);
    one(wine_sqrt, lo, hi, &a, cw, mx);
    one((void *)gp_sqrt, lo, hi, &b, cw, mx);
    /* the status word only for its stack-top field after the pop (sticky flags differ: fsqrt sets
     * the precision flag, fld does not; the game never reads them) */
    a.depth &= 0x3800; b.depth &= 0x3800;
    return !memcmp(&a, &b, sizeof a);
}

typedef struct { uint64_t lo, hi, bad; uint32_t first; } job_t;
static DWORD WINAPI floats(LPVOID p)
{
    job_t *j = p;
    /* Wine's CRT sets up its per-thread data (errno) on the first error in a thread, and that first
     * call leaves other registers: one warm-up error per thread before comparing */
    out_t w; one(wine_sqrt, 0, 0xbff00000u, &w, 0x007f, 0x1f80);
    for (uint64_t i = j->lo; i < j->hi; i++) {
        union { uint32_t u; float f; } c = { (uint32_t)i };
        union { double d; uint32_t w[2]; } d = { (double)c.f };
        if (!same(d.w[0], d.w[1], 0x007f, 0x1f80) && !j->bad++) j->first = (uint32_t)i;
    }
    return 0;
}

static uint32_t rng = 20261005;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }

/* ---- octile ---------------------------------------------------------------------------------- */
static float fb(uint32_t u) { union { uint32_t u; float f; } c = { u }; return c.f; }
static uint32_t bf(float f) { union { float f; uint32_t u; } c = { f }; return c.u; }
static float rf(float lo, float hi) { return lo + (hi - lo) * (float)(rnd() >> 8) / 16777216.0f; }
static float wide(int emin, int emax)
{
    int e = emin + (int)(rnd() % (unsigned)(emax - emin + 1));
    return fb((rnd() & 0x807fffffu) | (uint32_t)(e + 127) << 23);
}
static const uint32_t specials[] = {0, 0x80000000, 0x7f800000, 0xff800000, 0x7fc00000, 0xffc00000, 0x7fa00000,
    1, 0x80000001, 0x007fffff, 0x00800000, 0x7f7fffff, 0xff7fffff, 0x3f800000, 0xbf800000};
static void gen_seg(float p[4])
{
    switch (rnd() % 8) {
    case 0: for (int k = 0; k < 4; k++) p[k] = fb(rnd()); break;                      /* any bits */
    case 1: for (int k = 0; k < 4; k++) p[k] = wide(-149, 127); break;
    case 2: for (int k = 0; k < 4; k++) p[k] = rnd() & 1 ? fb(specials[rnd() % 15]) : rf(-3e3f, 3e3f); break;
    case 3: {                                                                          /* |dx| == |dy| */
        float d = rf(0, 500); p[0] = rf(0, 5000); p[1] = rf(0, 5000);
        p[2] = p[0] + (rnd() & 1 ? d : -d); p[3] = p[1] + (rnd() & 1 ? d : -d); break; }
    case 4: for (int k = 0; k < 4; k++) p[k] = (float)(rnd() % 1000) * 10.0f + 5.0f; break;   /* cell centres */
    case 5: for (int k = 0; k < 4; k++) p[k] = wide(-149, -110); break;               /* tiny: underflow */
    case 6: for (int k = 0; k < 4; k++) p[k] = wide(120, 127); break;                 /* huge: overflow */
    default: for (int k = 0; k < 4; k++) p[k] = rf(0, 6000); break;                   /* map positions */
    }
}
static void test_octile(HMODULE crt, double millions)
{
    void *wine_fabs = (void *)GetProcAddress(crt, "fabs");
    if (gp_fnv1a(orig_bytes(0x7658c3, 0x82), 0x82) != GP_FNV_7658C3) { verdict(1, "[6] 0x7658c3 differs\n"); return; }
    uint32_t off = orig_reserve_image();
    if (!off || orig_map_at(0xbd0000, 0x2000, off) || orig_map_at(0x765000, 0x1000, off) || orig_map_at(0xa3c000, 0x2000, off))
        { verdict(1, "[6] cannot map\n"); return; }
    *(void **)0xbd06a8 = wine_fabs;                     /* what the loader writes (both copies) */
    *(void **)(uintptr_t)(0xbd06a8 + off) = wine_fabs;
    uint8_t *orig = orig_copy(0x7658c3, 0x82, 0);
    static const uint32_t calls[] = {0x7658e0, 0x7658ee, 0x765921, 0x76592f};
    for (int i = 0; i < 4; i++) orig_fix_rel32(orig, 0x7658c3, calls[i], (void *)(uintptr_t)(0xa3cf8a + off));
    gp_va_offset = off;
    int ok = gp_patch_octile();
    gp_va_offset = 0;
    verdict(!ok, "[6] octile: %s to the original bytes (relocated copy)\n", ok ? "applied" : "NOT applied");
    if (!ok) return;
    void *repl = (void *)(uintptr_t)(0x7658c3 + off);
    static const struct { uint32_t cw, mx; const char *name; } modes[] = {{0x007f, 0x1f80, "game mode"},
        {0x027f, 0x1f80, "PC_53"}, {0x037f, 0x1f80, "PC_64"}, {0x047f, 0x1f80, "PC_24 RC down"},
        {0x0c7f, 0x1f80, "PC_24 RC chop"}, {0x087f, 0x1f80, "PC_24 RC up"}, {0x007f, 0x5f80, "MXCSR RC down"},
        {0x007f, 0x9fc0, "MXCSR FTZ+DAZ"}};
    for (unsigned m = 0; m < sizeof modes / sizeof modes[0]; m++) {
        uint64_t n = 0, bad = 0, total = m ? 100000 : (uint64_t)(millions * 1e6);
        LONG c0 = gp_l2_count(2), x0 = gp_l2_count(3);
        static float mem[2][8];
        for (uint64_t it = 0; it < total; it++) {
            float p[4]; gen_seg(p);
            hc_t c[2];
            for (int v = 0; v < 2; v++) {
                for (int k = 0; k < 8; k++) mem[v][k] = fb(0x7fc00000u + k);
                mem[v][1] = p[0]; mem[v][2] = p[1]; mem[v][5] = p[2]; mem[v][6] = p[3];
                hc_init(&c[v], (uint32_t)(uintptr_t)(v ? repl : (void *)orig), 2);
                c[v].cw = modes[m].cw; c[v].mxcsr = modes[m].mx;
                c[v].args[0] = (uint32_t)(uintptr_t)&mem[v][1]; c[v].args[1] = (uint32_t)(uintptr_t)&mem[v][5];
                hc_call(&c[v]);
            }
            __asm__ volatile("fninit");
            /* the argument slots are compared as written (floats), the pointers they held differ */
            const char *d = hc_diff(&c[0], &c[1], 0, 0);
            if (!*d && memcmp(mem[0], mem[1], sizeof mem[0])) d = "point memory";
            n++;
            if (*d && bad++ < 5) printf("  MISMATCH (%s) %s: a = %08x %08x, b = %08x %08x\n", d, modes[m].name,
                                        bf(p[0]), bf(p[1]), bf(p[2]), bf(p[3]));
        }
        LONG c1 = gp_l2_count(2) - c0, x1 = gp_l2_count(3) - x0;
        verdict(bad != 0 || (m && c1 != x1), "[%d] octile, %-14s %llu segments, full state + both points: %llu mismatches; "
                "%ld of %ld ran the x87 original\n", m ? 8 : 7, modes[m].name, n, bad, x1, c1);
    }
    /* [9] speed: map positions, game mode */
    static float pts[1024][2];
    for (int i = 0; i < 1024; i++) { pts[i][0] = rf(0, 6000); pts[i][1] = rf(0, 6000); }
    unsigned short gcw = 0x007f; unsigned gmx = 0x1f80;
    __asm__ volatile("fninit\n fldcw %0\n ldmxcsr %1" : : "m"(gcw), "m"(gmx));
    double ns[2];
    for (int v = 0; v < 2; v++) {
        float (__cdecl *f)(const float *, const float *) = (float (__cdecl *)(const float *, const float *))(v ? repl : (void *)orig);
        volatile float sink = 0; int N = 4000000;
        uint64_t t = now_us();
        for (int i = 0; i < N; i++) sink = f(pts[i & 1023], pts[(i + 1) & 1023]);
        ns[v] = (now_us() - t) * 1000.0 / N; (void)sink;
    }
    printf("[9] octile: original %.1f ns, replacement %.1f ns per call (with the loop)\n", ns[0], ns[1]);
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    double millions = argc > 2 ? atof(argv[2]) : 20;
    int nthreads = argc > 3 ? atoi(argv[3]) : 16;
    double frac = argc > 4 ? atof(argv[4]) : 1;
    HMODULE crt = LoadLibraryA("msvcr71.dll");
    wine_sqrt = crt ? (void *)GetProcAddress(crt, "sqrt") : NULL;
    if (!wine_sqrt) { printf("no msvcr71 sqrt\nFAIL\n"); return 1; }

    /* [0] */
    if (orig_map_at(0xbd0000, 0x2000, 0)) return 2;
    *(void **)0xbd06a0 = wine_sqrt;                     /* what the loader writes */
    int ok = gp_patch_crtsqrt();
    verdict(!ok || *(void **)0xbd06a0 != (void *)gp_sqrt || gp_sqrt_orig != (uint32_t)(uintptr_t)wine_sqrt,
            "[0] installer: %s; IAT 0xbd06a0 -> %s\n", ok ? "applied" : "NOT applied",
            *(void **)0xbd06a0 == (void *)gp_sqrt ? "gp_sqrt" : "unchanged");
    if (!ok) { printf("FAIL\n"); return 1; }
    LONG x0 = gp_sqrt_count(1);

    /* [1] all floats */
    uint64_t t0 = now_us(), bad = 0, total = (uint64_t)(frac * 4294967296.0);
    job_t jobs[64]; HANDLE th[64];
    if (nthreads > 64) nthreads = 64;
    for (int i = 0; i < nthreads; i++) {
        memset(&jobs[i], 0, sizeof jobs[i]);
        jobs[i].lo = total * i / nthreads; jobs[i].hi = total * (i + 1) / nthreads;
        th[i] = CreateThread(NULL, 0, floats, &jobs[i], 0, NULL);
    }
    WaitForMultipleObjects(nthreads, th, TRUE, INFINITE);
    for (int i = 0; i < nthreads; i++) {
        bad += jobs[i].bad;
        if (jobs[i].bad) printf("  MISMATCH float %08x\n", jobs[i].first);
    }
    verdict(bad != 0, "[1] %s2^32 floats as arguments: %llu mismatches; %lu ran Wine's sqrt (zeros, negatives, "
            "inf, NaN)  [%.0f s, %d threads]\n", frac < 1 ? "PART OF " : "all ", bad, (unsigned long)(gp_sqrt_count(1) - x0),
            (now_us() - t0) / 1e6, nthreads);

    /* [2] random, ties, specials */
    static const uint32_t sp[][2] = {{0, 0}, {0, 0x80000000}, {0, 0x7ff00000}, {0, 0xfff00000}, {0, 0x7ff80000},
        {1, 0x7ff00000}, {0, 0xfff80000}, {1, 0}, {0xffffffff, 0x000fffff}, {0, 0x00100000}, {0xffffffff, 0x7fefffff},
        {0, 0x3ff00000}, {0, 0x40000000}, {1, 0x80000000}, {0, 0xbff00000}, {0xffffffff, 0x7fffffff}};
    uint64_t n = 0, ties = 0; bad = 0;
    for (unsigned i = 0; i < sizeof sp / sizeof sp[0]; i++, n++)
        if (!same(sp[i][0], sp[i][1], 0x007f, 0x1f80) && bad++ < 5) printf("  MISMATCH %08x%08x\n", sp[i][1], sp[i][0]);
    uint64_t m = (uint64_t)(millions * 1e6);
    for (uint64_t it = 0; it < m; it++) {
        union { double d; uint64_t u; uint32_t w[2]; } x;
        switch (it % 4) {
        case 0: x.w[0] = rnd(); x.w[1] = rnd() & 0x7fffffff; break;              /* any bits, positive */
        case 1: x.w[0] = rnd(); x.w[1] = rnd() & 0x000fffff; break;              /* subnormals */
        default: {                                                                /* ties +- 1 ulp */
            uint64_t k = (uint64_t)((rnd() & 0xffffff) | 0x1000000) | 1;          /* 25-bit odd */
            int e = (int)(rnd() % 900) - 450;
            x.d = ldexp((double)(k * k), 2 * e);                                  /* exact: 50 bits */
            if (x.d == 0 || isinf(x.d)) continue;
            int s = it % 4 == 2 ? 0 : (rnd() & 1 ? 1 : -1);
            x.u += (uint64_t)(int64_t)s;
            ties++;
        }
        }
        n++;
        if (!same(x.w[0], x.w[1], 0x007f, 0x1f80) && bad++ < 5) printf("  MISMATCH %08x%08x\n", x.w[1], x.w[0]);
    }
    verdict(bad != 0, "[2] %llu doubles (%llu exact 24-bit ties and their neighbours, subnormals, specials): "
            "%llu mismatches\n", n, ties, bad);

    /* [3] full state */
    n = bad = 0;
    for (uint64_t it = 0; it < m / 20 + 1000; it++) {
        union { double d; uint32_t w[2]; } x;
        x.w[0] = rnd(); x.w[1] = it % 7 ? (rnd() & 0x7fffffff) : rnd();
        if (it % 5 == 0) x.d = (double)(float)x.d;
        hc_t c[2];
        for (int v = 0; v < 2; v++) {
            hc_init(&c[v], (uint32_t)(uintptr_t)(v ? (void *)gp_sqrt : wine_sqrt), 2);
            c[v].args[0] = x.w[0]; c[v].args[1] = x.w[1];
            hc_call(&c[v]);
        }
        __asm__ volatile("fninit");
        const char *d = hc_diff(&c[0], &c[1], 0, 0);
        n++;
        if (*d && bad++ < 5) printf("  MISMATCH (%s) x = %08x%08x\n", d, x.w[1], x.w[0]);
    }
    verdict(bad != 0, "[3] %llu calls, full machine state: %llu mismatches\n", n, bad);

    /* [4] other modes */
    static const struct { uint32_t cw, mx; const char *name; } modes[] = {
        {0x027f, 0x1f80, "PC_53"}, {0x037f, 0x1f80, "PC_64"}, {0x047f, 0x1f80, "PC_24 RC down"},
        {0x0c7f, 0x1f80, "PC_24 RC chop"}, {0x087f, 0x1f80, "PC_24 RC up"}, {0x007f, 0x5f80, "MXCSR RC down"},
        {0x007f, 0x9fc0, "MXCSR FTZ+DAZ"}};
    for (unsigned k = 0; k < sizeof modes / sizeof modes[0]; k++) {
        LONG c0 = gp_sqrt_count(0), f0 = gp_sqrt_count(1);
        n = bad = 0;
        for (int it = 0; it < 100000; it++) {
            uint32_t lo = rnd(), hi = it & 1 ? rnd() & 0x7fffffff : rnd() & 0x000fffff;
            n++;
            if (!same(lo, hi, modes[k].cw, modes[k].mx) && bad++ < 3) printf("  MISMATCH %08x%08x\n", hi, lo);
        }
        LONG c1 = gp_sqrt_count(0) - c0, f1 = gp_sqrt_count(1) - f0;
        verdict(bad != 0 || c1 != f1, "[4] %-14s %llu calls: %ld ran Wine's sqrt, %llu mismatches\n", modes[k].name, n, f1, bad);
    }

    /* [5] speed (game mode; inputs as the game's: float-valued sums) */
    static double in[4096];
    for (int i = 0; i < 4096; i++) in[i] = (double)((float)(rnd() >> 8) * 0.37f + 1.0f);
    double ns[2];
    unsigned short gcw = 0x007f; __asm__ volatile("fninit\n fldcw %0" : : "m"(gcw));
    for (int v = 0; v < 2; v++) {
        double (__cdecl *f)(double) = (double (__cdecl *)(double))(v ? (void *)gp_sqrt : wine_sqrt);
        volatile double sink = 0; int N = 4000000;
        uint64_t t = now_us();
        for (int i = 0; i < N; i++) sink = f(in[i & 4095]);
        ns[v] = (now_us() - t) * 1000.0 / N; (void)sink;
    }
    printf("[5] Wine's sqrt %.1f ns, gp_sqrt %.1f ns per call (with the loop)\n", ns[0], ns[1]);
    test_octile(crt, millions);
    gp_l2_exit_log();
    printf("%s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
