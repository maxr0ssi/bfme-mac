/* texupload - what the first use of one texture costs the game's thread under the Wine in use,
 * without the game: the click-time hitch of a portrait or button page, a HUD atlas or a house-colour
 * mask that is loaded the first time it is drawn (docs/PERFORMANCE.md, "First-use texture loads").
 *
 * Per texture, the way WW3D2 loads one (all D3DPOOL_MANAGED, each level LockRect(NOSYSLOCK)-filled):
 *   load   the file's bytes copied out of an in-memory archive (the .big is in the OS cache);
 *   fill   CreateTexture + every level locked and filled. A DDS copies its stored levels. A TGA
 *          (`tga` formats) is flipped bottom-up into an A8R8G8B8/X8R8G8B8 level 0 and, with mips,
 *          box-filtered on the CPU into each further level, as WW3D2's TGA loader does;
 *   draw   SetTexture + one quad: wined3d's upload of every level is queued here;
 *   sync   an event query waited on: the CS thread's upload and the GPU, which the next frame
 *          that needs the CS queue waits for.
 * Each texture is new (fresh bytes), so nothing is cached between samples. The median over --n
 * textures is printed per spec, after one warm-up texture. `frame` = load + fill + draw + sync;
 * `steady` the same frame drawn again with the texture already uploaded; `extra` = frame - steady,
 * what that one new texture adds to the frame it is first drawn in.
 *
 * Build: i686-w64-mingw32-gcc -O2 -o build/texupload.exe tools/texupload.c -ld3d9
 * Run:   in a throwaway prefix: WINEPREFIX=<scratch> wine build/texupload.exe [--n 9] spec...
 * Spec:  fmt:w:h:mips   fmt dxt1|dxt3|dxt5|argb (a DDS of that format) | tga32|tga24 (the TGA path);
 *        mips 0 = the full chain. Example: dxt5:512:512:0 tga32:2048:1024:1 tga32:2048:1024:0
 *        dx:<file>:mips  a real .dds/.tga loaded the way the game loads every texture (game.dat
 *        0x53117e): D3DXCreateTextureFromFileInMemoryEx(dev, bytes, size, 0, 0, mips, 0, UNKNOWN,
 *        MANAGED, D3DX_DEFAULT, D3DX_FILTER_BOX, ...) from the d3dx9_27 the game runs (the engine's
 *        builtin: WINEDLLOVERRIDES=d3dx9_27=b). mips 0 = the file's chain (DDS) or a full one (TGA);
 *        the APT movies ask for 1.
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define D3DX_DEFAULT_FILTER 0xffffffffu

typedef struct { const char *text; D3DFORMAT fmt; int tga, bpp; unsigned int w, h, mips; BYTE *data; DWORD size; } Spec;

typedef HRESULT (WINAPI *CreateFromMemEx)(IDirect3DDevice9 *, const void *, UINT, UINT, UINT, UINT, DWORD, D3DFORMAT,
        D3DPOOL, DWORD, DWORD, D3DCOLOR, void *, void *, IDirect3DTexture9 **);
static CreateFromMemEx d3dx_load;

static int read_file(const char *path, Spec *sp)
{
    FILE *f = fopen(path, "rb");
    long n;
    if (!f) return 0;
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    fseek(f, 0, SEEK_SET);
    sp->data = malloc(n);
    sp->size = (DWORD)fread(sp->data, 1, n, f);
    fclose(f);
    return sp->size == (DWORD)n;
}

/* Milliseconds since the first call, from integer ticks: Direct3D puts the x87 unit in 24-bit
 * precision (as in the game), so an absolute time in a float would lose every digit we need. */
static double now_ms(void)
{
    static LARGE_INTEGER f, t0;
    LARGE_INTEGER c;
    if (!f.QuadPart) QueryPerformanceFrequency(&f), QueryPerformanceCounter(&t0);
    QueryPerformanceCounter(&c);
    return (double)(LONG)(c.QuadPart - t0.QuadPart) / (double)(LONG)(f.QuadPart / 1000);
}

static unsigned int block_bytes(D3DFORMAT fmt)
{
    if (fmt == (D3DFORMAT)MAKEFOURCC('D','X','T','1')) return 8;
    if (fmt == (D3DFORMAT)MAKEFOURCC('D','X','T','3') || fmt == (D3DFORMAT)MAKEFOURCC('D','X','T','5')) return 16;
    return 0;
}

static unsigned int level_bytes(D3DFORMAT fmt, unsigned int w, unsigned int h)
{
    unsigned int b = block_bytes(fmt);
    return b ? ((w + 3) / 4) * ((h + 3) / 4) * b : w * h * 4;
}

static unsigned int full_chain(unsigned int w, unsigned int h)
{
    unsigned int n = 1, m = w > h ? w : h;
    while (m > 1) m >>= 1, ++n;
    return n;
}

static int parse(const char *s, Spec *sp)
{
    char f[16];
    memset(sp, 0, sizeof(*sp));
    sp->text = s;
    if (!strncmp(s, "dx:", 3))
    {
        const char *c = strrchr(s, ':');
        char path[MAX_PATH];
        if (c <= s + 3 || c - s - 3 >= MAX_PATH) return 0;
        memcpy(path, s + 3, c - s - 3);
        path[c - s - 3] = 0;
        sp->mips = atoi(c + 1);
        if (!d3dx_load)
        {
            HMODULE m = LoadLibraryA("d3dx9_27.dll");
            if (m) d3dx_load = (CreateFromMemEx)GetProcAddress(m, "D3DXCreateTextureFromFileInMemoryEx");
            if (!d3dx_load) { printf("FAIL no d3dx9_27\n"); return 0; }
        }
        sp->text = strrchr(path, '\\') ? s + 3 + (strrchr(path, '\\') - path) + 1 : s + 3;
        return read_file(path, sp);
    }
    if (sscanf(s, "%15[^:]:%u:%u:%u", f, &sp->w, &sp->h, &sp->mips) != 4) return 0;
    if (!strcmp(f, "dxt1")) sp->fmt = (D3DFORMAT)MAKEFOURCC('D','X','T','1');
    else if (!strcmp(f, "dxt3")) sp->fmt = (D3DFORMAT)MAKEFOURCC('D','X','T','3');
    else if (!strcmp(f, "dxt5")) sp->fmt = (D3DFORMAT)MAKEFOURCC('D','X','T','5');
    else if (!strcmp(f, "argb")) sp->fmt = D3DFMT_A8R8G8B8;
    else if (!strcmp(f, "tga32")) sp->fmt = D3DFMT_A8R8G8B8, sp->tga = 1, sp->bpp = 4;
    else if (!strcmp(f, "tga24")) sp->fmt = D3DFMT_X8R8G8B8, sp->tga = 1, sp->bpp = 3;
    else return 0;
    if (!sp->mips) sp->mips = full_chain(sp->w, sp->h);
    return 1;
}

/* The bytes the file holds: a TGA's pixels (level 0 only), or every stored level of a DDS. */
static size_t file_bytes(const Spec *sp)
{
    unsigned int l;
    size_t n = 0;
    if (sp->data) return sp->size;
    if (sp->tga) return (size_t)sp->w * sp->h * sp->bpp;
    for (l = 0; l < sp->mips; ++l)
        n += level_bytes(sp->fmt, sp->w >> l ? sp->w >> l : 1, sp->h >> l ? sp->h >> l : 1);
    return n;
}

static void scramble(BYTE *p, size_t n, unsigned int seed)
{
    unsigned int x = seed * 2654435761u + 1;
    size_t i;
    for (i = 0; i + 4 <= n; i += 4)
    {
        x ^= x << 13; x ^= x >> 17; x ^= x << 5;
        memcpy(p + i, &x, 4);
    }
}

/* WW3D2's TGA path: level 0 from the bottom-up file rows, each further level a 2x2 box of the one
 * above, computed on the game's thread. */
static void fill_tga(IDirect3DTexture9 *tex, const Spec *sp, const BYTE *src)
{
    unsigned int l, levels = IDirect3DTexture9_GetLevelCount(tex), w = sp->w, h = sp->h, x, y;
    BYTE *prev = malloc((size_t)w * h * 4), *cur = malloc((size_t)w * h * 4);
    for (y = 0; y < h; ++y)
    {
        const BYTE *s = src + (size_t)(h - 1 - y) * w * sp->bpp;
        BYTE *d = prev + (size_t)y * w * 4;
        for (x = 0; x < w; ++x, s += sp->bpp, d += 4)
            d[0] = s[0], d[1] = s[1], d[2] = s[2], d[3] = sp->bpp == 4 ? s[3] : 0xff;
    }
    for (l = 0; l < levels; ++l)
    {
        D3DLOCKED_RECT lr;
        if (l)
        {
            unsigned int pw = w, nw = w > 1 ? w / 2 : 1, nh = h > 1 ? h / 2 : 1, c;
            BYTE *t;
            for (y = 0; y < nh; ++y)
                for (x = 0; x < nw; ++x)
                    for (c = 0; c < 4; ++c)
                    {
                        unsigned int x0 = x * 2 < pw ? x * 2 : pw - 1, x1 = x * 2 + 1 < pw ? x * 2 + 1 : pw - 1;
                        unsigned int y0 = y * 2 < h ? y * 2 : h - 1, y1 = y * 2 + 1 < h ? y * 2 + 1 : h - 1;
                        cur[((size_t)y * nw + x) * 4 + c] = (BYTE)((prev[((size_t)y0 * pw + x0) * 4 + c]
                            + prev[((size_t)y0 * pw + x1) * 4 + c] + prev[((size_t)y1 * pw + x0) * 4 + c]
                            + prev[((size_t)y1 * pw + x1) * 4 + c] + 2) / 4);
                    }
            t = prev, prev = cur, cur = t, w = nw, h = nh;
        }
        if (FAILED(IDirect3DTexture9_LockRect(tex, l, &lr, NULL, D3DLOCK_NOSYSLOCK))) break;
        for (y = 0; y < h; ++y) memcpy((BYTE *)lr.pBits + y * lr.Pitch, prev + (size_t)y * w * 4, w * 4);
        IDirect3DTexture9_UnlockRect(tex, l);
    }
    free(prev);
    free(cur);
}

static void fill_dds(IDirect3DTexture9 *tex, const Spec *sp, const BYTE *src)
{
    unsigned int l, levels = IDirect3DTexture9_GetLevelCount(tex);
    for (l = 0; l < levels; ++l)
    {
        D3DSURFACE_DESC d;
        D3DLOCKED_RECT lr;
        unsigned int rows, rowbytes, r;
        IDirect3DTexture9_GetLevelDesc(tex, l, &d);
        rows = block_bytes(d.Format) ? (d.Height + 3) / 4 : d.Height;
        rowbytes = level_bytes(d.Format, d.Width, d.Height) / rows;
        if (FAILED(IDirect3DTexture9_LockRect(tex, l, &lr, NULL, D3DLOCK_NOSYSLOCK))) break;
        for (r = 0; r < rows; ++r) memcpy((BYTE *)lr.pBits + r * lr.Pitch, src + (size_t)r * rowbytes, rowbytes);
        IDirect3DTexture9_UnlockRect(tex, l);
        src += (size_t)rows * rowbytes;
    }
}

static void wait_gpu(IDirect3DDevice9 *dev)
{
    IDirect3DQuery9 *q;
    if (FAILED(IDirect3DDevice9_CreateQuery(dev, D3DQUERYTYPE_EVENT, &q))) return;
    IDirect3DQuery9_Issue(q, D3DISSUE_END);
    while (IDirect3DQuery9_GetData(q, NULL, 0, D3DGETDATA_FLUSH) == S_FALSE) SwitchToThread();
    IDirect3DQuery9_Release(q);
}

typedef struct { float x, y, z, rhw, u, v; } Vtx;

/* One quad with the texture; no Present, so the timings hold no swap-chain throttling (a Present
 * and a pause separate the samples instead). */
static void draw(IDirect3DDevice9 *dev, IDirect3DTexture9 *tex)
{
    static const Vtx quad[4] = {{0,0,0,1,0,0},{256,0,0,1,1,0},{0,256,0,1,0,1},{256,256,0,1,1,1}};
    IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0, 1.0f, 0);
    IDirect3DDevice9_BeginScene(dev);
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)tex);
    IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, quad, sizeof(Vtx));
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    IDirect3DDevice9_EndScene(dev);
}

static void settle(IDirect3DDevice9 *dev)
{
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
    wait_gpu(dev);
    Sleep(40);
}

static int cmp_d(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return x < y ? -1 : x > y;
}

static double median(double *v, int n)
{
    qsort(v, n, sizeof(*v), cmp_d);
    return v[n / 2];
}

int main(int argc, char **argv)
{
    IDirect3D9 *d3d;
    IDirect3DDevice9 *dev;
    D3DPRESENT_PARAMETERS pp = {0};
    HWND wnd;
    int i, n = 9;
    Spec specs[32];
    int nspec = 0;

    for (i = 1; i < argc; ++i)
    {
        if (!strcmp(argv[i], "--n") && i + 1 < argc) { n = atoi(argv[++i]); continue; }
        if (nspec == 32 || !parse(argv[i], &specs[nspec])) { printf("FAIL bad spec %s\n", argv[i]); return 1; }
        ++nspec;
    }
    if (!nspec || n < 1 || n > 64) { printf("usage: texupload [--n 9] fmt:w:h:mips...\n"); return 1; }
    now_ms();

    wnd = CreateWindowA("static", "texupload", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 0, 0, 640, 480, 0, 0, 0, 0);
    if (!(d3d = Direct3DCreate9(D3D_SDK_VERSION))) { printf("FAIL Direct3DCreate9\n"); return 1; }
    pp.Windowed = TRUE;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth = 640;
    pp.BackBufferHeight = 480;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8;
    pp.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;
    if (FAILED(IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, wnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev)))
    { printf("FAIL CreateDevice\n"); return 1; }
    draw(dev, NULL);
    wait_gpu(dev);

    printf("%-22s %7s %7s | median ms: %6s %6s %6s %6s %7s %7s %7s\n", "spec", "file MB", "tex MB",
            "load", "fill", "draw", "sync", "frame", "steady", "extra");
    for (i = 0; i < nspec; ++i)
    {
        const Spec *sp = &specs[i];
        size_t fb = file_bytes(sp), tb = 0;
        double load[64], fill[64], drw[64], sync[64], tot[64], steady[64], extra[64];
        BYTE *archive = malloc(fb), *file = malloc(fb);
        unsigned int l;
        int k;
        for (l = 0; !sp->data && l < sp->mips; ++l)
            tb += level_bytes(sp->fmt, sp->w >> l ? sp->w >> l : 1, sp->h >> l ? sp->h >> l : 1);
        for (k = -1; k < n; ++k)
        {
            IDirect3DTexture9 *tex;
            double t0, t1, t2, t3, t4, t5;
            if (sp->data) memcpy(archive, sp->data, fb);
            else scramble(archive, fb, (unsigned int)(i * 1000 + k + 7));
            settle(dev);
            t0 = now_ms();
            memcpy(file, archive, fb);
            t1 = now_ms();
            if (sp->data)
            {
                if (FAILED(d3dx_load(dev, file, (UINT)fb, 0, 0, sp->mips, 0, D3DFMT_UNKNOWN, D3DPOOL_MANAGED,
                        D3DX_DEFAULT_FILTER, 5 /* D3DX_FILTER_BOX */, 0, NULL, NULL, &tex)))
                { printf("FAIL D3DX load %s\n", sp->text); return 1; }
            }
            else
            {
                if (FAILED(IDirect3DDevice9_CreateTexture(dev, sp->w, sp->h, sp->mips, 0, sp->fmt, D3DPOOL_MANAGED, &tex, NULL)))
                { printf("FAIL CreateTexture %s\n", sp->text); return 1; }
                if (sp->tga) fill_tga(tex, sp, file); else fill_dds(tex, sp, file);
            }
            t2 = now_ms();
            if (sp->data && !tb)
                for (l = 0; l < IDirect3DTexture9_GetLevelCount(tex); ++l)
                {
                    D3DSURFACE_DESC d;
                    IDirect3DTexture9_GetLevelDesc(tex, l, &d);
                    tb += level_bytes(d.Format, d.Width, d.Height);
                }
            draw(dev, tex);
            t3 = now_ms();
            wait_gpu(dev);
            t4 = now_ms();
            draw(dev, tex);     /* the same frame again, the texture already on the GPU */
            wait_gpu(dev);
            t5 = now_ms();
            IDirect3DTexture9_Release(tex);
            if (k < 0) continue;    /* warm-up */
            load[k] = t1 - t0, fill[k] = t2 - t1, drw[k] = t3 - t2, sync[k] = t4 - t3, tot[k] = t4 - t0;
            steady[k] = t5 - t4, extra[k] = tot[k] - steady[k];
        }
        printf("%-22s %7.2f %7.2f | %17.2f %6.2f %6.2f %6.2f %7.2f %7.2f %7.2f\n", sp->text, fb / 1048576.0,
                tb / 1048576.0, median(load, n), median(fill, n), median(drw, n), median(sync, n), median(tot, n),
                median(steady, n), median(extra, n));
        fflush(stdout);
        free(archive);
        free(file);
    }
    IDirect3DDevice9_Release(dev);
    IDirect3D9_Release(d3d);
    DestroyWindow(wnd);
    return 0;
}
