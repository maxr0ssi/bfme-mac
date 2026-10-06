/* t_aura: aura3d (p_aura.c) against the original 3D distance functions and range query, all run from
 * the exe's bytes. Two relocated copies of the partition code (0xa39000-0xa3d000, the allocator stubs
 * 0x42f000-0x431000, 0xb4e370): A untouched, B patched by the installers (first aura3d alone, so the
 * original walk calls the new functions; then distcalc and scantree on top, as the game runs them).
 *   [0] aura3d applies to the original bytes
 *   [1] 0xa3a7d0 (centre 3D) and 0xa3aeb0 (bounding sphere 3D) alone, A against B, full machine state
 *       (lm_harness.h) from a mock object whose getters clobber ecx/edx/xmm0-1 and whose two geometry
 *       calls return different blocks: map positions, near points, inside the sphere, wide exponents,
 *       any bits, specials, huge and tiny values; then 7 other x87 modes and 3 other MXCSR modes
 *   [2] the range query 0xa3c4e0 (t_scan's mock world: 21 quadtrees built by the game's linkNode,
 *       getter and filter call logs): random worlds and queries, distance types 0-3 (mostly 2-3),
 *       radii up to 1e12, filters, sorts, regions, special values; B with aura3d alone, then with
 *       distcalc + scantree; same result vectors (objects, distance bits, order) and call logs
 *   [3] the real pulses: 1,300 objects of 16 players over 5,120 units, the spells' radii (999999, 1e12,
 *       9999999, 99999, 9999), distance types 3 and 2, no filters, unsorted, casters anywhere
 *   [4] sensitivity: B with a reassociated sum (gp_au_sens = 1) must be caught by [1] and [3]
 *   [5] ms per map-wide pulse: EA's code, as installed (distcalc + scantree), and with aura3d
 * usage: t_aura.exe <path to lotrbfme2ep1.exe 2.02> [thousands of inputs for [1] (default 500; [2]: a fifth)] */
#include "orig.h"
#include "gp_scale.h"
#include "gp_logic.h"
#include "p_aura.h"
#include "lm_harness.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include <xmmintrin.h>

static int fails, quiet, shown;                    /* quiet: [4], whose mismatches are expected */
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs = 0x2a7a3d01;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
static float rf(float lo, float hi) { return lo + (hi - lo) * (rnd() >> 8) / 16777216.0f; }
static float fb(uint32_t u) { float f; memcpy(&f, &u, 4); return f; }
static uint32_t bf(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }
static float wide(int emin, int emax)
{
    int e = emin + (int)(rnd() % (unsigned)(emax - emin + 1));
    return fb((rnd() & 0x807fffffu) | (uint32_t)(e + 127) << 23);
}
static const uint32_t specials[] = {0, 0x80000000, 0x7f800000, 0xff800000, 0x7fc00000, 0xffc00000, 0x7f800001,
    0xff812345, 0x00000001, 0x80000001, 0x007fffff, 0x00800000, 0x7f7fffff, 0xff7fffff, 0x5f800000, 0x1f800000};
static float special(void) { return fb(specials[rnd() % (sizeof specials / 4)]); }
static void restore_modes(void) { uint16_t cw = 0x027f; __asm__ volatile("fninit\n fldcw %0" : : "m"(cw)); _mm_setcsr(0x1f80); }

static uint32_t offa, offb;

/* ---- [1] the functions alone -------------------------------------------------------------- */
uint32_t ma_seq, ma_gn;
__asm__(".text\n"
"_ma_pos:\n  movl _ma_seq, %eax\n  leal 2(,%eax,4), %eax\n  movl %eax, _ma_seq\n"
"  leal 16(%ecx), %eax\n  movl _ma_seq, %edx\n  xorl $0x6e6e0002, %edx\n  movl _ma_seq, %ecx\n"
"  xorl $0x6e6e1002, %ecx\n  movd %ecx, %xmm1\n  ret\n"
"_ma_geom:\n  movl _ma_seq, %eax\n  leal 1(,%eax,4), %eax\n  movl %eax, _ma_seq\n"
"  movl _ma_gn, %eax\n  xorl $1, _ma_gn\n  shll $6, %eax\n  leal 64(%ecx,%eax), %eax\n"
"  movl _ma_seq, %edx\n  xorl $0x6e6e0001, %edx\n  movl _ma_seq, %ecx\n  xorl $0x6e6e1001, %ecx\n"
"  movd %edx, %xmm0\n  movd %ecx, %xmm1\n  ret\n");
void ma_pos(void); void ma_geom(void);
typedef struct { void **vt; uint32_t pad[3]; float pos[4]; uint8_t pad2[32]; float g[2][16]; } fobj;
static void *fvt[8] = {(void *)ma_geom, (void *)ma_pos};

static void gen(float p[3], float q[3], float h[2], float r[2], int kind)
{
    for (int k = 0; k < 3; k++) p[k] = k < 2 ? rf(0, 6000) : rf(0, 100), q[k] = p[k] + rf(-400, 400);
    for (int k = 0; k < 2; k++) h[k] = rf(0, 60), r[k] = rf(0, 300);
    switch (kind) {
    case 1: for (int k = 0; k < 3; k++) q[k] = rnd() & 1 ? p[k] : p[k] + rf(-1e-3f, 1e-3f);
            for (int k = 0; k < 2; k++) { h[k] = rnd() & 1 ? 0 : -q[2] + p[2]; r[k] = rnd() & 1 ? 0 : rf(0, 50); } break;
    case 2: for (int k = 0; k < 3; k++) p[k] = wide(-40, 40), q[k] = wide(-40, 40);
            for (int k = 0; k < 2; k++) { h[k] = wide(-40, 40), r[k] = wide(-40, 40); } break;
    case 3: for (int k = 0; k < 3; k++) p[k] = fb(rnd()), q[k] = fb(rnd());
            for (int k = 0; k < 2; k++) { h[k] = fb(rnd()), r[k] = fb(rnd()); } break;
    case 4: for (int n = 1 + rnd() % 2; n; n--) { int k = rnd() % 10;
                *(k < 3 ? &p[k] : k < 6 ? &q[k - 3] : k < 8 ? &h[k - 6] : &r[k - 8]) = special(); } break;
    case 5: for (int k = 0; k < 3; k++) p[k] = wide(55, 127), q[k] = wide(55, 127);
            for (int k = 0; k < 2; k++) { h[k] = wide(50, 127), r[k] = wide(50, 127); } break;
    case 6: for (int k = 0; k < 3; k++) p[k] = wide(-149, -55), q[k] = wide(-149, -55);
            for (int k = 0; k < 2; k++) { h[k] = wide(-149, -55), r[k] = wide(-149, -60); } break;
    case 7: for (int k = 0; k < 2; k++) r[k] = rf(300, 900); break;               /* inside the sphere */
    default: break;
    }
}
/* one input through A and B; 0 = identical. which 0: centre 3D, 1: bounding sphere 3D */
static const char *one_fn(int which, uint32_t cw, uint32_t mx, int kind, uint32_t *neg)
{
    static fobj o, ob[2]; static float qb[8], qs[2][8];
    float p[3], q[3], h[2], r[2];
    gen(p, q, h, r, kind);
    uint32_t gn = rnd() & 1, third = rnd();
    hc_t c[2]; uint32_t seq[2];
    for (int v = 0; v < 2; v++) {
        memset(&o, 0xa5, sizeof o); o.vt = fvt;
        memcpy(o.pos, p, 12);
        for (int k = 0; k < 2; k++) o.g[k][5] = r[k], o.g[k][8] = h[k];
        for (int k = 0; k < 8; k++) qb[k] = fb(0x7fc00000u + k);
        memcpy(&qb[2], q, 12);
        hc_init(&c[v], (which ? 0xa3aeb0 : 0xa3a7d0) + (v ? offb : offa), 3);
        c[v].cw = cw; c[v].mxcsr = mx;
        c[v].args[0] = (uint32_t)(uintptr_t)&qb[2]; c[v].args[1] = (uint32_t)(uintptr_t)&o; c[v].args[2] = third;
        ma_seq = 0; ma_gn = gn;
        hc_call(&c[v]); seq[v] = ma_seq;
        ob[v] = o; memcpy(qs[v], qb, sizeof qb);
    }
    restore_modes();
    if (which && (c[0].fpu[28 + 9] & 0x80)) ++*neg;
    /* 0xa3aeb0 leaves its sign test's FPU status word in ax; every caller overwrites ax with its own
     * fnstsw first (aura3d's SSE path leaves the geometry pointer there): the upper half is compared */
    const char *d = hc_diff(&c[0], &c[1], which ? 1 : 0, 0);
    if (!*d && which && (c[0].out[0] >> 16) != (c[1].out[0] >> 16)) d = "eax upper half";
    if (!*d && memcmp(&ob[0], &ob[1], sizeof ob[0])) d = "object memory";
    if (!*d && memcmp(qs[0], qs[1], sizeof qs[0])) d = "position memory";
    if (!*d && seq[0] != seq[1]) d = "getter call sequence";
    if (*d && !quiet && shown++ < 20)
        printf("  MISMATCH %s (%s) kind %d p %08x %08x %08x q %08x %08x %08x h %08x %08x r %08x %08x\n",
               which ? "sphere" : "centre", d, kind, bf(p[0]), bf(p[1]), bf(p[2]), bf(q[0]), bf(q[1]), bf(q[2]),
               bf(h[0]), bf(h[1]), bf(r[0]), bf(r[1]));
    return d;
}
static long fn_pass(long n, uint32_t cw, uint32_t mx, int kind_max, long *nbad, uint32_t *neg)
{
    long bad = 0;
    for (long i = 0; i < n; i++)
        for (int w = 0; w < 2; w++) bad += *one_fn(w, cw, mx, kind_max ? (int)(rnd() % (kind_max + 1)) : 0, neg) != 0;
    *nbad = bad;
    return 2 * n;
}

/* ---- the mock world (t_scan's) -------------------------------------------------------------- */
enum { L = 7, NCELL = 1 << L, NNODE = (((1 << (2 * L + 2)) - 1) / 3), MAXOBJ = 4000, LOGN = 1 << 17 };
typedef struct { void **vt; float pos[3]; float geom[12]; int cat; void *obj; int idx; } mobj;
typedef struct { uint32_t w[12]; } mentry;
typedef struct { void **vt; void *next; uint32_t mask; int rate; int id; } mfilt;
static uint8_t pm[0x140];
static mobj *objs; static mentry *ents;
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
static uint32_t __attribute__((thiscall)) f_mask(mfilt *f) { return f->mask; }
static void *filt_vt[3] = {NULL, (void *)f_allow, (void *)f_mask};
static mfilt filts[3];
static void *__cdecl m_alloc(uint32_t n, int a, int b) { (void)a; (void)b; return calloc(1, n ? n : 1); }
static void __cdecl m_free(void *p, int k) { (void)k; free(p); }

static void table_for(uint32_t off)
{
    static const uint32_t dc[5] = {0xa3a7a0, 0xa3ae50, 0xa3a7d0, 0xa3aeb0, 0xa3c7d0};
    for (int i = 0; i < 5; i++) ((uint32_t *)0xdbdaf8)[i] = dc[i] + off;
}
static float coord(int mode)
{
    switch (mode) {
    case 0: return rf(-100, 5300);
    case 1: return special();
    case 2: return ldexpf(rf(1, 2), (int)(rnd() % 160) - 80);
    default: return rf(1500, 3500);
    }
}
/* n objects; weird: special and wide values; spells: 16 players, real heights and radii */
static void build(int weird, int n, int spells)
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
        memset(o, 0, sizeof *o);
        o->vt = obj_vt; o->idx = i; o->cat = spells ? i % 16 : (int)(rnd() % 10) - 1;
        int m = weird && rnd() % 8 == 0 ? 1 + rnd() % 2 : i < n * 2 / 3 ? 3 : 0;
        if (spells) m = i % 3 ? 0 : 3;
        o->pos[0] = coord(m); o->pos[1] = coord(rnd() % 6 ? m : 0); o->pos[2] = rf(0, 50);
        if (i && rnd() % 20 == 0) memcpy(o->pos, objs[rnd() % i].pos, 8);
        o->geom[4] = weird && rnd() % 10 == 0 ? coord(1 + rnd() % 2) : rf(3, 40);   /* +0x10 circle */
        o->geom[5] = weird && rnd() % 10 == 0 ? coord(1 + rnd() % 2) : rf(3, 40);   /* +0x14 sphere */
        o->geom[8] = weird && rnd() % 10 == 0 ? coord(1 + rnd() % 2) : rf(1, 30);   /* +0x20 height */
        if (weird && rnd() % 10 == 0) o->pos[2] = coord(1 + rnd() % 2);
        o->obj = rnd() % 30 ? (uint8_t *)o + 0x100 : NULL;
        ents[i].w[1] = (uint32_t)(uintptr_t)o;
        typedef void (__attribute__((thiscall)) *link_fn)(void *pm, void *e);
        ((link_fn)(uintptr_t)(0xa3b220 + offa))(pm, &ents[i]);
    }
}

typedef void *(__attribute__((thiscall)) *range_fn)(void *pm, void **ret, const float *pos, float r, const float *region,
                                                      int dc, mfilt *filters, int sort);
typedef struct { uint32_t n; uint32_t *v; } result;
static result run(uint32_t off, const float *pos, float r, const float *region, int dc, mfilt *f, int sort, uint32_t cw)
{
    table_for(off);
    void *h = NULL;
    uint16_t cw0; __asm__ volatile("fnstcw %0" : "=m"(cw0));
    uint16_t c16 = (uint16_t)cw; __asm__ volatile("fldcw %0" :: "m"(c16));
    ((range_fn)(uintptr_t)(0xa3c4e0 + off))(pm, &h, pos, r, region, dc, f, sort);
    __asm__ volatile("fldcw %0" :: "m"(cw0));
    uint32_t *p = h;
    result res = {(p[1] - p[0]) / 4, NULL};
    res.v = malloc(res.n * 4 + 4);
    memcpy(res.v, (void *)(uintptr_t)p[0], res.n * 4);
    if (p[0]) free((void *)(uintptr_t)p[0]);
    free(p);
    return res;
}
/* the same query through A and B: 1 = identical results and call logs (sorted only without NaN keys,
 * whose order EA's sort leaves to the memory around the vector, t_scan) */
static long nansorts;
static int query(const float *pos, float r, const float *region, int dc, mfilt *fl, int sort, uint32_t cw, long *items)
{
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
        a = run(offa, pos, r, region, dc, fl, pass ? sort : 0, cw);
        na = nlog; memcpy(loga, logbuf, na * 4);
        nlog = 0;
        b = run(offb, pos, r, region, dc, fl, pass ? sort : 0, cw);
        ok = a.n == b.n && !memcmp(a.v, b.v, a.n * 4) && na == nlog && !memcmp(loga, logbuf, na * 4);
        if (!pass) *items += a.n / 2;
    }
    if (!ok && !quiet && shown++ < 20) printf("  MISMATCH dc %d r %08x pos %08x,%08x filters %s sort %d: %u/%u items, %d/%d log\n",
        dc, bf(r), pos ? bf(pos[0]) : 0, pos ? bf(pos[1]) : 0, fl ? "yes" : "no", sort, a.n / 2, b.n / 2, na, nlog);
    free(a.v); free(b.v);
    return ok;
}
static int rand_query(uint32_t cw, long *items)
{
    float pos[3], reg[6], r;
    int region = rnd() % 25 == 0, dc = rnd() % 4, sort = rnd() % 3, nf = rnd() % 4;
    if (rnd() % 3) dc = 2 + rnd() % 2;
    int m = rnd() % 10 == 0 ? 1 + rnd() % 2 : rnd() % 2 ? 3 : 0;
    pos[0] = coord(m); pos[1] = coord(m); pos[2] = rnd() % 10 ? rf(0, 50) : coord(1 + rnd() % 2);
    static const float big[] = {999999.0f, 1e12f, 9999999.0f, 99999.0f, 9999.0f};
    switch (rnd() % 8) {
    case 0: r = rf(0, 40); break;
    case 1: r = coord(1 + rnd() % 2); break;
    case 2: r = rf(0, 6000); break;
    case 3: r = big[rnd() % 5]; break;
    default: r = rf(100, 600);
    }
    for (int k = 0; k < 3; k++) reg[k] = coord(m), reg[3 + k] = reg[k] + rf(0, 800);
    for (int k = 0; k < nf; k++) {
        mfilt *f = &filts[k];
        f->vt = filt_vt; f->next = k + 1 < nf ? &filts[k + 1] : NULL; f->id = k;
        f->mask = rnd() % 3 ? rnd() & 0x1fffff : 0xffffffff; f->rate = rnd() % 3 ? 50 : 100;
    }
    return query(region ? NULL : pos, r, region ? reg : NULL, dc, nf ? &filts[0] : NULL, sort, cw, items);
}

/* [3] the spells' pulses: AttributeModifierNugget's shape (dc 3, r = max(radius, 1), no filters, unsorted) */
static const float spell_r[] = {999999.0f, 1e12f, 9999999.0f, 99999.0f, 9999.0f};
static long spell_pass(int n, long *items, long *bad)
{
    long q = 0;
    for (int i = 0; i < n; i++) {
        float pos[3] = {rf(0, 5120), rf(0, 5120), rf(0, 50)};
        if (i % 4 == 0) memcpy(pos, objs[rnd() % 1300].pos, 12);       /* the caster's own spot */
        for (int k = 0; k < 5; k++)
            for (int dc = 3; dc >= 2; dc--) { q++; *bad += !query(pos, spell_r[k], NULL, dc, NULL, 0, 0x007f, items); }
    }
    return q;
}

static double pulse_ms(uint32_t off, int dc, int n)
{
    uint64_t t0 = now_us();
    for (int i = 0; i < n; i++) {
        float pos[3] = {objs[i % 1300].pos[0], objs[i % 1300].pos[1], objs[i % 1300].pos[2]};
        nlog = 0;
        result r = run(off, pos, 999999.0f, NULL, dc, NULL, 0, 0x007f);
        free(r.v);
    }
    return (now_us() - t0) / 1000.0 / n;
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
    long nk = (argc > 2 ? atol(argv[2]) : 500) * 1000;
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
        if (orig_map_at(0xa39000, 0x4000, off) || orig_map_at(0x42f000, 0x2000, off) || orig_map_at(0xb4e000, 0x1000, off) ||
            orig_map_at(0xc1b000, 0x1000, off))
            return 2;
    }
    gp_va_offset = offb;
    int ok = gp_patch_aura3d();
    gp_va_offset = 0;
    verdict(!ok, "[0] aura3d: %s to the original bytes (relocated copy)\n", ok ? "applied" : "NOT applied");
    if (!ok) { printf("FAIL\n"); return 1; }
    uint8_t patched[2][8];
    memcpy(patched[0], (void *)(uintptr_t)(0xa3a7d0 + offb), 8); memcpy(patched[1], (void *)(uintptr_t)(0xa3aeb0 + offb), 8);
    objs = calloc(MAXOBJ, sizeof *objs); ents = calloc(MAXOBJ, sizeof *ents);
    logbuf = malloc(LOGN * 4); loga = malloc(LOGN * 4);

    /* [1] */
    long bad, n; uint32_t neg = 0;
    LONG s0[4]; memcpy(s0, (void *)gp_au_stats, sizeof s0);
    n = fn_pass(nk, 0x007f, 0x1f80, 7, &bad, &neg);
    verdict(bad != 0, "[1] %ld calls (centre and sphere 3D, 8 input kinds), game FPU mode: %ld mismatches; x87 original "
            "ran for %ld / %ld; %u results negative (inside the sphere)\n", n, bad, gp_au_stats[2] - s0[2],
            gp_au_stats[3] - s0[3], neg);
    static const uint32_t modes[][2] = {{0x027f, 0x1f80}, {0x037f, 0x1f80}, {0x047f, 0x1f80}, {0x087f, 0x1f80},
        {0x0c7f, 0x1f80}, {0x107f, 0x1f80}, {0x0a7f, 0x1f80}, {0x007f, 0x9f80}, {0x007f, 0x1fc0}, {0x007f, 0x3f80}};
    long badm = 0, nm = 0;
    memcpy(s0, (void *)gp_au_stats, sizeof s0);
    for (int m = 0; m < 10; m++) { long b; nm += fn_pass(nk / 50, modes[m][0], modes[m][1], 7, &b, &neg); badm += b; }
    verdict(badm != 0, "[1] %ld calls in 7 other x87 modes (53/64-bit, down/up/chop, and 0x107f: the game's mode with "
            "the obsolete infinity bit, which runs SSE) and 3 MXCSR modes (FTZ, DAZ, down): %ld mismatches; %ld ran the "
            "x87 original\n", nm, badm, gp_au_stats[2] + gp_au_stats[3] - s0[2] - s0[3]);

    /* [2] */
    long items = 0, nq = nk / 5;
    for (int phase = 0; phase < 2; phase++) {
        if (phase) {
            gp_va_offset = offb;
            int ok2 = gp_patch_distcalc() && gp_patch_scantree();
            gp_va_offset = 0;
            verdict(!ok2, "[2] distcalc + scantree %s on the aura3d copy\n", ok2 ? "applied" : "NOT applied");
        }
        bad = 0; items = 0;
        for (long it = 0; it < nq; it++) {
            if (it % 2500 == 0) build(it % 5000 == 2500, it % 7500 == 0 ? 1300 : 200 + rnd() % 2500, 0);
            bad += !rand_query(0x007f, &items);
        }
        long badm2 = 0;
        for (int m = 0; m < 7; m++)
            for (long it = 0; it < nq / 50; it++) {
                if (it % 2500 == 0) build(1, 300 + rnd() % 1500, 0);
                badm2 += !rand_query(modes[m][0], &items);
            }
        verdict(bad + badm2 != 0, "[2] range queries, %s: %ld in the game's mode + %ld in 7 other x87 modes, %ld objects "
                "returned: %ld + %ld mismatches (%ld with a NaN key compared unsorted only)\n",
                phase ? "aura3d + distcalc + scantree" : "aura3d with the original walk", nq, 7 * (nq / 50), items, bad,
                badm2, nansorts);
    }

    /* [3] */
    build(0, 1300, 1);
    items = 0; bad = 0;
    long q = spell_pass(200, &items, &bad);
    verdict(bad != 0, "[3] the spells' pulses on 1,300 objects of 16 players: %ld queries (radius 999999, 1e12, 9999999, "
            "99999, 9999; distance types 3 and 2; casters anywhere), %ld objects returned: %ld mismatches\n", q, items, bad);

    /* [4] */
    gp_au_sens = 1;
    long sb; uint32_t sn = 0;
    quiet = 1;
    long sq = fn_pass(20000, 0x007f, 0x1f80, 0, &sb, &sn);
    long sbad = 0, sitems = 0;
    long sqq = spell_pass(20, &sitems, &sbad);
    quiet = 0; gp_au_sens = 0;
    verdict(sb == 0 || sbad == 0, "[4] sensitivity, a reassociated sum: %ld of %ld map calls and %ld of %ld pulses differ "
            "(must not be 0)\n", sb, sq, sbad, sqq);

    /* [5] */
    double t[3][3] = {{0}};
    for (int round = 0; round < 3; round++)
        for (int dc = 3; dc >= 1; dc--) {
            t[0][3 - dc] += pulse_ms(offa, dc, 60) / 3;
            memcpy((void *)(uintptr_t)(0xa3a7d0 + offb), "\x8b\x4c\x24\x08\x8b\x01\xff\x50", 8);   /* as installed */
            memcpy((void *)(uintptr_t)(0xa3aeb0 + offb), "\x83\xec\x0c\x56\x8b\x74\x24\x18", 8);
            t[1][3 - dc] += pulse_ms(offb, dc, 60) / 3;
            memcpy((void *)(uintptr_t)(0xa3a7d0 + offb), patched[0], 8);
            memcpy((void *)(uintptr_t)(0xa3aeb0 + offb), patched[1], 8);
            t[2][3 - dc] += pulse_ms(offb, dc, 60) / 3;
        }
    printf("[5] ms per map-wide pulse (1,300 objects, radius 999999, no filters, unsorted; 3 x 60 pulses each): distance "
           "type 3 (the modifier nuggets): EA's code %.3f, as installed (distcalc + scantree) %.3f, with aura3d %.3f; "
           "type 2: %.3f, %.3f, %.3f; for comparison the 2D type 1 (scantree inlines it): %.3f, %.3f, %.3f\n",
           t[0][0], t[1][0], t[2][0], t[0][1], t[1][1], t[2][1], t[0][2], t[1][2], t[2][2]);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
