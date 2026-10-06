/* The game's terrain-tile bake on a fake WorldHeightMap (see t_terrain.h). WorldHeightMap fields the
 * bake reads (RotWK 2.02): +0x08 width, +0x0c height, +0x20 cells, +0x98 short tile[], +0x9c int
 * blend[], +0xa0 int cliff[], +0xa4 int extra blend[], +0xb0 TileData *source[0x1000] (tile / 4),
 * +0x80b0 / +0x80b4 the 16-byte blend entries (begin, end), +0x120e0 / +0x120e4 the cliff lookup's
 * origin. TileData: +0x2ab4 its normal-map companion. TheGlobalData (*0xde4364): +0x44 3-way blends,
 * +0x49 normal maps. The game's allocator: *0xdc5e44 (size, kind, 0), *0xdc5e3c (pointer, kind). */
#include "t_terrain.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TD_BYTES  (0x2ac0 + 32768)        /* TileData + terrain32's shadow (21.5 KB) with room */
#define SH_MAGIC  0x32335354u
static uint32_t off;
static uint8_t globals[0x200];

static void *__cdecl g_new(size_t n, int kind, int z) { (void)kind; (void)z; return calloc(1, n ? n : 1); }
static void __cdecl g_del(void *p, int kind) { (void)kind; free(p); }

/* ---- scenes --------------------------------------------------------------------------------- */
static int rd(FILE *f, void *p, size_t n) { return fread(p, 1, n, f) == n ? 0 : 1; }

int t_scene_load(t_scene *s, const char *path)
{
    memset(s, 0, sizeof *s);
    FILE *f = fopen(path, "rb");
    if (!f) return 1;
    char tag[4]; uint32_t ver, u;
    int32_t hdr[4];
    if (rd(f, tag, 4) || memcmp(tag, "TSCN", 4) || rd(f, &ver, 4) || ver != 1 || rd(f, hdr, 16)) { fclose(f); return 1; }
    s->width = hdr[0]; s->height = hdr[1]; s->border = hdr[2]; s->n = hdr[3];
    int16_t *cliff = malloc(2 * s->n);
    s->tile = malloc(2 * s->n); s->blend = malloc(2 * s->n); s->extra = malloc(2 * s->n);
    if (rd(f, s->tile, 2 * s->n) || rd(f, s->blend, 2 * s->n) || rd(f, s->extra, 2 * s->n) || rd(f, cliff, 2 * s->n) ||
        rd(f, &u, 4) || fseek(f, (long)u * s->height, SEEK_CUR) || rd(f, &u, 4)) { fclose(f); return 1; }
    free(cliff);
    s->nblend = (int)u;
    s->be = calloc(u + 1, sizeof *s->be);
    for (uint32_t i = 0; i < u; i++) {
        uint8_t e[16];                    /* i32 blend tile, 6 flags, 2 spare, i32 custom edge class */
        if (rd(f, e, 16)) { fclose(f); return 1; }
        memcpy(&s->be[i].ndx, e, 4); memcpy(s->be[i].f, e + 4, 6); memcpy(&s->be[i].custom, e + 12, 4);
    }
    if (rd(f, &u, 4)) { fclose(f); return 1; }
    s->ntiles = (int)u;
    s->src = calloc(u + 1, sizeof *s->src);
    for (uint32_t i = 0; i < u; i++) {
        uint32_t h[2];
        if (rd(f, h, 8)) { fclose(f); return 1; }
        s->src[i].slot = (int32_t)h[0]; s->src[i].hasnrm = (int)h[1];
        s->src[i].bgra = malloc(16384);
        if (rd(f, s->src[i].bgra, 16384)) { fclose(f); return 1; }
        if (h[1]) { s->src[i].nrm = malloc(16384); if (rd(f, s->src[i].nrm, 16384)) { fclose(f); return 1; } }
    }
    fclose(f);
    return 0;
}

static uint32_t rs;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }

void t_scene_synth(t_scene *s, uint32_t seed)
{
    memset(s, 0, sizeof *s);
    rs = seed | 1;
    s->width = s->height = 64; s->n = 64 * 64;
    s->tile = malloc(2 * s->n); s->blend = calloc(s->n, 2); s->extra = calloc(s->n, 2);
    enum { NT = 24 };
    s->ntiles = NT;
    s->src = calloc(NT, sizeof *s->src);
    for (int t = 0; t < NT; t++) {           /* smooth gradients with grain: 8-bit detail the 5-bit loses */
        s->src[t].slot = t; s->src[t].hasnrm = t & 1;
        s->src[t].bgra = malloc(16384);
        int r0 = rnd() % 200, g0 = rnd() % 200, b0 = rnd() % 200;
        for (int i = 0; i < 4096; i++) {
            int x = i & 63, y = i >> 6, gr = (int)(rnd() % 7) - 3;
            uint8_t *p = s->src[t].bgra + 4 * i;
            p[0] = (uint8_t)(b0 + x / 2 + gr + 3); p[1] = (uint8_t)(g0 + y / 3 + gr + 3); p[2] = (uint8_t)(r0 + (x + y) / 4 + 3); p[3] = 0;
        }
        if (t & 1) {
            s->src[t].nrm = malloc(16384);
            for (int i = 0; i < 4096; i++) { uint8_t *p = s->src[t].nrm + 4 * i; p[0] = 0; p[1] = (uint8_t)(100 + rnd() % 56); p[2] = (uint8_t)(100 + (i & 63)); p[3] = 0; }
        }
    }
    s->nblend = 40;
    s->be = calloc(s->nblend + 1, sizeof *s->be);
    for (int i = 1; i < s->nblend; i++) {
        s->be[i].ndx = (int32_t)(rnd() % (NT * 4));
        int kind = (int)(rnd() % 6);
        s->be[i].f[kind < 2 ? kind : kind < 4 ? 2 + (kind & 1) : 2 + (kind & 1)] = 1;
        if (kind >= 4) s->be[i].f[5] = 1;
        s->be[i].f[4] = (uint8_t)(rnd() & 1);
        s->be[i].custom = -1;
    }
    for (int i = 0; i < s->n; i++) {
        s->tile[i] = (int16_t)(rnd() % (NT * 4));
        if (rnd() % 3 == 0) s->blend[i] = (int16_t)(1 + rnd() % (s->nblend - 1));
        if (rnd() % 7 == 0) s->extra[i] = (int16_t)(1 + rnd() % (s->nblend - 1));
    }
}

/* ---- the world ------------------------------------------------------------------------------ */
uint32_t t_world_init(const char *exe)
{
    if (!VirtualAlloc((void *)0xbd0000, 0xe10000 - 0xbd0000, MEM_RESERVE, PAGE_READWRITE)) { printf("cannot reserve the data range\n"); return 0; }
    if (orig_load(exe) || orig_map_at(0xbd0000, 0x1b9000, 0)) return 0;
    if (!VirtualAlloc((void *)0xd89000, 0xe10000 - 0xd89000, MEM_COMMIT, PAGE_READWRITE)) { printf("cannot commit .bss\n"); return 0; }
    off = orig_reserve_image();
    if (!off || orig_map_at(0x401000, 0x7cf000, off)) return 0;
    HMODULE dx = LoadLibraryA("d3dx9_27.dll");
    void *ft = dx ? (void *)GetProcAddress(dx, "D3DXFilterTexture") : NULL, *ls = dx ? (void *)GetProcAddress(dx, "D3DXLoadSurfaceFromMemory") : NULL;
    if (!ft || !ls) { printf("cannot load d3dx9_27.dll\n"); return 0; }
    *(uint32_t *)0xbd0a20 = (uint32_t)(uintptr_t)ft;
    *(uint32_t *)0xbd0a1c = (uint32_t)(uintptr_t)ls;
    HMODULE crt = LoadLibraryA("msvcrt.dll");          /* the CRT imports the bake code calls */
    *(uint32_t *)0xbd06c8 = (uint32_t)(uintptr_t)GetProcAddress(crt, "memcpy");
    *(uint32_t *)0xbd06c4 = (uint32_t)(uintptr_t)GetProcAddress(crt, "memset");
    *(uint32_t *)0xdc5e44 = (uint32_t)(uintptr_t)g_new;
    *(uint32_t *)0xdc5e3c = (uint32_t)(uintptr_t)g_del;
    globals[0x44] = 1; globals[0x49] = 1;
    *(uint32_t *)0xde4364 = (uint32_t)(uintptr_t)globals;
    gp_va_offset = off;
    int ok = gp_patch_mipfilter() && gp_patch_terrainbox() && gp_patch_terrain32();
    return ok ? off : 0;
}

#define HM(hm, o, T) (*(T *)((uint8_t *)(hm) + (o)))
typedef void (__attribute__((thiscall)) *ctor_fn)(void *);

static void *new_td(const uint8_t *bgra)
{
    void *td = calloc(1, TD_BYTES);
    ((ctor_fn)(uintptr_t)(0x5111fd + off))(td);
    static uint8_t flat[256];             /* the loader's flat normal row (B 0, G 0x7f, R 0x7f), pitch 0 */
    for (int i = 0; i < 256; i += 4) { flat[i + 1] = 0x7f; flat[i + 2] = 0x7f; }
    if (bgra) gp_t32_fill(td, bgra, 256); else gp_t32_fill(td, flat, 0);
    return td;
}

void *t_world_build(const t_scene *s)
{
    uint8_t *hm = calloc(1, 0x12100);
    HM(hm, 0x08, int) = s->width; HM(hm, 0x0c, int) = s->height; HM(hm, 0x20, int) = s->n;
    int16_t *tile = malloc(2 * s->n);
    int *blend = malloc(4 * s->n), *extra = malloc(4 * s->n), *cliff = calloc(s->n, 4);
    memcpy(tile, s->tile, 2 * s->n);
    for (int i = 0; i < s->n; i++) { blend[i] = s->blend[i]; extra[i] = s->extra[i]; }
    HM(hm, 0x98, int16_t *) = tile; HM(hm, 0x9c, int *) = blend; HM(hm, 0xa0, int *) = cliff; HM(hm, 0xa4, int *) = extra;
    uint8_t *be = calloc(s->nblend + 1, 16);
    for (int i = 0; i < s->nblend; i++) {
        memcpy(be + 16 * i, &s->be[i].ndx, 4); memcpy(be + 16 * i + 4, s->be[i].f, 6); memcpy(be + 16 * i + 12, &s->be[i].custom, 4);
    }
    HM(hm, 0x80b0, uint8_t *) = be; HM(hm, 0x80b4, uint8_t *) = be + 16 * s->nblend;
    void **src = (void **)(hm + 0xb0);
    for (int i = 0; i < s->ntiles; i++) {
        if (s->src[i].slot < 0 || s->src[i].slot >= 0x1000) continue;
        void *td = new_td(s->src[i].bgra);
        HM(td, 0x2ab4, void *) = new_td(s->src[i].hasnrm ? s->src[i].nrm : NULL);
        src[s->src[i].slot] = td;
    }
    return hm;
}

static uint32_t *sh(void *td) { return (uint32_t *)((uint8_t *)td + 0x2ac0); }
static void each_td(void *hm, void (*fn)(void *td))
{
    void **src = (void **)((uint8_t *)hm + 0xb0);
    for (int i = 0; i < 0x1000; i++)
        if (src[i]) {
            fn(src[i]);
            void *n = HM(src[i], 0x2ab4, void *);
            if (n) fn(n);
        }
}
static void sh_on(void *td) { sh(td)[0] = SH_MAGIC; }
static void sh_off(void *td) { sh(td)[0] = 0; }
void t_world_set_shadows(void *hm, int on) { each_td(hm, on ? sh_on : sh_off); }

static void from16(void *td)
{
    uint32_t *l = sh(td) + 4;
    for (int w = 64; w >= 16; l += w * w, w /= 2) {
        const uint16_t *q = (const uint16_t *)((uint8_t *)td + (w == 64 ? 8 : w == 32 ? 0x2008 : 0x2808));
        for (int i = 0; i < w * w; i++) {
            uint32_t r = q[i] >> 10 & 31, g = q[i] >> 5 & 31, b = q[i] & 31;
            l[i] = (r << 3 | r >> 2) << 16 | (g << 3 | g >> 2) << 8 | (b << 3 | b >> 2);
        }
    }
    sh(td)[0] = SH_MAGIC;
}
void t_world_shadows_from16(void *hm) { each_td(hm, from16); }

void t_world_shadows_real(void *hm, const t_scene *s)
{
    void **src = (void **)((uint8_t *)hm + 0xb0);
    static uint8_t flat[256];
    for (int i = 0; i < 256; i += 4) { flat[i + 1] = 0x7f; flat[i + 2] = 0x7f; }
    for (int i = 0; i < s->ntiles; i++) {
        void *td = s->src[i].slot >= 0 && s->src[i].slot < 0x1000 ? src[s->src[i].slot] : NULL;
        if (!td) continue;
        gp_t32_shadow_fill(td, s->src[i].bgra, 256);
        void *n = HM(td, 0x2ab4, void *);
        if (n) { if (s->src[i].hasnrm) gp_t32_shadow_fill(n, s->src[i].nrm, 256); else gp_t32_shadow_fill(n, flat, 0); }
    }
}

/* ---- the bake ------------------------------------------------------------------------------- */
static char __attribute__((thiscall)) tc_ready(void *self) { (void)self; return 1; }
typedef int (__attribute__((thiscall)) *bake_fn)(void *holder, void *hm, int x, int y, int cells, int ppc, int layer);

gp_fake_tex *t_bake(void *hm, D3DFORMAT fmt, int x0, int y0, int cells, int ppc, int layer, double *ms)
{
    UINT w = (UINT)(cells * ppc);
    gp_fake_tex *t = gp_fake_create_pad(w, w, 3, fmt, fmt == D3DFMT_X8R8G8B8 ? 4 : 2, 0);
    static void *vt[16];
    vt[0x28 / 4] = (void *)tc_ready;
    struct { void **vtbl; uint8_t pad[0x10]; void *wrap; } tc = {vt, {0}, NULL};
    struct { uint8_t pad[8]; IDirect3DBaseTexture9 *tex; } wrap = {{0}, gp_fake_base(t)};
    tc.wrap = &wrap;
    void *holder = &tc;
    uint64_t t0 = now_us();
    if (fmt == D3DFMT_X8R8G8B8) gp_t32_bake(&holder, hm, x0, y0, cells, ppc, layer);
    else ((bake_fn)(uintptr_t)((fmt == D3DFMT_DXT1 ? 0x4eee64 : 0x4eec82) + off))(&holder, hm, x0, y0, cells, ppc, layer);
    if (ms) *ms = (now_us() - t0) / 1000.0;
    return t;
}

/* ---- pixels and PNG ------------------------------------------------------------------------- */
uint32_t *t_level_rgb(gp_fake_tex *t, UINT l, UINT *pw, UINT *ph)
{
    UINT w, h, p;
    uint8_t *b = gp_fake_bits(t, l, &w, &h, &p);
    if (!b) return NULL;
    uint32_t *o = calloc((size_t)w * h, 4);
    D3DSURFACE_DESC d;
    IDirect3DTexture9_GetLevelDesc((IDirect3DTexture9 *)gp_fake_base(t), 0, &d);
    for (UINT y = 0; y < h; y++)
        for (UINT x = 0; x < w; x++) {
            if (d.Format == D3DFMT_X8R8G8B8) { o[y * w + x] = ((uint32_t *)(b + y * p))[x] & 0xffffff; continue; }
            if (d.Format != D3DFMT_A1R5G5B5) continue;
            uint32_t v = ((uint16_t *)(b + y * p))[x], r = v >> 10 & 31, g = v >> 5 & 31, bl = v & 31;
            o[y * w + x] = (r << 3 | r >> 2) << 16 | (g << 3 | g >> 2) << 8 | (bl << 3 | bl >> 2);
        }
    if (d.Format == D3DFMT_DXT1)
        for (UINT by = 0; by < (h + 3) / 4; by++)
            for (UINT bx = 0; bx < (w + 3) / 4; bx++) {
                const uint8_t *k = b + by * p + bx * 8;
                unsigned c0 = k[0] | k[1] << 8, c1 = k[2] | k[3] << 8, col[4][3];
                for (int i = 0; i < 2; i++) {
                    unsigned c = i ? c1 : c0, r = c >> 11, g = c >> 5 & 63, bl = c & 31;
                    col[i][0] = r << 3 | r >> 2; col[i][1] = g << 2 | g >> 4; col[i][2] = bl << 3 | bl >> 2;
                }
                for (int j = 0; j < 3; j++) {
                    col[2][j] = c0 > c1 ? (2 * col[0][j] + col[1][j]) / 3 : (col[0][j] + col[1][j]) / 2;
                    col[3][j] = c0 > c1 ? (col[0][j] + 2 * col[1][j]) / 3 : 0;
                }
                uint32_t bits = k[4] | k[5] << 8 | k[6] << 16 | (uint32_t)k[7] << 24;
                for (UINT y = 0; y < 4 && by * 4 + y < h; y++)
                    for (UINT x = 0; x < 4 && bx * 4 + x < w; x++) {
                        unsigned *c = col[bits >> (2 * (4 * y + x)) & 3];
                        o[(by * 4 + y) * w + bx * 4 + x] = c[0] << 16 | c[1] << 8 | c[2];
                    }
            }
    if (pw) *pw = w;
    if (ph) *ph = h;
    return o;
}

static uint32_t crc_tab[256];
static uint32_t crc(uint32_t c, const uint8_t *p, size_t n)
{
    if (!crc_tab[1]) for (uint32_t i = 0; i < 256; i++) { uint32_t v = i; for (int k = 0; k < 8; k++) v = v & 1 ? 0xedb88320u ^ v >> 1 : v >> 1; crc_tab[i] = v; }
    c = ~c;
    while (n--) c = crc_tab[(c ^ *p++) & 255] ^ c >> 8;
    return ~c;
}
static void be32(uint8_t *p, uint32_t v) { p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16); p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v; }
static void chunk(FILE *f, const char *type, const uint8_t *d, uint32_t n)
{
    uint8_t h[8]; be32(h, n); memcpy(h + 4, type, 4);
    fwrite(h, 1, 8, f); if (n) fwrite(d, 1, n, f);
    uint32_t c = crc(crc(0, h + 4, 4), d, n); be32(h, c); fwrite(h, 1, 4, f);
}

/* RGB PNG, stored (uncompressed) deflate blocks */
int t_png(const char *path, const uint32_t *rgb, UINT w, UINT h)
{
    FILE *f = fopen(path, "wb");
    if (!f) return 1;
    static const uint8_t sig[8] = {0x89, 'P', 'N', 'G', 13, 10, 26, 10};
    fwrite(sig, 1, 8, f);
    uint8_t ih[13]; be32(ih, w); be32(ih + 4, h); ih[8] = 8; ih[9] = 2; ih[10] = ih[11] = ih[12] = 0;
    chunk(f, "IHDR", ih, 13);
    size_t raw = (size_t)h * (1 + 3 * w), nb = (raw + 65534) / 65535;
    uint8_t *r = malloc(raw), *z = malloc(raw + 5 * nb + 6);
    for (UINT y = 0; y < h; y++) {
        uint8_t *o = r + y * (1 + 3 * w);
        *o++ = 0;
        for (UINT x = 0; x < w; x++) { uint32_t v = rgb[y * w + x]; *o++ = (uint8_t)(v >> 16); *o++ = (uint8_t)(v >> 8); *o++ = (uint8_t)v; }
    }
    size_t zn = 0; uint32_t a = 1, b = 0;
    z[zn++] = 0x78; z[zn++] = 0x01;
    for (size_t i = 0; i < raw; i += 65535) {
        size_t n = raw - i < 65535 ? raw - i : 65535;
        z[zn++] = i + n >= raw; z[zn++] = (uint8_t)n; z[zn++] = (uint8_t)(n >> 8); z[zn++] = (uint8_t)~n; z[zn++] = (uint8_t)(~n >> 8);
        memcpy(z + zn, r + i, n); zn += n;
    }
    for (size_t i = 0; i < raw; i++) { a = (a + r[i]) % 65521; b = (b + a) % 65521; }
    be32(z + zn, b << 16 | a); zn += 4;
    chunk(f, "IDAT", z, (uint32_t)zn);
    chunk(f, "IEND", NULL, 0);
    free(r); free(z);
    return fclose(f) != 0;
}
