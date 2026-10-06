/* mipfilter (p_mipfilter.c, p_mipfilter_fake.c): the game's D3DXFilterTexture calls give the same
 * mip levels as the installed Wine d3dx9_27 (10.0 based: every filter but none/point/linear is its
 * point filter), without its generic per-pixel path. Kept out of gp.h / gp_render.h so it can grow
 * on its own; main.c and the test include it. */
#ifndef P_MIPFILTER_H
#define P_MIPFILTER_H
#include "gp.h"
#include <d3d9.h>

int  gp_patch_mipfilter(void);
void gp_mf_exit_log(void);

/* the replacement for D3DXFilterTexture at the game's call sites (stdcall, same arguments) */
HRESULT WINAPI gp_mf_filter(IDirect3DBaseTexture9 *tex, const PALETTEENTRY *pal, UINT srclevel, DWORD filter);
/* the fast path alone: S_OK when it made every level, S_FALSE when the call is not one it handles
 * (nothing locked or written), an error when a lock failed (levels may be half written: the caller
 * runs the original, which rewrites all of them) */
HRESULT gp_mf_fast(IDirect3DBaseTexture9 *tex, UINT srclevel, DWORD filter);
typedef HRESULT (WINAPI *gp_mf_fn)(IDirect3DBaseTexture9 *, const PALETTEENTRY *, UINT, DWORD);
extern gp_mf_fn gp_mf_orig;                /* the original (Wine's D3DXFilterTexture via the thunk) */
extern int gp_mf_state;                    /* 0 untested, 1 self-test passed, -1 failed: original only */
int  gp_mf_selftest(char *why, int cap);   /* fast path against gp_mf_orig on fake textures; 1 = equal */
/* calls, fast-path calls, levels made fast, original calls, lock failures, us fast, us original */
extern volatile LONG gp_mf_stats[7];

/* p_mipfilter_fake.c: an in-memory IDirect3DTexture9 (2D, any 16/32-bit format, a full or partial
 * mip chain) with the methods D3DXFilterTexture's lock path and the fast path use (GetDevice gives
 * no device: never pass it the point or linear filter, which first try a StretchRect) */
typedef struct gp_fake_tex gp_fake_tex;
gp_fake_tex *gp_fake_create(UINT w, UINT h, UINT levels, D3DFORMAT fmt, UINT bpp);
void  gp_fake_free(gp_fake_tex *t);
IDirect3DBaseTexture9 *gp_fake_base(gp_fake_tex *t);
uint8_t *gp_fake_bits(gp_fake_tex *t, UINT level, UINT *w, UINT *h, UINT *pitch);
void  gp_fake_fail_locks(gp_fake_tex *t, int from_lock);  /* lock number n (1-based) and later fail */
LONG  gp_fake_locks(gp_fake_tex *t);       /* locks taken so far */
LONG  gp_fake_open(gp_fake_tex *t);        /* locks not yet unlocked */
#endif
