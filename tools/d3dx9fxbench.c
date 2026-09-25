/* d3dx9fxbench - replays RotWK's ID3DXEffect call pattern on the game's own .fxo effects, to time and
 * compare d3dx9_27.dll builds without launching the game.
 *
 * The pattern (static analysis of lotrbfme2ep1.exe 2.02, see docs/PERFORMANCE.md "d3dx9 effects"):
 * the FX batch renderer 0x573beb drives a wrapper whose vtable is 0xbe9b84. Per batch:
 *   Begin wrapper 0x5517e6: SetTechnique(tech) [+0xe8], ApplyParameterBlock(material) [+0x12c] when the
 *     material has one, SetTexture(h, tex) for each (handle, texture) pair, then every parameter binding of
 *     the technique (0x552bd0 with 0xffff = all six update lists; setters such as 0x54cda1 SetMatrixTranspose,
 *     0x54ce2c SetMatrix, 0x54ce83 SetVector, 0x54cec5 SetFloat, SetRawValue for bones and lights, SetInt),
 *     then Begin(&passes, 6) [+0xfc]
 *   per pass: BeginPass(p) [+0x100]; per mesh group: the per-object list (list 1) again, CommitChanges()
 *     [+0x104], DrawIndexedPrimitive; EndPass() [+0x108]
 *   End() [+0x10c]
 * All handles are pointers the game got from GetParameter(NULL, i) at load (0x55143f), never names.
 *
 * Here: parameters are grouped by their annotations - "SasBindAddress" or a known engine name = set by
 * the game every batch ("scene"); Sas.Skeleton.*, Sas.PointLight*, World* and a few per-object names =
 * per mesh ("object"); "UIName" (material) = recorded once per material in a parameter block. The scene
 * is a fixed list of batches (--batches, --meshes, --main-share, --seed) drawn every frame twice at
 * UltraHigh: the shadow-map pass with each effect's _CreateShadowMap technique, then the main view
 * (--shadow 0: main view only). Values are deterministic: scene values depend on (frame, pass) only, as
 * the game's setters read one camera and one set of lights per pass; world matrices and bones on (object,
 * frame); point lights come from a small pool (3 in 5 objects have none); other per-object scalars and
 * the ints that select shaders keep their defaults, except NumJointsPerVertex / NumShadows /
 * NumPointLights and bools, which vary within a small range.
 *
 * Modes: --mode mgr (default) records every device call d3dx9 makes through an ID3DXEffectStateManager and
 * does not forward it: the time is d3dx9's own work. --mode fwd records and forwards to the real device.
 * --mode dev sets no state manager (d3dx9 calls the device, like the game). With --hash the recorded call
 * sequence (every state, constant register and its data; textures and shaders as indices) and every
 * BeginPass/CommitChanges result are checksummed: two d3dx9 builds must print the same HASH line for the
 * same arguments and --frames N.
 *
 * Build: i686-w64-mingw32-gcc -O2 -msse2 -mfpmath=sse -o build/d3dx9fxbench.exe tools/d3dx9fxbench.c -ld3d9
 * Run:   wine build/d3dx9fxbench.exe --dll 'Z:\path\to\d3dx9_27-x.dll' --fx defaultw3d.fxo [...]
 *        (the .fxo files are shaders/compiled/ in Shaders.big, tools/bigtool.py extracts them; give the
 *        DLL a name other than d3dx9_27.dll so that file is loaded and not the engine's)
 * Args:  --dll <path>  --fx <file.fxo> (repeatable, up to 16; the first gets --main-share of the batches)
 *        --frames N (0 = time based) --secs S --warmup S --batches N --meshes N --seed N --shadow 0|1
 *        --techs a,b (main-view techniques of the first effect; default Default_M = the medium shader LOD;
 *        "" = all valid) --mode mgr|fwd|dev --hash --list (print the parameter grouping and exit)
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#define D3DX_SDK_VERSION 27
#include <d3dx9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <x86intrin.h>

#define FXC(m, o, ...) ((o)->lpVtbl->m((o), ##__VA_ARGS__))
#define MAXP 512
#define MAXT 256
#define MAXFX 16
enum { G_NONE, G_SCENE, G_OBJ, G_MAT };
enum { T_SCENE, T_OBJ, T_TECH, T_BLOCK, T_TEX, T_BEGIN, T_PASS, T_COMMIT, T_ENDPASS, T_END, T_N };
static const char *tname[T_N] = {"batch-params", "object-params", "SetTechnique", "ApplyParamBlock",
    "SetTexture", "Begin", "BeginPass", "CommitChanges", "EndPass", "End"};

typedef HRESULT (WINAPI *create_fn)(IDirect3DDevice9 *, const void *, UINT, const D3DXMACRO *,
        ID3DXInclude *, DWORD, ID3DXEffectPool *, ID3DXEffect **, ID3DXBuffer **);

typedef struct { D3DXHANDLE h; D3DXPARAMETER_DESC d; int group, raw, vary, lo, hi; BYTE *def; UINT rawbytes; } Param;
typedef struct {
    const char *path; ID3DXEffect *fx; Param p[MAXP]; int np; D3DXHANDLE tech[MAXT]; int ntech;
    D3DXHANDLE block[16]; D3DXHANDLE textures[8]; int ntex; D3DXHANDLE shadow;
} Fx;

static struct { const char *dll, *fx[MAXFX], *techs; int nfx, frames, batches, meshes, mode, hash, list, shadow; double secs, warmup, main_share; unsigned seed; } cfg =
    {NULL, {0}, "Default_M", 0, 0, 300, 3, 0, 0, 0, 1, 5.0, 1.0, 0.8, 1};
static Fx fxs[MAXFX];
static IDirect3DDevice9 *dev;
static IDirect3DTexture9 *tex[8];
static unsigned rng;
static unsigned long long tcount[T_N], tcalls[T_N];

static unsigned lcg(void) { rng = rng * 1664525u + 1013904223u; return rng >> 8; }
static float frand(float lo, float hi) { return lo + (hi - lo) * (float)(lcg() & 0xffff) * (1.0f / 65536.0f); }

/* ---- recording state manager ---------------------------------------------------------------------- */
static unsigned long long hash = 1469598103934665603ull, ncalls;
static void *objs[256]; static int nobjs;
static void h_bytes(const void *p, size_t n) { const BYTE *b = p; while (n--) { hash ^= *b++; hash *= 1099511628211ull; } }
static void h_u32(DWORD v) { h_bytes(&v, 4); }
static void h_obj(void *o)
{
    int i;
    for (i = 0; i < nobjs && objs[i] != o; ++i) ;
    if (i == nobjs && nobjs < 256) objs[nobjs++] = o;
    h_u32(o ? i + 1 : 0);
}
static unsigned long long nid[20];
#define REC(id) do { ncalls++; nid[id]++; if (cfg.hash) h_u32(id); } while (0)
#define FWD (cfg.mode == 1)

static HRESULT WINAPI sm_qi(ID3DXEffectStateManager *s, REFIID r, void **o) { *o = s; return S_OK; }
static ULONG WINAPI sm_ref(ID3DXEffectStateManager *s) { return 1; }
static HRESULT WINAPI sm_transform(ID3DXEffectStateManager *s, D3DTRANSFORMSTATETYPE t, const D3DMATRIX *m)
{ REC(1); if (cfg.hash) { h_u32(t); h_bytes(m, 64); } return FWD ? IDirect3DDevice9_SetTransform(dev, t, m) : S_OK; }
static HRESULT WINAPI sm_material(ID3DXEffectStateManager *s, const D3DMATERIAL9 *m)
{ REC(2); if (cfg.hash) h_bytes(m, sizeof(*m)); return FWD ? IDirect3DDevice9_SetMaterial(dev, m) : S_OK; }
static HRESULT WINAPI sm_light(ID3DXEffectStateManager *s, DWORD i, const D3DLIGHT9 *l)
{ REC(3); if (cfg.hash) { h_u32(i); h_bytes(l, sizeof(*l)); } return FWD ? IDirect3DDevice9_SetLight(dev, i, l) : S_OK; }
static HRESULT WINAPI sm_lightenable(ID3DXEffectStateManager *s, DWORD i, BOOL e)
{ REC(4); if (cfg.hash) { h_u32(i); h_u32(e); } return FWD ? IDirect3DDevice9_LightEnable(dev, i, e) : S_OK; }
static HRESULT WINAPI sm_rs(ID3DXEffectStateManager *s, D3DRENDERSTATETYPE t, DWORD v)
{ REC(5); if (cfg.hash) { h_u32(t); h_u32(v); } return FWD ? IDirect3DDevice9_SetRenderState(dev, t, v) : S_OK; }
static HRESULT WINAPI sm_tex(ID3DXEffectStateManager *s, DWORD st, IDirect3DBaseTexture9 *t)
{ REC(6); if (cfg.hash) { h_u32(st); h_obj(t); } return FWD ? IDirect3DDevice9_SetTexture(dev, st, t) : S_OK; }
static HRESULT WINAPI sm_tss(ID3DXEffectStateManager *s, DWORD st, D3DTEXTURESTAGESTATETYPE t, DWORD v)
{ REC(7); if (cfg.hash) { h_u32(st); h_u32(t); h_u32(v); } return FWD ? IDirect3DDevice9_SetTextureStageState(dev, st, t, v) : S_OK; }
static HRESULT WINAPI sm_ss(ID3DXEffectStateManager *s, DWORD st, D3DSAMPLERSTATETYPE t, DWORD v)
{ REC(8); if (cfg.hash) { h_u32(st); h_u32(t); h_u32(v); } return FWD ? IDirect3DDevice9_SetSamplerState(dev, st, t, v) : S_OK; }
static HRESULT WINAPI sm_npatch(ID3DXEffectStateManager *s, FLOAT n)
{ REC(9); if (cfg.hash) h_bytes(&n, 4); return FWD ? IDirect3DDevice9_SetNPatchMode(dev, n) : S_OK; }
static HRESULT WINAPI sm_fvf(ID3DXEffectStateManager *s, DWORD f)
{ REC(10); if (cfg.hash) h_u32(f); return FWD ? IDirect3DDevice9_SetFVF(dev, f) : S_OK; }
static HRESULT WINAPI sm_vs(ID3DXEffectStateManager *s, IDirect3DVertexShader9 *v)
{ REC(11); if (cfg.hash) h_obj(v); return FWD ? IDirect3DDevice9_SetVertexShader(dev, v) : S_OK; }
static HRESULT WINAPI sm_vsf(ID3DXEffectStateManager *s, UINT r, const FLOAT *d, UINT n)
{ REC(12); if (cfg.hash) { h_u32(r); h_u32(n); h_bytes(d, n * 16); } return FWD ? IDirect3DDevice9_SetVertexShaderConstantF(dev, r, d, n) : S_OK; }
static HRESULT WINAPI sm_vsi(ID3DXEffectStateManager *s, UINT r, const INT *d, UINT n)
{ REC(13); if (cfg.hash) { h_u32(r); h_u32(n); h_bytes(d, n * 16); } return FWD ? IDirect3DDevice9_SetVertexShaderConstantI(dev, r, d, n) : S_OK; }
static HRESULT WINAPI sm_vsb(ID3DXEffectStateManager *s, UINT r, const BOOL *d, UINT n)
{ REC(14); if (cfg.hash) { h_u32(r); h_u32(n); h_bytes(d, n * 4); } return FWD ? IDirect3DDevice9_SetVertexShaderConstantB(dev, r, d, n) : S_OK; }
static HRESULT WINAPI sm_ps(ID3DXEffectStateManager *s, IDirect3DPixelShader9 *p)
{ REC(15); if (cfg.hash) h_obj(p); return FWD ? IDirect3DDevice9_SetPixelShader(dev, p) : S_OK; }
static HRESULT WINAPI sm_psf(ID3DXEffectStateManager *s, UINT r, const FLOAT *d, UINT n)
{ REC(16); if (cfg.hash) { h_u32(r); h_u32(n); h_bytes(d, n * 16); } return FWD ? IDirect3DDevice9_SetPixelShaderConstantF(dev, r, d, n) : S_OK; }
static HRESULT WINAPI sm_psi(ID3DXEffectStateManager *s, UINT r, const INT *d, UINT n)
{ REC(17); if (cfg.hash) { h_u32(r); h_u32(n); h_bytes(d, n * 16); } return FWD ? IDirect3DDevice9_SetPixelShaderConstantI(dev, r, d, n) : S_OK; }
static HRESULT WINAPI sm_psb(ID3DXEffectStateManager *s, UINT r, const BOOL *d, UINT n)
{ REC(18); if (cfg.hash) { h_u32(r); h_u32(n); h_bytes(d, n * 4); } return FWD ? IDirect3DDevice9_SetPixelShaderConstantB(dev, r, d, n) : S_OK; }
static ID3DXEffectStateManagerVtbl sm_vtbl = {sm_qi, sm_ref, sm_ref, sm_transform, sm_material, sm_light,
    sm_lightenable, sm_rs, sm_tex, sm_tss, sm_ss, sm_npatch, sm_fvf, sm_vs, sm_vsf, sm_vsi, sm_vsb, sm_ps,
    sm_psf, sm_psi, sm_psb};
static ID3DXEffectStateManager sm = {&sm_vtbl};

/* ---- parameters ----------------------------------------------------------------------------------- */
static const char *annot(ID3DXEffect *fx, D3DXHANDLE h, const char *name)
{
    D3DXHANDLE a = FXC(GetAnnotationByName, fx, h, name);
    LPCSTR s = NULL;
    if (!a || FAILED(FXC(GetString, fx, a, &s))) return NULL;
    return s;
}

static int iname(const char *n, const char *const *list)
{
    for (; *list; ++list) if (!strcmp(n, *list)) return 1;
    return 0;
}

/* register-layout size of one element for SetRawValue: every row of every leaf starts a register */
static UINT raw_size(ID3DXEffect *fx, D3DXHANDLE h)
{
    D3DXPARAMETER_DESC d; UINT i, s = 0;
    FXC(GetParameterDesc, fx, h, &d);
    if (d.Class != D3DXPC_STRUCT) return (d.Class == D3DXPC_MATRIX_COLUMNS ? d.Columns : d.Rows) * 16;
    for (i = 0; i < d.StructMembers; ++i) s += raw_size(fx, FXC(GetParameter, fx, h, i));
    return s;
}

static void classify(Fx *f)
{
    static const char *const obj[] = {"World", "WorldBones", "WorldBones_L", "NumJointsPerVertex", "PointLight",
        "NumPointLights", "OpacityOverride", "ObjectShroudStatus", "HouseColor", "HouseColorEnable", NULL};
    static const char *const scene[] = {"View", "Projection", "ViewI", "ViewProjection", "Time", "Shroud",
        "Cloud", "ShadowInfo", "NumShadows", "AmbientLightColor", "DirectionalLight", "NumDirectionalLights",
        "EyePosition", "Fog", "ShadowMap", "ShroudTexture", "CloudTexture", NULL};
    D3DXEFFECT_DESC ed; UINT i;
    FXC(GetDesc, f->fx, &ed);
    for (i = 0; i < ed.Parameters && f->np < MAXP; ++i)
    {
        Param *p = &f->p[f->np];
        const char *sas;
        p->h = FXC(GetParameter, f->fx, NULL, i);
        FXC(GetParameterDesc, f->fx, p->h, &p->d);
        if (p->d.Class == D3DXPC_OBJECT && p->d.Type != D3DXPT_TEXTURE && p->d.Type != D3DXPT_TEXTURE2D) continue;
        if (p->d.Type == D3DXPT_STRING) continue;
        sas = annot(f->fx, p->h, "SasBindAddress");
        if (iname(p->d.Name, obj) || (sas && (!strncmp(sas, "Sas.Skeleton", 12) || !strncmp(sas, "Sas.PointLight", 14))))
            p->group = G_OBJ;
        else if (sas || iname(p->d.Name, scene)) p->group = G_SCENE;
        else if (annot(f->fx, p->h, "UIName")) p->group = G_MAT;
        else p->group = G_NONE;
        p->def = calloc(1, p->d.Bytes + 16);
        FXC(GetValue, f->fx, p->h, p->def, p->d.Bytes);
        p->raw = p->d.Class == D3DXPC_STRUCT;
        if (p->raw) p->rawbytes = raw_size(f->fx, p->d.Elements ? FXC(GetParameterElement, f->fx, p->h, 0) : p->h)
                * (p->d.Elements ? p->d.Elements : 1);
        p->vary = p->d.Type == D3DXPT_FLOAT;
        if (!strcmp(p->d.Name, "NumJointsPerVertex")) { p->vary = 1; p->lo = 0; p->hi = 2; }
        if (!strcmp(p->d.Name, "NumShadows") || !strcmp(p->d.Name, "NumPointLights")) { p->vary = 1; p->lo = 0; p->hi = 1; }
        if (p->d.Type == D3DXPT_BOOL) { p->vary = 1; p->lo = 0; p->hi = 1; }
        f->np++;
    }
    for (i = 0; i < ed.Techniques && f->ntech < MAXT; ++i)
    {
        D3DXHANDLE t = FXC(GetTechnique, f->fx, i);
        D3DXTECHNIQUE_DESC td; char key[256];
        FXC(GetTechniqueDesc, f->fx, t, &td);
        snprintf(key, sizeof(key), ",%s,", td.Name);
        if (FAILED(FXC(ValidateTechnique, f->fx, t))) continue;
        if (!strcmp(td.Name, "_CreateShadowMap")) { f->shadow = t; continue; }
        { char list[1024]; snprintf(list, sizeof(list), ",%s,", cfg.techs); if (f == fxs && *cfg.techs && !strstr(list, key)) continue; }
        f->tech[f->ntech++] = t;
    }
}

/* Values. The game's setters read global state: camera, lights, time and fog are the same for every
 * batch of one render pass (the shadow-map pass uses the light's camera), so "scene" values depend on
 * (frame, pass) only; "object" values depend on the object (world matrix and bones also on the frame).
 * Point lights come from a small pool (most units have none nearby); other per-object scalars keep their
 * defaults; object ints/bools are per object. */
static unsigned vseed;
static unsigned vrand(void) { vseed = vseed * 1664525u + 1013904223u; return vseed >> 8; }
static float vfrand(float lo, float hi) { return lo + (hi - lo) * (float)(vrand() & 0xffff) * (1.0f / 65536.0f); }
static unsigned mix(unsigned a, unsigned b) { a ^= b * 0x9e3779b9u; a *= 0x85ebca6bu; return a ^ (a >> 13); }

static void set_param(Fx *f, Param *p, int frame, int pass, unsigned obj)
{
    ID3DXEffect *fx = f->fx;
    float buf[4096]; UINT n = p->d.Bytes / 4, i, idx = (UINT)(p - f->p);
    int is_obj = p->group == G_OBJ, world = !strncmp(p->d.Name, "World", 5);
    vseed = is_obj ? mix(mix(obj, idx), world ? (unsigned)frame : 0)
            : p->group == G_MAT ? mix(obj, idx) : mix(mix((unsigned)frame * 2 + pass, idx), 77);
    if (is_obj && !strcmp(p->d.Name, "PointLight"))
        vseed = obj % 5 < 3 ? 0 : mix(obj % 5, (unsigned)frame / 8);   /* 3 in 5 objects: no light (zeros) */
    if (p->d.Class == D3DXPC_OBJECT) { FXC(SetTexture, fx, p->h, (IDirect3DBaseTexture9 *)tex[(idx + pass) % 8]); return; }
    if (n > 4096) n = 4096;
    if (p->d.Type != D3DXPT_FLOAT)
    {
        int v = p->vary ? p->lo + (int)(vrand() % (p->hi - p->lo + 1)) : *(int *)p->def;
        if (p->d.Type == D3DXPT_BOOL) FXC(SetBool, fx, p->h, v);
        else FXC(SetInt, fx, p->h, v);
        return;
    }
    if (!strcmp(p->d.Name, "Time")) { FXC(SetFloat, fx, p->h, frame / 30.0f); return; }
    if (p->raw)
    {
        UINT rn = p->rawbytes / 4, used = rn;
        if (rn > 4096) rn = used = 4096;
        if (!strncmp(p->d.Name, "WorldBones", 10)) used = 8 * (1 + obj % 4);  /* 1-4 bones: quaternion + translation */
        if (used > rn) used = rn;
        for (i = 0; i < used; ++i) buf[i] = vseed ? vfrand(-1.0f, 1.0f) : 0.0f;
        FXC(SetRawValue, fx, p->h, buf, 0, used * 4);
        return;
    }
    memcpy(buf, p->def, n * 4);
    if (!is_obj || world)   /* per-object scalars keep their default */
        for (i = 0; i < n; ++i) buf[i] += vfrand(-0.5f, 0.5f);
    if (p->d.Class == D3DXPC_MATRIX_ROWS || p->d.Class == D3DXPC_MATRIX_COLUMNS)
    {
        if (p->d.Elements) FXC(SetMatrixArray, fx, p->h, (D3DXMATRIX *)buf, min(p->d.Elements, 64));
        else if (p->d.Rows == 4 && p->d.Columns == 4) FXC(SetMatrixTranspose, fx, p->h, (D3DXMATRIX *)buf);
        else FXC(SetValue, fx, p->h, buf, n * 4);
    }
    else if (p->d.Class == D3DXPC_VECTOR && !p->d.Elements) FXC(SetVector, fx, p->h, (D3DXVECTOR4 *)buf);
    else if (p->d.Class == D3DXPC_SCALAR && !p->d.Elements) FXC(SetFloat, fx, p->h, buf[0]);
    else FXC(SetFloatArray, fx, p->h, buf, n);
}

static double tick_ns;
#define T0() unsigned long long _t = __rdtsc()
#define T1(k) do { tcount[k] += __rdtsc() - _t; tcalls[k]++; } while (0)

static void set_group(Fx *f, int g, int frame, int pass, unsigned obj, int k)
{
    int i;
    T0();
    for (i = 0; i < f->np; ++i) if (f->p[i].group == g) set_param(f, &f->p[i], frame, pass, obj);
    T1(k);
}

/* the visible scene: fixed batches (effect, material, main technique, meshes), the same every frame */
typedef struct { Fx *f; int block, tech, meshes, tex[8]; unsigned obj; } Batch;
static Batch *scene; static int nscene;

static void build_scene(void)
{
    int b, t;
    scene = calloc(cfg.batches, sizeof(*scene));
    rng = cfg.seed;
    for (b = 0; b < cfg.batches; ++b)
    {
        Batch *s = &scene[nscene];
        s->f = &fxs[(cfg.nfx == 1 || frand(0, 1) < cfg.main_share) ? 0 : 1 + lcg() % (cfg.nfx - 1)];
        if (!s->f->ntech) continue;
        s->meshes = 1 + lcg() % cfg.meshes;
        s->tech = lcg() % s->f->ntech;
        s->block = lcg() % 16;
        for (t = 0; t < 8; ++t) s->tex[t] = lcg() % 8;
        s->obj = (unsigned)b * 64;
        ++nscene;
    }
}

static void render_batch(Batch *s, D3DXHANDLE tech, int fr, int pass)
{
    Fx *f = s->f; UINT passes = 0; int m, t, p;
    { T0(); FXC(SetTechnique, f->fx, tech); T1(T_TECH); }
    { T0(); FXC(ApplyParameterBlock, f->fx, f->block[s->block]); T1(T_BLOCK); }
    for (t = 0; t < f->ntex; ++t) { T0(); FXC(SetTexture, f->fx, f->textures[t], (IDirect3DBaseTexture9 *)tex[s->tex[t]]); T1(T_TEX); }
    set_group(f, G_SCENE, fr, pass, 0, T_SCENE);
    set_group(f, G_OBJ, fr, pass, s->obj, T_OBJ);
    { T0(); FXC(Begin, f->fx, &passes, 6); T1(T_BEGIN); }
    for (p = 0; p < (int)passes; ++p)
    {
        HRESULT hr;
        { T0(); hr = FXC(BeginPass, f->fx, p); T1(T_PASS); }
        if (cfg.hash) h_u32(hr);
        for (m = 0; m < s->meshes; ++m)
        {
            set_group(f, G_OBJ, fr, pass, s->obj + m, T_OBJ);
            { T0(); hr = FXC(CommitChanges, f->fx); T1(T_COMMIT); }
            if (cfg.hash) h_u32(hr);
        }
        { T0(); FXC(EndPass, f->fx); T1(T_ENDPASS); }
    }
    { T0(); FXC(End, f->fx); T1(T_END); }
}

/* UltraHigh: the shadow-map pass (UpdateShadowMap 0x47d5c9) first, then the main view */
static void frame(int fr)
{
    int b;
    if (cfg.shadow)
        for (b = 0; b < nscene; ++b)
            if (scene[b].f->shadow) render_batch(&scene[b], scene[b].f->shadow, fr, 0);
    for (b = 0; b < nscene; ++b)
        render_batch(&scene[b], scene[b].f->tech[scene[b].tech], fr, 1);
}

static BYTE *readfile(const char *path, DWORD *size)
{
    FILE *fp = fopen(path, "rb"); BYTE *d;
    if (!fp) return NULL;
    fseek(fp, 0, SEEK_END); *size = ftell(fp); fseek(fp, 0, SEEK_SET);
    d = malloc(*size); fread(d, 1, *size, fp); fclose(fp);
    return d;
}

static int cmp_d(const void *a, const void *b) { double x = *(double *)a, y = *(double *)b; return x < y ? -1 : x > y; }

int main(int argc, char **argv)
{
    static const char *gname[] = {"-", "scene", "object", "material"};
    D3DPRESENT_PARAMETERS pp = {0};
    IDirect3D9 *d3d; HWND wnd; HMODULE mod; create_fn create;
    LARGE_INTEGER qf, q0, q1; unsigned long long r0;
    double *ft = malloc(sizeof(double) * 100000), total = 0; int i, j, nf = 0, warm = 0, frames_run;
    char path[MAX_PATH];

    for (i = 1; i < argc; ++i)
    {
        const char *a = argv[i], *v = i + 1 < argc ? argv[i + 1] : "0";
        if (!strcmp(a, "--hash")) { cfg.hash = 1; continue; }
        if (!strcmp(a, "--list")) { cfg.list = 1; continue; }
        ++i;
        if (!strcmp(a, "--dll")) cfg.dll = v;
        else if (!strcmp(a, "--fx") && cfg.nfx < MAXFX) cfg.fx[cfg.nfx++] = v;
        else if (!strcmp(a, "--frames")) cfg.frames = atoi(v);
        else if (!strcmp(a, "--secs")) cfg.secs = atof(v);
        else if (!strcmp(a, "--warmup")) cfg.warmup = atof(v);
        else if (!strcmp(a, "--batches")) cfg.batches = atoi(v);
        else if (!strcmp(a, "--meshes")) cfg.meshes = atoi(v);
        else if (!strcmp(a, "--main-share")) cfg.main_share = atof(v);
        else if (!strcmp(a, "--techs")) cfg.techs = v;
        else if (!strcmp(a, "--seed")) cfg.seed = strtoul(v, NULL, 0);
        else if (!strcmp(a, "--shadow")) cfg.shadow = atoi(v);
        else if (!strcmp(a, "--mode")) cfg.mode = !strcmp(v, "fwd") ? 1 : !strcmp(v, "dev") ? 2 : 0;
        else { fprintf(stderr, "unknown argument %s\n", a); return 1; }
    }
    if (!cfg.dll || !cfg.nfx) { fprintf(stderr, "usage: d3dx9fxbench --dll <d3dx9_27.dll> --fx <file.fxo> [...]\n"); return 1; }
    _controlfp(_PC_24 | _RC_NEAR, _MCW_PC | _MCW_RC);   /* the game's FPU mode (0x440809) */
    if (!(mod = LoadLibraryA(cfg.dll)) || !(create = (create_fn)GetProcAddress(mod, "D3DXCreateEffect")))
    { fprintf(stderr, "cannot load %s (%lu)\n", cfg.dll, GetLastError()); return 1; }
    GetModuleFileNameA(mod, path, sizeof(path));
    printf("d3dx9: %s\n", path);

    wnd = CreateWindowA("STATIC", "d3dx9fxbench", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, NULL, NULL, NULL, NULL);
    d3d = Direct3DCreate9(D3D_SDK_VERSION);
    pp.Windowed = TRUE; pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.BackBufferWidth = 64; pp.BackBufferHeight = 64;
    pp.EnableAutoDepthStencil = TRUE; pp.AutoDepthStencilFormat = D3DFMT_D24S8;
    if (FAILED(IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, wnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev)))
    { fprintf(stderr, "no device\n"); return 1; }
    for (i = 0; i < 8; ++i) IDirect3DDevice9_CreateTexture(dev, 4, 4, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &tex[i], NULL);

    for (j = 0; j < cfg.nfx; ++j)
    {
        Fx *f = &fxs[j]; DWORD size; BYTE *data = readfile(cfg.fx[j], &size); ID3DXBuffer *err = NULL; HRESULT hr;
        f->path = cfg.fx[j];
        if (!data) { fprintf(stderr, "cannot read %s\n", cfg.fx[j]); return 1; }
        if (FAILED(hr = create(dev, data, size, NULL, NULL, 0, NULL, &f->fx, &err)))
        { fprintf(stderr, "D3DXCreateEffect(%s) failed %#lx\n", cfg.fx[j], hr); return 1; }
        classify(f);
        if (cfg.mode != 2) FXC(SetStateManager, f->fx, &sm);
        rng = cfg.seed * 7919u + j;
        for (i = 0; i < 16; ++i)   /* materials: parameter blocks of the material (UIName) parameters */
        {
            int k;
            FXC(BeginParameterBlock, f->fx);
            for (k = 0; k < f->np; ++k) if (f->p[k].group == G_MAT && f->p[k].d.Class != D3DXPC_OBJECT) set_param(f, &f->p[k], 0, 1, 1000003u * i + k);
            f->block[i] = FXC(EndParameterBlock, f->fx);
        }
        for (i = 0; i < f->np && f->ntex < 8; ++i)
            if (f->p[i].group == G_MAT && f->p[i].d.Class == D3DXPC_OBJECT) f->textures[f->ntex++] = f->p[i].h;
        printf("effect %s: %d parameters, %d main techniques%s, %d material textures\n", f->path, f->np, f->ntech,
                f->shadow ? " + _CreateShadowMap" : "", f->ntex);
        if (cfg.list)
            for (i = 0; i < f->np; ++i)
                printf("  %-8s %-40s class %u type %u %ux%u el %u bytes %u%s\n", gname[f->p[i].group], f->p[i].d.Name,
                        f->p[i].d.Class, f->p[i].d.Type, f->p[i].d.Rows, f->p[i].d.Columns, f->p[i].d.Elements,
                        f->p[i].d.Bytes, f->p[i].raw ? " (SetRawValue)" : "");
    }
    if (cfg.list) return 0;
    build_scene();

    QueryPerformanceFrequency(&qf);
    QueryPerformanceCounter(&q0); r0 = __rdtsc(); Sleep(200); QueryPerformanceCounter(&q1);
    tick_ns = (q1.QuadPart - q0.QuadPart) * 1e9 / qf.QuadPart / (double)(__rdtsc() - r0);
    rng = cfg.seed;
    for (i = 0; ; ++i)
    {
        double ms;
        QueryPerformanceCounter(&q0);
        frame(i);
        QueryPerformanceCounter(&q1);
        ms = (q1.QuadPart - q0.QuadPart) * 1000.0 / qf.QuadPart;
        if (cfg.frames) { if (nf < 100000) ft[nf++] = ms; total += ms; if (nf >= cfg.frames) break; continue; }
        if (!warm) { total += ms; if (total >= cfg.warmup * 1000) { warm = 1; total = 0; memset(tcount, 0, sizeof(tcount)); memset(tcalls, 0, sizeof(tcalls)); } continue; }
        if (nf < 100000) ft[nf++] = ms;
        total += ms;
        if (total >= cfg.secs * 1000) break;
    }
    frames_run = i + 1;
    qsort(ft, nf, sizeof(double), cmp_d);
    printf("per call (us): ");
    for (i = 0; i < T_N; ++i)
        if (tcalls[i]) printf("%s %.2f x%.0f  ", tname[i], tcount[i] * tick_ns / 1000.0 / tcalls[i], (double)tcalls[i] / nf);
    printf("\nRESULT frames=%d mean=%.3f p50=%.3f p95=%.3f ms/frame, device calls/frame=%.0f (mode %s)\n",
            nf, total / nf, ft[nf / 2], ft[nf * 95 / 100], (double)ncalls / frames_run, cfg.mode == 0 ? "mgr" : cfg.mode == 1 ? "fwd" : "dev");
    printf("device calls per frame by kind:");
    for (j = 1; j < 19; ++j) if (nid[j]) printf(" %d:%.0f", j, (double)nid[j] / frames_run);
    printf("\n");
    if (cfg.hash) printf("HASH %016llx calls=%llu frames=%d\n", hash, ncalls, frames_run);
    return 0;
}
