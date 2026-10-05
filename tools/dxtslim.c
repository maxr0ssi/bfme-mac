/* dxtslim - an opaque DXT5 texture rewritten as the DXT1 that draws the same texels, at half the memory
 * (docs/MEMORY-2GB.md, "Texture memory of our archives").
 *
 * A DXT5 block is an 8-byte alpha block plus an 8-byte colour block that is always decoded in
 * four-colour mode. A DXT1 block is the colour block alone, decoded in four-colour mode only when
 * colour0 > colour1. So when every alpha of every level is 255, the DXT1 is the colour blocks, with
 * each block whose colour0 < colour1 written with its endpoints swapped and its indices XOR 1 (the two
 * interpolated colours trade places), and a block whose endpoints are equal written with index 0
 * everywhere (all four colours are that endpoint). The alpha of a four-colour DXT1 texel is 255.
 *
 * The check is the GPU's, not the specification's: both files are loaded with the game's call
 * (D3DXCreateTextureFromFileInMemoryEx, as in tools/texbake.c), every level is drawn 1:1 with point
 * sampling into an A8R8G8B8 render target (the level chosen by SetLOD and MAXMIPLEVEL), read back, and
 * compared byte for byte. At start-up a texture with one colour per level checks that each draw shows
 * the level it asks for (exit 2 otherwise). OK only when every
 * level of both draws identically, so the game draws the same texels on this machine's renderer.
 *
 * Build: i686-w64-mingw32-gcc -O2 -o build/dxtslim.exe tools/dxtslim.c -ld3d9
 * Run:   wine build/dxtslim.exe <list>    each line of <list>: "<in.dds>|<out.dds>" (Windows paths)
 * Prints one line per texture: "OK <out> <w>x<h> <levels>", "SKIP <in> <why>" (not an opaque DXT5:
 * nothing written) or "FAIL <in> <why>"; exit 1 on any FAIL.
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef HRESULT (WINAPI *CreateFromMemEx)(IDirect3DDevice9 *, const void *, UINT, UINT, UINT, UINT, DWORD, D3DFORMAT,
        D3DPOOL, DWORD, DWORD, D3DCOLOR, void *, void *, IDirect3DTexture9 **);
static CreateFromMemEx d3dx_load;
static IDirect3DDevice9 *dev;

static BYTE *read_all(const char *path, DWORD *size)
{
    FILE *f = fopen(path, "rb");
    BYTE *b;
    long n;
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    fseek(f, 0, SEEK_SET);
    b = malloc(n ? n : 1);
    *size = (DWORD)fread(b, 1, n, f);
    fclose(f);
    if (*size != (DWORD)n) { free(b); return NULL; }
    return b;
}

/* The game's call (game.dat 0x53117e, mips 0, texture reduction 0). */
static IDirect3DTexture9 *load(const BYTE *data, DWORD size)
{
    IDirect3DTexture9 *tex = NULL;
    if (FAILED(d3dx_load(dev, data, size, 0, 0, 0, 0, D3DFMT_UNKNOWN, D3DPOOL_MANAGED, 0xffffffffu, 5, 0,
            NULL, NULL, &tex)))
        return NULL;
    return tex;
}

static DWORD blocks(DWORD w, DWORD h)
{
    return ((w + 3) / 4) * ((h + 3) / 4);
}

/* 1 when the alphas of a DXT5 alpha block are 255 for every texel inside the level (bw x bh of the
 * block's 4x4: a 2x2 or 1x1 level's block also holds texels that are never sampled). */
static int opaque_block(const BYTE *b, unsigned bw, unsigned bh)
{
    unsigned a0 = b[0], a1 = b[1], v[8], i;
    unsigned long long bits = 0;
    if (a0 == 255 && a1 == 255) return 1;
    if (bw > 4) bw = 4;
    if (bh > 4) bh = 4;
    v[0] = a0, v[1] = a1;
    if (a0 > a1) for (i = 1; i < 7; ++i) v[i + 1] = (a0 * (7 - i) + a1 * i) / 7;
    else { for (i = 1; i < 5; ++i) v[i + 1] = (a0 * (5 - i) + a1 * i) / 5; v[6] = 0, v[7] = 255; }
    for (i = 0; i < 6; ++i) bits |= (unsigned long long)b[2 + i] << (8 * i);
    for (i = 0; i < 16; ++i) if (i % 4 < bw && i / 4 < bh && v[(bits >> (3 * i)) & 7] != 255) return 0;
    return 1;
}

/* The DXT5 colour block as a DXT1 block that decodes to the same four-colour palette entries. */
static void colour_block(const BYTE *in, BYTE *out)
{
    WORD c0 = in[0] | in[1] << 8, c1 = in[2] | in[3] << 8;
    DWORD idx = in[4] | in[5] << 8 | in[6] << 16 | (DWORD)in[7] << 24;
    if (c0 < c1) { WORD t = c0; c0 = c1, c1 = t; idx ^= 0x55555555u; }
    else if (c0 == c1) idx = 0;
    out[0] = c0 & 0xff, out[1] = c0 >> 8, out[2] = c1 & 0xff, out[3] = c1 >> 8;
    out[4] = idx & 0xff, out[5] = idx >> 8 & 0xff, out[6] = idx >> 16 & 0xff, out[7] = idx >> 24;
}

/* in: DXT5 DDS; returns the DXT1 DDS (malloc'd, *n bytes) or NULL with *why set. */
static BYTE *transcode(const BYTE *in, DWORD size, DWORD *n, const char **why, DWORD *w, DWORD *h, DWORD *levels)
{
    DWORD l, i, off = 128, total = 0, lw, lh;
    BYTE *out, *p;
    if (size < 128 || memcmp(in, "DDS ", 4)) { *why = "not a DDS"; return NULL; }
    if (memcmp(in + 84, "DXT5", 4)) { *why = "not DXT5"; return NULL; }
    *h = *(const DWORD *)(in + 12), *w = *(const DWORD *)(in + 16);
    *levels = (*(const DWORD *)(in + 8) & 0x20000) && *(const DWORD *)(in + 28) ? *(const DWORD *)(in + 28) : 1;
    for (l = 0, lw = *w, lh = *h; l < *levels; ++l, lw = lw > 1 ? lw / 2 : 1, lh = lh > 1 ? lh / 2 : 1)
        total += blocks(lw, lh);
    if (size < 128 + total * 16) { *why = "truncated"; return NULL; }
    for (l = 0, i = 0, lw = *w, lh = *h; l < *levels; ++l, lw = lw > 1 ? lw / 2 : 1, lh = lh > 1 ? lh / 2 : 1)
    {
        DWORD x, y;
        for (y = 0; y < (lh + 3) / 4; ++y)
            for (x = 0; x < (lw + 3) / 4; ++x, ++i)
                if (!opaque_block(in + off + i * 16, lw - 4 * x, lh - 4 * y)) { *why = "has alpha below 255"; return NULL; }
    }
    *n = 128 + total * 8;
    p = out = malloc(*n);
    memcpy(out, in, 128);
    memcpy(out + 84, "DXT1", 4);
    *(DWORD *)(out + 8) |= 0x80000;                              /* LINEARSIZE */
    *(DWORD *)(out + 20) = blocks(*w, *h) * 8;
    p += 128;
    for (i = 0; i < total; ++i, p += 8) colour_block(in + off + i * 16 + 8, p);
    return out;
}

/* Level l of tex drawn 1:1, point-sampled, into a w x h A8R8G8B8 target; the rows, packed. */
static BYTE *draw_level(IDirect3DTexture9 *tex, DWORD l)
{
    struct { float x, y, z, rhw, u, v; } q[4];
    D3DSURFACE_DESC d;
    IDirect3DSurface9 *rt = NULL, *sys = NULL;
    D3DLOCKED_RECT lr;
    D3DVIEWPORT9 vp;
    BYTE *px = NULL;
    UINT y;
    IDirect3DTexture9_GetLevelDesc(tex, l, &d);
    if (FAILED(IDirect3DDevice9_CreateRenderTarget(dev, d.Width, d.Height, D3DFMT_A8R8G8B8, D3DMULTISAMPLE_NONE, 0,
            FALSE, &rt, NULL)) || FAILED(IDirect3DDevice9_CreateOffscreenPlainSurface(dev, d.Width, d.Height,
            D3DFMT_A8R8G8B8, D3DPOOL_SYSTEMMEM, &sys, NULL)))
        goto done;
    IDirect3DDevice9_SetRenderTarget(dev, 0, rt);
    vp.X = vp.Y = 0, vp.Width = d.Width, vp.Height = d.Height, vp.MinZ = 0, vp.MaxZ = 1;
    IDirect3DDevice9_SetViewport(dev, &vp);
    IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0x12345678, 1.0f, 0);
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)tex);
    IDirect3DTexture9_SetLOD(tex, l);              /* a managed texture's base level (MIPFILTER NONE)... */
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAXMIPLEVEL, l);  /* ...and the sampler's (POINT) */
    q[0].x = q[2].x = -0.5f, q[1].x = q[3].x = d.Width - 0.5f;
    q[0].y = q[1].y = -0.5f, q[2].y = q[3].y = d.Height - 0.5f;
    q[0].u = q[2].u = 0, q[1].u = q[3].u = 1, q[0].v = q[1].v = 0, q[2].v = q[3].v = 1;
    for (y = 0; y < 4; ++y) q[y].z = 0.5f, q[y].rhw = 1;
    IDirect3DDevice9_BeginScene(dev);
    IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, q, sizeof(q[0]));
    IDirect3DDevice9_EndScene(dev);
    if (FAILED(IDirect3DDevice9_GetRenderTargetData(dev, rt, sys))) goto done;
    if (FAILED(IDirect3DSurface9_LockRect(sys, &lr, NULL, D3DLOCK_READONLY))) goto done;
    px = malloc(d.Width * d.Height * 4);
    for (y = 0; y < d.Height; ++y) memcpy(px + y * d.Width * 4, (BYTE *)lr.pBits + y * lr.Pitch, d.Width * 4);
    IDirect3DSurface9_UnlockRect(sys);
done:
    if (sys) IDirect3DSurface9_Release(sys);
    if (rt) IDirect3DSurface9_Release(rt);
    return px;
}

/* 1 when draw_level shows the level it asks for: an 8x8 A8R8G8B8 texture, one colour per level. */
static int levels_take(void)
{
    static const DWORD colour[4] = {0xff102030, 0xff405060, 0xff708090, 0xffa0b0c0};
    IDirect3DTexture9 *t;
    DWORD l, ok = 1;
    if (FAILED(IDirect3DDevice9_CreateTexture(dev, 8, 8, 4, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &t, NULL))) return 0;
    for (l = 0; l < 4; ++l)
    {
        D3DLOCKED_RECT lr;
        UINT x, y, n = 8 >> l;
        IDirect3DTexture9_LockRect(t, l, &lr, NULL, 0);
        for (y = 0; y < n; ++y) for (x = 0; x < n; ++x) ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = colour[l];
        IDirect3DTexture9_UnlockRect(t, l);
    }
    for (l = 0; l < 4; ++l)
    {
        DWORD *px = (DWORD *)draw_level(t, l), i;
        if (!px) { ok = 0; break; }
        for (i = 0; i < (8u >> l) * (8u >> l); ++i) ok &= px[i] == colour[l];
        free(px);
    }
    IDirect3DTexture9_Release(t);
    return ok;
}

static const char *same_on_gpu(const BYTE *a, DWORD na, const BYTE *b, DWORD nb)
{
    IDirect3DTexture9 *ta = load(a, na), *tb = load(b, nb);
    const char *why = NULL;
    DWORD l, levels;
    if (!ta || !tb) why = "d3dx9 refused one of them";
    else if ((levels = IDirect3DTexture9_GetLevelCount(ta)) != IDirect3DTexture9_GetLevelCount(tb)) why = "level counts differ";
    else for (l = 0; l < levels && !why; ++l)
    {
        D3DSURFACE_DESC d;
        BYTE *pa = draw_level(ta, l), *pb = draw_level(tb, l);
        IDirect3DTexture9_GetLevelDesc(ta, l, &d);
        if (!pa || !pb) why = "a level did not draw";
        else if (memcmp(pa, pb, d.Width * d.Height * 4)) why = "a level draws differently";
        free(pa), free(pb);
    }
    if (ta) IDirect3DTexture9_Release(ta);
    if (tb) IDirect3DTexture9_Release(tb);
    return why;
}

static int slim(const char *in, const char *out)
{
    DWORD size, n, w, h, levels;
    const char *why = NULL;
    BYTE *src = read_all(in, &size), *dxt1;
    FILE *f;
    if (!src) { printf("FAIL %s unreadable\n", in); return 0; }
    if (!(dxt1 = transcode(src, size, &n, &why, &w, &h, &levels))) { printf("SKIP %s %s\n", in, why); free(src); return 1; }
    if ((why = same_on_gpu(src, size, dxt1, n))) printf("FAIL %s %s\n", in, why);
    else if (!(f = fopen(out, "wb")) || fwrite(dxt1, 1, n, f) != n || fclose(f)) printf("FAIL %s cannot write %s\n", in, why = out);
    else printf("OK %s %lux%lu %lu\n", out, (unsigned long)w, (unsigned long)h, (unsigned long)levels);
    free(src), free(dxt1);
    return !why;
}

int main(int argc, char **argv)
{
    IDirect3D9 *d3d;
    D3DPRESENT_PARAMETERS pp = {0};
    HWND wnd;
    HMODULE m;
    FILE *list;
    char line[2 * MAX_PATH + 8];
    int bad = 0, done = 0;

    if (argc != 2 || !(list = fopen(argv[1], "r"))) { printf("usage: dxtslim <list of in.dds|out.dds>\n"); return 2; }
    if (!(m = LoadLibraryA("d3dx9_27.dll")) || !(d3dx_load = (CreateFromMemEx)GetProcAddress(m,
            "D3DXCreateTextureFromFileInMemoryEx")))
    { printf("FAIL no d3dx9_27\n"); return 2; }
    wnd = CreateWindowA("static", "dxtslim", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, 0, 0, 0, 0);
    if (!(d3d = Direct3DCreate9(D3D_SDK_VERSION))) { printf("FAIL Direct3DCreate9\n"); return 2; }
    pp.Windowed = TRUE;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth = 64;
    pp.BackBufferHeight = 64;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8;
    if (FAILED(IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, wnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev)))
    { printf("FAIL CreateDevice\n"); return 2; }
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_LIGHTING, FALSE);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_ZENABLE, FALSE);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_CULLMODE, D3DCULL_NONE);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_ALPHABLENDENABLE, FALSE);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_ALPHATESTENABLE, FALSE);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLORARG1, D3DTA_TEXTURE);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_ALPHAOP, D3DTOP_SELECTARG1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_ALPHAARG1, D3DTA_TEXTURE);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MINFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAGFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MIPFILTER, D3DTEXF_POINT);
    if (!levels_take()) { printf("FAIL the drawn mip level is not the one asked for\n"); return 2; }
    while (fgets(line, sizeof(line), list))
    {
        char *bar = strchr(line, '|'), *end = line + strcspn(line, "\r\n");
        *end = 0;
        if (!bar) continue;
        *bar = 0;
        bad += !slim(line, bar + 1);
        ++done;
        fflush(stdout);
    }
    fclose(list);
    printf("%s %d of %d\n", bad ? "FAILED" : "DONE", done - bad, done);
    IDirect3DDevice9_Release(dev);
    IDirect3D9_Release(d3d);
    DestroyWindow(wnd);
    return bad ? 1 : 0;
}
