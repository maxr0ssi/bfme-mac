/* t_path [8]: pathsplit (p_path3.c) on the synthetic world. Requests are served the way the patched
 * queue serves them: a run starts (cell count 0), the parked request is resumed, then new requests
 * go on the fiber while the run's count is under 4000 and the fiber's pops under the budget. Each
 * request first sets the pathfinder state a findPath sets at its start (via points, corridor flags,
 * ignored obstacle), as the game's does. Between runs other searches run on the main stack (short
 * searches, move-away floods) and the pathfinder state a search reads is scrambled, as the game's
 * AI updates and other searches may leave it. Checks:
 *   - every request gives the same result as without splitting (popped-cell sequence, path, cost,
 *     cells, final lists), with via points empty and set, in two worlds with different memory
 *     layouts, and the same per-run pop counts in both;
 *   - no run pops more than the budget on the fiber;
 *   - a parked request whose unit is gone, whose request was cancelled, or that a map reset ends
 *     is dropped with clean lists; one whose unit asked again is finished and stays waiting; one
 *     parked inside the approach branch or a search for another unit is not split;
 *   - time per run without and with splitting, packed-horde searches among ordinary ones. */
#include "orig.h"
#include "gp_logic.h"
#include "t_path.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern uint32_t OFF;
typedef struct { pw_t *w; pw_query q; pw_result r; int other, start, end; } req_t;
static int cur_run;

static int nvia;                         /* via points of every request (baseline) */
static uint8_t viabuf[12 * 64];
static uint32_t lrng = 12345;
static uint32_t lr(void) { lrng ^= lrng << 13; lrng ^= lrng >> 17; lrng ^= lrng << 5; return lrng; }

static uint8_t *zone(uint8_t *pf, int i)   /* the corridor flag of zone block i */
{
    int rows = I32(pf, 0x1be98 + 8);
    return PTR(PTR(pf, 0x1be98), 4 * (i / rows)) + 0x44 * (i % rows) + 0x34;
}
static int nzones(uint8_t *pf) { return I32(pf, 0x1be98 + 4) * I32(pf, 0x1be98 + 8); }

static void baseline(pw_t *w)            /* what findPath sets at its start */
{
    uint8_t *pf = pw_pf(w);
    for (int i = 0; i < nzones(pf); i++) *zone(pf, i) = 1;
    U32(pf, 0x1c1cc) = U32(pf, 0x1c1d0) = (uint32_t)(uintptr_t)viabuf;
    U32(pf, 0x1c1d4) = (uint32_t)(uintptr_t)(viabuf + sizeof viabuf);
    for (int i = 0; i < nvia; i++) {
        int x, y; pw_center(w, i % 3, &x, &y);
        I32(viabuf, 12 * i) = 0; I32(viabuf, 12 * i + 4) = x; I32(viabuf, 12 * i + 8) = y;
    }
    U32(pf, 0x1c1d0) += 12 * nvia;
    U32(pf, 0x48) = 0xffff;
}

static void req_run(void *ctx)
{
    req_t *r = ctx;
    if (r->other >= 0) {                 /* a search for another unit first, on the same fiber */
        pw_query q = r->q; pw_result x;
        q.mover = r->other; baseline(r->w); pw_search(r->w, &q, &x);
    }
    baseline(r->w);
    pw_search(r->w, &r->q, &r->r);
    r->end = cur_run;
}
static uint8_t *split_pop(uint8_t *pf, uint8_t *obj, uint8_t *goal) { return gp_ps_pop_ctx(pf, obj, goal, NULL); }

/* findObjectByID stand-in: the movers (IDs 50-53) unless one is hidden */
static pw_t *bw;
static int hidden = -1;
static uint8_t *TC s_byid(void *logic, uint32_t id)
{
    (void)logic;
    int m = (int)id - 50;
    return m >= 0 && m < 4 && m != hidden ? pw_mover(bw, m) : NULL;
}
static void jmp_at(uint32_t va, void *target)
{
    uint8_t *p = (uint8_t *)(uintptr_t)(va + OFF);
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)target - (va + OFF + 5));
    p[0] = 0xe9; memcpy(p + 1, &rel, 4);
}

/* between two runs: other searches on the main stack, the state a search reads scrambled */
static pw_query side[64];
static int nside, scramble = 1;
static void between(pw_t *w, int run)
{
    uint8_t *pf = pw_pf(w);
    if (nside) {
        pw_result x;
        baseline(w);
        pw_search(w, &side[run % nside], &x);
    }
    if (!scramble) return;
    for (int i = 0; i < nzones(pf); i++) *zone(pf, i) = lr() & 1;
    int n = (int)(lr() % 60);
    for (int i = 0; i < 3 * n; i++) I32(viabuf, 4 * i) = (int)(lr() % 400);
    U32(pf, 0x1c1d0) = U32(pf, 0x1c1cc) + 12 * n;
    *(uint32_t *)(uintptr_t)0xde4b14 = lr() & 1 ? 0 : 30000;      /* over MaxCellsToExamineTowardsGoal */
    U8(pf, 0x38) = lr() & 1;
    U32(pf, 0x48) = lr();
}

typedef struct { int runs, parks; LONG maxpops, sumpops; double maxms, summs, wait; LONG pops[2048]; } qstat;

/* serve rq[0..n) the way the queue does; split 0: the original (whole requests) */
static void queue(pw_t *w, req_t *rq, int n, int split, int disturb, qstat *st)
{
    uint8_t *pf = pw_pf(w);
    int i = 0;
    LONG parks0 = gp_ps_stats[1];
    memset(st, 0, sizeof *st);
    pw_split_pop = split ? split_pop : NULL;
    while (i < n || gp_ps_parked()) {
        I32(pf, 0x3c) = 0;
        U32(pf, 0x1c1e0 + 0x800) = U32(pf, 0x1c1e0 + 0x804) = 0;   /* the game's queue would pop the units back */
        LONG p0 = gp_ps_pops;
        uint64_t s0 = pw_scan_us, t0 = now_us();
        cur_run = st->runs;
        if (split) { gp_ps_runstart(pf, 0); gp_ps_resume(pf); }
        while (i < n && I32(pf, 0x3c) < 4000) {
            req_t *r = &rq[i++];
            uint8_t *obj = pw_mover(w, r->q.mover);
            r->start = cur_run = st->runs;
            if (!split) req_run(r);
            else if (gp_ps_serve_fn(pf, obj, PTR(obj, 0x260), req_run, r)) I32(pf, 0x3c) = 0x40000000;
        }
        double ms = (double)(now_us() - t0 - (pw_scan_us - s0)) / 1000;
        LONG p = gp_ps_pops - p0;
        if (st->runs < 2048) st->pops[st->runs] = p;
        if (p > st->maxpops) st->maxpops = p;
        st->sumpops += p;
        if (ms > st->maxms) st->maxms = ms;
        st->summs += ms;
        st->runs++;
        if (disturb) between(w, st->runs);
    }
    st->parks = (int)(gp_ps_stats[1] - parks0);
    for (int k = 0; k < n; k++) st->wait += (double)(rq[k].end + 1) / n;   /* runs until each path is there */
    pw_split_pop = NULL;
}

static int same(const pw_result *a, const pw_result *b)
{
    return a->found == b->found && a->steps == b->steps && a->cells == b->cells && a->pathlen == b->pathlen &&
           a->cost == b->cost && a->pops == b->pops && a->path == b->path && a->lists == b->lists;
}

static int lists_clean(pw_t *w)          /* nothing open or closed anywhere */
{
    uint8_t *pf = pw_pf(w);
    if (U32(pf, 0x34) || U32(pf, 0x1d1f0) != U32(pf, 0x1d1f4)) return 0;
    for (int x = 0; x <= I32(pf, 0x1c); x++)
        for (int y = 0; y <= I32(pf, 0x20); y++) {
            uint8_t *in = PTR(PTR(PTR(pf, 0x10), 4 * x) + 16 * y, 0);
            if (in && (U32(in, 0x2c) & 0x18)) return 0;
        }
    return 1;
}

static void make_requests(pw_t *w, req_t *rq, int nq, int nh)
{
    pw_query q[256];
    pw_queries(w, q, nq, 99);
    int bx, by, gx, gy;
    pw_center(w, 0, &bx, &by); pw_center(w, 3, &gx, &gy);
    for (int i = 0; i < nq + nh; i++) {
        rq[i].w = w; rq[i].other = -1;
        if (i < nq) rq[i].q = q[i];
        else rq[i].q = (pw_query){bx - 8 + (int)(lr() % 17), by - 8 + (int)(lr() % 17), gx, gy, 3, 0, 5000, 0};
        if (rq[i].q.limit > 5000) rq[i].q.limit = 5000;       /* the group pack's MaxCellsFindPathLimit */
    }
}

/* ---- the asm entries the game calls (pop sites, run start, resume point, reset, approach marker,
 * request call), driven with stand-in frames: each passes the right frame fields and registers ---- */
void gp_ps_popA(void), gp_ps_popB(void), gp_ps_runstart_stub(void), gp_ps_resume_stub(void);
void gp_ps_reset_stub(void), gp_ps_approach_stub(void);
void TC gp_ps_serve(uint8_t *ai, uint8_t *pf);
extern uint32_t gp_ps_loop, gp_ps_exit, gp_ps_reset_cont, gp_ps_approach, gp_ps_ai_ret;
volatile int t_which;
void t_loop(void), t_exit(void), t_reset_cont(void);
__asm__(".text\n.globl _t_loop\n_t_loop: movl $1, _t_which\n ret\n.globl _t_exit\n_t_exit: movl $2, _t_which\n ret\n"
        ".globl _t_reset_cont\n_t_reset_cont: popl %esi\n popl %ebp\n popl %ebx\n popl %ecx\n movl $3, _t_which\n ret\n");

static uint8_t *cellp(uint8_t *pf, int x, int y) { return PTR(PTR(pf, 0x10), 4 * x) + 16 * y; }
static uint8_t xpat[128] __attribute__((aligned(16))), xgot[128] __attribute__((aligned(16)));
static int xbad;
uint8_t *xpat_p = xpat, *xgot_p = xgot;
static uint8_t *call_pop(void *stub, uint8_t *pf, uint8_t *frame)   /* xmm0-7 must come back unchanged */
{
    uint8_t *r;
    for (int i = 0; i < 128; i++) xpat[i] = (uint8_t)(i * 7 + 3);
    __asm__ volatile("movdqa _xpat, %%xmm0\n\tmovdqa _xpat+16, %%xmm1\n\tmovdqa _xpat+32, %%xmm2\n\t"
                     "movdqa _xpat+48, %%xmm3\n\tmovdqa _xpat+64, %%xmm4\n\tmovdqa _xpat+80, %%xmm5\n\t"
                     "movdqa _xpat+96, %%xmm6\n\tmovdqa _xpat+112, %%xmm7\n\t"
                     "pushl %%ebp\n\tmovl %%esi, %%ebp\n\tcall *%%edi\n\tpopl %%ebp\n\t"
                     "movdqa %%xmm0, _xgot\n\tmovdqa %%xmm1, _xgot+16\n\tmovdqa %%xmm2, _xgot+32\n\t"
                     "movdqa %%xmm3, _xgot+48\n\tmovdqa %%xmm4, _xgot+64\n\tmovdqa %%xmm5, _xgot+80\n\t"
                     "movdqa %%xmm6, _xgot+96\n\tmovdqa %%xmm7, _xgot+112"
                     : "=a"(r), "+c"(pf) : "S"(frame), "D"(stub)
                     : "edx", "memory", "cc", "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7");
    xbad += memcmp(xpat, xgot, 128) != 0;
    return r;
}
typedef struct { pw_t *w; void *stub; uint8_t *frame, *goal; int n; uint32_t seq[64]; } fs_t;
typedef void (TC *alloc_t)(void *cell, const int *pos);
typedef void (TC *cpush_t)(void *pf, void *cell);
typedef void (TC *cclose_t)(void *cell, void *head);
typedef void (TC *cclean_t)(void *pf);
#define TFN(t, va) ((t)(uintptr_t)((va) + OFF))
static void fake_search(void *ctx)        /* 40 cells on the open list, popped through a pop site's stub */
{
    fs_t *f = ctx;
    uint8_t *pf = pw_pf(f->w);
    int gpos[2] = {150, 150};
    TFN(alloc_t, 0x6ea019)(f->goal, gpos);
    for (int i = 0; i < 40; i++) {
        uint8_t *c = cellp(pf, 100 + i, 100);
        int pos[2] = {100 + i, 100};
        TFN(alloc_t, 0x6ea019)(c, pos);
        U32(PTR(c, 0), 0x10) = (uint32_t)((i * 37) % 101);
        TFN(cpush_t, 0x6f57a1)(pf, c);
    }
    f->n = 0;
    for (uint8_t *c; (c = call_pop(f->stub, pf, f->frame)); ) {
        if (f->n < 64) f->seq[f->n++] = (uint32_t)(uintptr_t)c;
        TFN(cclose_t, 0x934594)(c, pf + 0x34);
    }
    TFN(cclean_t, 0x6f5519)(pf);
}
static int appr_seen[5];
static int TC t_appr(void *ai, int a, int b, int c)
{
    appr_seen[0] = (int)(uintptr_t)ai; appr_seen[1] = a; appr_seen[2] = b; appr_seen[3] = c; appr_seen[4] = gp_ps_unsafe;
    return 77;
}
static void *dopf_fiber; static uint8_t *dopf_pf;
static void TC t_dopf(uint8_t *ai, uint8_t *pf) { (void)ai; dopf_fiber = GetCurrentFiber(); dopf_pf = pf; }

static int chk(int id, int c) { if (!c) printf("      check %d failed\n", id); return c; }
static int stub_test(pw_t *w)
{
    uint8_t *pf = pw_pf(w), *obj = pw_mover(w, 1);
    uint32_t fa[64] = {0}, fb[64] = {0};
    uint8_t *ea = (uint8_t *)fa + 0x20, *eb = (uint8_t *)fb + 0x80, *goal = cellp(pf, 150, 150);
    U32(ea, 0x68) = U32(eb, 8) = (uint32_t)(uintptr_t)obj;
    U32(ea, 0x58) = U32(eb, -0x34) = (uint32_t)(uintptr_t)goal;
    int ok = 1;
    for (int site = 0; site < 2; site++) {               /* the two pop stubs: same pops whole and parked */
        fs_t ref = {w, site ? (void *)gp_ps_popB : (void *)gp_ps_popA, site ? eb : ea, goal, 0, {0}}, f = ref;
        fake_search(&ref);
        gp_ps_budget = 5;
        LONG parks0 = gp_ps_stats[1];
        I32(pf, 0x3c) = 0; gp_ps_runstart(pf, 0);
        gp_ps_serve_fn(pf, obj, NULL, fake_search, &f);
        int goal_back = 1;
        while (gp_ps_parked()) {
            if (PTR(goal, 0)) { typedef void (TC *rel_t)(void *); TFN(rel_t, 0x9347c6)(goal); }   /* a unit leaves */
            I32(pf, 0x3c) = 0; gp_ps_runstart(pf, 0); gp_ps_resume(pf);
            goal_back &= PTR(goal, 0) != NULL;
        }
        ok &= chk(9, xbad == 0);
        ok &= chk(1, f.n == ref.n && f.n == 40 && !memcmp(f.seq, ref.seq, 4 * 40) && gp_ps_stats[1] - parks0 == 8 && goal_back);
    }
    /* the run-start stub: registers kept, the counts cleared, phase 5's second run shares the budget */
    fs_t f = {w, (void *)gp_ps_popA, ea, goal, 0, {0}};
    I32(pf, 0x3c) = 0; gp_ps_runstart(pf, 0);
    gp_ps_serve_fn(pf, obj, NULL, fake_search, &f);    /* parked after 5 pops */
    uint32_t fr[4] = {0, gp_ps_ai_ret, 0, 0}, a = 0x11111111, c = 0, d = 0x33333333;
    I32(pf, 0x3c) = I32(pf, 0x40) = I32(pf, 0x44) = 7;
    __asm__ volatile("pushl %%ebp\n\tmovl %%esi, %%ebp\n\tcall _gp_ps_runstart_stub\n\tpopl %%ebp"
                     : "+a"(a), "+c"(c), "+d"(d) : "b"(pf), "S"(fr) : "memory", "cc");
    ok &= chk(2, a == 0x11111111 && c == 0 && d == 0x33333333 && !I32(pf, 0x3c) && !I32(pf, 0x40) && !I32(pf, 0x44));
    LONG p0 = gp_ps_pops;
    /* the resume stub: resumes (no pops left in this phase: parked again at once), then the loop's test */
    gp_ps_loop = (uint32_t)(uintptr_t)t_loop; gp_ps_exit = (uint32_t)(uintptr_t)t_exit;
    t_which = 0;
    __asm__ volatile("call _gp_ps_resume_stub" : : "b"(pf), "S"(100) : "eax", "ecx", "edx", "memory", "cc");
    ok &= chk(3, gp_ps_pops == p0 && gp_ps_parked() && t_which == 2);          /* run over: the queue loop is skipped */
    fr[1] = 0;
    __asm__ volatile("pushl %%ebp\n\tmovl %%esi, %%ebp\n\tcall _gp_ps_runstart_stub\n\tpopl %%ebp"
                     : "+a"(a), "+c"(c), "+d"(d) : "b"(pf), "S"(fr) : "memory", "cc");
    __asm__ volatile("call _gp_ps_resume_stub" : : "b"(pf), "S"(100) : "eax", "ecx", "edx", "memory", "cc");
    ok &= chk(4, gp_ps_pops - p0 == 5 && gp_ps_parked() && t_which == 2);
    /* the reset stub drops it and runs the original's first instructions */
    gp_ps_reset_cont = (uint32_t)(uintptr_t)t_reset_cont;
    t_which = 0;
    __asm__ volatile("call _gp_ps_reset_stub" : : "c"(pf) : "eax", "edx", "memory", "cc");
    ok &= chk(5, !gp_ps_parked() && t_which == 3 && lists_clean(w));
    I32(pf, 0x3c) = 0; gp_ps_runstart(pf, 0);
    __asm__ volatile("call _gp_ps_resume_stub" : : "b"(pf), "S"(100) : "eax", "ecx", "edx", "memory", "cc");
    ok &= chk(6, t_which == 1);                                                    /* nothing parked: the loop runs */
    /* the approach marker: three arguments through, the marker set inside only */
    gp_ps_approach = (uint32_t)(uintptr_t)t_appr;
    typedef int (TC *appr_t)(void *, int, int, int);
    volatile uintptr_t va = (uintptr_t)gp_ps_approach_stub;
    int rv = ((appr_t)va)((void *)0x1234, 5, 6, 7);
    ok &= chk(7, rv == 77 && appr_seen[0] == 0x1234 && appr_seen[1] == 5 && appr_seen[2] == 6 && appr_seen[3] == 7 &&
          appr_seen[4] == 1 && gp_ps_unsafe == 0);
    /* the request call: the AI's vtable+0x230 runs on the fiber with the pathfinder */
    static uint32_t vt[0x100], fake_ai[0x400];
    vt[0x230 / 4] = (uint32_t)(uintptr_t)t_dopf;
    fake_ai[0] = (uint32_t)(uintptr_t)vt; fake_ai[2] = (uint32_t)(uintptr_t)obj;
    I32(pf, 0x3c) = 0; gp_ps_runstart(pf, 0);
    gp_ps_serve((uint8_t *)fake_ai, pf);
    ok &= chk(8, dopf_fiber && dopf_fiber != GetCurrentFiber() && dopf_pf == pf && I32(pf, 0x3c) == 0);
    gp_ps_budget = 1000;
    printf("    the game-side entries (pop sites A and B, run start, resume point, reset, approach marker, "
           "request call) with stand-in frames: %s\n", ok ? "as expected" : "WRONG");
    return ok;
}

int pw_split_test(const pw_cfg *cfg0, int nq)
{
    int fails = 0, nh = 8, n = nq + nh;
    req_t *ref = calloc(n, sizeof *ref), *rq = calloc(n, sizeof *rq);
    pw_cfg cfg = *cfg0;
    LONG pops_a[2][2048]; int runs_a[2] = {0, 0};
    uint64_t hres[2] = {0, 0};
    for (int lay = 0; lay < 2; lay++) {
        cfg.salt = lay ? 77 : 0;
        pw_t *w = pw_build(&cfg);
        bw = w;
        jmp_at(0x449681, (void *)s_byid);
        lrng = 12345;
        make_requests(w, ref, nq, nh);
        pw_moveaways(w, side, 16, 5);
        for (int i = 16; i < 32; i++) {                  /* short searches near the battles */
            int x, y; pw_center(w, i % 3, &x, &y);
            side[i] = (pw_query){x - 20 + (int)(lr() % 9), y - 20, x + 20, y + 20 - (int)(lr() % 9), (int)(lr() % 4), 0, 600, 0};
        }
        nside = 32;
        for (int v = 0; v < 2; v++) {
            nvia = v ? 2 : 0;
            qstat st0, st;
            memcpy(rq, ref, sizeof *rq * n);
            queue(w, ref, n, 0, 0, &st0);
            static const uint32_t budgets[3] = {500, 1000, 2000};
            for (int b = 0; b < 3; b++) {
                gp_ps_budget = budgets[b];
                req_t *t = calloc(n, sizeof *t);
                memcpy(t, rq, sizeof *t * n);
                queue(w, t, n, 1, 1, &st);
                int bad = 0;
                for (int i = 0; i < n; i++) bad += !same(&t[i].r, &ref[i].r);
                int over = st.maxpops > (LONG)budgets[b];
                if (b == 1 && v == 1) {
                    runs_a[lay] = st.runs; memcpy(pops_a[lay], st.pops, sizeof st.pops);
                    for (int i = 0; i < n; i++) hres[lay] = (hres[lay] ^ t[i].r.pops ^ t[i].r.path * 3 ^ t[i].r.lists * 5 ^
                                                            (uint64_t)t[i].r.cost << 7) * 0x100000001b3ull;
                }
                printf("    layout %d, via points %d, budget %4u: %d runs (%d without splitting), %d parks, most pops "
                       "in a run %ld; %d of %d results differ\n", lay, nvia, budgets[b], st.runs, st0.runs, st.parks,
                       st.maxpops, bad, n);
                fails += bad != 0 || over || st.parks == 0 || !lists_clean(w);
                free(t);
            }
        }
        if (lay) { pw_free(w); continue; }

        /* drops, a repeated request, the approach branch, another unit's search */
        nvia = 0; gp_ps_budget = 300;
        req_t one[2]; qstat st;
        queue(w, ref, n, 0, 0, &st);                     /* the references again, without via points */
        uint8_t *pf = pw_pf(w), *obj = pw_mover(w, 3), *ai = PTR(obj, 0x260);
        const char *what[4] = {"unit gone", "request cancelled", "map reset", "asked again"};
        for (int k = 0; k < 4; k++) {
            one[0] = ref[n - 1]; one[0].r = (pw_result){0};
            LONG d0 = gp_ps_stats[3] + gp_ps_stats[4] + gp_ps_stats[11], a0 = gp_ps_stats[5];
            pw_split_pop = split_pop;
            uint8_t *qq = pf + 0x1c1e0;
            U32(qq, 0x800) = U32(qq, 0x804) = 0;
            I32(pf, 0x3c) = 0; gp_ps_runstart(pf, 0);
            gp_ps_serve_fn(pf, obj, ai, req_run, &one[0]);
            int parked = gp_ps_parked(), wait = U8(ai, 0x3b1) == 1 && U32(qq, 4 * U32(qq, 0x800)) == U32(obj, 0x74) &&
                         U32(qq, 0x800) != U32(qq, 0x804);   /* waiting again, back at the queue's head */
            between(w, k);
            if (k == 0) hidden = 3;
            if (k == 1) U8(ai, 0x3b1) = 0;
            if (k == 2) gp_ps_drop();
            if (k == 3) I32(ai, 0x148) += 1;
            while (gp_ps_parked()) { I32(pf, 0x3c) = 0; gp_ps_runstart(pf, 0); gp_ps_resume(pf); }
            hidden = -1;
            pw_split_pop = NULL;
            int ok = parked && wait;
            if (k < 3) ok &= gp_ps_stats[3] + gp_ps_stats[4] + gp_ps_stats[11] == d0 + 1 && lists_clean(w);
            else ok &= gp_ps_stats[5] == a0 + 1 && same(&one[0].r, &ref[n - 1].r) && U8(ai, 0x3b1) == 1;
            U8(ai, 0x3b1) = 0; I32(ai, 0x148) = 0;
            one[1] = ref[n - 1];                         /* the next request is unaffected */
            queue(w, &one[1], 1, 1, 0, &st);
            ok &= same(&one[1].r, &ref[n - 1].r) && U8(ai, 0x3b1) == 0;
            printf("    %-17s: %s\n", what[k], ok ? "dropped / finished as expected, lists clean, the next request identical" : "WRONG");
            if (!ok) printf("      parked %d wait %d drops %ld again %ld clean %d same %d/%d\n", parked, wait,
                            gp_ps_stats[3] + gp_ps_stats[4] + gp_ps_stats[11] - d0, gp_ps_stats[5] - a0, lists_clean(w),
                            same(&one[0].r, &ref[n - 1].r), same(&one[1].r, &ref[n - 1].r));
            fails += !ok;
        }
        one[0] = ref[n - 1];
        gp_ps_unsafe = 1;                                /* as inside doPathfind's approach branch */
        queue(w, one, 1, 1, 0, &st);
        gp_ps_unsafe = 0;
        int ok = st.parks == 0 && same(&one[0].r, &ref[n - 1].r);
        one[0] = ref[n - 1]; one[0].other = 2;           /* another unit's search on the fiber first */
        queue(w, one, 1, 1, 1, &st);
        ok &= st.parks >= 1 && same(&one[0].r, &ref[n - 1].r) && st.pops[0] > 300;
        printf("    approach branch, another unit's search: %s (another unit's search: %ld pops in its run)\n",
               ok ? "not split, results identical" : "WRONG", st.pops[0]);
        fails += !ok;

        /* time per run: the original queue against splitting, packed-horde searches among the others */
        LONG hs = 0, hc = 0;
        for (int i = nq; i < n; i++) { hs += ref[i].r.steps; hc += ref[i].r.cells; }
        printf("    ms per queue run (searches only), %d requests of which %d are horde searches from inside "
               "the packed block to the closed base (limit 5000: %ld pops, %ld cells on average):\n", n, nh, hs / nh, hc / nh);
        for (int b = 0; b < 4; b++) {
            static const uint32_t budgets[4] = {0, 500, 1000, 2000};
            gp_ps_budget = budgets[b];
            double worst = 0, sum = 0, wait = 0; int runs = 0; LONG mp = 0, sp = 0;
            for (int rep = 0; rep < 3; rep++) {
                memcpy(rq, ref, sizeof *rq * n);
                queue(w, rq, n, b > 0, 0, &st);
                if (rep == 0 || st.maxms < worst) worst = st.maxms;   /* the least disturbed of 3 */
                sum += st.summs; runs = st.runs; mp = st.maxpops; sp = st.sumpops; wait = st.wait;
            }
            printf("      %-19s %3d runs, pops per run %4ld mean %5ld most, slowest run %6.2f ms, mean %5.2f ms; "
                   "a path is ready after %5.1f runs on average\n",
                   b ? (budgets[b] == 500 ? "split, budget 500" : budgets[b] == 1000 ? "split, budget 1000" : "split, budget 2000")
                     : "whole (as EA)", runs, sp / runs, mp, worst, sum / 3 / runs, wait);
        }
        fails += !stub_test(w);
        pw_free(w);
    }
    int det = runs_a[0] == runs_a[1] && !memcmp(pops_a[0], pops_a[1], sizeof(LONG) * (runs_a[0] < 2048 ? runs_a[0] : 2048))
              && hres[0] == hres[1];
    printf("    results and per-run pop counts in the two memory layouts: %s\n", det ? "identical" : "DIFFER");
    fails += !det;
    gp_ps_budget = 1000;
    free(ref); free(rq);
    return fails == 0;
}
