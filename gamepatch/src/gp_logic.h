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

/* p_lmath2.c/.S: crtsqrt (msvcr71!sqrt import -> SSE with Wine's builtin sqrt's exact result) and
 * octile (0x7658c3 path segment cost in SSE) */
#define GP_FNV_7658C3  0xc94432aeca6288b1ull   /* path segment cost (octile), 0x82 bytes */
int  gp_patch_crtsqrt(void);
int  gp_patch_octile(void);
void gp_l2_exit_log(void);
void gp_octile(void);                    /* cdecl (const Coord2D *a, const Coord2D *b) -> st0 */
extern uint32_t gp_oct_cont;             /* the x87 fallback continues at 0x7658ca */
LONG gp_l2_count(int k);                 /* [0] sqrt calls, [1] sqrt fallbacks, [2] octile, [3] octile x87 */
void gp_sqrt(void);                      /* cdecl double -> st0, replaces the IAT entry 0xbd06a0 */
extern uint32_t gp_sqrt_orig;            /* Wine's sqrt: the fallback */
LONG gp_sqrt_count(int fallback);        /* calls, or calls that ran Wine's sqrt */
int  gp_sqrt_selftest(void *crt_sqrt);   /* the install-time check: 1 = agrees */
extern DWORD gp_sqrt_period_ms;

/* logicstats (p_lstats.c/.S): diagnostic timers of GameLogic::update per phase, its subsystems,
 * direct calls and update modules; no behaviour change, off by default */
int  gp_patch_logicstats(void);
void gp_lst_exit_log(void);
void gp_lst_logic_stub(void); void gp_lst_mod_stub(void);
void gp_lst_sub0(void); void gp_lst_sub1(void); void gp_lst_sub2(void); void gp_lst_sub3(void);
void gp_lst_sub4(void); void gp_lst_sub5(void); void gp_lst_sub6(void); void gp_lst_sub7(void);
void gp_lst_sub8(void); void gp_lst_sub9(void); void gp_lst_sub10(void); void gp_lst_sub11(void);
void gp_lst_sub12(void); void gp_lst_sub13(void); void gp_lst_sub14(void); void gp_lst_sub15(void);
void gp_lst_sub16(void); void gp_lst_sub17(void); void gp_lst_sub18(void);
void gp_lst_call0(void); void gp_lst_call1(void); void gp_lst_call2(void); void gp_lst_call3(void);
void gp_lst_call4(void); void gp_lst_call5(void);
extern uint32_t gp_lst_logic_cont, gp_lst_cont[32], gp_lst_sub_slot[19];
extern DWORD gp_lst_period_ms;
void gp_lst_force_report(void);
void gp_lst_get(int kind, int ph, LONG *calls, uint64_t *ticks);   /* kind -1 logic, -2 modules */
LONG gp_lst_mod_calls(uint32_t vt);
int  gp_lst_phase(void);               /* current phase 0-6, -1 when logicstats is off */

/* p_path.c: pathfind (the search step's movement check and crowd cost, memoised per search) */
#define GP_FNV_6F9850  0xf408f22b1d288853ull   /* search step (examineNeighboringCells), 0x721 bytes */
#define GP_FNV_6EBAA0  0xde9bcb01ce4eebc1ull   /* checkForMovement, 0x3e9 bytes */
#define GP_FNV_6ED21E  0x560290640b570b21ull   /* crowd cost, 0x24e bytes */
#define GP_FNV_6E8200  0x029abeac3dde33b0ull   /* cell passable for locomotor surfaces, 0xb3 bytes */
#define GP_FNV_5E2E9C  0xadf9a0eb609c09adull   /* getCell, 0x56 bytes */
#define GP_FNV_6ED049  0x7a31266a0fbd808bull   /* cell -> world position wrapper, 0x28 bytes */
#define GP_FNV_6E8E19  0xca2906a0a57c138aull   /* cell -> world position, 0xba bytes */
#define GP_FNV_6FB231  0x41d67463d71979efull /* getMoveAwayFromPath, 0x449 bytes */
int  gp_patch_pathfind(void);
int  gp_patch_moveawaycap(void);
extern uint32_t gp_pf_macap;             /* popped cells per move-away search */
extern volatile LONG gp_pf_ma[3];        /* move-away searches, stopped at the cap, cells popped */
uint8_t *__attribute__((thiscall)) gp_pf_ma_pop(uint8_t *pf);
void gp_pf_exit_log(void);
/* p_path2.c: moveawayqueue (at most gp_maq_limit move-away orders at once per path, the rest later) */
#define GP_FNV_6F53AF  0x750d0026c4e93376ull   /* moveAllies' cell callback, 0x16a bytes */
#define GP_FNV_66C66E  0x54957e62d64b7e83ull   /* aiMoveAwayFromUnit, first 0x40 bytes */
#define GP_FNV_449681  0x7a62c420e47a4379ull   /* findObjectByID, 0x25 bytes */
int  gp_patch_moveawayqueue(void);
void gp_maq_exit_log(void);
void gp_maq_run(void);                   /* the queue-run hook's C part (tests call it directly) */
void __attribute__((thiscall)) gp_maq_order(uint8_t *cmd, uint8_t *mover, const float *pos, int source);
extern uint32_t gp_maq_limit;
extern volatile LONG gp_maq_stats[4];    /* orders, waited, given later, dropped */
extern volatile LONG gp_pf_stats[6];
extern uint32_t gp_pf_gen;

/* p_path3.c: pathsplit (the queue's long searches parked and resumed over queue runs, on a fiber) */
#define GP_FNV_6F236A  0x1f38a7f5d7d94828ull   /* the pathfind queue after its first 6 bytes, 0x294 bytes */
#define GP_FNV_6FD06F  0x134970761cde75a6ull   /* findPath's cell search, 0xd76 bytes */
#define GP_FNV_6FB869  0x1f0065078419a3c9ull   /* findClosestPath, 0x925 bytes */
#define GP_FNV_6F4AF2  0x27ba74db3b819cd8ull   /* open heap pop (+ clean open), 0x28 bytes */
#define GP_FNV_6F5A5E  0xe98889830bada086ull   /* Pathfinder::reset, 0x152 bytes */
#define GP_FNV_668E94  0x52c57a92be8be09full   /* AIUpdateInterface::doPathfind, 0x75b bytes */
#define GP_FNV_6EA019  0x9072b1fa2e7741c9ull   /* allocate a cell's info, 0x34 bytes */
#define GP_FNV_934594  0x0a944ab3fe409106ull   /* put on the closed list, 0x16 bytes */
#define GP_FNV_6E8074  0x92012db44667af58ull   /* unlink an info, 0x41 bytes */
#define GP_FNV_9347C6  0x2d86800885cc89e2ull   /* release a cell's info, 0x40 bytes */
#define GP_FNV_90BE00  0x036de4a89a083a29ull   /* vector<cell *>::push_back, 0x31 bytes */
#define GP_FNV_6EC096  0x611af9f649ad8f30ull   /* the queue holds an ID, 0x3b bytes */
#define GP_FNV_6EC1B7  0xffca189e1adf7a7eull   /* owner pointer delete, 0x4d bytes */
#define GP_FNV_93450F  0x377648e1d6b69ccdull   /* link an info at a list head, 0x29 bytes */
int  gp_patch_pathsplit(void);
void gp_ps_exit_log(void);
extern uint32_t gp_ps_budget;            /* popped cells per queue run */
extern volatile uint32_t gp_ps_stack_top;   /* pathsplit's fiber stack base, 0: none (p_stall.c) */
extern volatile LONG gp_ps_pops, gp_ps_stats[14], gp_ps_unsafe;   /* unsafe > 0: inside the approach branch */
/* the C parts of the hooks, for the tests: a queue run starts; a request (run(ctx) for the unit obj
 * with AI ai) is served on the fiber, 1 = the run must end; the parked request is resumed; a pop of a
 * splittable search; the pathfinder is reset */
void gp_ps_runstart(uint8_t *pf, uint32_t ret);   /* ret: the queue's caller (0 in the tests) */
int  gp_ps_serve_fn(uint8_t *pf, uint8_t *obj, uint8_t *ai, void (*run)(void *), void *ctx);
void gp_ps_resume(uint8_t *pf);
uint8_t *gp_ps_pop_ctx(uint8_t *pf, uint8_t *obj, uint8_t *goal, uint8_t *hp);
void gp_ps_drop(void);
int  gp_ps_parked(void);

#endif
