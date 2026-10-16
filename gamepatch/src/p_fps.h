/* The FPS roadmap's first two steps (docs/FPS-ROADMAP.md §4):
 *   framesplit  (p_framesplit.c/.S) diagnostic: per drawn frame, the time of the client pass, the
 *               draw, Present, the logic phase and the frame limiter's wait, into the monitor's
 *               frame records (p_monitor.c); on with the monitor
 *   phasebalance (p_phasebal.c/.S) GameLogic::update's list work spread evenly over phases 2-6:
 *               the same work in the same order, only the phase boundaries move (changes when
 *               work happens relative to the drawn frames: every LAN player needs the same switch)
 * Kept out of gp.h / gp_logic.h so these files stay independent of the other patch sets. */
#ifndef P_FPS_H
#define P_FPS_H
#include "gp.h"

/* ---- phasebalance ------------------------------------------------------------------------- */
#define GP_FNV_62E4E8  0x0a78f009bb0ad7e5ull   /* GameLogic::update, 0x985 bytes (as logicstats) */
int  gp_patch_phasebalance(void);
void gp_pb_exit_log(void);
/* the work items of one logic step after phase 2's own work, in the game's order */
enum { GP_PB_L0, GP_PB_L1, GP_PB_L2, GP_PB_AI, GP_PB_SUB, GP_PB_L3, GP_PB_DONE };
typedef struct { uint8_t item; uint16_t frac; } gp_pb_target;  /* frac: of a list, in 1/1024 */
/* mode: 1 = the balanced plan (gp_pb_plan), 2 = EA's own split re-expressed by the hooks (tests:
 * must give exactly the original's results) */
extern int gp_pb_mode;
extern gp_pb_target gp_pb_plan[7];       /* where each phase 1-6 ends; [0] unused */
extern uint32_t gp_pb_cont[12];          /* continuations (relocated by gp_va_offset) */
extern volatile LONG gp_pb_stats[6];     /* steps, rounds, re-entries, cuts, pending truncations, resets */
/* the asm stubs (p_phasebal.S) */
void gp_pb_s_lists(void); void gp_pb_s_start(void); void gp_pb_s_stop(void); void gp_pb_s_end(void);
void gp_pb_s_ai(void); void gp_pb_s_sub(void); void gp_pb_s_reenter(void);

/* ---- framesplit --------------------------------------------------------------------------- */
int  gp_patch_framesplit(void);
void gp_fs_exit_log(void);
enum { FS_CLIENT, FS_DRAW, FS_PRESENT, FS_LOGIC, FS_PHASES, FS_WAIT, FS_ITER, FS_ITERS, FS_N };
/* p_monitor.c: attach a frame split to the frame record of this engine iteration (stored by the
 * render-helper hook, not yet published) and publish it; 0 when no frame was drawn since the last
 * call (the split then carries over to the next drawn frame) */
int  gp_mon_split(const uint32_t v[FS_N]);
extern int gp_mon_split_on;               /* set by framesplit: frame records wait for their split */
extern uint32_t gp_fs_cont[8];            /* originals / continuations (relocated) */
void gp_fs_s_client(void); void gp_fs_s_step(void); void gp_fs_s_draw(void); void gp_fs_s_present(void);
void gp_fs_s_wait(void); void gp_fs_s_iter(void);

#endif
