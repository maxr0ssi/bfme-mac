/* Render-side patches (second batch): perfmarker, passtimers (p_perf.c/.S), particlevtx
 * (p_particle.c/.S), animdedup and animdecode (p_anim.c/.S). Kept out of gp.h so that other patch
 * sets can grow independently; main.c and the tests include both. */
#ifndef GP_RENDER_H
#define GP_RENDER_H
#include "gp.h"

/* FNV-1a 64 of original code these patches check (or call into) as a whole */
#define GP_FNV_517690  0xf74ba83fb9b86feaull   /* PerfTimer begin, 0xa7 bytes */
#define GP_FNV_51ECE0  0x39e29ee75613192bull   /* D3DPERF_BeginEvent wrapper, 0x80 bytes */
#define GP_FNV_51ED60  0x08cf7bb4e8fb073eull   /* D3DPERF_EndEvent wrapper, 0x0c bytes */
#define GP_FNV_579DA0  0x293276f3775cef0dull   /* particle vertex colour pack, 0x83 bytes */
#define GP_FNV_5A4DD0  0x5824da38d0711210ull   /* Animatable3DObjClass::Render, 0x53 bytes */
#define GP_FNV_5A4A70  0x50b36ba7d247d09bull   /* Single_Anim_Progress, 0x33 bytes */
#define GP_FNV_5A4770  0x03cf9ff1ff1cd9dbull   /* Compute_Current_Frame, 0x2e2 bytes */
#define GP_FNV_5A5050  0xfc746e5c8d24091bull   /* Animatable3DObjClass::USOT, 0x145 bytes */
#define GP_FNV_59CD70  0x9242d6d1c009ad87ull   /* HLodClass::USOT head, 0x10 bytes */
#define GP_FNV_5A3F70  0x02814e735f72f2c2ull   /* single-animation update, 0x6e bytes */
#define GP_FNV_5B18FE  0x75c8662ae4cddb30ull   /* motion channel base destructor, 0x1a bytes */

/* shared */
extern DWORD gp_render_tid;              /* the game's main thread (the one that ran DllMain) */
void gp_render_exit_log(void);           /* DLL_PROCESS_DETACH summary */
void gp_shadow_periodic(void);           /* p_shstats.c: the 60 s shadow lines (main thread) */

/* perfmarker / passtimers (p_perf.c, p_perf.S) */
int  gp_patch_perfmarker(void);
int  gp_patch_passtimers(void);
void gp_perfmark(void);                  /* asm, replaces the head of 0x517690 */
extern uint32_t gp_perfmark_cont;        /* 0x517696 (+ test offset) */
int  WINAPI gp_pt_begin(DWORD color, const WCHAR *name);   /* D3DPERF_BeginEvent-compatible */
int  WINAPI gp_pt_end(void);                                /* D3DPERF_EndEvent-compatible */
void gp_pt_report(void);                 /* write the summary now (tests) */
extern uint32_t gp_pt_ptr_va;            /* 0xdd361c: Begin pointer; End pointer follows */
extern DWORD gp_pt_period_ms;            /* summary period, 5000 */
typedef void (*gp_pt_sink_t)(const char *line);
extern gp_pt_sink_t gp_pt_sink;          /* where summary lines go (gp_log by default) */

/* particlevtx (p_particle.c, p_particle.S) */
int  gp_patch_particlevtx(void);
void gp_ptclvtx(void);                   /* asm, replaces 0x579da0..0x579e22 */
extern uint32_t gp_ptclvtx_cont;         /* 0x579e23 (+ test offset) */
extern uint32_t gp_ptclvtx_x87;          /* 0x579da9 (+ test offset): the original after the jmp */
extern volatile LONG gp_ptclvtx_fallbacks;

/* animdedup / animdecode (p_anim.c, p_anim.S) */
int  gp_patch_animdedup(void);
int  gp_patch_animdecode(void);
extern uint32_t gp_ad_vt_hlod;           /* HLodClass vtable 0xbec7f0 (tests: their own copy) */
extern uint32_t gp_ad_synctime_va;       /* WW3D::SyncTime 0xdd1e0c */
extern volatile LONG gp_ad_stats[4];     /* progress calls, skipped, snapshots taken, CCF moved */
extern volatile LONG gp_adq_stats[3];    /* decodes, continued from the cache, evictions */
extern volatile LONG gp_ad_pass[2][2];   /* [main, shadow-map pass]: HLod pose evaluations, Render skips */
void gp_ad_progress(void);               /* asm entries (thiscall) */
void gp_ad_usot_base(void);
void gp_ad_single(void);
void gp_adq_site0(void); void gp_adq_site1(void); void gp_adq_site2(void);
void gp_adq_site3(void); void gp_adq_site4(void); void gp_adq_site5(void);
void gp_adq_dtor(void);
void WINAPI gp_adq_evict(const void *chan);

/* renderstats (p_rstats.c, p_rstats.S): counters for the UltraHigh render model, switch/LOD log */
int  gp_patch_renderstats(void);
void gp_rst_exit_log(void);
void gp_rst_frame_stub(void); void gp_rst_vis_stub(void); void gp_rst_fxl_stub(void);
void gp_rst_fxs_stub(void); void gp_rst_dxs_stub(void); void gp_rst_sw_stub(void); void gp_rst_lod_stub(void);
void gp_rst_w3r_stub(void); void gp_rst_cr_stub(void); void gp_rst_obj_stub(void); void gp_rst_flush_stub(void);
void gp_rst_fx_stub(void);                     /* timed calls (the vis stub is timed too) */
extern uint32_t gp_rst_frame_cont, gp_rst_vis_cont, gp_rst_fxl_cont, gp_rst_fxs_cont, gp_rst_dxs_cont;
extern uint32_t gp_rst_w3r_cont, gp_rst_cr_cont, gp_rst_obj_cont, gp_rst_flush_cont, gp_rst_fx_cont;
void gp_rst_timer(unsigned kind, int pass, LONG *calls, uint64_t *ticks);  /* kind: p_rstats.S TIMED */
void gp_rst_force_report(void);                /* tests: log the 60 s lines now */
extern uint32_t gp_rst_sw_fn, gp_rst_lod_fn;   /* the originals the two logging stubs call */
void gp_rst_get(LONG *out, unsigned n);        /* the counters, in the order of p_rstats.c's rst_t */
extern LONG gp_rst_logged; extern uint32_t gp_rst_last_caller; extern int gp_rst_last_arg;

/* particlestats (p_pstats.c, p_pstats.S): timers/counters of the RenderParticles pass, per pass */
enum { PS_MGR, PS_ROBJ, PS_COLOR, PS_SORT, PS_PBUF, PS_N };   /* timed kinds */
#define PS_KINDS 9                                            /* draw module kinds of the system walk */
typedef struct {
    LONG calls[PS_N][2];                         /* [kind][0 main, 1 shadow-map pass] */
    LONG armed[2], robj_particles[2], sort_nodes[2];
    LONG live, walks, systems[PS_KINDS], particles[PS_KINDS], terrain, walk_cut;
} gp_pst_t;
extern gp_pst_t gp_pst;
int  gp_patch_particlestats(void);
void gp_pst_exit_log(void);
void gp_pst_force_report(void);                /* tests: log the 60 s lines now */
uint64_t gp_pst_ticks(unsigned kind, int pass);
void gp_pst_mgr_stub(void); void gp_pst_robj_stub(void); void gp_pst_c1_stub(void); void gp_pst_c2_stub(void);
void gp_pst_c3_stub(void); void gp_pst_sort_stub(void); void gp_pst_pbuf_stub(void);
extern uint32_t gp_pst_mgr_cont, gp_pst_robj_cont, gp_pst_c1_cont, gp_pst_c2_cont, gp_pst_c3_cont;
extern uint32_t gp_pst_sort_cont, gp_pst_pbuf_cont;
extern uint32_t gp_pst_sort_head_va;            /* 0xd9b2bc (tests may move it) */

#endif
