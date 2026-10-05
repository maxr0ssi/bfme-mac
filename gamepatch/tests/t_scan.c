/* t_scan: scantree (p_scan.c) against the original range query, both run from the exe's bytes.
 * Two relocated copies of the partition code (0xa39000-0xa3d000 with iterateObjectsInRange 0xa3c4e0,
 * the walk 0xa3a860, the distance functions, append, sort; the allocator stubs 0x42f000-0x431000; the
 * 3D distance's getter 0xb4e370): one patched by the installer, one untouched. One world for both:
 * 21 quadtrees of depth 7 (128 x 128 leaf cells over 5120 units), objects inserted by the game's own
 * linkNode 0xa3b220, mock objects whose getters (position, geometry, getObject, category) and mock
 * filters (allow, player mask) log every call. Each query runs through both copies of 0xa3c4e0 and
 * must give the same result vector (objects, distance bits, order, after the optional sort) and the
 * same call log (which getter or filter, on which object, in which order).
 *   [0] the patch applies to the original bytes (relocated copy)
 *   [1] random queries: distance types 0-3, 0-3 filters (masks, accept rates), sort 0-2, radius 0 to
 *       map-wide, query points on and off the map; worlds with clustered armies, objects at the same
 *       point, huge/tiny/denormal/infinite/NaN coordinates and radii; region queries (no position)
 *   [2] the same in seven other FPU modes (the x87 path runs; results must still be identical)
 *   [3] time per query: 1,500 units, a battle of 1,000 in 2000 x 2000 units, radius 300, bounding
 *       circle, enemies-of-4 mask and one 50 % filter, sorted (the mood scan's shape)
 * usage: t_scan.exe <path to lotrbfme2ep1.exe 2.02> [thousands of queries] */
#include "orig.h"
#include "gp_scale.h"
#include "gp_logic.h"
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
static uint32_t rs = 0x9e3779b9;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
static float rf(float lo, float hi) { return lo + (hi - lo) * (rnd() >> 8) / 16777216.0f; }
static float fb(uint32_t u) { float f; memcpy(&f, &u, 4); return f; }

/* ---- the mock world ----------------------------------------------------------------------- */
enum { L = 7, NCELL = 1 << L, NNODE = (((1 << (2 * L + 2)) - 1) / 3), MAXOBJ = 4000, LOGN = 1 << 17 };
typedef struct { void **vt; float pos[3]; float geom[12]; int cat; void *obj; int idx; } mobj;
typedef struct { uint32_t w[12]; } mentry;                       /* +4 iface, +0x14 next, +0x20.. cells */
typedef struct { void **vt; void *next; uint32_t mask; int rate; int id; } mfilt;
static uint8_t pm[0x140];
static mobj *objs; static mentry *ents; static int nobj;
static uint32_t *logbuf; static int nlog;
static void rec(uint32_t a, uint32_t b) { if (nlog + 2 <= LOGN) { logbuf[nlog++] = a; logbuf[nlog++] = b; } }

static void *__attribute__((thiscall)) g_geom(mobj *o) { rec(1, o->idx); return o->geom; }
static void *__attribute__((thiscall)) g_pos(mobj *o) { rec(2, o->idx); return o->pos; }
static void *__attribute__((thiscall)) g_obj(mobj *o) { rec(3, o->idx); return o->obj; }
static int __attribute__((thiscall)) g_cat(mobj *o) { return o->cat; }
static void *obj_vt[8] = {(void *)g_geom, (void *)g_pos, NULL, (void *)g_obj, NULL, NULL, NULL, (void *)g_cat};
static char __attribute__((thiscall)) f_allow(mfilt *f, void *obj)
{
    mobj *o = (mobj *)((uint8_t *)obj - 0x100);
    rec(0x10 + f->id, o->idx);
    return (uint32_t)(o->idx * 2654435761u + f->id * 40503u) % 100 < (uint32_t)f->rate;
}
static uint32_t __attribute__((thiscall)) f_mask(mfilt *f) { return f->mask; }
static void *filt_vt[3] = {NULL, (void *)f_allow, (void *)f_mask};
static mfilt filts[3];

static void *__cdecl m_alloc(uint32_t n, int a, int b) { (void)a; (void)b; return calloc(1, n ? n : 1); }
static void __cdecl m_free(void *p, int k) { (void)k; free(p); }

static uint32_t offa, offb;
static void table_for(uint32_t off)
{
    static const uint32_t dc[5] = {0xa3a7a0, 0xa3ae50, 0xa3a7d0, 0xa3aeb0, 0xa3c7d0};
    for (int i = 0; i < 5; i++) ((uint32_t *)0xdbdaf8)[i] = dc[i] + off;
}

static float coord(int mode)
{
    static const uint32_t sp[] = {0x7f800000, 0xff800000, 0x7fc00000, 0x00000001, 0x80000000, 0, 0x5f000000,
                                  0x1e800000, 0x7f7fffff, 0x00800000, 0x20000000, 0x9f000000};
    switch (mode) {
    case 0: return rf(-100, 5300);
    case 1: return fb(sp[rnd() % 12]);
    case 2: return ldexpf(rf(1, 2), (int)(rnd() % 160) - 80);
    default: return rf(1500, 3500);                               /* a battle */
    }
}
static void build(int weird, int n)
{
    memset(pm, 0, sizeof pm);
    *(float *)(pm + 0x118) = 1.0f / 5120; *(int *)(pm + 0x11c) = NCELL;
    for (int t = 0; t < 21; t++) {
        uint32_t *v = (uint32_t *)(pm + 0x18 + 12 * t);
        static uint8_t *nodes[21];
        if (!nodes[t]) nodes[t] = malloc(NNODE * 8);
        memset(nodes[t], 0, NNODE * 8);
        v[0] = (uint32_t)(uintptr_t)nodes[t]; v[1] = v[2] = v[0] + NNODE * 8;
    }
    nobj = n;
    memset(ents, 0, sizeof(mentry) * n);
    for (int i = 0; i < n; i++) {
        mobj *o = &objs[i];
        memset(o, 0, sizeof *o);
        o->vt = obj_vt; o->idx = i; o->cat = (int)(rnd() % 10) - 1;
        int m = weird && rnd() % 8 == 0 ? 1 + rnd() % 2 : i < n * 2 / 3 ? 3 : 0;
        o->pos[0] = coord(m); o->pos[1] = coord(rnd() % 6 ? m : 0); o->pos[2] = rf(0, 50);
        if (i && rnd() % 20 == 0) memcpy(o->pos, objs[rnd() % i].pos, 8);        /* same point */
        o->geom[4] = weird && rnd() % 10 == 0 ? coord(1 + rnd() % 2) : rf(3, 40);   /* +0x10 radius */
        o->geom[5] = rf(3, 40); o->geom[8] = rf(1, 30);                             /* +0x14, +0x20 (3D) */
        o->obj = rnd() % 30 ? (uint8_t *)o + 0x100 : NULL;
        ents[i].w[1] = (uint32_t)(uintptr_t)o;
        typedef void (__attribute__((thiscall)) *link_fn)(void *pm, void *e);
        ((link_fn)(uintptr_t)(0xa3b220 + offa))(pm, &ents[i]);
    }
}

typedef void *(__attribute__((thiscall)) *range_fn)(void *pm, void **ret, const float *pos, float r, const float *region,
                                                      int dc, mfilt *filters, int sort);
typedef struct { uint32_t n; uint32_t *v; } result;
static result run(int patched, const float *pos, float r, const float *region, int dc, mfilt *f, int sort, uint32_t cw)
{
    uint32_t off = patched ? offb : offa;
    table_for(off);
    void *h = NULL;
    uint16_t cw0; __asm__ volatile("fnstcw %0" : "=m"(cw0));
    uint16_t c16 = (uint16_t)cw; __asm__ volatile("fldcw %0" :: "m"(c16));
    ((range_fn)(uintptr_t)(0xa3c4e0 + off))(pm, &h, pos, r, region, dc, f, sort);
    __asm__ volatile("fldcw %0" :: "m"(cw0));
    uint32_t *p = h;                                            /* payload {begin, end, cap, cursor, rc} */
    result res = {(p[1] - p[0]) / 4, NULL};
    res.v = malloc(res.n * 4 + 4);
    memcpy(res.v, (void *)(uintptr_t)p[0], res.n * 4);
    if (p[0]) free((void *)(uintptr_t)p[0]);
    free(p);
    return res;
}

static uint32_t *loga;
static long nansorts;
static int one(int dcmax, uint32_t cw, long *items)
{
    float pos[3], reg[6], r;
    int region = rnd() % 25 == 0, dc = rnd() % (dcmax + 1), sort = rnd() % 3, nf = rnd() % 4;
    if (rnd() % 3 == 0) dc = 1;
    int m = rnd() % 10 == 0 ? 1 + rnd() % 2 : rnd() % 2 ? 3 : 0;
    pos[0] = coord(m); pos[1] = coord(m); pos[2] = rf(0, 50);
    switch (rnd() % 8) {
    case 0: r = rf(0, 40); break;
    case 1: r = coord(1 + rnd() % 2); break;
    case 2: r = rf(0, 6000); break;
    default: r = rf(100, 600);
    }
    for (int k = 0; k < 3; k++) reg[k] = coord(m), reg[3 + k] = reg[k] + rf(0, 800);
    for (int k = 0; k < nf; k++) {
        mfilt *f = &filts[k];
        f->vt = filt_vt; f->next = k + 1 < nf ? &filts[k + 1] : NULL; f->id = k;
        f->mask = rnd() % 3 ? rnd() & 0x1fffff : 0xffffffff; f->rate = rnd() % 3 ? 50 : 100;
    }
    mfilt *fl = nf ? &filts[0] : NULL;
    /* unsorted first; sorted only when no distance is NaN: with a NaN key EA's sort (its unguarded
     * insertion sort) runs past the vector, reading and writing the memory around it */
    result a, b;
    int ok = 1, na = 0;
    for (int pass = 0; pass < 2 && ok; pass++) {
        if (pass) {
            int nan = 0;
            for (uint32_t i = 1; i < a.n; i += 2) nan |= (a.v[i] & 0x7fffffff) > 0x7f800000;
            free(a.v); free(b.v);
            if (!sort || nan) { nansorts += sort && nan; return 1; }
        }
        nlog = 0;
        a = run(0, region ? NULL : pos, r, region ? reg : NULL, dc, fl, pass ? sort : 0, cw);
        na = nlog; memcpy(loga, logbuf, na * 4);
        nlog = 0;
        b = run(1, region ? NULL : pos, r, region ? reg : NULL, dc, fl, pass ? sort : 0, cw);
        ok = a.n == b.n && !memcmp(a.v, b.v, a.n * 4) && na == nlog && !memcmp(loga, logbuf, na * 4);
        if (!pass) *items += a.n / 2;
    }
    if (!ok && fails < 1000) printf("  MISMATCH dc %d r %08x pos %08x,%08x region %d filters %d sort %d: %u/%u items, "
        "%d/%d log\n", dc, *(uint32_t *)&r, *(uint32_t *)&pos[0], *(uint32_t *)&pos[1], region, nf, sort, a.n / 2, b.n / 2, na, nlog);
    if (!ok && a.n == b.n && getenv("T_SCAN_DEBUG"))
        for (uint32_t i = 0; i < a.n; i += 2)
            if (a.v[i] != b.v[i] || a.v[i + 1] != b.v[i + 1]) {
                printf("    first difference at %u: %08x %08x | %08x %08x\n", i / 2, a.v[i], a.v[i + 1], b.v[i], b.v[i + 1]);
                break;
            }
    free(a.v); free(b.v);
    return ok;
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
    static const uint32_t data[][2] = {{0xbd0000, 0x2000}, {0xbd8000, 0x1000}, {0xbde000, 0x1000}, {0xc1b000, 0x1000},
                                       {0xc95000, 0x1000}, {0xdbd000, 0x1000}, {0xdc5000, 0x1000}, {0xdef000, 0x1000}};
    for (unsigned i = 0; i < sizeof data / sizeof data[0]; i++) if (orig_map_at(data[i][0], data[i][1], 0)) return 2;
    HMODULE crt = LoadLibraryA("msvcr71.dll");
    *(void **)0xbd0580 = (void *)GetProcAddress(crt, "floor");
    *(void **)0xbd0588 = (void *)GetProcAddress(crt, "ceil");
    *(void **)0xdc5e44 = (void *)m_alloc; *(void **)0xdc5e3c = (void *)m_free;
    offa = orig_reserve_image(); offb = orig_reserve_image();
    for (int k = 0; k < 2; k++) {
        uint32_t off = k ? offb : offa;
        if (orig_map_at(0xa39000, 0x4000, off) || orig_map_at(0x42f000, 0x2000, off) || orig_map_at(0xb4e000, 0x1000, off) || orig_map_at(0xc1b000, 0x1000, off))
            return 2;
    }
    gp_va_offset = offb;
    int ok = gp_patch_scantree();
    gp_va_offset = 0;
    verdict(!ok, "[0] scantree: %s to the original bytes (relocated copy)\n", ok ? "applied" : "NOT applied");
    if (!ok) { printf("FAIL\n"); return 1; }
    objs = calloc(MAXOBJ, sizeof *objs); ents = calloc(MAXOBJ, sizeof *ents);
    logbuf = malloc(LOGN * 4); loga = malloc(LOGN * 4);

    /* [1] game FPU mode */
    long bad = 0, n = 0, items = 0, inl0 = gp_scan_stats[3], tab0 = gp_scan_stats[4];
    for (long it = 0; it < nq; it++) {
        if (it % 5000 == 0) build(it % 10000 == 5000, 200 + rnd() % 2500);
        n++; bad += !one(3, 0x007f, &items);
    }
    verdict(bad != 0, "[1] %ld queries (distance types 0-3, filters, sorts, regions, special values), %ld objects "
            "returned: %ld mismatches; distances inline %ld, x87 or table %ld; %ld queries with a NaN distance were "
            "compared unsorted only (EA's sort is undefined with NaN keys)\n", n, items, bad,
            gp_scan_stats[3] - inl0, gp_scan_stats[4] - tab0, nansorts);

    /* [2] other FPU modes */
    static const uint32_t cws[] = {0x027f, 0x037f, 0x047f, 0x087f, 0x0c7f, 0x107f, 0x0a7f};
    bad = 0; n = 0;
    for (int m = 0; m < 7; m++)
        for (long it = 0; it < nq / 20; it++) {
            if (it % 5000 == 0) build(1, 300 + rnd() % 1500);
            n++; bad += !one(3, cws[m], &items);
        }
    verdict(bad != 0, "[2] %ld queries in 7 other x87 modes (53/64-bit precision, rounding down/up/chop): %ld mismatches\n", n, bad);

    /* [3] time */
    build(0, 1500);
    for (int i = 0; i < 1500; i++) {                         /* 1,000 in the battle, 8 players */
        objs[i].cat = i % 8;
        if (i < 1000) { objs[i].pos[0] = rf(1600, 3600); objs[i].pos[1] = rf(1600, 3600); }
    }
    build(0, 0);
    nobj = 1500;
    for (int i = 0; i < 1500; i++) {
        typedef void (__attribute__((thiscall)) *link_fn)(void *pm, void *e);
        memset(&ents[i], 0, sizeof ents[i]); ents[i].w[1] = (uint32_t)(uintptr_t)&objs[i];
        ((link_fn)(uintptr_t)(0xa3b220 + offa))(pm, &ents[i]);
    }
    filts[0] = (mfilt){filt_vt, &filts[1], 0xf0, 100, 0}; filts[1] = (mfilt){filt_vt, NULL, 0xffffffff, 50, 1};
    double us[3]; long got = 0;
    LONG c0 = gp_scan_stats[2], w0 = gp_scan_stats[0];
    for (int k = 0; k < 2; k++) {
        uint64_t t0 = now_us();
        for (int i = 0; i < 4000; i++) {
            nlog = 0;
            result r = run(k, objs[i % 1000].pos, 300, NULL, 1, &filts[0], 1, 0x007f);
            got += r.n / 2; free(r.v);
        }
        us[k] = (now_us() - t0) / 4000.0;
    }
    gp_va_offset = offa;                                     /* the original as in the game: distcalc on */
    int dc_ok = gp_patch_distcalc();
    gp_va_offset = 0;
    uint64_t t0 = now_us();
    for (int i = 0; i < 4000; i++) { nlog = 0; result r = run(0, objs[i % 1000].pos, 300, NULL, 1, &filts[0], 1, 0x007f); free(r.v); }
    us[2] = (now_us() - t0) / 4000.0;
    if (!dc_ok) verdict(1, "[3] distcalc did not apply to the original copy\n");
    printf("[3] time per query (1,000-unit battle, radius 300, circle, 2 filters, sorted; %.0f candidates in %.1f "
           "tree walks and %.0f results per query): original %.2f us, with distcalc (as installed) %.2f us, scantree "
           "%.2f us\n", (gp_scan_stats[2] - c0) / 4000.0, (gp_scan_stats[0] - w0) / 4000.0, got / 8000.0, us[0], us[2], us[1]);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
