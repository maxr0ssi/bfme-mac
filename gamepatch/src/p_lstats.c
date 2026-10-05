/* logicstats: where the game-logic time goes, per logic phase (diagnostic, OFF by default; no
 * behaviour change). Logged every 30 s.
 *
 * Why (docs/PERFORMANCE.md §14): GameLogic::update 0x62e4e8 runs once per drawn frame with a
 * phase 1..6 (30 frames/s = 5 logic steps x 6 phases), and the phases are very uneven. In the
 * 2026-09-24 AI battle (memprobe, build/rotwk-re/probe-msync2) the logic took 1.5 / 5.3 / 11.2 /
 * 16.1 / 29.7 / 0.3 ms per step in phases 1-6, so one frame in six carries ~30 ms of logic on top
 * of rendering. Phase 2 runs two subsystems and a per-object loop (0x6260e1); phases 3-4 update the
 * first half / second half of update list 0, phase 5 lists 1-2 and twelve subsystems, phase 6 list 3.
 *
 * Hooks (all run the original with the caller's registers, p_lstats.S):
 *   vtable slots 0xbd85c4, 0xbfdb9c  GameLogic::update: ms per phase, frame interval per phase
 *   0x62ea97 (7 B)                    the update-list call [ebx+0x10]->vt[0]: ms per module vtable
 *   six direct calls (CALLS[])        ms per phase
 *   vt+0x28 of the 19 singletons GameLogic::update calls (SUBS[]; hooked at the first logic step
 *   that finds the object): ms per phase
 * Every site is checked against the original bytes, the whole function by its FNV-1a hash. */
#include "gp.h"
#include "gp_logic.h"
#include <stdio.h>
#include <string.h>

#define NK 32                   /* kinds: 0-18 subsystems, 24-29 direct calls */
#define NMOD 512                /* module vtables, open addressing */
#define PERIOD_MS 30000

static const uint32_t SUBS[19][2] = {   /* call site, the global holding the object */
    {0x62e6af, 0xde3bac}, {0x62e6ba, 0xde7804}, {0x62e8a8, 0xde7cd8}, {0x62e8b3, 0xde46a8},
    {0x62e8be, 0xde772c}, {0x62e93b, 0xde4354}, {0x62e946, 0xde4360}, {0x62eb69, 0xde4b40},
    {0x62eb85, 0xde4358}, {0x62eb90, 0xde435c}, {0x62eb9b, 0xde8200}, {0x62eba6, 0xde3be8},
    {0x62ebb8, 0xde4a1c}, {0x62ebc3, 0xde369c}, {0x62ebce, 0xde89ac}, {0x62ebd9, 0xde8ac0},
    {0x62ebef, 0xde4938}, {0x62ebfa, 0xde7924}, {0x62ec05, 0xde8304}};
static const uint32_t CALLS[6][2] = {   /* call site, callee */
    {0x62e8cf, 0x820ef0}, {0x62e8da, 0x81be85}, {0x62e96f, 0x6260e1}, {0x62eb76, 0x629da6},
    {0x62ebb3, 0x62a2c9}, {0x62ebea, 0x80f4d3}};

uint32_t gp_lst_logic_cont, gp_lst_cont[NK];
uint32_t gp_lst_sub_slot[19];           /* the hooked vtable slot of each subsystem (0 = not yet) */
DWORD gp_lst_period_ms = PERIOD_MS;
static void (*const sub_stub[19])(void) = {
    gp_lst_sub0, gp_lst_sub1, gp_lst_sub2, gp_lst_sub3, gp_lst_sub4, gp_lst_sub5, gp_lst_sub6,
    gp_lst_sub7, gp_lst_sub8, gp_lst_sub9, gp_lst_sub10, gp_lst_sub11, gp_lst_sub12, gp_lst_sub13,
    gp_lst_sub14, gp_lst_sub15, gp_lst_sub16, gp_lst_sub17, gp_lst_sub18};
static void (*const call_stub[6])(void) = {
    gp_lst_call0, gp_lst_call1, gp_lst_call2, gp_lst_call3, gp_lst_call4, gp_lst_call5};

typedef struct { uint64_t ticks; LONG calls; } acc_t;
typedef struct { uint32_t vt, fn; acc_t a; } mod_t;
static struct {
    acc_t logic[7], kind[NK][7], mods_by_phase[7];
    uint64_t gap_sum[7], gap_max[7]; LONG gap_n[7], gap_40[7], gap_50[7];   /* frame intervals */
    LONG steps;
} S, L;                                 /* totals, and the totals at the last report */
static mod_t mods[NMOD], lmods[NMOD];
static int phase, last_phase_seen, on, unresolved = 19;
static uint64_t last_entry, t_report, q_report;
static DWORD tick_report;

static void hook_subsystems(void)       /* the singletons exist once the engine is up */
{
    for (int i = 0; i < 19; i++) {
        if (gp_lst_sub_slot[i]) continue;
        const uint8_t *obj = *(const uint8_t *const *)(uintptr_t)SUBS[i][1];
        MEMORY_BASIC_INFORMATION mi;
        if (!obj || !VirtualQuery(obj, &mi, sizeof mi) || mi.State != MEM_COMMIT) continue;
        uint32_t slot = *(const uint32_t *)obj + 0x28, fn;
        int dup = 0;
        for (int j = 0; j < 19; j++) dup |= j != i && gp_lst_sub_slot[j] == slot;
        if (dup) { gp_lst_sub_slot[i] = slot; unresolved--; gp_log("logicstats: %06x shares %06x's update", SUBS[i][1], slot); continue; }
        if (!VirtualQuery((void *)(uintptr_t)slot, &mi, sizeof mi) || mi.State != MEM_COMMIT) continue;
        fn = *(const uint32_t *)(uintptr_t)slot;
        DWORD old;
        if (!VirtualProtect((void *)(uintptr_t)slot, 4, PAGE_READWRITE, &old)) continue;
        gp_lst_cont[i] = fn;
        *(volatile uint32_t *)(uintptr_t)slot = (uint32_t)(uintptr_t)sub_stub[i];
        VirtualProtect((void *)(uintptr_t)slot, 4, old, &old);
        gp_lst_sub_slot[i] = slot; unresolved--;
        gp_log("logicstats: subsystem %06x (object %p): update %08x at vtable slot %08x hooked", SUBS[i][1], obj, fn, slot);
    }
}

static uint64_t ticks_per_ms(void)      /* time stamp counter ticks per ms over the last window */
{
    LARGE_INTEGER q, f;
    QueryPerformanceCounter(&q); QueryPerformanceFrequency(&f);
    uint64_t t = __builtin_ia32_rdtsc(), dq = (uint64_t)q.QuadPart - q_report, dt = t - t_report, r = 0;
    if (q_report && dq) r = (uint64_t)((double)dt * (double)f.QuadPart / (double)dq / 1000.0);
    t_report = t; q_report = (uint64_t)q.QuadPart;
    return r;
}
static double msd(uint64_t ticks, uint64_t tpms, LONG n) { return tpms && n > 0 ? (double)ticks / (double)tpms / n : 0; }

static void report(void)
{
    uint64_t tpms = ticks_per_ms();
    LONG n = S.steps - L.steps;
    char b[480]; int k = 0;
    if (!tpms || n <= 0) goto done;
    k = snprintf(b, sizeof b, "logicstats: last %lu s, %ld logic steps; ms per step in phases 1-6 (frame interval after it: mean/max ms, frames > 40 / > 50 ms):",
                 (unsigned long)(gp_lst_period_ms / 1000), n);
    for (int p = 1; p <= 6 && k < (int)sizeof b; p++) {
        LONG g = S.gap_n[p] - L.gap_n[p];
        k += snprintf(b + k, sizeof b - k, " %d: %.2f (%.1f/%.1f, %ld/%ld)", p, msd(S.logic[p].ticks - L.logic[p].ticks, tpms, n),
                      msd(S.gap_sum[p] - L.gap_sum[p], tpms, g), msd(S.gap_max[p], tpms, 1), S.gap_40[p] - L.gap_40[p], S.gap_50[p] - L.gap_50[p]);
    }
    gp_log("%s", b);
    /* subsystems and direct calls: ms per step and the phase they mostly ran in */
    k = snprintf(b, sizeof b, "logicstats: ms per step, object@phase:");
    for (int kd = 0; kd < NK && k < (int)sizeof b - 40; kd++) {
        uint64_t t = 0, best = 0; int bp = 0;
        for (int p = 0; p <= 6; p++) {
            uint64_t d = S.kind[kd][p].ticks - L.kind[kd][p].ticks;
            t += d; if (d > best) { best = d; bp = p; }
        }
        if (msd(t, tpms, n) < 0.05) continue;
        k += snprintf(b + k, sizeof b - k, " %s%06x %.2f@%d", kd >= 24 ? "fn" : "", kd >= 24 ? CALLS[kd - 24][1] : SUBS[kd < 19 ? kd : 0][1],
                      msd(t, tpms, n), bp);
    }
    k += snprintf(b + k, sizeof b - k, "; update modules by phase");
    for (int p = 1; p <= 6 && k < (int)sizeof b; p++)
        k += snprintf(b + k, sizeof b - k, " %.2f", msd(S.mods_by_phase[p].ticks - L.mods_by_phase[p].ticks, tpms, n));
    gp_log("%s", b);
    /* the 12 module classes that took the most time */
    k = snprintf(b, sizeof b, "logicstats: update modules, update fn (vtable) ms per step / calls per step:");
    static uint8_t used[NMOD];
    memset(used, 0, sizeof used);
    for (int r = 0; r < 12; r++) {
        int bi = -1; uint64_t bt = 0;
        for (int i = 0; i < NMOD; i++) {
            uint64_t d = mods[i].a.ticks - lmods[i].a.ticks;
            if (mods[i].vt && !used[i] && d > bt) { bt = d; bi = i; }
        }
        if (bi < 0 || msd(bt, tpms, n) < 0.02) break;
        used[bi] = 1;
        k += snprintf(b + k, sizeof b - k, " %06x(%06x) %.2f/%.1f", mods[bi].fn, mods[bi].vt, msd(bt, tpms, n),
                      (double)(mods[bi].a.calls - lmods[bi].a.calls) / n);
        if (k >= (int)sizeof b - 32) break;
    }
    gp_log("%s", b);
done:
    L = S; memcpy(lmods, mods, sizeof mods);
    for (int p = 0; p <= 6; p++) S.gap_max[p] = 0;
}

static void acc(acc_t *a, uint32_t t0lo, uint32_t t0hi, uint32_t t1lo, uint32_t t1hi)
{
    uint64_t t0 = (uint64_t)t0hi << 32 | t0lo, t1 = (uint64_t)t1hi << 32 | t1lo;
    a->calls++;
    if (t1 > t0) a->ticks += t1 - t0;
}

/* called from p_lstats.S, main thread only (the logic and everything under it) */
uint64_t gp_lst_tpms_guess = 1000000;  /* ticks per ms (~1 GHz under Rosetta), measured at each report */
__attribute__((force_align_arg_pointer)) void gp_lst_begin(int ph)
{
    uint64_t t = __builtin_ia32_rdtsc();
    int lp = last_phase_seen;
    if (last_entry && lp >= 1 && t > last_entry) {    /* from the last step's start to this one's */
        uint64_t g = t - last_entry;
        S.gap_sum[lp] += g; S.gap_n[lp]++;
        if (g > S.gap_max[lp]) S.gap_max[lp] = g;
        if (g > 40 * gp_lst_tpms_guess) S.gap_40[lp]++;
        if (g > 50 * gp_lst_tpms_guess) S.gap_50[lp]++;
    }
    last_entry = t;
    last_phase_seen = phase = ph >= 1 && ph <= 6 ? ph : 0;
    if (unresolved) hook_subsystems();
}
__attribute__((force_align_arg_pointer)) void gp_lst_end(uint32_t t0lo, uint32_t t0hi, uint32_t t1lo, uint32_t t1hi)
{
    acc(&S.logic[phase], t0lo, t0hi, t1lo, t1hi);
    if (phase == 1) S.steps++;
    phase = 0;
    DWORD now = GetTickCount();
    if (!tick_report) { tick_report = now; ticks_per_ms(); L = S; return; }
    if (now - tick_report >= gp_lst_period_ms) {
        LARGE_INTEGER q, f; QueryPerformanceCounter(&q); QueryPerformanceFrequency(&f);
        uint64_t dq = (uint64_t)q.QuadPart - q_report, dt = __builtin_ia32_rdtsc() - t_report;
        if (dq) gp_lst_tpms_guess = (uint64_t)((double)dt * (double)f.QuadPart / (double)dq / 1000.0);
        report(); tick_report = now;
    }
}
__attribute__((force_align_arg_pointer))
void gp_lst_timed(unsigned kind, uint32_t t0lo, uint32_t t0hi, uint32_t t1lo, uint32_t t1hi)
{
    if (kind < NK) acc(&S.kind[kind][phase], t0lo, t0hi, t1lo, t1hi);
}
__attribute__((force_align_arg_pointer))
void gp_lst_mod(uint32_t vt, uint32_t t0lo, uint32_t t0hi, uint32_t t1lo, uint32_t t1hi)
{
    acc(&S.mods_by_phase[phase], t0lo, t0hi, t1lo, t1hi);
    uint32_t h = (vt >> 2) * 2654435761u >> 23;          /* 9 bits */
    for (int i = 0; i < NMOD; i++, h = (h + 1) & (NMOD - 1)) {
        mod_t *m = &mods[h];
        if (!m->vt) { m->vt = vt; m->fn = *(const uint32_t *)(uintptr_t)vt; }
        if (m->vt == vt) { acc(&m->a, t0lo, t0hi, t1lo, t1hi); return; }
    }
}

/* the phase the logic is in (0 outside GameLogic::update), -1 when off; read by the stall sampler's thread */
int gp_lst_phase(void) { return on ? phase : -1; }

/* tests */
void gp_lst_force_report(void) { tick_report = GetTickCount() - gp_lst_period_ms; gp_lst_end(0, 0, 0, 0); }
void gp_lst_get(int kind, int ph, LONG *calls, uint64_t *ticks)
{
    const acc_t *a = kind == -1 ? &S.logic[ph] : kind == -2 ? &S.mods_by_phase[ph] : &S.kind[kind][ph];
    *calls = a->calls; *ticks = a->ticks;
}
LONG gp_lst_mod_calls(uint32_t vt)
{
    for (int i = 0; i < NMOD; i++) if (mods[i].vt == vt) return mods[i].a.calls;
    return 0;
}

void gp_lst_exit_log(void)
{
    if (!on) return;
    LONG mc = 0;
    for (int i = 0; i < NMOD; i++) mc += mods[i].a.calls;
    gp_log("exit: logicstats: %ld logic steps, %ld update-module calls, %d of 19 subsystems hooked", S.steps, mc, 19 - unresolved);
}

int gp_patch_logicstats(void)
{
    static const uint8_t vt[] = {0xe8, 0xe4, 0x62, 0x00};                   /* 0x62e4e8 */
    static const uint8_t mod[] = {0x8d, 0x4b, 0x10, 0x8b, 0x01, 0xff, 0x10};
    static const uint8_t nop2[] = {0x66, 0x90};
    static uint8_t subpat[19][11], callb[6][5];
    gp_site s[40];
    int n = 0;
    gp_site_hash(&s[n++], 0x62e4e8, 0x985, 0x0a78f009bb0ad7e5ull);  /* GameLogic::update, whole */
    for (int i = 0; i < 19; i++) {           /* mov ecx,[G]; mov eax,[ecx]; call [eax+0x28] */
        uint8_t *p = subpat[i];
        p[0] = 0x8b; p[1] = 0x0d; memcpy(p + 2, &SUBS[i][1], 4);
        p[6] = 0x8b; p[7] = 0x01; p[8] = 0xff; p[9] = 0x50; p[10] = 0x28;
        gp_site_init(&s[n], SUBS[i][0], p, 11); s[n++].wlen = 0;      /* check only */
    }
    for (int i = 0; i < 6; i++, n++) {
        int32_t rel = (int32_t)(CALLS[i][1] - (CALLS[i][0] + 5));
        callb[i][0] = 0xe8; memcpy(callb[i] + 1, &rel, 4);
        gp_site_init(&s[n], CALLS[i][0], callb[i], 5);
        gp_rel32(&s[n], 0, 0xe8, (void *)call_stub[i]);
        gp_lst_cont[24 + i] = CALLS[i][1] + gp_va_offset;
    }
    gp_site_init(&s[n], 0x62ea97, mod, 7);
    gp_rel32(&s[n], 0, 0xe8, (void *)gp_lst_mod_stub);
    memcpy(s[n++].repl + 5, nop2, 2);
    uint32_t stub = (uint32_t)(uintptr_t)gp_lst_logic_stub;
    gp_site_init(&s[n], 0xbd85c4, vt, 4); memcpy(s[n++].repl, &stub, 4);
    gp_site_init(&s[n], 0xbfdb9c, vt, 4); memcpy(s[n++].repl, &stub, 4);
    gp_lst_logic_cont = 0x62e4e8 + gp_va_offset;
    if (!gp_apply("logicstats", s, n)) return 0;
    on = 1;
    return 1;
}
