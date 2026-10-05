/* t_path: pathfind (p_path.c) against the game's own pathfinder search, on synthetic 8-player
 * maps (t_path_world.c: what runs is the exe's code; only the object side is stood in for).
 *   [1] the patch applies to the original bytes (relocated copy of the code)
 *   [2] checkForMovement and the crowd cost called directly, original vs patched, on random
 *       crowded cells, radii, footprints and movement-info settings: same result and the same
 *       bytes written to the movement-info struct (the patched ones answer from the memo)
 *   [3] whole searches, original vs patched: the same popped-cell sequence, path, path cost,
 *       cell count and final open/closed lists, for reachable goals across the map, goals in a
 *       battle, and unreachable goals (the search runs to its cell limit)
 *   [4] determinism: the patched searches again (memo warm from [3]), and in a second world built
 *       from the same seed with a different memory layout (allocation order and addresses, the
 *       info pool's order), give the same results
 *   [5] time per search, original vs patched, per query kind (median of 3 runs)
 *   [6] moveawaycap: move-away floods (a goal-less search to the first free spot, as
 *       getMoveAwayFromPath 0x6fb231) from inside and at the edge of a packed block of standing
 *       units, per footprint: cells needed uncapped, then with caps of 200-1600 popped cells (found
 *       exactly when the uncapped run needed no more; repeated runs identical)
 *   [7] moveawayqueue: 7 orders for one mover in one queue run (2 given, 5 wait), a second mover,
 *       a vanished ally, then queue runs: the order log (ally, mover, position, queue run) must be
 *       the expected one, and the same when run again
 * usage: t_path.exe <path to lotrbfme2ep1.exe 2.02> [queries] [map cells per side] [units] */
#include "orig.h"
#include "gp_logic.h"
#include "t_path.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fails;
static const char *kind_name[3] = {"across the map", "into a battle", "unreachable goal"};

static int same(const pw_result *a, const pw_result *b)
{
    return a->found == b->found && a->steps == b->steps && a->cells == b->cells && a->pathlen == b->pathlen &&
           a->cost == b->cost && a->pops == b->pops && a->path == b->path && a->lists == b->lists;
}

static double run(pw_t *w, const pw_query *q, pw_result *r)
{
    pw_search(w, q, r);
    return (double)r->us;
}

static int cmpd(const void *a, const void *b) { double x = *(const double *)a, y = *(const double *)b; return (x > y) - (x < y); }

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (pw_init(argc > 1 ? argv[1] : orig_default_path())) { printf("FAIL\n"); return 2; }
    int nq = argc > 2 ? atoi(argv[2]) : 24, side = argc > 3 ? atoi(argv[3]) : 480, nunits = argc > 4 ? atoi(argv[4]) : 3200;
    pw_cfg cfg = {side, side, nunits, 20261005, 0, 1};
    pw_t *w = pw_build(&cfg);
    int units, blocked;
    pw_stats(w, &units, &blocked);
    printf("map %dx%d cells (%d x %d world units), %d blocked; %d units in four clusters\n", side, side,
           side * 10, side * 10, blocked, units);

    /* [1] */
    int ok = pw_patch(1);
    gp_va_offset = OFF;
    int ok2 = gp_patch_moveawaycap();
    gp_va_offset = 0;
    printf("[1] pathfind applied to the original bytes: %s; moveawaycap: %s\n", ok ? "yes" : "NO", ok2 ? "yes" : "NO");
    if (!ok || !ok2) { printf("FAIL\n"); return 1; }

    /* [2] */
    int bc, bw, nz = pw_direct(w, 7, 200000, &bc, &bw);
    printf("[2] 200000 direct calls each: checkForMovement %d mismatches, crowd cost %d mismatches "
           "(%d nonzero costs)\n", bc, bw, nz);
    fails += bc || bw || nz < 1000;

    /* [3] */
    pw_query *q = malloc(sizeof *q * nq);
    pw_result *ra = malloc(sizeof *ra * nq), *rb = malloc(sizeof *rb * nq);
    pw_queries(w, q, nq, 99);
    double ta[3][64], tb[3][64]; int nk[3] = {0};
    int bad = 0, found = 0, cells = 0, maxcells = 0;
    for (int i = 0; i < nq; i++) {
        double t[2][3];
        for (int k = 0; k < 3; k++) {
            pw_patch(0); t[0][k] = run(w, &q[i], &ra[i]);
            pw_patch(1); t[1][k] = run(w, &q[i], &rb[i]);
        }
        qsort(t[0], 3, sizeof(double), cmpd); qsort(t[1], 3, sizeof(double), cmpd);
        int kind = i % 3;
        if (nk[kind] < 64) { ta[kind][nk[kind]] = t[0][1]; tb[kind][nk[kind]] = t[1][1]; nk[kind]++; }
        if (!same(&ra[i], &rb[i])) { if (bad++ < 5) printf("  query %d differs: steps %d/%d cost %d/%d\n", i, ra[i].steps, rb[i].steps, ra[i].cost, rb[i].cost); }
        found += ra[i].found; cells += ra[i].cells; if (ra[i].cells > maxcells) maxcells = ra[i].cells;
    }
    printf("[3] %d searches, original vs patched: %d differ (%d found a path; %d cells allocated in all, "
           "at most %d in one)\n", nq, bad, found, cells, maxcells);
    fails += bad != 0 || found == 0;

    /* [4] */
    int bad2 = 0, bad3 = 0;
    for (int i = 0; i < nq; i++) { pw_result r; pw_search(w, &q[i], &r); bad2 += !same(&r, &rb[i]); }
    pw_free(w);
    cfg.salt = 77;
    w = pw_build(&cfg);
    for (int i = 0; i < nq; i++) { pw_result r; pw_search(w, &q[i], &r); bad3 += !same(&r, &rb[i]); }
    pw_patch(0);
    int bad4 = 0;
    for (int i = 0; i < nq; i++) { pw_result r; pw_search(w, &q[i], &r); bad4 += !same(&r, &ra[i]); }
    printf("[4] patched again: %d differ; patched in a world with another memory layout: %d differ; "
           "original there: %d differ\n", bad2, bad3, bad4);
    fails += bad2 || bad3 || bad4;

    /* [5] */
    printf("[5] ms per search (median of 3 runs each), original -> patched:\n");
    for (int k = 0; k < 3; k++) {
        if (!nk[k]) continue;
        double sa = 0, sb = 0, ma = 0, mb = 0;
        int n = nk[k], st = 0, ce = 0;
        for (int i = 0; i < n; i++) { sa += ta[k][i]; sb += tb[k][i]; if (ta[k][i] > ma) { ma = ta[k][i]; mb = tb[k][i]; } }
        for (int i = k; i < nq; i += 3) { st += ra[i].steps; ce += ra[i].cells; }
        printf("    %-17s %2d searches, %6d cells expanded on average: mean %7.2f -> %6.2f ms (x%.1f); "
               "slowest %7.2f -> %6.2f ms; %.2f -> %.2f us per expanded cell\n", kind_name[k], n, st / n,
               sa / n / 1000, sb / n / 1000, sa / (sb > 0 ? sb : 1), ma / 1000, mb / 1000,
               sa / (st ? st : 1), sb / (st ? st : 1));
        (void)ce;
    }
    {   /* the unreachable goals again with MaxCellsFindPathLimit 5000 (the group pack's value) */
        double s15 = 0, s5 = 0; int n = 0;
        for (int i = 2; i < nq; i += 3) {
            pw_query q5 = q[i]; q5.limit = 5000; pw_result r5;
            s5 += run(w, &q5, &r5); s15 += tb[2][n < 64 ? n : 63]; n++;
        }
        if (n) printf("    unreachable goal, MaxCellsFindPathLimit 15000 -> 5000 (patched): mean %.2f -> %.2f ms\n",
                      s15 / n / 1000, s5 / n / 1000);
    }
    printf("    memo: %ld resets, %ld checkForMovement calls, %ld crowd costs, %ld unit memo misses\n",
           gp_pf_stats[0], gp_pf_stats[1], gp_pf_stats[2], gp_pf_stats[3]);
    /* [6] */
    int nm = 48, caps[] = {200, 400, 800, 1600};
    pw_query *mq = malloc(sizeof *mq * nm);
    pw_moveaways(w, mq, nm, 5);
    pw_patch(1);
    printf("[6] move-away floods from inside / at the edge of the packed block (%d units), footprint 1/3/4/9 "
           "cells, uncapped:\n", units / 4);
    int need[4][64], nn[4] = {0}; double tm[4] = {0}, tmax[4] = {0}; int pmax[4] = {0};
    for (int i = 0; i < nm; i++) {
        pw_result r; double t = run(w, &mq[i], &r); int m = mq[i].mover;
        need[m][nn[m]++] = r.found ? r.steps : 1 << 30;
        tm[m] += t; if (t > tmax[m]) { tmax[m] = t; pmax[m] = r.steps; }
    }
    for (int m = 0; m < 4; m++) {
        printf("    footprint %d: %2d floods, mean %.2f ms, slowest %.2f ms (%d cells); cells to a free spot:",
               (int[]){1, 3, 4, 9}[m] , nn[m], tm[m] / nn[m] / 1000, tmax[m] / 1000, pmax[m]);
        for (int i = 0; i < nn[m]; i++) printf(need[m][i] < (1 << 30) ? " %d" : " none", need[m][i]);
        printf("\n");
    }
    pw_moveaway_pop = (void *)gp_pf_ma_pop;
    for (unsigned c = 0; c < sizeof caps / sizeof caps[0]; c++) {
        gp_pf_macap = caps[c];
        int okc = 0, agree = 0; double worst = 0;
        for (int i = 0; i < nm; i++) {
            pw_result r, r2; double t = run(w, &mq[i], &r); if (t > worst) worst = t;
            int m = mq[i].mover, k = 0; for (int j = 0; j < i; j++) k += mq[j].mover == m;
            okc += r.found; agree += r.found == (need[m][k] <= caps[c]);
            pw_search(w, &mq[i], &r2); agree -= !same(&r, &r2);
        }
        printf("    cap %4d cells: %2d of %d find a spot (%d as predicted by the uncapped runs, repeated runs "
               "identical), slowest %.2f ms\n", caps[c], okc, nm, agree, worst / 1000);
        fails += agree != nm;
    }
    pw_moveaway_pop = NULL; gp_pf_macap = 800;

    /* [7] */
    int r7 = pw_maq_test(w);
    printf("[7] moveawayqueue: %s\n", r7 ? "the expected orders at the expected queue runs, twice, identical" : "WRONG");
    fails += !r7;
    printf("%s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
