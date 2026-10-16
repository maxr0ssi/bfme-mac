/* aigeom: distance type 4 of the partition manager's range scans, without the work that cannot change
 * its answer (test t_aigeom, docs/PERFORMANCE.md §30).
 *
 * DamageNugget's hit scan (0x90def0) asks iterateObjectsInRange 0xa3c4e0 for distance type 4 whenever
 * its radius is 10 or more (every splash, cleave, crush and spell radius, and the fortress spikes'
 * r 150 every 250 ms that FireWeaponUpdate fires); 0x700dda and 0x82e5fc ask for it too. Type 4 is
 * 0xa3c7d0, run for every object in the scan's box of quadtree cells: it builds a function-static
 * sphere GeometryInfo once (0xdef920), and per object
 *   - sets the sphere's radius to fsqrt(r2) and recomputes its bounds, calcBoundingStuff 0xad2860
 *     (~200 x87 instructions with five fsqrt);
 *   - asks the object for getGeometryInfo (vt slot 0), its angle (slot 2) and getPosition (slot 1);
 *   - runs GeometryInfo::bfmeIntersects 0xad2ce0(object geometry, its position and angle, the sphere,
 *     the query point, 0): per pair of shapes a fsin/fcos rotation of the shape offset, two
 *     AsciiString copies under the string lock, a z-range test and a 2D test (circle-circle 0xad48f0,
 *     box-circle 0xad4870 via 0xad45a0, box-box 0xad4790);
 *   - returns 0.0 if they intersect, else FLT_MAX (0xbd1910), which the scan's r2 test rejects.
 * Its callers read st0 only (the walk 0xa3a860 and scantree's thunk: fsts, fcomps r2).
 * The replacement:
 *   - recalculates the sphere's bounds only when its bytes (struct, shape array) or the x87 control
 *     word differ from the state right after its last recalculation: calcBoundingStuff is a function
 *     of those alone (it reads only the geometry and constants), so the skipped call would write
 *     what is already there. The sphere is a function static: no other code touches it. Its radius's
 *     fsqrt likewise only when r2's bits or the control word change;
 *   - makes the three getter calls in the original's order, then answers "apart" without
 *     bfmeIntersects when the 2D distance from the query point to the object's position exceeds,
 *     for every shape of type 0-2 (other types never intersect), 1.001 x (the offset's length + the
 *     shape's reach: |major| for circles, whose test is d <= |a + r|; the half diagonal for boxes,
 *     both half sides >= 0) + the sphere's radius (fsin/fcos/fsincos of one angle below 1e6 give
 *     cos^2 + sin^2 = 1 far inside the 0.1 %), plus a margin of 0.01 + 1e-4 x the
 *     magnitudes involved (the x87 original's rounding is ~1e-7 relative). Every 2D test then fails,
 *     whatever the z ranges, so the original returns FLT_MAX too. Any non-finite or huge value
 *     (> 1e7; angle > 1e6), a sphere that is not one centred type-0 shape, or a shape list that is not
 *     whole shapes: the original's bfmeIntersects runs;
 *   - otherwise the intersection test inline (isect_fast): per active shape its world position by the
 *     original's own 0xad22f0, the two z-range tests and circle-circle in SSE where SSE single equals
 *     the x87 24-bit result (operands 0 or 2^-60..2^60, squares normal), box-circle by the original's
 *     0xad4870; without the shape copies (two AsciiString copies under the string lock per pair) and
 *     the sphere's own rotation (offset 0, angle 0). Anything outside those ranges: the original
 *     bfmeIntersects with the original's arguments.
 * The static not yet built, or another FPU mode (x87 not 24-bit / nearest, MXCSR not the default): the
 * original runs from its top.
 * Exact: deterministic across machines, LAN-safe even against a player without it. */
#include "gp.h"
#include "p_ai.h"
#include <string.h>
#include <math.h>

#define GP_FNV_A3C7D0 0xf1c7c69500a8cf67ull   /* distance type 4, 0xfd bytes */
#define GP_FNV_AD2CE0 0x7f8f683f51fb1332ull   /* GeometryInfo::bfmeIntersects, 0x335 bytes */
#define GP_FNV_AD2860 0x99e0a4091b025ad5ull   /* calcBoundingStuff, 0x12d bytes */
#define GP_FNV_AD2700 0xfbd503d0499fe767ull   /* its shape helpers and 0xad2040 */
#define GP_FNV_AD2770 0xe5356f785e30f4f6ull
#define GP_FNV_AD2040 0x90ea6fd0bfaeab04ull
#define GP_FNV_AD22F0 0xa79b107eeacd6889ull   /* shape world position: offset rotated by fsin/fcos */
#define GP_FNV_AD4870 0x85376478a04a3e35ull   /* box-circle */
#define GP_FNV_AD48F0 0x7a13a85891f24999ull   /* circle-circle */
#define GP_FNV_AD45A0 0xd79884eb48887c3full   /* box contains circle */

#define AG_STATIC 0xdef920u                   /* the sphere GeometryInfo, 0x5c bytes */
#define AG_GUARD  0xdef97cu                   /* bit 0: built */
#define AG_ZERO   0xc1b594u                   /* 0.0f */
#define AG_FAR    0xbd1910u                   /* FLT_MAX */
#define SNAP_SHAPES 4

volatile LONG gp_ag_stats[5];
uint32_t gp_ag_sens;
uint32_t gp_ag_cont;                          /* 0xa3c7d6: the original after its first instruction */
static uint32_t calc_va, isect_va, va_world, va_boxc;
static int on;
static uint8_t snap[0x5c + SNAP_SHAPES * 0x24];
static uint32_t snap_len;
static uint16_t snap_cw;
static int snap_ok;
static float sq_rad;                          /* the last fsqrt(r2), for r2's bits and the control word */
static uint32_t sq_r2;
static uint16_t sq_cw;
static int sq_ok_;

typedef struct { void **vt; } iface;
typedef void *(__attribute__((thiscall)) *getp_fn)(iface *);
typedef float (__attribute__((thiscall)) *getf_fn)(iface *);
typedef void (__attribute__((thiscall)) *calc_fn)(void *);
typedef char (__attribute__((thiscall)) *isect_fn)(void *g, const float *pos, float ang, void *g2, const float *pos2,
                                                     uint32_t ang2);
typedef float (__cdecl *t4_fn)(const float *q, void *iface, float r2);

float __cdecl gp_ag_orig(const float *q, void *iface, float r2);
__asm__(".intel_syntax noprefix\n.text\n.globl _gp_ag_orig\n.balign 16\n_gp_ag_orig:\n"
        "  mov eax, dword ptr fs:[0]\n"                 /* the instruction the jmp replaced */
        "  jmp dword ptr [_gp_ag_cont]\n.att_syntax prefix\n");

static inline float x87_sqrt(float x)          /* flds; fsqrt; fstps, as the original */
{
    float r;
    __asm__ volatile("flds %1\n\tfsqrt\n\tfstps %0" : "=m"(r) : "m"(x));
    return r;
}

/* the shape count as the original computes it: (end - begin) * 0x38e38e39 >> 35, rounded to 0 */
static inline int32_t shape_count(uint32_t b, uint32_t e)
{
    int32_t hi = (int32_t)(((int64_t)(int32_t)(e - b) * 0x38e38e39) >> 32) >> 3;
    return hi + (int32_t)((uint32_t)hi >> 31);
}

static inline int fin(float v, float lim) { return fabsf(v) < lim; }   /* false for NaN and inf */

/* 1 when no shape of the object's geometry can meet the query circle in 2D (see the header) */
static int apart(const float *q, const float *p, float ang, const uint8_t *g, float r, const uint8_t *sp)
{
    const uint8_t *s = *(uint8_t *const *)(g + 0x2c), *e = *(uint8_t *const *)(g + 0x30);
    uint32_t n = (uint32_t)(e - s);
    if (n % 0x24 || n > 64 * 0x24) return 0;
    if (*(const int32_t *)sp != 0 || *(const float *)(sp + 0x10) != 0.0f || *(const float *)(sp + 0x14) != 0.0f) return 0;
    if (!fin(ang, 1e6f) || !fin(q[0], 1e7f) || !fin(q[1], 1e7f) || !fin(p[0], 1e7f) || !fin(p[1], 1e7f) || !fin(r, 1e7f))
        return 0;
    double dx = (double)q[0] - p[0], dy = (double)q[1] - p[1], d = sqrt(dx * dx + dy * dy);
    double mag = fabs(q[0]) + fabs(q[1]) + fabs(p[0]) + fabs(p[1]) + fabs(r);
    for (; s < e; s += 0x24) {
        int32_t t = *(const int32_t *)s;
        if (t < 0 || t > 2) continue;                                  /* no 2D test for these */
        float a = *(const float *)(s + 8), b = *(const float *)(s + 0xc);
        float ox = *(const float *)(s + 0x10), oy = *(const float *)(s + 0x14);
        if (!fin(a, 1e7f) || !fin(b, 1e7f) || !fin(ox, 1e7f) || !fin(oy, 1e7f)) return 0;
        if (t == 2 && (a < 0 || b < 0)) return 0;
        double ext, margin;
        if (!gp_ag_sens || gp_ag_sens == 2) {
            ext = 1.001 * (sqrt((double)ox * ox + (double)oy * oy) + (t == 2 ? sqrt((double)a * a + (double)b * b) : fabs(a)));
            margin = 0.01 + 1e-4 * (mag + ext);
        } else if (gp_ag_sens == 1) {  /* test only: a bug, the shape offsets forgotten */
            ext = 1.001 * (t == 2 ? sqrt((double)a * a + (double)b * b) : fabs(a));
            margin = 0.01 + 1e-4 * (mag + ext);
        } else {                       /* test only: the true reach, no margin for the original's rounding */
            ext = sqrt((double)ox * ox + (double)oy * oy) + (t == 2 ? sqrt((double)a * a + (double)b * b) : fabs(a));
            margin = 0;
        }
        if (!(d > ext + fabs(r) + margin)) return 0;
    }
    return 1;
}

typedef void *(__cdecl *world_fn)(float *out, const float *pos, const uint8_t *shape, float ang);
typedef char (__cdecl *boxc_fn)(const uint8_t *circle, const uint8_t *box);
static inline uint32_t fbits(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }
/* 0, or 2^-60 <= |v| < 2^60: sums and differences of such floats are 0 or normal, so the x87 original
 * (24-bit, wider exponent) and SSE round them alike */
static inline int zok(float v) { uint32_t e = (fbits(v) >> 23) & 0xff; return (e >= 127 - 60 && e < 127 + 60) || !(fbits(v) << 1); }
/* 0 or 2^-62 <= |v| < 2^62: its square is 0 or a normal float */
static inline int sqok(float v) { uint32_t e = (fbits(v) >> 23) & 0xff; return (e >= 127 - 62 && e < 127 + 62) || !(fbits(v) << 1); }

/* bfmeIntersects(g1 at p1 / a1, the sphere's one shape s2 at p2 / angle 0) as the original computes it:
 * per active shape of g1 in order, its world position by the original's own 0xad22f0 (fsin/fcos), the
 * two z-range tests, then circle-circle in SSE or box-circle by the original's 0xad4870. Without the
 * shape copies (two AsciiString copies under the string lock per pair) and the sphere's own rotation
 * (offset 0, angle 0: its world position is p2 + 0). 1 hit, 0 none, -1 a value outside the range where
 * SSE equals the x87 original: the caller runs the original */
static int isect_fast(const uint8_t *g1, const float *p1, float a1, const uint8_t *s2, const float *p2)
{
    const uint8_t *s = *(uint8_t *const *)(g1 + 0x2c), *e = *(uint8_t *const *)(g1 + 0x30);
    float maj2 = *(const float *)(s2 + 8), oz2 = *(const float *)(s2 + 0x18);
    if ((uint32_t)(e - s) % 0x24 || !zok(p2[0]) || !zok(p2[1]) || !zok(p2[2]) || !zok(maj2) || !zok(oz2)) return -1;
    float w2x = p2[0] + 0.0f, w2y = 0.0f + p2[1], w2z = p2[2] + oz2;
    float top2 = maj2 + oz2, lo2 = p2[2] - top2, hi2;        /* a type-0 shape: its bottom offset = its top */
    if (!zok(w2x) || !zok(w2y) || !zok(w2z) || !zok(top2) || !zok(lo2)) return -1;
    hi2 = w2z + top2;
    for (; s < e; s += 0x24) {
        if (!s[0x20]) continue;
        int32_t t = *(const int32_t *)s;
        float w1[3];
        ((world_fn)(uintptr_t)va_world)(w1, p1, s, a1);
        float zext = t == 0 ? *(const float *)(s + 8) : t == 1 || t == 2 ? *(const float *)(s + 4) : 0.0f;
        float oz1 = *(const float *)(s + 0x18);
        if (!zok(zext) || !zok(oz1) || !zok(w1[0]) || !zok(w1[1]) || !zok(w1[2])) return -1;
        float top1 = zext + oz1;
        if (!zok(top1)) return -1;
        if (lo2 > w1[2] + top1) continue;                    /* the original's fcompp: skip if greater */
        if (gp_ag_sens != 4 && w1[2] > hi2) continue;
        if (t < 0 || t > 2) continue;
        if (t <= 1) {
            float maj1 = *(const float *)(s + 8);
            if (!zok(maj1)) return -1;
            float dx = w2x - w1[0], dy = w2y - w1[1], R = maj1 + maj2;
            if (!sqok(dx) || !sqok(dy) || !sqok(R)) return -1;
            if (!(dx * dx + dy * dy > R * R)) return 1;      /* within, or unordered: a hit */
        } else {
            uint8_t circle[0x34], box[0x34];
            memset(circle, 0, sizeof circle); memset(box, 0, sizeof box);
            memcpy(circle + 8, &maj2, 4); memcpy(circle + 0x24, &w2x, 4); memcpy(circle + 0x28, &w2y, 4);
            memcpy(box + 8, s + 8, 8); memcpy(box + 0x24, w1, 8); memcpy(box + 0x30, &a1, 4);
            if (((boxc_fn)(uintptr_t)va_boxc)(circle, box)) return 1;
        }
    }
    return 0;
}

float __cdecl gp_ag_t4(const float *q, void *it_, float r2)
{
    iface *it = it_;
    uint8_t *g = (uint8_t *)(uintptr_t)AG_STATIC;
    uint16_t cw; uint32_t mx;
    __asm__ volatile("fnstcw %0\n\tstmxcsr %1" : "=m"(cw), "=m"(mx));
    gp_ag_stats[0]++;
    if (!(*(volatile uint8_t *)(uintptr_t)AG_GUARD & 1) || (cw & 0xf3f) != 0x3f || (mx & 0xffc0) != 0x1f80) {
        gp_ag_stats[3]++;
        return gp_ag_orig(q, it_, r2);
    }
    uint32_t b = *(uint32_t *)(g + 0x2c), e = *(uint32_t *)(g + 0x30);
    int32_t n = shape_count(b, e);
    float rad = 0;
    if (n) {                                    /* fsqrt in this x87 mode: the same r2 bits give the same root */
        uint32_t rb; memcpy(&rb, &r2, 4);
        if (!sq_ok_ || rb != sq_r2 || cw != sq_cw) { sq_rad = x87_sqrt(r2); sq_r2 = rb; sq_cw = cw; sq_ok_ = 1; }
        rad = sq_rad;
        *(float *)(uintptr_t)(b + 8) = rad;
    }
    uint32_t len = 0x5c + (n > 0 && n <= SNAP_SHAPES ? (uint32_t)n * 0x24 : 0);
    int same = snap_ok && cw == snap_cw && len == snap_len && n >= 0 && n <= SNAP_SHAPES && !memcmp(snap, g, 0x5c)
               && (n == 0 || !memcmp(snap + 0x5c, (void *)(uintptr_t)b, (uint32_t)n * 0x24));
    if (gp_ag_sens == 2 && snap_ok) same = 1;
    if (!same) {
        gp_ag_stats[2]++;
        ((calc_fn)(uintptr_t)calc_va)(g);
        snap_ok = n >= 0 && n <= SNAP_SHAPES;
        if (snap_ok) {
            memcpy(snap, g, 0x5c);
            if (n) memcpy(snap + 0x5c, (void *)(uintptr_t)b, (uint32_t)n * 0x24);
            snap_len = len; snap_cw = cw;
        }
    }
    void *geom = ((getp_fn)it->vt[0])(it);
    float ang = ((getf_fn)it->vt[2])(it);
    const float *pos = ((getp_fn)it->vt[1])(it);
    if (n == 1 && apart(q, pos, ang, geom, rad, (const uint8_t *)(uintptr_t)b)) {
        gp_ag_stats[1]++;
        return *(volatile float *)(uintptr_t)AG_FAR;
    }
    if (n == 1) {
        const uint8_t *sp = (const uint8_t *)(uintptr_t)b;
        if (*(const int32_t *)sp == 0 && sp[0x20] && !fbits(*(const float *)(sp + 0x10)) && !fbits(*(const float *)(sp + 0x14))) {
            int h = isect_fast(geom, pos, ang, sp, q);
            if (h >= 0) {
                gp_ag_stats[4]++;
                return h ? *(volatile float *)(uintptr_t)AG_ZERO : *(volatile float *)(uintptr_t)AG_FAR;
            }
        }
    }
    char hit = ((isect_fn)(uintptr_t)isect_va)(geom, pos, ang, g, q, 0);
    return hit ? *(volatile float *)(uintptr_t)AG_ZERO : *(volatile float *)(uintptr_t)AG_FAR;
}

void gp_ag_exit_log(void)
{
    if (on) gp_log("exit: aigeom %ld type-4 distances, %ld answered apart without the intersection test, %ld tested "
                   "inline, %ld sphere bound recalculations, %ld by the original", gp_ag_stats[0], gp_ag_stats[1],
                   gp_ag_stats[4], gp_ag_stats[2], gp_ag_stats[3]);
}

int gp_patch_aigeom(void)
{
    static const uint8_t head[] = {0x64, 0xa1, 0x00, 0x00, 0x00, 0x00};   /* mov eax, fs:[0] */
    static const uint8_t far_[] = {0xff, 0xff, 0x7f, 0x7f}, zero[4] = {0};
    gp_site s[13];
    gp_site_hash(&s[0], 0xa3c7d0, 0xfd, GP_FNV_A3C7D0);
    gp_site_hash(&s[1], 0xad2ce0, 0x335, GP_FNV_AD2CE0);
    gp_site_hash(&s[2], 0xad2860, 0x12d, GP_FNV_AD2860);
    gp_site_hash(&s[3], 0xad2700, 0x65, GP_FNV_AD2700);
    gp_site_hash(&s[4], 0xad2770, 0xe4, GP_FNV_AD2770);
    gp_site_hash(&s[5], 0xad2040, 0x27c, GP_FNV_AD2040);
    gp_site_hash(&s[6], 0xad22f0, 0x84, GP_FNV_AD22F0);
    gp_site_hash(&s[7], 0xad4870, 0x7f, GP_FNV_AD4870);
    gp_site_hash(&s[8], 0xad48f0, 0x3d, GP_FNV_AD48F0);
    gp_site_hash(&s[9], 0xad45a0, 0xbb, GP_FNV_AD45A0);
    gp_site_init(&s[10], AG_FAR, far_, 4); s[10].wlen = 0;
    gp_site_init(&s[11], AG_ZERO, zero, 4); s[11].wlen = 0;
    gp_site_init(&s[12], 0xa3c7d0, head, sizeof head);
    gp_rel32(&s[12], 0, 0xe9, (void *)gp_ag_t4);
    s[12].repl[5] = 0x90;
    gp_ag_cont = 0xa3c7d6 + gp_va_offset;
    calc_va = 0xad2860 + gp_va_offset; isect_va = 0xad2ce0 + gp_va_offset;
    va_world = 0xad22f0 + gp_va_offset; va_boxc = 0xad4870 + gp_va_offset;
    snap_ok = 0;
    if (!gp_apply("aigeom", s, 13)) return 0;
    on = 1;
    return 1;
}
