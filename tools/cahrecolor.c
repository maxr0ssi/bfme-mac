/* cahrecolor - the Create-a-Hero colour rebuild of a house-colour mask texture, replayed without the
 * game (docs/CAH.md, "Hero colours"), to check that a rewrite of an uploaded MANAGED texture shows
 * under the Wine in use (Wine patch 0022 stashes managed textures' system memory: docs/MEMORY-4GB.md).
 *
 * The game's sequence (RotWK 2.02 game.dat), per mask texture:
 *   load   0x53101b: a 32-bit TGA goes through D3DXCreateTexture(w, h, mips, usage 0, A8R8G8B8,
 *          MANAGED), LockRect(level 0, NULL, D3DLOCK_NOSYSLOCK), copy, UnlockRect, then
 *          D3DXFilterTexture(tex, NULL, 0, D3DX_FILTER_BOX); anything else (a DDS) goes through
 *          D3DXCreateTextureFromFileInMemoryEx(..., usage 0, fmt, MANAGED, D3DX_DEFAULT, BOX, ...).
 *   save   0x532847 -> 0x531c77, right after the load, for a "rebuildable" colour (CaH objects):
 *          GetSurfaceLevel(0), LockRect(NULL, NOSYSLOCK), copy level 0 into a heap buffer, UnlockRect.
 *   colour 0x5321ba -> 0x531c77, at every picker change: GetSurfaceLevel(0), LockRect(NULL,
 *          NOSYSLOCK), write mask R*c1 + G*c2 + B*c3 (alpha kept) from the saved copy into the lock,
 *          UnlockRect, D3DXFilterTexture(tex, NULL, 0, D3DX_DEFAULT) for the other levels.
 * No UpdateTexture, no AddDirtyRect, no READONLY or DISCARD lock.
 *
 * Each variant creates --n masks (128x128, full chain, four flat quadrants), saves them, draws them
 * for a few frames (the upload), then recolours them three times; after each recolour every mask is
 * drawn at levels 0, 1 and 2 (point sampling) and read back, and its level 0 is read with a READONLY
 * lock. Variants: tga / dds (the two load paths) x first colour before / after the first draw; with
 * EvictManagedResources between colours; saved only after a draw; a mask without mip levels. Prints "ok"/"--" per variant and FAIL lines; exits
 * with the number of failures.
 *
 * Build: i686-w64-mingw32-gcc -O2 -o build/cahrecolor.exe tools/cahrecolor.c -ld3d9
 * Run:   scripts/cahrecolor.sh (engines/w10, WINED3D_STASH_MANAGED=1 and =0, throwaway prefix)
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define W 256
#define H 256
#define TS 128          /* mask size */
#define MAXN 64

typedef HRESULT (WINAPI *CreateTex)(IDirect3DDevice9 *, UINT, UINT, UINT, DWORD, D3DFORMAT, D3DPOOL, IDirect3DTexture9 **);
typedef HRESULT (WINAPI *FilterTex)(IDirect3DBaseTexture9 *, const PALETTEENTRY *, UINT, DWORD);
typedef HRESULT (WINAPI *CreateFromMemEx)(IDirect3DDevice9 *, const void *, UINT, UINT, UINT, UINT, DWORD, D3DFORMAT,
        D3DPOOL, DWORD, DWORD, D3DCOLOR, void *, void *, IDirect3DTexture9 **);
static CreateTex x_create;
static FilterTex x_filter;
static CreateFromMemEx x_load;

static IDirect3DDevice9 *dev;
static IDirect3DSurface9 *readback_surface;
static int failures, n_masks = 16;

typedef struct { float x, y, z, rhw; float u, v; } Vtx;

static void die(const char *what, HRESULT hr) { printf("FAIL %s: hr=%#lx\n", what, (unsigned long)hr); ExitProcess(100); }
#define CK(x) do { HRESULT hr_ = (x); if (FAILED(hr_)) die(#x, hr_); } while (0)

static int fail(int *bad, const char *name, const char *fmt, ...)
{
    va_list args;
    failures++;
    if ((*bad)++ < 6)
    {
        printf("FAIL %s: ", name);
        va_start(args, fmt); vprintf(fmt, args); va_end(args);
        printf("\n");
    }
    return 1;
}

/* The mask: four flat quadrants, R / G / B / a mix, alpha a per-quadrant constant. */
static DWORD mask_at(int x, int y, int size)
{
    int q = (x >= size / 2) + 2 * (y >= size / 2);
    static const DWORD m[4] = { 0x80ff0000, 0x9000ff00, 0xa00000ff, 0xb0804000 };
    return m[q];
}

/* The three picker colours of round r (0 = never shown: the saved mask is never coloured with it). */
static void colours(int r, DWORD c[3])
{
    static const DWORD set[4][3] = { { 0, 0, 0 }, { 0xc02010, 0x10c020, 0x2010c0 },
                                     { 0x30a0f0, 0xf0a030, 0x808080 }, { 0xffffff, 0x404040, 0x00ff80 } };
    memcpy(c, set[r], sizeof(set[r]));
}

/* 0x531c77's 32-bit branch: each channel = (mR * c1 + mG * c2 + mB * c3) / 255, clamped; alpha kept. */
static DWORD colour_texel(DWORD m, const DWORD c[3])
{
    unsigned int mr = m >> 16 & 0xff, mg = m >> 8 & 0xff, mb = m & 0xff, out = m & 0xff000000, s, ch;
    for (s = 0; s < 24; s += 8)
    {
        ch = (mr * (c[0] >> s & 0xff) + mg * (c[1] >> s & 0xff) + mb * (c[2] >> s & 0xff)) / 255;
        out |= (ch > 255 ? 255 : ch) << s;
    }
    return out;
}

static void quad(float x, float y, float sz)
{
    Vtx q[4] = { { x, y, 0, 1, 0, 0 }, { x + sz, y, 0, 1, 1, 0 }, { x, y + sz, 0, 1, 0, 1 }, { x + sz, y + sz, 0, 1, 1, 1 } };
    CK(IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, q, sizeof(*q)));
}

static const DWORD *frame(IDirect3DTexture9 *t, int want_frame)
{
    IDirect3DSurface9 *bb; D3DLOCKED_RECT lr; static DWORD f[W * H]; int y;
    CK(IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0xff000000, 1.0f, 0));
    CK(IDirect3DDevice9_BeginScene(dev));
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)t);
    quad(0, 0, TS);             /* level 0 */
    quad(160, 0, TS / 2);       /* level 1 */
    quad(160, 96, TS / 4);      /* level 2 */
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    CK(IDirect3DDevice9_EndScene(dev));
    if (want_frame)
    {
        CK(IDirect3DDevice9_GetBackBuffer(dev, 0, 0, D3DBACKBUFFER_TYPE_MONO, &bb));
        CK(IDirect3DDevice9_GetRenderTargetData(dev, bb, readback_surface));
        IDirect3DSurface9_Release(bb);
        CK(IDirect3DSurface9_LockRect(readback_surface, &lr, NULL, D3DLOCK_READONLY));
        for (y = 0; y < H; y++) memcpy(f + y * W, (BYTE *)lr.pBits + y * lr.Pitch, W * 4);
        IDirect3DSurface9_UnlockRect(readback_surface);
    }
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
    return f;
}

/* An in-memory A8R8G8B8 DDS of the mask with its full chain (what texbake ships for our parts). */
static BYTE *mask_dds(UINT *size)
{
    UINT levels = 8, total = 128, s, x, y, l;
    BYTE *b; DWORD *h, *p;
    for (s = TS, l = 0; l < levels; s >>= 1, ++l) total += s * s * 4;
    b = calloc(1, total);
    memcpy(b, "DDS ", 4);
    h = (DWORD *)(b + 4);
    h[0] = 124; h[1] = 0x1 | 0x2 | 0x4 | 0x8 | 0x1000 | 0x20000; h[2] = TS; h[3] = TS; h[4] = TS * 4; h[6] = levels;
    h[18] = 32; h[19] = 0x41; h[21] = 32; h[22] = 0xff0000; h[23] = 0xff00; h[24] = 0xff; h[25] = 0xff000000;
    h[26] = 0x1000 | 0x400000 | 0x8;
    p = (DWORD *)(b + 128);
    for (s = TS, l = 0; l < levels; s >>= 1, ++l)
        for (y = 0; y < s; y++) for (x = 0; x < s; x++) *p++ = mask_at(x, y, s);
    *size = total;
    return b;
}

static IDirect3DTexture9 *load_mask(int dds, int one_level)
{
    IDirect3DTexture9 *t = NULL; IDirect3DSurface9 *s; D3DLOCKED_RECT lr; int x, y;
    if (dds)
    {
        UINT size; BYTE *b = mask_dds(&size);
        CK(x_load(dev, b, size, 0, 0, 0, 0, D3DFMT_UNKNOWN, D3DPOOL_MANAGED, 0xffffffff, 5, 0, NULL, NULL, &t));
        free(b);
        return t;
    }
    CK(x_create(dev, TS, TS, one_level ? 1 : 0, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &t));
    CK(IDirect3DTexture9_GetSurfaceLevel(t, 0, &s));
    CK(IDirect3DSurface9_LockRect(s, &lr, NULL, D3DLOCK_NOSYSLOCK));
    for (y = 0; y < TS; y++) for (x = 0; x < TS; x++) ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = mask_at(x, y, TS);
    CK(IDirect3DSurface9_UnlockRect(s));
    IDirect3DSurface9_Release(s);
    if (!one_level) CK(x_filter((IDirect3DBaseTexture9 *)t, NULL, 0, 5));   /* skipped for 1 level */
    return t;
}

/* 0x531c77 with no saved copy yet: copy level 0 out. */
static DWORD *save_mask(IDirect3DTexture9 *t)
{
    IDirect3DSurface9 *s; D3DLOCKED_RECT lr; DWORD *copy = malloc(TS * TS * 4); int y;
    CK(IDirect3DTexture9_GetSurfaceLevel(t, 0, &s));
    CK(IDirect3DSurface9_LockRect(s, &lr, NULL, D3DLOCK_NOSYSLOCK));
    for (y = 0; y < TS; y++) memcpy(copy + y * TS, (BYTE *)lr.pBits + y * lr.Pitch, TS * 4);
    CK(IDirect3DSurface9_UnlockRect(s));
    IDirect3DSurface9_Release(s);
    return copy;
}

/* 0x531c77 with a saved copy: colour it into level 0, then D3DXFilterTexture (0x532198). */
static void recolour(IDirect3DTexture9 *t, const DWORD *saved, const DWORD c[3])
{
    IDirect3DSurface9 *s; D3DLOCKED_RECT lr; int x, y;
    CK(IDirect3DTexture9_GetSurfaceLevel(t, 0, &s));
    CK(IDirect3DSurface9_LockRect(s, &lr, NULL, D3DLOCK_NOSYSLOCK));
    for (y = 0; y < TS; y++) for (x = 0; x < TS; x++)
        ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = colour_texel(saved[y * TS + x], c);
    CK(IDirect3DSurface9_UnlockRect(s));
    IDirect3DSurface9_Release(s);
    CK(x_filter((IDirect3DBaseTexture9 *)t, NULL, 0, 0xffffffff));
}

static int close_to(DWORD a, DWORD b)
{
    int s, d;
    for (s = 0; s < 24; s += 8) { d = (int)(a >> s & 0xff) - (int)(b >> s & 0xff); if (d < -1 || d > 1) return 0; }
    return 1;
}

/* Every mask drawn at levels 0-2 and its level 0 read back must show round r's colours. */
static void check(IDirect3DTexture9 **t, DWORD **saved, int r, int *bad, const char *name)
{
    static const int ox[3] = { 0, 160, 160 }, oy[3] = { 0, 0, 96 };
    DWORD c[3], want, got; D3DLOCKED_RECT lr; const DWORD *f; int i, l, q, x, y, sz;
    colours(r, c);
    for (i = 0; i < n_masks; i++)
    {
        f = frame(t[i], 1);
        for (l = 0; l < 3; l++)
            for (q = 0; q < 4; q++)
            {
                sz = TS >> l;
                x = (q & 1) * sz / 2 + sz / 4; y = (q >> 1) * sz / 2 + sz / 4;
                want = colour_texel(saved[i][(y << l) * TS + (x << l)], c) & 0xffffff;
                got = f[(oy[l] + y) * W + ox[l] + x] & 0xffffff;
                if (!close_to(got, want))
                    fail(bad, name, "round %d mask %d level %d quadrant %d drawn %06lx, want %06lx", r, i, l, q,
                         (unsigned long)got, (unsigned long)want);
            }
        CK(IDirect3DTexture9_LockRect(t[i], 0, &lr, NULL, D3DLOCK_READONLY));
        got = ((DWORD *)((BYTE *)lr.pBits + 5 * lr.Pitch))[TS - 5];
        want = colour_texel(saved[i][5 * TS + TS - 5], c);
        IDirect3DTexture9_UnlockRect(t[i], 0);
        if (got != want) fail(bad, name, "round %d mask %d level 0 reads %08lx, want %08lx", r, i,
                              (unsigned long)got, (unsigned long)want);
    }
}

/* colour_before_draw: the first colour before the first draw; save_late: the mask is saved only after
 * it has been drawn (uploaded and stashed); one_level: a mask without mip levels. */
static void variant(int dds, int colour_before_draw, int evict, int save_late, int one_level)
{
    char name[64]; IDirect3DTexture9 *t[MAXN]; DWORD *saved[MAXN], c[3]; int i, r, k, bad = 0;
    snprintf(name, sizeof(name), "%s-%s%s%s%s", dds ? "dds" : "tga", colour_before_draw ? "early" : "late",
             evict ? "-evict" : "", save_late ? "-savelate" : "", one_level ? "-1level" : "");
    for (i = 0; i < n_masks; i++)
    {
        t[i] = load_mask(dds, one_level);
        if (save_late)
            for (k = 0; k < 4; k++) frame(t[i], 0);
        saved[i] = save_mask(t[i]);
        if (saved[i][5 * TS + TS - 5] != mask_at(TS - 5, 5, TS))
            fail(&bad, name, "mask %d saved %08lx, want %08lx", i, (unsigned long)saved[i][5 * TS + TS - 5],
                 (unsigned long)mask_at(TS - 5, 5, TS));
    }
    for (r = 1; r <= 3; r++)
    {
        if (r > 1 || !colour_before_draw)
            for (k = 0; k < 4; k++) for (i = 0; i < n_masks; i++) frame(t[i], 0);   /* uploads; the stash follows */
        if (evict) CK(IDirect3DDevice9_EvictManagedResources(dev));
        colours(r, c);
        for (i = 0; i < n_masks; i++) recolour(t[i], saved[i], c);
        check(t, saved, r, &bad, name);
    }
    for (i = 0; i < n_masks; i++) { IDirect3DTexture9_Release(t[i]); free(saved[i]); }
    if (bad > 6) printf("FAIL %s: %d more\n", name, bad - 6);
    printf("%s %s\n", bad ? "--" : "ok", name);
}

int main(int argc, char **argv)
{
    IDirect3D9 *d3d; D3DPRESENT_PARAMETERS pp = { 0 }; RECT rc = { 0, 0, W, H }; WNDCLASSA wc = { 0 }; HWND hwnd;
    HMODULE x; char env[8]; int i, pass;
    setvbuf(stdout, NULL, _IONBF, 0);
    for (i = 1; i < argc; i++)
        if (!strcmp(argv[i], "--n") && i + 1 < argc) n_masks = atoi(argv[++i]);
    if (n_masks < 1 || n_masks > MAXN) n_masks = 16;
    if (!(x = LoadLibraryA("d3dx9_27.dll"))) die("LoadLibrary d3dx9_27", E_FAIL);
    x_create = (CreateTex)GetProcAddress(x, "D3DXCreateTexture");
    x_filter = (FilterTex)GetProcAddress(x, "D3DXFilterTexture");
    x_load = (CreateFromMemEx)GetProcAddress(x, "D3DXCreateTextureFromFileInMemoryEx");
    if (!x_create || !x_filter || !x_load) die("d3dx9_27 exports", E_FAIL);
    printf("WINED3D_STASH_MANAGED=%s, %d masks\n",
           GetEnvironmentVariableA("WINED3D_STASH_MANAGED", env, sizeof(env)) ? env : "(unset)", n_masks);

    wc.lpfnWndProc = DefWindowProcA; wc.hInstance = GetModuleHandleA(NULL); wc.lpszClassName = "cahrecolor";
    RegisterClassA(&wc);
    AdjustWindowRect(&rc, WS_OVERLAPPEDWINDOW, FALSE);
    hwnd = CreateWindowA("cahrecolor", "cahrecolor", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 40, 40,
                         rc.right - rc.left, rc.bottom - rc.top, NULL, NULL, wc.hInstance, NULL);
    if (!(d3d = Direct3DCreate9(D3D_SDK_VERSION))) die("Direct3DCreate9", E_FAIL);
    pp.BackBufferWidth = W; pp.BackBufferHeight = H; pp.BackBufferFormat = D3DFMT_X8R8G8B8; pp.BackBufferCount = 1;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.hDeviceWindow = hwnd; pp.Windowed = TRUE;
    pp.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;
    CK(IDirect3D9_CreateDevice(d3d, D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, hwnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev));
    CK(IDirect3DDevice9_CreateOffscreenPlainSurface(dev, W, H, D3DFMT_X8R8G8B8, D3DPOOL_SYSTEMMEM, &readback_surface, NULL));
    IDirect3DDevice9_SetRenderState(dev, D3DRS_LIGHTING, FALSE);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_ZENABLE, FALSE);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_CULLMODE, D3DCULL_NONE);
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLORARG1, D3DTA_TEXTURE);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MINFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAGFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MIPFILTER, D3DTEXF_POINT);

    for (pass = 0; pass < 2; pass++)
    {
        printf("pass %d\n", pass);
        variant(0, 1, 0, 0, 0); variant(0, 0, 0, 0, 0); variant(1, 1, 0, 0, 0); variant(1, 0, 0, 0, 0);
        variant(0, 0, 1, 0, 0); variant(1, 0, 1, 0, 0);
        variant(0, 1, 0, 1, 0); variant(1, 0, 0, 1, 0); variant(0, 1, 0, 0, 1); variant(0, 0, 1, 1, 1);
    }
    printf("%d failure(s)\n", failures);
    IDirect3DSurface9_Release(readback_surface);
    IDirect3DDevice9_Release(dev); IDirect3D9_Release(d3d);
    DestroyWindow(hwnd);
    return failures;
}
