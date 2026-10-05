/* texstash - managed textures in a large-address-aware 32-bit process, the way the game loads them,
 * past the 4 GB address space: what wined3d patch 0022 (patches/wined3d-wow64-buffers) changes, and
 * that every texture still draws the same (docs/MEMORY-4GB.md, "Patch 0022").
 *
 * Load: textures in our packs' formats and sizes (byte shares of an all-faction match: X8R8G8B8 normal
 * maps 1024/2048, DXT5 and DXT1 sheets 1024-4096, A8R8G8B8 house-colour masks), every level
 * LockRect(NOSYSLOCK)-filled once with bytes from the texture's number (as WW3D2's loader does:
 * D3DPOOL_MANAGED, full chain), until --gb GB or the first failure; --default-frac of them in
 * D3DPOOL_DEFAULT through a SYSTEMMEM staging texture and UpdateTexture. After every 256 MB the 4 GB
 * is walked with VirtualQuery: committed + reserved ("used"), the largest free block, the peak.
 *
 * Check: each texture is drawn twice into a 128x64 target, point-sampled 1:1 - a 64x64 window of level
 * 0 and its first level of 64 or less - and read back; one CRC32 per texture ("CRC <n> <crc>" lines).
 * The bytes depend on the texture's number only, so two runs (with and without the patch) must print
 * the same CRC for every texture both created. Then: EvictManagedResources and draw again; relock 32
 * managed textures (read back, compare, rewrite level 0 with other bytes, draw); GetDC on 4 X8R8G8B8
 * level-0 surfaces (a GDI rectangle, draw); device Reset (managed textures survive it) and draw again.
 * Every check prints CRC lines; "FAIL" lines are hard failures.
 *
 * Time: fill (application thread), first draw of each texture (upload; finished with an event query)
 * per MB, and --frames frames drawing 256 already-uploaded textures with a dynamic vertex buffer
 * (DISCARD/NOOVERWRITE, wined3d 0003/0009) - median ms per frame.
 *
 * Build: i686-w64-mingw32-gcc -O2 -msse2 -mfpmath=sse -Wl,--large-address-aware -o build/texstash.exe tools/texstash.c
 *          -ld3d9 -lgdi32   (SSE maths: CreateDevice drops the x87 to 24 bits, too coarse for the clock)
 * Run:   scripts/texstash.sh (both engines, compares the CRCs)
 * Args:  --gb G (4.5) --default-frac F (0.1) --frames N (120) --crc-file PATH
 *        --reserve MB (0): take MB of address space first, as the game's own memory would (~1300 in a match)
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXTEX 8192
typedef struct { D3DFORMAT fmt; UINT w, h; } Kind;
/* byte shares close to an all-faction match (docs/MEMORY-2GB.md): ~40 % X8R8G8B8, ~37 % DXT5, ~22 % DXT1 */
static const Kind mix[] = {
    {D3DFMT_X8R8G8B8, 1024, 1024}, {(D3DFORMAT)MAKEFOURCC('D','X','T','5'), 2048, 2048},
    {(D3DFORMAT)MAKEFOURCC('D','X','T','1'), 2048, 2048}, {D3DFMT_X8R8G8B8, 1024, 1024},
    {(D3DFORMAT)MAKEFOURCC('D','X','T','5'), 1024, 1024}, {D3DFMT_X8R8G8B8, 2048, 2048},
    {(D3DFORMAT)MAKEFOURCC('D','X','T','5'), 2048, 2048}, {(D3DFORMAT)MAKEFOURCC('D','X','T','1'), 4096, 4096},
    {D3DFMT_A8R8G8B8, 2048, 1024}, {(D3DFORMAT)MAKEFOURCC('D','X','T','5'), 4096, 4096},
    {(D3DFORMAT)MAKEFOURCC('D','X','T','1'), 1024, 1024}, {D3DFMT_X8R8G8B8, 1024, 1024},
};
#define NMIX (sizeof(mix) / sizeof(mix[0]))

static struct { double gb, default_frac; int frames, reserve; const char *crc_file; } opt = {4.5, 0.1, 120, 0, NULL};
static IDirect3DDevice9 *dev;
static D3DPRESENT_PARAMETERS pp;
static IDirect3DTexture9 *tex[MAXTEX];
static int ntex, nfail, is_default[MAXTEX];
static HRESULT last_hr;
static double tex_mb[MAXTEX];
static FILE *crcf;
static double peak_used, min_largest = 1e9;

static double now_ms(void)
{
    static LARGE_INTEGER f;
    LARGE_INTEGER c;
    if (!f.QuadPart) QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&c);
    return c.QuadPart * 1000.0 / f.QuadPart;
}

static void vm(const char *phase, double payload)
{
    MEMORY_BASIC_INFORMATION m;
    char *p = (char *)0x10000;
    double used = 0, freemb = 0, largest = 0;
    while ((ULONG_PTR)p < 0xffff0000u && VirtualQuery(p, &m, sizeof(m)))
    {
        double mb = m.RegionSize / 1048576.0;
        if (m.State == MEM_FREE) { freemb += mb; if (mb > largest) largest = mb; }
        else used += mb;
        if ((ULONG_PTR)m.BaseAddress + m.RegionSize < (ULONG_PTR)p) break;
        p = (char *)m.BaseAddress + m.RegionSize;
        if (!p) break;
    }
    if (used > peak_used) peak_used = used;
    if (largest < min_largest) min_largest = largest;
    printf("VA %-14s payload %7.0f MB  used %7.0f MB  free %7.0f MB  largest free %6.0f MB\n", phase, payload, used,
           freemb, largest);
    fflush(stdout);
}

static int is_dxt(D3DFORMAT f) { return f == (D3DFORMAT)MAKEFOURCC('D','X','T','1') || f == (D3DFORMAT)MAKEFOURCC('D','X','T','5'); }

static UINT level_bytes(D3DFORMAT f, UINT w, UINT h)
{
    if (is_dxt(f)) return ((w + 3) / 4) * ((h + 3) / 4) * (f == (D3DFORMAT)MAKEFOURCC('D','X','T','1') ? 8 : 16);
    return w * h * 4;
}

static UINT rows_of(D3DFORMAT f, UINT h) { return is_dxt(f) ? (h + 3) / 4 : h; }

/* the bytes of texture n, level l: a xorshift stream from (n, l, seed) */
static void fill(BYTE *dst, INT pitch, D3DFORMAT f, UINT w, UINT h, unsigned n, unsigned l, unsigned seed)
{
    UINT y, x, rows = rows_of(f, h), row = level_bytes(f, w, h) / rows;
    unsigned s = 2463534242u ^ (n * 2654435761u) ^ (l * 40503u) ^ seed;
    for (y = 0; y < rows; ++y)
    {
        unsigned *d = (unsigned *)(dst + y * pitch);
        for (x = 0; x < row / 4; ++x) { s ^= s << 13; s ^= s >> 17; s ^= s << 5; d[x] = s; }
    }
}

static int fill_texture(IDirect3DTexture9 *t, const Kind *k, unsigned n, unsigned seed, int only0)
{
    DWORD l, levels = only0 ? 1 : IDirect3DTexture9_GetLevelCount(t);
    for (l = 0; l < levels; ++l)
    {
        D3DLOCKED_RECT lr;
        UINT w = max(1, k->w >> l), h = max(1, k->h >> l);
        if (FAILED(IDirect3DTexture9_LockRect(t, l, &lr, NULL, D3DLOCK_NOSYSLOCK))) return 0;
        fill(lr.pBits, lr.Pitch, k->fmt, w, h, n, l, seed);
        IDirect3DTexture9_UnlockRect(t, l);
    }
    return 1;
}

static double chain_mb(const Kind *k)
{
    UINT w = k->w, h = k->h;
    double b = 0;
    for (; w || h; w >>= 1, h >>= 1) b += level_bytes(k->fmt, max(1, w), max(1, h));
    return b / 1048576.0;
}

static int create(int n)
{
    const Kind *k = &mix[n % NMIX];
    IDirect3DTexture9 *t = NULL, *stage = NULL;
    int dflt = opt.default_frac > 0 && (n % 100) < (int)(opt.default_frac * 100);
    if (dflt)
    {
        if (FAILED(IDirect3DDevice9_CreateTexture(dev, k->w, k->h, 0, 0, k->fmt, D3DPOOL_SYSTEMMEM, &stage, NULL))) return 0;
        if (!fill_texture(stage, k, n, 0, 0)
                || FAILED(IDirect3DDevice9_CreateTexture(dev, k->w, k->h, 0, 0, k->fmt, D3DPOOL_DEFAULT, &t, NULL))
                || FAILED(IDirect3DDevice9_UpdateTexture(dev, (IDirect3DBaseTexture9 *)stage, (IDirect3DBaseTexture9 *)t)))
        { IDirect3DTexture9_Release(stage); if (t) IDirect3DTexture9_Release(t); return 0; }
        IDirect3DTexture9_Release(stage);
    }
    else
    {
        if (FAILED(last_hr = IDirect3DDevice9_CreateTexture(dev, k->w, k->h, 0, 0, k->fmt, D3DPOOL_MANAGED, &t, NULL))) return 0;
        if (!fill_texture(t, k, n, 0, 0)) { IDirect3DTexture9_Release(t); return 0; }
    }
    tex[n] = t, is_default[n] = dflt, tex_mb[n] = chain_mb(k);
    return 1;
}

/* ---- drawing */
typedef struct { float x, y, z, rhw, u, v; } Vtx;
static IDirect3DVertexBuffer9 *vb;
static UINT vb_pos;
static IDirect3DSurface9 *rt, *sys, *backbuf;
#define VB_QUADS 4096

static void quad(float x, float y, float w, float h, float u0, float v0, float u1, float v1)
{
    Vtx *v;
    DWORD flags = D3DLOCK_NOOVERWRITE;
    if (vb_pos + 4 > VB_QUADS * 4) { vb_pos = 0; flags = D3DLOCK_DISCARD; }
    IDirect3DVertexBuffer9_Lock(vb, vb_pos * sizeof(Vtx), 4 * sizeof(Vtx), (void **)&v, flags);
    v[0] = (Vtx){x - .5f, y - .5f, .5f, 1, u0, v0};     v[1] = (Vtx){x + w - .5f, y - .5f, .5f, 1, u1, v0};
    v[2] = (Vtx){x - .5f, y + h - .5f, .5f, 1, u0, v1}; v[3] = (Vtx){x + w - .5f, y + h - .5f, .5f, 1, u1, v1};
    IDirect3DVertexBuffer9_Unlock(vb);
    IDirect3DDevice9_DrawPrimitive(dev, D3DPT_TRIANGLESTRIP, vb_pos, 2);
    vb_pos += 4;
}

static unsigned crc32(const BYTE *p, size_t n, unsigned c)
{
    size_t i;
    int k;
    c = ~c;
    for (i = 0; i < n; ++i) { c ^= p[i]; for (k = 0; k < 8; ++k) c = c >> 1 ^ (0xedb88320u & -(c & 1)); }
    return ~c;
}

static void finish(void)
{
    IDirect3DQuery9 *q;
    if (SUCCEEDED(IDirect3DDevice9_CreateQuery(dev, D3DQUERYTYPE_EVENT, &q)))
    {
        IDirect3DQuery9_Issue(q, D3DISSUE_END);
        while (IDirect3DQuery9_GetData(q, NULL, 0, D3DGETDATA_FLUSH) == S_FALSE) Sleep(0);
        IDirect3DQuery9_Release(q);
    }
}

/* level 0 window and the first level <= 64 of texture n, 1:1, point-sampled; CRC of the 128x64 */
static unsigned draw_crc(int n)
{
    const Kind *k = &mix[n % NMIX];
    D3DLOCKED_RECT lr;
    DWORD l = 0, y;
    unsigned c = 0;
    while (max(k->w >> l, 1) > 64 || max(k->h >> l, 1) > 64) ++l;
    IDirect3DDevice9_SetRenderTarget(dev, 0, rt);
    IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0xff00ff00, 1, 0);
    IDirect3DDevice9_BeginScene(dev);
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)tex[n]);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAXMIPLEVEL, 0);
    quad(0, 0, 64, 64, 0, 0, 64.0f / k->w, 64.0f / k->h);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAXMIPLEVEL, l);
    quad(64, 0, (float)max(k->w >> l, 1), (float)max(k->h >> l, 1), 0, 0, 1, 1);
    IDirect3DDevice9_EndScene(dev);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAXMIPLEVEL, 0);
    if (FAILED(IDirect3DDevice9_GetRenderTargetData(dev, rt, sys)) || FAILED(IDirect3DSurface9_LockRect(sys, &lr, NULL, D3DLOCK_READONLY)))
        { printf("FAIL readback of texture %d\n", n); return 0; }
    for (y = 0; y < 64; ++y) c = crc32((BYTE *)lr.pBits + y * lr.Pitch, 128 * 4, c);
    IDirect3DSurface9_UnlockRect(sys);
    return c;
}

static void crc_pass(const char *tag, int from, int to, int step)
{
    int n;
    for (n = from; n < to; n += step)
        if (tex[n]) fprintf(crcf, "CRC %s %d %08x\n", tag, n, draw_crc(n));
    fflush(crcf);
}

static void setup_states(void)
{
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    IDirect3DDevice9_SetStreamSource(dev, 0, vb, 0, sizeof(Vtx));
    IDirect3DDevice9_SetRenderState(dev, D3DRS_LIGHTING, FALSE);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_ZENABLE, FALSE);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_CULLMODE, D3DCULL_NONE);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLORARG1, D3DTA_TEXTURE);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_ALPHAOP, D3DTOP_SELECTARG1);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_ALPHAARG1, D3DTA_TEXTURE);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MINFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAGFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MIPFILTER, D3DTEXF_POINT);
}

static int make_targets(void)
{
    return SUCCEEDED(IDirect3DDevice9_CreateVertexBuffer(dev, VB_QUADS * 4 * sizeof(Vtx), D3DUSAGE_DYNAMIC | D3DUSAGE_WRITEONLY,
                D3DFVF_XYZRHW | D3DFVF_TEX1, D3DPOOL_DEFAULT, &vb, NULL))
        && SUCCEEDED(IDirect3DDevice9_CreateRenderTarget(dev, 128, 64, D3DFMT_A8R8G8B8, D3DMULTISAMPLE_NONE, 0, FALSE, &rt, NULL))
        && SUCCEEDED(IDirect3DDevice9_CreateOffscreenPlainSurface(dev, 128, 64, D3DFMT_A8R8G8B8, D3DPOOL_SYSTEMMEM, &sys, NULL))
        && SUCCEEDED(IDirect3DDevice9_GetBackBuffer(dev, 0, 0, D3DBACKBUFFER_TYPE_MONO, &backbuf));
}

static void release_targets(void)
{
    IDirect3DVertexBuffer9_Release(vb); IDirect3DSurface9_Release(rt);
    IDirect3DSurface9_Release(sys); IDirect3DSurface9_Release(backbuf);
    vb_pos = 0;
}

static int cmp_double(const void *a, const void *b) { double d = *(double *)a - *(double *)b; return d < 0 ? -1 : d > 0; }

int main(int argc, char **argv)
{
    IDirect3D9 *d3d;
    HWND wnd;
    double t0, payload = 0, next = 256, fill_ms, up_ms, up_mb = 0, *ft;
    int i, n, relocked = 0;

    for (i = 1; i < argc; ++i)
    {
        if (!strcmp(argv[i], "--gb") && i + 1 < argc) opt.gb = atof(argv[++i]);
        else if (!strcmp(argv[i], "--default-frac") && i + 1 < argc) opt.default_frac = atof(argv[++i]);
        else if (!strcmp(argv[i], "--frames") && i + 1 < argc) opt.frames = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--crc-file") && i + 1 < argc) opt.crc_file = argv[++i];
        else if (!strcmp(argv[i], "--reserve") && i + 1 < argc) opt.reserve = atoi(argv[++i]);
        else { printf("usage: texstash [--gb G] [--default-frac F] [--frames N] [--crc-file PATH] [--reserve MB]\n"); return 2; }
    }
    /* --reserve: commit MB in 16 MB pieces first, standing in for the game's own use (~1.3 GB in a match) */
    for (i = 0; i < opt.reserve / 16; ++i)
        if (!VirtualAlloc(NULL, 16 << 20, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE)) { printf("FAIL --reserve at %d MB\n", i * 16); break; }
    crcf = opt.crc_file ? fopen(opt.crc_file, "w") : stdout;
    if (!crcf) { printf("FAIL cannot write %s\n", opt.crc_file); return 2; }
    wnd = CreateWindowA("static", "texstash", WS_OVERLAPPEDWINDOW, 0, 0, 256, 128, 0, 0, 0, 0);
    if (!(d3d = Direct3DCreate9(D3D_SDK_VERSION))) { printf("FAIL Direct3DCreate9\n"); return 2; }
    pp.Windowed = TRUE, pp.SwapEffect = D3DSWAPEFFECT_DISCARD, pp.BackBufferWidth = 256, pp.BackBufferHeight = 128;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8, pp.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;
    if (FAILED(IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, wnd, D3DCREATE_HARDWARE_VERTEXPROCESSING | D3DCREATE_FPU_PRESERVE, &pp, &dev)))
    { printf("FAIL CreateDevice\n"); return 2; }
    if (!make_targets()) { printf("FAIL targets\n"); return 2; }
    setup_states();
    vm("device", 0);

    /* load until --gb or the first failure */
    t0 = now_ms();
    for (n = 0; n < MAXTEX && payload < opt.gb * 1024; ++n)
    {
        if (!create(n)) { ++nfail; printf("FAIL create/fill texture %d (%s %ux%u) at %.0f MB, hr %#lx (%s); GetAvailableTextureMem %u MB\n", n,
                is_dxt(mix[n % NMIX].fmt) ? "DXT" : "RGB", mix[n % NMIX].w, mix[n % NMIX].h, payload, last_hr,
                last_hr == D3DERR_OUTOFVIDEOMEMORY ? "out of video memory" : last_hr == E_OUTOFMEMORY ? "out of memory" : "-",
                IDirect3DDevice9_GetAvailableTextureMem(dev) >> 20); break; }
        payload += tex_mb[n];
        if (payload >= next) { vm("loaded", payload); next += 256; }
    }
    ntex = n;
    fill_ms = now_ms() - t0;
    vm("loaded", payload);
    printf("LOAD %d textures, %.0f MB, %d failed; fill %.2f ms/MB (application thread)\n", ntex, payload, nfail, fill_ms / payload);

    /* first draw of each = the upload */
    t0 = now_ms();
    for (n = 0; n < ntex; ++n) if (tex[n]) { fprintf(crcf, "CRC first %d %08x\n", n, draw_crc(n)); if (!is_default[n]) up_mb += tex_mb[n]; }
    finish();
    up_ms = now_ms() - t0;
    vm("drawn", payload);
    printf("UPLOAD first draws: %.2f ms per managed MB (incl. one 128x64 readback per texture)\n", up_ms / up_mb);

    /* frames: 256 uploaded textures, 4 quads each, dynamic VB */
    ft = malloc(sizeof(double) * opt.frames);
    IDirect3DDevice9_SetRenderTarget(dev, 0, backbuf);
    finish();
    up_ms = now_ms();
    for (i = 0; i < opt.frames; ++i)
    {
        int j;
        t0 = now_ms();
        IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0, 1, 0);
        IDirect3DDevice9_BeginScene(dev);
        for (j = 0; j < 256 && j < ntex; ++j)
        {
            int m = (i * 37 + j * 13) % ntex, q;
            if (!tex[m]) continue;
            IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)tex[m]);
            for (q = 0; q < 4; ++q) quad((float)(j % 16) * 16, (float)(j / 16) * 8 + q, 16, 8, 0, 0, 1, 1);
        }
        IDirect3DDevice9_EndScene(dev);
        IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
        ft[i] = now_ms() - t0;
    }
    finish();
    up_ms = (now_ms() - up_ms) / opt.frames;
    qsort(ft, opt.frames, sizeof(double), cmp_double);
    printf("FRAMES %d: application thread median %.3f ms, p95 %.3f ms; with the GPU done %.3f ms a frame "
           "(256 textures, 1024 quads, dynamic VB)\n", opt.frames, ft[opt.frames / 2], ft[opt.frames * 95 / 100], up_ms);

    /* eviction: the GPU copies go; the next draw uploads again from the (stashed) system memory */
    IDirect3DDevice9_EvictManagedResources(dev);
    t0 = now_ms();
    crc_pass("evict", 0, ntex, 1);
    finish();
    vm("after evict", payload);
    printf("EVICT redraw of every texture: %.2f ms per managed MB\n", (now_ms() - t0) / up_mb);

    /* relock 32 managed textures: read level 0 back, compare, rewrite it with other bytes, draw */
    for (n = 0; n < ntex && relocked < 32; n += max(1, ntex / 32))
    {
        const Kind *k = &mix[n % NMIX];
        D3DLOCKED_RECT lr;
        UINT bytes = level_bytes(k->fmt, k->w, k->h), rows = rows_of(k->fmt, k->h), y;
        BYTE *want;
        if (!tex[n] || is_default[n]) continue;
        want = malloc(bytes);
        fill(want, bytes / rows, k->fmt, k->w, k->h, n, 0, 0);
        if (FAILED(IDirect3DTexture9_LockRect(tex[n], 0, &lr, NULL, D3DLOCK_READONLY))) { printf("FAIL relock %d\n", n); free(want); continue; }
        for (y = 0; y < rows; ++y)
            if (memcmp((BYTE *)lr.pBits + y * lr.Pitch, want + y * (bytes / rows), bytes / rows)) { printf("FAIL relock %d: level 0 row %u differs\n", n, y); break; }
        IDirect3DTexture9_UnlockRect(tex[n], 0);
        free(want);
        fill_texture(tex[n], k, n, 0x5eed, 1);
        fprintf(crcf, "CRC relock %d %08x\n", n, draw_crc(n));
        ++relocked;
    }
    vm("after relock", payload);

    /* GetDC on X8R8G8B8 level 0 surfaces: a GDI rectangle, then draw */
    for (n = 0, i = 0; n < ntex && i < 4; ++n)
    {
        IDirect3DSurface9 *s;
        HDC dc;
        RECT r = {0, 0, 48, 48};
        if (!tex[n] || is_default[n] || mix[n % NMIX].fmt != D3DFMT_X8R8G8B8) continue;
        IDirect3DTexture9_GetSurfaceLevel(tex[n], 0, &s);
        if (FAILED(IDirect3DSurface9_GetDC(s, &dc))) { printf("FAIL GetDC %d\n", n); IDirect3DSurface9_Release(s); continue; }
        FillRect(dc, &r, GetStockObject(WHITE_BRUSH));
        IDirect3DSurface9_ReleaseDC(s, dc);
        IDirect3DSurface9_Release(s);
        fprintf(crcf, "CRC getdc %d %08x\n", n, draw_crc(n));
        ++i;
    }

    /* device Reset: DEFAULT resources go (here: none of the textures we check), managed ones stay */
    for (n = 0; n < ntex; ++n) if (tex[n] && is_default[n]) { IDirect3DTexture9_Release(tex[n]); tex[n] = NULL; }
    release_targets();
    if (FAILED(IDirect3DDevice9_Reset(dev, &pp))) printf("FAIL Reset\n");
    else
    {
        if (!make_targets()) { printf("FAIL targets after Reset\n"); return 1; }
        setup_states();
        crc_pass("reset", 0, ntex, 1);
        vm("after reset", payload);
    }
    printf("PEAK used %.0f MB of 4096, smallest largest-free %.0f MB\n", peak_used, min_largest);
    for (n = 0; n < ntex; ++n) if (tex[n]) IDirect3DTexture9_Release(tex[n]);
    release_targets();
    vm("released", 0);
    IDirect3DDevice9_Release(dev);
    IDirect3D9_Release(d3d);
    if (crcf != stdout) fclose(crcf);
    return 0;
}
