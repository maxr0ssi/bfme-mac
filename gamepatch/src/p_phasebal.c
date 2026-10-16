/* phasebalance: GameLogic::update's list work spread over logic phases 2-6 (OFF by default; it
 * changes when work runs relative to the drawn frames, so every LAN player needs the same switch).
 *
 * Why (docs/FPS-ROADMAP.md §1, §4 step 1; docs/PERFORMANCE.md §29): the game draws one frame per
 * logic phase, and the phases are very uneven. In the 2026-10-05 8-player match the logic took 2.1 /
 * 1.9 / 6.6 / 8.6 / 12.0 / 1.4 ms per step in phases 1-6, so the phase-5 frame drops below 30 FPS.
 *
 * What GameLogic::update 0x62e4e8 does with a logic step's work (after phase 1 and phase 2's own
 * subsystems), in this order:
 *   L0  update list 0 (AI, animals, hordes' AI, workers ...)   EA: phase 3 [0, n/2), phase 4 [n/2, n)
 *   L1  update list 1 (HordeContain)                           EA: phase 5
 *   L2  update list 2 (weapons, special powers, production ...) EA: phase 5
 *   AI  TheAI's update (0xde4b40 vt+0x28)                      EA: phase 5
 *   SUB the twelve subsystems after it (shroud, destroy list ...) EA: phase 5
 *   L3  update list 3                                          EA: phase 6
 * Each list's last pass moves its sleeping modules to the sleep list (the clean-up); every call
 * ends with 0x629da6 (objects that changed cell this phase), except that in EA's phase 5 it runs
 * between AI and SUB. The phase boundaries here (gp_pb_plan) cut the same sequence elsewhere:
 *   phase 2: its own work, L0 [0, 36 %)         phase 3: L0 [36 %, 74 %)
 *   phase 4: L0 [74 %, end), L1 [0, 30 %)       phase 5: L1 [30 %, end), L2, AI
 *   phase 6: SUB, L3
 * Cuts are list indices, fractions of the list's size when its first pass of the step began; a pass
 * resumes where the previous one stopped, so every module in a list is visited once per step in
 * list order (EA's own half split recomputes n/2 at phase 4 and skips modules woken in between).
 * No time, address or machine property is read: the same lists give the same cuts everywhere.
 * 0x629da6 runs at the end of each phase and after AI, as in EA; the pending objects the subsystems
 * add are dropped before list 3, as EA's next call drops them (its prologue erases the list).
 *
 * Hooks: seven sites in GameLogic::update become jumps to p_phasebal.S (the dispatch, the start
 * index, the stop test, the clean-up test, the AI test, the subsystems test, and the call after
 * them, where list 3 gets a second round of EA's own list loop). The list loop itself, the module
 * calls, the clean-up and every subsystem call are the game's code. The function is checked whole
 * by hash (logicstats' call sites, if applied first, read as their original bytes). */
#include "gp.h"
#include "p_fps.h"
#include <string.h>

int gp_pb_mode;
gp_pb_target gp_pb_plan[7] = {
    {GP_PB_L0, 0}, {GP_PB_L0, 0}, {GP_PB_L0, 369}, {GP_PB_L0, 758}, {GP_PB_L1, 307}, {GP_PB_SUB, 0},
    {GP_PB_DONE, 0}};
uint32_t gp_pb_cont[12];
uint32_t gp_pb_stop_at = 0xffffffffu;
volatile LONG gp_pb_stats[6];

static const uint8_t ITEM_OF_LIST[4] = {GP_PB_L0, GP_PB_L1, GP_PB_L2, GP_PB_L3};
static const uint8_t NEXT[GP_PB_DONE + 1] = {GP_PB_L1, GP_PB_L2, GP_PB_AI, GP_PB_SUB, GP_PB_L3, GP_PB_DONE, GP_PB_DONE};

static struct {
    uint32_t frame;
    int valid, item, round2, pend_set;
    uint32_t resume, pass_start, pend_n, nfirst[4];
    uint8_t started[4];
} st;

static uint32_t vsize(const uint32_t *vec) { return (uint32_t)((int32_t)(vec[1] - vec[0]) >> 2); }
static gp_pb_target target(int phase)
{
    gp_pb_target z = {GP_PB_L0, 0};
    return phase >= 1 && phase <= 6 ? gp_pb_plan[phase] : z;
}
static uint32_t cut(int list, uint16_t frac) { return (uint32_t)(((uint64_t)st.nfirst[list] * frac) >> 10); }
static int is_cut(gp_pb_target t, int list) { return t.item == ITEM_OF_LIST[list] && t.frac; }

static void sync(const uint8_t *gl, int phase, int new_step)
{
    uint32_t fr = *(const uint32_t *)(gl + 0x40);       /* the logic frame, +1 in phase 1 */
    if (st.valid && fr == st.frame && !(new_step && phase == 1)) return;
    memset(&st, 0, sizeof st);
    st.valid = 1; st.frame = fr; st.item = GP_PB_L0;
    gp_pb_stats[0]++;
}

/* is there list work between the cursor and the phase's end? */
static int ahead(gp_pb_target t)
{
    if (t.item != st.item) return t.item > st.item;
    if (st.item > GP_PB_L2 || !t.frac) return 0;
    int l = st.item;            /* L0..L2 are lists 0..2 */
    return !st.started[l] || cut(l, t.frac) > st.resume;
}

__attribute__((force_align_arg_pointer)) int gp_pb_c_lists(uint8_t *gl, int phase, int32_t out[2])
{
    if (gp_pb_mode == 2) {      /* EA: 3-4 list 0, 5 lists 1-2, 6 list 3 */
        if (phase == 3 || phase == 4) { out[0] = 0; out[1] = 1; return 1; }
        if (phase == 5) { out[0] = 1; out[1] = 3; return 1; }
        if (phase == 6) { out[0] = 3; out[1] = 4; return 1; }
        return 0;
    }
    sync(gl, phase, 1);
    gp_pb_target t = target(phase);
    if (st.item > GP_PB_L2 || !ahead(t)) return 0;
    int last = t.item <= GP_PB_L2 ? (t.frac ? t.item : t.item - 1) : GP_PB_L2;
    if (last < st.item) return 0;
    out[0] = st.item; out[1] = last + 1;
    gp_pb_stats[1]++;
    return 1;
}

__attribute__((force_align_arg_pointer)) int gp_pb_c_start(uint8_t *gl, int phase, uint32_t *vec, int list)
{
    uint32_t n = vsize(vec);
    if (gp_pb_mode == 2) {
        gp_pb_stop_at = phase == 3 && list == 0 ? 0 : 0xffffffffu;
        return phase == 4 && list == 0 ? (int)(n >> 1) : 0;
    }
    sync(gl, phase, 0);
    if (list < 0 || list > 3 || ITEM_OF_LIST[list] != st.item) {   /* never expected: skip the pass */
        gp_pb_stop_at = 0;
        st.pass_start = 0x7fffffff;
        return 0x7fffffff;
    }
    if (!st.started[list]) { st.started[list] = 1; st.nfirst[list] = n; }
    gp_pb_target t = target(phase);
    gp_pb_stop_at = is_cut(t, list) ? cut(list, t.frac) : 0xffffffffu;
    st.pass_start = st.resume;
    return (int)st.resume;
}

__attribute__((force_align_arg_pointer)) int gp_pb_c_stop(uint8_t *gl, int phase, int list, uint32_t *vec, uint32_t idx)
{
    (void)gl;
    if (gp_pb_mode == 2) return phase == 3 && list == 0 && idx == vsize(vec) >> 1;
    if (st.pass_start == 0x7fffffff) return 1;
    st.resume = idx;
    gp_pb_stats[3]++;
    return 1;
}

__attribute__((force_align_arg_pointer)) int gp_pb_c_end(uint8_t *gl, int phase, int list, uint32_t *vec)
{
    if (gp_pb_mode == 2) return phase > 3;
    sync(gl, phase, 0);
    if (st.pass_start == 0x7fffffff || list < 0 || list > 3) return 0;
    if (is_cut(target(phase), list)) {          /* the list ended before the cut: resume there */
        uint32_t n = vsize(vec);
        st.resume = n > st.pass_start ? n : st.pass_start;
        return 0;
    }
    st.item = NEXT[ITEM_OF_LIST[list]];
    st.resume = 0;
    return 1;
}

/* 2: TheAI and 0x629da6, 1: 0x629da6 only, 0: neither */
__attribute__((force_align_arg_pointer)) int gp_pb_c_ai(uint8_t *gl, int phase)
{
    if (gp_pb_mode == 2) return phase == 5 ? 2 : 1;
    sync(gl, phase, 0);
    gp_pb_target t = target(phase);
    if (st.item == GP_PB_AI && t.item > GP_PB_AI) { st.item = GP_PB_SUB; return 2; }
    int sub_now = st.item == GP_PB_SUB && t.item > GP_PB_SUB;
    int list3_round = !st.round2 && (sub_now || st.item == GP_PB_L3) && t.item > GP_PB_L3;
    return list3_round ? 0 : 1;             /* 0x629da6 ends the phase, as in EA */
}

__attribute__((force_align_arg_pointer)) int gp_pb_c_sub(uint8_t *gl, int phase)
{
    if (gp_pb_mode == 2) return phase == 5;
    sync(gl, phase, 0);
    if (st.item != GP_PB_SUB || target(phase).item <= GP_PB_SUB) return 0;
    st.item = GP_PB_L3;
    st.pend_n = vsize((const uint32_t *)(gl + 0x164)); /* objects that changed cell, so far */
    st.pend_set = 1;
    return 1;
}

__attribute__((force_align_arg_pointer)) int gp_pb_c_reenter(uint8_t *gl, int phase, int32_t out[2])
{
    if (gp_pb_mode == 2) return 0;
    sync(gl, phase, 0);
    if (!st.round2 && st.item == GP_PB_L3 && target(phase).item > GP_PB_L3) {
        st.round2 = 1;
        if (st.pend_set) {      /* EA ran the subsystems last in phase 5; phase 6's prologue erased what they added */
            uint32_t *v = (uint32_t *)(gl + 0x164);
            if (vsize(v) > st.pend_n) { v[1] = v[0] + 4 * st.pend_n; gp_pb_stats[4]++; }
        }
        st.pend_set = 0;
        out[0] = 3; out[1] = 4;
        gp_pb_stats[2]++;
        return 1;
    }
    st.round2 = 0; st.pend_set = 0;
    return 0;
}

void gp_pb_exit_log(void)
{
    if (!gp_pb_mode) return;
    gp_log("exit: phasebalance: %ld logic steps, %ld list rounds, %ld list-3 rounds after the subsystems, %ld cuts, "
           "%ld pending-object truncations", gp_pb_stats[0], gp_pb_stats[1], gp_pb_stats[2], gp_pb_stats[3], gp_pb_stats[4]);
}

/* ---- install -------------------------------------------------------------------------------- */
#define FN_VA  0x62e4e8
#define FN_LEN 0x985
static const struct { uint32_t va; uint8_t len, b[7]; } LST_SITES[7] = {   /* logicstats' call sites */
    {0x62e8cf, 5, {0xe8, 0x1c, 0x26, 0x1f, 0x00}}, {0x62e8da, 5, {0xe8, 0xa6, 0xd5, 0x1e, 0x00}},
    {0x62e96f, 5, {0xe8, 0x6d, 0x77, 0xff, 0xff}}, {0x62eb76, 5, {0xe8, 0x2b, 0xb2, 0xff, 0xff}},
    {0x62ebb3, 5, {0xe8, 0x11, 0xb7, 0xff, 0xff}}, {0x62ebea, 5, {0xe8, 0xe4, 0x08, 0x1e, 0x00}},
    {0x62ea97, 7, {0x8d, 0x4b, 0x10, 0x8b, 0x01, 0xff, 0x10}}};

static int function_ok(void)
{
    static uint8_t b[FN_LEN];
    MEMORY_BASIC_INFORMATION mi;
    const uint8_t *p = (const uint8_t *)(uintptr_t)(FN_VA + gp_va_offset);
    if (!VirtualQuery(p, &mi, sizeof mi) || mi.State != MEM_COMMIT ||
        (uintptr_t)mi.BaseAddress + mi.RegionSize < (uintptr_t)p + FN_LEN) return 0;
    memcpy(b, p, FN_LEN);
    for (int i = 0; i < 7; i++) {
        uint8_t *s = b + (LST_SITES[i].va - FN_VA);
        if (s[0] == 0xe8 && (LST_SITES[i].len == 5 || (s[5] == 0x66 && s[6] == 0x90)))
            memcpy(s, LST_SITES[i].b, LST_SITES[i].len);
    }
    uint64_t h = gp_fnv1a(b, FN_LEN);
    if (h != GP_FNV_62E4E8) gp_log("phasebalance: GameLogic::update differs (hash %016llx); patch skipped", (unsigned long long)h);
    return h == GP_FNV_62E4E8;
}

int gp_patch_phasebalance(void)
{
    /* the original bytes of each region a stub replaces (only the first 5 run any more) */
    static const uint8_t r_lists[0x48] = {
        0x0f,0x8e,0xdb,0x01,0x00,0x00,0x8b,0x45,0x08,0x6a,0x03,0x33,0xff,0x59,0x3b,0xc1,0x89,0x7d,0xe0,0x7c,
        0x27,0x6a,0x04,0x5a,0x3b,0xc2,0x7e,0x19,0x83,0xf8,0x05,0x74,0x0c,0x83,0xf8,0x06,0x75,0x16,0x8b,0xf9,
        0x89,0x55,0xe0,0xeb,0x0f,0x33,0xff,0x47,0x89,0x4d,0xe0,0xeb,0x07,0xc7,0x45,0xe0,0x01,0x00,0x00,0x00,
        0x3b,0x7d,0xe0,0x89,0x7d,0xe8,0x0f,0x8d,0x99,0x01,0x00,0x00};
    static const uint8_t r_start[22] = {0x83,0x7d,0x08,0x04,0x75,0x0d,0x8b,0x47,0x04,0x2b,0x07,0xc1,0xf8,0x02,
        0xd1,0xe8,0x48,0xeb,0x03,0x83,0xc8,0xff};
    static const uint8_t r_stop[27] = {0x83,0x7d,0x08,0x03,0x89,0x45,0xe4,0x75,0x12,0x8b,0x4f,0x04,0x2b,0x0f,
        0xc1,0xf9,0x02,0xd1,0xe9,0x3b,0xc1,0x0f,0x84,0x2d,0x01,0x00,0x00};
    static const uint8_t r_end[6] = {0x83,0x7d,0x08,0x03,0x7e,0x6c};
    static const uint8_t r_ai[6] = {0x83,0x7d,0x08,0x05,0x75,0x0b};
    static const uint8_t r_sub[10] = {0x83,0x7d,0x08,0x05,0x0f,0x85,0x8b,0x00,0x00,0x00};
    static const uint8_t r_reent[7] = {0x8b,0xce,0xe8,0x49,0x2f,0xe1,0xff};
    static const struct { uint32_t va; const uint8_t *b; uint32_t len; void (*stub)(void); } R[7] = {
        {0x62e982, r_lists, sizeof r_lists, gp_pb_s_lists}, {0x62e9d4, r_start, sizeof r_start, gp_pb_s_start},
        {0x62ea09, r_stop, sizeof r_stop, gp_pb_s_stop}, {0x62eadf, r_end, sizeof r_end, gp_pb_s_end},
        {0x62eb63, r_ai, sizeof r_ai, gp_pb_s_ai}, {0x62eb7b, r_sub, sizeof r_sub, gp_pb_s_sub},
        {0x62ec10, r_reent, sizeof r_reent, gp_pb_s_reenter}};
    static const uint32_t cont[10] = {0x62e9ca, 0x62e9ea, 0x62ea24, 0x62eb51, 0x62eae5, 0x62eb69, 0x62eb74,
                                      0x62eb85, 0x62ec17, 0x441b60};
    if (!function_ok()) return 0;
    gp_site s[14];
    int n = 0;
    for (int i = 0; i < 7; i++) {
        gp_site_init(&s[n], R[i].va, R[i].b, R[i].len); s[n++].wlen = 0;          /* the whole region */
        uint32_t w = R[i].len < 40 ? R[i].len : 40;
        gp_site_init(&s[n], R[i].va, R[i].b, w);
        memset(s[n].repl, 0xcc, w);                                               /* never reached */
        gp_rel32(&s[n++], 0, 0xe9, (void *)R[i].stub);
    }
    for (int i = 0; i < 10; i++) gp_pb_cont[i] = cont[i] + gp_va_offset;
    if (!gp_pb_mode) gp_pb_mode = 1;
    if (!gp_apply("phasebalance", s, n)) { gp_pb_mode = 0; return 0; }
    gp_log("phasebalance: logic phases 2-6 end at list 0 %u/1024, list 0 %u/1024, list 1 %u/1024, before the "
           "subsystems, the step's end (EA: list 0 half, list 0 end, lists 1-2 + AI + subsystems, list 3)",
           gp_pb_plan[2].frac, gp_pb_plan[3].frac, gp_pb_plan[4].frac);
    return 1;
}
