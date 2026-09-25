/* t_adecode: animdecode against the game's own motion channel code (.text at its address +
 * offset, .rdata/.data at their own addresses). Random AdaptiveDelta channels of all six kinds
 * (4- and 8-bit deltas; 1, 3 and 4 components; frame counts 1..700, not multiples of 16) are
 * queried through the real Get_* functions (vtable slots +0xc/+0x10/+0x14) with no cache stream,
 * the way HAnim Get_Translation / Get_Orientation do for the second animation of a blend.
 *   [1] the premise: the same queries through a cache stream (the path the game uses for the
 *       first animation, continuing from its last frame) give the same bits as from frame 0 while
 *       the cached frame is below the channel's frame count (at or past it they need not: the
 *       decoder then returns the cached value as is; counted separately);
 *   [2] script A (original code) vs script B (after gp_patch_animdecode rewrote the six call
 *       sites and the channel destructor entry exactly as in the game): 3 M queries interleaved
 *       over 600 channels (forward, repeated, backward, fractional, past the end, negative
 *       frames), results compared bit for bit, and B must mostly continue from its cache; B also
 *       evicts channels now and then (as their destructor does). Frames in [-2,-1) are run but not
 *       compared: there the original leaves A (an uninitialised local of Get_*) unwritten;
 *   [3] registers: each call-site entry keeps what the original decoder keeps (ebx esi edi ebp,
 *       xmm2-7) and the same stack; the destructor entry forgets the channel and hands the
 *       original exactly its state after the six bytes it replaced.
 * usage: t_adecode.exe <path to lotrbfme2ep1.exe 2.02> [thousands of queries] */
#include "orig.h"
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <xmmintrin.h>

#define TC __attribute__((thiscall))
static uint32_t OFF;
static uint32_t reloc(uint32_t v) { return v >= 0x401000 && v < 0xbd0000 ? v + OFF : v; }
static uint32_t rng;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static float frand(float lo, float hi) { return lo + (hi - lo) * (float)(rnd() & 0xffffff) / 16777216.0f; }
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define F32(p, o) (*(float *)((uint8_t *)(p) + (o)))
typedef void (TC *get_t)(void *, float, float *, void **);

#define NCH 600
static uint8_t *chan[NCH], *vt[2];
static int kind[NCH];                 /* 0..5 = decoder index: 4-bit 1/3/4 comps, 8-bit 1/3/4 comps */
static const int ncomp[6] = {1, 3, 4, 1, 3, 4};
static const uint32_t slot[6] = {0xc, 0x10, 0x14, 0xc, 0x10, 0x14};

static void build(void)
{
    rng = 4711;
    for (int b = 0; b < 2; b++) {
        vt[b] = malloc(0x20);
        for (int i = 0; i < 0x1c; i += 4) U32(vt[b], i) = reloc(*(uint32_t *)(uintptr_t)((b ? 0xbecd5c : 0xbecd40) + i));
    }
    for (int c = 0; c < NCH; c++) {
        int k = kind[c] = c % 6, b8 = k >= 3, n = ncomp[k];
        int frames = c % 7 == 0 ? 1 + rnd() % 3 : 1 + rnd() % 700;
        uint8_t *p = chan[c] = calloc(1, 0x40);
        U32(p, 0) = (uint32_t)(uintptr_t)vt[b8]; U32(p, 4) = 1; U32(p, 0xc) = frames; U32(p, 0x10) = n;
        F32(p, 0x14) = frand(0.01f, 3.0f);
        for (int i = 0; i < n; i++) F32(p, 0x18 + 4 * i) = frand(-2, 2);
        int per = b8 ? 17 : 9, bytes = ((frames + 15) / 16 + 1) * per * n + 64;
        uint8_t *d = malloc(bytes);
        for (int i = 0; i < bytes; i++) d[i] = (uint8_t)rnd();
        for (int i = 0; i + per <= bytes; i += per) d[i] = (uint8_t)(rnd() % 10);     /* scale 1e-8..10 */
        U32(p, 0x28) = (uint32_t)(uintptr_t)d;
    }
}

static float next_frame(float cur, int frames)
{
    switch (rnd() % 10) {
    case 0: return frand(-3, 0);                                   /* negative (a ping-pong edge) */
    case 1: return frand(0, frames + 40);                          /* anywhere, past the end too */
    case 2: return cur;                                            /* the same frame again */
    case 3: return cur - frand(0, 5);                              /* backwards */
    default: return cur + frand(0, 2.5f);                          /* forwards, fractional */
    }
}

static uint32_t *qframe;              /* integer frame of each query */
/* the query script: n queries over all channels, results into out (4 floats each) */
static void script(int n, float *out, int evict)
{
    static float cur[NCH];
    rng = 99991;
    for (int c = 0; c < NCH; c++) cur[c] = 0;
    for (int q = 0; q < n; q++) {
        int c = rnd() % NCH;
        if (rnd() % 3) c = (c % 40) + (q / 5000 % 15) * 40;       /* a working set, like a battle */
        cur[c] = next_frame(cur[c], U32(chan[c], 0xc));
        float *o = out + 4 * q;
        o[0] = o[1] = o[2] = o[3] = -7.0f;
        get_t g = (get_t)(uintptr_t)U32(U32(chan[c], 0), slot[kind[c]]);
        qframe[q] = (uint32_t)_mm_cvttss_si32(_mm_set_ss(cur[c]));
        g(chan[c], cur[c], o, NULL);
        if (evict && q % 4999 == 0) gp_adq_evict(chan[c]);
    }
}

/* ---- [3] register harness (as t_regs) ---- */
typedef struct {
    uint32_t fn, nargs, args[6];   /*  0, 4, 8 */
    uint32_t in[7], out[7];        /* 32, 60 */
    uint8_t xin[128], xout[128];   /* 88, 216 */
    int32_t esp_delta;             /* 344 */
} ctx_t;
ctx_t *cur_ctx; uint32_t saved_esp, target;
__asm__(".text\n"
"_regcall:\n"
"  pushl %ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n"
"  movl 20(%esp), %eax\n  movl %eax, _cur_ctx\n  movl %esp, _saved_esp\n"
"  movups 88(%eax), %xmm0\n  movups 104(%eax), %xmm1\n  movups 120(%eax), %xmm2\n  movups 136(%eax), %xmm3\n"
"  movups 152(%eax), %xmm4\n  movups 168(%eax), %xmm5\n  movups 184(%eax), %xmm6\n  movups 200(%eax), %xmm7\n"
"  movl 4(%eax), %ecx\n"
"1: testl %ecx, %ecx\n  jz 2f\n  pushl 4(%eax,%ecx,4)\n  decl %ecx\n  jmp 1b\n"
"2: movl (%eax), %ecx\n  movl %ecx, _target\n"
"  movl 36(%eax), %ebx\n  movl 40(%eax), %ecx\n  movl 44(%eax), %edx\n  movl 48(%eax), %esi\n"
"  movl 52(%eax), %edi\n  movl 56(%eax), %ebp\n  movl 32(%eax), %eax\n"
"  call *_target\n"
"  pushl %eax\n  movl _cur_ctx, %eax\n  popl 60(%eax)\n"
"  movl %ebx, 64(%eax)\n  movl %ecx, 68(%eax)\n  movl %edx, 72(%eax)\n  movl %esi, 76(%eax)\n"
"  movl %edi, 80(%eax)\n  movl %ebp, 84(%eax)\n"
"  movups %xmm0, 216(%eax)\n  movups %xmm1, 232(%eax)\n  movups %xmm2, 248(%eax)\n  movups %xmm3, 264(%eax)\n"
"  movups %xmm4, 280(%eax)\n  movups %xmm5, 296(%eax)\n  movups %xmm6, 312(%eax)\n  movups %xmm7, 328(%eax)\n"
"  movl %esp, %ecx\n  subl _saved_esp, %ecx\n  movl %ecx, 344(%eax)\n"
"  movl _saved_esp, %esp\n"
"  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n"
/* stands in for the destructor after its first 6 bytes: records its state, undoes the two pushes */
"_dtor_probe:\n"
"  movl %eax, _probe+0\n  movl %ecx, _probe+4\n  movl %edx, _probe+8\n  movl %esi, _probe+12\n"
"  movl (%esp), %eax\n  movl %eax, _probe+16\n  movl 4(%esp), %eax\n  movl %eax, _probe+20\n"
"  movl _probe+0, %eax\n  addl $4, %esp\n  popl %esi\n  ret\n");
void regcall(ctx_t *c);
void dtor_probe(void);
uint32_t probe[6];
static const char *rn[7] = {"eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"};

int main(int argc, char **argv)
{
    int fail = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    int n = (argc > 2 ? atoi(argv[2]) : 3000) * 1000;
    if (orig_map_at(0xbd0000, 0x1b9000, 0) || orig_map_at(0xd89000, 0x81000, 0)) return 2;
    OFF = orig_reserve_image();
    if (!OFF || orig_map_at(0x401000, 0x7cf000, OFF)) return 2;
    unsigned short cw = 0x007f;
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));
    _mm_setcsr(0x1f80);
    build();

    /* [1] the stream path (continuing) against from-frame-0, original code */
    {
        uint64_t q = 0, bad = 0, past = 0, past_bad = 0;
        rng = 5;
        for (int c = 0; c < NCH; c++) {
            uint8_t rec[4 + 32]; memset(rec, 0xff, sizeof rec);       /* as 0x560850 resets it */
            float cur = 0;
            get_t g = (get_t)(uintptr_t)U32(U32(chan[c], 0), slot[kind[c]]);
            for (int i = 0; i < 400; i++) {
                uint32_t prev = U32(rec, 0);                           /* the stream's cached frame */
                cur = next_frame(cur, U32(chan[c], 0xc));
                float a[4] = {0}, b[4] = {0};
                void *stream = rec, *s0 = rec;
                g(chan[c], cur, a, &stream);
                g(chan[c], cur, b, NULL);
                int differ = memcmp(a, b, 4 * ncomp[kind[c]]) || (uint8_t *)stream - (uint8_t *)s0 != 4 + 8 * ncomp[kind[c]];
                uint32_t dst = (uint32_t)_mm_cvttss_si32(_mm_set_ss(cur));
                if (prev < U32(chan[c], 0xc) && dst != 0xffffffffu) { q++; bad += differ; } else { past++; past_bad += differ; }
            }
        }
        printf("[1] cache stream vs from frame 0 (original code), cached frame below the channel's frame count: "
               "%llu queries, %llu differ; at or past it, or frame -1 (never continued by animdecode): %llu queries, "
               "%llu differ\n", q, bad, past, past_bad);
        fail |= bad != 0;
    }

    /* [2] */
    float *ra = malloc(16ull * n), *rb = malloc(16ull * n);
    qframe = malloc(4ull * n);
    uint64_t t0 = now_us(); script(n, ra, 0); uint64_t ta = now_us() - t0;
    gp_va_offset = OFF;
    int ok = gp_patch_animdecode();
    gp_va_offset = 0;
    printf("[2] animdecode applied to the original bytes: %s\n", ok ? "yes" : "NO");
    if (!ok) { printf("FAIL\n"); return 1; }
    t0 = now_us(); script(n, rb, 1); uint64_t tb = now_us() - t0;
    uint64_t bad = 0, minus1 = 0;
    for (int q = 0; q < n; q++) {
        if (qframe[q] == 0xffffffffu) { minus1++; continue; }
        if (memcmp(ra + 4 * q, rb + 4 * q, 16)) { if (bad++ < 5) printf("  MISMATCH query %d\n", q); }
    }
    printf("[2] %d queries: %llu mismatches; %ld of %ld decodes continued from the cache, %ld evictions; "
           "%.0f vs %.0f ns per query; %llu queries at frame -1 not compared (from frame 0 the original "
           "never stores A there: the result depends on an uninitialised local, patched or not)\n", n, bad,
           gp_adq_stats[1], gp_adq_stats[0], gp_adq_stats[2], ta * 1000.0 / n, tb * 1000.0 / n, minus1);
    fail |= bad != 0 || gp_adq_stats[1] < gp_adq_stats[0] / 4;

    /* [3] registers: decoder k called directly vs through its call-site entry */
    void (*entry[6])(void) = {gp_adq_site0, gp_adq_site1, gp_adq_site2, gp_adq_site3, gp_adq_site4, gp_adq_site5};
    static const uint32_t dec[6] = {0x5b19c0, 0x5b1aba, 0x5b1c00, 0x5b1d49, 0x5b1e2b, 0x5b1f5b};
    for (int k = 0; k < 6; k++) {
        int c = k;                                                  /* chan[k] is of kind k */
        for (int rep = 0; rep < 2; rep++) {
            static float A[2][4], B[2][4];
            ctx_t a, b; memset(&a, 0, sizeof a);
            for (int r = 0; r < 7; r++) a.in[r] = 0x11111111u * (r + 1);
            a.in[2] = (uint32_t)(uintptr_t)chan[c];
            for (int i = 0; i < 128; i++) a.xin[i] = (uint8_t)(0x5a ^ i * 37);
            a.nargs = 5; a.args[0] = (uint32_t)(uintptr_t)(chan[c] + 0x18); a.args[1] = 0; a.args[2] = 3 + rep * 5;
            b = a;
            a.args[3] = (uint32_t)(uintptr_t)A[0]; a.args[4] = (uint32_t)(uintptr_t)A[1];
            b.args[3] = (uint32_t)(uintptr_t)B[0]; b.args[4] = (uint32_t)(uintptr_t)B[1];
            a.fn = reloc(dec[k]); b.fn = (uint32_t)(uintptr_t)entry[k];
            __asm__ volatile("fninit\n fldcw %0" : : "m"(cw)); regcall(&a);
            __asm__ volatile("fninit\n fldcw %0" : : "m"(cw)); regcall(&b);
            int bd = memcmp(A, B, sizeof A) != 0;
            for (int r = 0; r < 7; r++) if (a.out[r] == a.in[r] && b.out[r] != b.in[r]) { printf("  site %d: %s changed\n", k, rn[r]); bd++; }
            for (int x = 0; x < 8; x++)
                if (!memcmp(a.xout + 16 * x, a.xin + 16 * x, 16) && memcmp(b.xout + 16 * x, b.xin + 16 * x, 16)) { printf("  site %d: xmm%d changed\n", k, x); bd++; }
            if (a.esp_delta != b.esp_delta) { printf("  site %d: esp %+ld vs %+ld\n", k, (long)a.esp_delta, (long)b.esp_delta); bd++; }
            fail |= bd != 0;
            printf("[3] site %d (decoder %06lx, %s call): %s\n", k, (unsigned long)dec[k], rep ? "cached" : "first",
                   bd ? "DIFFERS" : "same results, preserved registers and stack");
        }
    }
    {   /* the destructor entry */
        extern uint32_t gp_adq_dtor_cont;
        uint32_t save = gp_adq_dtor_cont;
        gp_adq_dtor_cont = (uint32_t)(uintptr_t)dtor_probe;
        LONG ev = gp_adq_stats[2];
        ctx_t a; memset(&a, 0, sizeof a);
        for (int r = 0; r < 7; r++) a.in[r] = 0x11111111u * (r + 1);
        a.in[2] = (uint32_t)(uintptr_t)chan[2];
        a.fn = (uint32_t)(uintptr_t)gp_adq_dtor;
        regcall(&a);
        gp_adq_dtor_cont = save;
        int bd = probe[0] != a.in[0] || probe[1] != a.in[2] || probe[2] != a.in[3] || probe[3] != a.in[2] ||
                 probe[4] != U32(chan[2], 0x28) || probe[5] != a.in[4] || a.out[4] != a.in[4] || a.esp_delta ||
                 gp_adq_stats[2] != ev + 1;
        printf("[3] destructor entry: %s\n", bd ? "DIFFERS" : "channel forgotten; eax ecx edx esi and the two pushes as "
               "the original's first 6 bytes leave them");
        fail |= bd;
    }
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
