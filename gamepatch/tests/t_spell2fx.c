/* t_spell2fx: fxparamused (p_spell2fx.c) against the original, with the game's own code and Wine's
 * real d3dx9_27 effects. Two relocated copies of .text (one patched by the installer, with its hash
 * and byte checks; one untouched); .rdata/.data at their own addresses, the kernel32 / msvcr71 /
 * d3dx9_27 imports filled as the loader fills them, the code pointers in .rdata (vtables) pointed at
 * the unpatched copy; a D3D9 device on a small window; every compiled
 * effect of the game's Shaders.big (next to the exe) created through the game's thunk 0xa3ed20.
 *   [0] the patch applies: 0x55207f calls its stub, both IAT slots go to its wrappers
 *   [1] every top-level parameter x every technique (and NULL technique, NULL parameter, a
 *       technique of another effect) of every effect: the cached answer, asked three times in a
 *       shuffled order, against the effect's own IsParameterUsed: identical; then all effects
 *       released and created again (the cache must be cleared: counted) and the same again
 *   [2] the game's 0x551f8f in both copies, each on its own material (the game's constructor
 *       0x551f2c, list helpers 0x550c35 / 0x48287a / 0x50df9f) on the same DefaultW3D effect, for
 *       each of its techniques: the converted material's 15 parameters (Texture_0 included; texture
 *       loads 0x532875 by a stand-in, the same in both), then particles as the RenderObject module
 *       sets them, ColorEmissive / Opacity / ColorDiffuse per particle per pass, two passes a frame:
 *       after every call the return value, the material's parameter list (every field), its texture
 *       list and its recorded block (Wine's parameter block: every recorded byte) are identical
 *   [3] sensitivity: the patched copy's call site answering one parameter wrongly -> caught by
 *       [2]'s comparison; one wrong cached answer -> caught by [1]'s
 *   [4] time: IsParameterUsed direct -> cached; one colour set (0x551f8f with the list copy and
 *       merge around it, as 0x50e040 does) original -> patched, per technique
 * usage: t_spell2fx.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include "p_spell2.h"
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#define TC __attribute__((thiscall))
#define SC __attribute__((stdcall))
#define AT(va) ((uint32_t *)(uintptr_t)(va))
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define VT(o, off) (((void **)*(void **)(o))[(off) / 4])
typedef void *H;

static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs = 1;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
static uint32_t off[2];
static LONG WINAPI crash(EXCEPTION_POINTERS *e)
{
    CONTEXT *c = e->ContextRecord;
    printf("exception %08lx at %p (off %08x / %08x) eax %08lx ecx %08lx esi %08lx edi %08lx\nFAIL\n",
           e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress, off[0], off[1],
           c->Eax, c->Ecx, c->Esi, c->Edi);
    ExitProcess(3);
}
static void jmp_to(uint32_t va, void *target)
{
    uint8_t *p = (uint8_t *)(uintptr_t)va;
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)target - (va + 5));
    p[0] = 0xe9; memcpy(p + 1, &rel, 4);
}
static uint32_t call_target(uint32_t va)
{
    const uint8_t *p = (const uint8_t *)(uintptr_t)va;
    int32_t rel; memcpy(&rel, p + 1, 4);
    return va + 5 + rel;
}

/* ---- the exe's imports, filled from the test's own modules ------------------------------- */
static uint8_t *exe; static long exe_len;
static uint32_t rva2off(uint32_t rva)
{
    IMAGE_NT_HEADERS32 *nt = (IMAGE_NT_HEADERS32 *)(exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    IMAGE_SECTION_HEADER *s = IMAGE_FIRST_SECTION(nt);
    for (int i = 0; i < nt->FileHeader.NumberOfSections; i++)
        if (rva >= s[i].VirtualAddress && rva < s[i].VirtualAddress + s[i].SizeOfRawData)
            return rva - s[i].VirtualAddress + s[i].PointerToRawData;
    return 0;
}
static int fill_imports(void)
{
    static const char *dlls[] = {"kernel32.dll", "msvcr71.dll", "d3dx9_27.dll", NULL};
    IMAGE_NT_HEADERS32 *nt = (IMAGE_NT_HEADERS32 *)(exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    IMAGE_IMPORT_DESCRIPTOR *d = (IMAGE_IMPORT_DESCRIPTOR *)(exe + rva2off(
        nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress));
    int n = 0;
    for (; d->Name; d++) {
        const char *name = (const char *)exe + rva2off(d->Name);
        int want = 0;
        for (int i = 0; dlls[i]; i++) want |= !_stricmp(name, dlls[i]);
        if (!want) continue;
        HMODULE m = LoadLibraryA(name);
        if (!m) { printf("cannot load %s\n", name); return 1; }
        uint32_t *thunk = (uint32_t *)(exe + rva2off(d->OriginalFirstThunk ? d->OriginalFirstThunk : d->FirstThunk));
        for (uint32_t i = 0; thunk[i]; i++) {
            FARPROC f = thunk[i] & 0x80000000u ? GetProcAddress(m, (LPCSTR)(uintptr_t)(thunk[i] & 0xffff))
                                               : GetProcAddress(m, (const char *)exe + rva2off(thunk[i]) + 2);
            *AT(GP_EXE_BASE + d->FirstThunk + 4 * i) = (uint32_t)(uintptr_t)f;
            n += f != NULL;
        }
    }
    printf("imports filled: %d (kernel32, msvcr71, d3dx9_27)\n", n);
    return 0;
}

/* code pointers in .rdata (vtables, functors, handler tables) still name the image's own
 * addresses, where a test process has no code: point those that land on a function start (after
 * int3 / ret / nop padding) at the unpatched copy */
static int relocate_code_pointers(void)
{
    IMAGE_NT_HEADERS32 *nt = (IMAGE_NT_HEADERS32 *)(exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    uint32_t iat = GP_EXE_BASE + nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IAT].VirtualAddress;
    uint32_t iat_end = iat + nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IAT].Size;
    int n = 0;
    for (uint32_t a = 0xbd0000; a < 0xd89000; a += 4) {
        if (a >= iat && a < iat_end) continue;
        uint32_t v = *AT(a);
        if (v < 0x401000 || v >= 0xbd0000) continue;
        const uint8_t *b = orig_bytes(v - 3, 3);
        if (!b || !(b[2] == 0xcc || b[2] == 0xc3 || b[2] == 0x90 || b[0] == 0xc2)) continue;
        *AT(a) = v + off[0];
        n++;
    }
    return n;
}

/* ---- allocator and texture stand-ins (the same in both copies) ---------------------------- */
static void *__cdecl t_alloc(uint32_t n, int a, int b) { (void)a; (void)b; return calloc(1, n ? n : 1); }
static void __cdecl t_free(void *p, int a) { (void)a; free(p); }
typedef struct { void *vt; uint32_t refs; char name[48]; } tex_t;   /* refcount word at +4 */
static tex_t texs[16]; static int ntex; static long tex_loads;
static void *tex_vt[4];
static void *__cdecl tex_load(void **holder, const char *name, int a, int b)
{
    (void)a; (void)b;
    tex_loads++;
    if (!name) { *holder = NULL; return holder; }
    int i = 0;
    while (i < ntex && strcmp(texs[i].name, name)) i++;
    if (i == ntex && ntex < 16) { texs[i].vt = tex_vt; texs[i].refs = 0x100; snprintf(texs[i].name, 48, "%s", name); ntex++; }
    *holder = &texs[i];
    texs[i].refs++;                                    /* as the original's holder takes a reference */
    return holder;
}

/* ---- effects ----------------------------------------------------------------------------- */
typedef HRESULT (SC *create_t)(IDirect3DDevice9 *, const void *, UINT, const void *, void *, DWORD, void *, void **, void **);
typedef struct { const char *Creator; UINT Parameters, Techniques, Functions; } EDESC;
enum { MAXFX = 16, MAXP = 256, MAXT = 32 };
typedef struct { char name[64]; uint8_t *data; uint32_t len; void *fx; int np, nt; H p[MAXP], t[MAXT]; } fx_t;
static fx_t fxs[MAXFX]; static int nfx;
static IDirect3DDevice9 *dev;

static int load_big(const char *exe_path)
{
    char path[MAX_PATH]; snprintf(path, sizeof path, "%s", exe_path);
    char *sl = strrchr(path, '\\'); if (!sl) sl = strrchr(path, '/');
    if (!sl) return 1;
    strcpy(sl + 1, "Shaders.big");
    FILE *f = fopen(path, "rb");
    if (!f) { printf("cannot open %s\n", path); return 1; }
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *b = malloc(n);
    if (fread(b, 1, n, f) != (size_t)n) { fclose(f); return 1; }
    fclose(f);
#define BE(p) ((uint32_t)(p)[0] << 24 | (uint32_t)(p)[1] << 16 | (uint32_t)(p)[2] << 8 | (p)[3])
    uint32_t cnt = BE(b + 8), o = 16;
    for (uint32_t i = 0; i < cnt && nfx < MAXFX; i++) {
        uint32_t fo = BE(b + o), fl = BE(b + o + 4);
        const char *nm = (const char *)b + o + 8;
        o += 8 + (uint32_t)strlen(nm) + 1;
        size_t k = strlen(nm);
        if (k > 4 && !_stricmp(nm + k - 4, ".fxo")) {
            fx_t *e = &fxs[nfx++];
            const char *base = strrchr(nm, '\\');
            snprintf(e->name, sizeof e->name, "%s", base ? base + 1 : nm);
            e->data = b + fo; e->len = fl;
        }
    }
    printf("Shaders.big: %d compiled effects\n", nfx);
    return nfx == 0;
}
static int create_all(create_t cr)
{
    int ok = 0;
    for (int i = 0; i < nfx; i++) {
        fx_t *e = &fxs[i];
        void *err = NULL;
        e->fx = NULL;
        HRESULT hr = cr(dev, e->data, e->len, NULL, NULL, 0, NULL, &e->fx, &err);
        if (FAILED(hr) || !e->fx) { printf("  %s: D3DXCreateEffect %08lx\n", e->name, hr); continue; }
        EDESC d; ((HRESULT (SC *)(void *, EDESC *))VT(e->fx, 0xc))(e->fx, &d);
        e->np = d.Parameters < MAXP ? (int)d.Parameters : MAXP;
        e->nt = d.Techniques < MAXT ? (int)d.Techniques : MAXT;
        for (int k = 0; k < e->np; k++) e->p[k] = ((H (SC *)(void *, H, UINT))VT(e->fx, 0x20))(e->fx, NULL, k);
        for (int k = 0; k < e->nt; k++) e->t[k] = ((H (SC *)(void *, UINT))VT(e->fx, 0x30))(e->fx, k);
        ok++;
    }
    return ok;
}
static void release_all(void)
{
    for (int i = 0; i < nfx; i++)
        if (fxs[i].fx) { ((ULONG (SC *)(void *))VT(fxs[i].fx, 8))(fxs[i].fx); fxs[i].fx = NULL; }
}
static BOOL direct(void *fx, H p, H t) { return ((BOOL (SC *)(void *, H, H))VT(fx, 0xf8))(fx, p, t); }

/* [1]: every pair, three times, shuffled */
typedef struct { int fx; H p, t; } pair_t;
static long check_pairs(long *npairs, int corrupt)
{
    static pair_t pr[200000];
    long n = 0, bad = 0;
    for (int i = 0; i < nfx; i++) {
        fx_t *e = &fxs[i];
        if (!e->fx) continue;
        for (int a = 0; a < e->np; a++) {
            for (int b = 0; b <= e->nt + 1 && n < 199990; b++) {
                H t = b < e->nt ? e->t[b] : b == e->nt ? NULL : fxs[(i + 1) % nfx].t[0];
                pr[n++] = (pair_t){i, e->p[a], t};
            }
        }
        pr[n++] = (pair_t){i, NULL, e->nt ? e->t[0] : NULL};
    }
    *npairs = n;
    for (int rep = 0; rep < 3; rep++) {
        for (long k = n - 1; k > 0; k--) { long j = rnd() % (k + 1); pair_t x = pr[k]; pr[k] = pr[j]; pr[j] = x; }
        for (long k = 0; k < n; k++) {
            void *fx = fxs[pr[k].fx].fx;
            BOOL want = direct(fx, pr[k].p, pr[k].t);
            BOOL got = gp_fxu_isused(fx, pr[k].p, pr[k].t);
            if (corrupt && rep == 2 && k == n / 2) got = !got;   /* the sensitivity run's wrong entry */
            if (!want != !got) { if (bad++ < 3 && !corrupt) printf("  MISMATCH %s param %p tech %p: %d vs %d\n", fxs[pr[k].fx].name, pr[k].p, pr[k].t, want, got); }
        }
    }
    return bad;
}

/* ---- the game's material code ------------------------------------------------------------- */
typedef struct { uint32_t name, type, tex; float v[4]; int32_t i; uint8_t b, pad[3]; } entry_t;   /* 0x24 */
typedef struct { entry_t *b, *e, *c; } evec_t;
static const char *str(uint32_t a) { return a ? (const char *)(uintptr_t)(a + 8) : ""; }
#define FN(k, va) ((uintptr_t)(va) + off[k])
static void entry_new(int k, entry_t *e, const char *name, int type)
{ ((void (TC *)(entry_t *, const char *, int))FN(k, 0x550c35))(e, name, type); }
static void entry_del(int k, entry_t *e) { ((void (TC *)(entry_t *))FN(k, 0x47b396))(e); }
static void vec_push(int k, evec_t *v, entry_t *e) { ((void (TC *)(evec_t *, entry_t *))FN(k, 0x47d3b4))(v, e); }
static void vec_set(int k, evec_t *v, entry_t *e) { ((void (TC *)(evec_t *, entry_t *))FN(k, 0x48287a))(v, e); }
static void vec_copy(int k, evec_t *d, evec_t *s) { ((void (TC *)(evec_t *, evec_t *))FN(k, 0x50df9f))(d, s); }
static void vec_del(int k, evec_t *v) { ((void (TC *)(evec_t *))FN(k, 0x47bf9d))(v); }
static char rec(int k, uint8_t *m, evec_t *l) { return ((char (TC *)(uint8_t *, evec_t *))FN(k, 0x551f8f))(m, l); }

/* the effect wrapper 0x550dd1 / 0x551215 read: vt+0x28 "ready", +0x14 -> {+4 effect, +0xc defaults} */
static char TC w_ready(void *w) { (void)w; return 1; }
static void TC w_load(void *w) { (void)w; }
static void *w_vt[16];
typedef struct { void **vt; uint8_t pad[0x10]; uint8_t *res; } wrap_t;
typedef struct { wrap_t w; uint8_t res[0x40]; uint8_t mat[0x80]; evec_t in; } world_t;
static world_t W[2];

static const struct { const char *n; int type; } P[] = {
    {"ColorAmbient", 4}, {"ColorDiffuse", 4}, {"ColorSpecular", 4}, {"Shininess", 2}, {"ColorEmissive", 4},
    {"Opacity", 2}, {"DepthWriteEnable", 7}, {"HouseColorEnable", 7}, {"SecondaryTextureBlendMode", 6},
    {"AlphaTestEnable", 7}, {"CullingEnable", 7}, {"BlendMode", 6}, {"NumTextures", 6}, {"Texture_0", 1},
    {"Texture_1", 1}};
enum { NP = sizeof P / sizeof P[0] };
static void fill(int k, entry_t *e, int i, uint32_t seed)
{
    entry_new(k, e, P[i].n, P[i].type);
    for (int c = 0; c < 4; c++) e->v[c] = (float)((seed >> (c * 3)) & 7) / 7.0f;
    e->i = (int32_t)(seed % 5); e->b = (uint8_t)(seed & 1);
    if (P[i].type == 1)
        ((void (TC *)(uint32_t *, const char *))FN(k, 0x4050e6))(&e->tex, i == 13 ? "exlight01.tga" : "exground01.tga");
}
static void build(int k, void *fx, H tech, int with_tex1)
{
    world_t *w = &W[k];
    memset(w, 0, sizeof *w);
    w->w.vt = w_vt; w->w.res = w->res;
    U32(w->res, 4) = (uint32_t)(uintptr_t)fx;
    evec_t *def = (evec_t *)(w->res + 0xc);
    for (int i = 0; i < NP; i++) {                     /* the effect's defaults */
        entry_t e; fill(k, &e, i, 0x5a5a + i * 77); vec_push(k, def, &e); entry_del(k, &e);
    }
    ((void (TC *)(uint8_t *))FN(k, 0x551f2c))(w->mat);
    U32(w->mat, 8) = (uint32_t)(uintptr_t)&w->w;
    U32(w->mat, 0x20) = (uint32_t)(uintptr_t)tech;
    for (int i = 0; i < NP - !with_tex1; i++) {        /* the converted material's own values */
        entry_t e; fill(k, &e, i, 0x1234 + i * 1013); vec_push(k, &w->in, &e); entry_del(k, &e);
    }
}
static double rec_us[2]; static long rec_n[2];
/* one colour set as 0x50e040 / 0x50e244 / 0x50e413 do it: copy the material's list, set one
 * parameter by name, record */
static char set_colour(int k, int which, const float *v)
{
    static const struct { const char *n; int type; } S[3] = {{"ColorEmissive", 4}, {"Opacity", 2}, {"ColorDiffuse", 4}};
    world_t *w = &W[k];
    evec_t tmp; vec_copy(k, &tmp, (evec_t *)(w->mat + 0xc));
    entry_t e; entry_new(k, &e, S[which].n, S[which].type);
    memcpy(e.v, v, 16);
    vec_set(k, &tmp, &e);
    uint64_t t0 = now_us();
    char r = rec(k, w->mat, &tmp);
    rec_us[k] += now_us() - t0; rec_n[k]++;
    entry_del(k, &e); vec_del(k, &tmp);
    return r;
}
static H wrong_param;
static BOOL SC wrong_used(void *fx, H p, H t) { BOOL v = gp_fxu_isused(fx, p, t); return p == wrong_param ? !v : v; }
/* the two materials after the same call: list, texture list, block */
static int same_material(char r0, char r1)
{
    if (r0 != r1) return -1;
    uint8_t *a = W[0].mat, *b = W[1].mat;
    evec_t *la = (evec_t *)(a + 0xc), *lb = (evec_t *)(b + 0xc);
    if (la->e - la->b != lb->e - lb->b) return -2;
    for (entry_t *x = la->b, *y = lb->b; x < la->e; x++, y++)
        if (strcmp(str(x->name), str(y->name)) || x->type != y->type || strcmp(str(x->tex), str(y->tex)) ||
            memcmp(x->v, y->v, 16) || x->i != y->i || x->b != y->b) return -3;
    uint32_t *ta = (uint32_t *)(uintptr_t)U32(a, 0x28), *tae = (uint32_t *)(uintptr_t)U32(a, 0x2c);
    uint32_t *tb = (uint32_t *)(uintptr_t)U32(b, 0x28), *tbe = (uint32_t *)(uintptr_t)U32(b, 0x2c);
    if (tae - ta != tbe - tb || memcmp(ta, tb, (size_t)(tae - ta) * 4)) return -4;
    uint8_t *ba = (uint8_t *)(uintptr_t)U32(a, 0x24), *bb = (uint8_t *)(uintptr_t)U32(b, 0x24);
    if (!ba != !bb) return -5;
    if (ba) {                                          /* Wine's d3dx_parameter_block: magic, effect, list, size, offset, buffer */
        if (memcmp(ba, "@!#\xfe", 4) || memcmp(bb, "@!#\xfe", 4)) return -6;
        if (U32(ba, 4) != U32(bb, 4) || U32(ba, 0x14) != U32(bb, 0x14)) return -7;
        if (memcmp((void *)(uintptr_t)U32(ba, 0x18), (void *)(uintptr_t)U32(bb, 0x18), U32(ba, 0x14))) return -8;
    }
    return 1;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    SetUnhandledExceptionFilter(crash);
    if (!VirtualAlloc((void *)0xbd0000, 0xe10000 - 0xbd0000, MEM_RESERVE, PAGE_READWRITE)) {
        printf("cannot reserve the image's data range\nFAIL\n"); return 2;
    }
    const char *path = argc > 1 ? argv[1] : orig_default_path();
    if (orig_load(path)) return 2;
    FILE *f = fopen(path, "rb");
    if (!f) return 2;
    fseek(f, 0, SEEK_END); exe_len = ftell(f); fseek(f, 0, SEEK_SET);
    exe = malloc(exe_len);
    if (fread(exe, 1, exe_len, f) != (size_t)exe_len) return 2;
    fclose(f);
    if (orig_map_at(0xbd0000, 0x1b9000, 0) || orig_map_at(0xd89000, 0x81000, 0)) return 2;
    for (int k = 0; k < 2; k++)
        if (!(off[k] = orig_reserve_image()) || orig_map_at(0x401000, 0x7cf000, off[k])) return 2;
    if (fill_imports()) { printf("FAIL\n"); return 2; }
    printf("code pointers in .rdata moved to the unpatched copy: %d\n", relocate_code_pointers());
    *AT(0xdc5e44) = (uint32_t)(uintptr_t)t_alloc; *AT(0xdc5e3c) = (uint32_t)(uintptr_t)t_free;
    w_vt[0x28 / 4] = (void *)w_ready; w_vt[0x2c / 4] = (void *)w_load;

    WNDCLASSA wc = {0}; wc.lpfnWndProc = DefWindowProcA; wc.lpszClassName = "t_spell2fx"; wc.hInstance = GetModuleHandleA(NULL);
    RegisterClassA(&wc);
    HWND hw = CreateWindowA("t_spell2fx", "t_spell2fx", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, NULL, NULL, wc.hInstance, NULL);
    HMODULE d9 = LoadLibraryA("d3d9.dll");             /* loaded now: linked, it would sit in the image's range */
    typedef IDirect3D9 *(WINAPI *d3dcreate_t)(UINT);
    d3dcreate_t d3dcreate = d9 ? (d3dcreate_t)(void *)GetProcAddress(d9, "Direct3DCreate9") : NULL;
    IDirect3D9 *d3d = d3dcreate ? d3dcreate(D3D_SDK_VERSION) : NULL;
    D3DPRESENT_PARAMETERS pp = {0};
    pp.Windowed = TRUE; pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.BackBufferFormat = D3DFMT_UNKNOWN; pp.hDeviceWindow = hw;
    HRESULT hr = d3d ? IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, hw, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev) : E_FAIL;
    if (!dev) { printf("no D3D9 device (%08lx)\nFAIL\n", hr); return 2; }
    if (load_big(path)) { printf("FAIL\n"); return 2; }
    unsigned short cw = 0x007f;                          /* the game's FPU mode: 24-bit, nearest */
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));

    gp_va_offset = off[1];
    int ok = gp_patch_fxparamused();
    gp_va_offset = 0;
    uint32_t site = call_target(0x55207f + off[1]);
    ok = ok && site == (uint32_t)(uintptr_t)gp_fxu_isused && *(uint8_t *)(uintptr_t)(0x55207f + off[0]) == 0xff
         && *AT(GP_FXU_IAT) == (uint32_t)(uintptr_t)gp_fxu_create_mem && *AT(GP_FXU_IAT + 4) == (uint32_t)(uintptr_t)gp_fxu_create_file;
    verdict(!ok, "[0] fxparamused: %s (0x55207f -> %08x, IAT -> %08x %08x)\n", ok ? "applied" : "NOT applied", site,
            *AT(GP_FXU_IAT), *AT(GP_FXU_IAT + 4));
    if (!ok) { printf("FAIL\n"); return 1; }
    for (int k = 0; k < 2; k++) jmp_to(0x532875 + off[k], (void *)tex_load);
    create_t thunk = (create_t)(uintptr_t)(0xa3ed20 + off[1]);   /* the game's way in: thunk -> IAT */

    /* [1] */
    LONG g0 = gp_fxu_gen;
    int made = create_all(thunk);
    long np, bad = check_pairs(&np, 0);
    LONG calls = gp_fxu_stats[0], hits = gp_fxu_stats[1];
    release_all();
    LONG g1 = gp_fxu_gen;
    int made2 = create_all(thunk);
    long np2, bad2 = check_pairs(&np2, 0);
    LONG g2 = gp_fxu_gen;
    verdict(bad || bad2 || made != nfx || made2 != nfx || g1 - g0 != made || g2 - g1 != made2 || hits < calls / 2,
            "[1] %d effects, %ld parameter/technique pairs x 3, twice (all effects released and created again "
            "between): %ld + %ld mismatches; cache cleared at each creation (%ld + %ld); %ld of %ld answers from the cache\n",
            made, np, bad, bad2, (long)(g1 - g0), (long)(g2 - g1), (long)hits, (long)calls);

    /* [2] the game's 0x551f8f, original against patched, on DefaultW3D */
    fx_t *dw = NULL;
    for (int i = 0; i < nfx; i++) if (!_stricmp(fxs[i].name, "defaultw3d.fxo")) dw = &fxs[i];
    if (!dw || !dw->fx) { printf("no DefaultW3D effect\nFAIL\n"); return 1; }
    long mism = 0, calls2 = 0, recorded = 0;
    double tset[2][MAXT] = {{0}}; long nset[MAXT] = {0};
    for (int ti = 0; ti < dw->nt; ti++) {
        H tech = dw->t[ti];
        for (int tex1 = 0; tex1 < 2; tex1++) {
            for (int k = 0; k < 2; k++) build(k, dw->fx, tech, tex1);
            char r0 = rec(0, W[0].mat, &W[0].in), r1 = rec(1, W[1].mat, &W[1].in);
            calls2++; recorded += U32(W[0].mat, 0x24) != 0;
            { int sm = same_material(r0, r1); if (sm != 1) { if (mism++ < 3) printf("  MISMATCH (%d): material creation, technique %d\n", sm, ti); } }
            rs = 0x9e3779b9u + ti * 31 + tex1;
            for (int frame = 0; frame < 24; frame++) {
                float col[3][4];
                for (int s = 0; s < 3; s++)
                    for (int c = 0; c < 4; c++) col[s][c] = (rnd() % 4 == 0 && frame) ? col[s][c] : (float)(rnd() % 1000) / 999.0f;
                for (int pass = 0; pass < 2; pass++)
                    for (int s = 0; s < 3; s++) {
                        uint64_t t0 = now_us();
                        char a = set_colour(0, s, col[s]);
                        uint64_t t1 = now_us();
                        char b = set_colour(1, s, col[s]);
                        uint64_t t2 = now_us();
                        if (frame) { tset[0][ti] += t1 - t0; tset[1][ti] += t2 - t1; nset[ti]++; }
                        calls2++; recorded += U32(W[0].mat, 0x24) != 0;
                        { int sm = same_material(a, b); if (sm != 1) { if (mism++ < 3) printf("  MISMATCH (%d): technique %d frame %d pass %d set %d\n", sm, ti, frame, pass, s); } }
                    }
            }
        }
    }
    verdict(mism || recorded < calls2 / 2, "[2] the game's 0x551f8f on DefaultW3D, %d techniques: %ld records "
            "(%ld with a block), original vs patched copy: %ld mismatches in return value, parameter list, "
            "texture list or recorded block; texture loads %ld\n", dw->nt, calls2, recorded, mism, tex_loads);

    /* [3] sensitivity: the patched copy's site answering one parameter wrongly must show in [2]'s check */
    H wrong_p = ((H (SC *)(void *, H, const char *))VT(dw->fx, 0x24))(dw->fx, NULL, "ColorEmissive");
    for (int k = 0; k < 2; k++) build(k, dw->fx, dw->t[0], 1);
    rec(0, W[0].mat, &W[0].in); rec(1, W[1].mat, &W[1].in);
    uint8_t *site1 = (uint8_t *)(uintptr_t)(0x55207f + off[1]);
    uint8_t keep[5]; memcpy(keep, site1, 5);
    wrong_param = wrong_p;
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)wrong_used - (uint32_t)(uintptr_t)(site1 + 5)); memcpy(site1 + 1, &rel, 4);
    static const float c3[4] = {0.25f, 0.5f, 0.75f, 1.0f};
    char sa = set_colour(0, 0, c3), sb = set_colour(1, 0, c3);
    int caught2 = same_material(sa, sb) != 1;
    memcpy(site1, keep, 5);
    verdict(!caught2, "[3a] sensitivity: the patched copy answering \"ColorEmissive unused\" is %s by [2]'s check\n", caught2 ? "caught" : "NOT caught");
    /* [3] sensitivity */
    long np3, bad3 = check_pairs(&np3, 1);
    verdict(bad3 == 0, "[3b] sensitivity: one wrong cached answer is %s\n", bad3 ? "caught" : "NOT caught");

    /* [4] time */
    double td = 0, tc = 0; long n4 = 0;
    for (int rep = 0; rep < 3; rep++)
        for (int a = 0; a < dw->np; a++) {
            uint64_t t0 = now_us();
            for (int b = 0; b < dw->nt; b++) direct(dw->fx, dw->p[a], dw->t[b]);
            uint64_t t1 = now_us();
            for (int b = 0; b < dw->nt; b++) gp_fxu_isused(dw->fx, dw->p[a], dw->t[b]);
            td += t1 - t0; tc += now_us() - t1; n4 += dw->nt;
        }
    printf("[4] IsParameterUsed on DefaultW3D (%d parameters x %d techniques): %.2f us direct, %.3f us cached\n",
           dw->np, dw->nt, td / n4, tc / n4);
    for (int ti = 0; ti < dw->nt; ti++) {
        typedef struct { const char *Name; UINT Passes, Annotations; } TDESC;
        TDESC d = {0}; ((HRESULT (SC *)(void *, H, TDESC *))VT(dw->fx, 0x14))(dw->fx, dw->t[ti], &d);
        printf("    technique %-18s one colour set (list copy, merge, record): %.1f -> %.1f us\n", d.Name ? d.Name : "?",
               tset[0][ti] / nset[ti], tset[1][ti] / nset[ti]);
    }
    printf("    of which the record 0x551f8f itself (all techniques): %.1f -> %.1f us\n", rec_us[0] / rec_n[0], rec_us[1] / rec_n[1]);
    release_all();
    printf("%s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
