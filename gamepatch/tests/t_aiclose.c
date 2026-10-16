/* t_aiclose: aiclosest (p_aiclose.c) against the original getClosestObject 0xa3bdb0, both run from the
 * exe's bytes. Two relocated copies of the partition code (0xa39000-0xa3e000: the search, its heap
 * functions, the cell index functions, the distance functions, linkNode), the allocator stubs and the
 * 3D distance's getter 0xb4e370: copy A untouched, copy B patched by the installer (aiclosest, with
 * distcalc, scantree and aura3d beside it as the game runs). One world for both: 21 quadtrees of depth
 * 7 (128 x 128 leaf cells over 5,120 units), objects inserted by the game's own linkNode, mock objects
 * whose getters (position, geometry, getObject) and mock filters (allow, mask) log every call.
 *   [0] the patch applies to the original bytes (relocated copy)
 *   [1] random searches: distance types 0-3 (and an invalid one), 0-3 filters, regions, radius 0 to
 *       map-wide, query points on and off the map; worlds with clustered armies, many objects on one
 *       point (ties), huge/tiny/denormal/infinite/NaN coordinates and radii: same object returned and
 *       the same getter / filter call log
 *   [2] the same in seven other x87 modes and three other MXCSR modes (the original runs)
 *   [3] two memory layouts: the same world built again from copies of its objects at other
 *       addresses; A and B must return the same object (by index) and call log in both layouts
 *   [4] sensitivity: a deliberate tie-break bug must be caught
 *   [5] time per search: an animal's flee scan (r 250, type 0, two filters) away from and inside a
 *       1,000-unit battle of a 1,500-object world, and a map-wide closest search
 * usage: t_aiclose.exe <path to lotrbfme2ep1.exe 2.02> [thousands of searches] */
#include "orig.h"
#include "p_ai.h"
#include "gp_scale.h"
#include "gp_logic.h"
#include "p_aura.h"
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
static uint32_t rs = 0x6b43a9b5;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
static float rf(float lo, float hi) { return lo + (hi - lo) * (rnd() >> 8) / 16777216.0f; }
static float fb(uint32_t u) { float f; memcpy(&f, &u, 4); return f; }

/* ---- the mock world (as t_scan) ---------------------------------------------------------- */
enum { L = 7, NCELL = 1 << L, NNODE = (((1 << (2 * L + 2)) - 1) / 3), MAXOBJ = 4000, LOGN = 1 << 18 };
typedef struct { void **vt; float pos[3]; float geom[12]; int cat; void *obj; int idx; } mobj;
typedef struct { uint32_t w[12]; } mentry;
typedef struct { void **vt; void *next; uint32_t mask; int rate; int id; } mfilt;
static uint8_t pm[0x140];
static mobj *objs, *objs2, *cur; static mentry *ents; static int nobj;
static uint32_t *logbuf, *loga; static int nlog;
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
static uint32_t __attribute__((thiscall)) f_mask(mfilt *f) { rec(0x20 + f->id, 0); return f->mask; }
static void *filt_vt[3] = {NULL, (void *)f_allow, (void *)f_mask};
static mfilt filts[3];

static void *__cdecl m_alloc(uint32_t n, int a, int b) { (void)a; (void)b; return calloc(1, n ? n : 1); }
static void __cdecl m_free(void *p, int k) { (void)k; free(p); }
static int __cdecl m_onexit(void *f) { (void)f; return 0; }

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
static void link_all(mobj *base, int n, const int *order)
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
    for (int j = 0; j < n; j++) {
        int i = order ? order[j] : j;
        ents[i].w[1] = (uint32_t)(uintptr_t)&base[i];
        typedef void (__attribute__((thiscall)) *link_fn)(void *pm, void *e);
        ((link_fn)(uintptr_t)(0xa3b220 + offa))(pm, &ents[i]);
    }
    cur = base; nobj = n;
}
static void build(int weird, int n)
{
    for (int i = 0; i < n; i++) {
        mobj *o = &objs[i];
        memset(o, 0, sizeof *o);
        o->vt = obj_vt; o->idx = i; o->cat = (int)(rnd() % 10) - 1;
        int m = weird && rnd() % 8 == 0 ? 1 + rnd() % 2 : i < n * 2 / 3 ? 3 : 0;
        o->pos[0] = coord(m); o->pos[1] = coord(rnd() % 6 ? m : 0); o->pos[2] = rf(0, 50);
        if (i && rnd() % 6 == 0) memcpy(o->pos, objs[rnd() % i].pos, 8);         /* same point: ties */
        o->geom[4] = weird && rnd() % 10 == 0 ? coord(1 + rnd() % 2) : rf(3, 40);   /* +0x10 radius */
        o->geom[5] = rf(3, 40); o->geom[8] = rf(1, 30);
        o->obj = rnd() % 30 ? (uint8_t *)o + 0x100 : NULL;
    }
    link_all(objs, n, NULL);
}

typedef void *(__attribute__((thiscall)) *closest_fn)(void *pm, const float *pos, float r, const float *region, int type,
                                                        mfilt *filters);
static uint32_t g_mx = 0x1f80;                                   /* MXCSR for the searches */
static int run(uint32_t off, const float *pos, float r, const float *reg, int type, mfilt *f, uint32_t cw)
{
    table_for(off);
    uint16_t cw0, c16 = (uint16_t)cw; uint32_t mx0;
    __asm__ volatile("fnstcw %0\n\tstmxcsr %1" : "=m"(cw0), "=m"(mx0));
    __asm__ volatile("fldcw %0\n\tldmxcsr %1" :: "m"(c16), "m"(g_mx));
    void *o = ((closest_fn)(uintptr_t)(0xa3bdb0 + off))(pm, pos, r, reg, type, f);
    __asm__ volatile("fldcw %0\n\tldmxcsr %1" :: "m"(cw0), "m"(mx0));
    return o ? ((mobj *)((uint8_t *)o - 0x100))->idx : -1;
}

typedef struct { float pos[3], reg[6], r; int region, type, nf; } query;
static void make(query *q, int weird)
{
    q->region = rnd() % 8 == 0; q->type = rnd() % 5; q->nf = rnd() % 4;
    if (rnd() % 3 == 0) q->type = 0;
    if (q->type == 4 && rnd() % 2) q->type = 7;                   /* invalid: the original uses 0 */
    int m = weird && rnd() % 10 == 0 ? 1 + rnd() % 2 : rnd() % 2 ? 3 : 0;
    q->pos[0] = coord(m); q->pos[1] = coord(m); q->pos[2] = rf(0, 50);
    switch (rnd() % 9) {
    case 0: q->r = rf(0, 40); break;
    case 1: q->r = weird ? coord(1 + rnd() % 2) : rf(0, 1); break;
    case 2: q->r = rf(0, 8000); break;
    case 3: q->r = rf(1e5f, 1e7f); break;
    default: q->r = rf(100, 600);
    }
    for (int k = 0; k < 3; k++) q->reg[k] = coord(m), q->reg[3 + k] = q->reg[k] + rf(0, 1500);
}
static void set_filters(const query *q, uint32_t seed)
{
    uint32_t s0 = rs; rs = seed | 1;
    for (int k = 0; k < q->nf; k++) {
        mfilt *f = &filts[k];
        f->vt = filt_vt; f->next = k + 1 < q->nf ? &filts[k + 1] : NULL; f->id = k;
        f->mask = rnd() % 3 ? rnd() & 0x1fffff : 0xffffffff; f->rate = rnd() % 3 ? 50 : 100;
    }
    rs = s0;
}
/* one search on A then B; 1 if identical (object and call log) */
static int one(const query *q, uint32_t cw, uint32_t seed, int *ra, int *la_n)
{
    set_filters(q, seed);
    mfilt *fl = q->nf ? &filts[0] : NULL;
    nlog = 0;
    int a = run(offa, q->pos, q->r, q->region ? q->reg : NULL, q->type, fl, cw);
    int na = nlog; memcpy(loga, logbuf, na * 4);
    nlog = 0;
    int b = run(offb, q->pos, q->r, q->region ? q->reg : NULL, q->type, fl, cw);
    int ok = a == b && na == nlog && !memcmp(loga, logbuf, na * 4);
    if (!ok && fails < 1000 && !gp_ac_sens)
        printf("  MISMATCH type %d r %08x pos %08x,%08x region %d filters %d: object %d/%d, log %d/%d\n", q->type,
               *(uint32_t *)&q->r, *(uint32_t *)&q->pos[0], *(uint32_t *)&q->pos[1], q->region, q->nf, a, b, na, nlog);
    if (ra) *ra = a;
    if (la_n) *la_n = na;
    return ok;
}

static LONG WINAPI crash(EXCEPTION_POINTERS *e)
{
    CONTEXT *c = e->ContextRecord;
    printf("CRASH %08lx at %p (a %08x b %08x) eax %08lx ecx %08lx edx %08lx esi %08lx edi %08lx\nFAIL\n",
           e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress, offa, offb, c->Eax, c->Ecx, c->Edx,
           c->Esi, c->Edi);
    for (int i = 0; i < 12; i++) printf(" %08lx", ((DWORD *)c->Esp)[i]);
    printf(" (stack)\n");
    ExitProcess(3);
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    SetUnhandledExceptionFilter(crash);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    long nq = (argc > 2 ? atol(argv[2]) : 200) * 1000;
    static const uint32_t data[][2] = {{0xbd0000, 0x2000}, {0xbd8000, 0x1000}, {0xbde000, 0x1000}, {0xc1b000, 0x1000},
                                       {0xc95000, 0x1000}, {0xdbd000, 0x1000}, {0xdc5000, 0x1000}, {0xdef000, 0x1000},
                                       {0xe09000, 0x1000}};
    for (unsigned i = 0; i < sizeof data / sizeof data[0]; i++) if (orig_map_at(data[i][0], data[i][1], 0)) return 2;
    HMODULE crt = LoadLibraryA("msvcr71.dll");
    *(void **)0xbd0580 = (void *)GetProcAddress(crt, "floor");
    *(void **)0xbd0588 = (void *)GetProcAddress(crt, "ceil");
    *(void **)0xdc5e44 = (void *)m_alloc; *(void **)0xdc5e3c = (void *)m_free;
    *(void **)0xbd044c = (void *)m_onexit; *(uint32_t *)0xe09070 = 0xffffffff;   /* the search's static vector: atexit */
    offa = orig_reserve_image(); offb = orig_reserve_image();
    for (int k = 0; k < 2; k++) {
        uint32_t off = k ? offb : offa;
        if (orig_map_at(0xa39000, 0x5000, off) || orig_map_at(0x42f000, 0x2000, off) || orig_map_at(0xb4e000, 0x1000, off) ||
            orig_map_at(0xc1b000, 0x1000, off) || orig_map_at(0xbd0000, 0x1000, off))
            return 2;
    }
    gp_va_offset = offb;
    int ok = gp_patch_aiclosest(), ok2 = gp_patch_distcalc() && gp_patch_scantree() && gp_patch_aura3d();
    gp_va_offset = 0;
    verdict(!ok || !ok2, "[0] aiclosest: %s to the original bytes (relocated copy); distcalc, scantree, aura3d beside it: %s\n",
            ok ? "applied" : "NOT applied", ok2 ? "applied" : "NOT applied");
    if (!ok) { printf("FAIL\n"); return 1; }
    objs = calloc(MAXOBJ, sizeof *objs); objs2 = calloc(MAXOBJ + 8, sizeof *objs2); ents = calloc(MAXOBJ, sizeof *ents);
    logbuf = malloc(LOGN * 4); loga = malloc(LOGN * 4);

    /* [1] */
    long bad = 0, n = 0, found = 0, s0 = gp_ac_stats[0], c0 = gp_ac_stats[2], i0 = gp_ac_stats[3];
    for (long it = 0; it < nq; it++) {
        if (it % 4000 == 0) build(it % 8000 == 4000, 200 + rnd() % 2500);
        query q; make(&q, nobj && it % 8000 >= 4000);
        int a;
        n++; bad += !one(&q, 0x007f, rnd(), &a, NULL);
        found += a >= 0;
    }
    verdict(bad != 0, "[1] %ld searches (types 0-3 and invalid, filters, regions, ties, special values), %ld found an "
            "object: %ld mismatches; B: %ld searches, %.1f candidates each, %.0f %% of the distances inline\n", n, found, bad,
            gp_ac_stats[0] - s0, (double)(gp_ac_stats[2] - c0) / (gp_ac_stats[0] - s0 + 1),
            100.0 * (gp_ac_stats[3] - i0) / (gp_ac_stats[2] - c0 + 1));

    /* [2] */
    static const uint32_t cws[] = {0x027f, 0x037f, 0x047f, 0x087f, 0x0c7f, 0x107f, 0x0a7f};
    bad = 0; n = 0;
    for (int m = 0; m < 7; m++) {
        build(1, 300 + rnd() % 1500);
        for (long it = 0; it < nq / 20; it++) { query q; make(&q, 1); n++; bad += !one(&q, cws[m], rnd(), NULL, NULL); }
    }
    static const uint32_t mxs[] = {0x9fc0, 0x3f80, 0x1fc0};      /* FTZ + DAZ, rounding down, DAZ */
    for (int m = 0; m < 3; m++) {
        g_mx = mxs[m];
        build(1, 300 + rnd() % 1500);
        for (long it = 0; it < nq / 20; it++) { query q; make(&q, 1); n++; bad += !one(&q, 0x007f, rnd(), NULL, NULL); }
    }
    g_mx = 0x1f80;
    verdict(bad != 0, "[2] %ld searches in 7 other x87 modes and 3 other MXCSR modes: %ld mismatches\n", n, bad);

    /* [3] two memory layouts: the objects copied to another array (other addresses, other alignment) */
    bad = 0; n = 0;
    long diff = 0;
    for (int w = 0; w < 4; w++) {
        build(w & 1, 500 + rnd() % 2000);
        int nn = nobj;
        static query qs[2000]; static int ra[2000], la[2000]; static uint32_t seeds[2000];
        int nqs = (int)(nq / 400 < 2000 ? nq / 400 : 2000);
        for (int i = 0; i < nqs; i++) { make(&qs[i], w & 1); seeds[i] = rnd(); n++; bad += !one(&qs[i], 0x007f, seeds[i], &ra[i], &la[i]); }
        mobj *o2 = (mobj *)((uint8_t *)objs2 + 7 * sizeof *objs2 + 4);
        for (int i = 0; i < nn; i++) {
            o2[i] = objs[i];
            o2[i].obj = objs[i].obj ? (uint8_t *)&o2[i] + 0x100 : NULL;
        }
        link_all(o2, nn, NULL);                                    /* the same trees, other addresses */
        for (int i = 0; i < nqs; i++) {
            int a2, l2;
            n++; bad += !one(&qs[i], 0x007f, seeds[i], &a2, &l2);
            diff += a2 != ra[i] || l2 != la[i];
        }
    }
    verdict(bad != 0 || diff != 0, "[3] %ld searches over two memory layouts of the same worlds: %ld mismatches A/B, %ld "
            "results that changed with the layout\n", n, bad, diff);

    /* [4] */
    gp_ac_sens = 1; bad = 0; n = 0;
    build(0, 1500);
    for (long it = 0; it < nq / 20; it++) { query q; make(&q, 0); n++; bad += !one(&q, 0x007f, rnd(), NULL, NULL); }
    gp_ac_sens = 0;
    verdict(bad == 0, "[4] sensitivity, equal distances keep the first object: %ld of %ld searches differ (%s)\n", bad, n,
            bad ? "caught" : "NOT CAUGHT");

    /* [5] time */
    build(0, 1500);
    for (int i = 0; i < 1500; i++) {
        objs[i].cat = i % 8; objs[i].obj = (uint8_t *)&objs[i] + 0x100;
        if (i < 1000) { objs[i].pos[0] = rf(1600, 3600); objs[i].pos[1] = rf(1600, 3600); }
        else { objs[i].pos[0] = rf(0, 5120); objs[i].pos[1] = rf(0, 5120); }
    }
    link_all(objs, 1500, NULL);
    query q = {{0}, {0}, 250, 0, 0, 2};
    static const char *what[] = {"flee scan away from the battle", "flee scan inside the battle", "map-wide closest"};
    double us[3][3]; long cands[3] = {0};
    for (int pass = 0; pass < 2; pass++) {
      if (pass) {                                              /* the original as in the game: distcalc on */
          gp_va_offset = offa;
          int dc_ok = gp_patch_distcalc();
          gp_va_offset = 0;
          if (!dc_ok) verdict(1, "[5] distcalc did not apply to the original copy\n");
      }
      for (int s = 0; s < 3; s++) {
        for (int k = pass ? 0 : 0; k < (pass ? 1 : 2); k++) {
            uint32_t r0 = 777;
            LONG cc = gp_ac_stats[2];
            uint64_t t0 = now_us();
            for (int i = 0; i < 4000; i++) {
                rs = r0 + i;
                if (s == 0) { q.pos[0] = rf(0, 1500); q.pos[1] = rf(0, 5120); q.r = 250; }
                else if (s == 1) { q.pos[0] = rf(1600, 3600); q.pos[1] = rf(1600, 3600); q.r = 250; }
                else { q.pos[0] = rf(0, 5120); q.pos[1] = rf(0, 5120); q.r = 999999; }
                q.nf = 2;
                filts[0] = (mfilt){filt_vt, &filts[1], 0xf0, 100, 0}; filts[1] = (mfilt){filt_vt, NULL, 0xffffffff, 30, 1};
                nlog = 0;
                run(k ? offb : offa, q.pos, q.r, NULL, 0, &filts[0], 0x007f);
            }
            us[s][pass ? 2 : k] = (now_us() - t0) / 4000.0;
            if (k) cands[s] = gp_ac_stats[2] - cc;
        }
      }
    }
    for (int s = 0; s < 3; s++)
        printf("[5] %s (%.1f candidates): original %.2f us, with distcalc (as installed) %.2f us, aiclosest %.2f us per "
               "search\n", what[s], cands[s] / 4000.0, us[s][0], us[s][2], us[s][1]);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
