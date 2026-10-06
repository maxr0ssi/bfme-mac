/* mipfilter: the game's D3DXFilterTexture calls give the mip levels the installed Wine d3dx9_27
 * gives, without its generic per-pixel path.
 *
 * The in-match freezes of the 2026-10-05 18:24 session (docs/PERFORMANCE.md §23): the terrain is
 * drawn in tiles of 16x16 cells, and each tile near the camera gets its own textures, baked on the
 * CPU from the map's terrain tiles (0x4e0a73 > 0x511f6b > 0x4ae3cd > 0x4eec82: two square A1R5G5B5
 * textures per tile, then D3DXFilterTexture(tex, NULL, 0, D3DX_FILTER_BOX) for their mip levels). A
 * tile leaving the camera's near range drops its textures; normally two are rebuilt per frame, but
 * when a camera moves more than 20 units between two updates (or the camera list changes) the next
 * frame rebuilds every waiting tile at once (up to 99): 30-90 textures, ~3 ms each, 100-430 ms, ~89 %
 * of it inside d3dx9.
 *
 * The d3dx9_27 that scripts/wine-fixes.sh installs is built from Wine 10.0 (patches/d3dx9-setrawvalue),
 * and Wine 10.0 has no box filter: D3DXLoadSurfaceFromSurface sends every filter except none, point and
 * linear (those first try the device's StretchRect) to point_filter_argb_pixels, which for a mip level
 * of the same format takes source pixel (x * sw / dw, y * sh / dh) and passes it through
 * get_relevant_argb_components / make_argb_color: per pixel and channel a byte loop, so ~20 ns a pixel
 * for what is a copy of the bits that belong to a channel (the X bits of X1R5G5B5, X4R4G4B4 and
 * X8R8G8B8 come out 0).
 *
 * Here every call site of the D3DXFilterTexture thunk (0xa3ecd2) calls gp_mf_filter. For a 2D texture
 * in A8R8G8B8, X8R8G8B8, R5G6B5, X1R5G5B5, A1R5G5B5, A4R4G4B4 or X4R4G4B4, called with the box filter
 * (5) or D3DX_DEFAULT (what the game passes), it makes each level below srclevel from the one above as
 * that code does, with the same locks (the source level read-only without a rect, then the
 * destination with its full rect; released in reverse order). Anything else, or a lock that fails
 * (the original then redoes every level), runs the original. Only when d3dx9_27 is Wine's builtin;
 * before the first use it checks itself against Wine's function on in-memory textures of every format
 * (p_mipfilter_fake.c) and stays off on any difference, so a d3dx9 with a real box filter (Wine 11)
 * turns it off instead of being imitated wrongly. Client side only: texture pixels, no game logic.
 * Test: gamepatch/tests/t_mipfilter.c. */
#define COBJMACROS
#include "p_mipfilter.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define THUNK      0xa3ecd2u           /* jmp *0xbd0a20 (d3dx9_27!D3DXFilterTexture) */
#define IAT_SLOT   0xbd0a20u
#define FILTER_BOX 5u
#define DX_DEFAULT 0xffffffffu

gp_mf_fn gp_mf_orig;
int gp_mf_state;
volatile LONG gp_mf_stats[7];
static LONGLONG qfreq;

/* the formats, their bytes per pixel and the bits Wine's channels keep (its format table) */
static const struct { D3DFORMAT f; UINT bpp; uint32_t keep; } fmts[] = {
    {D3DFMT_A8R8G8B8, 4, 0xffffffffu}, {D3DFMT_X8R8G8B8, 4, 0x00ffffffu},
    {D3DFMT_R5G6B5, 2, 0xffffu}, {D3DFMT_X1R5G5B5, 2, 0x7fffu}, {D3DFMT_A1R5G5B5, 2, 0xffffu},
    {D3DFMT_A4R4G4B4, 2, 0xffffu}, {D3DFMT_X4R4G4B4, 2, 0x0fffu},
};
enum { NF = sizeof fmts / sizeof fmts[0] };

static int fmt_index(D3DFORMAT f)
{
    for (int k = 0; k < NF; k++) if (fmts[k].f == f) return k;
    return -1;
}

/* one level: dst (dw x dh) from src (sw x sh), Wine's point filter for the same format */
static void level(UINT bpp, uint32_t keep, const uint8_t *src, UINT sp, UINT sw, UINT sh,
                  uint8_t *dst, UINT dp, UINT dw, UINT dh)
{
    int half = sw == 2 * dw;
    for (UINT y = 0; y < dh; y++) {
        const uint8_t *r = src + (size_t)(y * sh / dh) * sp;
        uint8_t *o = dst + (size_t)y * dp;
        if (bpp == 2) {
            const uint16_t *s = (const uint16_t *)r;
            uint16_t *d = (uint16_t *)o, k = (uint16_t)keep;
            if (half) for (UINT x = 0; x < dw; x++) d[x] = s[2 * x] & k;
            else for (UINT x = 0; x < dw; x++) d[x] = s[x * sw / dw] & k;
        } else {
            const uint32_t *s = (const uint32_t *)r;
            uint32_t *d = (uint32_t *)o;
            if (half) for (UINT x = 0; x < dw; x++) d[x] = s[2 * x] & keep;
            else for (UINT x = 0; x < dw; x++) d[x] = s[x * sw / dw] & keep;
        }
    }
}

HRESULT gp_mf_fast(IDirect3DBaseTexture9 *base, UINT src, DWORD filter)
{
    if (!base || (filter != FILTER_BOX && filter != DX_DEFAULT)) return S_FALSE;
    UINT n = IDirect3DBaseTexture9_GetLevelCount(base);
    if (src == DX_DEFAULT) src = 0;
    if (src >= n || n > 16) return S_FALSE;
    if (IDirect3DBaseTexture9_GetType(base) != D3DRTYPE_TEXTURE) return S_FALSE;
    IDirect3DTexture9 *t = (IDirect3DTexture9 *)base;
    D3DSURFACE_DESC d[16];
    for (UINT l = src; l < n; l++)
        if (FAILED(IDirect3DTexture9_GetLevelDesc(t, l, &d[l])) || d[l].MultiSampleType != D3DMULTISAMPLE_NONE ||
            d[l].Format != d[src].Format || !d[l].Width || !d[l].Height)
            return S_FALSE;
    int k = fmt_index(d[src].Format);
    if (k < 0) return S_FALSE;
    for (UINT l = src + 1; l < n; l++) {
        D3DLOCKED_RECT a, b;
        RECT full = {0, 0, (LONG)d[l].Width, (LONG)d[l].Height};
        if (FAILED(IDirect3DTexture9_LockRect(t, l - 1, &a, NULL, D3DLOCK_READONLY))) return E_FAIL;
        if (FAILED(IDirect3DTexture9_LockRect(t, l, &b, &full, 0))) {
            IDirect3DTexture9_UnlockRect(t, l - 1);
            return E_FAIL;
        }
        level(fmts[k].bpp, fmts[k].keep, a.pBits, a.Pitch, d[l - 1].Width, d[l - 1].Height,
              b.pBits, b.Pitch, d[l].Width, d[l].Height);
        IDirect3DTexture9_UnlockRect(t, l);
        IDirect3DTexture9_UnlockRect(t, l - 1);
        gp_mf_stats[2]++;
    }
    return S_OK;
}

/* ---- self-test: the fast path against the original on in-memory textures -------------------- */
static uint32_t rs = 0x2545f491u;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }

static int same_tex(gp_fake_tex *a, gp_fake_tex *b)
{
    for (UINT l = 0; l < 16; l++) {
        UINT h, p;
        uint8_t *x = gp_fake_bits(a, l, NULL, &h, &p), *y = gp_fake_bits(b, l, NULL, NULL, NULL);
        if (!x) return 1;
        if (memcmp(x, y, (size_t)h * p)) return 0;
    }
    return 1;
}

int gp_mf_selftest(char *why, int cap)
{
    why[0] = 0;
    if (!gp_mf_orig) { snprintf(why, cap, "no original"); return 0; }
    static const UINT sz[2][2] = {{64, 64}, {48, 20}};   /* a power of two, and not (odd steps, 1-wide levels) */
    for (int k = 0; k < NF; k++)
        for (int s = 0; s < 2; s++) {
            UINT w = sz[s][0], h = sz[s][1];
            gp_fake_tex *a = gp_fake_create(w, h, 16, fmts[k].f, fmts[k].bpp), *b = gp_fake_create(w, h, 16, fmts[k].f, fmts[k].bpp);
            if (!a || !b) { gp_fake_free(a); gp_fake_free(b); snprintf(why, cap, "out of memory"); return 0; }
            UINT p, hh;
            uint8_t *la = gp_fake_bits(a, 0, NULL, &hh, &p), *lb = gp_fake_bits(b, 0, NULL, NULL, NULL);
            for (size_t i = 0; i < (size_t)hh * p; i++) la[i] = lb[i] = (uint8_t)rnd();
            HRESULT ra = gp_mf_orig(gp_fake_base(a), NULL, 0, s ? DX_DEFAULT : FILTER_BOX);
            HRESULT rb = gp_mf_fast(gp_fake_base(b), 0, s ? DX_DEFAULT : FILTER_BOX);
            int same = ra == D3D_OK && rb == S_OK && same_tex(a, b);
            gp_fake_free(a); gp_fake_free(b);
            if (!same) {
                snprintf(why, cap, "format %u %ux%u differs (original %08lx, fast %08lx)", (unsigned)fmts[k].f, w, h, ra, rb);
                return 0;
            }
        }
    return 1;
}

/* ---- the call sites' replacement ---------------------------------------------------------- */
static LONGLONG qpc(void) { LARGE_INTEGER x; QueryPerformanceCounter(&x); return x.QuadPart; }
static LONG last_stats[7];
static DWORD last_tick;

static void periodic(void)
{
    DWORD now = GetTickCount();
    if (!last_tick) last_tick = now;
    if (now - last_tick < 60000) return;
    LONG d[7];
    for (int i = 0; i < 7; i++) { d[i] = gp_mf_stats[i] - last_stats[i]; last_stats[i] = gp_mf_stats[i]; }
    if (d[0])
        gp_log("mipfilter: last %lu s, %ld filter calls: %ld fast (%ld levels, %.1f ms), %ld original (%.1f ms), "
               "%ld lock failures", (now - last_tick) / 1000, d[0], d[1], d[2], d[5] / 1000.0, d[3], d[6] / 1000.0, d[4]);
    last_tick = now;
}

__attribute__((force_align_arg_pointer))
HRESULT WINAPI gp_mf_filter(IDirect3DBaseTexture9 *tex, const PALETTEENTRY *pal, UINT src, DWORD filter)
{
    gp_mf_stats[0]++;
    if (!gp_mf_state) {
        char why[160];
        gp_mf_state = gp_mf_selftest(why, sizeof why) ? 1 : -1;
        if (gp_mf_state > 0) gp_log("mipfilter: self-test against Wine's D3DXFilterTexture passed (%d formats)", NF);
        else gp_log("mipfilter: self-test failed (%s); the original runs", why);
    }
    LONGLONG t0 = qpc();
    if (gp_mf_state > 0) {
        HRESULT r = gp_mf_fast(tex, src, filter);
        if (r == S_OK) {
            gp_mf_stats[1]++;
            gp_mf_stats[5] += (LONG)((qpc() - t0) * 1000000 / qfreq);
            periodic();
            return D3D_OK;
        }
        if (FAILED(r)) gp_mf_stats[4]++;
    }
    HRESULT r = gp_mf_orig(tex, pal, src, filter);
    gp_mf_stats[3]++;
    gp_mf_stats[6] += (LONG)((qpc() - t0) * 1000000 / qfreq);
    periodic();
    return r;
}

int gp_patch_mipfilter(void)
{
    static const uint32_t sites[] = {0x4eee4a, 0x4eefde, 0x4ef148, 0x530fea, 0x5312e7, 0x5313e3, 0x532198, 0x570cba};
    enum { NS = sizeof sites / sizeof sites[0] };
    static const uint8_t thunk[6] = {0xff, 0x25, 0x20, 0x0a, 0xbd, 0x00};
    HMODULE dx = GetModuleHandleA("d3dx9_27.dll");
    FARPROC f = dx ? GetProcAddress(dx, "D3DXFilterTexture") : NULL;
    if (!f || memcmp((const char *)dx + 0x40, "Wine builtin DLL", 16)) {
        gp_log("mipfilter: d3dx9_27 is not Wine's builtin (Windows?); patch skipped");
        return 0;
    }
    if (*(volatile uint32_t *)(uintptr_t)IAT_SLOT != (uint32_t)(uintptr_t)f) {
        gp_log("mipfilter: the D3DXFilterTexture import is not d3dx9_27's (%08x); patch skipped",
               *(volatile uint32_t *)(uintptr_t)IAT_SLOT);
        return 0;
    }
    static uint8_t orig[NS][5];
    gp_site s[NS + 1];
    gp_site_init(&s[0], THUNK, thunk, 6); s[0].wlen = 0;           /* check only */
    for (int i = 0; i < NS; i++) {
        int32_t rel = (int32_t)(THUNK - (sites[i] + 5));
        orig[i][0] = 0xe8; memcpy(&orig[i][1], &rel, 4);
        gp_site_init(&s[i + 1], sites[i], orig[i], 5);
        gp_rel32(&s[i + 1], 0, 0xe8, (void *)gp_mf_filter);
    }
    LARGE_INTEGER fq; QueryPerformanceFrequency(&fq); qfreq = fq.QuadPart;
    gp_mf_orig = (gp_mf_fn)(uintptr_t)(THUNK + gp_va_offset);
    if (!gp_apply("mipfilter", s, NS + 1)) return 0;
    gp_log("mipfilter: D3DXFilterTexture's mip levels made as Wine's d3dx9 makes them, without its per-pixel path (%d call sites)", NS);
    return 1;
}

void gp_mf_exit_log(void)
{
    if (gp_mf_stats[0])
        gp_log("exit: mipfilter %ld filter calls: %ld fast (%ld levels, %.1f ms), %ld original (%.1f ms), %ld lock failures, "
               "self-test %s", gp_mf_stats[0], gp_mf_stats[1], gp_mf_stats[2], gp_mf_stats[5] / 1000.0, gp_mf_stats[3],
               gp_mf_stats[6] / 1000.0, gp_mf_stats[4], gp_mf_state > 0 ? "passed" : gp_mf_state < 0 ? "FAILED" : "not run");
}
