/* t_particle: particlevtx (gp_ptclvtx replacing the per-vertex colour pack 0x579da0..0x579e22)
 * against the original bytes, run in place: the page is copied from the exe to its address +
 * offset, gp_patch_particlevtx() rewrites it exactly as in the game, and a `ret` is put at the
 * loop's continuation 0x579e23 so both versions can be called with a prepared frame (ebp).
 *   [1] all 2^32 bit patterns as r = g = b = a (the loop clamps to [0,1] first; everything else
 *       must fall back to the x87 original), every register compared: eax ebx ecx edx esi edi,
 *       xmm0-7, x87 control word and stack top, esp; also how often a single-precision
 *       (mulss + cvttss2si) version would have differed, for the record;
 *   [2] 40 M random 4-tuples (unit range, NaNs, -0, denormals, wide values, specials);
 *   [3] 12 x87 control words x 4 MXCSR settings, 2 M tuples each;
 *   [4] a multiplier other than 255 (the fallback), and the time per vertex.
 * usage: t_particle.exe <path to lotrbfme2ep1.exe 2.02> [threads] */
#include "orig.h"
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <xmmintrin.h>

typedef struct { uint32_t r[8]; uint8_t x[8][16]; uint16_t cw, sw; uint32_t pad[3]; } regs_t;
_Static_assert(sizeof(regs_t) == 32 + 128 + 16, "layout");

__asm__(".text\n"
"_run:\n"                              /* cdecl run(fn, ebp value, regs_t *io) */
"  pushl %ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n"
"  movl 20(%esp), %eax\n  movl 24(%esp), %ecx\n  movl 28(%esp), %edx\n"
"  pushl %edx\n  pushl %eax\n"
"  movups 48(%edx), %xmm1\n  movups 64(%edx), %xmm2\n  movups 80(%edx), %xmm3\n  movups 96(%edx), %xmm4\n"
"  movups 112(%edx), %xmm5\n  movups 128(%edx), %xmm6\n  movups 144(%edx), %xmm7\n"
"  movl %ecx, %ebp\n"
"  movss -0xf0(%ebp), %xmm0\n"         /* as the loop leaves it (0x579d8c) */
"  movl 4(%edx), %ebx\n  movl 8(%edx), %ecx\n  movl 16(%edx), %esi\n  movl 20(%edx), %edi\n"
"  movl 0(%edx), %eax\n  movl 12(%edx), %edx\n"
"  call *(%esp)\n"
"  pushl %eax\n  movl 8(%esp), %eax\n  popl (%eax)\n"
"  movl %ebx, 4(%eax)\n  movl %ecx, 8(%eax)\n  movl %edx, 12(%eax)\n  movl %esi, 16(%eax)\n"
"  movl %edi, 20(%eax)\n  movl %esp, 24(%eax)\n"
"  movups %xmm0, 32(%eax)\n  movups %xmm1, 48(%eax)\n  movups %xmm2, 64(%eax)\n  movups %xmm3, 80(%eax)\n"
"  movups %xmm4, 96(%eax)\n  movups %xmm5, 112(%eax)\n  movups %xmm6, 128(%eax)\n  movups %xmm7, 144(%eax)\n"
"  fnstcw 160(%eax)\n  fnstsw 162(%eax)\n"
"  addl $8, %esp\n"
"  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n");
void run(void *fn, void *ebpv, regs_t *io);

static void *orig_fn, *repl_fn;
static uint32_t rng_seed = 99;
static uint32_t rnd(uint32_t *s) { *s ^= *s << 13; *s ^= *s >> 17; *s ^= *s << 5; return *s; }
static float fb(uint32_t u) { union { uint32_t u; float f; } c = { u }; return c.f; }

typedef struct { uint8_t mem[0x200]; float col[4]; } frame_t;
static void setup(frame_t *f, uint32_t r, uint32_t g, uint32_t b, uint32_t a, uint32_t mul)
{
    uint8_t *ebpv = f->mem + 0x1c0;
    memcpy(f->col + 0, &r, 4); memcpy(f->col + 1, &g, 4); memcpy(f->col + 2, &b, 4); memcpy(f->col + 3, &a, 4);
    *(float **)(ebpv - 0x104) = f->col;
    memcpy(ebpv - 0xf4, &mul, 4);
    memcpy(ebpv - 0xf0, &a, 4);
}
static void io_init(regs_t *io)
{
    for (int i = 0; i < 8; i++) io->r[i] = 0x10101010u * (i + 1);
    for (int i = 0; i < 128; i++) ((uint8_t *)io->x)[i] = (uint8_t)(0xa5 ^ i * 29);
}
/* 0 = same: registers, xmm0-7, esp, x87 control word and stack top (status flags may differ) */
static int compare(frame_t *f, uint16_t cw, uint32_t mxcsr, regs_t *a, regs_t *b)
{
    uint8_t *ebpv = f->mem + 0x1c0;
    io_init(a); io_init(b);
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw)); _mm_setcsr(mxcsr);
    run(orig_fn, ebpv, a);
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw)); _mm_setcsr(mxcsr);
    run(repl_fn, ebpv, b);
    return memcmp(a->r, b->r, 28) || memcmp(a->x, b->x, 128) || a->cw != b->cw ||
           ((a->sw ^ b->sw) & 0x3800);
}

typedef struct { uint64_t lo, hi, bad, single_bad; } job_t;
static DWORD WINAPI exhaustive(LPVOID p)
{
    job_t *j = p; frame_t f; regs_t a, b;
    for (uint64_t u = j->lo; u < j->hi; u++) {
        uint32_t v = (uint32_t)u;
        setup(&f, v, v, v, v, 0x437f0000);
        if (compare(&f, 0x007f, 0x1f80, &a, &b)) { if (j->bad++ < 3) printf("  MISMATCH x = %08lx\n", (unsigned long)v); }
        float x = fb(v);
        if (x >= 0.0f && x <= 1.0f && (int)(x * 255.0f) != (int)(a.r[1] >> 16)) j->single_bad++;
    }
    return 0;
}

int main(int argc, char **argv)
{
    int fail = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    int threads = argc > 2 ? atoi(argv[2]) : 0;
    if (threads <= 0) { SYSTEM_INFO si; GetSystemInfo(&si); threads = si.dwNumberOfProcessors; }

    /* the page of the loop at its address + offset: original A, then the same bytes patched */
    uint32_t off = orig_reserve_image();
    if (!off || orig_map_at(0x579000, 0x1000, off)) return 2;
    uint8_t *page = (uint8_t *)(uintptr_t)(0x579000 + off);
    gp_va_offset = off;
    int ok = gp_patch_particlevtx();
    gp_va_offset = 0;
    printf("[0] particlevtx applied to the original bytes: %s\n", ok ? "yes" : "NO");
    if (!ok) return 1;
    page[0xe23] = 0xc3;                                   /* 0x579e23: return to the harness */
    orig_fn = orig_copy(0x579da0, 0x83, 1);
    ((uint8_t *)orig_fn)[0x83] = 0xc3;
    repl_fn = page + 0xda0;

    /* [1] */
    uint64_t t0 = now_us();
    job_t jobs[64]; HANDLE h[64];
    if (threads > 64) threads = 64;
    for (int i = 0; i < threads; i++) {
        jobs[i].lo = (1ull << 32) * i / threads; jobs[i].hi = (1ull << 32) * (i + 1) / threads;
        jobs[i].bad = jobs[i].single_bad = 0;
        h[i] = CreateThread(NULL, 0, exhaustive, &jobs[i], 0, NULL);
    }
    uint64_t bad = 0, sbad = 0;
    for (int i = 0; i < threads; i++) { WaitForSingleObject(h[i], INFINITE); bad += jobs[i].bad; sbad += jobs[i].single_bad; }
    printf("[1] all 2^32 inputs (%d threads, %.0f s): %llu mismatches; %lu went to the x87 original (|x| > 1 or "
           "infinite); a mulss+cvttss2si version would differ on %llu of the inputs in [0,1]\n", threads,
           (now_us() - t0) / 1e6, bad, (unsigned long)gp_ptclvtx_fallbacks, sbad);
    fail |= bad != 0;

    /* [2], [3] */
    static const uint32_t spec[] = {0, 0x80000000, 0x3f800000, 0xbf800000, 0x7f800000, 0xff800000, 0x7fc00000,
        0xffc00000, 0x7f800001, 0x00000001, 0x807fffff, 0x3f7fffff, 0x3f800001, 0x3b808081, 0x3c008081, 0x3effffff};
    frame_t f; regs_t a, b;
    static const uint16_t cws[] = {0x007f, 0x027f, 0x037f, 0x047f, 0x087f, 0x0c7f, 0x067f, 0x0a7f, 0x0e7f, 0x0f7f,
                                   0x0b7f, 0x077f};
    static const uint32_t csrs[] = {0x1f80, 0x9fc0, 0x3f80, 0x7f80};
    for (int pass = 0; pass < 2; pass++) {
        uint64_t n = 0; bad = 0;
        int modes = pass ? (int)(sizeof cws / 2 * 4) : 1;
        for (int m = 0; m < modes; m++) {
            uint16_t cw = pass ? cws[m / 4] : 0x007f; uint32_t csr = pass ? csrs[m % 4] : 0x1f80;
            for (int i = 0; i < (pass ? 2000000 : 40000000); i++) {
                uint32_t v[4];
                for (int k = 0; k < 4; k++) {
                    switch (rnd(&rng_seed) % 6) {
                    case 0: v[k] = rnd(&rng_seed) % 0x3f800001u; break;                  /* [0,1] */
                    case 1: { float x = (float)(rnd(&rng_seed) % 256) / 255.0f; memcpy(&v[k], &x, 4); break; }
                    case 2: v[k] = spec[rnd(&rng_seed) % 16]; break;
                    case 3: v[k] = rnd(&rng_seed); break;
                    case 4: v[k] = rnd(&rng_seed) & 0x807fffff; break;                   /* denormals */
                    default: { float x = (float)(rnd(&rng_seed) % 256) / 255.0f; uint32_t u; memcpy(&u, &x, 4);
                               v[k] = u + (rnd(&rng_seed) % 5) - 2; break; }            /* near k/255 */
                    }
                }
                setup(&f, v[0], v[1], v[2], v[3], 0x437f0000);
                n++;
                if (compare(&f, cw, csr, &a, &b)) {
                    if (bad++ < 5) printf("  MISMATCH cw %04x mxcsr %04lx rgba %08lx %08lx %08lx %08lx\n", cw,
                                          (unsigned long)csr, (unsigned long)v[0], (unsigned long)v[1],
                                          (unsigned long)v[2], (unsigned long)v[3]);
                }
            }
        }
        printf("[%d] %s: %llu tuples, %llu mismatches\n", pass + 2,
               pass ? "12 x87 control words x 4 MXCSR (DAZ/FTZ/rounding)" : "random tuples, game FPU mode", n, bad);
        fail |= bad != 0;
    }
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cws[0])); _mm_setcsr(0x1f80);

    /* [4] */
    uint64_t n4 = 0, bad4 = 0; uint32_t fb0 = (uint32_t)gp_ptclvtx_fallbacks;
    for (int i = 0; i < 100000; i++) {
        uint32_t mul = i % 2 ? 0x437f0001 : rnd(&rng_seed);
        setup(&f, rnd(&rng_seed) % 0x3f800001u, rnd(&rng_seed) % 0x3f800001u, rnd(&rng_seed), rnd(&rng_seed) % 0x3f800001u, mul);
        n4++; bad4 += compare(&f, 0x007f, 0x1f80, &a, &b) != 0;
    }
    uint32_t fb4 = (uint32_t)gp_ptclvtx_fallbacks - fb0;
    printf("[4] multiplier != 255: %llu tuples, %llu mismatches, %lu went to the x87 original\n", n4, bad4,
           (unsigned long)fb4);
    fail |= bad4 != 0 || fb4 != 100000;
    {
        const int N = 2000000; uint64_t s[2];
        setup(&f, 0x3f000000, 0x3e800000, 0x3f400000, 0x3f800000, 0x437f0000);
        for (int k = 0; k < 2; k++) {
            uint64_t t = now_us();
            for (int i = 0; i < N; i++) run(k ? repl_fn : orig_fn, f.mem + 0x1c0, &a);
            s[k] = now_us() - t;
        }
        printf("[4] per vertex incl. harness: original %.1f ns, replacement %.1f ns\n", s[0] * 1000.0 / N, s[1] * 1000.0 / N);
    }
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
