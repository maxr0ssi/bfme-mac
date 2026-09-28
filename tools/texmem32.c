/* texmem32 - how much of a 32-bit process's address space each byte of Direct3D 9 texture or
 * buffer costs under the Wine in use, without the game. Answers the art mod's question "what does a
 * megabyte of texture cost in BFME2's 2 GB (LAA off)?" (docs/MEMORY-2GB.md).
 *
 * It creates --mb N megabytes of textures the way WW3D2 does (TextureLoadTaskClass: D3DPOOL_MANAGED,
 * full mip chain, every level LockRect(NULL, D3DLOCK_NOSYSLOCK)-filled once), draws each once and
 * waits for the GPU, then EvictManagedResources and draws again, then releases them. After every
 * phase it walks the 2 GB user range with VirtualQuery and prints committed/reserved/free memory
 * and the largest free block, plus the delta per texture byte against the baseline.
 * --pool default makes the same textures in D3DPOOL_DEFAULT through a SYSTEMMEM staging texture
 * and UpdateTexture (staging released): the floor a "free the copy after upload" fix could reach.
 * --vb N does the same for N MB of vertex buffers (--vbpool managed|default|dynamic).
 * --relock re-reads every level after the upload and compares it with what was written (a check
 * for a wined3d that drops its system-memory copy).
 *
 * Build: i686-w64-mingw32-gcc -O2 -o build/texmem32.exe tools/texmem32.c -ld3d9
 * Run:   in a throwaway prefix: WINEPREFIX=<scratch> wine build/texmem32.exe --mb 256
 * Args:  --mb N (256) --size S (1024) --fmt dxt1|dxt5|argb (dxt5) --pool managed|default|sysmem
 *        --vb N --vbpool managed|default|dynamic --relock --hold S (sleep S s at the end, for vmmap)
 *        --batches B (B rounds of --mb, each created, filled and drawn, none released: how far the
 *        process gets before CreateTexture fails, and whether freed memory is reused)
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static struct { int mb, size, vb, relock, hold, batches; D3DFORMAT fmt; D3DPOOL pool; const char *vbpool; }
    opt = { 256, 1024, 0, 0, 0, 0, (D3DFORMAT)MAKEFOURCC('D','X','T','5'), D3DPOOL_MANAGED, "managed" };

typedef struct { double priv, mapped, image, reserved, free, largest; } VmStat;

static void vm_walk(VmStat *s)
{
    MEMORY_BASIC_INFORMATION mbi;
    char *p = (char *)0x10000;
    memset(s, 0, sizeof(*s));
    while ((ULONG_PTR)p < 0x7fff0000 && VirtualQuery(p, &mbi, sizeof(mbi)))
    {
        double mb = mbi.RegionSize / 1048576.0;
        if (mbi.State == MEM_COMMIT)
        {
            if (mbi.Type == MEM_PRIVATE) s->priv += mb;
            else if (mbi.Type == MEM_MAPPED) s->mapped += mb;
            else s->image += mb;
        }
        else if (mbi.State == MEM_RESERVE) s->reserved += mb;
        else if (mbi.State == MEM_FREE) { s->free += mb; if (mb > s->largest) s->largest = mb; }
        p = (char *)mbi.BaseAddress + mbi.RegionSize;
    }
}

static VmStat base;
static double payload_mb;

static void report(const char *phase)
{
    static LARGE_INTEGER last, freq;
    LARGE_INTEGER now;
    VmStat s;
    double used, base_used;
    QueryPerformanceCounter(&now);
    if (!freq.QuadPart) QueryPerformanceFrequency(&freq), last = now;
    printf("%6.0f ms  ", (now.QuadPart - last.QuadPart) * 1000.0 / freq.QuadPart);
    vm_walk(&s);
    used = s.priv + s.mapped + s.image + s.reserved;
    base_used = base.priv + base.mapped + base.image + base.reserved;
    printf("%-22s commit_priv=%7.1f mapped=%6.1f image=%6.1f reserved=%7.1f free=%7.1f largest_free=%7.1f"
            "  d_commit=%7.1f d_addrspace=%7.1f", phase, s.priv, s.mapped, s.image, s.reserved, s.free,
            s.largest, s.priv + s.mapped - base.priv - base.mapped, used - base_used);
    if (payload_mb > 0)
        printf("  per_byte commit=%.3f addrspace=%.3f", (s.priv + s.mapped - base.priv - base.mapped) / payload_mb,
                (used - base_used) / payload_mb);
    printf("\n");
    fflush(stdout);
    QueryPerformanceCounter(&last);
}

static unsigned int level_bytes(D3DFORMAT fmt, unsigned int w, unsigned int h)
{
    if (fmt == (D3DFORMAT)MAKEFOURCC('D','X','T','1')) return ((w + 3) / 4) * ((h + 3) / 4) * 8;
    if (fmt == (D3DFORMAT)MAKEFOURCC('D','X','T','5')) return ((w + 3) / 4) * ((h + 3) / 4) * 16;
    return w * h * 4;
}

static unsigned int rows_of(D3DFORMAT fmt, unsigned int h)
{
    return fmt == D3DFMT_A8R8G8B8 ? h : (h + 3) / 4;
}

static unsigned int seed_byte(unsigned int t, unsigned int l, unsigned int i)
{
    unsigned int x = t * 2654435761u ^ l * 40503u ^ i * 2246822519u;
    x ^= x >> 15; x *= 2246822519u; x ^= x >> 13;
    return x & 0xff;
}

/* Fill (or check) every level of a lockable texture with a deterministic pattern. */
static int fill_texture(IDirect3DTexture9 *tex, unsigned int t, int check, DWORD flags)
{
    unsigned int l, levels = IDirect3DTexture9_GetLevelCount(tex), bad = 0;
    for (l = 0; l < levels; ++l)
    {
        D3DSURFACE_DESC d;
        D3DLOCKED_RECT lr;
        unsigned int r, rows, rowbytes, i;
        IDirect3DTexture9_GetLevelDesc(tex, l, &d);
        if (FAILED(IDirect3DTexture9_LockRect(tex, l, &lr, NULL, flags)))
        {
            static unsigned int fails;
            if (fails++ < 3) printf("FAIL lock %u/%u%s\n", t, l, fails == 3 ? " (further lock failures not shown)" : "");
            return 1;
        }
        rows = rows_of(d.Format, d.Height);
        rowbytes = level_bytes(d.Format, d.Width, d.Height) / rows;
        for (r = 0; r < rows; ++r)
        {
            BYTE *row = (BYTE *)lr.pBits + r * lr.Pitch;
            for (i = 0; i < rowbytes; ++i)
            {
                BYTE v = seed_byte(t, l, r * rowbytes + i);
                if (!check) row[i] = v;
                else if (row[i] != v) ++bad;
            }
        }
        IDirect3DTexture9_UnlockRect(tex, l);
    }
    if (bad) printf("FAIL texture %u: %u bytes differ after upload\n", t, bad);
    return bad != 0;
}

static void wait_gpu(IDirect3DDevice9 *dev)
{
    IDirect3DQuery9 *q;
    if (FAILED(IDirect3DDevice9_CreateQuery(dev, D3DQUERYTYPE_EVENT, &q))) return;
    IDirect3DQuery9_Issue(q, D3DISSUE_END);
    while (IDirect3DQuery9_GetData(q, NULL, 0, D3DGETDATA_FLUSH) == S_FALSE) Sleep(1);
    IDirect3DQuery9_Release(q);
}

typedef struct { float x, y, z, rhw, u, v; } Vtx;

static void draw_all(IDirect3DDevice9 *dev, IDirect3DTexture9 **tex, unsigned int n)
{
    static const Vtx quad[4] = {{0,0,0,1,0,0},{64,0,0,1,1,0},{0,64,0,1,0,1},{64,64,0,1,1,1}};
    unsigned int i;
    IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0, 1.0f, 0);
    IDirect3DDevice9_BeginScene(dev);
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    for (i = 0; i < n; ++i)
    {
        IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)tex[i]);
        IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, quad, sizeof(Vtx));
    }
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    IDirect3DDevice9_EndScene(dev);
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
    wait_gpu(dev);
}

/* Draw the first 15 textures point-sampled in a grid and checksum the back buffer: the GPU copies
 * must stay the same through a build change, an eviction and a relock. */
static unsigned int render_crc(IDirect3DDevice9 *dev, IDirect3DTexture9 **tex, unsigned int n)
{
    IDirect3DSurface9 *bb, *sys;
    D3DLOCKED_RECT lr;
    unsigned int i, x, y, crc = ~0u;
    IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0, 1.0f, 0);
    IDirect3DDevice9_BeginScene(dev);
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MINFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAGFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MIPFILTER, D3DTEXF_NONE);
    for (i = 0; i < n && i < 15; ++i)
    {
        float x0 = (float)(i % 5) * 128, y0 = (float)(i / 5) * 128;
        Vtx q[4] = {{x0,y0,0,1,0,0},{x0+128,y0,0,1,1,0},{x0,y0+128,0,1,0,1},{x0+128,y0+128,0,1,1,1}};
        IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)tex[i]);
        IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, q, sizeof(Vtx));
    }
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    IDirect3DDevice9_EndScene(dev);
    IDirect3DDevice9_GetRenderTarget(dev, 0, &bb);
    IDirect3DDevice9_CreateOffscreenPlainSurface(dev, 640, 480, D3DFMT_X8R8G8B8, D3DPOOL_SYSTEMMEM, &sys, NULL);
    IDirect3DDevice9_GetRenderTargetData(dev, bb, sys);
    IDirect3DSurface9_LockRect(sys, &lr, NULL, D3DLOCK_READONLY);
    for (y = 0; y < 384; ++y)
        for (x = 0; x < 640 * 4; ++x)
        {
            unsigned int k;
            crc ^= ((BYTE *)lr.pBits)[y * lr.Pitch + x] | ((x & 3) == 3 ? 0xff : 0);
            for (k = 0; k < 8; ++k) crc = (crc >> 1) ^ (0xedb88320u & -(crc & 1));
        }
    IDirect3DSurface9_UnlockRect(sys);
    IDirect3DSurface9_Release(sys);
    IDirect3DSurface9_Release(bb);
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
    return ~crc;
}

static void run_textures(IDirect3DDevice9 *dev)
{
    unsigned int per = 0, n, i, s, fails = 0;
    IDirect3DTexture9 **tex;
    for (s = opt.size; s; s >>= 1) per += level_bytes(opt.fmt, s, s);
    n = (unsigned int)(((double)opt.mb * 1048576.0) / per + 0.5);
    payload_mb = (double)n * per / 1048576.0;
    tex = calloc(n, sizeof(*tex));
    printf("textures: %u x %ux%u %.4s, %u bytes each with mips, payload %.1f MB, pool %d\n",
            n, opt.size, opt.size, opt.fmt == D3DFMT_A8R8G8B8 ? "ARGB" : (char *)&opt.fmt, per, payload_mb, opt.pool);
    for (i = 0; i < n; ++i)
    {
        HRESULT hr;
        if (opt.pool == D3DPOOL_DEFAULT)
        {
            IDirect3DTexture9 *stage;
            if (FAILED(hr = IDirect3DDevice9_CreateTexture(dev, opt.size, opt.size, 0, 0, opt.fmt,
                    D3DPOOL_SYSTEMMEM, &stage, NULL))) { printf("FAIL create staging %u %#lx\n", i, hr); break; }
            fill_texture(stage, i, 0, D3DLOCK_NOSYSLOCK);
            if (FAILED(hr = IDirect3DDevice9_CreateTexture(dev, opt.size, opt.size, 0, 0, opt.fmt,
                    D3DPOOL_DEFAULT, &tex[i], NULL))) { printf("FAIL create %u %#lx\n", i, hr); IDirect3DTexture9_Release(stage); break; }
            IDirect3DDevice9_UpdateTexture(dev, (IDirect3DBaseTexture9 *)stage, (IDirect3DBaseTexture9 *)tex[i]);
            IDirect3DTexture9_Release(stage);
            if (!(i % 64)) wait_gpu(dev);
        }
        else
        {
            if (FAILED(hr = IDirect3DDevice9_CreateTexture(dev, opt.size, opt.size, 0, 0, opt.fmt,
                    opt.pool, &tex[i], NULL))) { printf("FAIL create %u %#lx\n", i, hr); break; }
            fill_texture(tex[i], i, 0, D3DLOCK_NOSYSLOCK);
        }
    }
    n = i;
    report("created+filled");
    if (opt.pool == D3DPOOL_SYSTEMMEM) goto release;
    draw_all(dev, tex, n);
    report("drawn once");
    printf("CRC drawn once %08x\n", render_crc(dev, tex, n));
    draw_all(dev, tex, n);
    report("drawn twice");
    if (opt.relock)
    {
        for (i = 0; i < n; ++i) fails += fill_texture(tex[i], i, 1, D3DLOCK_READONLY | D3DLOCK_NOSYSLOCK);
        printf("relock check: %u of %u textures differ\n", fails, n);
        report("after relock read");
        draw_all(dev, tex, n);
        report("drawn after relock");
        printf("CRC after relock %08x\n", render_crc(dev, tex, n));
    }
    IDirect3DDevice9_EvictManagedResources(dev);
    report("evicted");
    draw_all(dev, tex, n);
    report("drawn after evict");
    printf("CRC after evict %08x\n", render_crc(dev, tex, n));
release:
    for (i = 0; i < n; ++i) IDirect3DTexture9_Release(tex[i]);
    wait_gpu(dev);
    report("released");
    free(tex);
}

/* A level being loaded bit by bit: --batches B rounds of --mb N managed textures, each round
 * created, filled and drawn, none released. Shows whether memory freed after upload is reused. */
static void run_batches(IDirect3DDevice9 *dev)
{
    unsigned int per = 0, n, b, i, s;
    IDirect3DTexture9 **tex;
    char name[32];
    for (s = opt.size; s; s >>= 1) per += level_bytes(opt.fmt, s, s);
    n = (unsigned int)(((double)opt.mb * 1048576.0) / per + 0.5);
    tex = calloc(n * opt.batches, sizeof(*tex));
    printf("batches: %d x %u textures %ux%u %.4s (%u bytes each)\n", opt.batches, n, opt.size, opt.size,
            opt.fmt == D3DFMT_A8R8G8B8 ? "ARGB" : (char *)&opt.fmt, per);
    for (b = 0; b < (unsigned int)opt.batches; ++b)
    {
        for (i = b * n; i < (b + 1) * n; ++i)
        {
            if (FAILED(IDirect3DDevice9_CreateTexture(dev, opt.size, opt.size, 0, 0, opt.fmt,
                    D3DPOOL_MANAGED, &tex[i], NULL))) { printf("FAIL create %u (out of memory?)\n", i); goto done; }
            fill_texture(tex[i], i, 0, D3DLOCK_NOSYSLOCK);
        }
        draw_all(dev, tex + b * n, n);
        payload_mb = (double)(b + 1) * n * per / 1048576.0;
        sprintf(name, "batch %u drawn", b + 1);
        report(name);
    }
done:
    for (i = 0; i < n * opt.batches && tex[i]; ++i) IDirect3DTexture9_Release(tex[i]);
    free(tex);
}

static void run_buffers(IDirect3DDevice9 *dev)
{
    enum { CHUNK = 1 << 20 };
    unsigned int n = opt.vb, i;
    IDirect3DVertexBuffer9 **vb = calloc(n, sizeof(*vb));
    D3DPOOL pool = strcmp(opt.vbpool, "managed") ? D3DPOOL_DEFAULT : D3DPOOL_MANAGED;
    DWORD usage = D3DUSAGE_WRITEONLY | (strcmp(opt.vbpool, "dynamic") ? 0 : D3DUSAGE_DYNAMIC);
    payload_mb = n;
    printf("vertex buffers: %u x 1 MB, pool %d usage %#lx\n", n, pool, usage);
    for (i = 0; i < n; ++i)
    {
        void *p;
        if (FAILED(IDirect3DDevice9_CreateVertexBuffer(dev, CHUNK, usage, D3DFVF_XYZRHW | D3DFVF_TEX1, pool, &vb[i], NULL)))
        { printf("FAIL vb %u\n", i); break; }
        IDirect3DVertexBuffer9_Lock(vb[i], 0, 0, &p, usage & D3DUSAGE_DYNAMIC ? D3DLOCK_DISCARD : 0);
        memset(p, i & 0xff, CHUNK);
        memset(p, 0, 3 * sizeof(Vtx));
        IDirect3DVertexBuffer9_Unlock(vb[i]);
    }
    n = i;
    report("vb created+filled");
    IDirect3DDevice9_BeginScene(dev);
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    for (i = 0; i < n; ++i)
    {
        IDirect3DDevice9_SetStreamSource(dev, 0, vb[i], 0, sizeof(Vtx));
        IDirect3DDevice9_DrawPrimitive(dev, D3DPT_TRIANGLELIST, 0, 1);
    }
    IDirect3DDevice9_EndScene(dev);
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
    wait_gpu(dev);
    report("vb drawn");
    for (i = 0; i < n; ++i) IDirect3DVertexBuffer9_Release(vb[i]);
    wait_gpu(dev);
    report("vb released");
    free(vb);
}

int main(int argc, char **argv)
{
    D3DPRESENT_PARAMETERS pp = {0};
    IDirect3DDevice9 *dev;
    IDirect3D9 *d3d;
    HWND wnd;
    int i;

    for (i = 1; i < argc; ++i)
    {
        const char *a = argv[i], *v = i + 1 < argc ? argv[i + 1] : "";
        if (!strcmp(a, "--mb")) opt.mb = atoi(v), ++i;
        else if (!strcmp(a, "--size")) opt.size = atoi(v), ++i;
        else if (!strcmp(a, "--vb")) opt.vb = atoi(v), opt.mb = 0, ++i;
        else if (!strcmp(a, "--vbpool")) opt.vbpool = v, ++i;
        else if (!strcmp(a, "--relock")) opt.relock = 1;
        else if (!strcmp(a, "--hold")) opt.hold = atoi(v), ++i;
        else if (!strcmp(a, "--batches")) opt.batches = atoi(v), ++i;
        else if (!strcmp(a, "--fmt"))
        {
            opt.fmt = !strcmp(v, "argb") ? D3DFMT_A8R8G8B8 : !strcmp(v, "dxt1")
                    ? (D3DFORMAT)MAKEFOURCC('D','X','T','1') : (D3DFORMAT)MAKEFOURCC('D','X','T','5');
            ++i;
        }
        else if (!strcmp(a, "--pool"))
        {
            opt.pool = !strcmp(v, "default") ? D3DPOOL_DEFAULT : !strcmp(v, "sysmem") ? D3DPOOL_SYSTEMMEM : D3DPOOL_MANAGED;
            ++i;
        }
        else { printf("unknown argument %s\n", a); return 2; }
    }

    report("process start");
    wnd = CreateWindowA("static", "texmem32", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 0, 0, 640, 480, 0, 0, 0, 0);
    if (!(d3d = Direct3DCreate9(D3D_SDK_VERSION))) { printf("FAIL Direct3DCreate9\n"); return 1; }
    pp.Windowed = TRUE;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth = 640;
    pp.BackBufferHeight = 480;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8;
    pp.hDeviceWindow = wnd;
    if (FAILED(IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, wnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev)))
    { printf("FAIL CreateDevice\n"); return 1; }
    {
        static const Vtx tri[3] = {{0,0,0,1,0,0},{1,0,0,1,0,0},{0,1,0,1,0,0}};
        IDirect3DDevice9_BeginScene(dev);
        IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
        IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLELIST, 1, tri, sizeof(Vtx));
        IDirect3DDevice9_EndScene(dev);
        IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
        wait_gpu(dev);
    }
    vm_walk(&base);
    report("device ready (base)");
    if (opt.batches) run_batches(dev);
    else if (opt.mb) run_textures(dev);
    if (opt.vb) run_buffers(dev);
    if (opt.hold) Sleep(opt.hold * 1000);
    IDirect3DDevice9_Release(dev);
    IDirect3D9_Release(d3d);
    DestroyWindow(wnd);
    return 0;
}
