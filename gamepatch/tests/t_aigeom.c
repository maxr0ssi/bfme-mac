/* t_aigeom: aigeom (p_aigeom.c) against the original distance type 4 (0xa3c7d0), both run from the
 * exe's bytes. Two relocated copies of the partition code (0xa39000-0xa3e000: the type-4 function,
 * iterateObjectsInRange, the walk), the geometry code (0xad0000-0xad6000: GeometryInfo::set,
 * calcBoundingStuff, bfmeIntersects and its shape tests), GeometryInfo's constructor, the string and
 * allocator code they call: copy A untouched, copy B patched by the installer (aigeom, and scantree as
 * the game runs it). Object geometries are built by the game's own GeometryInfo constructor (one
 * shape), then given extra shapes (offsets, mixed types, inactive ones). Mock objects log every getter
 * call (geometry, angle, position, getObject). Data, the type-4 function's static sphere included, is
 * shared at its real address.
 *   [0] the patch applies to the original bytes (relocated copy)
 *   [1] single calls in batches: B runs a batch, then A runs the same batch; per call the result bits,
 *       the getter log and the static sphere's bytes after the call must match. Units (cylinders),
 *       spheres, buildings (boxes), multi-shape geometries, odd ones (negative or special sizes, other
 *       types, no shapes), any angle (huge, NaN), points near the reach boundary, radii repeated or
 *       changed between calls (the bound recalculation), special values
 *   [2] the same in seven other x87 modes and three other MXCSR modes (the original runs)
 *   [3] whole range queries 0xa3c4e0 with type 4 over a world of 300-2,500 objects in 21 quadtrees
 *       (the game's linkNode), 0-2 filters: same result vectors and getter logs
 *   [4] sensitivity: three deliberate bugs must be caught (and the rounding margin's use is shown)
 *   [5] two memory layouts: the same objects with their geometries and shape arrays copied to other
 *       addresses give the same results and call logs
 *   [6] time: the fortress spikes' scan (r 150, a fortress area of 200 objects in a 1,300-object world)
 *       and a splash hit (r 40) inside a 1,000-unit battle
 * usage: t_aigeom.exe <path to lotrbfme2ep1.exe 2.02> [thousands of calls] */
#include "orig.h"
#include "p_ai.h"
#include "gp_scale.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>

static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs = 0x2545f491;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
static float rf(float lo, float hi) { return lo + (hi - lo) * (rnd() >> 8) / 16777216.0f; }
static float fb(uint32_t u) { float f; memcpy(&f, &u, 4); return f; }
static uint32_t bits(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }
static float special(void)
{
    static const uint32_t sp[] = {0x7f800000, 0xff800000, 0x7fc00000, 0x00000001, 0x80000000, 0, 0x5f000000,
                                  0x1e800000, 0x7f7fffff, 0x00800000, 0x4b800000, 0xcb000000};
    return fb(sp[rnd() % 12]);
}

/* ---- the mock objects ------------------------------------------------------------------ */
enum { MAXOBJ = 3000, LOGN = 1 << 18, L = 7, NCELL = 1 << L, NNODE = (((1 << (2 * L + 2)) - 1) / 3) };
typedef struct { void **vt; float pos[3]; float ang; uint8_t *geom; int cat; void *obj; int idx; } mobj;
typedef struct { uint32_t w[12]; } mentry;
typedef struct { void **vt; void *next; uint32_t mask; int rate; int id; } mfilt;
static mobj *objs; static mentry *ents;
static uint32_t *logbuf, *loga; static int nlog;
static void rec(uint32_t a, uint32_t b) { if (nlog + 2 <= LOGN) { logbuf[nlog++] = a; logbuf[nlog++] = b; } }
static void *__attribute__((thiscall)) g_geom(mobj *o) { rec(1, o->idx); return o->geom; }
static void *__attribute__((thiscall)) g_pos(mobj *o) { rec(2, o->idx); return o->pos; }
static float __attribute__((thiscall)) g_ang(mobj *o) { rec(4, o->idx); return o->ang; }
static void *__attribute__((thiscall)) g_obj(mobj *o) { rec(3, o->idx); return o->obj; }
static int __attribute__((thiscall)) g_cat(mobj *o) { return o->cat; }
static void *obj_vt[8] = {(void *)g_geom, (void *)g_pos, (void *)g_ang, (void *)g_obj, NULL, NULL, NULL, (void *)g_cat};
static char __attribute__((thiscall)) f_allow(mfilt *f, void *obj)
{
    mobj *o = (mobj *)((uint8_t *)obj - 0x100);
    rec(0x10 + f->id, o->idx);
    return (uint32_t)(o->idx * 2654435761u + f->id * 40503u) % 100 < (uint32_t)f->rate;
}
static uint32_t __attribute__((thiscall)) f_mask(mfilt *f) { return f->mask; }
static void *filt_vt[3] = {NULL, (void *)f_allow, (void *)f_mask};
static mfilt filts[2];

static void *__cdecl m_alloc(uint32_t n, int a, int b) { (void)a; (void)b; return calloc(1, n ? n : 1); }
static void __cdecl m_free(void *p, int k) { (void)k; free(p); }
static int __cdecl m_onexit(void *f) { (void)f; return 0; }

static uint32_t offa, offb;
static uint8_t strbuf[64] = {0x40, 0x42, 0x0f, 0x00};          /* a shared AsciiString: refcount 1,000,000 */

/* a GeometryInfo by the game's constructor: GeometryInfo(type, isSmall, height, major, minor) */
static uint8_t *geometry(int type, float h, float a, float b)
{
    typedef void (__attribute__((thiscall)) *ctor_fn)(void *, int, int, float, float, float);
    uint8_t *g = calloc(1, 0x60);
    ((ctor_fn)(uintptr_t)(0x450429 + offa))(g, type, rnd() & 1, h, a, b);
    return g;
}
/* extra shapes after the constructor's one: offsets, any type, active or not */
static void add_shapes(uint8_t *g, int n, int odd)
{
    uint8_t *old = *(uint8_t **)(g + 0x2c), *arr = calloc(n + 1, 0x24);
    memcpy(arr, old, 0x24);
    for (int i = 1; i <= n; i++) {
        uint8_t *s = arr + 0x24 * i;
        int t = odd && rnd() % 6 == 0 ? (int)(rnd() % 5) - 1 : (int)(rnd() % 3);
        *(int32_t *)s = t;
        *(float *)(s + 4) = rf(1, 60);
        *(float *)(s + 8) = odd && rnd() % 5 == 0 ? (rnd() % 2 ? special() : -rf(1, 60)) : rf(2, 60);
        *(float *)(s + 0xc) = odd && rnd() % 5 == 0 ? -rf(1, 40) : rf(2, 60);
        *(float *)(s + 0x10) = rf(-120, 120); *(float *)(s + 0x14) = rf(-120, 120); *(float *)(s + 0x18) = rf(-10, 30);
        if (odd && rnd() % 8 == 0) *(float *)(s + 0x10) = special();
        *(uint8_t **)(s + 0x1c) = rnd() % 4 ? NULL : strbuf;
        s[0x20] = rnd() % 5 != 0; s[0x21] = 1;
    }
    *(uint8_t **)(g + 0x2c) = arr; *(uint8_t **)(g + 0x30) = arr + 0x24 * (n + 1); *(uint8_t **)(g + 0x34) = arr + 0x24 * (n + 1);
}
static uint8_t *random_geometry(int odd)
{
    uint8_t *g;
    switch (rnd() % 6) {
    case 0: case 1: g = geometry(1, rf(8, 30), rf(3, 20), 0); break;                 /* a unit: cylinder */
    case 2: g = geometry(0, rf(5, 40), rf(3, 40), 0); break;                         /* sphere */
    case 3: g = geometry(2, rf(10, 80), rf(10, 100), rf(10, 100)); break;            /* a building: box */
    default: g = geometry(rnd() % 3, rf(5, 60), rf(5, 60), rf(5, 60)); add_shapes(g, 1 + rnd() % 3, odd); break;
    }
    if (odd && rnd() % 12 == 0) *(uint8_t **)(g + 0x30) = *(uint8_t **)(g + 0x2c);    /* no shapes */
    if (odd && rnd() % 12 == 0) *(float *)(*(uint8_t **)(g + 0x2c) + 8) = rnd() % 2 ? special() : -rf(1, 100);
    return g;
}

/* ---- single calls --------------------------------------------------------------------- */
typedef float (__cdecl *t4_fn)(const float *q, void *it, float r2);
typedef struct { uint32_t res; uint8_t stat[0x5c + 0x24]; int l0, l1; } outcome;
static uint32_t g_mx = 0x1f80;                                   /* MXCSR for the calls */
static float call(uint32_t off, const float *q, mobj *o, float r2, uint32_t cw)
{
    uint16_t cw0, c16 = (uint16_t)cw; uint32_t mx0; float r;
    __asm__ volatile("fnstcw %0\n\tstmxcsr %1" : "=m"(cw0), "=m"(mx0));
    __asm__ volatile("fldcw %0\n\tldmxcsr %1" :: "m"(c16), "m"(g_mx));
    r = ((t4_fn)(uintptr_t)(0xa3c7d0 + off))(q, o, r2);
    __asm__ volatile("fldcw %0\n\tldmxcsr %1" :: "m"(cw0), "m"(mx0));
    return r;
}
static void snap_static(uint8_t *out)
{
    uint8_t *g = (uint8_t *)0xdef920, *s = *(uint8_t **)(g + 0x2c);
    memcpy(out, g, 0x5c);
    if (s && *(uint8_t **)(g + 0x30) - s >= 0x24) memcpy(out + 0x5c, s, 0x24); else memset(out + 0x5c, 0, 0x24);
}

enum { BATCH = 64 };
typedef struct { float q[3]; float r2; } query;
static void make_query(query *qq, mobj *o, int odd, float r2prev)
{
    float r = rnd() % 4 == 0 && r2prev >= 0 ? sqrtf(r2prev) : rf(10, 600);
    qq->r2 = rnd() % 3 == 0 ? r2prev : r * r;
    if (odd && rnd() % 20 == 0) qq->r2 = rnd() % 2 ? special() : -rf(1, 1e4f);
    float ang = rf(0, 6.2831853f), d;
    switch (rnd() % 4) {
    case 0: d = rf(0, r); break;
    case 1: d = rf(0, 3 * r + 300); break;
    case 2: {                                                   /* near a shape's reach: the boundary */
        uint8_t *s = *(uint8_t **)(o->geom + 0x2c), *e = *(uint8_t **)(o->geom + 0x30);
        float reach = 0;
        int n = (int)((e - s) / 0x24);
        if (n > 0) {
            uint8_t *p = s + 0x24 * (rnd() % n);
            float a = *(float *)(p + 8), b = *(float *)(p + 0xc), ox = *(float *)(p + 0x10), oy = *(float *)(p + 0x14);
            reach = sqrtf(ox * ox + oy * oy) + (*(int *)p == 2 ? sqrtf(a * a + b * b) : fabsf(a));
        }
        d = reach + sqrtf(fabsf(qq->r2)) + rf(-0.05f, 0.05f) * (1 + (rnd() % 3) * 30);
        break;
    }
    default: d = rf(0, 40000); break;
    }
    qq->q[0] = o->pos[0] + d * cosf(ang); qq->q[1] = o->pos[1] + d * sinf(ang); qq->q[2] = rf(-50, 50);
    if (odd && rnd() % 25 == 0) qq->q[rnd() % 2] = special();
}
static void place(mobj *o, int odd)
{
    o->pos[0] = rf(0, 5120); o->pos[1] = rf(0, 5120); o->pos[2] = rf(0, 40);
    o->ang = rnd() % 8 ? rf(-7, 7) : rnd() % 2 ? rf(-3e5f, 3e5f) : 0;
    if (odd && rnd() % 15 == 0) o->ang = rnd() % 2 ? special() : rf(-1e20f, 1e20f);
    if (odd && rnd() % 25 == 0) o->pos[rnd() % 3] = special();
    if (odd && rnd() % 25 == 0) { o->pos[0] = rf(1e7f, 1e9f); }
}

static long batch(uint32_t cw, int odd, long *apart)
{
    static query qs[BATCH]; static mobj *os[BATCH];
    static outcome ob[BATCH];
    static uint32_t *logs[BATCH];
    static int nl[BATCH];
    if (!logs[0]) for (int i = 0; i < BATCH; i++) logs[i] = malloc(64 * 4);
    float r2 = rf(10, 600); r2 *= r2;
    for (int i = 0; i < BATCH; i++) {
        mobj *o = os[i] = &objs[rnd() % 400];
        make_query(&qs[i], o, odd, r2);
        r2 = qs[i].r2;
    }
    long a0 = gp_ag_stats[1];
    for (int i = 0; i < BATCH; i++) {                           /* B, the whole batch */
        nlog = 0;
        ob[i].res = bits(call(offb, qs[i].q, os[i], qs[i].r2, cw));
        snap_static(ob[i].stat);
        nl[i] = nlog < 64 ? nlog : 64; memcpy(logs[i], logbuf, nl[i] * 4);
    }
    *apart += gp_ag_stats[1] - a0;
    long bad = 0;
    for (int i = 0; i < BATCH; i++) {                           /* then A */
        uint8_t st[0x5c + 0x24];
        nlog = 0;
        uint32_t res = bits(call(offa, qs[i].q, os[i], qs[i].r2, cw));
        snap_static(st);
        int ok = res == ob[i].res && nlog == nl[i] && !memcmp(logbuf, logs[i], nl[i] * 4) && !memcmp(st, ob[i].stat, sizeof st);
        if (!ok) {
            bad++;
            if (fails + bad < 12 && !gp_ag_sens)
                printf("  MISMATCH q %08x,%08x r2 %08x obj %d (pos %08x,%08x ang %08x): result %08x/%08x, log %d/%d, static %s\n",
                       bits(qs[i].q[0]), bits(qs[i].q[1]), bits(qs[i].r2), os[i]->idx, bits(os[i]->pos[0]), bits(os[i]->pos[1]),
                       bits(os[i]->ang), res, ob[i].res, nlog, nl[i], memcmp(st, ob[i].stat, sizeof st) ? "differs" : "same");
        }
    }
    return bad;
}

static void build_objects(int odd)
{
    for (int i = 0; i < 400; i++) {
        mobj *o = &objs[i];
        o->vt = obj_vt; o->idx = i; o->cat = (int)(rnd() % 9) - 1; o->obj = (uint8_t *)o + 0x100;
        o->geom = random_geometry(odd);
        place(o, odd);
    }
}

/* ---- range queries ------------------------------------------------------------------- */
static uint8_t pm[0x140];
static void world(int n, int fortress)
{
    memset(pm, 0, sizeof pm);
    *(float *)(pm + 0x118) = 1.0f / 5120; *(int *)(pm + 0x11c) = NCELL;
    static uint8_t *nodes[21];
    for (int t = 0; t < 21; t++) {
        uint32_t *v = (uint32_t *)(pm + 0x18 + 12 * t);
        if (!nodes[t]) nodes[t] = malloc(NNODE * 8);
        memset(nodes[t], 0, NNODE * 8);
        v[0] = (uint32_t)(uintptr_t)nodes[t]; v[1] = v[2] = v[0] + NNODE * 8;
    }
    memset(ents, 0, sizeof(mentry) * n);
    for (int i = 0; i < n; i++) {
        mobj *o = &objs[i];
        o->vt = obj_vt; o->idx = i; o->cat = (int)(rnd() % 9) - 1;
        o->obj = rnd() % 30 ? (uint8_t *)o + 0x100 : NULL;
        if (!fortress || i >= 400) o->geom = random_geometry(0);
        place(o, 0);
        if (fortress && i < 200) { o->pos[0] = 2000 + rf(-300, 300); o->pos[1] = 2000 + rf(-300, 300); }
        else if (i < n / 2) { o->pos[0] = rf(1500, 3500); o->pos[1] = rf(1500, 3500); }
        ents[i].w[1] = (uint32_t)(uintptr_t)o;
        typedef void (__attribute__((thiscall)) *link_fn)(void *pm, void *e);
        ((link_fn)(uintptr_t)(0xa3b220 + offa))(pm, &ents[i]);
    }
}
typedef void *(__attribute__((thiscall)) *range_fn)(void *pm, void **ret, const float *pos, float r, const float *region,
                                                      int dc, mfilt *filters, int sort);
typedef struct { uint32_t n; uint32_t *v; } result;
static result range(uint32_t off, const float *pos, float r, int dc, mfilt *f)
{
    static const uint32_t dc_va[5] = {0xa3a7a0, 0xa3ae50, 0xa3a7d0, 0xa3aeb0, 0xa3c7d0};
    for (int i = 0; i < 5; i++) ((uint32_t *)0xdbdaf8)[i] = dc_va[i] + off;
    void *h = NULL;
    uint16_t cw0, c16 = 0x007f;                                 /* the game's x87 mode */
    __asm__ volatile("fnstcw %0" : "=m"(cw0));
    __asm__ volatile("fldcw %0" :: "m"(c16));
    ((range_fn)(uintptr_t)(0xa3c4e0 + off))(pm, &h, pos, r, NULL, dc, f, 0);
    __asm__ volatile("fldcw %0" :: "m"(cw0));
    uint32_t *p = h;
    result res = {(p[1] - p[0]) / 4, NULL};
    res.v = malloc(res.n * 4 + 4);
    memcpy(res.v, (void *)(uintptr_t)p[0], res.n * 4);
    if (p[0]) free((void *)(uintptr_t)p[0]);
    free(p);
    return res;
}
static long range_one(long *items)
{
    float pos[3] = {rf(0, 5120), rf(0, 5120), rf(0, 30)}, r = rnd() % 4 ? rf(10, 400) : rf(400, 3000);
    if (rnd() % 2) { pos[0] = rf(1500, 3500); pos[1] = rf(1500, 3500); }
    int nf = rnd() % 3;
    for (int k = 0; k < nf; k++)
        filts[k] = (mfilt){filt_vt, k + 1 < nf ? &filts[k + 1] : NULL, rnd() % 3 ? rnd() & 0x1fffff : 0xffffffff, rnd() % 2 ? 50 : 100, k};
    nlog = 0;
    result a = range(offa, pos, r, 4, nf ? filts : NULL);
    int na = nlog; memcpy(loga, logbuf, na * 4);
    nlog = 0;
    result b = range(offb, pos, r, 4, nf ? filts : NULL);
    int ok = a.n == b.n && !memcmp(a.v, b.v, a.n * 4) && na == nlog && !memcmp(loga, logbuf, na * 4);
    *items += a.n / 2;
    if (!ok && fails < 20) printf("  RANGE MISMATCH r %g at %g,%g: %u/%u items, %d/%d log\n", r, pos[0], pos[1], a.n / 2, b.n / 2, na, nlog);
    free(a.v); free(b.v);
    return !ok;
}

/* ms per type-4 range scan at points around (c, c) +- spread: the original, aigeom + scantree, and for
 * comparison the original walk with the 2D centre distance (type 0) */
static void time_scan(const char *what, float c, float spread, float r)
{
    double ms[3]; long got = 0, cand0 = gp_ag_stats[0], apart0 = gp_ag_stats[1];
    for (int k = 0; k < 3; k++) {
        uint32_t s0 = rs;
        uint64_t t0 = now_us();
        for (int i = 0; i < 400; i++) {
            float pos[3] = {c + rf(-spread, spread), c + rf(-spread, spread), 10};
            result res = range(k == 1 ? offb : offa, pos, r, k == 2 ? 0 : 4, NULL);
            if (k < 2) got += res.n / 2;
            free(res.v);
        }
        ms[k] = (now_us() - t0) / 400.0 / 1000.0;
        if (k < 2) rs = s0;
    }
    long cand = gp_ag_stats[0] - cand0, apart1 = gp_ag_stats[1] - apart0;
    printf("[6] %s: %.0f candidates, %.0f answered apart, %.0f hits per scan; original %.3f ms, aigeom + scantree %.3f ms "
           "per scan (the original walk with the 2D centre distance instead: %.3f ms)\n",
           what, cand / 400.0, apart1 / 400.0, got / 800.0, ms[0], ms[1], ms[2]);
}

static LONG WINAPI crash(EXCEPTION_POINTERS *e)
{
    CONTEXT *c = e->ContextRecord;
    printf("CRASH %08lx at %p (a %08x b %08x) eax %08lx ecx %08lx edx %08lx esi %08lx edi %08lx\nFAIL\n",
           e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress, offa, offb, c->Eax, c->Ecx, c->Edx,
           c->Esi, c->Edi);
    ExitProcess(3);
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    SetUnhandledExceptionFilter(crash);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    long nq = (argc > 2 ? atol(argv[2]) : 200) * 1000;
    static const uint32_t data[][2] = {{0xbd0000, 0x10000}, {0xc1b000, 0x1000}, {0xc95000, 0x1000}, {0xdbd000, 0x1000},
                                       {0xdc5000, 0x2000}, {0xdef000, 0x1000}, {0xe09000, 0x1000}};
    for (unsigned i = 0; i < sizeof data / sizeof data[0]; i++) if (orig_map_at(data[i][0], data[i][1], 0)) return 2;
    HMODULE k32 = GetModuleHandleA("kernel32.dll"), crt = LoadLibraryA("msvcr71.dll");
    *(void **)0xbd015c = (void *)GetProcAddress(k32, "InitializeCriticalSection");
    *(void **)0xbd0200 = (void *)GetProcAddress(k32, "EnterCriticalSection");
    *(void **)0xbd0204 = (void *)GetProcAddress(k32, "LeaveCriticalSection");
    *(void **)0xbd044c = (void *)m_onexit;
    *(uint32_t *)0xe09070 = 0xffffffff;
    *(void **)0xbd0580 = (void *)GetProcAddress(crt, "floor");
    *(void **)0xbd0588 = (void *)GetProcAddress(crt, "ceil");
    *(void **)0xdc5e44 = (void *)m_alloc; *(void **)0xdc5e3c = (void *)m_free;
    offa = orig_reserve_image(); offb = orig_reserve_image();
    /* the code pages of everything the tested functions call directly (a call-graph closure from the
     * exe: GeometryInfo's constructor, the type-4 function, iterateObjectsInRange, linkNode), and the
     * data sites the installer checks */
    static const uint32_t pages[] = {0x401000, 0x402000, 0x405000, 0x406000, 0x42c000, 0x42f000, 0x430000, 0x435000,
        0x436000, 0x437000, 0x43b000, 0x440000, 0x44d000, 0x450000, 0x462000, 0x463000, 0x478000, 0x4b3000, 0x4b4000,
        0x4bb000, 0x576000, 0x617000, 0x640000, 0x641000, 0x6dd000, 0x828000, 0x851000, 0x915000, 0xa39000, 0xa3a000,
        0xa3b000, 0xa3c000, 0xa3d000, 0xaaa000, 0xad0000, 0xad1000, 0xad2000, 0xad3000, 0xad4000, 0xadf000, 0xb4e000,
        0xbd1000, 0xc1b000};
    for (int k = 0; k < 2; k++)
        for (unsigned i = 0; i < sizeof pages / sizeof pages[0]; i++)
            if (orig_map_at(pages[i], 0x1000, k ? offb : offa)) return 2;
    gp_va_offset = offb;
    int ok = gp_patch_aigeom();
    int ok2 = gp_patch_scantree();
    gp_va_offset = 0;
    verdict(!ok || !ok2, "[0] aigeom: %s to the original bytes (relocated copy); scantree beside it: %s\n",
            ok ? "applied" : "NOT applied", ok2 ? "applied" : "NOT applied");
    if (!ok) { printf("FAIL\n"); return 1; }
    objs = calloc(MAXOBJ, sizeof *objs); ents = calloc(MAXOBJ, sizeof *ents);
    logbuf = malloc(LOGN * 4); loga = malloc(LOGN * 4);

    /* [1] */
    long bad = 0, n = 0, apart = 0, orig0 = gp_ag_stats[3], calc0 = gp_ag_stats[2], inl0 = gp_ag_stats[4];
    for (long it = 0; it < nq / BATCH; it++) {
        if (it % 200 == 0) build_objects(it % 400 == 200);
        bad += batch(0x007f, it % 3 == 0, &apart); n += BATCH;
    }
    verdict(bad != 0, "[1] %ld calls in batches of %d (B then A): %ld mismatches (result, getter log, static sphere); "
            "%ld answered apart without the intersection test, %ld tested inline, %ld bound recalculations, %ld by the "
            "original\n", n, BATCH, bad, apart, gp_ag_stats[4] - inl0, gp_ag_stats[2] - calc0, gp_ag_stats[3] - orig0);

    /* [2] */
    static const uint32_t cws[] = {0x027f, 0x037f, 0x047f, 0x087f, 0x0c7f, 0x107f, 0x0a7f};
    bad = 0; n = 0;
    for (int m = 0; m < 7; m++) {
        build_objects(1);
        for (long it = 0; it < nq / BATCH / 20; it++) { bad += batch(cws[m], 1, &apart); n += BATCH; }
    }
    static const uint32_t mxs[] = {0x9fc0, 0x3f80, 0x1fc0};      /* FTZ + DAZ, rounding down, DAZ */
    for (int m = 0; m < 3; m++) {
        g_mx = mxs[m];
        build_objects(1);
        for (long it = 0; it < nq / BATCH / 20; it++) { bad += batch(0x007f, 1, &apart); n += BATCH; }
    }
    g_mx = 0x1f80;
    verdict(bad != 0, "[2] %ld calls in 7 other x87 modes and 3 other MXCSR modes: %ld mismatches\n", n, bad);

    /* [3] */
    bad = 0; n = 0; long items = 0;
    for (long it = 0; it < nq / 50; it++) {
        if (it % 500 == 0) world(300 + rnd() % 2200, 0);
        n++; bad += range_one(&items);
    }
    verdict(bad != 0, "[3] %ld range queries with type 4 (r 10-3,000, 0-2 filters; scantree on in B): %ld mismatches, "
            "%ld objects returned\n", n, bad, items);

    /* [4] */
    static const char *what[] = {"", "shape offsets forgotten", "the sphere's bounds never recalculated",
                                 "the exact reach, no rounding margin", "the inline test without its second z test"};
    for (uint32_t s = 1; s <= 4; s++) {
        gp_ag_sens = s; bad = 0; n = 0;
        build_objects(0);
        for (long it = 0; it < nq / BATCH / 4; it++) { bad += batch(0x007f, 0, &apart); n += BATCH; }
        gp_ag_sens = 0;
        if (s != 3) verdict(bad == 0, "[4] sensitivity, %s: %ld of %ld calls differ (%s)\n", what[s], bad, n, bad ? "caught" : "NOT CAUGHT");
        else printf("[4] with %s: %ld of %ld calls differ\n", what[s], bad, n);
    }

    /* [5] two memory layouts: the same objects and geometries copied to other addresses */
    {
        build_objects(0);
        enum { NQ = 4000 };
        static query qs[NQ]; static int qo[NQ]; static uint32_t ra[NQ], rb[NQ]; static int la[NQ];
        long bad6 = 0, moved = 0;
        for (int i = 0; i < NQ; i++) { qo[i] = rnd() % 400; make_query(&qs[i], &objs[qo[i]], 0, 22500); }
        for (int pass = 0; pass < 2; pass++) {
            for (int i = 0; i < NQ; i++) {
                nlog = 0; uint32_t a = bits(call(offa, qs[i].q, &objs[qo[i]], qs[i].r2, 0x007f));
                int na = nlog;
                nlog = 0; uint32_t b = bits(call(offb, qs[i].q, &objs[qo[i]], qs[i].r2, 0x007f));
                bad6 += a != b || na != nlog;
                if (!pass) { ra[i] = a; la[i] = na; } else { rb[i] = a; moved += ra[i] != rb[i] || la[i] != na; }
            }
            if (pass) break;
            for (int i = 0; i < 400; i++) {                       /* new geometry and shape arrays, other addresses */
                uint8_t *g = calloc(1, 0x60 + 4 * (i % 7)) + 4 * (i % 7), *old = objs[i].geom;
                memcpy(g, old, 0x5c);
                uint8_t *sb = *(uint8_t **)(old + 0x2c), *se = *(uint8_t **)(old + 0x30);
                uint32_t len = (uint32_t)(se - sb);
                uint8_t *arr = calloc(1, len + 0x24 + 8) + 8;
                memcpy(arr, sb, len);
                *(uint8_t **)(g + 0x2c) = arr; *(uint8_t **)(g + 0x30) = arr + len; *(uint8_t **)(g + 0x34) = arr + len;
                objs[i].geom = g;
            }
        }
        verdict(bad6 != 0 || moved != 0, "[5] %d calls in two memory layouts of the same objects: %ld mismatches A/B, %ld "
                "results that changed with the layout\n", 2 * NQ, bad6, moved);
    }

    /* [6] */
    for (int i = 0; i < 400; i++)
        objs[i].geom = i < 40 ? geometry(2, rf(20, 60), rf(15, 60), rf(15, 60)) : i < 200 ? geometry(1, rf(10, 20), rf(4, 12), 0)
                                                                                    : random_geometry(0);
    world(1300, 1);
    time_scan("the fortress spikes' scan (r 150 at the fortress, its area of 200 objects)", 2000, 100, 150);
    for (int i = 0; i < 1300; i++) {
        objs[i].geom = i < 1000 ? geometry(1, rf(10, 20), rf(4, 12), 0) : random_geometry(0);
    }
    world(1300, 0);
    for (int i = 0; i < 1000; i++) objs[i].ang = rf(-3.2f, 3.2f);
    time_scan("a splash hit (r 40) inside a battle of 1,000 units in 2,000 x 2,000", 2500, 900, 40);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
