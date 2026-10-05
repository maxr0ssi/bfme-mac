/* texbake - a TGA texture rewritten as a DDS holding exactly the texture the game builds from it, so the
 * game loads it without generating mipmaps on its thread (docs/PERFORMANCE.md, "First-use texture loads").
 *
 * The game loads every texture with one call (game.dat 0x53117e):
 *   D3DXCreateTextureFromFileInMemoryEx(dev, bytes, size, 0, 0, mips, 0, D3DFMT_UNKNOWN, D3DPOOL_MANAGED,
 *                                       D3DX_DEFAULT, D3DX_FILTER_BOX | skip << 26, 0, NULL, NULL, &tex)
 * For a TGA, d3dx9 decodes it and box-filters the whole mip chain on the game's thread: 30-170 ms for
 * our 1024-2048 normal maps and house-colour masks (tools/texupload.c). This tool makes that call with
 * the d3dx9_27 the game runs (the engine's builtin: WINEDLLOVERRIDES=d3dx9_27=b), reads every level of
 * the texture it built and writes them, in the format it chose, as an uncompressed DDS. It then loads
 * that DDS with the same call and compares format, size, level count and every byte of every level
 * with the TGA's texture: OK only when they are identical, so the game draws the same texels.
 * (Identical at the texture-reduction setting 0; with a reduction both still drop whole top levels.)
 *
 * Build: i686-w64-mingw32-gcc -O2 -o build/texbake.exe tools/texbake.c -ld3d9
 * Run:   wine build/texbake.exe <list>    each line of <list>: "<in.tga>|<out.dds>" (Windows paths)
 * Prints one line per texture: "OK <out> <format> <w>x<h> <levels>" or "FAIL <in> <why>"; exit 1 on any FAIL.
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

/* The game's call. */
static IDirect3DTexture9 *load(const BYTE *data, DWORD size)
{
    IDirect3DTexture9 *tex = NULL;
    if (FAILED(d3dx_load(dev, data, size, 0, 0, 0, 0, D3DFMT_UNKNOWN, D3DPOOL_MANAGED, 0xffffffffu, 5, 0,
            NULL, NULL, &tex)))
        return NULL;
    return tex;
}

static int bytes_per_pixel(D3DFORMAT f)
{
    return f == D3DFMT_A8R8G8B8 || f == D3DFMT_X8R8G8B8 ? 4 : 0;
}

/* Every level of tex, tightly packed, in one buffer (rows of w * 4 bytes). */
static BYTE *levels_of(IDirect3DTexture9 *tex, D3DFORMAT *fmt, UINT *w, UINT *h, DWORD *levels, DWORD *total)
{
    D3DSURFACE_DESC d;
    DWORD l, n = 0;
    BYTE *buf, *p;
    *levels = IDirect3DTexture9_GetLevelCount(tex);
    IDirect3DTexture9_GetLevelDesc(tex, 0, &d);
    *fmt = d.Format, *w = d.Width, *h = d.Height;
    if (!bytes_per_pixel(d.Format)) return NULL;
    for (l = 0; l < *levels; ++l)
    {
        IDirect3DTexture9_GetLevelDesc(tex, l, &d);
        n += d.Width * d.Height * 4;
    }
    p = buf = malloc(n);
    for (l = 0; l < *levels; ++l)
    {
        D3DLOCKED_RECT lr;
        UINT y;
        IDirect3DTexture9_GetLevelDesc(tex, l, &d);
        if (FAILED(IDirect3DTexture9_LockRect(tex, l, &lr, NULL, D3DLOCK_READONLY))) { free(buf); return NULL; }
        for (y = 0; y < d.Height; ++y, p += d.Width * 4)
            memcpy(p, (BYTE *)lr.pBits + y * lr.Pitch, d.Width * 4);
        IDirect3DTexture9_UnlockRect(tex, l);
    }
    *total = n;
    return buf;
}

static int write_dds(const char *path, D3DFORMAT fmt, UINT w, UINT h, DWORD levels, const BYTE *px, DWORD n)
{
    DWORD hd[32] = {0};
    FILE *f;
    hd[0] = 124;                                    /* dwSize */
    hd[1] = 0x1 | 0x2 | 0x4 | 0x8 | 0x1000 | (levels > 1 ? 0x20000 : 0);  /* CAPS HEIGHT WIDTH PITCH PIXELFORMAT MIPMAPCOUNT */
    hd[2] = h, hd[3] = w, hd[4] = w * 4, hd[6] = levels;
    hd[18] = 32;                                    /* DDS_PIXELFORMAT.dwSize */
    hd[19] = fmt == D3DFMT_A8R8G8B8 ? 0x41 : 0x40;  /* RGB (| ALPHAPIXELS) */
    hd[21] = 32, hd[22] = 0xff0000, hd[23] = 0xff00, hd[24] = 0xff;
    hd[25] = fmt == D3DFMT_A8R8G8B8 ? 0xff000000u : 0;
    hd[26] = 0x1000 | (levels > 1 ? 0x400008 : 0); /* TEXTURE (| COMPLEX MIPMAP) */
    if (!(f = fopen(path, "wb"))) return 0;
    fwrite("DDS ", 1, 4, f);
    fwrite(hd, 4, 31, f);
    fwrite(px, 1, n, f);
    return fclose(f) == 0;
}

static int bake(const char *in, const char *out)
{
    DWORD size, size2, levels, levels2, n, n2;
    D3DFORMAT fmt, fmt2;
    UINT w, h, w2, h2;
    BYTE *src = read_all(in, &size), *px, *px2, *dds;
    IDirect3DTexture9 *tex, *tex2;
    const char *why = NULL;

    if (!src) { printf("FAIL %s unreadable\n", in); return 0; }
    if (!(tex = load(src, size))) { printf("FAIL %s d3dx9 refused it\n", in); free(src); return 0; }
    px = levels_of(tex, &fmt, &w, &h, &levels, &n);
    IDirect3DTexture9_Release(tex);
    free(src);
    if (!px) { printf("FAIL %s format %#x is not A8R8G8B8/X8R8G8B8\n", in, (unsigned)fmt); return 0; }
    if (!write_dds(out, fmt, w, h, levels, px, n)) { printf("FAIL %s cannot write %s\n", in, out); free(px); return 0; }

    /* the check: the DDS through the same call gives the same texture */
    if (!(dds = read_all(out, &size2)) || !(tex2 = load(dds, size2))) why = "the DDS does not load";
    else
    {
        px2 = levels_of(tex2, &fmt2, &w2, &h2, &levels2, &n2);
        IDirect3DTexture9_Release(tex2);
        if (!px2) why = "the DDS loads in another format";
        else if (fmt2 != fmt || w2 != w || h2 != h || levels2 != levels || n2 != n) why = "the DDS loads at another size";
        else if (memcmp(px, px2, n)) why = "the DDS's texels differ";
        free(px2);
    }
    free(dds);
    free(px);
    if (why) { printf("FAIL %s %s\n", in, why); DeleteFileA(out); return 0; }
    printf("OK %s %s %ux%u %lu\n", out, fmt == D3DFMT_A8R8G8B8 ? "A8R8G8B8" : "X8R8G8B8", w, h, (unsigned long)levels);
    return 1;
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

    if (argc != 2 || !(list = fopen(argv[1], "r"))) { printf("usage: texbake <list of in.tga|out.dds>\n"); return 2; }
    if (!(m = LoadLibraryA("d3dx9_27.dll")) || !(d3dx_load = (CreateFromMemEx)GetProcAddress(m,
            "D3DXCreateTextureFromFileInMemoryEx")))
    { printf("FAIL no d3dx9_27\n"); return 2; }
    wnd = CreateWindowA("static", "texbake", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, 0, 0, 0, 0);
    if (!(d3d = Direct3DCreate9(D3D_SDK_VERSION))) { printf("FAIL Direct3DCreate9\n"); return 2; }
    pp.Windowed = TRUE;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD;
    pp.BackBufferWidth = 64;
    pp.BackBufferHeight = 64;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8;
    if (FAILED(IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, wnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev)))
    { printf("FAIL CreateDevice\n"); return 2; }
    while (fgets(line, sizeof(line), list))
    {
        char *bar = strchr(line, '|'), *end = line + strcspn(line, "\r\n");
        *end = 0;
        if (!bar) continue;
        *bar = 0;
        bad += !bake(line, bar + 1);
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
