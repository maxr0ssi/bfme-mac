/* terrain32 (OFF by default; a picture change, the player's choice): the terrain tile textures in
 * 8 bits per channel instead of 5 (docs/PERFORMANCE.md §26).
 *
 * The map's terrain art is 24/32-bit TGA, cut into 64 x 64 source tiles (TileData, 2 x 2 cells each).
 * The loader (0x4ab896) box-averages each tile to widths 64..1 and keeps only X1R5G5B5 (0x511299:
 * (v + 1) * 31 / 256 per channel); the tile bake (0x4eec82) then copies those 16-bit pixels, or for a
 * blended cell expands them to 8 bits (0x4ac284), blends in 8 bits (0x4ad85f, 0x4ac035) and truncates
 * back to 5 (v >> 3), into A1R5G5B5 tile textures. So every terrain texel carries 32 levels per
 * channel: banding in smooth ground and blend ramps, and the far tiles' DXT1 is encoded from that.
 *
 * Here:
 *   - each TileData allocation (0x4ab99f colour, 0x4ab9db normal map) gets SHADOW more bytes, and the
 *     fill (0x4abbe7, 0x4abc37 -> 0x5113b2) also keeps widths 64, 32 and 16 in 8 bits there (the same
 *     rounded box averages as the game's, without the 5-bit step);
 *   - the 16 -> 32-bit tile expansion (0x4ad882, 0x4ae8ae -> 0x4ac284) copies those 8-bit pixels
 *     instead, when every one of them quantises to the 16-bit pixel the game holds (else the original
 *     runs): blended cells and the DXT1 far tiles get 8-bit sources;
 *   - the near tiles' colour and normal-map textures (0x511fe1, 0x51204e; with terrain32=2 also the far
 *     tiles' normal map 0x514969 and uncompressed colour 0x5148f9) are created X8R8G8B8: the bake's
 *     format check (0x4ae431) also takes X8R8G8B8, and its bake call (0x4ae44d) goes to gp_t32_bake,
 *     which fetches every cell as the 16-bit bake does (a blended cell through the game's own
 *     0x4ae772 in its 8-bit path, any other its source tile alone) and writes 32-bit pixels in the
 *     same layout (alpha 0xff, as A1R5G5B5's 1), then calls whatever D3DXFilterTexture
 *     the original bake's site calls (terrainbox, mipfilter or Wine's).
 * Memory: +21.5 KB per TileData (46 MB on mp eastfarthing hills, 1068 tiles + normal maps, game heap)
 * and 2 x the near tile textures (512 x 512, 3 levels: 0.69 -> 1.38 MB each; managed, so outside the
 * 32-bit address space with Wine patch 0022). Texture pixels only: no game logic, nothing a LAN game
 * sees. Test: gamepatch/tests/t_terrain32.c. */
#define COBJMACROS
#include "p_terrain.h"
#include <stdio.h>
#include <string.h>

#define TD_SIZE    0x2ac0u
#define SH_MAGIC   0x32335354u                      /* "TS32" */
typedef struct { uint32_t magic, pad[3], l64[64 * 64], l32[32 * 32], l16[16 * 16]; } shadow;
#define SHADOW     ((uint32_t)sizeof(shadow))

typedef void (__attribute__((thiscall)) *fill_fn)(void *td, const uint8_t *src, int pitch);
typedef char (__attribute__((thiscall)) *tile_fn)(void *hm, int ndx, int ppc, uint32_t *buf, int len, int layer);
typedef int (__attribute__((thiscall)) *bake_fn)(void *holder, void *hm, int x, int y, int cells, int ppc, int layer);
typedef const uint32_t *(__attribute__((thiscall)) *cell_fn)(void *hm, int x, int y, int ppc, int layer, void *dst, int pitch);
typedef IDirect3DBaseTexture9 *(__attribute__((thiscall)) *peek_fn)(void *holder);
typedef char (__attribute__((thiscall)) *cliff_fn)(void *hm, int x, int y);

static fill_fn o_fill;
static tile_fn o_tile;
static bake_fn o_bake;
static cell_fn o_cell;                     /* 0x4ae772: one cell's pixels (32-bit path when dst is NULL) */
static peek_fn o_peek;                     /* 0x5321dc: the TextureClass's IDirect3DTexture9 */
static cliff_fn o_cliff;                   /* 0x4ab717: a cliff cell (its blends are not drawn) */
uint32_t gp_t32_yes, gp_t32_no;            /* the bake's two branches (for the format check stub) */
volatile LONG gp_t32_stats[6];             /* fills, 8-bit tiles, 16-bit fallbacks, 32-bit bakes, other bakes, bad shadows */

static shadow *sh_of(void *td) { return (shadow *)((uint8_t *)td + TD_SIZE); }
static const uint16_t *td16(void *td, int w)   /* TileData::getRGBDataForWidth */
{
    return (const uint16_t *)((uint8_t *)td + (w == 64 ? 8 : w == 32 ? 0x2008 : 0x2808));
}
static uint32_t *sh_level(shadow *s, int w) { return w == 64 ? s->l64 : w == 32 ? s->l32 : s->l16; }

/* the game's 5-bit step of one rounded average v (0x511299): (v + 1) * 31 / 256 */
static inline uint32_t q16(uint32_t p)
{
    return ((p >> 16 & 255) + 1) * 31 >> 8 << 10 | ((p >> 8 & 255) + 1) * 31 >> 8 << 5 | ((p & 255) + 1) * 31 >> 8;
}

/* ---- TileData fill: the original, then the 8-bit widths 64, 32, 16 -------------------------- */
void gp_t32_shadow_fill(void *td, const uint8_t *src, int pitch)
{
    shadow *s = sh_of(td);
    for (int w = 64; w >= 16; w /= 2) {
        int n = 64 / w, nn = n * n;
        uint32_t *o = sh_level(s, w);
        for (int y = 0; y < w; y++)
            for (int x = 0; x < w; x++) {
                uint32_t b = 0, g = 0, r = 0;
                for (int j = 0; j < n; j++) {
                    const uint8_t *p = src + (y * n + j) * pitch + x * n * 4;
                    for (int i = 0; i < n; i++, p += 4) { b += p[0]; g += p[1]; r += p[2]; }
                }
                b = (b + nn / 2) / nn; g = (g + nn / 2) / nn; r = (r + nn / 2) / nn;
                o[y * w + x] = (r > 255 ? 255 : r) << 16 | (g > 255 ? 255 : g) << 8 | (b > 255 ? 255 : b);
            }
    }
    s->magic = SH_MAGIC;
}

__attribute__((thiscall)) void gp_t32_fill(void *td, const uint8_t *src, int pitch)
{
    o_fill(td, src, pitch);
    gp_t32_stats[0]++;
    if (td && src) gp_t32_shadow_fill(td, src, pitch);
}

/* ---- 16 -> 32-bit tile expansion: the 8-bit pixels when they agree with the 16-bit ones ------ */
__attribute__((thiscall)) char gp_t32_tile(void *hm, int ndx, int ppc, uint32_t *buf, int len, int layer)
{
    int idx = (short)ndx / 4, w = 2 * ppc;
    void *td = idx >= 0 && idx < 0x1000 ? ((void **)((uint8_t *)hm + 0xb0))[idx] : NULL;
    if (td && layer == 1) td = *(void **)((uint8_t *)td + 0x2ab4);
    if (!td || !buf || len < ppc * ppc * 4 || (w != 64 && w != 32 && w != 16) || sh_of(td)->magic != SH_MAGIC) {
        gp_t32_stats[2]++;
        return o_tile(hm, ndx, ppc, buf, len, layer);
    }
    const uint32_t *l = sh_level(sh_of(td), w);
    const uint16_t *q = td16(td, w);
    int x0 = ndx & 1 ? ppc : 0, y0 = ndx & 2 ? ppc : 0;
    /* the first and last row of the quadrant must be what the game holds (a stale or foreign shadow
     * fails here; the shadow is written by the same fill as the 16-bit planes) */
    for (int r = 0; r < ppc; r += ppc - 1)
        for (int c = 0; c < ppc; c++)
            if (q16(l[(y0 + r) * w + x0 + c]) != (q[(y0 + r) * w + x0 + c] & 0x7fffu)) {
                gp_t32_stats[5]++; gp_t32_stats[2]++;
                return o_tile(hm, ndx, ppc, buf, len, layer);
            }
    for (int r = 0; r < ppc; r++) memcpy(buf + r * ppc, l + (y0 + r) * w + x0, (size_t)ppc * 4);
    gp_t32_stats[1]++;
    return 1;
}

/* ---- the bake for X8R8G8B8 tile textures (0x4eec82's layout, 32-bit pixels) ---------------- */
static uint32_t filter_site;               /* the original bake's D3DXFilterTexture call (0x4eee4a) */

__attribute__((thiscall)) int gp_t32_bake(void *holder, void *hm, int x, int y, int cells, int ppc, int layer)
{
    IDirect3DBaseTexture9 *base = o_peek(holder);
    IDirect3DSurface9 *s = NULL;
    D3DSURFACE_DESC d;
    if (!base || IDirect3DBaseTexture9_GetType(base) != D3DRTYPE_TEXTURE ||
        FAILED(IDirect3DTexture9_GetSurfaceLevel((IDirect3DTexture9 *)base, 0, &s)) || !s)
        return o_bake(holder, hm, x, y, cells, ppc, layer);
    if (FAILED(IDirect3DSurface9_GetDesc(s, &d)) || d.Format != D3DFMT_X8R8G8B8) {
        IDirect3DSurface9_Release(s);
        gp_t32_stats[4]++;
        return o_bake(holder, hm, x, y, cells, ppc, layer);
    }
    int n = cells * ppc;
    D3DLOCKED_RECT lr;
    if ((int)d.Width != n || FAILED(IDirect3DSurface9_LockRect(s, &lr, NULL, 0))) {
        IDirect3DSurface9_Release(s);
        return 0;
    }
    /* each cell as 0x4ae772 gives it to the 16-bit bake: a cell without a blend (or a cliff cell) is its
     * source tile alone, copied straight (no 3-way blend either); a blended one goes through the
     * game's blends, here in its 32-bit path (no destination) */
    static uint32_t one[64 * 64];
    int wd = *(int *)((uint8_t *)hm + 0x08), ht = *(int *)((uint8_t *)hm + 0x0c), cnt = *(int *)((uint8_t *)hm + 0x20);
    const int16_t *tile = *(int16_t **)((uint8_t *)hm + 0x98);
    const int *blend = *(int **)((uint8_t *)hm + 0x9c);
    for (int i = 0; i < cells; i++)
        for (int j = 0; j < cells; j++) {
            int cx = x + j, cy = y + i, idx = cy * wd + cx;
            if (cx < 0 || cy < 0 || cx >= wd || cy >= ht || idx >= cnt || ppc > 32) continue;
            const uint32_t *p = NULL;
            if (blend[idx] > 0 && !o_cliff(hm, cx, cy)) p = o_cell(hm, cx, cy, ppc, layer, NULL, 0);
            else if (gp_t32_tile(hm, tile[idx], ppc, one, sizeof one, layer)) p = one;
            if (!p) continue;
            for (int k = 0; k < ppc; k++) {   /* source row k of cell (j, i) -> texture row n-1 - i*ppc - k */
                uint32_t *o = (uint32_t *)((uint8_t *)lr.pBits + (size_t)(n - 1 - i * ppc - k) * lr.Pitch) + j * ppc;
                const uint32_t *q = p + k * ppc;
                for (int c = 0; c < ppc; c++) o[c] = q[c] | 0xff000000u;
            }
        }
    IDirect3DSurface9_UnlockRect(s);
    IDirect3DSurface9_Release(s);
    uint32_t va = filter_site + gp_va_offset;
    gp_tb_fn f = (gp_tb_fn)(uintptr_t)(va + 5 + *(const int32_t *)(uintptr_t)(va + 1));
    f(base, NULL, 0, 5);
    gp_t32_stats[3]++;
    return (int)d.Height;
}

/* the bake's format check (0x4ae431..0x4ae439: cmpl $0x19,0x1c(%ebp); mov %esi,-4(%ebp); jne):
 * A1R5G5B5 or X8R8G8B8 goes to the bake call, anything else where it went */
__asm__(".globl _gp_t32_check\n_gp_t32_check:\n"
        "  movl %esi, -4(%ebp)\n"
        "  cmpl $0x19, 0x1c(%ebp)\n  je 1f\n"
        "  cmpl $0x16, 0x1c(%ebp)\n  je 1f\n"
        "  jmp *_gp_t32_no\n"
        "1: jmp *_gp_t32_yes\n");
void gp_t32_check(void);

/* ---- the patch ------------------------------------------------------------------------------ */
int gp_t32_level = 1;                      /* 1 near tiles, 2 also the far tiles' 16-bit textures */

int gp_patch_terrain32(void)
{
    static const uint8_t alloc[5] = {0x68, 0xc0, 0x2a, 0x00, 0x00}, push19[2] = {0x6a, 0x19};
    static const uint8_t check[9] = {0x83, 0x7d, 0x1c, 0x19, 0x89, 0x75, 0xfc, 0x75, 0x1a};
    static const struct { uint32_t va, to; } calls[] = {
        {0x4abbe7, 0x5113b2}, {0x4abc37, 0x5113b2}, {0x4ad882, 0x4ac284}, {0x4ae8ae, 0x4ac284}, {0x4ae44d, 0x4eec82}};
    static const uint32_t pushes[4] = {0x511fe1, 0x51204e, 0x514969, 0x5148f9};
    static uint8_t cbytes[5][5];
    gp_site s[2 + 5 + 4 + 1 + 4];
    int n = 0;
    for (int i = 0; i < 2; i++) {
        gp_site_init(&s[n], i ? 0x4ab9db : 0x4ab99f, alloc, 5);
        uint32_t sz = TD_SIZE + SHADOW;
        memcpy(&s[n].repl[1], &sz, 4);
        n++;
    }
    void *repl[5] = {(void *)gp_t32_fill, (void *)gp_t32_fill, (void *)gp_t32_tile, (void *)gp_t32_tile, (void *)gp_t32_bake};
    for (int i = 0; i < 5; i++) {
        int32_t rel = (int32_t)(calls[i].to - (calls[i].va + 5));
        cbytes[i][0] = 0xe8; memcpy(&cbytes[i][1], &rel, 4);
        gp_site_init(&s[n], calls[i].va, cbytes[i], 5);
        gp_rel32(&s[n], 0, 0xe8, repl[i]);
        n++;
    }
    for (int i = 0; i < (gp_t32_level >= 2 ? 4 : 2); i++) {
        gp_site_init(&s[n], pushes[i], push19, 2);
        s[n].repl[1] = 0x16;                  /* D3DFMT_X8R8G8B8 */
        n++;
    }
    gp_site_init(&s[n], 0x4ae431, check, 9);
    gp_rel32(&s[n], 0, 0xe9, (void *)gp_t32_check);
    memset(&s[n].repl[5], 0x90, 4);
    n++;
    /* check-only: the original bake's filter call and the functions called from here */
    static const uint8_t fcall[5] = {0xe8, 0x83, 0xfe, 0x54, 0x00}, cell[3] = {0x55, 0x8b, 0xec};
    static const uint8_t peek[5] = {0x56, 0x8b, 0x31, 0x85, 0xf6}, cliff[6] = {0x8b, 0x81, 0xe4, 0x20, 0x01, 0x00};
    gp_site_init(&s[n], 0x4eee4a, fcall, 5); s[n].wlen = 0;
    /* (mipfilter / terrainbox may have retargeted it: only its opcode matters) */
    s[n].len = 1;
    n++;
    gp_site_init(&s[n], 0x4ae772, cell, 3); s[n].wlen = 0; n++;
    gp_site_init(&s[n], 0x5321dc, peek, 5); s[n].wlen = 0; n++;
    gp_site_init(&s[n], 0x4ab717, cliff, 6); s[n].wlen = 0; n++;
    o_fill = (fill_fn)(uintptr_t)(0x5113b2 + gp_va_offset);
    o_tile = (tile_fn)(uintptr_t)(0x4ac284 + gp_va_offset);
    o_bake = (bake_fn)(uintptr_t)(0x4eec82 + gp_va_offset);
    o_cell = (cell_fn)(uintptr_t)(0x4ae772 + gp_va_offset);
    o_peek = (peek_fn)(uintptr_t)(0x5321dc + gp_va_offset);
    o_cliff = (cliff_fn)(uintptr_t)(0x4ab717 + gp_va_offset);
    gp_t32_yes = 0x4ae43a + gp_va_offset;
    gp_t32_no = 0x4ae454 + gp_va_offset;
    filter_site = 0x4eee4a;
    if (!gp_apply("terrain32", s, n)) return 0;
    gp_log("terrain32: terrain tiles keep 8 bits per channel (+%u bytes per source tile); %s tile textures X8R8G8B8",
           SHADOW, gp_t32_level >= 2 ? "near and far 16-bit" : "near");
    return 1;
}

void gp_t32_exit_log(void)
{
    if (gp_t32_stats[0])
        gp_log("exit: terrain32 %ld tile fills, %ld 8-bit tile reads, %ld 16-bit (%ld shadows that did not match), "
               "%ld 32-bit bakes, %ld 16-bit bakes", gp_t32_stats[0], gp_t32_stats[1], gp_t32_stats[2], gp_t32_stats[5],
               gp_t32_stats[3], gp_t32_stats[4]);
}
