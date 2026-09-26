/* t_logic: the game-logic x87 replacements (p_logic.c/.S) against the original bytes of the exe.
 * The installers patch a relocated copy of the code pages (as in the game, byte checks included);
 * the reference is an untouched copy of each original function; the constant/IAT/.data pages the
 * code reads are mapped at their own addresses. Every compared call runs through lm_harness.h
 * (all registers, xmm0-7, x87 state, MXCSR, argument slots, stack), plus the output memory with
 * guard bytes, plus the sequence of virtual getter calls.
 *   [0] the four patches apply to the original bytes
 *   [1] mat2quat 0xb2bd10: rotation / scaled / random / wide / special matrices, out == m aliasing
 *   [2] distcalc 0xa3a7a0 (centre 2D) and 0xa3ae50 (bounding circle 2D) through a mock object
 *   [3] bsphere: the sqrt stub for all 2^32 inputs; the whole 0x59bc50 with a mock box
 *   [4] worldcell 0x6e8ce6: all 2^32 x values with both `exact` flags; random full-state calls
 *   [5] seven other FPU modes: everything falls back and stays identical
 *   [6] time per call, original vs replacement
 * usage: t_logic.exe <path to lotrbfme2ep1.exe 2.02> [millions per random test] [threads] */
#include "orig.h"
#include "gp_logic.h"
#include "lm_harness.h"
#include <stdlib.h>
#include <math.h>
#include <xmmintrin.h>
#include <stdarg.h>

uint32_t mk_seq;
__asm__(".text\n"
/* the getters leave their own ecx, edx and xmm0/xmm1 (compiled code may): whatever the second
 * one leaves must be what the replacement leaves */
"_mk_geom:\n  movl _mk_seq, %eax\n  leal 1(,%eax,4), %eax\n  movl %eax, _mk_seq\n"
"  leal 32(%ecx), %eax\n  movl $0x6e6e0001, %edx\n  movl $0x6e6e1001, %ecx\n"
"  movd %edx, %xmm0\n  movd %ecx, %xmm1\n  ret\n"
"_mk_pos:\n  movl _mk_seq, %eax\n  leal 2(,%eax,4), %eax\n  movl %eax, _mk_seq\n"
"  leal 16(%ecx), %eax\n  movl $0x6e6e0002, %edx\n  movl $0x6e6e1002, %ecx\n  movd %ecx, %xmm1\n  ret\n"
"_mk_box:\n  movl _mk_seq, %eax\n  leal 3(,%eax,4), %eax\n  movl %eax, _mk_seq\n"
"  pushl %esi\n  pushl %edi\n  leal 64(%ecx), %esi\n  movl 12(%esp), %edi\n  movl $6, %ecx\n  cld\n  rep movsl\n"
"  popl %edi\n  popl %esi\n  movl $0x6e6e0003, %edx\n  movl $0x6e6e1003, %ecx\n  ret $4\n"
/* the 9 bytes at 0x59bcb9 inline in a frame like 0x59bc50's; (fn = 0: original, else the stub) */
"_call_sq:\n  subl $0x24, %esp\n  movl 0x2c(%esp), %eax\n  movl %eax, 0x20(%esp)\n  movl $0xdeadbeef, (%esp)\n"
"  movl 0x28(%esp), %eax\n  testl %eax, %eax\n  jz 1f\n  call *%eax\n  jmp 2f\n"
"1: flds 0x20(%esp)\n  fsqrt\n  fstps (%esp)\n"
"2: movl (%esp), %eax\n  addl $0x24, %esp\n  ret\n"
"_call_wc:\n  pushl 16(%esp)\n  pushl 16(%esp)\n  pushl 16(%esp)\n  call *16(%esp)\n  movl 4(%esp), %eax\n  addl $12, %esp\n  ret\n"
"_call_this1:\n  movl 4(%esp), %eax\n  movl 8(%esp), %ecx\n  pushl 12(%esp)\n  call *%eax\n  ret\n");
void mk_geom(void); void mk_pos(void); void mk_box(void);
uint32_t call_sq(void *fn, uint32_t r2);
uint32_t call_wc(void *fn, int32_t *out, uint32_t exact, const float *p);
void call_this1(void *fn, void *self, void *arg);

typedef struct { void **vt; uint32_t pad[3]; float pos[4]; uint8_t geom[32]; float box[8]; } mobj_t;
static void *vtab[80];

static uint32_t rng = 20260925;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static float fb(uint32_t u) { union { uint32_t u; float f; } c = { u }; return c.f; }
static uint32_t bf(float f) { union { float f; uint32_t u; } c = { f }; return c.u; }
static float rf(float lo, float hi) { return lo + (hi - lo) * (float)(rnd() >> 8) / 16777216.0f; }
static float wide(int emin, int emax)
{
    int e = emin + (int)(rnd() % (unsigned)(emax - emin + 1));
    return fb((rnd() & 0x807fffffu) | (uint32_t)(e + 127) << 23);
}
static const uint32_t specials[] = {0, 0x80000000, 0x7f800000, 0xff800000, 0x7fc00000, 0xffc00000,
    0x7fa00001, 0x7f800001, 1, 0x80000001, 0x007fffff, 0x00800000, 0x7f7fffff, 0xff7fffff, 0x3f800000,
    0xbf800000, 0x3f000000, 0x00400000, 0x5f800000, 0x1f800000, 0x7e800000, 0x20000000};
static float special(void) { return fb(specials[rnd() % (sizeof specials / 4)]); }
static unsigned short game_cw = 0x007f;
static void game_modes(void) { __asm__ volatile("fninit\n fldcw %0" : : "m"(game_cw)); _mm_setcsr(0x1f80); }

static int fails;
static double exh_frac = 1;   /* dev runs: only this fraction of the exhaustive ranges */
static uint32_t mode_cw = 0x007f, mode_mx = 0x1f80;   /* the state the compared calls start from */
#define HC_INIT(c, fn, n) (hc_init(c, fn, n), (c)->cw = mode_cw, (c)->mxcsr = mode_mx)
static void verdict(int bad, const char *fmt, ...) __attribute__((format(printf, 2, 3)));
static int quiet;                                   /* [5]: only failures and the summary */
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt);
    if (bad || !quiet) vprintf(fmt, ap);
    va_end(ap);
    fails += bad != 0;
}

/* ---- [1] mat2quat -------------------------------------------------------------------------- */
static void rot(float m[12], double scale_lo, double scale_hi)
{
    double q[4], l = 0;
    for (int k = 0; k < 4; k++) { q[k] = rf(-1, 1); l += q[k] * q[k]; }
    l = sqrt(l); if (l == 0) { q[3] = 1; l = 1; }
    for (int k = 0; k < 4; k++) q[k] /= l;
    double x = q[0], y = q[1], z = q[2], w = q[3];
    double r[9] = {1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
                   2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
                   2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)};
    for (int c = 0; c < 3; c++) {
        double s = scale_lo == scale_hi ? scale_lo : scale_lo + (scale_hi - scale_lo) * rf(0, 1);
        for (int rr = 0; rr < 3; rr++) m[4 * rr + c] = (float)(r[3 * rr + c] * s);
    }
}
static void gen_matrix(float m[12], int kind)
{
    static const int diag[3] = {0, 5, 10};
    switch (kind) {
    case 0: rot(m, 1, 1); break;
    case 1: rot(m, 0.01, 100); break;
    case 2: for (int k = 0; k < 12; k++) m[k] = rf(-2, 2); break;
    case 3: for (int k = 0; k < 12; k++) m[k] = wide(-70, 70); break;
    case 4: for (int k = 0; k < 12; k++) m[k] = fb(rnd()); break;
    case 5: rot(m, 1, 1); for (int n = 1 + rnd() % 3; n; n--) m[rnd() % 12] = special(); break;
    case 6: {   /* near 180 degrees (trace near -1) and trace near 0: the second path's branches */
        rot(m, 1, 1);
        int i = rnd() % 3; float a = rf(-1, 1), b = rf(-1, 1);
        m[diag[i]] = a; m[diag[(i + 1) % 3]] = b; m[diag[(i + 2) % 3]] = rnd() & 1 ? -(a + b) : -1 - a - b;
        break; }
    default: for (int k = 0; k < 12; k++) m[k] = wide(-149, 127); break;   /* over/underflow */
    }
    m[3] = rf(-1000, 1000); m[7] = rf(-1000, 1000); m[11] = rf(-1000, 1000);
}
static void test_mat2quat(void *orig, void *repl, double millions)
{
    uint64_t n = 0, bad = 0, total = (uint64_t)(millions * 1e6), x87 = gp_lm_count(1, LM_M2Q), pos_tr = 0;
    static float live[24], buf[2][24];
    for (uint64_t it = 0; it < total; it++) {
        float m[12]; gen_matrix(m, rnd() % 8);
        pos_tr += _mm_comigt_ss(_mm_add_ss(_mm_add_ss(_mm_set_ss(m[5]), _mm_set_ss(m[0])), _mm_set_ss(m[10])), _mm_setzero_ps());
        int alias = rnd() % 16 == 0, oidx = alias ? 4 + rnd() % 4 : 18;
        hc_t c[2];
        for (int v = 0; v < 2; v++) {
            for (int k = 0; k < 24; k++) live[k] = fb(0x7fc00000u + k);
            memcpy(&live[4], m, sizeof m);
            HC_INIT(&c[v], (uint32_t)(uintptr_t)(v ? repl : orig), 2);
            c[v].args[0] = (uint32_t)(uintptr_t)&live[oidx]; c[v].args[1] = (uint32_t)(uintptr_t)&live[4];
            hc_call(&c[v]);
            memcpy(buf[v], live, sizeof live);
        }
        game_modes();
        const char *d = hc_diff(&c[0], &c[1], 0, 0);
        if (!*d && memcmp(buf[0], buf[1], sizeof buf[0])) d = "output / matrix memory";
        n++;
        if (*d) { if (bad++ < 5) printf("  MISMATCH (%s) m = %08x %08x %08x | %08x %08x %08x | %08x %08x %08x\n", d,
            bf(m[0]), bf(m[1]), bf(m[2]), bf(m[4]), bf(m[5]), bf(m[6]), bf(m[8]), bf(m[9]), bf(m[10])); }
    }
    verdict(bad, "[1] mat2quat: %llu matrices (%llu with trace > 0), %llu mismatches (full state, quaternion, "
            "argument slots, out == m aliasing 1/16); %ld ran the x87 original\n", n, pos_tr, bad,
            gp_lm_count(1, LM_M2Q) - (LONG)x87);
}

/* ---- [2] distcalc ------------------------------------------------------------------------- */
static void gen_dist(float p[3], float pos[3], float *r, int kind)
{
    for (int k = 0; k < 3; k++) { p[k] = rf(0, 6000); pos[k] = p[k] + rf(-400, 400); }
    *r = rf(0, 300);
    switch (kind) {
    case 1: for (int k = 0; k < 3; k++) pos[k] = rnd() & 1 ? p[k] : p[k] + rf(-1e-3f, 1e-3f);
            *r = rnd() & 1 ? 0 : rf(0, 50); break;
    case 2: for (int k = 0; k < 3; k++) { p[k] = wide(-40, 40); pos[k] = wide(-40, 40); } *r = wide(-40, 40); break;
    case 3: for (int k = 0; k < 3; k++) { p[k] = fb(rnd()); pos[k] = fb(rnd()); } *r = fb(rnd()); break;
    case 4: for (int n = 1 + rnd() % 2; n; n--) { int k = rnd() % 7; *(k < 3 ? &p[k] : k < 6 ? &pos[k - 3] : r) = special(); } break;
    case 5: for (int k = 0; k < 3; k++) { p[k] = wide(55, 127); pos[k] = wide(55, 127); } break;
    case 6: for (int k = 0; k < 3; k++) { p[k] = wide(-149, -55); pos[k] = wide(-149, -55); } *r = wide(-149, -60); break;
    default: break;
    }
}
static void test_dist(void *oc, void *rc, void *ob, void *rb, double millions)
{
    static mobj_t lo, o[2]; static float lp[8], pb[2][8];
    uint64_t n = 0, bad[2] = {0, 0}, total = (uint64_t)(millions * 1e6), inside = 0;
    LONG x0 = gp_lm_count(1, LM_DCC), x1 = gp_lm_count(1, LM_DCB);
    for (uint64_t it = 0; it < total; it++) {
        float p[3], pos[3], r; gen_dist(p, pos, &r, rnd() % 8);
        uint32_t third = rnd();
        for (int which = 0; which < 2; which++) {
            hc_t c[2]; uint32_t seq[2];
            for (int v = 0; v < 2; v++) {
                memset(&lo, 0xa5, sizeof lo); lo.vt = vtab;
                memcpy(lo.pos, pos, 12); memcpy(lo.geom + 16, &r, 4);
                for (int k = 0; k < 8; k++) lp[k] = fb(0x7fc00000u + k);
                memcpy(&lp[2], p, 12);
                HC_INIT(&c[v], (uint32_t)(uintptr_t)(which ? (v ? rb : ob) : (v ? rc : oc)), 3);
                c[v].args[0] = (uint32_t)(uintptr_t)&lp[2]; c[v].args[1] = (uint32_t)(uintptr_t)&lo;
                c[v].args[2] = third;
                mk_seq = 0; hc_call(&c[v]); seq[v] = mk_seq;
                o[v] = lo; memcpy(pb[v], lp, sizeof lp);
            }
            game_modes();
            if (which && (c[0].fpu[28 + 9] & 0x80)) inside++;        /* negative result: d < 0 */
            /* 0xa3ae50 leaves the FPU status word in ax (its sign test); only reachable through
             * the distance-proc table, so its callers cannot use eax */
            const char *d = hc_diff(&c[0], &c[1], which ? 1 : 0, 0);
            if (!*d && memcmp(&o[0], &o[1], sizeof o[0])) d = "object memory";
            if (!*d && memcmp(pb[0], pb[1], sizeof pb[0])) d = "position memory";
            if (!*d && seq[0] != seq[1]) d = "getter call sequence";
            if (*d && bad[which]++ < 5)
                printf("  MISMATCH %s (%s) p = %08x %08x pos = %08x %08x r = %08x\n", which ? "circle" : "centre", d,
                       bf(p[0]), bf(p[1]), bf(pos[0]), bf(pos[1]), bf(r));
        }
        n++;
    }
    verdict(bad[0] + bad[1], "[2] distcalc: %llu inputs; centre 2D %llu mismatches (%ld ran x87), bounding circle 2D "
            "%llu mismatches (%ld ran x87, %llu inside the circle); getter calls, argument slots, full state compared\n",
            n, bad[0], gp_lm_count(1, LM_DCC) - x0, bad[1], gp_lm_count(1, LM_DCB) - x1, inside);
}

/* ---- [3] bsphere -------------------------------------------------------------------------- */
typedef struct { uint64_t lo, hi, bad, top; uint32_t first; } sqjob_t;
static DWORD WINAPI sq_job(LPVOID arg)
{
    sqjob_t *j = arg;
    game_modes();
    for (uint64_t i = j->lo; i < j->hi; i++) {
        uint32_t a = call_sq(NULL, (uint32_t)i), b = call_sq((void *)gp_bsph, (uint32_t)i);
        if (a != b) { if (!j->bad++) j->first = (uint32_t)i; }
        if (!(i & 0xfff)) { unsigned short sw; __asm__ volatile("fnstsw %0" : "=m"(sw)); j->top += (sw >> 11 & 7) != 0; }
    }
    return 0;
}
static void test_bsphere(void *orig, void *repl, double millions, int nthreads)
{
    sqjob_t jobs[64]; HANDLE th[64]; uint64_t t0 = now_us(), bad = 0, top = 0;
    if (nthreads) {
    for (int i = 0; i < nthreads; i++) {
        memset(&jobs[i], 0, sizeof jobs[i]);
        jobs[i].lo = (uint64_t)(exh_frac * 0x100000000ull) * i / nthreads; jobs[i].hi = (uint64_t)(exh_frac * 0x100000000ull) * (i + 1) / nthreads;
        th[i] = CreateThread(NULL, 0, sq_job, &jobs[i], 0, NULL);
    }
    WaitForMultipleObjects(nthreads, th, TRUE, INFINITE);
    for (int i = 0; i < nthreads; i++) {
        bad += jobs[i].bad; top += jobs[i].top;
        if (jobs[i].bad) printf("  MISMATCH r2 = %08x\n", jobs[i].first);
    }
    verdict(bad + top, "[3] bsphere sqrt: %s2^32 inputs, %llu mismatches, %llu x87 stack leaks  [%.0f s, %d threads]\n",
            exh_frac < 1 ? "PART OF " : "all ", bad, top, (now_us() - t0) / 1e6, nthreads);
    }
    static mobj_t lo, o[2]; static float lout[8], out[2][8];
    uint64_t n = 0, bad2 = 0, total = (uint64_t)(millions * 1e6);
    for (uint64_t it = 0; it < total; it++) {
        float box[6]; int kind = rnd() % 4;
        for (int k = 0; k < 6; k++)
            box[k] = kind == 0 ? (k < 3 ? rf(-5000, 5000) : rf(0, 200)) : kind == 1 ? wide(-75, 70) :
                     kind == 2 ? fb(rnd()) : (rnd() & 1 ? special() : rf(-100, 100));
        hc_t c[2]; uint32_t seq[2];
        for (int v = 0; v < 2; v++) {
            memset(&lo, 0xa5, sizeof lo); lo.vt = vtab; memcpy(lo.box, box, sizeof box);
            for (int k = 0; k < 8; k++) lout[k] = fb(0x7fc00000u + k);
            HC_INIT(&c[v], (uint32_t)(uintptr_t)(v ? repl : orig), 1);
            c[v].in[2] = (uint32_t)(uintptr_t)&lo; c[v].args[0] = (uint32_t)(uintptr_t)&lout[2];
            mk_seq = 0; hc_call(&c[v]); seq[v] = mk_seq;
            o[v] = lo; memcpy(out[v], lout, sizeof lout);
        }
        game_modes();
        const char *d = hc_diff(&c[0], &c[1], 0, 0);
        if (!*d && (memcmp(out[0], out[1], sizeof out[0]) || memcmp(&o[0], &o[1], sizeof o[0]))) d = "sphere / object memory";
        if (!*d && seq[0] != seq[1]) d = "getter call sequence";
        n++;
        if (*d && bad2++ < 5) printf("  MISMATCH (%s) extents %08x %08x %08x\n", d, bf(box[3]), bf(box[4]), bf(box[5]));
    }
    verdict(bad2, "[3] bsphere 0x59bc50 with a mock box: %llu calls, %llu mismatches (full state, sphere)\n", n, bad2);
}

/* ---- [4] worldcell ------------------------------------------------------------------------ */
static void *wc_orig;
typedef struct { uint64_t lo, hi, bad; uint32_t first; } wcjob_t;
static DWORD WINAPI wc_job(LPVOID arg)
{
    wcjob_t *j = arg;
    game_modes();
    for (uint64_t i = j->lo; i < j->hi; i++) {
        float p[3] = {fb((uint32_t)i), fb((uint32_t)i), 1.0f};   /* x and y: the same input */
        for (uint32_t exact = 0; exact < 2; exact++) {
            int32_t a[2] = {0x55555555, 0x55555555}, b[2] = {0x55555555, 0x55555555};
            uint32_t sa = call_wc(wc_orig, a, exact, p), sb = call_wc((void *)gp_wcell, b, exact, p);
            if (sa != sb || memcmp(a, b, 8)) { if (!j->bad++) j->first = (uint32_t)i; }
        }
    }
    return 0;
}
static float gen_coord(void)
{
    switch (rnd() % 8) {
    case 0: case 1: return rf(-500, 10000);
    case 2: { float v = (float)((int)(rnd() % 2000) - 100) * 10.0f; uint32_t u = bf(v) + (rnd() % 7) - 3;
              return rnd() & 1 ? fb(u) : v - 5.0f; }          /* on and next to cell edges */
    case 3: return fb(rnd());
    case 4: return special();
    case 5: return wide(-149, -100);                         /* products below FLT_MIN */
    case 6: return wide(20, 127);
    default: return rf(-3, 3);
    }
}
static void test_worldcell(void *orig, void *repl, double millions, int nthreads, int crt)
{
    static int32_t lout[6], out[2][6]; static float lp[6], pb[2][6];
    static const uint32_t flags[] = {0, 1, 0x100, 0xff, 0x12345601};
    uint64_t n = 0, bad = 0, total = (uint64_t)(millions * 1e6);
    LONG x0 = gp_lm_count(1, LM_WCELL);
    for (uint64_t it = 0; it < total; it++) {
        float p[3] = {gen_coord(), gen_coord(), gen_coord()};
        uint32_t flag = flags[rnd() % 5];
        hc_t c[2];
        for (int v = 0; v < 2; v++) {
            for (int k = 0; k < 6; k++) { lout[k] = 0x33333333 + k; lp[k] = fb(0x7fc00000u + k); }
            memcpy(&lp[1], p, 12);
            HC_INIT(&c[v], (uint32_t)(uintptr_t)(v ? repl : orig), 3);
            c[v].args[0] = (uint32_t)(uintptr_t)&lout[2]; c[v].args[1] = flag;
            c[v].args[2] = (uint32_t)(uintptr_t)&lp[1];
            hc_call(&c[v]);
            memcpy(out[v], lout, sizeof lout); memcpy(pb[v], lp, sizeof lp);
        }
        game_modes();
        /* edx, and xmm0-7 whenever the CRT's floor runs (floor patch off, or gp_floor passing it a
         * zero, infinity or NaN): what that external function left there */
        int crt_runs = crt;
        for (int k = 0; k < 2; k++) {
            float v = p[k] * 0.1f + ((uint8_t)flag ? 0.0f : 0.5f);
            crt_runs |= v == 0 || isinf(v) || isnan(v) || fabsf(p[k]) < 1e-30f;
        }
        const char *d = hc_diff(&c[0], &c[1], 1 << 3, crt_runs ? 0xff : 0);
        if (!*d && (memcmp(out[0], out[1], sizeof out[0]) || memcmp(pb[0], pb[1], sizeof pb[0]))) d = "cell / position memory";
        n++;
        if (*d && bad++ < 5) printf("  MISMATCH (%s) p = %08x %08x flag %x\n", d, bf(p[0]), bf(p[1]), flag);
    }
    verdict(bad, "[4] worldcell, IAT floor = %s: %llu random positions, %llu mismatches (full state%s, cells, argument "
            "slot); %ld ran x87\n", crt ? "msvcr71" : "gp_floor", n, bad, crt ? " but edx, xmm" : " but edx, xmm when msvcr71's floor ran", gp_lm_count(1, LM_WCELL) - x0);
    if (!nthreads) return;
    wc_orig = orig;
    wcjob_t jobs[64]; HANDLE th[64]; uint64_t t0 = now_us(); bad = 0;
    for (int i = 0; i < nthreads; i++) {
        memset(&jobs[i], 0, sizeof jobs[i]);
        jobs[i].lo = (uint64_t)(exh_frac * 0x100000000ull) * i / nthreads; jobs[i].hi = (uint64_t)(exh_frac * 0x100000000ull) * (i + 1) / nthreads;
        th[i] = CreateThread(NULL, 0, wc_job, &jobs[i], 0, NULL);
    }
    WaitForMultipleObjects(nthreads, th, TRUE, INFINITE);
    for (int i = 0; i < nthreads; i++) {
        bad += jobs[i].bad;
        if (jobs[i].bad) printf("  MISMATCH x = %08x\n", jobs[i].first);
    }
    verdict(bad, "[4] worldcell: %s2^32 coordinate values x both flags, %llu mismatches (cells, argument slot)  "
            "[%.0f s, %d threads]\n", exh_frac < 1 ? "PART OF " : "all ", bad, (now_us() - t0) / 1e6, nthreads);
}

/* ---- [6] speed ---------------------------------------------------------------------------- */
typedef void (*m2q_fn)(float *, const float *);
typedef float (*dist_fn)(const float *, void *, int);
static void speed(void *const fn[5][2])
{
    const int N = 1000000; double ns[6][2];
    float mA[12], mB[12], q[4], p[3] = {1000, 2000, 0}; static mobj_t o; int32_t cell[2];
    rot(mA, 1, 1); mA[0] = mA[5] = mA[10] = 0.9f;                  /* trace > 0 */
    rot(mB, 1, 1); mB[0] = 0.5f; mB[5] = -0.6f; mB[10] = -0.7f;    /* the largest-diagonal path */
    o.vt = vtab; o.pos[0] = 1100; o.pos[1] = 1900; memcpy(o.geom + 16, &(float){30}, 4);
    for (int k = 0; k < 6; k++) o.box[k] = 10 + k;
    for (int v = 0; v < 2; v++) {
        uint64_t t[7]; t[0] = now_us();
        for (int i = 0; i < N; i++) ((m2q_fn)fn[0][v])(q, mA);
        t[1] = now_us();
        for (int i = 0; i < N; i++) ((m2q_fn)fn[0][v])(q, mB);
        t[2] = now_us();
        for (int i = 0; i < N; i++) ((dist_fn)fn[1][v])(p, &o, 0);
        t[3] = now_us();
        for (int i = 0; i < N; i++) ((dist_fn)fn[2][v])(p, &o, 0);
        t[4] = now_us();
        for (int i = 0; i < N; i++) call_this1(fn[3][v], &o, q);
        t[5] = now_us();
        for (int i = 0; i < N; i++) call_wc(fn[4][v], cell, i & 1, p);
        t[6] = now_us();
        for (int k = 0; k < 6; k++) ns[k][v] = (t[k + 1] - t[k]) * 1000.0 / N;
    }
    static const char *name[6] = {"mat2quat (trace > 0)", "mat2quat (other path)", "distcalc centre 2D",
                                   "distcalc circle 2D", "0x59bc50 bounding sphere", "worldcell"};
    for (int k = 0; k < 6; k++)
        printf("[6] %-26s original %6.1f ns, replacement %6.1f ns per call (incl. mock getters)\n", name[k], ns[k][0], ns[k][1]);
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    double millions = argc > 2 ? atof(argv[2]) : 10;
    int nthreads = argc > 3 ? atoi(argv[3]) : 16;
    if (argc > 4) exh_frac = atof(argv[4]);
    static const struct { uint32_t va, len; uint64_t fnv; } fn[5] = {{0xb2bd10, 0x168, GP_FNV_B2BD10},
        {0xa3a7a0, 0x26, GP_FNV_A3A7A0}, {0xa3ae50, 0x53, GP_FNV_A3AE50}, {0x59bc50, 0x82, GP_FNV_59BC50},
        {0x6e8ce6, 0xa2, GP_FNV_6E8CE6}};
    for (int i = 0; i < 5; i++)
        if (gp_fnv1a(orig_bytes(fn[i].va, fn[i].len), fn[i].len) != fn[i].fnv) { printf("code at %08x differs\n", fn[i].va); return 2; }
    static const uint32_t data[][2] = {{0xbd0000, 0x9000}, {0xc1b000, 0x1000}, {0xdc3000, 0x1000}};
    static const uint32_t code[][2] = {{0xb2b000, 0x1000}, {0xa3a000, 0x1000}, {0x59b000, 0x1000}, {0x6e8000, 0x1000}};
    for (int i = 0; i < 3; i++) if (orig_map_at(data[i][0], data[i][1], 0)) return 2;   /* what the code reads */
    uint32_t off = orig_reserve_image();
    if (!off) return 2;
    for (int i = 0; i < 3; i++) if (orig_map_at(data[i][0], data[i][1], off)) return 2;
    for (int i = 0; i < 4; i++) if (orig_map_at(code[i][0], code[i][1], off)) return 2;
    void *crt_floor = GetProcAddress(LoadLibraryA("msvcr71.dll"), "floor");
    *(void **)0xbd0580 = crt_floor;                 /* what the loader writes (floor patch off) */
    gp_va_offset = off;
    int ok = gp_patch_mat2quat() + gp_patch_distcalc() + gp_patch_bsphere() + gp_patch_worldcell();
    gp_va_offset = 0;
    verdict(ok != 4, "[0] %d of 4 patches applied to the original bytes (relocated copy)\n", ok);
    if (ok != 4) { printf("FAIL\n"); return 1; }
    void *f[5][2];
    for (int i = 0; i < 5; i++) { f[i][0] = orig_copy(fn[i].va, fn[i].len, 0); f[i][1] = (void *)(uintptr_t)(fn[i].va + off); }
    vtab[0] = (void *)mk_geom; vtab[1] = (void *)mk_pos; vtab[0x110 / 4] = (void *)mk_box;
    gp_lm_period_ms = 5000;
    game_modes();

    test_mat2quat(f[0][0], f[0][1], millions);
    test_dist(f[1][0], f[1][1], f[2][0], f[2][1], millions);
    test_bsphere(f[3][0], f[3][1], millions, nthreads);
    test_worldcell(f[4][0], f[4][1], millions, 0, 1);
    gp_floor_orig = (uint32_t)(uintptr_t)crt_floor;
    *(void **)0xbd0580 = (void *)gp_floor;          /* the floor patch (default on) */
    test_worldcell(f[4][0], f[4][1], millions, nthreads, 0);

    static const struct { uint32_t cw, mx; const char *name; } modes[] = {
        {0x027f, 0x1f80, "PC_53"}, {0x037f, 0x1f80, "PC_64"}, {0x047f, 0x1f80, "PC_24 RC down"},
        {0x0c7f, 0x1f80, "PC_24 RC chop"}, {0x087f, 0x1f80, "PC_24 RC up"}, {0x007f, 0x5f80, "MXCSR RC down"},
        {0x007f, 0x9fc0, "MXCSR FTZ+DAZ"}};
    for (unsigned m = 0; m < sizeof modes / sizeof modes[0]; m++) {
        LONG c0 = 0, x0 = 0;
        for (int i = 0; i < LM_N; i++) { c0 += gp_lm_count(0, i); x0 += gp_lm_count(1, i); }
        mode_cw = modes[m].cw; mode_mx = modes[m].mx; quiet = 1;
        int f0 = fails;
        test_mat2quat(f[0][0], f[0][1], 0.1);
        test_dist(f[1][0], f[1][1], f[2][0], f[2][1], 0.1);
        test_bsphere(f[3][0], f[3][1], 0.1, 0);
        test_worldcell(f[4][0], f[4][1], 0.1, 0, 0);
        quiet = 0;
        LONG c1 = 0, x1 = 0;
        for (int i = 0; i < LM_N; i++) { c1 += gp_lm_count(0, i); x1 += gp_lm_count(1, i); }
        verdict(c1 - c0 != x1 - x0, "[5] %-14s %ld calls of the five entries (0.1 M inputs each, full state compared): "
                "%ld ran the x87 original, %s\n", modes[m].name, c1 - c0, x1 - x0, fails == f0 ? "0 mismatches" : "MISMATCHES above");
    }
    mode_cw = 0x007f; mode_mx = 0x1f80;
    game_modes();
    speed((void *const (*)[2])f);
    gp_logic_exit_log();
    printf("%s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
