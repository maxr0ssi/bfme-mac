/* Game-logic x87 replacements (third batch, p_logic.c/.S): exact SSE versions of small x87
 * functions that the logic and animation code calls per unit, per bone or per range-scan
 * candidate. Kept out of gp.h / gp_render.h so the patch sets can grow independently.
 *   mat2quat   0xb2bd10 Matrix3D -> quaternion (animation blending; x87 sqrt and divide)
 *   distcalc   0xa3a7a0 / 0xa3ae50 PartitionManager distance procs, 2D centre and bounding
 *              circle (called per candidate object of every range scan)
 *   bsphere    the x87 sqrt inside 0x59bc50 (a render object's bounding sphere from its box)
 *   worldcell  0x6e8ce6 world position -> pathfinder cell (two floor calls and fistp)
 *   ftol2      0xa3cfa4 the CRT's x87 _ftol2 (every float -> int cast) in integer arithmetic */
#ifndef GP_LOGIC_H
#define GP_LOGIC_H
#include "gp.h"

/* FNV-1a 64 of the original functions (checked before anything is written) */
#define GP_FNV_B2BD10  0x5946adfe116dbab6ull   /* matrix -> quaternion, 0x168 bytes */
#define GP_FNV_A3A7A0  0xd08cd54e35a49b18ull   /* distCalcProc centre 2D, 0x26 bytes */
#define GP_FNV_A3AE50  0x4438963b97ee0ca9ull   /* distCalcProc bounding circle 2D, 0x53 bytes */
#define GP_FNV_59BC50  0xe0a17517134f2f6dull   /* bounding sphere from box, 0x82 bytes */
#define GP_FNV_6E8CE6  0x834b436ff760e053ull   /* world -> pathfinder cell, 0xa2 bytes */
#define GP_FNV_A3CFA4  0x401dfa8ffc792418ull   /* _ftol2, 0x75 bytes */

int  gp_patch_mat2quat(void);
int  gp_patch_distcalc(void);
int  gp_patch_bsphere(void);
int  gp_patch_worldcell(void);
int  gp_patch_ftol2(void);
void gp_logic_exit_log(void);            /* DLL_PROCESS_DETACH totals */

/* asm entries (p_logic.S) and where their x87 fallbacks continue (set by the installers to the
 * original + n, i.e. relocated by gp_va_offset in the tests) */
void gp_m2q(void);                       /* cdecl (Quaternion *ret, const Matrix3D *m) -> eax = ret */
void gp_dc_center2d(void);               /* cdecl (const Coord3D *p, const Object *o, int) -> st0 */
void gp_dc_bound2d(void);
void gp_bsph(void);                      /* called from 0x59bcb9 instead of flds/fsqrt/fstps */
void gp_wcell(void);                     /* cdecl (int out[2], bool center, const Coord3D *p) */
void gp_ftol2(void);                     /* st0 -> edx:eax (p_ftol2.S) */
extern uint32_t gp_ftol2_cont;
extern volatile LONG gp_ftol2_calls[16][16];   /* per thread line: [0] calls, [1] x87 runs */
extern uint32_t gp_m2q_cont, gp_m2q_next, gp_dcc_cont, gp_dcb_cont, gp_wcell_cont;
extern uint32_t gp_dcc_x87, gp_dcb_tail;   /* x87 fallbacks after the getter calls */

/* counters per entry: calls, and calls that ran the original x87 code (other FPU mode, or an
 * input whose SSE result could differ: overflow, underflow, invalid, NaN) */
enum { LM_M2Q, LM_DCC, LM_DCB, LM_BSPH, LM_WCELL, LM_N };
LONG gp_lm_count(int x87, int k);         /* summed over the per-thread counter lines */
void gp_lm_periodic(void);               /* the 60 s log line; p_logic.S calls it every 64 k calls */
extern DWORD gp_lm_period_ms;            /* 60000 (tests shorten it) */

#endif
