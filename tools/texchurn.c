/* texchurn - the game's terrain tile texture churn in a standalone 32-bit D3D9 process, to see whether
 * process memory (the host's, outside the 32-bit address space) stays flat over many create / fill /
 * filter / draw / release cycles (docs/MEMORY-4GB.md, "Growth over a match").
 *
 * Every camera move the game drops the near terrain tiles it no longer needs and bakes new ones: per
 * tile two textures (colour + normal map) made by D3DXCreateTexture(512, 512, 3 levels, MANAGED; with
 * terrain32 X8R8G8B8, else A1R5G5B5), level 0 locked and filled, D3DXFilterTexture for levels 1-2, drawn
 * that frame, released when the camera leaves (docs/PERFORMANCE.md §23, §26). Here: --live textures
 * stay alive; each cycle releases the --per oldest, creates --per new ones the same way, draws every
 * live texture once and presents. Every --every cycles a line
 *     C <cycle> <textures created> <ms> <32-bit committed MB> <32-bit reserved MB> <kept> <kept MB>
 * goes to stdout; scripts/texchurn.sh samples the macOS footprint from outside alongside.
 *
 * Build: i686-w64-mingw32-gcc -O2 -msse2 -mfpmath=sse -Wl,--large-address-aware -o build/texchurn.exe
 *          tools/texchurn.c -ld3d9
 * Args:  --cycles N (2000) --per T (30) --live L (120) --size S (512) --levels N (3)
 *        --fmt x8|a1|dxt1 (x8) --every K (50) --nodraw --nofilter --sysmem (D3DPOOL_SYSTEMMEM, no draw)
 *        --grow N: every N cycles one more texture that stays, its size cycling 256-2048 (new units and
 *        buildings loading in a match), managed, full chain, every level filled, drawn once
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef HRESULT (WINAPI *create_fn)(IDirect3DDevice9 *, UINT, UINT, UINT, DWORD, D3DFORMAT, D3DPOOL,
                                    IDirect3DTexture9 **);
typedef HRESULT (WINAPI *filter_fn)(IDirect3DBaseTexture9 *, const PALETTEENTRY *, UINT, DWORD);

static struct { int cycles, per, live, size, levels, every, draw, filter, sysmem, grow; D3DFORMAT fmt; } opt =
    {2000, 30, 120, 512, 3, 50, 1, 1, 0, 0, D3DFMT_X8R8G8B8};
static IDirect3DDevice9 *dev;
static IDirect3DTexture9 **ring;
static create_fn d3dx_create;
static filter_fn d3dx_filter;

static double now_ms(void)
{
    static LARGE_INTEGER f;
    LARGE_INTEGER c;
    if (!f.QuadPart) QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&c);
    return c.QuadPart * 1000.0 / f.QuadPart;
}

static void vm(double *committed, double *reserved)
{
    MEMORY_BASIC_INFORMATION m;
    char *p = (char *)0x10000;
    *committed = *reserved = 0;
    while ((ULONG_PTR)p < 0xffff0000u && VirtualQuery(p, &m, sizeof(m)))
    {
        if (m.State == MEM_COMMIT) *committed += m.RegionSize / 1048576.0;
        else if (m.State == MEM_RESERVE) *reserved += m.RegionSize / 1048576.0;
        if ((ULONG_PTR)m.BaseAddress + m.RegionSize < (ULONG_PTR)p) break;
        p = (char *)m.BaseAddress + m.RegionSize;
        if (!p) break;
    }
}

static int is_dxt(void) { return opt.fmt == (D3DFORMAT)MAKEFOURCC('D','X','T','1'); }

/* level 0 like the bake writes it (the bytes depend on n), then the mip levels */
static int make(unsigned n, IDirect3DTexture9 **out)
{
    IDirect3DTexture9 *t = NULL;
    D3DLOCKED_RECT lr;
    D3DPOOL pool = opt.sysmem ? D3DPOOL_SYSTEMMEM : D3DPOOL_MANAGED;
    UINT y, x, rows = is_dxt() ? opt.size / 4 : opt.size;
    UINT row = is_dxt() ? opt.size * 2 : opt.size * (opt.fmt == D3DFMT_X8R8G8B8 ? 4 : 2);
    unsigned s = 2463534242u ^ (n * 2654435761u);
    HRESULT hr = d3dx_create ? d3dx_create(dev, opt.size, opt.size, opt.levels, 0, opt.fmt, pool, &t)
                             : IDirect3DDevice9_CreateTexture(dev, opt.size, opt.size, opt.levels, 0, opt.fmt, pool, &t, NULL);
    if (FAILED(hr)) { printf("FAIL create %u: %#lx\n", n, (unsigned long)hr); return 0; }
    if (FAILED(IDirect3DTexture9_LockRect(t, 0, &lr, NULL, 0))) { printf("FAIL lock %u\n", n); return 0; }
    for (y = 0; y < rows; ++y)
    {
        unsigned *d = (unsigned *)((BYTE *)lr.pBits + y * lr.Pitch);
        for (x = 0; x < row / 4; ++x) { s ^= s << 13; s ^= s >> 17; s ^= s << 5; d[x] = s; }
    }
    IDirect3DTexture9_UnlockRect(t, 0);
    if (opt.filter && opt.levels != 1 && d3dx_filter && FAILED(d3dx_filter((IDirect3DBaseTexture9 *)t, NULL, 0, 2 /* BOX */)))
        { printf("FAIL filter %u\n", n); return 0; }
    *out = t;
    return 1;
}

/* --grow: a texture that stays (sizes 256, 512, 1024, 2048 in turn; X8R8G8B8 or DXT5 alternately) */
static IDirect3DTexture9 *kept[65536];
static unsigned nkept;
static double kept_mb;

static int keep_one(void)
{
    static const UINT sizes[] = {256, 1024, 512, 2048, 512, 1024};
    UINT size = sizes[nkept % 6], l, levels;
    D3DFORMAT f = nkept % 2 ? (D3DFORMAT)MAKEFOURCC('D','X','T','5') : D3DFMT_X8R8G8B8;
    IDirect3DTexture9 *t;
    if (nkept == 65536 || FAILED(IDirect3DDevice9_CreateTexture(dev, size, size, 0, 0, f, D3DPOOL_MANAGED, &t, NULL)))
        return 0;
    levels = IDirect3DTexture9_GetLevelCount(t);
    for (l = 0; l < levels; ++l)
    {
        D3DLOCKED_RECT lr;
        UINT w = size >> l ? size >> l : 1, rows = f == D3DFMT_X8R8G8B8 ? w : (w + 3) / 4;
        UINT row = f == D3DFMT_X8R8G8B8 ? w * 4 : ((w + 3) / 4) * 16, y;
        if (FAILED(IDirect3DTexture9_LockRect(t, l, &lr, NULL, 0))) return 0;
        for (y = 0; y < rows; ++y) memset((BYTE *)lr.pBits + y * lr.Pitch, (int)(nkept + l + y), row);
        IDirect3DTexture9_UnlockRect(t, l);
        kept_mb += (double)row * rows / 1048576.0;
    }
    kept[nkept++] = t;
    return 1;
}

typedef struct { float x, y, z, rhw, u, v; } Vtx;

static void draw_all(void)
{
    int i;
    Vtx v[4] = {{-.5f, -.5f, .5f, 1, 0, 0}, {63.5f, -.5f, .5f, 1, 1, 0}, {-.5f, 63.5f, .5f, 1, 0, 1}, {63.5f, 63.5f, .5f, 1, 1, 1}};
    IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0xff000000, 1, 0);
    IDirect3DDevice9_BeginScene(dev);
    for (i = 0; i < opt.live; ++i)
    {
        if (!ring[i]) continue;
        IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)ring[i]);
        IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, v, sizeof(Vtx));
    }
    if (nkept)   /* the newest kept texture: its first draw uploads it */
    {
        IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)kept[nkept - 1]);
        IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, v, sizeof(Vtx));
    }
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    IDirect3DDevice9_EndScene(dev);
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
}

int main(int argc, char **argv)
{
    D3DPRESENT_PARAMETERS pp = {0};
    IDirect3D9 *d3d;
    HMODULE dx;
    HWND wnd;
    unsigned made = 0, head = 0;
    double t0, c, r;
    int i, k;

    for (i = 1; i < argc; ++i)
    {
        const char *a = argv[i], *v = i + 1 < argc ? argv[i + 1] : "0";
        if (!strcmp(a, "--cycles")) opt.cycles = atoi(v), ++i;
        else if (!strcmp(a, "--per")) opt.per = atoi(v), ++i;
        else if (!strcmp(a, "--live")) opt.live = atoi(v), ++i;
        else if (!strcmp(a, "--size")) opt.size = atoi(v), ++i;
        else if (!strcmp(a, "--levels")) opt.levels = atoi(v), ++i;
        else if (!strcmp(a, "--every")) opt.every = atoi(v), ++i;
        else if (!strcmp(a, "--grow")) opt.grow = atoi(v), ++i;
        else if (!strcmp(a, "--nodraw")) opt.draw = 0;
        else if (!strcmp(a, "--nofilter")) opt.filter = 0;
        else if (!strcmp(a, "--sysmem")) opt.sysmem = 1, opt.draw = 0;
        else if (!strcmp(a, "--fmt"))
        {
            opt.fmt = !strcmp(v, "a1") ? D3DFMT_A1R5G5B5 : !strcmp(v, "dxt1") ? (D3DFORMAT)MAKEFOURCC('D','X','T','1')
                    : D3DFMT_X8R8G8B8;
            ++i;
        }
        else { printf("unknown argument %s\n", a); return 2; }
    }
    if (opt.live < opt.per) opt.live = opt.per;
    ring = calloc(opt.live, sizeof(*ring));
    if ((dx = LoadLibraryA("d3dx9_27.dll")))
    {
        d3dx_create = (create_fn)GetProcAddress(dx, "D3DXCreateTexture");
        d3dx_filter = (filter_fn)GetProcAddress(dx, "D3DXFilterTexture");
    }
    printf("texchurn: %d cycles x %d textures %dx%d %d levels fmt %#lx, %d live, d3dx9_27 %s, draw %d, filter %d, pool %s\n",
           opt.cycles, opt.per, opt.size, opt.size, opt.levels, (unsigned long)opt.fmt, opt.live, dx ? "yes" : "no",
           opt.draw, opt.filter, opt.sysmem ? "systemmem" : "managed");
    wnd = CreateWindowA("static", "texchurn", WS_OVERLAPPEDWINDOW, 0, 0, 128, 64, 0, 0, 0, 0);
    if (!(d3d = Direct3DCreate9(D3D_SDK_VERSION))) { printf("FAIL Direct3DCreate9\n"); return 2; }
    pp.Windowed = TRUE, pp.SwapEffect = D3DSWAPEFFECT_DISCARD, pp.BackBufferWidth = 128, pp.BackBufferHeight = 64;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8, pp.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;
    if (FAILED(IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, wnd, D3DCREATE_HARDWARE_VERTEXPROCESSING | D3DCREATE_FPU_PRESERVE, &pp, &dev)))
        { printf("FAIL CreateDevice\n"); return 2; }
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    t0 = now_ms();
    for (i = 0; i <= opt.cycles; ++i)
    {
        if (i % opt.every == 0)
        {
            vm(&c, &r);
            printf("C %d %u %.0f %.0f %.0f %u %.0f\n", i, made, now_ms() - t0, c, r, nkept, kept_mb);
            fflush(stdout);
        }
        if (i == opt.cycles) break;
        for (k = 0; k < opt.per; ++k, head = (head + 1) % opt.live)
        {
            if (ring[head]) IDirect3DTexture9_Release(ring[head]);
            ring[head] = NULL;
            if (!make(made++, &ring[head])) return 1;
        }
        if (opt.grow && i % opt.grow == 0 && !keep_one()) { printf("FAIL keep %u\n", nkept); return 1; }
        if (opt.draw) draw_all();
    }
    for (k = 0; k < (int)nkept; ++k) IDirect3DTexture9_Release(kept[k]);
    for (i = 0; i < opt.live; ++i) if (ring[i]) IDirect3DTexture9_Release(ring[i]);
    vm(&c, &r);
    printf("END %u textures, %.0f ms, committed %.0f MB, reserved %.0f MB\n", made, now_ms() - t0, c, r);
    IDirect3DDevice9_Release(dev);
    IDirect3D9_Release(d3d);
    return 0;
}
