/* scantree: the quadtree walk of the partition manager's range query (test t_scan).
 *
 * RotWK keeps every object in one of 21 quadtrees (one per owning player slot and one for none;
 * PartitionManager +0x18, 12-byte vectors of 8-byte nodes in preorder: {objects below, list head}).
 * iterateObjectsInRange 0xa3c4e0 (142 call sites through 0xa39340: the AI's mood-target scans,
 * auras, fear, stealth detection, hunts) turns the radius into a box of leaf cells and, for each
 * tree its filters allow, calls the walk 0xa3a860: a recursion with 15 stack arguments that, at every
 * node overlapping the box, runs each object through the distance function of the query
 * (table 0xdbdaf8), getObject, the filter chain and an append to the result vector.
 * This replacement (the call at 0xa3c659 is redirected; 0xa3a860 itself is untouched) does the same
 * walk in the same order with:
 *   - the 2D distance functions (centre 0xa3a7a0 and bounding circle 0xa3ae50, the two the game uses,
 *     §17) inline in SSE, after the same virtual getter calls in the same order. Exact: every value
 *     is a float operation the x87 original rounds the same way at 24-bit precision; inputs whose
 *     result could overflow or underflow the float range (|coordinate| >= 2^62, 0 < |dx| < 2^-62 ...)
 *     and any other FPU mode run the table's function and the original's x87 compare (asm below);
 *   - the filter chain (0xa39450) and the append's fast path (0xa3a3a0) inline: the same virtual
 *     calls, the same stores; a full vector goes through the original append (its allocator).
 * Region queries (no position) run the original walk. */
#include "gp_scale.h"
#include <string.h>

volatile LONG gp_scan_stats[5];
static uint32_t dc0, dc1, orig_walk, orig_append;
static int on;
static DWORD last_tick;
static LONG last[5], nwalks;

typedef struct { void **vt; } iface;
typedef struct entry { uint32_t pad0; iface *it; uint32_t pad[3]; struct entry *next; } entry;   /* next at +0x14 */
typedef struct filt { void **vt; struct filt *next; } filt;
typedef struct { uint8_t *begin, *end, *cap, *cursor; } payload;
typedef const float *(__attribute__((thiscall)) *getpos_fn)(iface *);
typedef const uint8_t *(__attribute__((thiscall)) *getgeom_fn)(iface *);
typedef void *(__attribute__((thiscall)) *getobj_fn)(iface *);
typedef char (__attribute__((thiscall)) *allow_fn)(filt *, void *);
typedef void (__attribute__((thiscall)) *append_fn)(payload **, void *, uint32_t);
typedef uint32_t (__attribute__((thiscall)) *walk_fn)(void *, payload **, uint32_t *, uint32_t, int, int, int, int,
                                                      int, int, int, const float *, uint32_t, const float *, void *, filt *);

/* x87, exactly as the original: the table's distance function, or (after the getters, which the C
 * code calls) the arithmetic of 0xa3a7a0 / 0xa3ae50; then the walk's compare. Each returns 1 if
 * accepted (st0 <= r2 or unordered) and stores the float the original appends to *d2. */
int gp_scan_dist(void *fn, const float *pos, iface *it, uint32_t r2, float *d2);
int gp_scan_x0(const float *p, const float *pos, uint32_t r2, float *d2);
int gp_scan_x1(const float *p, const float *pos, const float *rad, uint32_t r2, float *d2);
__asm__(".text\n.globl _gp_scan_dist\n_gp_scan_dist:\n"
"  pushl 16(%esp)\n  pushl 16(%esp)\n  pushl 16(%esp)\n  call *16(%esp)\n  addl $12, %esp\n"
"  movl 20(%esp), %eax\n  jmp 9f\n"
".globl _gp_scan_x0\n_gp_scan_x0:\n"
"  movl 4(%esp), %eax\n  movl 8(%esp), %ecx\n"
"  flds 4(%eax)\n  fsubs 4(%ecx)\n  flds (%eax)\n  fsubs (%ecx)\n  fld %st(0)\n  fmul %st(1), %st\n"
"  fld %st(2)\n  fmul %st(3), %st\n  faddp %st, %st(1)\n  fstp %st(2)\n  fstp %st(0)\n"
"  movl 16(%esp), %eax\n  fsts (%eax)\n  fcomps 12(%esp)\n  jmp 8f\n"
".globl _gp_scan_x1\n_gp_scan_x1:\n"
"  movl 4(%esp), %eax\n  movl 8(%esp), %ecx\n  movl 20(%esp), %edx\n"
"  flds 4(%eax)\n  fsubs 4(%ecx)\n  flds (%eax)\n  fsubs (%ecx)\n  fld %st(0)\n  fmul %st(1), %st\n"
"  fld %st(2)\n  fmul %st(3), %st\n  faddp %st, %st(1)\n  fstps (%edx)\n  fstp %st(0)\n  fstp %st(0)\n"
"  flds (%edx)\n  fsqrt\n  movl 12(%esp), %ecx\n  fsubs (%ecx)\n  fcoms _gp_scan_zero\n  fld %st(0)\n"
"  fnstsw %ax\n  testb $5, %ah\n  jp 1f\n  fmulp %st, %st(1)\n  fchs\n  jmp 2f\n1: fmulp %st, %st(1)\n"
"2: movl %edx, %eax\n  fsts (%eax)\n  fcomps 16(%esp)\n  jmp 8f\n"
"9: fsts (%eax)\n  fcomps 16(%esp)\n"
"8: fnstsw %ax\n  testb $0x41, %ah\n  setnz %al\n  movzbl %al, %eax\n  ret\n"
".data\n.balign 4\n_gp_scan_zero: .long 0\n.text\n");

static inline uint32_t bits(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }
static inline float flt(uint32_t u) { float f; memcpy(&f, &u, 4); return f; }
/* |v| < 2^62 (finite) and (v == 0 or |v| >= 2^-62): its square is a normal float or zero */
static inline int sq_ok(float v) { uint32_t e = (bits(v) >> 23) & 0xff; return e < 127 + 62 && (e >= 127 - 62 || !(bits(v) << 1)); }
static inline int small(float v) { return ((bits(v) >> 23) & 0xff) < 127 + 62; }

typedef struct {
    payload **res; int minx, miny, maxx, maxy; const float *pos; uint32_t r2; float r2f; void *dp; filt *filters;
    int fast; LONG nodes, cands, inl, tab;
} walk_ctx;

/* 1 if accepted; *d2 the float the original appends. For the two 2D functions the getters run here,
 * once each and in the original's order, then SSE (fast mode, safe range) or the x87 replica. */
static int dist(walk_ctx *c, iface *it, float *d2)
{
    int k = c->dp == (void *)(uintptr_t)dc0 ? 0 : c->dp == (void *)(uintptr_t)dc1 ? 1 : -1;
    if (k < 0) { c->tab++; return gp_scan_dist(c->dp, c->pos, it, c->r2, d2); }
    const float *p = ((getpos_fn)it->vt[1])(it);
    const float *rad = k ? (const float *)(((getgeom_fn)it->vt[0])(it) + 0x10) : NULL;
    if (c->fast && small(p[0]) && small(p[1]) && small(c->pos[0]) && small(c->pos[1])) {
        float dx = p[0] - c->pos[0], dy = p[1] - c->pos[1];
        if (sq_ok(dx) && sq_ok(dy)) {
            float q = dx * dx + dy * dy;
            if (k) {
                float d = __builtin_sqrtf(q) - *rad;
                q = d * d;
                if (!small(*rad) || !sq_ok(d)) goto x87;
                if (bits(d) > 0x80000000u) q = -q;              /* d < 0 (not -0): -(d*d) */
            }
            c->inl++; *d2 = q;
            return !(q > c->r2f);
        }
    }
x87:
    c->tab++;
    return k ? gp_scan_x1(p, c->pos, rad, c->r2, d2) : gp_scan_x0(p, c->pos, c->r2, d2);
}

static void walk(walk_ctx *c, uint32_t *node, uint32_t s, int nx, int ny, int size)
{
    for (;;) {
        c->nodes++;
        for (entry *e = (entry *)(uintptr_t)node[1]; e; e = e->next) {
            iface *it = e->it;
            float d2;
            c->cands++;
            if (!dist(c, it, &d2)) continue;
            void *obj = ((getobj_fn)it->vt[3])(it);
            if (!obj) continue;
            filt *f = c->filters;
            for (; f; f = f->next) if (!((allow_fn)f->vt[1])(f, obj)) break;
            if (f) continue;
            payload *pl = *c->res;
            if (pl->end != pl->cap) {
                ((uint32_t *)pl->end)[0] = (uint32_t)(uintptr_t)obj;
                ((uint32_t *)pl->end)[1] = bits(d2);
                pl->end += 8;
                pl->cursor = pl->begin;
            } else ((append_fn)(uintptr_t)orig_append)(c->res, obj, bits(d2));
        }
        if (!node[0]) return;
        int h = size / 2;
        uint32_t *ch = node + 2, cs = s >> 2;
        if (c->miny < ny + h) {
            if (c->minx < nx + h) walk(c, ch, cs, nx, ny, h);
            if (c->maxx >= nx + h) walk(c, ch + 2 * s, cs, nx + h, ny, h);
        }
        if (c->maxy < ny + h) return;
        if (c->minx < nx + h) walk(c, ch + 4 * s, cs, nx, ny + h, h);
        if (c->maxx < nx + h) return;
        node = ch + 6 * s; s = cs; nx += h; ny += h; size = h;   /* the original's tail loop */
    }
}

static void periodic(void)
{
    if (++nwalks & 255) return;
    DWORD t = GetTickCount();
    if (t - last_tick < gp_scale_period_ms) return;
    LONG d[5];
    for (int i = 0; i < 5; i++) { d[i] = gp_scan_stats[i] - last[i]; last[i] = gp_scan_stats[i]; }
    gp_log("scantree: last %lu s, %ld tree walks, %ld nodes, %ld candidates (%ld distances inline, %ld through "
           "the table)", (t - last_tick) / 1000, d[0], d[1], d[2], d[3], d[4]);
    last_tick = t;
}

uint32_t __attribute__((thiscall)) gp_scantree(void *pm, payload **res, uint32_t *node, uint32_t s, int minx, int miny,
    int maxx, int maxy, int nx, int ny, int size, const float *pos, uint32_t r2, const float *region, void *dp, filt *filters)
{
    if (!pos)
        return ((walk_fn)(uintptr_t)orig_walk)(pm, res, node, s, minx, miny, maxx, maxy, nx, ny, size, pos, r2, region, dp, filters);
    walk_ctx c = {res, minx, miny, maxx, maxy, pos, r2, flt(r2), dp, filters, 0, 0, 0, 0, 0};
    uint16_t cw; uint32_t mx;
    __asm__ volatile("fnstcw %0\n\tstmxcsr %1" : "=m"(cw), "=m"(mx));
    c.fast = (cw & 0xf3f) == 0x3f && (mx & 0xffc0) == 0x1f80;   /* x87 24-bit, nearest, masked; SSE likewise, no FTZ/DAZ */
    walk(&c, node, s, nx, ny, size);
    gp_scan_stats[0]++; gp_scan_stats[1] += c.nodes; gp_scan_stats[2] += c.cands;
    gp_scan_stats[3] += c.inl; gp_scan_stats[4] += c.tab;
    periodic();
    return 0;
}

void gp_scan_exit_log(void)
{
    if (on) gp_log("exit: scantree %ld walks, %ld nodes, %ld candidates (%ld distances inline, %ld through the table)",
                   gp_scan_stats[0], gp_scan_stats[1], gp_scan_stats[2], gp_scan_stats[3], gp_scan_stats[4]);
}

int gp_patch_scantree(void)
{
    static const uint8_t call_walk[] = {0xe8, 0x02, 0xe2, 0xff, 0xff};     /* 0xa3c659: call 0xa3a860 */
    static const uint8_t zero[4] = {0};
    gp_site s[8];
    gp_site_hash(&s[0], 0xa3a860, 0x29d, GP_FNV_A3A860);
    gp_site_hash(&s[1], 0xa3a3a0, 0x67, GP_FNV_A3A3A0);
    gp_site_hash(&s[2], 0xa39450, 0x31, GP_FNV_A39450);
    gp_site_hash(&s[3], 0xa3a7a8, 0x1e, GP_FNV_A3A7A8);
    gp_site_hash(&s[4], 0xa3ae58, 0x4b, GP_FNV_A3AE58);
    gp_site_hash(&s[5], 0xa3c4e0, 0x20d, GP_FNV_A3C4E0);
    gp_site_init(&s[6], 0xc1b594, zero, 4); s[6].wlen = 0;          /* the 0.0f the circle function compares with */
    gp_site_init(&s[7], 0xa3c659, call_walk, 5);
    gp_rel32(&s[7], 0, 0xe8, (void *)gp_scantree);
    dc0 = 0xa3a7a0 + gp_va_offset; dc1 = 0xa3ae50 + gp_va_offset;
    orig_walk = 0xa3a860 + gp_va_offset; orig_append = 0xa3a3a0 + gp_va_offset;
    if (!gp_apply("scantree", s, 8)) return 0;
    on = 1; last_tick = GetTickCount();
    return 1;
}
