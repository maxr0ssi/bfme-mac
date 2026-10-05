/* d3d9bench - synthetic Direct3D 9 load in the shape of EA's WW3D2 renderer (BFME2 / RotWK), for
 * comparing wined3d builds on this Mac without launching the game.
 *
 * Per frame, per object, it issues what WW3D2's DX8Wrapper::Draw -> Apply_Render_State_Changes
 * issues (dx8wrapper.cpp / dx8vertexbuffer.cpp / dx8indexbuffer.cpp in EA's Generals source):
 * shader-preset render and texture stage states (filtered against a cache like
 * Set_DX8_Render_State; --redundant N adds N unfiltered re-sets), SetTexture, SetMaterial,
 * SetTransform(WORLD) for every object (WW3D never filters it), stream source/indices/FVF or
 * declaration/shaders plus the per-object WVP and bone palette as VS constants, then
 * DrawIndexedPrimitive. Dynamic objects append to ONE shared 5000-vertex XYZNDUV2 vertex buffer
 * (DYNAMIC|WRITEONLY, POOL_DEFAULT) and a 5000-index buffer: each draw locks exactly its range,
 * NOSYSLOCK|NOOVERWRITE, or DISCARD when the offset is 0 (wrap, and the first lock of a frame).
 * Static meshes live in MANAGED buffers. Shaders are vs_1_1+ps_1_1 or vs_2_0+ps_2_0, hand-encoded.
 *
 * Build: i686-w64-mingw32-gcc -O2 -o build/d3d9bench.exe tools/d3d9bench.c -ld3d9
 *        (one file on purpose, so the build is that one line: allow-large-file)
 * Run:   scripts/bench-d3d9.sh <variant> [args]   (picks the wined3d.dll; see the README)
 * Args:  --secs N --warmup N --objects N --dyn-frac F --ffp-frac F --vs 11|20 --bones N
 *        --dyn-verts N --mesh-verts N --textures N --redundant N --clip N --order mix|grouped
 *        --phases 0|1 --crc [--bmp file.bmp] --expect-dll <path of the file that should be loaded>
 * UI work the game does besides WW3D's draws (all default 0; measured in the "ui" phase):
 *        --radar N    N one-pixel LockRect/UnlockRect of a 128x128 MANAGED texture per frame (the
 *                     radar draws its 2x2 blips a pixel at a time), then a quad drawn with it
 *        --text N     N times per frame: LockRect a 64x64 SYSTEMMEM texture, write "glyphs",
 *                     UnlockRect, UpdateTexture into a DEFAULT texture, draw a quad with it
 *        --relock N   N Lock(flags 0)/Unlock of 64-vertex ranges of a MANAGED vertex buffer, reading
 *                     the vertices and writing them back unchanged (checked: FAIL if they differ),
 *                     then one draw from it (WW3D's terrain and water buffers are relocked like that)
 *        --dyntex N   N DISCARD LockRect/UnlockRect of a 256x256 DYNAMIC texture per frame (video,
 *                     animated UI), each followed by a quad drawn with it
 *        --cpu-ms F   spin F ms per frame on the application thread before drawing: the game's own
 *                     work (~20 ms in a battle), which gives the render thread time to catch up
 *        --hitch N:MS[:sleep]  every Nth frame, MS ms more on the application thread (spinning, or
 *                     with :sleep waiting in Sleep); each prints "HITCH frame=.. unix_ms=.. ms=..",
 *                     the known answer for scripts/monitor.sh bench
 * Shader warm-up instead of the frame loop:
 *        --programs N N new vertex/pixel shader pairs, created up front followed by a 2 s pause (a
 *                     loading screen), then each drawn once and waited for with an event query:
 *                     the time wined3d needs to build each GL program at first use (the hitches)
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <x86intrin.h>

#define DYN_SIZE 5000                 /* DEFAULT_VB_SIZE / DEFAULT_IB_SIZE in WW3D2 */
#define FVF_DYN (D3DFVF_XYZ | D3DFVF_NORMAL | D3DFVF_DIFFUSE | D3DFVF_TEX2)   /* dynamic_fvf_type */
#define POSES 16
#define W 640
#define H 480

typedef struct { float x, y, z, nx, ny, nz; DWORD c; float u0, v0, u1, v1; } VtxDyn;   /* 44 bytes */
typedef struct { float x, y, z, nx, ny, nz, u, v, bone; } VtxSkin;                    /* 36 bytes */
typedef struct { float m[4][4]; } Mat;
enum { K_FFP, K_VS, K_DYN };
enum { P_LOCK, P_FILL, P_UNLOCK, P_STATE, P_DRAW, P_PRESENT, P_UI, P_CPU, P_N };

static struct {
    double secs, warmup, dyn_frac, ffp_frac;
    int objects, vs20, bones, dyn_verts, mesh_verts, textures, redundant, clip, grouped, phases, crc;
    const char *bmp, *expect;
    int radar, text, relock, dyntex;
    double cpu_ms;
    int programs;
    int hitch_every; double hitch_ms; int hitch_sleep;
} cfg = { 10, 2, 0.15, 0.5, 2000, 0, 24, 32, 256, 32, 2, 0, 0, 1, 0, NULL, NULL, 0, 0, 0, 0, 0, 0 };

static IDirect3DDevice9 *dev;
static IDirect3DVertexBuffer9 *dyn_vb, *mesh_vb[2];
static IDirect3DIndexBuffer9 *dyn_ib, *mesh_ib;
static IDirect3DTexture9 **tex;
static IDirect3DVertexShader9 *vs;
static IDirect3DPixelShader9 *ps;
static IDirect3DVertexDeclaration9 *skin_decl;
static IDirect3DTexture9 *radar_tex, *text_sys, *text_tex, *dyn_tex;
static IDirect3DVertexBuffer9 *relock_vb;
static unsigned int relock_sum;       /* checksum of relock_vb, for --relock */
static unsigned char *kinds;
static float (*poses)[4];             /* POSES palettes of bones*3 float4 registers */
static int mesh_nv, mesh_ntri, dyn_off_v, dyn_off_i, cols;
static unsigned long long ph[P_N], calls;
static Mat view, proj, viewproj;
static float sin_tab[256];           /* the bench's own math stays out of the timings (x87 under Rosetta) */

static void die(const char *what, HRESULT hr) { printf("FAIL %s: hr=%#lx\n", what, (unsigned long)hr); fflush(stdout); ExitProcess(1); }
#define CK(x) do { HRESULT hr_ = (x); if (FAILED(hr_)) die(#x, hr_); } while (0)
#define T0() unsigned long long t_ = cfg.phases ? __rdtsc() : 0
#define T1(p) do { if (cfg.phases) { unsigned long long n_ = __rdtsc(); ph[p] += n_ - t_; t_ = n_; } } while (0)

/* ---- math (row vectors, D3D convention) ---- */
static Mat mul(const Mat *a, const Mat *b)
{
    Mat r; int i, j;
    for (i = 0; i < 4; i++) for (j = 0; j < 4; j++)
        r.m[i][j] = a->m[i][0] * b->m[0][j] + a->m[i][1] * b->m[1][j] + a->m[i][2] * b->m[2][j] + a->m[i][3] * b->m[3][j];
    return r;
}
static Mat world_of(float x, float z, int ang)       /* ang in 1/256 turns */
{
    Mat r = {{{0}}}; float c = sin_tab[(ang + 64) & 255], n = sin_tab[ang & 255];
    r.m[0][0] = c; r.m[0][2] = -n; r.m[1][1] = 1; r.m[2][0] = n; r.m[2][2] = c;
    r.m[3][0] = x; r.m[3][2] = z; r.m[3][3] = 1;
    return r;
}
static void setup_camera(void)          /* LookAtLH from (0, .9L, -1.1L) to the origin, 57 degree FOV */
{
    float L = cols * 1.2f, ey = L * 0.9f, ez = -L * 1.1f, zl = sqrtf(ey * ey + ez * ez);
    float zy = -ey / zl, zz = -ez / zl, yy = zz, yz = -zy, f = 1.0f / tanf(0.5f), zn = 1, zf = L * 4;
    memset(&view, 0, sizeof(view)); memset(&proj, 0, sizeof(proj));
    view.m[0][0] = 1;                                    /* x axis (1,0,0); y = z cross x; z = view dir */
    view.m[1][1] = yy; view.m[1][2] = zy;
    view.m[2][1] = yz; view.m[2][2] = zz;
    view.m[3][1] = -(yy * ey + yz * ez); view.m[3][2] = -(zy * ey + zz * ez); view.m[3][3] = 1;
    proj.m[0][0] = f * H / W; proj.m[1][1] = f; proj.m[2][2] = zf / (zf - zn); proj.m[2][3] = 1;
    proj.m[3][2] = -zn * zf / (zf - zn);
    viewproj = mul(&view, &proj);
}

static int cmpd_(const void *a, const void *b) { double x = *(const double *)a, y = *(const double *)b; return (x > y) - (x < y); }

/* ---- hand-assembled shaders (D3D9 token format; SM2 opcodes carry an instruction length) ---- */
static DWORD sh[96]; static int shn, sm2;
#define DST(t, n, m) (0x80000000u | (((t) & 7u) << 28) | ((((t) >> 3) & 3u) << 11) | ((DWORD)(m) << 16) | (n))
#define SRC(t, n, s) (0x80000000u | (((t) & 7u) << 28) | ((((t) >> 3) & 3u) << 11) | ((DWORD)(s) << 16) | (n))
#define REL 0x2000u
enum { R_TEMP = 0, R_IN = 1, R_CONST = 2, R_ADDR = 3, R_TEX = 3, R_RAST = 4, R_ATTR = 5, R_TCOUT = 6, R_COLOROUT = 8, R_SAMP = 10 };
enum { XYZW = 0xe4, XXXX = 0x00, YYYY = 0x55, WWWW = 0xff };
static void ins(DWORD op, int n, DWORD a, DWORD b, DWORD c, DWORD d)
{
    DWORD t[4] = { a, b, c, d }; int i;
    sh[shn++] = op | (sm2 ? (DWORD)n << 24 : 0);
    for (i = 0; i < n; i++) sh[shn++] = t[i];
}
static void dcl(DWORD usage, int reg) { ins(0x1f, 2, 0x80000000u | usage, DST(R_IN, reg, 0xf), 0, 0); }
static void mat_rel(DWORD op, DWORD dst, DWORD src)     /* m4x3 / m3x3 dst, src, c16[a0.x] */
{
    if (sm2) ins(op, 4, dst, src, SRC(R_CONST, 16, XYZW) | REL, SRC(R_ADDR, 0, XXXX));
    else ins(op, 3, dst, src, SRC(R_CONST, 16, XYZW) | REL, 0);
}
/* Variant v of the bench's shaders: the same code plus one instruction reading constant 8 + v
 * (vertex shader) or c(v % 8) (pixel shader), so every pair is a new GL program. */
static void make_variant(int v, IDirect3DVertexShader9 **vsv, IDirect3DPixelShader9 **psv)
{
    sm2 = cfg.vs20; shn = 0;
    sh[shn++] = sm2 ? 0xfffe0200 : 0xfffe0101;
    dcl(0, 0); dcl(3, 1); dcl(5, 2); dcl(2, 3);
    ins(sm2 ? 0x2e : 0x01, 2, DST(R_ADDR, 0, 1), SRC(R_IN, 3, XXXX), 0, 0);
    mat_rel(0x15, DST(R_TEMP, 0, 7), SRC(R_IN, 0, XYZW));
    ins(0x01, 2, DST(R_TEMP, 0, 8), SRC(R_CONST, 7, YYYY), 0, 0);
    ins(0x14, 3, DST(R_RAST, 0, 0xf), SRC(R_TEMP, 0, XYZW), SRC(R_CONST, 0, XYZW), 0);
    ins(0x01, 2, DST(R_ATTR, 0, 0xf), SRC(R_CONST, 8 + v % 80, XYZW), 0, 0);             /* mov oD0, c[8+v] */
    ins(0x02, 3, DST(R_TCOUT, 0, 3), SRC(R_IN, 2, XYZW), SRC(R_CONST, 88 + v / 80 % 8, XYZW), 0); /* add oT0.xy */
    sh[shn++] = 0xffff;
    CK(IDirect3DDevice9_CreateVertexShader(dev, sh, vsv));
    shn = 0;
    sh[shn++] = 0xffff0101;
    ins(0x42, 1, DST(R_TEX, 0, 0xf), 0, 0, 0);
    ins(0x05, 3, DST(R_TEMP, 0, 0xf), SRC(R_TEX, 0, XYZW), SRC(R_IN, 0, XYZW), 0);
    ins(0x02, 3, DST(R_TEMP, 0, 0xf), SRC(R_TEMP, 0, XYZW), SRC(R_CONST, v % 8, XYZW), 0);  /* add r0, c(v%8) */
    sh[shn++] = 0xffff;
    CK(IDirect3DDevice9_CreatePixelShader(dev, sh, psv));
}
static int program_warmup(void)
{
    IDirect3DQuery9 *q; LARGE_INTEGER f, a, b; double *t = calloc(cfg.programs, sizeof(*t)), sum = 0; int i;
    IDirect3DVertexShader9 **vsv = calloc(cfg.programs, sizeof(*vsv)); IDirect3DPixelShader9 **psv = calloc(cfg.programs, sizeof(*psv));
    CK(IDirect3DDevice9_CreateQuery(dev, D3DQUERYTYPE_EVENT, &q));
    for (i = 0; i < cfg.programs; i++) make_variant(i, &vsv[i], &psv[i]);   /* the game loads its shaders */
    Sleep(2000);
    QueryPerformanceFrequency(&f);
    CK(IDirect3DDevice9_BeginScene(dev));
    IDirect3DDevice9_SetVertexDeclaration(dev, skin_decl);
    IDirect3DDevice9_SetStreamSource(dev, 0, mesh_vb[1], 0, sizeof(VtxSkin));
    IDirect3DDevice9_SetIndices(dev, mesh_ib);
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)tex[0]);
    for (i = 0; i < cfg.programs; i++)
    {
        IDirect3DDevice9_SetVertexShader(dev, vsv[i]); IDirect3DDevice9_SetPixelShader(dev, psv[i]);
        IDirect3DQuery9_Issue(q, D3DISSUE_END);
        while (IDirect3DQuery9_GetData(q, NULL, 0, D3DGETDATA_FLUSH) == S_FALSE) ;
        QueryPerformanceCounter(&a);
        CK(IDirect3DDevice9_DrawIndexedPrimitive(dev, D3DPT_TRIANGLELIST, 0, 0, mesh_nv, 0, 2));
        IDirect3DQuery9_Issue(q, D3DISSUE_END);
        while (IDirect3DQuery9_GetData(q, NULL, 0, D3DGETDATA_FLUSH) == S_FALSE) ;
        QueryPerformanceCounter(&b);
        sum += t[i] = (b.QuadPart - a.QuadPart) * 1000.0 / f.QuadPart;
    }
    IDirect3DDevice9_SetVertexShader(dev, NULL); IDirect3DDevice9_SetPixelShader(dev, NULL);
    for (i = 0; i < cfg.programs; i++) { IDirect3DVertexShader9_Release(vsv[i]); IDirect3DPixelShader9_Release(psv[i]); }
    CK(IDirect3DDevice9_EndScene(dev));
    IDirect3DQuery9_Release(q);
    qsort(t, cfg.programs, sizeof(*t), cmpd_);
    printf("PROGRAMS n=%d mean=%.3f p50=%.3f p95=%.3f max=%.3f ms per new program (first %.3f ms)\n", cfg.programs,
           sum / cfg.programs, t[cfg.programs / 2], t[(int)(cfg.programs * 0.95)], t[cfg.programs - 1], t[0]);
    return 0;
}

static void make_shaders(void)
{
    /* c0-c3 WVP^T, c4 light dir, c5 diffuse, c6 ambient, c7 (0,1,0,0), c16.. bones (3 regs each) */
    sm2 = cfg.vs20; shn = 0;
    sh[shn++] = sm2 ? 0xfffe0200 : 0xfffe0101;
    dcl(0, 0); dcl(3, 1); dcl(5, 2); dcl(2, 3);            /* position, normal, texcoord, blendindices */
    ins(sm2 ? 0x2e : 0x01, 2, DST(R_ADDR, 0, 1), SRC(R_IN, 3, XXXX), 0, 0);    /* mova/mov a0.x, v3.x */
    mat_rel(0x15, DST(R_TEMP, 0, 7), SRC(R_IN, 0, XYZW));                      /* m4x3 r0.xyz, v0, c16[a0] */
    ins(0x01, 2, DST(R_TEMP, 0, 8), SRC(R_CONST, 7, YYYY), 0, 0);              /* mov r0.w, c7.y */
    ins(0x14, 3, DST(R_RAST, 0, 0xf), SRC(R_TEMP, 0, XYZW), SRC(R_CONST, 0, XYZW), 0);   /* m4x4 oPos */
    mat_rel(0x17, DST(R_TEMP, 1, 7), SRC(R_IN, 1, XYZW));                      /* m3x3 r1.xyz, v1, c16[a0] */
    ins(0x08, 3, DST(R_TEMP, 1, 8), SRC(R_TEMP, 1, XYZW), SRC(R_CONST, 4, XYZW), 0);     /* dp3 r1.w */
    ins(0x0b, 3, DST(R_TEMP, 1, 8), SRC(R_TEMP, 1, WWWW), SRC(R_CONST, 7, XXXX), 0);     /* max */
    ins(0x04, 4, DST(R_ATTR, 0, 0xf), SRC(R_TEMP, 1, WWWW), SRC(R_CONST, 5, XYZW), SRC(R_CONST, 6, XYZW)); /* mad oD0 */
    ins(0x01, 2, DST(R_TCOUT, 0, 3), SRC(R_IN, 2, XYZW), 0, 0);                /* mov oT0.xy, v2 */
    sh[shn++] = 0xffff;
    CK(IDirect3DDevice9_CreateVertexShader(dev, sh, &vs));
    shn = 0;
    if (sm2)
    {
        sh[shn++] = 0xffff0200;
        ins(0x1f, 2, 0x80000000u, DST(R_TEX, 0, 3), 0, 0);                     /* dcl t0.xy */
        ins(0x1f, 2, 0x80000000u, DST(R_IN, 0, 0xf), 0, 0);                    /* dcl v0 */
        ins(0x1f, 2, 0x90000000u, DST(R_SAMP, 0, 0xf), 0, 0);                  /* dcl_2d s0 */
        ins(0x42, 3, DST(R_TEMP, 0, 0xf), SRC(R_TEX, 0, XYZW), SRC(R_SAMP, 0, XYZW), 0);  /* texld */
        ins(0x05, 3, DST(R_TEMP, 0, 0xf), SRC(R_TEMP, 0, XYZW), SRC(R_IN, 0, XYZW), 0);   /* mul */
        ins(0x01, 2, DST(R_COLOROUT, 0, 0xf), SRC(R_TEMP, 0, XYZW), 0, 0);                /* mov oC0 */
    }
    else
    {
        sh[shn++] = 0xffff0101;
        ins(0x42, 1, DST(R_TEX, 0, 0xf), 0, 0, 0);                                        /* tex t0 */
        ins(0x05, 3, DST(R_TEMP, 0, 0xf), SRC(R_TEX, 0, XYZW), SRC(R_IN, 0, XYZW), 0);    /* mul r0 */
    }
    sh[shn++] = 0xffff;
    CK(IDirect3DDevice9_CreatePixelShader(dev, sh, &ps));
}

/* ---- WW3D2-style state cache: only changes reach the device, like Set_DX8_Render_State ---- */
static DWORD rs_cache[256], tss_cache[8][33];
static void *cur_tex, *cur_mat_p, *cur_vb;
static int cur_kind = -1;
static void rs(D3DRENDERSTATETYPE s, DWORD v)
{
    if (rs_cache[s] == v) return;
    rs_cache[s] = v; calls++;
    IDirect3DDevice9_SetRenderState(dev, s, v);
}
static void tss(DWORD st, D3DTEXTURESTAGESTATETYPE s, DWORD v)
{
    if (tss_cache[st][s] == v) return;
    tss_cache[st][s] = v; calls++;
    IDirect3DDevice9_SetTextureStageState(dev, st, s, v);
}
static void redundant(int i)          /* re-set states to the values they already have */
{
    int r;
    for (r = 0; r < cfg.redundant; r++, calls++)
        switch ((i + r) % 3)
        {
        case 0: IDirect3DDevice9_SetRenderState(dev, D3DRS_ZENABLE, rs_cache[D3DRS_ZENABLE]); break;
        case 1: IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLOROP, tss_cache[0][D3DTSS_COLOROP]); break;
        default: IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAGFILTER, D3DTEXF_LINEAR); break;
        }
}
static void shader_preset(int p)      /* ShaderClass::Apply: opaque, alpha test, blend, additive */
{
    rs(D3DRS_ALPHABLENDENABLE, p >= 2);
    rs(D3DRS_SRCBLEND, p == 3 ? D3DBLEND_ONE : D3DBLEND_SRCALPHA);
    rs(D3DRS_DESTBLEND, p == 3 ? D3DBLEND_ONE : D3DBLEND_INVSRCALPHA);
    rs(D3DRS_ALPHATESTENABLE, p == 1);
    rs(D3DRS_ZWRITEENABLE, p < 2);
    rs(D3DRS_CULLMODE, p == 3 ? D3DCULL_NONE : D3DCULL_CCW);
    tss(0, D3DTSS_COLOROP, D3DTOP_MODULATE);
    tss(0, D3DTSS_ALPHAOP, p == 3 ? D3DTOP_SELECTARG2 : D3DTOP_MODULATE);
    tss(1, D3DTSS_COLOROP, D3DTOP_DISABLE);
}

/* ---- resources ---- */
static void make_textures(void)
{
    int k, l, x, y;
    tex = calloc(cfg.textures, sizeof(*tex));
    for (k = 0; k < cfg.textures; k++)
    {
        DWORD col = 0x404040u | ((k * 0x9e3779b9u) & 0xbfbfbfu);
        CK(IDirect3DDevice9_CreateTexture(dev, 64, 64, 0, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &tex[k], NULL));
        for (l = 0; l < (int)IDirect3DTexture9_GetLevelCount(tex[k]); l++)
        {
            D3DLOCKED_RECT lr; int sz = 64 >> l;
            CK(IDirect3DTexture9_LockRect(tex[k], l, &lr, NULL, 0));
            for (y = 0; y < sz; y++) for (x = 0; x < sz; x++)
            {
                DWORD a = (DWORD)(255 * (x + y) / (2 * sz)) << 24;
                ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = a | ((((x << l) ^ (y << l)) & 8) ? col : 0xe0e0e0u);
            }
            IDirect3DTexture9_UnlockRect(tex[k], l);
        }
    }
}
static void make_meshes(void)
{
    static const D3DVERTEXELEMENT9 el[] = {
        { 0, 0, D3DDECLTYPE_FLOAT3, 0, D3DDECLUSAGE_POSITION, 0 }, { 0, 12, D3DDECLTYPE_FLOAT3, 0, D3DDECLUSAGE_NORMAL, 0 },
        { 0, 24, D3DDECLTYPE_FLOAT2, 0, D3DDECLUSAGE_TEXCOORD, 0 }, { 0, 32, D3DDECLTYPE_FLOAT1, 0, D3DDECLUSAGE_BLENDINDICES, 0 },
        D3DDECL_END() };
    int n = (int)sqrtf((float)cfg.mesh_verts) - 1, r, s, p, b, k;
    VtxDyn *vd; VtxSkin *vk; WORD *ix;
    if (n < 3) n = 3;
    mesh_nv = (n + 1) * (n + 1); mesh_ntri = n * n * 2;
    CK(IDirect3DDevice9_CreateVertexBuffer(dev, mesh_nv * sizeof(VtxDyn), D3DUSAGE_WRITEONLY, FVF_DYN, D3DPOOL_MANAGED, &mesh_vb[0], NULL));
    CK(IDirect3DDevice9_CreateVertexBuffer(dev, mesh_nv * sizeof(VtxSkin), D3DUSAGE_WRITEONLY, 0, D3DPOOL_MANAGED, &mesh_vb[1], NULL));
    CK(IDirect3DDevice9_CreateIndexBuffer(dev, mesh_ntri * 6, D3DUSAGE_WRITEONLY, D3DFMT_INDEX16, D3DPOOL_MANAGED, &mesh_ib, NULL));
    CK(IDirect3DVertexBuffer9_Lock(mesh_vb[0], 0, 0, (void **)&vd, 0));
    CK(IDirect3DVertexBuffer9_Lock(mesh_vb[1], 0, 0, (void **)&vk, 0));
    for (r = 0; r <= n; r++) for (s = 0; s <= n; s++)
    {
        float ph = 3.14159265f * r / n, th = 6.2831853f * s / n;
        float x = sinf(ph) * cosf(th), y = cosf(ph), z = sinf(ph) * sinf(th);
        VtxDyn d = { x * 0.8f, y * 0.8f + 0.8f, z * 0.8f, x, y, z, 0xffffffffu, (float)s / n, (float)r / n, 0, 0 };
        VtxSkin k2 = { d.x, d.y, d.z, x, y, z, d.u0, d.v0, (float)(3 * (r * cfg.bones / (n + 1))) };
        *vd++ = d; *vk++ = k2;
    }
    IDirect3DVertexBuffer9_Unlock(mesh_vb[0]); IDirect3DVertexBuffer9_Unlock(mesh_vb[1]);
    CK(IDirect3DIndexBuffer9_Lock(mesh_ib, 0, 0, (void **)&ix, 0));
    for (r = 0; r < n; r++) for (s = 0; s < n; s++)
    {
        WORD a = r * (n + 1) + s, c = a + n + 1;
        *ix++ = a; *ix++ = a + 1; *ix++ = c; *ix++ = a + 1; *ix++ = c + 1; *ix++ = c;
    }
    IDirect3DIndexBuffer9_Unlock(mesh_ib);
    CK(IDirect3DDevice9_CreateVertexDeclaration(dev, el, &skin_decl));
    /* bone palettes: POSES precomputed poses, a sway around y that grows up the mesh */
    poses = calloc(POSES * cfg.bones * 3, sizeof(*poses));
    for (p = 0; p < POSES; p++) for (b = 0; b < cfg.bones; b++)
    {
        float a = sinf(p * 0.39f + b * 0.3f) * 0.25f * b / cfg.bones, c = cosf(a), sn = sinf(a);
        float (*reg)[4] = poses + (p * cfg.bones + b) * 3, t[3][4] = { { c, 0, sn, 0 }, { 0, 1, 0, 0 }, { -sn, 0, c, 0 } };
        for (k = 0; k < 3; k++) memcpy(reg[k], t[k], sizeof(t[k]));   /* rows of the transposed 4x3 */
    }
    /* the shared dynamic buffers (DX8VertexBufferClass / DX8IndexBufferClass with USAGE_DYNAMIC) */
    CK(IDirect3DDevice9_CreateVertexBuffer(dev, DYN_SIZE * sizeof(VtxDyn), D3DUSAGE_DYNAMIC | D3DUSAGE_WRITEONLY, FVF_DYN, D3DPOOL_DEFAULT, &dyn_vb, NULL));
    CK(IDirect3DDevice9_CreateIndexBuffer(dev, DYN_SIZE * 2, D3DUSAGE_DYNAMIC | D3DUSAGE_WRITEONLY, D3DFMT_INDEX16, D3DPOOL_DEFAULT, &dyn_ib, NULL));
}

/* ---- one frame ---- */
static void draw_dynamic(int i, float ox, float oz, int frame, unsigned long long t_)
{
    int nv = cfg.dyn_verts, ni = nv / 4 * 6, q;
    DWORD c = 0x80000000u | ((i * 0x51f15e) & 0xffffffu) | 0x303030u;
    VtxDyn *v; WORD *ix;
    if (dyn_off_v + nv > DYN_SIZE) dyn_off_v = 0;          /* Allocate_DX8_Dynamic_Buffer: wrap */
    if (dyn_off_i + ni > DYN_SIZE) dyn_off_i = 0;
    calls += 5;
    CK(IDirect3DVertexBuffer9_Lock(dyn_vb, dyn_off_v * sizeof(VtxDyn), nv * sizeof(VtxDyn), (void **)&v,
            D3DLOCK_NOSYSLOCK | (dyn_off_v ? D3DLOCK_NOOVERWRITE : D3DLOCK_DISCARD)));
    T1(P_LOCK);
    for (q = 0; q < nv / 4; q++, v += 4)    /* camera-facing quads rising through the object */
    {
        float cx = ox + ((q * 37) % 11 - 5) * 0.12f, cy = 0.3f + ((frame * 23 + q * 13 + i) % 200) * 0.01f, cz = oz + ((q * 53) % 7 - 3) * 0.12f;
        VtxDyn a = { cx - 0.15f, cy - 0.15f, cz, 0, 0, -1, c, 0, 1, 0, 0 };
        v[0] = a; v[1] = a; v[1].x += 0.3f; v[1].u0 = 1;
        v[2] = a; v[2].y += 0.3f; v[2].v0 = 0; v[3] = v[1]; v[3].y += 0.3f; v[3].v0 = 0;
    }
    T1(P_FILL);
    CK(IDirect3DVertexBuffer9_Unlock(dyn_vb));
    T1(P_UNLOCK);
    CK(IDirect3DIndexBuffer9_Lock(dyn_ib, dyn_off_i * 2, ni * 2, (void **)&ix, dyn_off_i ? D3DLOCK_NOOVERWRITE : D3DLOCK_DISCARD));
    T1(P_LOCK);
    for (q = 0; q < nv / 4; q++, ix += 6)
    {
        ix[0] = q * 4; ix[1] = q * 4 + 1; ix[2] = q * 4 + 2; ix[3] = q * 4 + 2; ix[4] = q * 4 + 1; ix[5] = q * 4 + 3;
    }
    T1(P_FILL);
    CK(IDirect3DIndexBuffer9_Unlock(dyn_ib));
    T1(P_UNLOCK);
    CK(IDirect3DDevice9_DrawIndexedPrimitive(dev, D3DPT_TRIANGLELIST, dyn_off_v, 0, nv, dyn_off_i, nv / 2));
    T1(P_DRAW);
    dyn_off_v += nv; dyn_off_i += ni;
}
static void draw_object(int i, int frame)
{
    static D3DMATERIAL9 mats[4];
    float ox = (i % cols - cols / 2) * 2.0f, oz = (i / cols - cols / 2) * 2.0f;
    int kind = kinds[i], preset = kind == K_DYN ? 3 - (i & 1) : (i % 4 == 3), k;
    IDirect3DTexture9 *tx = tex[(i * 7) % cfg.textures];
    Mat w = kind == K_DYN ? world_of(0, 0, 0) : world_of(ox, oz, frame * 2 + i * 41);   /* particles: world space */
    T0();
    if (!mats[0].Diffuse.a)
        for (k = 0; k < 4; k++)
        {
            mats[k].Diffuse.r = 0.6f + 0.1f * k; mats[k].Diffuse.g = 0.8f; mats[k].Diffuse.b = 0.9f - 0.1f * k;
            mats[k].Diffuse.a = mats[k].Ambient.a = 1; mats[k].Ambient.r = mats[k].Ambient.g = mats[k].Ambient.b = 0.3f;
        }
    shader_preset(preset);
    if (tx != cur_tex) { cur_tex = tx; calls++; IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)tx); }
    redundant(i);
    if (kind != K_VS) rs(D3DRS_LIGHTING, kind == K_FFP);
    if (kind == K_FFP && cur_mat_p != &mats[i & 3])
        { cur_mat_p = &mats[i & 3]; calls++; IDirect3DDevice9_SetMaterial(dev, &mats[i & 3]); }
    calls++;
    IDirect3DDevice9_SetTransform(dev, D3DTS_WORLD, (D3DMATRIX *)&w);      /* every object, unfiltered */
    if (kind != cur_kind)
    {
        calls += 3;
        if (kind == K_VS)
        {
            IDirect3DDevice9_SetVertexDeclaration(dev, skin_decl);
            IDirect3DDevice9_SetVertexShader(dev, vs); IDirect3DDevice9_SetPixelShader(dev, ps);
        }
        else if (cur_kind == K_VS || cur_kind < 0)
        {
            IDirect3DDevice9_SetVertexShader(dev, NULL); IDirect3DDevice9_SetPixelShader(dev, NULL);
            IDirect3DDevice9_SetFVF(dev, FVF_DYN);
        }
        cur_kind = kind;
    }
    {
        void *vb = kind == K_DYN ? (void *)dyn_vb : (void *)mesh_vb[kind == K_VS];
        if (vb != cur_vb)
        {
            cur_vb = vb; calls += 2;
            IDirect3DDevice9_SetStreamSource(dev, 0, vb, 0, kind == K_VS ? sizeof(VtxSkin) : sizeof(VtxDyn));
            IDirect3DDevice9_SetIndices(dev, kind == K_DYN ? dyn_ib : mesh_ib);
        }
    }
    if (kind == K_VS)
    {
        Mat m = mul(&w, &viewproj), tr; int a, b;
        for (a = 0; a < 4; a++) for (b = 0; b < 4; b++) tr.m[a][b] = m.m[b][a];
        calls += 2;
        IDirect3DDevice9_SetVertexShaderConstantF(dev, 0, &tr.m[0][0], 4);
        IDirect3DDevice9_SetVertexShaderConstantF(dev, 16, poses[((i + frame) % POSES) * cfg.bones * 3], cfg.bones * 3);
    }
    T1(P_STATE);
    if (kind == K_DYN) { draw_dynamic(i, ox, oz, frame, t_); return; }
    calls++;
    CK(IDirect3DDevice9_DrawIndexedPrimitive(dev, D3DPT_TRIANGLELIST, 0, 0, mesh_nv, 0, mesh_ntri));
    T1(P_DRAW);
}

/* ---- UI: radar pixel locks, text surfaces, managed buffer relocks ---- */
typedef struct { float x, y, z, rhw, u, v; } VtxUi;
static unsigned int sum32(const void *p, size_t n)
{
    const BYTE *b = p; unsigned int h = 2166136261u;
    while (n--) h = (h ^ *b++) * 16777619u;
    return h;
}
static void make_ui(void)
{
    D3DLOCKED_RECT lr; int y;
    if (cfg.radar)
    {
        CK(IDirect3DDevice9_CreateTexture(dev, 128, 128, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &radar_tex, NULL));
        CK(IDirect3DTexture9_LockRect(radar_tex, 0, &lr, NULL, 0));
        for (y = 0; y < 128; y++) memset((BYTE *)lr.pBits + y * lr.Pitch, 0x20, 128 * 4);
        IDirect3DTexture9_UnlockRect(radar_tex, 0);
    }
    if (cfg.dyntex)
        CK(IDirect3DDevice9_CreateTexture(dev, 256, 256, 1, D3DUSAGE_DYNAMIC, D3DFMT_A8R8G8B8, D3DPOOL_DEFAULT, &dyn_tex, NULL));
    if (cfg.text)
    {
        CK(IDirect3DDevice9_CreateTexture(dev, 64, 64, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_SYSTEMMEM, &text_sys, NULL));
        CK(IDirect3DDevice9_CreateTexture(dev, 64, 64, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_DEFAULT, &text_tex, NULL));
    }
    if (cfg.relock)
    {
        void *p, *q;
        CK(IDirect3DDevice9_CreateVertexBuffer(dev, mesh_nv * sizeof(VtxDyn), D3DUSAGE_WRITEONLY, FVF_DYN, D3DPOOL_MANAGED, &relock_vb, NULL));
        CK(IDirect3DVertexBuffer9_Lock(mesh_vb[0], 0, 0, &p, D3DLOCK_READONLY));
        CK(IDirect3DVertexBuffer9_Lock(relock_vb, 0, 0, &q, 0));
        memcpy(q, p, mesh_nv * sizeof(VtxDyn));
        relock_sum = sum32(q, mesh_nv * sizeof(VtxDyn));
        IDirect3DVertexBuffer9_Unlock(relock_vb);
        IDirect3DVertexBuffer9_Unlock(mesh_vb[0]);
    }
}
static void ui_quad(IDirect3DTexture9 *t, float x, float y, float sz)
{
    VtxUi q[4] = { { x, y, 0, 1, 0, 0 }, { x + sz, y, 0, 1, 1, 0 }, { x, y + sz, 0, 1, 0, 1 }, { x + sz, y + sz, 0, 1, 1, 1 } };
    calls += 2;
    IDirect3DDevice9_SetTexture(dev, 0, (IDirect3DBaseTexture9 *)t);
    CK(IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, q, sizeof(*q)));
}
static void draw_ui(int frame)
{
    D3DLOCKED_RECT lr; int i, x, y;
    T0();
    if (!cfg.radar && !cfg.text && !cfg.relock && !cfg.dyntex) return;
    for (i = 0; i < cfg.relock; i++)                    /* WW3D's managed buffers, relocked with flags 0 */
    {
        int n = mesh_nv < 64 ? mesh_nv : 64, off = (i * 61 + frame * 7) % (mesh_nv - n + 1);
        VtxDyn *v, tmp[64];
        CK(IDirect3DVertexBuffer9_Lock(relock_vb, off * sizeof(VtxDyn), n * sizeof(VtxDyn), (void **)&v, 0));
        memcpy(tmp, v, n * sizeof(VtxDyn)); memcpy(v, tmp, n * sizeof(VtxDyn));
        CK(IDirect3DVertexBuffer9_Unlock(relock_vb));
    }
    if (cfg.relock && !(frame & 63))                     /* the data must still be what was created */
    {
        void *p; unsigned int h;
        CK(IDirect3DVertexBuffer9_Lock(relock_vb, 0, 0, &p, D3DLOCK_READONLY));
        h = sum32(p, mesh_nv * sizeof(VtxDyn));
        IDirect3DVertexBuffer9_Unlock(relock_vb);
        if (h != relock_sum) { printf("FAIL relock: managed vertex buffer contents changed\n"); ExitProcess(4); }
    }
    if (cfg.relock)                                      /* drawn as a static FFP mesh at the origin */
    {
        Mat w = world_of(0, 0, 0);
        calls += 6;
        IDirect3DDevice9_SetVertexShader(dev, NULL); IDirect3DDevice9_SetPixelShader(dev, NULL);
        IDirect3DDevice9_SetFVF(dev, FVF_DYN);
        IDirect3DDevice9_SetTransform(dev, D3DTS_WORLD, (D3DMATRIX *)&w);
        IDirect3DDevice9_SetStreamSource(dev, 0, relock_vb, 0, sizeof(VtxDyn));
        IDirect3DDevice9_SetIndices(dev, mesh_ib);
        CK(IDirect3DDevice9_DrawIndexedPrimitive(dev, D3DPT_TRIANGLELIST, 0, 0, mesh_nv, 0, mesh_ntri));
    }
    calls += 12;
    IDirect3DDevice9_SetVertexShader(dev, NULL); IDirect3DDevice9_SetPixelShader(dev, NULL);
    IDirect3DDevice9_SetFVF(dev, D3DFVF_XYZRHW | D3DFVF_TEX1);
    rs(D3DRS_ZENABLE, D3DZB_FALSE); rs(D3DRS_ALPHABLENDENABLE, FALSE); rs(D3DRS_ALPHATESTENABLE, FALSE);
    rs(D3DRS_CULLMODE, D3DCULL_NONE); rs(D3DRS_LIGHTING, FALSE);
    tss(0, D3DTSS_COLOROP, D3DTOP_SELECTARG1); tss(0, D3DTSS_COLORARG1, D3DTA_TEXTURE);
    tss(0, D3DTSS_ALPHAOP, D3DTOP_SELECTARG1); tss(0, D3DTSS_ALPHAARG1, D3DTA_TEXTURE); tss(1, D3DTSS_COLOROP, D3DTOP_DISABLE);
    if (cfg.radar)
    {
        for (i = 0; i < cfg.radar; i++)                  /* 2x2 blips, one pixel per lock */
        {
            RECT r; int b = i / 4, px = (b * 37 + frame * 3) % 126 + (i & 1), py = (b * 53 + frame) % 126 + ((i >> 1) & 1);
            SetRect(&r, px, py, px + 1, py + 1);
            CK(IDirect3DTexture9_LockRect(radar_tex, 0, &lr, &r, 0));
            *(DWORD *)lr.pBits = 0xff000000u | ((b * 0x3571f) & 0xffffff) | 0x404040u;
            CK(IDirect3DTexture9_UnlockRect(radar_tex, 0));
        }
        ui_quad(radar_tex, W - 136, 8, 128);
    }
    for (i = 0; i < cfg.text; i++)                       /* one string at a time through a sysmem surface */
    {
        CK(IDirect3DTexture9_LockRect(text_sys, 0, &lr, NULL, D3DLOCK_NOSYSLOCK));
        for (y = 0; y < 64; y++)
            for (x = 0; x < 64; x++)
                ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = (((x / 6 + i + frame) ^ (y / 8)) & 1) ? 0xffffffffu : 0xff000000u | (i * 0x2a1f3);
        CK(IDirect3DTexture9_UnlockRect(text_sys, 0));
        CK(IDirect3DDevice9_UpdateTexture(dev, (IDirect3DBaseTexture9 *)text_sys, (IDirect3DBaseTexture9 *)text_tex));
        ui_quad(text_tex, 8 + (i % 8) * 20, 8 + (i / 8 % 20) * 20, 16);
    }
    for (i = 0; i < cfg.dyntex; i++)                     /* a video frame or animated panel */
    {
        CK(IDirect3DTexture9_LockRect(dyn_tex, 0, &lr, NULL, D3DLOCK_DISCARD));
        for (y = 0; y < 256; y++)
        {
            DWORD *row = (DWORD *)((BYTE *)lr.pBits + y * lr.Pitch), c = 0xff000000u | ((y + i * 16 + frame) & 255) << 8 | (i * 40 & 255);
            for (x = 0; x < 256; x++) row[x] = c | (x << 16);
        }
        CK(IDirect3DTexture9_UnlockRect(dyn_tex, 0));
        ui_quad(dyn_tex, W - 136 - (i % 4) * 70, H - 72 - (i / 4 % 6) * 70, 64);
    }
    rs(D3DRS_ZENABLE, D3DZB_TRUE);
    cur_kind = -1; cur_tex = cur_vb = NULL; calls++;
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    T1(P_UI);
}

static void begin_frame(int frame)
{
    static const float c4[4] = { 0.4f, 0.8f, -0.45f, 0 }, c5[4] = { 0.8f, 0.75f, 0.7f, 1 }, c6[4] = { 0.25f, 0.25f, 0.3f, 1 }, c7[4] = { 0, 1, 0, 0 };
    D3DLIGHT9 l = { D3DLIGHT_DIRECTIONAL };
    MSG msg; int i;
    T0();
    if (cfg.cpu_ms > 0)                           /* the game's own work: no D3D calls */
    {
        LARGE_INTEGER f, a, b;
        QueryPerformanceFrequency(&f); QueryPerformanceCounter(&a);
        do QueryPerformanceCounter(&b); while ((b.QuadPart - a.QuadPart) * 1000.0 < cfg.cpu_ms * f.QuadPart);
        T1(P_CPU);
    }
    if (cfg.hitch_every > 0 && frame > 0 && frame % cfg.hitch_every == 0)
    {
        LARGE_INTEGER f, a, b; FILETIME ft;
        GetSystemTimeAsFileTime(&ft);
        QueryPerformanceFrequency(&f); QueryPerformanceCounter(&a);
        if (cfg.hitch_sleep) Sleep((DWORD)cfg.hitch_ms);
        else do QueryPerformanceCounter(&b); while ((b.QuadPart - a.QuadPart) * 1000.0 < cfg.hitch_ms * f.QuadPart);
        printf("HITCH frame=%d unix_ms=%llu ms=%.0f %s\n", frame,
               ((unsigned long long)ft.dwHighDateTime << 32 | ft.dwLowDateTime) / 10000 - 11644473600000ull,
               cfg.hitch_ms, cfg.hitch_sleep ? "sleep" : "spin");
    }
    while (PeekMessageA(&msg, NULL, 0, 0, PM_REMOVE)) { TranslateMessage(&msg); DispatchMessageA(&msg); }
    dyn_off_v = dyn_off_i = 0;                    /* DynamicVBAccessClass::_Reset(frame_changed) */
    CK(IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, 0xff203040, 1.0f, 0));
    CK(IDirect3DDevice9_BeginScene(dev));
    IDirect3DDevice9_SetTransform(dev, D3DTS_VIEW, (D3DMATRIX *)&view);
    IDirect3DDevice9_SetTransform(dev, D3DTS_PROJECTION, (D3DMATRIX *)&proj);
    l.Diffuse.r = l.Diffuse.g = l.Diffuse.b = 0.9f; l.Direction.x = -0.4f; l.Direction.y = -0.8f; l.Direction.z = 0.45f;
    IDirect3DDevice9_SetLight(dev, 0, &l); IDirect3DDevice9_LightEnable(dev, 0, TRUE);
    IDirect3DDevice9_SetVertexShaderConstantF(dev, 4, c4, 1); IDirect3DDevice9_SetVertexShaderConstantF(dev, 5, c5, 1);
    IDirect3DDevice9_SetVertexShaderConstantF(dev, 6, c6, 1); IDirect3DDevice9_SetVertexShaderConstantF(dev, 7, c7, 1);
    calls += 10;
    T1(P_PRESENT);
    for (i = 0; i < cfg.objects; i++) draw_object(i, frame);
}
static void end_frame(int frame)
{
    draw_ui(frame);
    {
    T0();
    CK(IDirect3DDevice9_EndScene(dev));
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);   /* WW3D ignores Present's result too */
    /* End_Scene: release the buffers and textures every frame */
    IDirect3DDevice9_SetStreamSource(dev, 0, NULL, 0, 0); IDirect3DDevice9_SetIndices(dev, NULL);
    IDirect3DDevice9_SetTexture(dev, 0, NULL);
    calls += 5;
    cur_tex = cur_vb = cur_mat_p = NULL;
    T1(P_PRESENT);
    }
}

/* ---- checksum of a deterministic frame ---- */
static DWORD crc32(DWORD crc, const BYTE *p, size_t n)
{
    int k;
    crc = ~crc;
    while (n--) { crc ^= *p++; for (k = 0; k < 8; k++) crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1))); }
    return ~crc;
}
static void readback(void)
{
    IDirect3DSurface9 *bb, *sys; D3DLOCKED_RECT lr; DWORD crc = 0, row[W]; int x, y, nonbg = 0; FILE *f = NULL;
    CK(IDirect3DDevice9_GetBackBuffer(dev, 0, 0, D3DBACKBUFFER_TYPE_MONO, &bb));
    CK(IDirect3DDevice9_CreateOffscreenPlainSurface(dev, W, H, D3DFMT_X8R8G8B8, D3DPOOL_SYSTEMMEM, &sys, NULL));
    CK(IDirect3DDevice9_GetRenderTargetData(dev, bb, sys));
    CK(IDirect3DSurface9_LockRect(sys, &lr, NULL, D3DLOCK_READONLY));
    if (cfg.bmp && (f = fopen(cfg.bmp, "wb")))
    {
        BITMAPFILEHEADER fh = { 0x4d42, sizeof(fh) + sizeof(BITMAPINFOHEADER) + W * H * 4, 0, 0, sizeof(fh) + sizeof(BITMAPINFOHEADER) };
        BITMAPINFOHEADER ih = { sizeof(ih), W, -H, 1, 32, BI_RGB };
        fwrite(&fh, sizeof(fh), 1, f); fwrite(&ih, sizeof(ih), 1, f);
    }
    for (y = 0; y < H; y++)
    {
        const DWORD *src = (const DWORD *)((BYTE *)lr.pBits + y * lr.Pitch);
        for (x = 0; x < W; x++) { row[x] = src[x] | 0xff000000u; nonbg += (row[x] & 0xffffff) != 0x203040; }
        crc = crc32(crc, (const BYTE *)row, sizeof(row));
        if (f) fwrite(row, sizeof(row), 1, f);
    }
    if (f) fclose(f);
    IDirect3DSurface9_UnlockRect(sys);
    printf("CRC %08lx (non-background pixels: %d of %d)%s%s\n", (unsigned long)crc, nonbg, W * H,
           cfg.bmp ? ", image: " : "", cfg.bmp ? cfg.bmp : "");
    IDirect3DSurface9_Release(sys); IDirect3DSurface9_Release(bb);
}

/* ---- which wined3d.dll is this process running? ---- */
static DWORD pe_fingerprint(const BYTE *base)
{
    const IMAGE_NT_HEADERS32 *nt = (const IMAGE_NT_HEADERS32 *)(base + ((const IMAGE_DOS_HEADER *)base)->e_lfanew);
    const IMAGE_SECTION_HEADER *s = IMAGE_FIRST_SECTION(nt);
    DWORD v[7] = { nt->FileHeader.TimeDateStamp, nt->FileHeader.NumberOfSections, nt->OptionalHeader.SizeOfCode,
                   nt->OptionalHeader.SizeOfInitializedData, nt->OptionalHeader.AddressOfEntryPoint,
                   nt->OptionalHeader.SizeOfImage, nt->OptionalHeader.CheckSum };
    DWORD crc = crc32(0, (const BYTE *)v, sizeof(v)); int i;
    for (i = 0; i < nt->FileHeader.NumberOfSections && i < 40; i++)   /* not ImageBase: relocation may change it */
    {
        crc = crc32(crc, s[i].Name, 8);
        crc = crc32(crc, (const BYTE *)&s[i].Misc.VirtualSize, 12);
    }
    return crc;
}
static int report_wined3d(void)
{
    HMODULE m = GetModuleHandleA("wined3d.dll"); WCHAR wpath[MAX_PATH]; char path[MAX_PATH * 3], env[256];
    BYTE hdr[4096]; DWORD got = 0, fp; HANDLE f; int ok = 1, i;
    const char *vars[] = { "WINED3D_WOW64_BUFFERS", "WINE_D3D_CONFIG", "WINEDLLOVERRIDES" };
    if (!m) { printf("wined3d: not loaded\n"); return 0; }
    GetModuleFileNameW(m, wpath, MAX_PATH);
    WideCharToMultiByte(CP_UTF8, 0, wpath, -1, path, sizeof(path), NULL, NULL);
    fp = pe_fingerprint((const BYTE *)m);
    printf("wined3d: %s (%s load, fingerprint %08lx)\n", path,
           memcmp((const BYTE *)m + 0x40, "Wine builtin DLL", 16) ? "native" : "builtin", (unsigned long)fp);
    if (cfg.expect)
    {
        f = CreateFileA(cfg.expect, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
        if (f == INVALID_HANDLE_VALUE || !ReadFile(f, hdr, sizeof(hdr), &got, NULL) || got < sizeof(hdr))
            { printf("expect: cannot read %s\n", cfg.expect); ok = 0; }
        else
        {
            ok = pe_fingerprint(hdr) == fp;
            printf("expect: %s fingerprint %08lx -> %s\n", cfg.expect, (unsigned long)pe_fingerprint(hdr), ok ? "MATCH" : "MISMATCH");
        }
        if (f != INVALID_HANDLE_VALUE) CloseHandle(f);
    }
    for (i = 0; i < 3; i++)
        printf("env: %s=%s\n", vars[i], GetEnvironmentVariableA(vars[i], env, sizeof(env)) ? env : "(unset)");
    return ok;
}

/* ---- setup, timing loop, report ---- */
static int cmpd(const void *a, const void *b) { return cmpd_(a, b); }
static DWORD WINAPI watchdog(void *arg)
{
    Sleep((DWORD)(size_t)arg * 1000); printf("FAIL watchdog: still running after %u s\n", (unsigned)(size_t)arg);
    ExitProcess(3);
}
int main(int argc, char **argv)
{
    IDirect3D9 *d3d; D3DPRESENT_PARAMETERS pp = { 0 }; D3DADAPTER_IDENTIFIER9 id; RECT rc = { 0, 0, W, H };
    WNDCLASSA wc = { 0 }; HWND hwnd; LARGE_INTEGER qf, q0, q1, qs; unsigned long long tsc0, tsc1, calls0;
    double *ft = NULL, sum = 0, el, tps; int nft = 0, cap = 0, i, frame = 0, counts[3] = { 0 };

    for (i = 1; i < argc; i++)
    {
        const char *a = argv[i], *v = i + 1 < argc ? argv[i + 1] : "0";
        if (!strcmp(a, "--crc")) { cfg.crc = 1; continue; }
        if (!strncmp(a, "--", 2)) i++;
        if (!strcmp(a, "--secs")) cfg.secs = atof(v);
        else if (!strcmp(a, "--warmup")) cfg.warmup = atof(v);
        else if (!strcmp(a, "--objects")) cfg.objects = atoi(v);
        else if (!strcmp(a, "--dyn-frac")) cfg.dyn_frac = atof(v);
        else if (!strcmp(a, "--ffp-frac")) cfg.ffp_frac = atof(v);
        else if (!strcmp(a, "--vs")) cfg.vs20 = atoi(v) >= 20;
        else if (!strcmp(a, "--bones")) cfg.bones = atoi(v);
        else if (!strcmp(a, "--dyn-verts")) cfg.dyn_verts = atoi(v) & ~3;
        else if (!strcmp(a, "--mesh-verts")) cfg.mesh_verts = atoi(v);
        else if (!strcmp(a, "--textures")) cfg.textures = atoi(v);
        else if (!strcmp(a, "--redundant")) cfg.redundant = atoi(v);
        else if (!strcmp(a, "--clip")) cfg.clip = atoi(v);
        else if (!strcmp(a, "--order")) cfg.grouped = !strcmp(v, "grouped");
        else if (!strcmp(a, "--phases")) cfg.phases = atoi(v);
        else if (!strcmp(a, "--bmp")) cfg.bmp = v;
        else if (!strcmp(a, "--expect-dll")) cfg.expect = v;
        else if (!strcmp(a, "--radar")) cfg.radar = atoi(v);
        else if (!strcmp(a, "--text")) cfg.text = atoi(v);
        else if (!strcmp(a, "--relock")) cfg.relock = atoi(v);
        else if (!strcmp(a, "--dyntex")) cfg.dyntex = atoi(v);
        else if (!strcmp(a, "--cpu-ms")) cfg.cpu_ms = atof(v);
        else if (!strcmp(a, "--programs")) cfg.programs = atoi(v);
        else if (!strcmp(a, "--hitch")) { cfg.hitch_every = atoi(v); const char *c = strchr(v, ':');
            cfg.hitch_ms = c ? atof(c + 1) : 100; cfg.hitch_sleep = c && strstr(c + 1, ":sleep") != NULL; }
        else { printf("unknown argument %s (see the header of tools/d3d9bench.c)\n", a); return 1; }
    }
    if (cfg.objects < 1 || cfg.textures < 1 || cfg.bones < 1 || cfg.bones > 80 || cfg.dyn_verts < 4
            || cfg.dyn_verts / 4 * 6 > DYN_SIZE || cfg.mesh_verts > 16384 || cfg.clip < 0 || cfg.clip > 6)
        { printf("bad arguments: bones 1-80, dyn-verts 4-3332, mesh-verts <= 16384, clip 0-6\n"); return 1; }
    setvbuf(stdout, NULL, _IONBF, 0);
    CreateThread(NULL, 0, watchdog, (void *)(size_t)(cfg.crc ? 120 : (int)(cfg.secs + cfg.warmup) + 90), 0, NULL);
    printf("d3d9bench: objects=%d dyn-frac=%.2f ffp-frac=%.2f vs=%s bones=%d dyn-verts=%d mesh-verts=%d textures=%d "
           "redundant=%d clip=%d order=%s radar=%d text=%d relock=%d dyntex=%d cpu-ms=%.1f%s\n", cfg.objects, cfg.dyn_frac,
           cfg.ffp_frac, cfg.vs20 ? "2.0" : "1.1", cfg.bones, cfg.dyn_verts, cfg.mesh_verts, cfg.textures, cfg.redundant,
           cfg.clip, cfg.grouped ? "grouped" : "mix", cfg.radar, cfg.text, cfg.relock, cfg.dyntex, cfg.cpu_ms, cfg.crc ? " crc" : "");
    if (!report_wined3d()) { printf("FAIL the loaded wined3d.dll is not the expected file\n"); return 2; }

    wc.lpfnWndProc = DefWindowProcA; wc.hInstance = GetModuleHandleA(NULL); wc.lpszClassName = "d3d9bench";
    wc.hCursor = LoadCursorA(NULL, (LPCSTR)IDC_ARROW);
    RegisterClassA(&wc);
    AdjustWindowRect(&rc, WS_OVERLAPPEDWINDOW, FALSE);
    hwnd = CreateWindowA("d3d9bench", "d3d9bench", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 40, 40,
                         rc.right - rc.left, rc.bottom - rc.top, NULL, NULL, wc.hInstance, NULL);
    if (!(d3d = Direct3DCreate9(D3D_SDK_VERSION))) die("Direct3DCreate9", E_FAIL);
    IDirect3D9_GetAdapterIdentifier(d3d, 0, 0, &id);
    printf("adapter: %s\n", id.Description);
    pp.BackBufferWidth = W; pp.BackBufferHeight = H; pp.BackBufferFormat = D3DFMT_X8R8G8B8; pp.BackBufferCount = 1;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.hDeviceWindow = hwnd; pp.Windowed = TRUE;
    pp.EnableAutoDepthStencil = TRUE; pp.AutoDepthStencilFormat = D3DFMT_D24S8;
    pp.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;
    CK(IDirect3D9_CreateDevice(d3d, D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, hwnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev));

    cols = (int)ceil(sqrt((double)cfg.objects));
    kinds = malloc(cfg.objects);
    for (i = 0; i < cfg.objects; i++)       /* deterministic mix: a hash of i against the fractions */
    {
        double h = ((i * 2654435761u) >> 8) / 16777216.0, h2 = ((i * 2246822519u + 7) >> 8) / 16777216.0;
        kinds[i] = h < cfg.dyn_frac ? K_DYN : h2 < cfg.ffp_frac ? K_FFP : K_VS;
        counts[kinds[i]]++;
    }
    if (cfg.grouped)
        for (i = 0; i < cfg.objects; i++) kinds[i] = i < counts[K_FFP] ? K_FFP : i < counts[K_FFP] + counts[K_VS] ? K_VS : K_DYN;
    printf("draws/frame: %d static FFP, %d vertex shader, %d dynamic VB (%d-vertex locks)\n",
           counts[K_FFP], counts[K_VS], counts[K_DYN], cfg.dyn_verts);
    for (i = 0; i < 256; i++) sin_tab[i] = sinf(i * 6.2831853f / 256);
    setup_camera(); make_textures(); make_meshes(); make_shaders(); make_ui();
    for (i = 0; i < 8; i++)
    {
        IDirect3DDevice9_SetSamplerState(dev, i, D3DSAMP_MINFILTER, D3DTEXF_LINEAR);
        IDirect3DDevice9_SetSamplerState(dev, i, D3DSAMP_MAGFILTER, D3DTEXF_LINEAR);
        IDirect3DDevice9_SetSamplerState(dev, i, D3DSAMP_MIPFILTER, D3DTEXF_LINEAR);
    }
    memset(rs_cache, 0xff, sizeof(rs_cache)); memset(tss_cache, 0xff, sizeof(tss_cache));
    rs(D3DRS_ZENABLE, D3DZB_TRUE); rs(D3DRS_ALPHAREF, 0x60); rs(D3DRS_ALPHAFUNC, D3DCMP_GREATEREQUAL);
    rs(D3DRS_AMBIENT, 0xff404040);
    for (i = 0; i < cfg.clip; i++)           /* planes that clip nothing: only the enable mask matters */
    {
        float plane[4] = { 0, 0, 0, 1 };
        IDirect3DDevice9_SetClipPlane(dev, i, plane);
    }
    rs(D3DRS_CLIPPLANEENABLE, (1u << cfg.clip) - 1);

    if (cfg.programs > 0) return program_warmup();
    if (cfg.crc)                             /* same frame three times; read back before Present */
    {
        for (i = 0; i < 3; i++) { begin_frame(0); if (i < 2) end_frame(0); }
        draw_ui(0);
        CK(IDirect3DDevice9_EndScene(dev));
        readback();
        IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
        return 0;
    }
    QueryPerformanceFrequency(&qf); QueryPerformanceCounter(&qs);
    do { begin_frame(frame); end_frame(frame); frame++; QueryPerformanceCounter(&q0); }
    while ((q0.QuadPart - qs.QuadPart) < cfg.warmup * qf.QuadPart);
    memset(ph, 0, sizeof(ph)); calls0 = calls; tsc0 = __rdtsc(); qs = q0;
    do
    {
        begin_frame(frame); end_frame(frame); frame++;
        QueryPerformanceCounter(&q1);
        if (nft == cap) ft = realloc(ft, (cap = cap ? cap * 2 : 1024) * sizeof(*ft));
        sum += ft[nft++] = (q1.QuadPart - q0.QuadPart) * 1000.0 / qf.QuadPart;
        q0 = q1;
    } while ((q1.QuadPart - qs.QuadPart) < cfg.secs * qf.QuadPart);
    tsc1 = __rdtsc();
    el = (q1.QuadPart - qs.QuadPart) / (double)qf.QuadPart;
    tps = (tsc1 - tsc0) / el;
    qsort(ft, nft, sizeof(*ft), cmpd);
    printf("RESULT frames=%d secs=%.2f fps=%.2f mean=%.3f p50=%.3f p95=%.3f p99=%.3f calls/frame=%llu\n", nft, el,
           nft / el, sum / nft, ft[nft / 2], ft[(int)(nft * 0.95)], ft[(int)(nft * 0.99)], (calls - calls0) / nft);
    if (cfg.phases)
    {
        double tot = 0, p[P_N];
        for (i = 0; i < P_N; i++) tot += p[i] = ph[i] / tps * 1000.0 / nft;
        printf("PHASES ms/frame lock=%.3f fill=%.3f unlock=%.3f state=%.3f draw=%.3f present=%.3f ui=%.3f cpu=%.3f other=%.3f\n",
               p[P_LOCK], p[P_FILL], p[P_UNLOCK], p[P_STATE], p[P_DRAW], p[P_PRESENT], p[P_UI], p[P_CPU], sum / nft - tot);
    }
    IDirect3DDevice9_Release(dev); IDirect3D9_Release(d3d);
    DestroyWindow(hwnd);
    return 0;
}
