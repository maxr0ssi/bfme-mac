/* terrainbox (OFF by default; a picture change, the player's choice): the terrain tile textures get
 * box-filtered mip levels, as Windows' d3dx9 and Wine 11's give them, instead of the point-sampled
 * ones of the installed Wine 10 d3dx9_27 (docs/PERFORMANCE.md §23, §26).
 *
 * The terrain is drawn in tiles of 16 x 16 cells; each tile's textures are baked on the CPU from the
 * map's source tiles and then get their mip levels from D3DXFilterTexture(tex, NULL, 0, BOX)
 * (TerrainTextureClass, 3 levels: 512/256/128 near, 256/128/64 far). Wine 10.0's d3dx9 has no box
 * filter: every level takes the top-left pixel of each 2x2 block (mipfilter reproduces that fast).
 * Point-sampled levels alias, and each one sits half a texel off the level above, so distant and
 * moving terrain shimmers and swims where Windows shows it smooth. Three call sites:
 *   0x4eee4a  A1R5G5B5 tile bake 0x4eec82 (near tiles: colour 0x511fe1 and normal map 0x51204e;
 *             far tiles' normal map 0x514969; far colour when not compressed 0x5148f9)
 *   0x4ef148  A1R5G5B5 texture-class atlas 0x4ef000
 *   0x4eefde  DXT1 tile bake 0x4eee64 (far tiles' colour, all built at map load)
 * The 16-bit sites get gp_tb_box: Wine 11's box_filter_argb_pixels to the bit (float per channel,
 * summed top-left, top-right, bottom-left, bottom-right, x0.25, x max + 0.5, truncated). That is
 * (sum + 2) >> 2 for 1-, 4-, 6- and 8-bit channels; for 5-bit channels the float error rounds some
 * exact halves down, so a 128 KB bitmap built from the float formula at first use says which
 * (a, b, c, d) do (gamepatch/tests/t_terrainbox.c checks every one of the 2^20 against Wine 11's
 * d3dx9_27 in the game's FPU mode). The DXT1 site gets each level box-filtered from the bake's
 * uncompressed X8R8G8B8 image (still in its frame at the call) and compressed by the game's own
 * D3DXLoadSurfaceFromMemory, as the bake compresses level 0: no decompress-filter-recompress
 * round trip. Anything else (other sizes or formats, a failed lock) runs what the site called
 * before (mipfilter, else Wine's function).
 *
 * Before the first use: the fast path is checked against the float reference on in-memory textures
 * of every format, and the installed d3dx9's own D3DXFilterTexture is asked to filter one: if it
 * already box-filters (Wine 11 installed) or gives neither result, the patch stays off. */
#define COBJMACROS
#include "p_terrain.h"
#include "p_mipfilter.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <emmintrin.h>

#define THUNK_FILTER 0xa3ecd2u          /* jmp *0xbd0a20 (D3DXFilterTexture) */
#define THUNK_LOAD   0xa3ecd8u          /* jmp *0xbd0a1c (D3DXLoadSurfaceFromMemory) */
#define FILTER_BOX   5u
#define DX_DEFAULT   0xffffffffu
#define SITE_DXT     0x4eefde

gp_tb_fn gp_tb_next;
gp_tb_load_fn gp_tb_load;
int gp_tb_state;
int gp_tb_mode = 1;
volatile LONG gp_tb_stats[9];
static LONGLONG qfreq;

static const struct { D3DFORMAT f; UINT bpp; } fmts[] = {
    {D3DFMT_A8R8G8B8, 4}, {D3DFMT_X8R8G8B8, 4}, {D3DFMT_R5G6B5, 2}, {D3DFMT_X1R5G5B5, 2},
    {D3DFMT_A1R5G5B5, 2}, {D3DFMT_A4R4G4B4, 2}, {D3DFMT_X4R4G4B4, 2}};
enum { NF = sizeof fmts / sizeof fmts[0] };
static int fmt_index(D3DFORMAT f)
{
    for (int k = 0; k < NF; k++) if (fmts[k].f == f) return k;
    return -1;
}

/* ---- the reference: Wine 11's arithmetic, one channel --------------------------------------- */
static unsigned ref_ch(unsigned max, unsigned a, unsigned b, unsigned c, unsigned d)
{
    volatile float m = (float)max;      /* a real division each time, as Wine's (float)v / mask */
    float s = (float)a / m;
    s += (float)b / m;
    s += (float)c / m;
    s += (float)d / m;
    s *= 0.25f;
    if (s > 1.0f) s = 1.0f;
    if (!(s >= 0.0f)) s = 0.0f;
    return (unsigned)(s * m + 0.5f);
}

/* channel layout per format: shift and bits of A, R, G, B (0 bits: absent, comes out 0) */
static const struct { uint8_t sh[4], bits[4]; } lay[NF] = {
    {{24, 16, 8, 0}, {8, 8, 8, 8}}, {{24, 16, 8, 0}, {0, 8, 8, 8}}, {{0, 11, 5, 0}, {0, 5, 6, 5}},
    {{15, 10, 5, 0}, {0, 5, 5, 5}}, {{15, 10, 5, 0}, {1, 5, 5, 5}}, {{12, 8, 4, 0}, {4, 4, 4, 4}},
    {{12, 8, 4, 0}, {0, 4, 4, 4}}};

static uint32_t px(const uint8_t *p, UINT bpp) { return bpp == 2 ? *(const uint16_t *)p : *(const uint32_t *)p; }

int gp_tb_level_ref(D3DFORMAT f, const uint8_t *src, UINT sp, UINT sw, UINT sh, uint8_t *dst, UINT dp, int exact)
{
    int k = fmt_index(f);
    if (k < 0 || sw < 2 || sh < 2) return 0;
    UINT bpp = fmts[k].bpp;
    for (UINT y = 0; y < sh / 2; y++)
        for (UINT x = 0; x < sw / 2; x++) {
            const uint8_t *r0 = src + (size_t)2 * y * sp + 2 * x * bpp, *r1 = r0 + sp;
            uint32_t q[4] = {px(r0, bpp), px(r0 + bpp, bpp), px(r1, bpp), px(r1 + bpp, bpp)}, o = 0;
            for (int c = 0; c < 4; c++) {
                unsigned n = lay[k].bits[c], s = lay[k].sh[c], m = (1u << n) - 1;
                if (!n) continue;
                unsigned a = q[0] >> s & m, b = q[1] >> s & m, c = q[2] >> s & m, d = q[3] >> s & m;
                o |= (exact ? ref_ch(m, a, b, c, d) : (a + b + c + d + 2) / 4) << s;
            }
            if (bpp == 2) ((uint16_t *)(dst + (size_t)y * dp))[x] = (uint16_t)o;
            else ((uint32_t *)(dst + (size_t)y * dp))[x] = o;
        }
    return 1;
}

/* ---- the fast path -------------------------------------------------------------------------- */
static uint32_t tie5[1 << 15];          /* bit a|b<<5|c<<10|d<<15 set: this exact half rounds down */
static volatile LONG tie5_ready;

static void tie5_build(void)
{
    if (tie5_ready) return;
    static uint32_t t[1 << 15];
    for (uint32_t i = 0; i < 1u << 20; i++) {
        unsigned a = i & 31, b = i >> 5 & 31, c = i >> 10 & 31, d = i >> 15, s = a + b + c + d;
        if ((s & 3) == 2 && ref_ch(31, a, b, c, d) != (s + 2) >> 2) t[i >> 5] |= 1u << (i & 31);
    }
    memcpy(tie5, t, sizeof tie5);
    InterlockedExchange(&tie5_ready, 1);
}
#define TIE(i) (tie5[(i) >> 5] >> ((i) & 31) & 1)

/* t: the 5-bit lanes (bits 0, 10, 20 of the spread sum s) whose sum is 2 mod 4. The four pixels'
 * spread values e0..e3 hold each 5-bit channel at the bottom of a 10-bit lane, so x = e0 | e1 << 5
 * and y = e2 | e3 << 5 hold every lane's bitmap index (a | b << 5, c | d << 5) at once. The lookups
 * are made for every lane and masked, as a branch on t mispredicts on most terrain pixels. */
static inline uint32_t fix5(uint32_t r, uint32_t t, uint32_t x, uint32_t y, int l1)
{
    uint32_t i0 = (x & 1023) | (y & 1023) << 10, i2 = (x >> 20 & 1023) | (y >> 20 & 1023) << 10;
    uint32_t m = TIE(i0) | TIE(i2) << 20;
    if (l1) { uint32_t i1 = (x >> 10 & 1023) | (y >> 10 & 1023) << 10; m |= TIE(i1) << 10; }
    return r - (m & t);
}

/* the rounded average, 8 pixels at a time (SSE2): the four pixels of each block as 16-bit lanes */
#define CH(sh, m) _mm_slli_epi16(_mm_srli_epi16(_mm_add_epi16(_mm_add_epi16( \
        _mm_add_epi16(_mm_and_si128(_mm_srli_epi16(a, sh), m), _mm_and_si128(_mm_srli_epi16(b, sh), m)), \
        _mm_add_epi16(_mm_and_si128(_mm_srli_epi16(c, sh), m), _mm_and_si128(_mm_srli_epi16(d, sh), m))), two), 2), sh)
static UINT sse16(D3DFORMAT f, const uint16_t *r0, const uint16_t *r1, uint16_t *o, UINT dw)
{
    const __m128i m31 = _mm_set1_epi16(31), m63 = _mm_set1_epi16(63), m15 = _mm_set1_epi16(15),
                  m1 = _mm_set1_epi16(1), two = _mm_set1_epi16(2);
    UINT x = 0;
    for (; x + 8 <= dw; x += 8) {
        __m128i u0 = _mm_loadu_si128((const __m128i *)(r0 + 2 * x)), u1 = _mm_loadu_si128((const __m128i *)(r0 + 2 * x + 8));
        __m128i v0 = _mm_loadu_si128((const __m128i *)(r1 + 2 * x)), v1 = _mm_loadu_si128((const __m128i *)(r1 + 2 * x + 8));
        /* even pixels (sign-extended so the signed pack keeps them), odd pixels */
        __m128i a = _mm_packs_epi32(_mm_srai_epi32(_mm_slli_epi32(u0, 16), 16), _mm_srai_epi32(_mm_slli_epi32(u1, 16), 16));
        __m128i b = _mm_packs_epi32(_mm_srai_epi32(u0, 16), _mm_srai_epi32(u1, 16));
        __m128i c = _mm_packs_epi32(_mm_srai_epi32(_mm_slli_epi32(v0, 16), 16), _mm_srai_epi32(_mm_slli_epi32(v1, 16), 16));
        __m128i d = _mm_packs_epi32(_mm_srai_epi32(v0, 16), _mm_srai_epi32(v1, 16));
        __m128i r;
        switch (f) {
        case D3DFMT_A1R5G5B5: r = _mm_or_si128(_mm_or_si128(CH(0, m31), CH(5, m31)), _mm_or_si128(CH(10, m31), CH(15, m1))); break;
        case D3DFMT_X1R5G5B5: r = _mm_or_si128(_mm_or_si128(CH(0, m31), CH(5, m31)), CH(10, m31)); break;
        case D3DFMT_R5G6B5:   r = _mm_or_si128(_mm_or_si128(CH(0, m31), CH(5, m63)), CH(11, m31)); break;
        case D3DFMT_A4R4G4B4: r = _mm_or_si128(_mm_or_si128(CH(0, m15), CH(4, m15)), _mm_or_si128(CH(8, m15), CH(12, m15))); break;
        default:              r = _mm_or_si128(_mm_or_si128(CH(0, m15), CH(4, m15)), CH(8, m15)); break;   /* X4R4G4B4 */
        }
        _mm_storeu_si128((__m128i *)(o + x), r);
    }
    return x;
}

int gp_tb_level(D3DFORMAT f, const uint8_t *src, UINT sp, UINT sw, UINT sh, uint8_t *dst, UINT dp, int exact)
{
    int k = fmt_index(f);
    if (k < 0 || sw < 2 || sh < 2) return 0;
    UINT dw = sw / 2, dh = sh / 2;
    uint32_t tmask = exact ? 0xffffffffu : 0;   /* the rounded average: no exact-half correction */
    for (UINT y = 0; y < dh; y++) {
        const uint8_t *a = src + (size_t)2 * y * sp, *b = a + sp;
        uint8_t *o8 = dst + (size_t)y * dp;
        if (fmts[k].bpp == 4) {
            const uint32_t *r0 = (const uint32_t *)a, *r1 = (const uint32_t *)b;
            uint32_t *o = (uint32_t *)o8, keep = f == D3DFMT_X8R8G8B8 ? 0x00ffffffu : 0xffffffffu;
            for (UINT x = 0; x < dw; x++) {
                uint32_t p0 = r0[2 * x], p1 = r0[2 * x + 1], p2 = r1[2 * x], p3 = r1[2 * x + 1];
                uint32_t e = (p0 & 0x00ff00ff) + (p1 & 0x00ff00ff) + (p2 & 0x00ff00ff) + (p3 & 0x00ff00ff);
                uint32_t g = (p0 >> 8 & 0x00ff00ff) + (p1 >> 8 & 0x00ff00ff) + (p2 >> 8 & 0x00ff00ff) + (p3 >> 8 & 0x00ff00ff);
                e = (e + 0x00020002) >> 2 & 0x00ff00ff;
                g = (g + 0x00020002) >> 2 & 0x00ff00ff;
                o[x] = (e | g << 8) & keep;
            }
            continue;
        }
        const uint16_t *r0 = (const uint16_t *)a, *r1 = (const uint16_t *)b;
        uint16_t *o = (uint16_t *)o8;
        UINT x0 = exact ? 0 : sse16(f, r0, r1, o, dw);
        switch (f) {
        case D3DFMT_A1R5G5B5: case D3DFMT_X1R5G5B5: {
            int alpha = f == D3DFMT_A1R5G5B5;
            for (UINT x = x0; x < dw; x++) {
                uint32_t p0 = r0[2 * x], p1 = r0[2 * x + 1], p2 = r1[2 * x], p3 = r1[2 * x + 1];
#define SP555(p) (((p) & 0x1f) | ((p) & 0x3e0) << 5 | ((p) & 0x7c00) << 10)
                uint32_t e0 = SP555(p0), e1 = SP555(p1), e2 = SP555(p2), e3 = SP555(p3), s = e0 + e1 + e2 + e3;
                uint32_t r = (s + 0x00200802) >> 2, t = (s >> 1) & ~s & 0x00100401 & tmask;
                r = fix5(r, t, e0 | e1 << 5, e2 | e3 << 5, 1);
                uint32_t v = (r & 0x1f) | (r >> 5 & 0x3e0) | (r >> 10 & 0x7c00);
                if (alpha && (p0 >> 15) + (p1 >> 15) + (p2 >> 15) + (p3 >> 15) >= 2) v |= 0x8000;
                o[x] = (uint16_t)v;
            }
            break;
        }
        case D3DFMT_R5G6B5:
            for (UINT x = x0; x < dw; x++) {
                uint32_t p0 = r0[2 * x], p1 = r0[2 * x + 1], p2 = r1[2 * x], p3 = r1[2 * x + 1];
#define SP565(p) (((p) & 0x1f) | ((p) & 0x7e0) << 5 | ((p) & 0xf800) << 9)
                uint32_t e0 = SP565(p0), e1 = SP565(p1), e2 = SP565(p2), e3 = SP565(p3), s = e0 + e1 + e2 + e3;
                uint32_t r = (s + 0x00200802) >> 2, t = (s >> 1) & ~s & 0x00100001 & tmask;
                r = fix5(r, t, (e0 & 0x01f0001f) | (e1 & 0x01f0001f) << 5, (e2 & 0x01f0001f) | (e3 & 0x01f0001f) << 5, 0);
                o[x] = (uint16_t)((r & 0x1f) | (r >> 5 & 0x7e0) | (r >> 9 & 0xf800));
            }
            break;
        default: {   /* A4R4G4B4, X4R4G4B4 */
            uint32_t keep = f == D3DFMT_X4R4G4B4 ? 0x0fffu : 0xffffu;
            for (UINT x = x0; x < dw; x++) {
                uint32_t p0 = r0[2 * x], p1 = r0[2 * x + 1], p2 = r1[2 * x], p3 = r1[2 * x + 1];
#define SP4(p) (((p) & 0x0f0f) | ((p) & 0xf0f0) << 12)
                uint32_t r = (SP4(p0) + SP4(p1) + SP4(p2) + SP4(p3) + 0x02020202) >> 2 & 0x0f0f0f0f;
                o[x] = (uint16_t)(((r & 0x0f0f) | (r >> 12 & 0xf0f0)) & keep);
            }
        }
        }
    }
    return 1;
}

/* every level of a 2D texture whose levels below srclevel each halve a power-of-two level of at
 * least 2 x 2 (what Wine 11 box-filters; it reads past a 1-pixel-high level, so those are left) */
HRESULT gp_tb_box(IDirect3DBaseTexture9 *base, UINT src, int exact)
{
    if (!base) return S_FALSE;
    UINT n = IDirect3DBaseTexture9_GetLevelCount(base);
    if (src == DX_DEFAULT) src = 0;
    if (src >= n || n > 16 || IDirect3DBaseTexture9_GetType(base) != D3DRTYPE_TEXTURE) return S_FALSE;
    IDirect3DTexture9 *t = (IDirect3DTexture9 *)base;
    D3DSURFACE_DESC d[16];
    for (UINT l = src; l < n; l++) {
        if (FAILED(IDirect3DTexture9_GetLevelDesc(t, l, &d[l])) || d[l].MultiSampleType != D3DMULTISAMPLE_NONE ||
            d[l].Format != d[src].Format)
            return S_FALSE;
        if (l > src) {
            UINT pw = d[l - 1].Width, ph = d[l - 1].Height;
            if (pw < 2 || ph < 2 || (pw & (pw - 1)) || (ph & (ph - 1)) || d[l].Width != pw / 2 || d[l].Height != ph / 2)
                return S_FALSE;
        }
    }
    if (fmt_index(d[src].Format) < 0) return S_FALSE;
    if (exact) tie5_build();
    for (UINT l = src + 1; l < n; l++) {
        D3DLOCKED_RECT a, b;
        RECT full = {0, 0, (LONG)d[l].Width, (LONG)d[l].Height};
        if (FAILED(IDirect3DTexture9_LockRect(t, l - 1, &a, NULL, D3DLOCK_READONLY))) return E_FAIL;
        if (FAILED(IDirect3DTexture9_LockRect(t, l, &b, &full, 0))) {
            IDirect3DTexture9_UnlockRect(t, l - 1);
            return E_FAIL;
        }
        gp_tb_level(d[src].Format, a.pBits, a.Pitch, d[l - 1].Width, d[l - 1].Height, b.pBits, b.Pitch, exact);
        IDirect3DTexture9_UnlockRect(t, l);
        IDirect3DTexture9_UnlockRect(t, l - 1);
        gp_tb_stats[2]++;
    }
    return S_OK;
}

/* ---- DXT1 tiles: each level from the uncompressed image, compressed by D3DX ---------------- */
static HRESULT dxt_box(const uint8_t *buf, IDirect3DTexture9 *t)
{
    D3DSURFACE_DESC d0;
    UINT n = IDirect3DTexture9_GetLevelCount(t);
    if (FAILED(IDirect3DTexture9_GetLevelDesc(t, 0, &d0)) || d0.Format != D3DFMT_DXT1 || d0.Width != d0.Height ||
        d0.Width < 4 || (d0.Width & (d0.Width - 1)) || n < 2 || n > 16)
        return S_FALSE;
    UINT w = d0.Width;
    for (UINT l = 1; l < n; l++) {
        D3DSURFACE_DESC d;
        if (FAILED(IDirect3DTexture9_GetLevelDesc(t, l, &d)) || d.Format != D3DFMT_DXT1 || d.Width != w >> l ||
            d.Height != w >> l || d.Width < 1)
            return S_FALSE;
    }
    uint8_t *tmp = malloc((size_t)w * w + (size_t)w * w / 4);   /* odd levels at 0, even ones after */
    if (!tmp) return S_FALSE;
    const uint8_t *prev = buf;
    UINT pw = w;
    HRESULT hr = S_OK;
    for (UINT l = 1; l < n && pw >= 2; l++, pw /= 2) {
        uint8_t *out = (l & 1) ? tmp : tmp + (size_t)w * w;
        gp_tb_level(D3DFMT_X8R8G8B8, prev, pw * 4, pw, pw, out, pw / 2 * 4, 0);   /* 8-bit: both modes agree */
        IDirect3DSurface9 *s = NULL;
        if (FAILED(IDirect3DTexture9_GetSurfaceLevel(t, l, &s)) || !s) { hr = E_FAIL; break; }
        RECT r = {0, 0, (LONG)(pw / 2), (LONG)(pw / 2)};
        hr = gp_tb_load(s, NULL, NULL, out, D3DFMT_X8R8G8B8, pw / 2 * 4, NULL, &r, 1 /* D3DX_FILTER_NONE */, 0);
        IDirect3DSurface9_Release(s);
        if (FAILED(hr)) break;
        prev = out;
        gp_tb_stats[2]++;
    }
    free(tmp);
    return hr;
}

/* ---- self-test and the d3dx9 check ----------------------------------------------------------- */
static uint32_t rs = 0x6a09e667u;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }

int gp_tb_selftest(char *why, int cap)
{
    why[0] = 0;
    tie5_build();
    static uint8_t a[64 * 64 * 4], b[32 * 32 * 4], c[32 * 32 * 4];
    for (int exact = 0; exact < 2; exact++)
        for (int k = 0; k < NF; k++)
            for (int kind = 0; kind < 3; kind++) {   /* random; smooth (many exact halves); 0x00 / 0xff */
                UINT bpp = fmts[k].bpp, sp = 64 * bpp;
                uint32_t base = rnd();
                for (UINT i = 0; i < 64 * 64; i++) {
                    uint32_t v = kind == 0 ? rnd() : kind == 1 ? base + (rnd() & 0x03030303) * (bpp == 2 ? 0x21 : 1)
                                                             : (rnd() & 1 ? 0xffffffffu : 0);
                    if (bpp == 2) ((uint16_t *)a)[i] = (uint16_t)v; else ((uint32_t *)a)[i] = v;
                }
                gp_tb_level(fmts[k].f, a, sp, 64, 64, b, 32 * bpp, exact);
                gp_tb_level_ref(fmts[k].f, a, sp, 64, 64, c, 32 * bpp, exact);
                if (memcmp(b, c, 32 * 32 * bpp)) {
                    snprintf(why, cap, "format %u (%s data, %s) differs from its reference", (unsigned)fmts[k].f,
                             kind == 0 ? "random" : kind == 1 ? "smooth" : "black/white", exact ? "Wine 11 exact" : "rounded");
                    return 0;
                }
            }
    /* the whole texture path on an in-memory A1R5G5B5 texture, 3 levels like a terrain tile */
    for (int exact = 0; exact < 2; exact++) {
        gp_fake_tex *t = gp_fake_create(64, 64, 3, D3DFMT_A1R5G5B5, 2);
        if (!t) { snprintf(why, cap, "out of memory"); return 0; }
        UINT p0, p1;
        uint8_t *l0 = gp_fake_bits(t, 0, NULL, NULL, &p0);
        for (UINT y = 0; y < 64; y++) for (UINT x = 0; x < 64; x++) ((uint16_t *)(l0 + y * p0))[x] = (uint16_t)rnd();
        HRESULT r = gp_tb_box(gp_fake_base(t), 0, exact);
        uint8_t *l1 = gp_fake_bits(t, 1, NULL, NULL, &p1);
        static uint8_t ref[32 * 64];
        gp_tb_level_ref(D3DFMT_A1R5G5B5, l0, p0, 64, 64, ref, 64, exact);
        int same = r == S_OK && !gp_fake_open(t);
        for (UINT y = 0; same && y < 32; y++) same = !memcmp(l1 + y * p1, ref + y * 64, 64);
        gp_fake_free(t);
        if (!same) { snprintf(why, cap, "the texture path differs (%08lx)", r); return 0; }
    }
    return 1;
}

/* what the installed D3DXFilterTexture does with a box-filter call: 1 point (Wine 10), 2 box, 0 other */
static int d3dx_kind(gp_tb_fn thunk)
{
    gp_fake_tex *t = gp_fake_create(16, 16, 2, D3DFMT_A1R5G5B5, 2);
    if (!t) return 0;
    UINT p0, p1;
    uint8_t *l0 = gp_fake_bits(t, 0, NULL, NULL, &p0);
    for (UINT y = 0; y < 16; y++) for (UINT x = 0; x < 16; x++) ((uint16_t *)(l0 + y * p0))[x] = (uint16_t)rnd();
    HRESULT r = thunk(gp_fake_base(t), NULL, 0, FILTER_BOX);
    uint8_t *l1 = gp_fake_bits(t, 1, NULL, NULL, &p1);
    static uint8_t box[2][8 * 16];
    gp_tb_level_ref(D3DFMT_A1R5G5B5, l0, p0, 16, 16, box[0], 16, 0);
    gp_tb_level_ref(D3DFMT_A1R5G5B5, l0, p0, 16, 16, box[1], 16, 1);
    int point = 1, box0 = 1, box1 = 1;
    for (UINT y = 0; y < 8; y++)
        for (UINT x = 0; x < 8; x++) {
            uint16_t v = ((uint16_t *)(l1 + y * p1))[x];
            point &= v == ((uint16_t *)(l0 + 2 * y * p0))[2 * x];
            box0 &= v == ((uint16_t *)(box[0] + y * 16))[x];
            box1 &= v == ((uint16_t *)(box[1] + y * 16))[x];
        }
    int isbox = box0 || box1;
    gp_fake_free(t);
    return r != D3D_OK ? 0 : point ? 1 : isbox ? 2 : 0;
}

static void first_use(void)
{
    char why[160];
    if (!gp_tb_selftest(why, sizeof why)) {
        gp_tb_state = -1;
        gp_log("terrainbox: self-test failed (%s); mip levels as before", why);
        return;
    }
    int k = d3dx_kind((gp_tb_fn)(uintptr_t)(THUNK_FILTER + gp_va_offset));
    gp_tb_state = k == 1 ? 1 : -1;
    if (k == 1) gp_log("terrainbox: self-test passed (%d formats); terrain tile mip levels box-filtered (%s)", NF,
                       gp_tb_mode == 2 ? "Wine 11's arithmetic to the bit" : "rounded average");
    else gp_log("terrainbox: the installed d3dx9_27 %s; left to it", k == 2 ? "already box-filters" : "gives neither point nor box levels");
}

/* ---- the call sites' replacements ----------------------------------------------------------- */
static LONGLONG qpc(void) { LARGE_INTEGER x; QueryPerformanceCounter(&x); return x.QuadPart; }
static LONG us(LONGLONG t0) { return (LONG)((qpc() - t0) * 1000000 / qfreq); }

__attribute__((force_align_arg_pointer))
HRESULT WINAPI gp_tb_filter(IDirect3DBaseTexture9 *tex, const PALETTEENTRY *pal, UINT src, DWORD filter)
{
    gp_tb_stats[0]++;
    if (!gp_tb_state) first_use();
    LONGLONG t0 = qpc();
    if (gp_tb_state > 0 && (filter == FILTER_BOX || filter == DX_DEFAULT) && !pal) {
        HRESULT r = gp_tb_box(tex, src, gp_tb_mode == 2);
        if (r == S_OK) { gp_tb_stats[1]++; gp_tb_stats[6] += us(t0); return D3D_OK; }
    }
    HRESULT r = gp_tb_next(tex, pal, src, filter);
    gp_tb_stats[5]++; gp_tb_stats[8] += us(t0);
    return r;
}

__attribute__((force_align_arg_pointer))
HRESULT WINAPI gp_tb_dxt(const uint8_t *buf, IDirect3DBaseTexture9 *tex, const PALETTEENTRY *pal, UINT src, DWORD filter)
{
    gp_tb_stats[3]++;
    if (!gp_tb_state) first_use();
    LONGLONG t0 = qpc();
    if (gp_tb_state > 0 && buf && tex && filter == FILTER_BOX && !src && !pal &&
        IDirect3DBaseTexture9_GetType(tex) == D3DRTYPE_TEXTURE) {
        HRESULT r = dxt_box(buf, (IDirect3DTexture9 *)tex);
        if (r == S_OK) { gp_tb_stats[4]++; gp_tb_stats[7] += us(t0); return D3D_OK; }
    }
    HRESULT r = gp_tb_next(tex, pal, src, filter);   /* also after a failed level: redoes them all */
    gp_tb_stats[5]++; gp_tb_stats[8] += us(t0);
    return r;
}

/* at 0x4eefde the DXT1 bake (frame pointer ebp) still holds its X8R8G8B8 image at [ebp-0x18]:
 * pass it as an extra first argument; gp_tb_dxt pops five, the site pushed four */
__asm__(".globl _gp_tb_dxt_site\n_gp_tb_dxt_site:\n"
        "  popl %ecx\n"
        "  pushl -0x18(%ebp)\n"
        "  pushl %ecx\n"
        "  jmp _gp_tb_dxt@20\n");

/* ---- the patch ------------------------------------------------------------------------------ */
int gp_patch_terrainbox(void)
{
    static const uint32_t sites[3] = {0x4eee4a, 0x4ef148, SITE_DXT};
    /* the DXT1 bake's frame: prologue, the image pointer's store, its use as the source, its free */
    static const uint8_t pro[9] = {0x55, 0x8b, 0xec, 0x83, 0xec, 0x5c, 0x53, 0x8b, 0x5d};
    static const uint8_t st[3] = {0x89, 0x45, 0xe8}, use[3] = {0xff, 0x75, 0xe8};
    HMODULE dx = GetModuleHandleA("d3dx9_27.dll");
    if (!dx || !GetProcAddress(dx, "D3DXFilterTexture") || !GetProcAddress(dx, "D3DXLoadSurfaceFromMemory")) {
        gp_log("terrainbox: d3dx9_27 not loaded; patch skipped");
        return 0;
    }
    /* each site calls the D3DXFilterTexture thunk, or mipfilter's wrapper when mipfilter is on */
    uint32_t thunk = THUNK_FILTER + gp_va_offset, mf = (uint32_t)(uintptr_t)gp_mf_filter, next = 0;
    static uint8_t orig[3][5];
    gp_site s[3 + 4];
    for (int i = 0; i < 3; i++) {
        uint32_t va = sites[i] + gp_va_offset;
        const uint8_t *p = (const uint8_t *)(uintptr_t)va;
        uint32_t tgt = p[0] == 0xe8 ? va + 5 + *(const int32_t *)(p + 1) : 0;
        if (tgt != thunk && tgt != mf) { gp_log("terrainbox: site %08x does not call D3DXFilterTexture; patch skipped", sites[i]); return 0; }
        if (next && tgt != next) { gp_log("terrainbox: the sites call different filters; patch skipped"); return 0; }
        next = tgt;
        memcpy(orig[i], p, 5);
        gp_site_init(&s[i], sites[i], orig[i], 5);
        gp_rel32(&s[i], 0, 0xe8, i < 2 ? (void *)gp_tb_filter : (void *)gp_tb_dxt_site);
    }
    gp_site_init(&s[3], 0x4eee64, pro, 9); s[3].wlen = 0;
    gp_site_init(&s[4], 0x4eee95, st, 3); s[4].wlen = 0;
    gp_site_init(&s[5], 0x4eefa4, use, 3); s[5].wlen = 0;
    gp_site_init(&s[6], 0x4eefee, use, 3); s[6].wlen = 0;
    LARGE_INTEGER fq; QueryPerformanceFrequency(&fq); qfreq = fq.QuadPart;
    gp_tb_next = (gp_tb_fn)(uintptr_t)next;
    gp_tb_load = (gp_tb_load_fn)(uintptr_t)(THUNK_LOAD + gp_va_offset);
    if (!gp_apply("terrainbox", s, 7)) return 0;
    gp_log("terrainbox: terrain tile mip levels box-filtered at 3 call sites (16-bit bakes, DXT1 bake); unhandled calls go to %s",
           next == mf ? "mipfilter" : "Wine's D3DXFilterTexture");
    return 1;
}

void gp_tb_exit_log(void)
{
    if (gp_tb_stats[0] || gp_tb_stats[3])
        gp_log("exit: terrainbox %ld 16-bit calls (%ld box, %.1f ms), %ld DXT1 calls (%ld box, %.1f ms), %ld box levels, "
               "%ld passed on (%.1f ms), %s", gp_tb_stats[0], gp_tb_stats[1], gp_tb_stats[6] / 1000.0, gp_tb_stats[3],
               gp_tb_stats[4], gp_tb_stats[7] / 1000.0, gp_tb_stats[2], gp_tb_stats[5], gp_tb_stats[8] / 1000.0,
               gp_tb_state > 0 ? "on" : gp_tb_state < 0 ? "OFF (see the first line)" : "not used");
}
