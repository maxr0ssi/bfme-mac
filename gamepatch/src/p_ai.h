/* Exact speed-ups of the per-object logic that the 8-player logicstats rank highest (docs/PERFORMANCE.md
 * §30): the range scans' geometry-intersection distance (aigeom, p_aigeom.c: DamageNugget radius hits,
 * FireWeaponUpdate's fortress spikes), the partition manager's closest-object search (aiclosest,
 * p_aiclose.c: AnimalAIUpdate's flee and wander scans, EmotionTracker, the AI's closest-target asks).
 * Both give the original's results bit for bit; tests t_aigeom and t_aiclose. */
#ifndef P_AI_H
#define P_AI_H
#include <windows.h>
#include <stdint.h>

/* aigeom: distance type 4 of the range query (0xa3c7d0, the table 0xdbdaf8[4]) */
int  gp_patch_aigeom(void);
void gp_ag_exit_log(void);
float __cdecl gp_ag_t4(const float *q, void *iface, float r2);  /* replaces 0xa3c7d0 */
/* [0] calls, [1] answered "apart" without the intersection test, [2] bounding recalculations of the
 * query sphere, [3] run by the original (its static not yet built, or another FPU mode), [4] the
 * intersection test answered inline */
extern volatile LONG gp_ag_stats[5];
extern uint32_t gp_ag_sens;   /* tests only: 1 = shape offsets forgotten, 2 = the sphere's bounds never
                                 recalculated, 3 = the exact reach with no rounding margin, 4 = the inline
                                 test without its second z-range test */

/* aiclosest: PartitionManager getClosestObject (0xa3bdb0) */
int  gp_patch_aiclosest(void);
void gp_ac_exit_log(void);
/* [0] searches, [1] heap pops, [2] candidates, [3] 2D distances inline, [4] through the table,
 * [5] run by the original (another FPU mode) */
extern volatile LONG gp_ac_stats[6];
extern uint32_t gp_ac_sens;   /* tests only: 1 = equal distances keep the first object found */

/* aiprof: diagnostic, call-site timers inside AnimalAIUpdate, AIUpdateInterface::update, FireWeaponUpdate
 * and the AI state updates (p_aiprof.c / .S) */
int  gp_patch_aiprof(void);
void gp_ap_exit_log(void);
extern void (*const gp_ap_stub[21])(void);   /* site stubs; 20 is a test-only cdecl one with 3 arguments */
void gp_ap_state(void);                      /* replaces mov ebx, ecx; call [eax+0x18] at 0x8db70b */
extern uint32_t gp_ap_target[21];
extern volatile uint64_t gp_ap_ticks[21];
extern volatile LONG gp_ap_calls[21];

#endif
