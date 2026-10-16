/* t_phasebal: phasebalance (p_phasebal.c/.S) on the game's own GameLogic::update, run on a synthetic
 * world of objects and update modules (t_phasebal_world.c; phases 2-6 through the game's code).
 *   [1] the patch applies to the original bytes (the function by hash, the seven regions) and
 *       writes a jump to its stub at each region;
 *   [2] mode 2 (EA's own split, re-expressed by the hooks) gives exactly the original's events,
 *       phase labels included, in a static and a mutating world, in two memory layouts: the hooks
 *       and their frame handling are transparent;
 *   [3] the balanced plan: the same events again in a second run and in a second memory layout;
 *       no module updated twice in a step, every module due at a step's start updated in it, each
 *       list's modules in list order; EA's own split misses some in the mutating world (modules
 *       woken between its two halves move n/2);
 *   [4] the balanced plan against the original in the static world: the same sequence of module
 *       updates, subsystems and phase-2 work, only the phase labels (and the pathfind queue and the
 *       pending-object pass that start/end each phase) move; the share of each list per phase;
 *   [5] pending objects (cell changes): those the phase-5 subsystems add are dropped in both, as
 *       the game drops them; those the modules add are processed in both;
 *   [6] with logicstats applied first, phasebalance still applies and gives the same events;
 *   [7] the expected ms per phase from the logicstats profiles (the 2026-10-05 and 2026-10-15
 *       8-player matches), original and balanced, and the hooks' own cost.
 * usage: t_phasebal.exe <path to lotrbfme2ep1.exe 2.02> [objects] [steps] */
#include "orig.h"
#include "gp.h"
#include "gp_logic.h"
#include "p_fps.h"
#include "t_phasebal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXEV 4000000
static int fails;
static pb_ev *A, *B;

static int run(int mode, uint32_t seed, uint32_t salt, int mutate, int nobj, int steps, pb_ev *e,
               int *missed, int *twice, int *unord)
{
    if (!pb_patch(mode)) { printf("cannot patch\n"); exit(1); }
    pb_cfg c = {seed, salt, mutate, nobj};
    pb_world *w = pb_build(&c);
    int n = pb_run(w, steps, e, MAXEV, missed, twice, unord);
    pb_free(w);
    if (n > MAXEV) { printf("event buffer too small (%d)\n", n); exit(1); }
    return n;
}

/* 0 = equal; else 1 + the index of the first difference */
static int cmp_ev(const pb_ev *a, int na, const pb_ev *b, int nb, int phases)
{
    int n = na < nb ? na : nb;
    for (int i = 0; i < n; i++)
        if (a[i].step != b[i].step || a[i].kind != b[i].kind || a[i].id != b[i].id || a[i].aux != b[i].aux ||
            (phases && a[i].phase != b[i].phase)) return i + 1;
    return na == nb ? 0 : n + 1;
}
static int keep_work(const pb_ev *e) { return e->kind == EV_MOD || e->kind == EV_SUB || e->kind == EV_AI || e->kind == EV_P2 || e->kind == EV_SUBCALL; }
static int filter(pb_ev *e, int n)
{
    int k = 0;
    for (int i = 0; i < n; i++) if (keep_work(&e[i])) e[k++] = e[i];
    return k;
}
static int count(const pb_ev *e, int n, int kind, int sentinel)
{
    int c = 0;
    for (int i = 0; i < n; i++) if (e[i].kind == kind && (sentinel < 0 || !!(e[i].id & 0x80000000u) == sentinel)) c++;
    return c;
}

/* ---- [7] the per-phase model ---------------------------------------------------------------- */
typedef struct { const char *name; double p1, p2own, l0, l0a, l0b, l1, l2, ai, sub, l3, q; } prof;
static const prof PROF[4] = {   /* ms per logic step (docs/PERFORMANCE.md §29: where each comes from) */
    {"10-05 mean", 2.1, 1.9, 15.2, 6.6, 8.6, 2.3, 3.7, 0.86, 4.94, 1.4, 0.2},
    {"10-05 heaviest quarter", 2.7, 2.8, 19.0, 7.9, 11.1, 3.2, 5.2, 1.2, 7.2, 2.2, 0.2},
    {"10-15 mean", 1.55, 1.11, 9.87, 3.98, 5.89, 2.29, 1.98, 0.36, 2.96, 0.52, 0.1},
    {"10-15 heaviest quarter", 3.07, 1.61, 16.6, 6.52, 10.07, 3.3, 2.94, 0.5, 4.46, 0.71, 0.1}};
static double cumshare(const prof *p, double x)   /* list 0's cost up to index fraction x: linear density fitted to its halves */
{
    double h = p->l0a / (p->l0a + p->l0b), r = (h - 0.5) / (0.125 - h / 2), al = 1 / (1 + r / 2), be = r * al;
    return al * x + be * x * x / 2;
}
static double item_cost(const prof *p, int item, double a, double b)
{
    double c[6] = {0, p->l1, p->l2, p->ai, p->sub, p->l3};
    return item == GP_PB_L0 ? p->l0 * (cumshare(p, b) - cumshare(p, a)) : c[item] * (b - a);
}
static void model(const prof *p, const gp_pb_target *plan, double out[7])
{
    out[1] = p->p1;
    int it = GP_PB_L0; double f = 0;
    for (int ph = 2; ph <= 6; ph++) {
        double t = ph == 2 ? p->p2own : p->q;
        int ti = plan[ph].item; double tf = plan[ph].frac / 1024.0;
        while (it < GP_PB_DONE && (it < ti || (it == ti && f < tf))) {
            double end = it == ti ? tf : 1.0;
            t += item_cost(p, it, f, end);
            if (it == ti) { f = tf; break; }
            it++; f = 0;
        }
        out[ph] = t;
    }
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (pb_init(argc > 1 ? argv[1] : orig_default_path())) { printf("FAIL\n"); return 2; }
    int nobj = argc > 2 ? atoi(argv[2]) : 1500, steps = argc > 3 ? atoi(argv[3]) : 60;
    A = malloc(sizeof *A * MAXEV); B = malloc(sizeof *B * MAXEV);
    int mi, tw, un, mi2, tw2, un2;

    /* [1] */
    uint8_t before[0x985];
    memcpy(before, (void *)(uintptr_t)(0x62e4e8 + OFF), sizeof before);
    int ok = pb_patch(1);
    static const uint32_t RVA[7] = {0x62e982, 0x62e9d4, 0x62ea09, 0x62eadf, 0x62eb63, 0x62eb7b, 0x62ec10};
    void (*const stub[7])(void) = {gp_pb_s_lists, gp_pb_s_start, gp_pb_s_stop, gp_pb_s_end, gp_pb_s_ai, gp_pb_s_sub, gp_pb_s_reenter};
    int wrong = 0, changed = 0;
    for (int i = 0; i < 7; i++) {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(RVA[i] + OFF);
        int32_t rel; memcpy(&rel, p + 1, 4);
        wrong += p[0] != 0xe9 || (uint32_t)(uintptr_t)(p + 5) + (uint32_t)rel != (uint32_t)(uintptr_t)stub[i];
    }
    for (int i = 0; i < 0x985; i++) changed += before[i] != ((uint8_t *)(uintptr_t)(0x62e4e8 + OFF))[i];
    wrong += gp_pb_cont[0] != 0x62e9ca + OFF || gp_pb_cont[9] != 0x441b60 + OFF;
    printf("[1] phasebalance applied to the original bytes: %s; 7 jumps to the stubs, continuations: %s (%d bytes "
           "of GameLogic::update changed)\n", ok ? "yes" : "NO", wrong ? "WRONG" : "right", changed);
    if (!ok || wrong) { printf("FAIL\n"); return 1; }

    /* [2] */
    int bad = 0, nev = 0;
    for (int mut = 0; mut < 2; mut++)
        for (uint32_t salt = 0; salt < 2; salt++) {
            int na = run(0, 20261015 + mut, salt * 5, mut, nobj, steps, A, &mi, &tw, &un);
            int nb = run(2, 20261015 + mut, salt * 5, mut, nobj, steps, B, &mi2, &tw2, &un2);
            int d = cmp_ev(A, na, B, nb, 1);
            if (d) printf("    %s world, layout %u: first difference at event %d of %d / %d\n", mut ? "mutating" : "static",
                          salt, d - 1, na, nb);
            bad += d != 0; nev += na;
        }
    printf("[2] EA's split through the hooks against the original: %s (%d events in 4 runs of %d steps, %d objects)\n",
           bad ? "DIFFERENT" : "identical, phase labels included", nev, steps, nobj);
    fails += bad;

    /* [3] */
    bad = 0;
    int ea_missed = 0, ea_twice = 0;
    for (int mut = 0; mut < 2; mut++) {
        int na = run(1, 20261015 + mut, 0, mut, nobj, steps, A, &mi, &tw, &un);
        int bm = mi, bt = tw, bu = un;
        for (int r = 0; r < 2; r++) {
            int nb = run(1, 20261015 + mut, r ? 11 : 0, mut, nobj, steps, B, &mi2, &tw2, &un2);
            int d = cmp_ev(A, na, B, nb, 1);
            if (d) printf("    %s world, %s: first difference at event %d\n", mut ? "mutating" : "static",
                          r ? "second layout" : "second run", d - 1);
            bad += d != 0;
        }
        printf("    %s world, balanced: %d events; modules due but not updated %d, updated twice %d, out of list "
               "order %d\n", mut ? "mutating" : "static", na, bm, bt, bu);
        bad += bm || bt || bu;
        run(0, 20261015 + mut, 0, mut, nobj, steps, B, &mi2, &tw2, &un2);
        if (mut) { ea_missed = mi2; ea_twice = tw2; }
        printf("    %s world, original: modules due but not updated %d, updated twice %d, out of list order %d\n",
               mut ? "mutating" : "static", mi2, tw2, un2);
    }
    printf("[3] balanced: the same events in a second run and a second memory layout, every due module once, in list "
           "order: %s (the game's own split: %d due modules a step later, %d twice)\n", bad ? "NO" : "yes", ea_missed, ea_twice);
    fails += bad;

    /* [4] */
    int na = run(0, 20261015, 0, 0, nobj, steps, A, &mi, &tw, &un);
    int nb = run(1, 20261015, 0, 0, nobj, steps, B, &mi2, &tw2, &un2);
    long per[7][4] = {{0}}, tot[4] = {0};
    for (int i = 0; i < nb; i++) if (B[i].kind == EV_MOD) { per[B[i].phase][B[i].aux >> 24]++; tot[B[i].aux >> 24]++; }
    int qa = count(A, na, EV_Q, -1), qb = count(B, nb, EV_Q, -1), da = count(A, na, EV_D, -1), db = count(B, nb, EV_D, -1);
    int fa = filter(A, na), fb = filter(B, nb);
    int d = cmp_ev(A, fa, B, fb, 0);
    printf("[4] static world, balanced against the original: the same %d updates, subsystem calls and phase-2 work in "
           "the same order: %s; queue runs %d / %d, pending passes %d / %d\n", fa, d ? "NO" : "yes", qa, qb, da, db);
    if (d) printf("    first difference at work event %d\n", d - 1);
    fails += d != 0 || qa != qb || da != db;
    for (int ph = 2; ph <= 6; ph++)
        printf("    phase %d: list 0 %4.1f %%, list 1 %4.1f %%, list 2 %4.1f %%, list 3 %4.1f %% of each list's updates\n", ph,
               100.0 * per[ph][0] / (tot[0] ? tot[0] : 1), 100.0 * per[ph][1] / (tot[1] ? tot[1] : 1),
               100.0 * per[ph][2] / (tot[2] ? tot[2] : 1), 100.0 * per[ph][3] / (tot[3] ? tot[3] : 1));

    /* [5] */
    na = run(0, 20261016, 0, 1, nobj, steps, A, &mi, &tw, &un);
    nb = run(1, 20261016, 0, 1, nobj, steps, B, &mi2, &tw2, &un2);
    int sa = count(A, na, EV_PEND, 1), sb = count(B, nb, EV_PEND, 1), pa = count(A, na, EV_PEND, 0), pb = count(B, nb, EV_PEND, 0);
    printf("[5] pending objects from the subsystems processed: original %d, balanced %d (expected 0, %ld truncations); "
           "from the modules: %d / %d\n", sa, sb, (long)gp_pb_stats[4], pa, pb);
    fails += sa || sb || !pa || !pb || !gp_pb_stats[4];

    /* [6] */
    na = run(1, 20261016, 0, 1, nobj, steps, A, &mi, &tw, &un);
    pb_patch(0);
    static uint8_t fn_keep[0x985];
    memcpy(fn_keep, (void *)(uintptr_t)(0x62e4e8 + OFF), sizeof fn_keep);
    gp_va_offset = OFF;
    int okl = gp_patch_logicstats(), okp = okl ? gp_patch_phasebalance() : 0;
    gp_va_offset = 0;
    gp_pb_mode = 1;
    if (okp) {
        pb_cfg c = {20261016, 0, 1, nobj};
        pb_world *w = pb_build(&c);
        nb = pb_run(w, steps, B, MAXEV, &mi2, &tw2, &un2);
        pb_free(w);
    }
    LONG lcalls = gp_lst_mod_calls((uint32_t)(uintptr_t)pb_iface_vt());
    memcpy((void *)(uintptr_t)(0x62e4e8 + OFF), fn_keep, sizeof fn_keep);   /* both off again */
    d = okp ? cmp_ev(A, na, B, nb, 1) : 1;
    printf("[6] with logicstats applied first: logicstats %s, phasebalance %s, events %s (logicstats timed %ld module "
           "updates)\n", okl ? "applied" : "NOT applied", okp ? "applied" : "NOT applied", d ? "DIFFERENT" : "identical", lcalls);
    fails += !okl || !okp || d || lcalls < 1;

    /* [7] */
    gp_pb_target ea[7] = {{0, 0}, {GP_PB_L0, 0}, {GP_PB_L0, 0}, {GP_PB_L0, 512}, {GP_PB_L1, 0}, {GP_PB_L3, 0}, {GP_PB_DONE, 0}};
    printf("[7] expected ms per logic step in phases 1-6 (profile costs, list 0's cost density from its measured halves):\n");
    for (int i = 0; i < 4; i++) {
        double o[7], b2[7], mo = 0, mb = 0;
        model(&PROF[i], ea, o); model(&PROF[i], gp_pb_plan, b2);
        for (int ph = 1; ph <= 6; ph++) { if (o[ph] > mo) mo = o[ph]; if (b2[ph] > mb) mb = b2[ph]; }
        printf("    %-24s original %4.1f %4.1f %4.1f %4.1f %4.1f %4.1f (max %4.1f) | balanced %4.1f %4.1f %4.1f %4.1f %4.1f %4.1f (max %4.1f)\n",
               PROF[i].name, o[1], o[2], o[3], o[4], o[5], o[6], mo, b2[1], b2[2], b2[3], b2[4], b2[5], b2[6], mb);
    }
    double us[3];
    int lists = 0, mods = 0;
    for (int mode = 0; mode < 3; mode++) {
        pb_patch(mode);
        pb_cfg c = {20261015, 0, 0, nobj};
        pb_world *w = pb_build(&c);
        double best = 1e30;
        for (int r = 0; r < 5; r++) { double t = pb_us_per_step(w, 20); if (t < best) best = t; }
        if (!mode) pb_counts(w, &mods, &lists);
        pb_free(w);
        us[mode] = best;
    }
    printf("    the hooks' cost: %.1f us a step original, %.1f balanced, %.1f EA's split through the hooks (static world, "
           "%d modules, %d in update lists; best of 5 x 20 steps)\n", us[0], us[1], us[2], mods, lists);
    printf("%s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
