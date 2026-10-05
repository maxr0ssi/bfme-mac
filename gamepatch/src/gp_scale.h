/* Patches for the logic systems that grow with the unit count (docs/PERFORMANCE.md §18): the shroud
 * span updaters (p_shroud.c, switch shroudspan) and the partition-manager range scan (p_scan.c/.S,
 * switch scantree). Both give the original's results bit for bit; tests t_shroud and t_scan. */
#ifndef GP_SCALE_H
#define GP_SCALE_H
#include "gp.h"

/* FNV-1a 64 of the original functions (checked before anything is written) */
#define GP_FNV_B4FC80  0x5840418a31541debull   /* shroud span: reveal count +1 per player bit, 0x9f bytes */
#define GP_FNV_B4FD20  0xadbeb0655dcd861bull   /* shroud span: reveal count -1, 0x9f bytes */
#define GP_FNV_B4FDC0  0xf7e70ffdb3a62448ull   /* shroud span: saturating add to a counter layer, 0x75 bytes */
#define GP_FNV_B4E460  0x122e5552245ff5beull   /* the span's element range in a row, 0x87 bytes */
#define GP_FNV_B52E10  0xe4c61e77325df03eull   /* one cell +1 and its status change, 0xa5 bytes */
#define GP_FNV_B52EC0  0x272bf79de0df4b74ull   /* one cell -1 and its status change, 0x95 bytes */
#define GP_FNV_B52BF0  0xa6cc1dbc0e12c874ull   /* one cell's layer add, 0x37 bytes */

int  gp_patch_shroudspan(void);
void gp_shroud_exit_log(void);
uint32_t __attribute__((thiscall)) gp_shr_inc(void *visitor, int x0, int x1, int y);
uint32_t __attribute__((thiscall)) gp_shr_dec(void *visitor, int x0, int x1, int y);
uint32_t __attribute__((thiscall)) gp_shr_add(void *visitor, int x0, int x1, int y);
extern uint32_t gp_shr_slow_inc, gp_shr_slow_dec, gp_shr_true_pred;   /* original VAs (+ offset) */
/* [0] spans, [1] cell updates (cells x player bits), [2] status changes (the original's code) */
extern volatile LONG gp_shr_stats[3];
extern DWORD gp_scale_period_ms;

/* scantree: the quadtree walk of PartitionManager's range query (0xa3a860, called from 0xa3c659) */
#define GP_FNV_A3A860  0xb3a103a50c8471f9ull   /* the walk, 0x29d bytes (left in place: region queries) */
#define GP_FNV_A3C4E0  0x58ed378e107e52b2ull   /* iterateObjectsInRange, 0x20d bytes (its call at 0xa3c659) */
#define GP_FNV_A3A3A0  0x23f42c7fbbb7846eull   /* result append, 0x67 bytes */
#define GP_FNV_A39450  0x2b33a7e2098eeeb1ull   /* filter chain allow, 0x31 bytes */
#define GP_FNV_A3A7A8  0x4740fed2064e99a0ull   /* centre 2D distance after its first 8 bytes (distcalc writes 6) */
#define GP_FNV_A3AE58  0xee8b229e037841faull   /* bounding circle 2D after its first 8 bytes (distcalc writes 7) */
int  gp_patch_scantree(void);
void gp_scan_exit_log(void);
/* [0] walks, [1] nodes, [2] candidates, [3] inline distances, [4] distances through the table */
extern volatile LONG gp_scan_stats[5];

#endif
