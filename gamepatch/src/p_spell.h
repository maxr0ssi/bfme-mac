/* spell patches (docs/PERFORMANCE.md §24): declarations for main.c and the tests */
#ifndef P_SPELL_H
#define P_SPELL_H
#include <windows.h>
#include <stdint.h>
int  gp_patch_firecircle(void);          /* p_spellfire.c */
void gp_fc_exit_log(void);
void gp_fc_cell(void);
void gp_fc_rowcall(void);
extern volatile LONG gp_fc_stats[3];     /* rows skipped, cells skipped, rows called */
#endif
