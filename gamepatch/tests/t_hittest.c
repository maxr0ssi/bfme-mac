/* t_hittest: the SSE hit test (gp_hittest, replacing 0xb0dfe0 + 0xb0deb0) against the original
 * x87 functions copied from the exe, on synthetic shapes: UI-like shapes and transforms, points
 * on vertices and edges (ties), degenerate triangles, wide-range and special floats (NaN, inf,
 * denormals, huge) in vertices, matrices and points. Every result must be identical.
 * usage: t_hittest.exe <path to lotrbfme2ep1.exe 2.02> [millions of cases] */
#include "orig.h"
#include "gp.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <xmmintrin.h>

typedef int (WINAPI *hit_t)(const void *shape, const float *m, int ix, int iy);

static uint32_t rng = 987654321;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static float frand(float lo, float hi) { return lo + (hi - lo) * (rnd() & 0xffffff) / 16777216.0f; }
static float fbits(uint32_t u) { union { uint32_t u; float f; } c = { u }; return c.f; }
static float wide(void)
{
    static const uint32_t s[] = {0x7fc00000, 0xffc00000, 0x7f800000, 0xff800000, 0x00000001, 0x80400000,
                                 0x7f7fffff, 0xff7fffff, 0x00800000, 0x80000000, 0x0, 0x7f800001};
    switch (rnd() % 4) {
    case 0: return s[rnd() % (sizeof s / 4)];
    case 1: return fbits(rnd());
    default: return fbits((rnd() & 0x807fffff) | ((uint32_t)(60 + rnd() % 134) << 23)); /* 2^-67..2^66 */
    }
}

typedef struct { uint8_t hdr[0x14]; int count; int pad; float *v; int16_t *idx; } shape_t;

static void set_game_modes(void)
{
    unsigned short cw = 0x007f;
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));
    _mm_setcsr(0x1f80);
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    double millions = argc > 2 ? atof(argv[2]) : 20;
    const uint8_t *a = orig_bytes(0xb0dfe0, 0x110), *b = orig_bytes(0xb0deb0, 0x130);
    if (gp_fnv1a(a, 0x110) != GP_FNV_B0DFE0 || gp_fnv1a(b, 0x130) != GP_FNV_B0DEB0) {
        printf("hit-test code differs from the expected bytes\n"); return 2;
    }
    uint8_t *buf = VirtualAlloc(NULL, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(buf, a, 0x110); memcpy(buf + 0x110, b, 0x130);
    orig_fix_rel32(buf, 0xb0dfe0, 0xb0e0b4, buf + 0x110);
    hit_t orig = (hit_t)buf, repl = (hit_t)(void *)gp_hittest;
    gp_hittest_cont = (uint32_t)(uintptr_t)buf + 7;
    set_game_modes();

    static float V[64 * 2]; static int16_t I[80 * 3];
    shape_t sh; memset(&sh, 0, sizeof sh); sh.v = V; sh.idx = I;
    uint64_t n = 0, bad = 0, hits = 0, cls[6] = {0};
    uint64_t total = (uint64_t)(millions * 1e6);
    for (uint64_t it = 0; it < total; it++) {
        int kind = rnd() % 6;              /* 0-2 UI-like, 3 degenerate, 4 wide floats, 5 specials */
        int nv = 3 + rnd() % 30, nt = 1 + rnd() % 40;
        for (int i = 0; i < nv; i++) {
            if (kind <= 3) {
                V[2 * i] = (float)((int)(rnd() % 400) - 200) + (rnd() & 1 ? 0.5f : 0.0f);
                V[2 * i + 1] = (float)((int)(rnd() % 400) - 200) + (rnd() & 3 ? 0.0f : 0.25f);
                if (kind == 3 && i > 0 && rnd() % 2) { V[2 * i] = V[0]; if (rnd() & 1) V[2 * i + 1] = V[1]; }
            } else if (kind == 4) { V[2 * i] = frand(-1e4f, 1e4f) * fbits(0x3f800000 + ((rnd() % 40) << 23) - (20u << 23)); V[2 * i + 1] = frand(-1e4f, 1e4f); }
            else { V[2 * i] = rnd() % 4 ? frand(-100, 100) : wide(); V[2 * i + 1] = rnd() % 4 ? frand(-100, 100) : wide(); }
        }
        for (int t = 0; t < nt * 3; t++) I[t] = (int16_t)(rnd() % nv);
        sh.count = rnd() % 50 == 0 ? -(int)(rnd() % 3) : nt;
        float m[6];
        if (kind <= 3) {
            float s = rnd() % 3 ? 1.0f : frand(0.1f, 4.0f), r = rnd() % 4 ? 0.0f : frand(-3.2f, 3.2f);
            m[0] = s * cosf(r); m[1] = s * sinf(r); m[2] = -s * sinf(r); m[3] = s * cosf(r);
            if (kind == 1) { m[0] = rnd() % 2 ? 1.0f : 0.75f; m[1] = m[2] = 0; m[3] = m[0]; }
            m[4] = (float)(rnd() % 1600) + (rnd() & 1 ? 0.5f : 0.0f); m[5] = (float)(rnd() % 1200);
        } else if (kind == 4) { for (int k = 0; k < 6; k++) m[k] = frand(-50, 50) * fbits(0x3f800000 + ((rnd() % 60) << 23) - (30u << 23)); }
        else { for (int k = 0; k < 6; k++) m[k] = rnd() % 3 ? frand(-4, 4) : wide(); }
        /* the point: near the shape, on a transformed vertex, random, or extreme */
        int ix, iy, pk = rnd() % 5;
        int t0 = I[3 * (rnd() % (nt ? nt : 1))];
        float px = m[0] * V[2 * t0] + m[2] * V[2 * t0 + 1] + m[4], py = m[1] * V[2 * t0] + m[3] * V[2 * t0 + 1] + m[5];
        if (!(fabsf(px) < 2e9f)) px = 0;
        if (!(fabsf(py) < 2e9f)) py = 0;
        switch (pk) {
        case 0: ix = (int)px; iy = (int)py; break;
        case 1: ix = (int)px + (int)(rnd() % 41) - 20; iy = (int)py + (int)(rnd() % 41) - 20; break;
        case 2: ix = (int)(rnd() % 2000) - 200; iy = (int)(rnd() % 1500) - 200; break;
        case 3: ix = (int)rnd(); iy = (int)rnd(); break;
        default: ix = (int)px + (int)(rnd() % 400) - 200; iy = (int)py + (int)(rnd() % 3) - 1; break;
        }
        int r1 = orig(&sh, m, ix, iy) & 0xff;
        int r2 = repl(&sh, m, ix, iy) & 0xff;
        n++; hits += r1 != 0; cls[kind]++;
        if (r1 != r2) {
            if (bad < 5) printf("  MISMATCH kind %d: orig %d new %d point (%d,%d) m %g %g %g %g %g %g\n",
                                kind, r1, r2, ix, iy, m[0], m[1], m[2], m[3], m[4], m[5]);
            bad++;
        }
        unsigned short sw; __asm__ volatile("fnstsw %0" : "=m"(sw));
        if ((sw >> 11) & 7) { printf("  x87 stack not empty after call\n"); bad++; set_game_modes(); }
    }
    printf("[1] %llu cases (UI %llu, degenerate %llu, wide %llu, specials %llu), %llu hits: %llu mismatches\n",
           n, cls[0] + cls[1] + cls[2], cls[3], cls[4], cls[5], hits, bad);
    printf("    replacement: %ld calls, %ld rejected by the bounding box, %ld scanned, %ld run in x87 "
           "(flags raised)\n", gp_hittest_stats[0], gp_hittest_stats[1], gp_hittest_stats[2], gp_hittest_stats[3]);

    /* [2] modes other than the game's must run the original */
    unsigned short cw53 = 0x027f;
    __asm__ volatile("fldcw %0" : : "m"(cw53));
    LONG fb0 = gp_hittest_stats[0];
    uint64_t d2 = 0;
    for (int it = 0; it < 200000; it++) {
        for (int i = 0; i < 12; i++) { V[2 * i] = frand(-100, 100); V[2 * i + 1] = frand(-100, 100); }
        for (int t = 0; t < 30; t++) I[t] = (int16_t)(rnd() % 12);
        sh.count = 10; float m[6] = {frand(0.3f, 3), frand(-1, 1), frand(-1, 1), frand(0.3f, 3), frand(0, 900), frand(0, 700)};
        int ix = (int)(m[4] + frand(-100, 100)), iy = (int)(m[5] + frand(-100, 100));
        d2 += (orig(&sh, m, ix, iy) & 0xff) != (repl(&sh, m, ix, iy) & 0xff);
    }
    LONG reached = gp_hittest_stats[0] - fb0;
    printf("[2] PC_53 mode: 200000 cases, %llu mismatches, %ld reached the SSE code (must be 0)\n", d2, reached);
    set_game_modes();

    /* [3] speed on a UI-like button (20 triangles), pointer elsewhere and pointer on it */
    for (int i = 0; i < 24; i++) { V[2 * i] = (float)(rnd() % 120); V[2 * i + 1] = (float)(rnd() % 40); }
    for (int t = 0; t < 60; t++) I[t] = (int16_t)(rnd() % 24);
    sh.count = 20; float m[6] = {1, 0, 0, 1, 400, 300};
    for (int where = 0; where < 2; where++) {
        int ix = where ? 460 : 900, iy = where ? 320 : 100; const int N = 200000;
        uint64_t s0 = now_us(); for (int i = 0; i < N; i++) orig(&sh, m, ix, iy);
        uint64_t s1 = now_us(); for (int i = 0; i < N; i++) repl(&sh, m, ix, iy);
        uint64_t s2 = now_us();
        printf("[3] 20-triangle shape, pointer %s: original %.0f ns, replacement %.0f ns per call\n",
               where ? "over it" : "elsewhere", (s1 - s0) * 1000.0 / N, (s2 - s1) * 1000.0 / N);
    }
    int fail = bad != 0 || d2 != 0 || reached != 0;
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
