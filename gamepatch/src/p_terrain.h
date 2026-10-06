/* Terrain picture switches (p_terrainbox.c, p_terrain32.c), all OFF by default: they change the
 * picture, so each is the player's choice (docs/PERFORMANCE.md §26). Texture pixels only: no game
 * logic, nothing a LAN game sees. */
#ifndef P_TERRAIN_H
#define P_TERRAIN_H
#include "gp.h"
#include <d3d9.h>

/* ---- terrainbox: box-filtered mip levels for the terrain tile textures ---------------------- */
int  gp_patch_terrainbox(void);
void gp_tb_exit_log(void);

/* the call-site replacements (stdcall, D3DXFilterTexture's arguments) */
HRESULT WINAPI gp_tb_filter(IDirect3DBaseTexture9 *tex, const PALETTEENTRY *pal, UINT srclevel, DWORD filter);
/* the DXT1 tile bake's site: buf32 is that bake's X8R8G8B8 level-0 image (read from its frame) */
HRESULT WINAPI gp_tb_dxt(const uint8_t *buf32, IDirect3DBaseTexture9 *tex, const PALETTEENTRY *pal, UINT srclevel,
                         DWORD filter);
void gp_tb_dxt_site(void);                 /* asm entry at the DXT1 bake's call: passes [ebp-0x18] */

/* every level below srclevel from the one above with Wine 11's (and Windows') 2x2 box filter, for a
 * 2D power-of-two texture whose levels each halve, in the 7 formats mipfilter knows: S_OK when made,
 * S_FALSE when not handled (nothing locked or written), an error when a lock failed */
HRESULT gp_tb_box(IDirect3DBaseTexture9 *tex, UINT srclevel, int exact);
/* one level, dst (sw/2 x sh/2) from src (sw x sh), and the per-pixel reference it is checked
 * against. exact = 0: each channel the rounded average (a + b + c + d + 2) / 4 (SSE2). exact = 1:
 * Wine 11's box_filter_argb_pixels arithmetic to the bit: each channel v / max as a float, summed
 * top-left, top-right, bottom-left, bottom-right, times 0.25, times max + 0.5, truncated (the same
 * as the rounded average except at some exact halves of 5-bit channels, which its float error rounds
 * down). Channels the format lacks come out 0 in both. */
int  gp_tb_level(D3DFORMAT f, const uint8_t *src, UINT sp, UINT sw, UINT sh, uint8_t *dst, UINT dp, int exact);
int  gp_tb_level_ref(D3DFORMAT f, const uint8_t *src, UINT sp, UINT sw, UINT sh, uint8_t *dst, UINT dp, int exact);
int  gp_tb_selftest(char *why, int cap);   /* fast against the reference on fake textures; 1 = equal */
typedef HRESULT (WINAPI *gp_tb_fn)(IDirect3DBaseTexture9 *, const PALETTEENTRY *, UINT, DWORD);
extern gp_tb_fn gp_tb_next;                /* what an unhandled call runs (mipfilter, else the thunk) */
typedef HRESULT (WINAPI *gp_tb_load_fn)(IDirect3DSurface9 *, const PALETTEENTRY *, const RECT *, const void *,
                                        D3DFORMAT, UINT, const PALETTEENTRY *, const RECT *, DWORD, D3DCOLOR);
extern gp_tb_load_fn gp_tb_load;           /* D3DXLoadSurfaceFromMemory (through the game's thunk) */
extern int gp_tb_mode;                    /* 1 rounded average (fast), 2 Wine 11 to the bit; main.c */
extern int gp_tb_state;                    /* 0 untested, 1 on, -1 off (self-test or d3dx9 check) */
/* calls, box calls, box levels, DXT calls, DXT box calls, fallbacks, us box, us DXT, us fallback */
extern volatile LONG gp_tb_stats[9];

/* ---- terrain32: 8 bits per channel for the terrain tiles (p_terrain32.c) -------------------- */
int  gp_patch_terrain32(void);
void gp_t32_exit_log(void);
extern int gp_t32_level;                   /* 1 near tiles, 2 also the far tiles' 16-bit textures; main.c */
/* the replacements (thiscall, the originals' arguments) */
__attribute__((thiscall)) void gp_t32_fill(void *tiledata, const uint8_t *src32, int pitch);
__attribute__((thiscall)) char gp_t32_tile(void *heightmap, int tilendx, int ppc, uint32_t *buf, int len, int layer);
__attribute__((thiscall)) int gp_t32_bake(void *holder, void *heightmap, int x, int y, int cells, int ppc, int layer);
void gp_t32_shadow_fill(void *tiledata, const uint8_t *src32, int pitch);  /* the 8-bit widths alone */
extern volatile LONG gp_t32_stats[6];
#endif
