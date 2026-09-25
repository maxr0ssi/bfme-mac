/* t_invsqrt: bit-exactness of the invsqrt and normtail patches against the original x87 code.
 *   1. all 2^32 inputs, game FPU mode (PC_24, nearest): original 0x441c56 vs gp_invsqrt, the full
 *      80-bit st0 results compared (the caller keeps computing in x87 with it);
 *   2. the same SSE sequence without the input-range guard, to show where the guard is needed;
 *   3. other x87/SSE modes (fallback must make them identical);
 *   4. the two normalize tails (0x4f1710, 0xb2b875) vs their original bytes, random vectors;
 *   5. speed of one call, original vs replacement.
 * usage: t_invsqrt.exe <path to lotrbfme2ep1.exe 2.02> [threads] */
#include "orig.h"
#include "gp.h"
#include "isqrt_range.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <xmmintrin.h>

void gp_norm_4f1710(void);
void gp_norm_b2b875(void);

__asm__(".text\n"
"_call_f80:\n"            /* cdecl (fn, uint32 x, void *out10): stdcall float -> st0 */
"  movl 4(%esp), %eax\n"
"  pushl 8(%esp)\n"
"  call *%eax\n"
"  movl 12(%esp), %eax\n"
"  fstpt (%eax)\n"
"  ret\n"
"_call_tail3:\n"          /* cdecl (fn, float *v, uint32 len2): esi = v, [ebp+8] = len2 */
"  pushl %ebp\n  pushl %esi\n"
"  movl 12(%esp), %eax\n  movl 16(%esp), %esi\n  movl 20(%esp), %edx\n"
"  subl $12, %esp\n  movl %edx, 8(%esp)\n  movl %esp, %ebp\n"
"  call *%eax\n"
"  addl $12, %esp\n  popl %esi\n  popl %ebp\n  ret\n"
"_call_tail4:\n"          /* cdecl (fn, float *v, uint32 len2): esi = v, eax = len2 */
"  pushl %esi\n"
"  movl 8(%esp), %ecx\n  movl 12(%esp), %esi\n  movl 16(%esp), %eax\n"
"  call *%ecx\n"
"  popl %esi\n  ret\n");
void call_f80(void *fn, uint32_t x, void *out);
void call_tail3(void *fn, float *v, uint32_t len2);
void call_tail4(void *fn, float *v, uint32_t len2);

static void *orig_fn;
static unsigned short game_cw = 0x007f;   /* _fpreset + _controlfp(_PC_24 | _RC_NEAR) */

static void set_modes(unsigned short cw, unsigned mxcsr)
{
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));
    _mm_setcsr(mxcsr);
}
static unsigned fpu_top(void)
{
    unsigned short sw;
    __asm__ volatile("fnstsw %0" : "=m"(sw));
    return (sw >> 11) & 7;
}

/* the SSE sequence with no guard (same operation order as p_invsqrt.S) */
static float unguarded(uint32_t x)
{
    union { uint32_t u; float f; } y = { (0xbe6eb508u - x) >> 1 }, xh = { x - 0x800000u };
    __m128 Y = _mm_set_ss(y.f), H = _mm_set_ss(xh.f), c = _mm_set_ss(1.5f);
    __m128 A = _mm_mul_ss(_mm_mul_ss(Y, Y), H);
    __m128 t = _mm_sub_ss(c, A);
    __m128 B = _mm_mul_ss(_mm_mul_ss(A, t), t);
    __m128 y1 = _mm_mul_ss(Y, t);
    t = _mm_sub_ss(c, B);
    __m128 C = _mm_mul_ss(_mm_mul_ss(B, t), t);
    __m128 y2 = _mm_mul_ss(y1, t);
    return _mm_cvtss_f32(_mm_mul_ss(y2, _mm_sub_ss(c, C)));
}

typedef struct { uint64_t lo, hi; uint64_t bad, bad_ung, ung_in_range, fast; uint32_t first_bad[4];
                 uint32_t ung_min, ung_max; } job_t;

static DWORD WINAPI exhaustive(LPVOID p)
{
    job_t *j = p;
    uint8_t a[16], b[16];
    set_modes(game_cw, 0x1f80);
    j->ung_min = 0xffffffff; j->ung_max = 0;
    for (uint64_t i = j->lo; i < j->hi; i++) {
        uint32_t x = (uint32_t)i;
        call_f80(orig_fn, x, a);
        call_f80((void *)gp_invsqrt, x, b);
        if (memcmp(a, b, 10)) { if (j->bad < 4) j->first_bad[j->bad] = x; j->bad++; }
        long double u = unguarded(x);
        if (memcmp(a, &u, 10)) {
            j->bad_ung++;
            if (x >= GP_ISQRT_LO && x <= GP_ISQRT_HI) j->ung_in_range++;
            if (x < 0x80000000u) { if (x < j->ung_min) j->ung_min = x; if (x > j->ung_max) j->ung_max = x; }
        }
        if (x >= GP_ISQRT_LO && x <= GP_ISQRT_HI) j->fast++;
    }
    return 0;
}

static uint32_t rng = 12345;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static float rnd_float(int emin, int emax)
{
    union { uint32_t u; float f; } c;
    int e = emin + (int)(rnd() % (unsigned)(emax - emin + 1));
    c.u = (rnd() & 0x807fffffu) | ((uint32_t)(e + 127) << 23);
    return c.f;
}
static uint32_t special(void)
{
    static const uint32_t s[] = {0, 0x80000000, 0x7f800000, 0xff800000, 0x7fc00000, 0x7f800001,
                                 0xffc00000, 0x7fbfffff, 1, 0x007fffff, 0x00800000, 0x7f7fffff,
                                 0x3f800000, 0xbf800000, 0x00400000, 0x7e800000, 0x7e7fffff,
                                 GP_ISQRT_HI, GP_ISQRT_HI + 1, GP_ISQRT_LO - 1};
    return rnd() & 1 ? s[rnd() % (sizeof s / 4)] : rnd();
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    int nthreads = argc > 2 ? atoi(argv[2]) : 16;
    const uint8_t *code = orig_bytes(0x441c56, 0x52);
    if (gp_fnv1a(code, 0x52) != GP_FNV_441C56) { printf("invsqrt bytes differ from the expected ones\n"); return 2; }
    orig_fn = orig_copy(0x441c56, 0x52, 0);
    gp_invsqrt_cont = (uint32_t)(uintptr_t)orig_fn + 5;
    gp_invsqrt_fn = (uint32_t)(uintptr_t)orig_fn;
    int fail = 0;

    /* 1 + 2: exhaustive */
    uint64_t t0 = now_us();
    job_t jobs[64]; HANDLE th[64];
    for (int i = 0; i < nthreads; i++) {
        memset(&jobs[i], 0, sizeof jobs[i]);
        jobs[i].lo = (0x100000000ull * i) / nthreads; jobs[i].hi = (0x100000000ull * (i + 1)) / nthreads;
        th[i] = CreateThread(NULL, 0, exhaustive, &jobs[i], 0, NULL);
    }
    WaitForMultipleObjects(nthreads, th, TRUE, INFINITE);
    uint64_t bad = 0, bad_ung = 0, ung_in = 0, fast = 0; uint32_t umin = 0xffffffff, umax = 0;
    for (int i = 0; i < nthreads; i++) {
        bad += jobs[i].bad; bad_ung += jobs[i].bad_ung; ung_in += jobs[i].ung_in_range; fast += jobs[i].fast;
        if (jobs[i].ung_min < umin) umin = jobs[i].ung_min;
        if (jobs[i].ung_max > umax) umax = jobs[i].ung_max;
        for (unsigned k = 0; k < jobs[i].bad && k < 4; k++) printf("  MISMATCH x=%08x\n", jobs[i].first_bad[k]);
    }
    printf("[1] all 2^32 inputs, game mode: %llu mismatches (80-bit st0 compared); %llu inputs (%.1f%%) "
           "take the SSE path  [%.0f s, %d threads]\n", bad, fast, 100.0 * fast / 4294967296.0,
           (now_us() - t0) / 1e6, nthreads);
    printf("[2] unguarded SSE sequence: %llu inputs differ from x87, %llu of them inside the guard range; "
           "positive inputs that differ lie in %08x..%08x\n", bad_ung, ung_in, umin, umax);
    fail |= bad != 0 || ung_in != 0;

    /* 3: other modes (must all fall back) */
    static const struct { unsigned short cw; unsigned mx; const char *name; } modes[] = {
        {0x027f, 0x1f80, "PC_53"}, {0x037f, 0x1f80, "PC_64"}, {0x047f, 0x1f80, "PC_24 RC down"},
        {0x0c7f, 0x1f80, "PC_24 RC chop"}, {0x007f, 0x5f80, "MXCSR RC down"},
        {0x007f, 0x9fc0, "MXCSR FTZ+DAZ"}, {0x007f, 0x1f00, "MXCSR PE unmasked"}};
    for (unsigned m = 0; m < sizeof modes / sizeof modes[0]; m++) {
        uint8_t a[16], b[16]; uint64_t n = 0, d = 0;
        set_modes(modes[m].cw, modes[m].mx);
        for (int i = 0; i < (1 << 22); i++) {
            uint32_t x = i & 1 ? rnd() : (rnd() & 0x3fffffff) + 0x10000000;
            if (modes[m].mx == 0x1f00) x = 0x3f800000;   /* exact input: no precision exception */
            call_f80(orig_fn, x, a); call_f80((void *)gp_invsqrt, x, b);
            n++; d += memcmp(a, b, 10) != 0;
        }
        set_modes(game_cw, 0x1f80);
        printf("[3] %-18s %llu inputs, %llu mismatches\n", modes[m].name, n, d);
        fail |= d != 0;
    }

    /* 4: tails */
    uint8_t *t3 = orig_copy(0x4f1710, 0x20, 1), *t4 = orig_copy(0xb2b875, 0x22, 1);
    orig_fix_rel32(t3, 0x4f1710, 0x4f1717, orig_fn);
    orig_fix_rel32(t4, 0xb2b875, 0xb2b876, orig_fn);
    t3[0x20] = 0xc3; t4[0x22] = 0xc3;
    set_modes(game_cw, 0x1f80);
    for (int which = 3; which <= 4; which++) {
        uint64_t n = 0, d = 0, stack = 0;
        for (int i = 0; i < 4000000; i++) {
            float v[4], a[4], b[4];
            int wide = i % 3 == 0;
            for (int k = 0; k < 4; k++) v[k] = rnd_float(wide ? -149 : -20, wide ? 127 : 20);
            if (i % 7 == 0) v[rnd() % 4] = 0.0f;
            __m128 s = _mm_mul_ss(_mm_set_ss(v[0]), _mm_set_ss(v[0]));
            for (int k = 1; k < which; k++) s = _mm_add_ss(s, _mm_mul_ss(_mm_set_ss(v[k]), _mm_set_ss(v[k])));
            union { float f; uint32_t u; } l = { _mm_cvtss_f32(s) };
            if (i % 11 == 0) l.u = special();
            memcpy(a, v, 16); memcpy(b, v, 16);
            if (which == 3) { call_tail3(t3, a, l.u); call_tail3((void *)gp_norm_4f1710, b, l.u); }
            else            { call_tail4(t4, a, l.u); call_tail4((void *)gp_norm_b2b875, b, l.u); }
            n++; d += memcmp(a, b, 16) != 0; stack += fpu_top() != 0;
            if (memcmp(a, b, 16) && d <= 3)
                printf("  MISMATCH tail%d len2=%08x v0=%08x\n", which, l.u, *(uint32_t *)&v[0]);
        }
        printf("[4] tail 0x%s (%d floats): %llu random vectors, %llu mismatches, %llu x87 stack leaks\n",
               which == 3 ? "4f1710" : "b2b875", which, n, d, stack);
        fail |= d != 0 || stack != 0;
    }

    /* 5: speed */
    {
        uint8_t a[16]; const int N = 2000000;
        uint64_t s0 = now_us();
        for (int i = 0; i < N; i++) call_f80(orig_fn, 0x3f000000 + (i & 0xffffff), a);
        uint64_t s1 = now_us();
        for (int i = 0; i < N; i++) call_f80((void *)gp_invsqrt, 0x3f000000 + (i & 0xffffff), a);
        uint64_t s2 = now_us();
        printf("[5] per call: original %.1f ns, replacement %.1f ns\n", (s1 - s0) * 1000.0 / N, (s2 - s1) * 1000.0 / N);
    }
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
