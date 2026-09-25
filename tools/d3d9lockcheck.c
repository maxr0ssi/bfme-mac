/* d3d9lockcheck - checks the D3D9 lock semantics that wined3d's application-thread map paths rely
 * on, by drawing after every lock and reading the frame back. Each check prints "ok" or "--" plus
 * FAIL lines, and the program exits with the number of failures. Run it against two wined3d builds.
 *
 *   managed-pixels   1x1 LockRect of a MANAGED texture between draws (the radar): every draw
 *                    shows the texels written before it and none written after
 *   sysmem-update    LockRect a SYSTEMMEM texture, UpdateTexture into a DEFAULT one, draw, repeat
 *                    with the same textures (text rendering): every draw shows its own contents
 *   update-surface   the same through UpdateSurface
 *   managed-relock   Lock(flags 0) of a MANAGED vertex buffer between draws: reads return what was
 *                    written last, every draw uses the vertices written before it
 *   sysmem-ib        the same with a SYSTEMMEM index buffer rewritten between draws
 *   dynamic-discard  DISCARD LockRect of a DYNAMIC texture: whole, sub-rectangle, every draw
 *   dynamic-levels   DISCARD locks of two levels of a DYNAMIC texture held at the same time
 *
 * Build: i686-w64-mingw32-gcc -O2 -o build/d3d9lockcheck.exe tools/d3d9lockcheck.c -ld3d9
 * Run:   next to a wined3d.dll with WINEDLLOVERRIDES=wined3d=n (as scripts/bench-d3d9.sh stages it)
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#define W 256
#define H 256

static IDirect3DDevice9 *dev;
static IDirect3DSurface9 *readback_surface;
static int failures;

typedef struct { float x, y, z, rhw; DWORD c; float u, v; } Vtx;

static void die(const char *what, HRESULT hr) { printf("FAIL %s: hr=%#lx\n", what, (unsigned long)hr); ExitProcess(100); }
#define CK(x) do { HRESULT hr_ = (x); if (FAILED(hr_)) die(#x, hr_); } while (0)

/* Reports the first few failures of a check; returns 1 when the condition failed. */
static int fail(int *bad, const char *name, const char *fmt, ...)
{
    va_list args;
    failures++;
    if ((*bad)++ < 5)
    {
        printf("FAIL %s: ", name);
        va_start(args, fmt); vprintf(fmt, args); va_end(args);
        printf("\n");
    }
    return 1;
}

static void result(int bad, const char *name)
{
    if (bad > 5) printf("FAIL %s: %d more\n", name, bad - 5);
    printf("%s %s\n", bad ? "--" : "ok", name);
}

static void quad(float x, float y, float sz)
{
    Vtx q[4] = { { x, y, 0, 1, 0, 0, 0 }, { x + sz, y, 0, 1, 0, 1, 0 }, { x, y + sz, 0, 1, 0, 0, 1 }, { x + sz, y + sz, 0, 1, 0, 1, 1 } };
    CK(IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, q, sizeof(*q)));
}

static void begin(void)
{
    CK(IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0xff000000, 1.0f, 0));
    CK(IDirect3DDevice9_BeginScene(dev));
}

/* Ends the scene and returns the frame (valid until the next call). */
static const DWORD *end(void)
{
    IDirect3DSurface9 *bb; D3DLOCKED_RECT lr; static DWORD frame[W * H]; int y;
    CK(IDirect3DDevice9_EndScene(dev));
    CK(IDirect3DDevice9_GetBackBuffer(dev, 0, 0, D3DBACKBUFFER_TYPE_MONO, &bb));
    CK(IDirect3DDevice9_GetRenderTargetData(dev, bb, readback_surface));
    IDirect3DSurface9_Release(bb);
    CK(IDirect3DSurface9_LockRect(readback_surface, &lr, NULL, D3DLOCK_READONLY));
    for (y = 0; y < H; y++) memcpy(frame + y * W, (BYTE *)lr.pBits + y * lr.Pitch, W * 4);
    IDirect3DSurface9_UnlockRect(readback_surface);
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
    return frame;
}

static DWORD px(const DWORD *f, int x, int y) { return f[y * W + x] & 0xffffff; }
static DWORD texel(const D3DLOCKED_RECT *lr, int x, int y) { return ((DWORD *)((BYTE *)lr->pBits + y * lr->Pitch))[x]; }

static void texture_states(void)
{
    IDirect3DDevice9_SetVertexShader(dev, NULL); IDirect3DDevice9_SetPixelShader(dev, NULL);
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_DIFFUSE | D3DFVF_TEX1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLORARG1, D3DTA_TEXTURE);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MINFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAGFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MIPFILTER, D3DTEXF_NONE);
}

/* A 16x16 texture drawn 16 times 1:1; before draw i texel (i, i) gets a colour of its own.
 * Draw i must show the diagonal texels 0..i and not i+1.. */
static void managed_pixels(void)
{
    static const char name[] = "managed-pixels";
    IDirect3DTexture9 *t; D3DLOCKED_RECT lr; RECT r; const DWORD *f; int i, j, y, bad = 0;
    CK(IDirect3DDevice9_CreateTexture(dev, 16, 16, 1, 0, D3DFMT_X8R8G8B8, D3DPOOL_MANAGED, &t, NULL));
    CK(IDirect3DTexture9_LockRect(t, 0, &lr, NULL, 0));
    for (y = 0; y < 16; y++) memset((BYTE *)lr.pBits + y * lr.Pitch, 0x10, 16 * 4);
    IDirect3DTexture9_UnlockRect(t, 0);
    texture_states();
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)t);
    begin();
    for (i = 0; i < 16; i++)
    {
        SetRect(&r, i, i, i + 1, i + 1);
        CK(IDirect3DTexture9_LockRect(t, 0, &lr, &r, 0));
        if ((*(DWORD *)lr.pBits & 0xffffff) != 0x101010)
            fail(&bad, name, "texel %d reads %08lx before it is written", i, (unsigned long)*(DWORD *)lr.pBits);
        *(DWORD *)lr.pBits = 0xff000000u | (0x20 + i * 8) << 16 | 0x80;
        CK(IDirect3DTexture9_UnlockRect(t, 0));
        quad((float)(i % 8) * 32, (float)(i / 8) * 32, 16);
    }
    f = end();
    for (i = 0; i < 16; i++)
        for (j = 0; j < 16; j++)
        {
            DWORD want = j <= i ? (DWORD)((0x20 + j * 8) << 16 | 0x80) : 0x101010, got = px(f, (i % 8) * 32 + j, (i / 8) * 32 + j);
            if (got != want) fail(&bad, name, "draw %d texel %d: got %06lx, want %06lx", i, j, (unsigned long)got, (unsigned long)want);
        }
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    IDirect3DTexture9_Release(t);
    result(bad, name);
}

/* One SYSTEMMEM texture and one DEFAULT texture, 16 rounds of lock/fill/unlock/update/draw. */
static void sysmem_update(int use_surface)
{
    const char *name = use_surface ? "update-surface" : "sysmem-update";
    IDirect3DTexture9 *sys, *def; IDirect3DSurface9 *ss, *ds; D3DLOCKED_RECT lr; const DWORD *f; int i, y, x, bad = 0;
    CK(IDirect3DDevice9_CreateTexture(dev, 16, 16, 1, 0, D3DFMT_X8R8G8B8, D3DPOOL_SYSTEMMEM, &sys, NULL));
    CK(IDirect3DDevice9_CreateTexture(dev, 16, 16, 1, 0, D3DFMT_X8R8G8B8, D3DPOOL_DEFAULT, &def, NULL));
    CK(IDirect3DTexture9_GetSurfaceLevel(sys, 0, &ss)); CK(IDirect3DTexture9_GetSurfaceLevel(def, 0, &ds));
    texture_states();
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)def);
    begin();
    for (i = 0; i < 16; i++)
    {
        CK(IDirect3DSurface9_LockRect(ss, &lr, NULL, D3DLOCK_NOSYSLOCK));
        if (i && texel(&lr, 5, 3) != (0xff000000u | (i - 1) * 0x0f0a05))   /* the previous round's contents */
            fail(&bad, name, "round %d reads %08lx", i, (unsigned long)texel(&lr, 5, 3));
        for (y = 0; y < 16; y++) for (x = 0; x < 16; x++)
            ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = 0xff000000u | i * 0x0f0a05;
        CK(IDirect3DSurface9_UnlockRect(ss));
        if (use_surface) CK(IDirect3DDevice9_UpdateSurface(dev, ss, NULL, ds, NULL));
        else CK(IDirect3DDevice9_UpdateTexture(dev, (IDirect3DBaseTexture9 *)sys, (IDirect3DBaseTexture9 *)def));
        quad((float)(i % 8) * 32, (float)(i / 8) * 32, 16);
    }
    f = end();
    for (i = 0; i < 16; i++)
    {
        DWORD got = px(f, (i % 8) * 32 + 8, (i / 8) * 32 + 8), want = i * 0x0f0a05;
        if (got != want) fail(&bad, name, "draw %d: got %06lx, want %06lx", i, (unsigned long)got, (unsigned long)want);
    }
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    IDirect3DSurface9_Release(ss); IDirect3DSurface9_Release(ds);
    IDirect3DTexture9_Release(sys); IDirect3DTexture9_Release(def);
    result(bad, name);
}

static DWORD quad_colour(int k) { return 0xff000000u | (0x100 + k * 0x0b0d); }

/* A MANAGED vertex buffer of 16 quads. Round i reads the quads back, moves quads 0..i to row i
 * and draws them. Row i of the frame must hold exactly quads 0..i. */
static void managed_relock(int sysmem_ib)
{
    const char *name = sysmem_ib ? "sysmem-ib" : "managed-relock";
    IDirect3DVertexBuffer9 *vb; IDirect3DIndexBuffer9 *ib; Vtx *v; WORD *ix; const DWORD *f; int i, k, bad = 0;
    CK(IDirect3DDevice9_CreateVertexBuffer(dev, 64 * sizeof(Vtx), D3DUSAGE_WRITEONLY, 0, D3DPOOL_MANAGED, &vb, NULL));
    CK(IDirect3DDevice9_CreateIndexBuffer(dev, 96 * 2, 0, D3DFMT_INDEX16, sysmem_ib ? D3DPOOL_SYSTEMMEM : D3DPOOL_MANAGED, &ib, NULL));
    CK(IDirect3DVertexBuffer9_Lock(vb, 0, 0, (void **)&v, 0));
    memset(v, 0, 64 * sizeof(Vtx));
    IDirect3DVertexBuffer9_Unlock(vb);
    CK(IDirect3DIndexBuffer9_Lock(ib, 0, 0, (void **)&ix, 0));
    memset(ix, 0, 96 * 2);
    IDirect3DIndexBuffer9_Unlock(ib);
    IDirect3DDevice9_SetVertexShader(dev, NULL); IDirect3DDevice9_SetPixelShader(dev, NULL);
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_DIFFUSE | D3DFVF_TEX1);
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLORARG1, D3DTA_DIFFUSE);
    IDirect3DDevice9_SetStreamSource(dev, 0, vb, 0, sizeof(Vtx));
    IDirect3DDevice9_SetIndices(dev, ib);
    begin();
    for (i = 0; i < 16; i++)
    {
        CK(IDirect3DVertexBuffer9_Lock(vb, 0, 0, (void **)&v, 0));
        for (k = 0; k < i; k++)
            if (v[k * 4].c != quad_colour(k) || v[k * 4].y != (float)(i - 1) * 16)
                fail(&bad, name, "round %d: quad %d reads %08lx at y %.0f", i, k, (unsigned long)v[k * 4].c, v[k * 4].y);
        for (k = 0; k <= i; k++)
        {
            Vtx a = { (float)k * 16, (float)i * 16, 0, 1, quad_colour(k), 0, 0 };
            v[k * 4] = a; v[k * 4 + 1] = a; v[k * 4 + 1].x += 8; v[k * 4 + 2] = a; v[k * 4 + 2].y += 8;
            v[k * 4 + 3] = v[k * 4 + 1]; v[k * 4 + 3].y += 8;
        }
        CK(IDirect3DVertexBuffer9_Unlock(vb));
        /* the indices of quad i, written just before the first draw that uses them */
        CK(IDirect3DIndexBuffer9_Lock(ib, i * 12, 12, (void **)&ix, 0));
        { WORD b = i * 4; ix[0] = b; ix[1] = b + 1; ix[2] = b + 2; ix[3] = b + 2; ix[4] = b + 1; ix[5] = b + 3; }
        CK(IDirect3DIndexBuffer9_Unlock(ib));
        CK(IDirect3DDevice9_DrawIndexedPrimitive(dev, D3DPT_TRIANGLELIST, 0, 0, 64, 0, (i + 1) * 2));
    }
    f = end();
    for (i = 0; i < 16; i++)
        for (k = 0; k < 16; k++)
        {
            DWORD got = px(f, k * 16 + 4, i * 16 + 4), want = k <= i ? quad_colour(k) & 0xffffff : 0;
            if (got != want) fail(&bad, name, "row %d quad %d: got %06lx, want %06lx", i, k, (unsigned long)got, (unsigned long)want);
        }
    IDirect3DDevice9_SetStreamSource(dev, 0, NULL, 0, 0); IDirect3DDevice9_SetIndices(dev, NULL);
    IDirect3DVertexBuffer9_Release(vb); IDirect3DIndexBuffer9_Release(ib);
    result(bad, name);
}

static DWORD round_colour(int i) { return 0xff000000u | (0x30 + i * 0x11) << 8 | (0x80 + i * 7); }

/* 12 rounds of a DISCARD lock of a 64x64 DYNAMIC texture (whole, or a 32x32 sub-rectangle on odd
 * rounds), a fill and a draw. Inside the rectangle every draw must show its own colour. */
static void dynamic_discard(void)
{
    static const char name[] = "dynamic-discard";
    IDirect3DTexture9 *t; D3DLOCKED_RECT lr; RECT r; const DWORD *f; int i, x, y, bad = 0;
    CK(IDirect3DDevice9_CreateTexture(dev, 64, 64, 1, D3DUSAGE_DYNAMIC, D3DFMT_X8R8G8B8, D3DPOOL_DEFAULT, &t, NULL));
    texture_states();
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)t);
    begin();
    for (i = 0; i < 12; i++)
    {
        int sub = i & 1;
        SetRect(&r, 16, 8, 48, 40);
        CK(IDirect3DTexture9_LockRect(t, 0, &lr, sub ? &r : NULL, D3DLOCK_DISCARD));
        for (y = 0; y < (sub ? 32 : 64); y++) for (x = 0; x < (sub ? 32 : 64); x++)
            ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = round_colour(i);
        CK(IDirect3DTexture9_UnlockRect(t, 0));
        quad((float)(i % 4) * 64, (float)(i / 4) * 64, 64);
    }
    f = end();
    for (i = 0; i < 12; i++)
    {
        DWORD got = px(f, (i % 4) * 64 + 32, (i / 4) * 64 + 24), want = round_colour(i) & 0xffffff;
        if (got != want) fail(&bad, name, "draw %d: got %06lx, want %06lx", i, (unsigned long)got, (unsigned long)want);
    }
    CK(IDirect3DTexture9_LockRect(t, 0, &lr, NULL, D3DLOCK_READONLY));   /* sees the last write */
    if ((texel(&lr, 20, 20) & 0xffffff) != (round_colour(11) & 0xffffff))
        fail(&bad, name, "READONLY lock reads %08lx", (unsigned long)texel(&lr, 20, 20));
    IDirect3DTexture9_UnlockRect(t, 0);
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    IDirect3DTexture9_Release(t);
    result(bad, name);
}

/* Two levels of a DYNAMIC texture DISCARD-locked at the same time and unlocked in either order;
 * READONLY locks afterwards must see both. */
static void dynamic_levels(void)
{
    static const char name[] = "dynamic-levels";
    IDirect3DTexture9 *t; D3DLOCKED_RECT l0, l1; int round, x, y, bad = 0;
    CK(IDirect3DDevice9_CreateTexture(dev, 32, 32, 2, D3DUSAGE_DYNAMIC, D3DFMT_X8R8G8B8, D3DPOOL_DEFAULT, &t, NULL));
    for (round = 0; round < 4; round++)
    {
        DWORD c0 = 0xff000000u | (0x102030 + round * 0x40), c1 = 0xff000000u | (0x605040 + round * 0x40);
        CK(IDirect3DTexture9_LockRect(t, 0, &l0, NULL, D3DLOCK_DISCARD));
        CK(IDirect3DTexture9_LockRect(t, 1, &l1, NULL, D3DLOCK_DISCARD));
        for (y = 0; y < 32; y++) for (x = 0; x < 32; x++) ((DWORD *)((BYTE *)l0.pBits + y * l0.Pitch))[x] = c0;
        for (y = 0; y < 16; y++) for (x = 0; x < 16; x++) ((DWORD *)((BYTE *)l1.pBits + y * l1.Pitch))[x] = c1;
        if (round & 1) { CK(IDirect3DTexture9_UnlockRect(t, 0)); CK(IDirect3DTexture9_UnlockRect(t, 1)); }
        else { CK(IDirect3DTexture9_UnlockRect(t, 1)); CK(IDirect3DTexture9_UnlockRect(t, 0)); }
        CK(IDirect3DTexture9_LockRect(t, 0, &l0, NULL, D3DLOCK_READONLY));
        CK(IDirect3DTexture9_LockRect(t, 1, &l1, NULL, D3DLOCK_READONLY));
        if (texel(&l0, 9, 7) != c0) fail(&bad, name, "round %d level 0 reads %08lx", round, (unsigned long)texel(&l0, 9, 7));
        if (texel(&l1, 3, 5) != c1) fail(&bad, name, "round %d level 1 reads %08lx", round, (unsigned long)texel(&l1, 3, 5));
        IDirect3DTexture9_UnlockRect(t, 1); IDirect3DTexture9_UnlockRect(t, 0);
    }
    IDirect3DTexture9_Release(t);
    result(bad, name);
}

int main(void)
{
    IDirect3D9 *d3d; D3DPRESENT_PARAMETERS pp = { 0 }; RECT rc = { 0, 0, W, H }; WNDCLASSA wc = { 0 }; HWND hwnd; int pass;
    setvbuf(stdout, NULL, _IONBF, 0);
    wc.lpfnWndProc = DefWindowProcA; wc.hInstance = GetModuleHandleA(NULL); wc.lpszClassName = "d3d9lockcheck";
    RegisterClassA(&wc);
    AdjustWindowRect(&rc, WS_OVERLAPPEDWINDOW, FALSE);
    hwnd = CreateWindowA("d3d9lockcheck", "d3d9lockcheck", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 40, 40,
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

    for (pass = 0; pass < 3; pass++)   /* again with the render thread warmed up */
    {
        printf("pass %d\n", pass);
        managed_pixels();
        sysmem_update(0);
        sysmem_update(1);
        managed_relock(0);
        managed_relock(1);
        dynamic_discard();
        dynamic_levels();
    }

    printf("%d failure(s)\n", failures);
    IDirect3DSurface9_Release(readback_surface);
    IDirect3DDevice9_Release(dev); IDirect3D9_Release(d3d);
    DestroyWindow(hwnd);
    return failures;
}
