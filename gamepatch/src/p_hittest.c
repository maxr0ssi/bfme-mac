/* hittest: SSE version of the APT (Flash UI) button hit test, called for every button shape every
 * frame by the mouse-over code at 0xb0e620 (only caller, 0xb0e8b5).
 *
 * Original 0xb0dfe0(shape, m, ix, iy), x87: for each triangle (int16 index triples at shape+0x20,
 * count at +0x14, float2 vertices at +0x1c) transform its three vertices by the 2x3 matrix m
 *   X = (m2*vy + m0*vx) + m4,  Y = (vx*m1 + vy*m3) + m5   (rounded to float)
 * and call the crossing-number test 0xb0deb0 with the point (float)ix, (float)iy; return 1 at the
 * first triangle that contains it. 0xb0deb0 toggles on each edge (a,b) with
 *   (Ya <= fy < Yb or Yb <= fy < Ya) and fx < ((Xb-Xa)*(fy-Ya))/(Yb-Ya) + Xa
 * (edges (p0,p2), (p1,p0), (p2,p1) in that operand order).
 *
 * Here: the same operations in the same order in SSE single precision. In the game's x87 mode
 * (24-bit, nearest) every operation rounds to the same value as SSE unless a result overflows or
 * is an inexact denormal, and comparisons are exact; the asm entry (p_hittest.S) runs the
 * original function whenever this code raised invalid, divide-by-zero, overflow or underflow.
 * Two early rejects, both exact:
 *   - per triangle, the X coordinates are only computed when some edge straddles fy (the
 *     original's own condition; without a straddling edge the triangle test returns 0);
 *   - per shape, a bounding box of the referenced vertices in shape space, mapped through m in
 *     double precision and widened by 2^-12 of the magnitudes involved (the x87 computation's
 *     rounding error is below 2^-19 of them): if fy is outside its Y range, or fx right of its X
 *     range, no edge can straddle / no crossing lies right of the point, so the result is 0.
 * gamepatch/tests/t_hittest.c compares this against the original bytes on synthetic shapes. */
#include "gp.h"

volatile LONG gp_hittest_stats[4];

static inline int straddles(float ya, float yb, float fy)
{
    return (ya <= fy && fy < yb) || (yb <= fy && fy < ya);
}

static inline int finite_bits(float f)
{
    union { float f; uint32_t u; } c = { f };
    return (c.u & 0x7f800000u) != 0x7f800000u;
}

static inline double dmin(double a, double b) { return a < b ? a : b; }
static inline double dmax(double a, double b) { return a > b ? a : b; }
static inline double dabs(double a) { return a < 0 ? -a : a; }

/* 1 when the point cannot be inside any triangle; 0 = don't know */
static int bbox_reject(const int16_t *idx, const float *v, int count, const float *m, float fx, float fy)
{
    float minx = 0, maxx = 0, miny = 0, maxy = 0;
    for (int t = 0; t < count; t++) {
        for (int k = 0; k < 3; k++) {
            const float *p = v + 2 * idx[3 * t + k];
            float x = p[0], y = p[1];
            if (!finite_bits(x) || !finite_bits(y)) return 0;
            if (t == 0 && k == 0) { minx = maxx = x; miny = maxy = y; continue; }
            if (x < minx) minx = x;
            if (x > maxx) maxx = x;
            if (y < miny) miny = y;
            if (y > maxy) maxy = y;
        }
    }
    for (int i = 0; i < 6; i++) if (!finite_bits(m[i])) return 0;
    double m0 = m[0], m1 = m[1], m2 = m[2], m3 = m[3], m4 = m[4], m5 = m[5];
    double ax = dmax(dabs(minx), dabs(maxx)), ay = dmax(dabs(miny), dabs(maxy));
    double Mx = dabs(m4) + dabs(m0) * ax + dabs(m2) * ay;
    double My = dabs(m5) + dabs(m1) * ax + dabs(m3) * ay;
    if (!(Mx < 0x1p60) || !(My < 0x1p60)) return 0;
    double xhi = m4 + dmax(m0 * minx, m0 * maxx) + dmax(m2 * miny, m2 * maxy);
    double ylo = m5 + dmin(m1 * minx, m1 * maxx) + dmin(m3 * miny, m3 * maxy);
    double yhi = m5 + dmax(m1 * minx, m1 * maxx) + dmax(m3 * miny, m3 * maxy);
    double dx = Mx * 0x1p-12 + 1e-30, dy = My * 0x1p-12 + 1e-30;
    return (double)fy < ylo - dy || (double)fy > yhi + dy || (double)fx > xhi + dx;
}

__attribute__((force_align_arg_pointer))
int WINAPI gp_hittest_c(const uint8_t *shape, const float *m, int ix, int iy)
{
    int count = *(const int *)(shape + 0x14);
    const float *v = *(const float *const *)(shape + 0x1c);
    const int16_t *idx = *(const int16_t *const *)(shape + 0x20);
    float fx = (float)ix, fy = (float)iy;
    InterlockedIncrement(&gp_hittest_stats[0]);
    if (count <= 0) return 0;
    if (bbox_reject(idx, v, count, m, fx, fy)) { InterlockedIncrement(&gp_hittest_stats[1]); return 0; }
    InterlockedIncrement(&gp_hittest_stats[2]);
    const float m0 = m[0], m1 = m[1], m2 = m[2], m3 = m[3], m4 = m[4], m5 = m[5];
    for (int t = 0; t < count; t++, idx += 3) {
        const float *a = v + 2 * idx[0], *b = v + 2 * idx[1], *c = v + 2 * idx[2];
        float y0 = (a[0] * m1 + a[1] * m3) + m5;
        float y1 = (b[1] * m3 + b[0] * m1) + m5;
        float y2 = (c[1] * m3 + m1 * c[0]) + m5;
        int e02 = straddles(y0, y2, fy), e10 = straddles(y1, y0, fy), e21 = straddles(y2, y1, fy);
        if (!(e02 | e10 | e21)) continue;
        float x0 = (m2 * a[1] + m0 * a[0]) + m4;
        float x1 = (b[0] * m0 + b[1] * m2) + m4;
        float x2 = (m0 * c[0] + m2 * c[1]) + m4;
        int in = 0;
        if (e02 && ((x2 - x0) * (fy - y0)) / (y2 - y0) + x0 > fx) in = 1;
        if (e10 && ((x0 - x1) * (fy - y1)) / (y0 - y1) + x1 > fx) in = !in;
        if (e21 && ((x1 - x2) * (fy - y2)) / (y1 - y2) + x2 > fx) in = !in;
        if (in) return 1;
    }
    return 0;
}

static const uint8_t head[] = {0x83,0xec,0x1c, 0xdb,0x44,0x24,0x28};

int gp_patch_hittest(void)
{
    /* this replaces both original functions, so both must be exactly the expected code */
    gp_site s[3];
    gp_site_hash(&s[0], 0xb0dfe0, 0x110, GP_FNV_B0DFE0);
    gp_site_hash(&s[1], 0xb0deb0, 0x130, GP_FNV_B0DEB0);
    gp_site_init(&s[2], 0xb0dfe0, head, sizeof head);
    gp_rel32(&s[2], 0, 0xe9, (void *)gp_hittest);
    s[2].repl[5] = 0x90; s[2].repl[6] = 0x90;
    return gp_apply("hittest", s, 3);
}
