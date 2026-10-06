/* An in-memory IDirect3DTexture9 for mipfilter's self-test and gamepatch/tests/t_mipfilter.c: a 2D texture
 * with its levels in plain memory, the IDirect3DTexture9 / IDirect3DSurface9 methods that Wine's
 * D3DXFilterTexture (D3DXLoadSurfaceFromSurface, lock_surface) and gp_mf_fast call, and a lock count
 * with an injectable failure. Each row has 4 spare bytes past the pixels, so a wrong pitch shows. */
#define COBJMACROS
#include "p_mipfilter.h"
#include <stdlib.h>
#include <string.h>

typedef struct fsurf { IDirect3DSurface9 iface; gp_fake_tex *t; UINT level; } fsurf;
typedef struct { UINT w, h, pitch; uint8_t *bits; fsurf s; int locked; } flevel;
struct gp_fake_tex {
    IDirect3DTexture9 iface;
    D3DFORMAT fmt;
    UINT n, bpp;
    flevel lv[16];
    LONG locks, open, fail_from;
};

static gp_fake_tex *tex_of(void *iface) { return (gp_fake_tex *)iface; }

/* ---- shared stubs ---- */
static HRESULT WINAPI f_qi(void *i, REFIID r, void **o) { (void)i; (void)r; *o = NULL; return E_NOINTERFACE; }
static ULONG WINAPI f_ref(void *i) { (void)i; return 1; }
static HRESULT WINAPI f_dev(void *i, IDirect3DDevice9 **d) { (void)i; *d = NULL; return D3DERR_INVALIDCALL; }
static HRESULT WINAPI f_spd(void *i, REFGUID g, const void *d, DWORD n, DWORD f) { (void)i; (void)g; (void)d; (void)n; (void)f; return E_NOTIMPL; }
static HRESULT WINAPI f_gpd(void *i, REFGUID g, void *d, DWORD *n) { (void)i; (void)g; (void)d; (void)n; return E_NOTIMPL; }
static HRESULT WINAPI f_fpd(void *i, REFGUID g) { (void)i; (void)g; return E_NOTIMPL; }
static DWORD WINAPI f_setpri(void *i, DWORD p) { (void)i; (void)p; return 0; }
static DWORD WINAPI f_getpri(void *i) { (void)i; return 0; }
static void WINAPI f_preload(void *i) { (void)i; }

static HRESULT lock(gp_fake_tex *t, UINT l, D3DLOCKED_RECT *lr, const RECT *r, DWORD flags)
{
    (void)flags;
    if (l >= t->n || t->lv[l].locked) return D3DERR_INVALIDCALL;
    t->locks++;
    if (t->fail_from && t->locks >= t->fail_from) return D3DERR_INVALIDCALL;
    flevel *v = &t->lv[l];
    UINT x = 0, y = 0;
    if (r) {
        if (r->left < 0 || r->top < 0 || r->right > (LONG)v->w || r->bottom > (LONG)v->h) return D3DERR_INVALIDCALL;
        x = r->left; y = r->top;
    }
    lr->Pitch = v->pitch;
    lr->pBits = v->bits + y * v->pitch + x * t->bpp;
    v->locked = 1; t->open++;
    return D3D_OK;
}
static HRESULT unlock(gp_fake_tex *t, UINT l)
{
    if (l >= t->n || !t->lv[l].locked) return D3DERR_INVALIDCALL;
    t->lv[l].locked = 0; t->open--;
    return D3D_OK;
}
static void desc(gp_fake_tex *t, UINT l, D3DSURFACE_DESC *d)
{
    memset(d, 0, sizeof *d);
    d->Format = t->fmt; d->Type = D3DRTYPE_SURFACE; d->Pool = D3DPOOL_MANAGED;
    d->MultiSampleType = D3DMULTISAMPLE_NONE; d->Width = t->lv[l].w; d->Height = t->lv[l].h;
}

/* ---- surface ---- */
static fsurf *surf_of(IDirect3DSurface9 *i) { return (fsurf *)i; }
static D3DRESOURCETYPE WINAPI s_type(IDirect3DSurface9 *i) { (void)i; return D3DRTYPE_SURFACE; }
static HRESULT WINAPI s_container(IDirect3DSurface9 *i, REFIID r, void **o) { (void)i; (void)r; *o = NULL; return E_NOINTERFACE; }
static HRESULT WINAPI s_desc(IDirect3DSurface9 *i, D3DSURFACE_DESC *d) { desc(surf_of(i)->t, surf_of(i)->level, d); return D3D_OK; }
static HRESULT WINAPI s_lock(IDirect3DSurface9 *i, D3DLOCKED_RECT *lr, const RECT *r, DWORD f) { return lock(surf_of(i)->t, surf_of(i)->level, lr, r, f); }
static HRESULT WINAPI s_unlock(IDirect3DSurface9 *i) { return unlock(surf_of(i)->t, surf_of(i)->level); }
static HRESULT WINAPI s_getdc(IDirect3DSurface9 *i, HDC *dc) { (void)i; (void)dc; return E_NOTIMPL; }
static HRESULT WINAPI s_reldc(IDirect3DSurface9 *i, HDC dc) { (void)i; (void)dc; return E_NOTIMPL; }
static IDirect3DSurface9Vtbl svt = {
    (void *)f_qi, (void *)f_ref, (void *)f_ref, (void *)f_dev, (void *)f_spd, (void *)f_gpd, (void *)f_fpd,
    (void *)f_setpri, (void *)f_getpri, (void *)f_preload, s_type, s_container, s_desc, s_lock, s_unlock,
    s_getdc, s_reldc};

/* ---- texture ---- */
static D3DRESOURCETYPE WINAPI t_type(IDirect3DTexture9 *i) { (void)i; return D3DRTYPE_TEXTURE; }
static DWORD WINAPI t_setlod(IDirect3DTexture9 *i, DWORD l) { (void)i; (void)l; return 0; }
static DWORD WINAPI t_getlod(IDirect3DTexture9 *i) { (void)i; return 0; }
static DWORD WINAPI t_count(IDirect3DTexture9 *i) { return tex_of(i)->n; }
static HRESULT WINAPI t_setagf(IDirect3DTexture9 *i, D3DTEXTUREFILTERTYPE f) { (void)i; (void)f; return E_NOTIMPL; }
static D3DTEXTUREFILTERTYPE WINAPI t_getagf(IDirect3DTexture9 *i) { (void)i; return D3DTEXF_NONE; }
static void WINAPI t_genmips(IDirect3DTexture9 *i) { (void)i; }
static HRESULT WINAPI t_desc(IDirect3DTexture9 *i, UINT l, D3DSURFACE_DESC *d)
{
    if (l >= tex_of(i)->n) return D3DERR_INVALIDCALL;
    desc(tex_of(i), l, d); return D3D_OK;
}
static HRESULT WINAPI t_surf(IDirect3DTexture9 *i, UINT l, IDirect3DSurface9 **s)
{
    if (l >= tex_of(i)->n) { *s = NULL; return D3DERR_INVALIDCALL; }
    *s = &tex_of(i)->lv[l].s.iface; return D3D_OK;
}
static HRESULT WINAPI t_lock(IDirect3DTexture9 *i, UINT l, D3DLOCKED_RECT *lr, const RECT *r, DWORD f) { return lock(tex_of(i), l, lr, r, f); }
static HRESULT WINAPI t_unlock(IDirect3DTexture9 *i, UINT l) { return unlock(tex_of(i), l); }
static HRESULT WINAPI t_dirty(IDirect3DTexture9 *i, const RECT *r) { (void)i; (void)r; return D3D_OK; }
static IDirect3DTexture9Vtbl tvt = {
    (void *)f_qi, (void *)f_ref, (void *)f_ref, (void *)f_dev, (void *)f_spd, (void *)f_gpd, (void *)f_fpd,
    (void *)f_setpri, (void *)f_getpri, (void *)f_preload, t_type, t_setlod, t_getlod, t_count, t_setagf,
    t_getagf, t_genmips, t_desc, t_surf, t_lock, t_unlock, t_dirty};

gp_fake_tex *gp_fake_create(UINT w, UINT h, UINT levels, D3DFORMAT fmt, UINT bpp)
{
    return gp_fake_create_pad(w, h, levels, fmt, bpp, 4);
}
gp_fake_tex *gp_fake_create_pad(UINT w, UINT h, UINT levels, D3DFORMAT fmt, UINT bpp, UINT pad)
{
    gp_fake_tex *t = calloc(1, sizeof *t);
    if (!t) return NULL;
    t->iface.lpVtbl = &tvt; t->fmt = fmt; t->bpp = bpp;
    for (UINT l = 0; l < levels && l < 16; l++) {
        flevel *v = &t->lv[l];
        v->w = w; v->h = h; v->pitch = (w * bpp + 3) / 4 * 4 + pad;
        v->bits = calloc((size_t)v->pitch * h + 16, 1);
        if (!v->bits) { gp_fake_free(t); return NULL; }
        v->s.iface.lpVtbl = &svt; v->s.t = t; v->s.level = l;
        t->n = l + 1;
        if (w == 1 && h == 1) break;
        w = w > 1 ? w / 2 : 1; h = h > 1 ? h / 2 : 1;
    }
    return t;
}
void gp_fake_free(gp_fake_tex *t)
{
    if (!t) return;
    for (UINT l = 0; l < 16; l++) free(t->lv[l].bits);
    free(t);
}
IDirect3DBaseTexture9 *gp_fake_base(gp_fake_tex *t) { return (IDirect3DBaseTexture9 *)&t->iface; }
uint8_t *gp_fake_bits(gp_fake_tex *t, UINT l, UINT *w, UINT *h, UINT *pitch)
{
    if (l >= t->n) return NULL;
    if (w) *w = t->lv[l].w;
    if (h) *h = t->lv[l].h;
    if (pitch) *pitch = t->lv[l].pitch;
    return t->lv[l].bits;
}
void gp_fake_fail_locks(gp_fake_tex *t, int from_lock) { t->fail_from = from_lock; t->locks = 0; }
LONG gp_fake_locks(gp_fake_tex *t) { return t->locks; }
LONG gp_fake_open(gp_fake_tex *t) { return t->open; }
