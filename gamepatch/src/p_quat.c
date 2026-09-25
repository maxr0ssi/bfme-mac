/* quatmat: SSE version of 0xb26100, the quaternion to rotation matrix conversion used by the
 * animation code (0.7-0.9 % of the main thread in big battles). Original, x87 at 24-bit precision,
 * q = (x, y, z, w), writing the 3x3 part of a row-major 3x4 matrix (translation left alone):
 *   m00 = 1 - 2(yy+zz)   m01 = 2(xy-wz)   m02 = 2(wy+xz)
 *   m10 = 2(wz+xy)       m11 = 1 - 2(xx+zz) m12 = 2(zy-wx)
 *   m20 = 2(xz-wy)       m21 = 2(wx+zy)   m22 = 1 - 2(xx+yy)
 * (each 2(a) is a + a; the 1 is the double constant 1.0 at 0xbd2c98). The same operations in
 * SSE single give the same floats unless one overflows or underflows, which the entry
 * (p_quat.S) detects from the MXCSR flags and then runs the original; NaN inputs also go to the
 * original (NaN payloads propagate differently). Test: t_quat.c. */
#include "gp.h"

volatile LONG gp_quat2mat_fallbacks;

__attribute__((force_align_arg_pointer))
int WINAPI gp_quat2mat_c(float *m, const float *q)
{
    const uint8_t *mb = (const uint8_t *)m, *qb = (const uint8_t *)q;
    if (mb < qb + 16 && qb < mb + 44) return 2;          /* overlapping: let the original do it */
    /* a NaN input raises no SSE flag, and with two NaN operands x87 and SSE pick different ones */
    for (int i = 0; i < 4; i++) if ((((const uint32_t *)q)[i] & 0x7fffffffu) > 0x7f800000u) return 2;
    float x = q[0], y = q[1], z = q[2], w = q[3], s;
    float r[9];
    s = y * y + z * z; r[0] = 1.0f - (s + s);
    s = x * y - w * z; r[1] = s + s;
    s = w * y + x * z; r[2] = s + s;
    s = w * z + x * y; r[3] = s + s;
    s = x * x + z * z; r[4] = 1.0f - (s + s);
    s = z * y - w * x; r[5] = s + s;
    s = x * z - w * y; r[6] = s + s;
    s = w * x + z * y; r[7] = s + s;
    s = x * x + y * y; r[8] = 1.0f - (s + s);
    m[0] = r[0]; m[1] = r[1]; m[2] = r[2];
    m[4] = r[3]; m[5] = r[4]; m[6] = r[5];
    m[8] = r[6]; m[9] = r[7]; m[10] = r[8];
    return 0;
}

int gp_patch_quatmat(void)
{
    static const uint8_t head[] = {0x8b,0x44,0x24,0x04, 0xd9,0x40,0x08};   /* mov eax,[esp+4]; fld [eax+8] */
    gp_site s[2];
    gp_site_hash(&s[0], 0xb26100, 0xcd, GP_FNV_B26100);
    gp_site_init(&s[1], 0xb26100, head, sizeof head);
    gp_rel32(&s[1], 0, 0xe9, (void *)gp_quat2mat);
    s[1].repl[5] = 0x90; s[1].repl[6] = 0x90;
    return gp_apply("quatmat", s, 2);
}
