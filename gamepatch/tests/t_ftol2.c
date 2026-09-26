/* t_ftol2: gp_ftol2 (p_ftol2.S, replacing the CRT's x87 _ftol2 at 0xa3cfa4) against the original
 * bytes of the exe, both entered with the value in st0: edx:eax, ecx (which the original changes
 * on one path and not on the other), ebx esi edi ebp, the x87 status word's stack top and the
 * control word are compared after each call.
 *   [0] the patch applies to the original bytes (relocated copy)
 *   [1] every float (all 2^32 bit patterns, loaded exactly as the game's fld dword does)
 *   [2] random doubles: all bit patterns, near-integers, halves, large magnitudes
 *   [3] random 80-bit values: 64-bit significands, int64 values, +-0.5 offsets, specials,
 *       unnormals, pseudo-denormals
 *   [4] other x87 modes (the original runs)
 *   [5] time per call
 * usage: t_ftol2.exe <path to lotrbfme2ep1.exe 2.02> [millions per random test] [threads] */
#include "orig.h"
#include "gp_logic.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct { uint32_t eax, edx, ecx, ebx, esi, edi, ebp; uint16_t sw, cw; } fr_t;
__asm__(".text\n"
"_call_ftol:\n"                 /* cdecl (fn, const void *x80, fr_t *out, uint32_t ecx, uint32_t cw) */
"  pushl %ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n"
"  fninit\n  fldcw 36(%esp)\n"
"  movl 24(%esp), %eax\n  fldt (%eax)\n"
"  movl 20(%esp), %eax\n  movl 32(%esp), %ecx\n"
"  movl $0x22222222, %ebx\n  movl $0x55555555, %esi\n  movl $0x66666666, %edi\n  movl $0x77777777, %ebp\n"
"  call *%eax\n"
"  pushl %eax\n  movl 32(%esp), %eax\n  popl (%eax)\n"
"  movl %edx, 4(%eax)\n  movl %ecx, 8(%eax)\n  movl %ebx, 12(%eax)\n  movl %esi, 16(%eax)\n"
"  movl %edi, 20(%eax)\n  movl %ebp, 24(%eax)\n  fnstsw 28(%eax)\n  fnstcw 30(%eax)\n"
"  fninit\n  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n");
void call_ftol(void *fn, const void *x80, fr_t *out, uint32_t ecx, uint32_t cw);
__asm__(".text\n_ft_pop:\n  fstp %st(0)\n  ret\n");
void ft_pop(void);

static void *orig_fn;
static uint32_t game_cw = 0x007f;
typedef struct { uint8_t b[10]; } x80_t;
static x80_t from_ld(long double v) { x80_t x; memcpy(x.b, &v, 10); return x; }
static x80_t make80(uint64_t m, unsigned se) { x80_t x; memcpy(x.b, &m, 8); x.b[8] = se & 0xff; x.b[9] = se >> 8; return x; }

/* 1 = identical (registers, stack top, control word) */
static int same(const x80_t *x, uint32_t ecx, uint32_t cw, fr_t *a, fr_t *b)
{
    call_ftol(orig_fn, x, a, ecx, cw);
    call_ftol((void *)gp_ftol2, x, b, ecx, cw);
    return !memcmp(a, b, 28) && (a->sw & 0x3800) == (b->sw & 0x3800) && a->cw == b->cw;
}

static uint32_t rng = 4242;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static uint64_t rnd64(void) { return (uint64_t)rnd() << 32 | rnd(); }

typedef struct { uint64_t lo, hi, bad, ecx_kept; uint32_t first; } job_t;
static DWORD WINAPI floats(LPVOID p)
{
    job_t *j = p;
    for (uint64_t i = j->lo; i < j->hi; i++) {
        union { uint32_t u; float f; } c = { (uint32_t)i };
        x80_t x = from_ld((long double)c.f);
        fr_t a, b;
        if (!same(&x, 0x33333333u ^ (uint32_t)i, game_cw, &a, &b)) { if (!j->bad++) j->first = (uint32_t)i; }
        j->ecx_kept += a.ecx == (0x33333333u ^ (uint32_t)i);
    }
    return 0;
}

static void report(const char *what, uint64_t n, uint64_t bad, const x80_t *first)
{
    printf("%s: %llu values, %llu mismatches", what, n, bad);
    if (bad) printf(" (first: %02x%02x %02x%02x%02x%02x%02x%02x%02x%02x)", first->b[9], first->b[8], first->b[7],
                    first->b[6], first->b[5], first->b[4], first->b[3], first->b[2], first->b[1], first->b[0]);
    printf("\n");
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    double millions = argc > 2 ? atof(argv[2]) : 50;
    int nthreads = argc > 3 ? atoi(argv[3]) : 16;
    double frac = argc > 4 ? atof(argv[4]) : 1;           /* dev runs: part of [1] only */
    if (gp_fnv1a(orig_bytes(0xa3cfa4, 0x75), 0x75) != GP_FNV_A3CFA4) { printf("_ftol2 differs\n"); return 2; }
    uint32_t off = orig_reserve_image();
    if (!off || orig_map_at(0xa3c000, 0x2000, off)) return 2;
    gp_va_offset = off;
    int ok = gp_patch_ftol2();
    gp_va_offset = 0;
    printf("[0] %d of 1 patch applied to the original bytes (relocated copy)\n", ok);
    if (!ok) { printf("FAIL\n"); return 1; }
    orig_fn = orig_copy(0xa3cfa4, 0x75, 0);
    int fail = 0;

    /* [1] all floats */
    uint64_t t0 = now_us(), bad = 0, kept = 0, total = (uint64_t)(frac * 4294967296.0);
    job_t jobs[64]; HANDLE th[64];
    for (int i = 0; i < nthreads; i++) {
        memset(&jobs[i], 0, sizeof jobs[i]);
        jobs[i].lo = total * i / nthreads; jobs[i].hi = total * (i + 1) / nthreads;
        th[i] = CreateThread(NULL, 0, floats, &jobs[i], 0, NULL);
    }
    WaitForMultipleObjects(nthreads, th, TRUE, INFINITE);
    for (int i = 0; i < nthreads; i++) {
        bad += jobs[i].bad; kept += jobs[i].ecx_kept;
        if (jobs[i].bad) printf("  MISMATCH float %08x\n", jobs[i].first);
    }
    printf("[1] %s2^32 floats: %llu mismatches (%llu returned at once with ecx untouched)  [%.0f s, %d threads]\n",
           frac < 1 ? "PART OF " : "all ", bad, kept, (now_us() - t0) / 1e6, nthreads);
    fail |= bad != 0;

    /* [2] doubles, [3] 80-bit values */
    uint64_t n = (uint64_t)(millions * 1e6);
    for (int part = 2; part <= 3; part++) {
        uint64_t b = 0; x80_t firstbad = {{0}};
        for (uint64_t i = 0; i < n; i++) {
            x80_t x; int k = rnd() % 8;
            if (part == 2) {
                union { uint64_t u; double d; } c;
                if (k < 3) c.u = rnd64();                                             /* any double */
                else {
                    if (k == 3) c.d = ldexp(1.0 + (double)(rnd() >> 4) / 268435456.0, rnd() % 64);
                    else if (k == 4) c.d = (double)(rnd64() >> (rnd() % 64));          /* integers */
                    else if (k == 5) c.d = (double)(rnd64() >> (12 + rnd() % 52)) + 0.5; /* halves */
                    else if (k == 6) c.d = ldexp((double)(rnd64() >> 11), -(int)(rnd() % 80));
                    else { c.d = (double)(rnd64() >> (rnd() % 64)); c.u += (int)(rnd() % 5) - 2; }
                    if (rnd() & 1) c.u |= 1ull << 63;
                }
                x = from_ld((long double)c.d);
            } else {
                uint64_t m = rnd64();
                unsigned e = 16383 + (int)(rnd() % 140) - 70;
                switch (k) {
                case 0: m |= 1ull << 63; break;                                        /* normal */
                case 1: { int64_t v = (int64_t)rnd64() >> (rnd() % 64);                 /* int64, exact */
                          x = from_ld((long double)v + (rnd() & 1 ? 0.5L : (rnd() & 1) ? -0.5L : 0.0L));
                          goto have; }
                case 2: m |= 1ull << 63; e = 16383 + 60 + rnd() % 6; break;             /* around 2^63 */
                case 3: m = rnd() % 2 ? ~0ull : 1ull << 63; e = 16383 + 62 + rnd() % 2; break;
                case 4: e = rnd() % 2 ? 0 : 0x7fff; if (e) m |= 1ull << 63; break;       /* denormal/zero, inf/NaN */
                case 5: m &= ~(1ull << 63); break;                                      /* unnormal */
                case 6: m = (1ull << 63) | (rnd64() & (rnd() % 2 ? 0 : 0xffff)); e = 16383 - 1 + rnd() % 3; break;
                default: m |= 1ull << 63; e = 16383 + (int)(rnd() % 8) - 3; break;      /* |x| near 1 */
                }
                if (rnd() & 1) e |= 0x8000;
                x = make80(m, e);
            }
        have:;
            fr_t ra, rb;
            if (!same(&x, rnd(), game_cw, &ra, &rb)) { if (!b++) firstbad = x; }
        }
        report(part == 2 ? "[2] random doubles" : "[3] random 80-bit values", n, b, &firstbad);
        fail |= b != 0;
    }

    /* [4] other modes */
    static const struct { uint32_t cw; const char *name; } modes[] = {{0x027f, "PC_53"}, {0x037f, "PC_64"},
        {0x047f, "PC_24 RC down"}, {0x087f, "PC_24 RC up"}, {0x0c7f, "PC_24 RC chop"}, {0x0f7f, "PC_64 RC chop"}};
    for (unsigned m = 0; m < sizeof modes / sizeof modes[0]; m++) {
        uint64_t b = 0, cnt = 1000000; LONG x0 = 0, x1 = 0; x80_t firstbad = {{0}};
        for (int i = 0; i < 16; i++) x0 += gp_ftol2_calls[i][1];
        for (uint64_t i = 0; i < cnt; i++) {
            union { uint64_t u; double d; } c = { rnd64() >> (rnd() % 12) };
            if (i & 1) c.d = (double)(int)rnd() / 256.0;
            x80_t x = from_ld((long double)c.d); fr_t ra, rb;
            if (!same(&x, rnd(), modes[m].cw, &ra, &rb)) { if (!b++) firstbad = x; }
        }
        for (int i = 0; i < 16; i++) x1 += gp_ftol2_calls[i][1];
        char what[64]; snprintf(what, sizeof what, "[4] %s (%ld ran the original)", modes[m].name, x1 - x0);
        report(what, cnt, b, &firstbad);
        fail |= b != 0 || (uint64_t)(x1 - x0) != cnt;
    }

    /* [5] speed */
    {
        const int N = 2000000; fr_t r; double ns[2];
        x80_t v[4] = {from_ld(12.75L), from_ld(-3.25L), from_ld(0.3L), from_ld(1234567.0L)};
        for (int k = 0; k < 2; k++) {
            uint64_t s0 = now_us();
            for (int i = 0; i < N; i++) call_ftol(k ? (void *)gp_ftol2 : orig_fn, &v[i & 3], &r, 0, game_cw);
            ns[k] = (now_us() - s0) * 1000.0 / N;
        }
        uint64_t s0 = now_us();
        for (int i = 0; i < N; i++) call_ftol((void *)ft_pop, &v[i & 3], &r, 0, game_cw);
        double base = (now_us() - s0) * 1000.0 / N;
        printf("[5] per call: original %.1f ns, replacement %.1f ns (harness overhead %.1f ns subtracted)\n",
               ns[0] - base, ns[1] - base, base);
    }
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
