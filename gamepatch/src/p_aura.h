/* aura3d (p_aura.c): the partition manager's two 3D distance functions in SSE, exact in the game's
 * FPU mode. Declarations for main.c and the test t_aura. docs/PERFORMANCE.md §27. */
#ifndef P_AURA_H
#define P_AURA_H
#include <windows.h>
#include <stdint.h>
int  gp_patch_aura3d(void);
void gp_au_exit_log(void);
void gp_au_c3(void);                     /* replaces 0xa3a7d0 (centre 3D), cdecl (pos, iface, r2) -> st0 */
void gp_au_b3(void);                     /* replaces 0xa3aeb0 (bounding sphere 3D), same signature */
/* [0] centre 3D calls, [1] bounding 3D calls, [2] / [3] of these, run by the x87 original */
extern volatile LONG gp_au_stats[4];
extern uint32_t gp_au_sens;              /* tests only: 1 = a deliberately reassociated sum (t_aura [4]) */
#endif
