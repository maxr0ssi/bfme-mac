/* spell patches, second round (docs/PERFORMANCE.md §25): declarations for main.c and the tests */
#ifndef P_SPELL2_H
#define P_SPELL2_H
#include <windows.h>
#include <stdint.h>
int  gp_patch_fxparamused(void);          /* p_spell2fx.c */
void gp_fxu_exit_log(void);
BOOL __attribute__((stdcall)) gp_fxu_isused(void *fx, void *param, void *tech);
void gp_fxu_create_mem(void);             /* IAT wrappers: clear the cache, then the real import */
void gp_fxu_create_file(void);
extern volatile LONG gp_fxu_gen;          /* cache generation: +1 per effect creation */
extern volatile LONG gp_fxu_stats[4];     /* calls, answered from the cache, not cached (full), creations */
extern uint32_t gp_fxu_create[2];         /* the IAT's D3DXCreateEffect, D3DXCreateEffectFromFileA */
#define GP_FXU_IAT 0xbd09f4u              /* those two IAT slots (not relocated in the tests) */
#endif
