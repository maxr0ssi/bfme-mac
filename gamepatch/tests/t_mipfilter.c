/* t_mipfilter: mipfilter (p_mipfilter.c) against Wine's own D3DXFilterTexture (d3dx9_27, the builtin
 * this prefix loads: the same build as the game's), on in-memory textures (p_mipfilter_fake.c).
 *   [0] the patch applies to a relocated copy of the exe: the 8 call sites of the D3DXFilterTexture
 *       thunk call gp_mf_filter, and its original is the copy's thunk (through the import slot)
 *   [1] the first call runs the self-test, which passes, and takes the fast path
 *   [2] per format, 2048x2048 textures where the sampled pixel of the 2x2 blocks takes every 16-bit
 *       value (16-bit formats) or 2^20 spread values with every byte in every channel (32-bit), the
 *       other three random: all 12 levels byte for byte (rows and padding) as Wine's
 *   [3] terrain-like 512x512 and 256x256 A1R5G5B5 textures (the game's tile bakes): identical, and the
 *       time per texture, Wine's D3DXFilterTexture -> mipfilter
 *   [4] other sizes (not powers of two, 1-wide levels), D3DX_DEFAULT, srclevel 2: identical; a lock
 *       that fails half way: the fast path stops cleanly and the original redoes every level; what it
 *       leaves alone (point filter, DXT1, srclevel past the end) is not touched
 *   [5] sensitivity: a decimation that keeps the X bits, or samples another pixel of the block,
 *       differs from Wine
 * usage: t_mipfilter.exe <path to lotrbfme2ep1.exe 2.02> */
#define COBJMACROS
#include "orig.h"
#include "p_mipfilter.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#define AT(va) ((uint32_t *)(uintptr_t)(va))
static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs = 0x9e3779b9u;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
static uint32_t call_target(uint32_t va) { return va + 5 + *(int32_t *)(uintptr_t)(va + 1); }
static gp_mf_fn wine_filter;            /* d3dx9_27!D3DXFilterTexture itself */

static int same_tex(gp_fake_tex *a, gp_fake_tex *b, long *diff_bytes)
{
    int same = 1;
    for (UINT l = 0; l < 16; l++) {
        UINT h, p;
        uint8_t *x = gp_fake_bits(a, l, NULL, &h, &p), *y = gp_fake_bits(b, l, NULL, NULL, NULL);
        if (!x) break;
        if (memcmp(x, y, (size_t)h * p)) {
            same = 0;
            if (diff_bytes) for (size_t i = 0; i < (size_t)h * p; i++) *diff_bytes += x[i] != y[i];
        }
    }
    return same;
}
static void copy_levels(gp_fake_tex *dst, gp_fake_tex *src, UINT upto)
{
    for (UINT l = 0; l <= upto; l++) {
        UINT h, p;
        uint8_t *s = gp_fake_bits(src, l, NULL, &h, &p);
        if (s) memcpy(gp_fake_bits(dst, l, NULL, NULL, NULL), s, (size_t)h * p);
    }
}
static void fill_random(gp_fake_tex *t, UINT upto)
{
    for (UINT l = 0; l <= upto; l++) {
        UINT h, p;
        uint8_t *x = gp_fake_bits(t, l, NULL, &h, &p);
        if (x) for (size_t i = 0; i < (size_t)h * p; i++) x[i] = (uint8_t)rnd();
    }
}

static const struct { const char *name; D3DFORMAT f; UINT bpp; } F[] = {
    {"A8R8G8B8", D3DFMT_A8R8G8B8, 4}, {"X8R8G8B8", D3DFMT_X8R8G8B8, 4}, {"R5G6B5", D3DFMT_R5G6B5, 2},
    {"X1R5G5B5", D3DFMT_X1R5G5B5, 2}, {"A1R5G5B5", D3DFMT_A1R5G5B5, 2}, {"A4R4G4B4", D3DFMT_A4R4G4B4, 2},
    {"X4R4G4B4", D3DFMT_X4R4G4B4, 2}};
enum { NFMT = sizeof F / sizeof F[0] };

static void terrain_fill(gp_fake_tex *t)
{
    UINT w, h, p;
    uint8_t *l0 = gp_fake_bits(t, 0, &w, &h, &p);
    float fx = (rnd() % 1000) / 1000.0f, fy = (rnd() % 1000) / 1000.0f;
    for (UINT y = 0; y < h; y++)
        for (UINT x = 0; x < w; x++) {      /* two tile colours blended, with grain, as the bake gives */
            int g = (int)(rnd() % 24) - 12, k = (int)((x * fx + y * fy) * 0.25f) & 63;
            int r = 90 + k + g, gg = 80 + (k >> 1) + g, bb = 50 + (k >> 2) + g;
            r = r < 0 ? 0 : r > 255 ? 255 : r; gg = gg < 0 ? 0 : gg > 255 ? 255 : gg; bb = bb < 0 ? 0 : bb > 255 ? 255 : bb;
            ((uint16_t *)(l0 + y * p))[x] = (uint16_t)(0x8000 | (r >> 3) << 10 | (gg >> 3) << 5 | (bb >> 3));
        }
}
static int cmp_u64(const void *a, const void *b)
{
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return x < y ? -1 : x > y;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (!VirtualAlloc((void *)0xbd0000, 0xe10000 - 0xbd0000, MEM_RESERVE, PAGE_READWRITE)) {
        printf("cannot reserve the image's data range\nFAIL\n"); return 2;
    }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xbd0000, 0x1b9000, 0)) return 2;
    uint32_t off = orig_reserve_image();
    if (!off || orig_map_at(0x401000, 0x7cf000, off)) return 2;
    HMODULE dx = LoadLibraryA("d3dx9_27.dll");           /* after the image's ranges are taken */
    wine_filter = dx ? (gp_mf_fn)(void *)GetProcAddress(dx, "D3DXFilterTexture") : NULL;
    if (!wine_filter) { printf("cannot load d3dx9_27.dll\nFAIL\n"); return 2; }
    *AT(0xbd0a20) = (uint32_t)(uintptr_t)wine_filter;    /* the import, as the loader fills it */

    /* [0] */
    gp_va_offset = off;
    int ok = gp_patch_mipfilter();
    gp_va_offset = 0;
    static const uint32_t sites[] = {0x4eee4a, 0x4eefde, 0x4ef148, 0x530fea, 0x5312e7, 0x5313e3, 0x532198, 0x570cba};
    int nsite = 0;
    for (int i = 0; i < 8; i++) nsite += call_target(sites[i] + off) == (uint32_t)(uintptr_t)gp_mf_filter;
    ok = ok && nsite == 8 && (uint32_t)(uintptr_t)gp_mf_orig == 0xa3ecd2 + off;
    verdict(!ok, "[0] mipfilter: %s (%d of 8 call sites -> gp_mf_filter, original = the thunk copy)\n",
            ok ? "applied" : "NOT applied", nsite);
    if (!ok) { printf("FAIL\n"); return 1; }

    /* [1] */
    {
        gp_fake_tex *a = gp_fake_create(64, 64, 7, D3DFMT_A1R5G5B5, 2), *b = gp_fake_create(64, 64, 7, D3DFMT_A1R5G5B5, 2);
        fill_random(a, 0); copy_levels(b, a, 0);
        HRESULT ra = wine_filter(gp_fake_base(a), NULL, 0, 5), rb = gp_mf_filter(gp_fake_base(b), NULL, 0, 5);
        ok = ra == D3D_OK && rb == D3D_OK && gp_mf_state == 1 && gp_mf_stats[1] == 1 && same_tex(a, b, NULL);
        verdict(!ok, "[1] self-test %s; the first call %s, %s\n", gp_mf_state > 0 ? "passed" : "FAILED",
                gp_mf_stats[1] ? "fast" : "original", ok ? "identical" : "DIFFERENT");
        gp_fake_free(a); gp_fake_free(b);
    }

    /* [2] */
    for (int k = 0; k < NFMT; k++) {
        enum { S = 2048 };
        gp_fake_tex *a = gp_fake_create(S, S, 12, F[k].f, F[k].bpp), *b = gp_fake_create(S, S, 12, F[k].f, F[k].bpp);
        fill_random(a, 0);
        UINT p;
        uint8_t *l0 = gp_fake_bits(a, 0, NULL, NULL, &p);
        for (uint32_t i = 0; i < (S / 2) * (S / 2); i++) {
            uint8_t *px = l0 + (size_t)(2 * (i / (S / 2))) * p + (size_t)(2 * (i % (S / 2))) * F[k].bpp;
            if (F[k].bpp == 2) *(uint16_t *)px = (uint16_t)i;
            else *(uint32_t *)px = (i & 0xff) * 0x01010101u ^ (rnd() & ~0xffu) ^ ((i >> 8) << 24);
        }
        copy_levels(b, a, 0);
        uint64_t t0 = now_us();
        HRESULT ra = wine_filter(gp_fake_base(a), NULL, 0, 5);
        uint64_t t1 = now_us();
        HRESULT rb = gp_mf_fast(gp_fake_base(b), 0, 5);
        uint64_t t2 = now_us();
        long d = 0;
        ok = ra == D3D_OK && rb == S_OK && same_tex(a, b, &d);
        verdict(!ok, "[2] %-8s 2048x2048, every %s at the sampled pixels, 12 levels: %s (%ld bytes differ); Wine %.1f ms,"
                " mipfilter %.1f ms\n", F[k].name, F[k].bpp == 2 ? "16-bit value" : "byte in every channel",
                ok ? "identical" : "DIFFERENT", d, (t1 - t0) / 1000.0, (t2 - t1) / 1000.0);
        gp_fake_free(a); gp_fake_free(b);
    }

    /* [3] */
    for (int sz = 512; sz >= 256; sz /= 2) {
        enum { N = 40 };
        uint64_t tw[N], tf[N];
        int same = 1;
        LONG f0 = gp_mf_stats[1];
        for (int i = 0; i < N; i++) {
            gp_fake_tex *a = gp_fake_create(sz, sz, 16, D3DFMT_A1R5G5B5, 2), *b = gp_fake_create(sz, sz, 16, D3DFMT_A1R5G5B5, 2);
            terrain_fill(a); copy_levels(b, a, 0);
            uint64_t t0 = now_us();
            HRESULT ra = wine_filter(gp_fake_base(a), NULL, 0, 5);
            uint64_t t1 = now_us();
            HRESULT rb = gp_mf_filter(gp_fake_base(b), NULL, 0, 5);
            uint64_t t2 = now_us();
            tw[i] = t1 - t0; tf[i] = t2 - t1;
            same &= ra == D3D_OK && rb == D3D_OK && same_tex(a, b, NULL);
            gp_fake_free(a); gp_fake_free(b);
        }
        same &= gp_mf_stats[1] - f0 == N;
        qsort(tw, N, sizeof tw[0], cmp_u64); qsort(tf, N, sizeof tf[0], cmp_u64);
        verdict(!same, "[3] %d terrain-like %dx%d A1R5G5B5 textures through the wrapper: %s; per texture (median, min-max)"
                " Wine %.3f ms (%.3f-%.3f) -> mipfilter %.3f ms (%.3f-%.3f), %.0fx\n", N, sz, sz, same ? "identical" : "DIFFERENT",
                tw[N / 2] / 1000.0, tw[0] / 1000.0, tw[N - 1] / 1000.0, tf[N / 2] / 1000.0, tf[0] / 1000.0,
                tf[N - 1] / 1000.0, (double)tw[N / 2] / (tf[N / 2] ? tf[N / 2] : 1));
    }

    /* [4] other shapes and arguments, every format */
    static const struct { UINT w, h, src; DWORD filter; } shp[] = {
        {300, 170, 0, 5}, {512, 256, 0, 0xffffffffu}, {1, 64, 0, 5}, {64, 1, 0, 5}, {48, 20, 0, 0xffffffffu},
        {7, 3, 0, 5}, {128, 128, 2, 5}, {256, 256, 0xffffffffu, 0xffffffffu}};
    int nshape = 0, nsame = 0;
    for (int k = 0; k < NFMT; k++)
        for (unsigned s = 0; s < sizeof shp / sizeof shp[0]; s++) {
            gp_fake_tex *a = gp_fake_create(shp[s].w, shp[s].h, 16, F[k].f, F[k].bpp), *b = gp_fake_create(shp[s].w, shp[s].h, 16, F[k].f, F[k].bpp);
            UINT src = shp[s].src == 0xffffffffu ? 0 : shp[s].src;
            fill_random(a, src); copy_levels(b, a, src);
            HRESULT ra = wine_filter(gp_fake_base(a), NULL, shp[s].src, shp[s].filter);
            HRESULT rb = gp_mf_fast(gp_fake_base(b), shp[s].src, shp[s].filter);
            nshape++; nsame += ra == D3D_OK && rb == S_OK && same_tex(a, b, NULL) && !gp_fake_open(b);
            gp_fake_free(a); gp_fake_free(b);
        }
    verdict(nsame != nshape, "[4] %d of %d (format, shape) cases identical: 300x170, 512x256 (DEFAULT), 1x64, 64x1, 48x20"
            " (DEFAULT), 7x3, srclevel 2, srclevel DEFAULT\n", nsame, nshape);
    {
        gp_fake_tex *a = gp_fake_create(256, 256, 9, D3DFMT_A1R5G5B5, 2), *b = gp_fake_create(256, 256, 9, D3DFMT_A1R5G5B5, 2);
        fill_random(a, 8); copy_levels(b, a, 8);             /* junk in the lower levels: all must be rewritten */
        fill_random(b, 0); copy_levels(b, a, 0);
        HRESULT ra = wine_filter(gp_fake_base(a), NULL, 0, 5);
        gp_fake_fail_locks(b, 7);                             /* the 7th lock: level 4's source */
        LONG lf = gp_mf_stats[4];
        HRESULT rf = gp_mf_fast(gp_fake_base(b), 0, 5);
        int open = gp_fake_open(b);
        gp_fake_fail_locks(b, 0);
        HRESULT ro = wine_filter(gp_fake_base(b), NULL, 0, 5);  /* what gp_mf_filter does next */
        ok = FAILED(rf) && !open && ra == D3D_OK && ro == D3D_OK && same_tex(a, b, NULL) && gp_mf_stats[4] == lf;
        verdict(!ok, "[4] a lock fails half way: fast path %08lx with %d locks left open; the original then: %s\n",
                rf, open, ok ? "same as Wine's" : "DIFFERENT");
        gp_fake_free(a); gp_fake_free(b);
    }
    {
        static const struct { const char *what; D3DFORMAT f; UINT bpp, src; DWORD filter; } no[] = {
            {"point filter", D3DFMT_A1R5G5B5, 2, 0, 2}, {"linear filter", D3DFMT_A8R8G8B8, 4, 0, 3},
            {"triangle filter", D3DFMT_A8R8G8B8, 4, 0, 4}, {"DXT1", D3DFMT_DXT1, 2, 0, 5},
            {"A8", D3DFMT_A8, 1, 0, 5}, {"srclevel past the end", D3DFMT_A1R5G5B5, 2, 7, 5}};
        int good = 0;
        for (unsigned i = 0; i < sizeof no / sizeof no[0]; i++) {
            gp_fake_tex *a = gp_fake_create(64, 64, 7, no[i].f, no[i].bpp), *b = gp_fake_create(64, 64, 7, no[i].f, no[i].bpp);
            fill_random(a, 6); copy_levels(b, a, 6);
            HRESULT r = gp_mf_fast(gp_fake_base(b), no[i].src, no[i].filter);
            good += r == S_FALSE && !gp_fake_locks(b) && same_tex(a, b, NULL);
            gp_fake_free(a); gp_fake_free(b);
        }
        verdict(good != 6, "[4] left to the original, untouched (no lock, no byte): %d of 6 (point, linear, triangle,"
                " DXT1, A8, srclevel past the end)\n", good);
    }

    /* [5] */
    {
        gp_fake_tex *a = gp_fake_create(256, 256, 9, D3DFMT_X1R5G5B5, 2);
        fill_random(a, 0);
        wine_filter(gp_fake_base(a), NULL, 0, 5);
        UINT p0, p1;
        uint8_t *l0 = gp_fake_bits(a, 0, NULL, NULL, &p0), *l1 = gp_fake_bits(a, 1, NULL, NULL, &p1);
        long keepx = 0, other = 0;
        for (UINT y = 0; y < 128; y++)
            for (UINT x = 0; x < 128; x++) {
                uint16_t w = ((uint16_t *)(l1 + y * p1))[x];
                keepx += w != ((uint16_t *)(l0 + 2 * y * p0))[2 * x];
                other += w != (((uint16_t *)(l0 + (2 * y + 1) * p0))[2 * x + 1] & 0x7fff);
            }
        gp_fake_free(a);
        verdict(!keepx || !other, "[5] X1R5G5B5 level 1 against Wine: keeping the X bit differs in %ld of 16384 pixels,"
                " sampling the bottom-right pixel in %ld\n", keepx, other);
    }
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
