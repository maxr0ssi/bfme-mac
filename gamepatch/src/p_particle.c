/* particlevtx: the colour pack of the particle / point-group vertex write loop without the two
 * x87 control-word switches per vertex (fldcw is expensive under Rosetta). The code
 * and the exactness argument are in p_particle.S; test: tests/t_particle.c (all 2^32 inputs). */
#include "gp.h"
#include "gp_render.h"

#define GP_FNV_579C1A 0xebb101bf48a4241bull  /* the loop head that sets [ebp-0x104], [ebp-0xf4] */

int gp_patch_particlevtx(void)
{
    static const uint8_t head[] = {0x83,0xec,0x14, 0x9b, 0x9b};   /* sub esp,0x14; fwait; (fstcw..) */
    gp_site s[3];
    gp_site_hash(&s[0], 0x579c1a, 0x186, GP_FNV_579C1A);
    gp_site_hash(&s[1], 0x579da0, 0x83, GP_FNV_579DA0);
    gp_site_init(&s[2], 0x579da0, head, sizeof head);
    gp_rel32(&s[2], 0, 0xe9, (void *)gp_ptclvtx);
    gp_ptclvtx_cont = 0x579e23 + gp_va_offset;
    gp_ptclvtx_x87 = 0x579da9 + gp_va_offset;
    return gp_apply("particlevtx", s, 3);
}
