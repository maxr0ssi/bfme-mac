/* t_terrainbox: terrainbox (p_terrainbox.c) against Wine 11's d3dx9_27 box filter, the reference it
 * imitates, in the game's FPU mode (x87, 24-bit precision; Wine's i386 d3dx9 does its float math on
 * the x87). Wine 11's DLL: d3dx9_27_w11.dll next to this exe or $T_D3DX11 (scripts/game-patch.sh
 * copies wine/build-11.0's when it exists); without it [2] and the Wine 11 columns are skipped.
 *   [0] the patch on a relocated copy of the exe after mipfilter: the 2 16-bit sites call
 *       gp_tb_filter, the DXT1 site the frame stub, unhandled calls go on to mipfilter
 *   [1] the first call: self-test passes, the installed (Wine 10) d3dx9 is recognised as point
 *       filtering, the call takes the box path; with Wine 11's DLL behind the thunk it switches off
 *   [2] every (a, b, c, d) of a 5-bit channel (2^20, all three channels, A1R5G5B5, X1R5G5B5, R5G6B5),
 *       every 4-bit one (A4R4G4B4, X4R4G4B4), 4 M random 2x2 blocks of the 8-bit formats: level 1
 *       byte for byte as Wine 11's; the same in the default FPU mode (informational)
 *   [3] terrain-like 512x512 and 256x256 A1R5G5B5, 3 levels (the tile textures): ms per texture,
 *       Wine 10 / mipfilter (point) / terrainbox / Wine 11
 *   [4] DXT1 256x256 tile textures, 3 levels: terrainbox's levels (box from the bake's X8R8G8B8 image,
 *       compressed by D3DX) against Wine 10's and Wine 11's D3DXFilterTexture: error against the
 *       exact box of the uncompressed image, and ms
 *   [5] left alone (no lock, no byte): non-power-of-two, a 1-high level, DXT3, a palette, point filter
 *   [6] the DXT1 site stub reads [ebp-0x18] and leaves the stack as the original call did
 * usage: t_terrainbox.exe <lotrbfme2ep1.exe 2.02> */
#define COBJMACROS
#include "orig.h"
#include "p_mipfilter.h"
#include "p_terrain.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <float.h>
#include <math.h>

static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs = 0x1234567u;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
static uint32_t call_target(uint32_t va) { return va + 5 + *(int32_t *)(uintptr_t)(va + 1); }
static gp_mf_fn w10, w11;               /* D3DXFilterTexture: the prefix's (Wine 10) and Wine 11's */
static gp_tb_load_fn w10load;
static int cmp_u64(const void *a, const void *b)
{
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return x < y ? -1 : x > y;
}
static void pc24(void) { _controlfp(_PC_24, _MCW_PC); }
static void pc64(void) { _controlfp(_PC_64, _MCW_PC); }

static long diff_level(gp_fake_tex *a, gp_fake_tex *b, UINT l)
{
    UINT h, p, w, bpp;
    uint8_t *x = gp_fake_bits(a, l, &w, &h, &p), *y = gp_fake_bits(b, l, NULL, NULL, NULL);
    bpp = (p - 4) / (w ? w : 1);
    long n = 0;
    for (UINT r = 0; r < h; r++) n += memcmp(x + r * p, y + r * p, w * bpp) != 0 ? 1 : 0;
    if (!n) return 0;
    n = 0;
    for (UINT r = 0; r < h; r++) for (UINT i = 0; i < w * bpp; i++) n += x[r * p + i] != y[r * p + i];
    return n;
}
static void copy0(gp_fake_tex *d, gp_fake_tex *s)
{
    UINT h, p; uint8_t *x = gp_fake_bits(s, 0, NULL, &h, &p);
    memcpy(gp_fake_bits(d, 0, NULL, NULL, NULL), x, (size_t)h * p);
}
/* the 2x2 block i of level 0 */
static void put(uint8_t *l0, UINT p, UINT bpp, uint32_t i, int k, uint32_t v)
{
    uint8_t *q = l0 + (size_t)(2 * (i >> 10) + (k >> 1)) * p + (2 * (i & 1023) + (k & 1)) * bpp;
    if (bpp == 2) *(uint16_t *)q = (uint16_t)v; else *(uint32_t *)q = v;
}

static const struct { const char *name; D3DFORMAT f; UINT bpp; uint8_t sh[3], bits[3]; uint32_t amask; } F[] = {
    {"A1R5G5B5", D3DFMT_A1R5G5B5, 2, {0, 5, 10}, {5, 5, 5}, 0x8000}, {"X1R5G5B5", D3DFMT_X1R5G5B5, 2, {0, 5, 10}, {5, 5, 5}, 0x8000},
    {"R5G6B5", D3DFMT_R5G6B5, 2, {0, 5, 11}, {5, 6, 5}, 0}, {"A4R4G4B4", D3DFMT_A4R4G4B4, 2, {0, 4, 8}, {4, 4, 4}, 0xf000},
    {"X4R4G4B4", D3DFMT_X4R4G4B4, 2, {0, 4, 8}, {4, 4, 4}, 0xf000}, {"A8R8G8B8", D3DFMT_A8R8G8B8, 4, {0, 8, 16}, {8, 8, 8}, 0xff000000u},
    {"X8R8G8B8", D3DFMT_X8R8G8B8, 4, {0, 8, 16}, {8, 8, 8}, 0xff000000u}};
enum { NFMT = sizeof F / sizeof F[0] };

/* level 0 of a 2048x2048 texture: block i's channel c takes the 4 values of combo perm_c(i) */
static void fill_combos(gp_fake_tex *t, int k)
{
    UINT p; uint8_t *l0 = gp_fake_bits(t, 0, NULL, NULL, &p);
    for (uint32_t i = 0; i < 1u << 20; i++) {
        uint32_t px[4] = {0, 0, 0, 0};
        for (int c = 0; c < 3; c++) {
            unsigned n = F[k].bits[c];
            uint32_t combo;
            if (n <= 5) combo = c == 0 ? i : c == 1 ? (i * 0x9e3u + 0x51) & 0xfffff : i ^ 0xabcde;   /* bijections */
            else combo = rnd();
            for (int q = 0; q < 4; q++) px[q] |= (combo >> (n * q) & ((1u << n) - 1)) << F[k].sh[c];
        }
        for (int q = 0; q < 4; q++) put(l0, p, F[k].bpp, i, q, px[q] | (rnd() & F[k].amask));
    }
}
static void terrain_fill(uint8_t *l0, UINT w, UINT p, int bpp32)
{
    float fx = (rnd() % 1000) / 1000.0f, fy = (rnd() % 1000) / 1000.0f;
    for (UINT y = 0; y < w; y++)
        for (UINT x = 0; x < w; x++) {      /* two tile colours blended, with grain, as the bake gives */
            int g = (int)(rnd() % 24) - 12, k = (int)((x * fx + y * fy) * 0.25f) & 63;
            int r = 90 + k + g, gg = 80 + (k >> 1) + g, bb = 50 + (k >> 2) + g;
            r = r < 0 ? 0 : r > 255 ? 255 : r; gg = gg < 0 ? 0 : gg > 255 ? 255 : gg; bb = bb < 0 ? 0 : bb > 255 ? 255 : bb;
            if (bpp32) ((uint32_t *)(l0 + y * p))[x] = (uint32_t)(r << 16 | gg << 8 | bb);
            else ((uint16_t *)(l0 + y * p))[x] = (uint16_t)(0x8000 | (r >> 3) << 10 | (gg >> 3) << 5 | (bb >> 3));
        }
}
static double median_ms(uint64_t *t, int n) { qsort(t, n, sizeof *t, cmp_u64); return t[n / 2] / 1000.0; }

/* DXT1 level -> X8R8G8B8 through Wine's own loader, for the error measure */
static void dxt_to_32(gp_fake_tex *t, UINT l, uint32_t *out)
{
    UINT w, h, p; uint8_t *b = gp_fake_bits(t, l, &w, &h, &p);
    for (UINT by = 0; by < (h + 3) / 4; by++)
        for (UINT bx = 0; bx < (w + 3) / 4; bx++) {
            const uint8_t *k = b + by * p + bx * 8;
            unsigned c0 = k[0] | k[1] << 8, c1 = k[2] | k[3] << 8, col[4][3];
            for (int i = 0; i < 2; i++) {
                unsigned c = i ? c1 : c0;
                col[i][0] = (c >> 11) * 255 / 31; col[i][1] = (c >> 5 & 63) * 255 / 63; col[i][2] = (c & 31) * 255 / 31;
            }
            for (int j = 0; j < 3; j++) {
                col[2][j] = c0 > c1 ? (2 * col[0][j] + col[1][j]) / 3 : (col[0][j] + col[1][j]) / 2;
                col[3][j] = c0 > c1 ? (col[0][j] + 2 * col[1][j]) / 3 : 0;
            }
            uint32_t bits = k[4] | k[5] << 8 | k[6] << 16 | (uint32_t)k[7] << 24;
            for (int y = 0; y < 4; y++) for (int x = 0; x < 4; x++) {
                if (by * 4 + y >= h || bx * 4 + x >= w) continue;
                unsigned *c = col[bits >> (2 * (4 * y + x)) & 3];
                out[(by * 4 + y) * w + bx * 4 + x] = c[0] << 16 | c[1] << 8 | c[2];
            }
        }
}
static double rms(const uint32_t *a, const uint32_t *b, UINT n)
{
    double s = 0;
    for (UINT i = 0; i < n; i++) for (int c = 0; c < 24; c += 8) { int d = (int)(a[i] >> c & 255) - (int)(b[i] >> c & 255); s += d * d; }
    return sqrt(s / (3.0 * n));
}

/* [6]: call the stub as the bake does: ebp = a frame whose [ebp-0x18] is the image */
static const uint8_t *seen_buf; static int seen_n;
static HRESULT WINAPI stub_next(IDirect3DBaseTexture9 *t, const PALETTEENTRY *p, UINT s, DWORD f) { (void)t; (void)p; (void)s; (void)f; seen_n++; return D3D_OK; }
static int call_stub(const uint8_t *buf, uint32_t *esp_delta)
{
    uint32_t frame[16], d;
    frame[16 - 6] = (uint32_t)(uintptr_t)buf;          /* [ebp-0x18] with ebp = &frame[16] */
    __asm__ volatile(
        "pushl %%ebp\n movl %1, %%ebp\n movl %%esp, %%esi\n"
        "pushl $5\n pushl $0\n pushl $0\n pushl $0\n call _gp_tb_dxt_site\n"
        "movl %%esp, %0\n subl %%esi, %0\n popl %%ebp\n"
        : "=&r"(d) : "r"(&frame[16]) : "esi", "eax", "ecx", "edx", "memory");
    *esp_delta = d;
    return 0;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (!VirtualAlloc((void *)0xbd0000, 0xe10000 - 0xbd0000, MEM_RESERVE, PAGE_READWRITE)) { printf("cannot reserve the data range\nFAIL\n"); return 2; }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xbd0000, 0x1b9000, 0)) return 2;
    uint32_t off = orig_reserve_image();
    if (!off || orig_map_at(0x401000, 0x7cf000, off)) return 2;
    HMODULE dx = LoadLibraryA("d3dx9_27.dll");
    w10 = dx ? (gp_mf_fn)(void *)GetProcAddress(dx, "D3DXFilterTexture") : NULL;
    w10load = dx ? (gp_tb_load_fn)(void *)GetProcAddress(dx, "D3DXLoadSurfaceFromMemory") : NULL;
    if (!w10 || !w10load) { printf("cannot load d3dx9_27.dll\nFAIL\n"); return 2; }
    *(uint32_t *)0xbd0a20 = (uint32_t)(uintptr_t)w10;
    *(uint32_t *)0xbd0a1c = (uint32_t)(uintptr_t)w10load;
    char path[MAX_PATH], *e;
    if (!GetEnvironmentVariableA("T_D3DX11", path, sizeof path)) {
        GetModuleFileNameA(NULL, path, sizeof path);
        if ((e = strrchr(path, '\\'))) strcpy(e + 1, "d3dx9_27_w11.dll");
    }
    HMODULE dx11 = LoadLibraryA(path);
    w11 = dx11 ? (gp_mf_fn)(void *)GetProcAddress(dx11, "D3DXFilterTexture") : NULL;
    printf("Wine 11 d3dx9_27: %s\n", w11 ? path : "not found (its checks are skipped)");

    /* [0] */
    gp_va_offset = off;
    int ok = gp_patch_mipfilter() && gp_patch_terrainbox();
    gp_va_offset = 0;
    ok = ok && call_target(0x4eee4a + off) == (uint32_t)(uintptr_t)gp_tb_filter &&
         call_target(0x4ef148 + off) == (uint32_t)(uintptr_t)gp_tb_filter &&
         call_target(0x4eefde + off) == (uint32_t)(uintptr_t)gp_tb_dxt_site &&
         gp_tb_next == (gp_tb_fn)gp_mf_filter && (uint32_t)(uintptr_t)gp_tb_load == 0xa3ecd8 + off;
    verdict(!ok, "[0] terrainbox after mipfilter: %s (16-bit sites -> gp_tb_filter, DXT1 site -> stub, unhandled -> mipfilter)\n",
            ok ? "applied" : "NOT applied");
    if (!ok) { printf("FAIL\n"); return 1; }
    gp_va_offset = off;                   /* the thunks the patch calls through live in the copy */

    /* [1] */
    {
        pc24();
        gp_fake_tex *a = gp_fake_create(64, 64, 3, D3DFMT_A1R5G5B5, 2);
        UINT p; uint8_t *l0 = gp_fake_bits(a, 0, NULL, NULL, &p);
        terrain_fill(l0, 64, p, 0);
        HRESULT r = gp_tb_filter(gp_fake_base(a), NULL, 0, 5);
        ok = r == D3D_OK && gp_tb_state == 1 && gp_tb_stats[1] == 1;
        int off11 = -2;
        if (w11) {   /* Wine 11 behind the thunk: the check finds a box filter and stays off */
            *(uint32_t *)0xbd0a20 = (uint32_t)(uintptr_t)w11;
            gp_tb_state = 0;
            gp_tb_filter(gp_fake_base(a), NULL, 0, 5);
            off11 = gp_tb_state;
            *(uint32_t *)0xbd0a20 = (uint32_t)(uintptr_t)w10;
            gp_tb_state = 1;
            ok = ok && off11 == -1;
        }
        verdict(!ok, "[1] first call: self-test and d3dx9 check %s, box path taken: %s; with Wine 11's d3dx9: %s\n",
                gp_tb_state > 0 ? "passed (Wine 10 point-filters)" : "FAILED", gp_tb_stats[1] ? "yes" : "NO",
                off11 == -2 ? "skipped" : off11 == -1 ? "stays off (already box)" : "WRONGLY ON");
        gp_fake_free(a);
    }

    /* [2] */
    if (w11 && !getenv("T_SKIP2")) {
        for (int mode = 0; mode < 2; mode++) {
            if (mode) pc64(); else pc24();
            for (int k = 0; k < NFMT; k++) {
                gp_fake_tex *a = gp_fake_create(2048, 2048, 2, F[k].f, F[k].bpp), *b = gp_fake_create(2048, 2048, 2, F[k].f, F[k].bpp);
                fill_combos(a, k); copy0(b, a);
                gp_fake_tex *c = gp_fake_create(2048, 2048, 2, F[k].f, F[k].bpp);
                copy0(c, a);
                HRESULT ra = w11(gp_fake_base(a), NULL, 0, 5);
                HRESULT rb = gp_tb_box(gp_fake_base(b), 0, 1), rc = gp_tb_box(gp_fake_base(c), 0, 0);
                long d = diff_level(a, b, 1), dr = diff_level(a, c, 1);
                if (!mode) verdict(ra != D3D_OK || rb != S_OK || rc != S_OK || d || (dr && F[k].bits[0] != 5),
                                   "[2] %-8s %s: level 1 exact mode %s Wine 11's (%ld bytes differ); rounded mode: %ld bytes "
                                   "differ%s\n", F[k].name,
                                   F[k].bits[0] <= 5 ? (F[k].bits[0] == 5 ? "every (a,b,c,d) of each 5-bit channel" : "every (a,b,c,d) of each 4-bit channel")
                                   : "1 M random 2x2 blocks", ra == D3D_OK && rb == S_OK && !d ? "identical to" : "DIFFERS from", d, dr,
                                   F[k].bits[0] == 5 ? " (exact halves Wine 11's float rounds down, one 5-bit step)" : "");
                else if (k == 0 || d) printf("    (default FPU mode, 64-bit precision: %s %ld bytes differ%s)\n", F[k].name, d,
                                             d ? ": Wine 11's result depends on the FPU mode; the game runs 24-bit" : "");
                gp_fake_free(c);
                gp_fake_free(a); gp_fake_free(b);
            }
        }
        pc24();
    } else printf("[2] skipped: no Wine 11 d3dx9_27\n");

    /* [3] */
    for (UINT sz = 512; sz >= 256; sz /= 2) {
        enum { N = 40 };
        uint64_t t[5][N];
        long d11 = 0;
        for (int i = 0; i < N; i++) {
            gp_fake_tex *x[4];
            for (int j = 0; j < 4; j++) x[j] = gp_fake_create(sz, sz, 3, D3DFMT_A1R5G5B5, 2);
            UINT p; uint8_t *l0 = gp_fake_bits(x[0], 0, NULL, NULL, &p); terrain_fill(l0, sz, p, 0);
            for (int j = 1; j < 4; j++) copy0(x[j], x[0]);
            uint64_t t0 = now_us(); w10(gp_fake_base(x[0]), NULL, 0, 5);
            uint64_t t1 = now_us(); gp_mf_fast(gp_fake_base(x[1]), 0, 5);
            uint64_t t2 = now_us(); gp_tb_box(gp_fake_base(x[2]), 0, 1);
            uint64_t t3 = now_us(); if (w11) w11(gp_fake_base(x[3]), NULL, 0, 5);
            uint64_t t4 = now_us();
            copy0(x[1], x[0]);
            uint64_t t5 = now_us(); gp_tb_box(gp_fake_base(x[1]), 0, 0);
            uint64_t t6 = now_us();
            t[0][i] = t1 - t0; t[1][i] = t2 - t1; t[2][i] = t3 - t2; t[3][i] = t4 - t3; t[4][i] = t6 - t5;
            if (w11) d11 += diff_level(x[2], x[3], 1) + diff_level(x[2], x[3], 2);
            for (int j = 0; j < 4; j++) gp_fake_free(x[j]);
        }
        double m[5]; for (int j = 0; j < 5; j++) m[j] = median_ms(t[j], N);
        verdict(d11 != 0, "[3] %u terrain-like %ux%u A1R5G5B5, 3 levels, ms per texture (median): Wine 10 %.3f, mipfilter %.3f "
                "(point), terrainbox rounded %.3f, terrainbox exact %.3f (%s Wine 11: %s), Wine 11 %.3f\n", N, sz, sz, m[0], m[1],
                m[4], m[2], w11 ? "same as" : "vs", w11 ? (d11 ? "NO" : "yes") : "skipped", w11 ? m[3] : 0.0);
    }

    /* [4] */
    {
        enum { W = 256, N = 12 };
        double e[3][2] = {{0}}; uint64_t t[3][N];
        static uint32_t img[W * W], ref1[W / 2 * W / 2], ref2[W / 4 * W / 4], got[W / 2 * W / 2];
        for (int i = 0; i < N; i++) {
            terrain_fill((uint8_t *)img, W, W * 4, 1);
            gp_tb_level(D3DFMT_X8R8G8B8, (uint8_t *)img, W * 4, W, W, (uint8_t *)ref1, W / 2 * 4, 0);
            gp_tb_level(D3DFMT_X8R8G8B8, (uint8_t *)ref1, W / 2 * 4, W / 2, W / 2, (uint8_t *)ref2, W / 4 * 4, 0);
            gp_fake_tex *x[3];
            for (int j = 0; j < 3; j++) {
                x[j] = gp_fake_create(W, W, 3, D3DFMT_DXT1, 2);
                IDirect3DSurface9 *s; IDirect3DTexture9_GetSurfaceLevel((IDirect3DTexture9 *)gp_fake_base(x[j]), 0, &s);
                RECT r = {0, 0, W, W};
                w10load(s, NULL, NULL, img, D3DFMT_X8R8G8B8, W * 4, NULL, &r, 1, 0);
            }
            uint64_t t0 = now_us(); w10(gp_fake_base(x[0]), NULL, 0, 5);
            uint64_t t1 = now_us(); HRESULT r = gp_tb_dxt((const uint8_t *)img, gp_fake_base(x[1]), NULL, 0, 5);
            uint64_t t2 = now_us(); if (w11) w11(gp_fake_base(x[2]), NULL, 0, 5);
            uint64_t t3 = now_us();
            t[0][i] = t1 - t0; t[1][i] = t2 - t1; t[2][i] = t3 - t2;
            if (r != D3D_OK) fails++;
            for (int j = 0; j < 3; j++) {
                if (j == 2 && !w11) continue;
                dxt_to_32(x[j], 1, got); e[j][0] += rms(got, ref1, W / 2 * W / 2) / N;
                dxt_to_32(x[j], 2, got); e[j][1] += rms(got, ref2, W / 4 * W / 4) / N;
            }
            for (int j = 0; j < 3; j++) gp_fake_free(x[j]);
        }
        double m[3]; for (int j = 0; j < 3; j++) m[j] = median_ms(t[j], N);
        verdict(!(e[1][0] < e[0][0] && e[1][1] < e[0][1]) || gp_tb_stats[4] < N,
                "[4] %d DXT1 %dx%d terrain-like tiles, 3 levels: RMS error of levels 1 / 2 against the exact box of the "
                "uncompressed image: Wine 10 %.2f / %.2f (%.3f ms), terrainbox %.2f / %.2f (%.3f ms), Wine 11 %.2f / %.2f (%.3f ms)\n",
                N, W, W, e[0][0], e[0][1], m[0], e[1][0], e[1][1], m[1], e[2][0], e[2][1], m[2]);
    }

    /* [5] */
    {
        static const struct { const char *what; UINT w, h, n; D3DFORMAT f; UINT bpp; DWORD filter; int pal; } no[] = {
            {"300x170", 300, 170, 9, D3DFMT_A1R5G5B5, 2, 5, 0}, {"64x32 (a 2x1 level)", 64, 32, 7, D3DFMT_A1R5G5B5, 2, 5, 0},
            {"DXT3", 64, 64, 7, D3DFMT_DXT3, 2, 5, 0}, {"A8", 64, 64, 7, D3DFMT_A8, 1, 5, 0}};
        int good = 0;
        for (unsigned i = 0; i < sizeof no / sizeof no[0]; i++) {
            gp_fake_tex *a = gp_fake_create(no[i].w, no[i].h, no[i].n, no[i].f, no[i].bpp);
            good += gp_tb_box(gp_fake_base(a), 0, 0) == S_FALSE && gp_tb_box(gp_fake_base(a), 0, 1) == S_FALSE && !gp_fake_locks(a);
            gp_fake_free(a);
        }
        gp_tb_fn keep = gp_tb_next; gp_tb_next = stub_next; seen_n = 0;
        gp_fake_tex *a = gp_fake_create(64, 64, 7, D3DFMT_A1R5G5B5, 2);
        PALETTEENTRY pal[256];
        gp_tb_filter(gp_fake_base(a), pal, 0, 5); gp_tb_filter(gp_fake_base(a), NULL, 0, 2);
        good += seen_n == 2 && !gp_fake_locks(a);
        gp_fake_free(a);
        gp_tb_next = keep;
        verdict(good != 5, "[5] left alone, untouched (no lock, no byte): %d of 5 (300x170, 64x32, DXT3, A8; a palette or the "
                "point filter goes on to the next filter)\n", good);
    }

    /* [6] */
    {
        gp_tb_fn keep = gp_tb_next; gp_tb_next = stub_next; seen_n = 0;
        int st = gp_tb_state; gp_tb_state = -1;          /* straight to "next": only the stub's plumbing is tested */
        uint32_t delta = 1;
        static uint8_t buf[16];
        LONG c0 = gp_tb_stats[3];
        call_stub(buf, &delta);
        gp_tb_state = st; gp_tb_next = keep;
        verdict(delta != 0 || seen_n != 1 || gp_tb_stats[3] != c0 + 1, "[6] DXT1 site stub: reached gp_tb_dxt %s, stack after the call %s\n",
                gp_tb_stats[3] == c0 + 1 ? "yes" : "NO", delta == 0 ? "as before (4 arguments popped)" : "UNBALANCED");
        (void)seen_buf;
    }
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
