/* pathsplit: the pathfind queue's long searches split over queue runs (docs/PERFORMANCE.md §21).
 *
 * The pathfind queue (0x6f2364, at the top of every logic phase) serves requests while its cell
 * count is under MaxPathfindCellsPerFrame, but a request's cells are counted only when its search
 * ends, so one search runs to its own end in one phase: a failing horde search of 5000 cells costs
 * 0.1-0.2 s in one frame. Here every request (AIUpdateInterface::doPathfind, vt+0x230, called at
 * 0x6f2570) runs on a fiber. The unit's own big searches, findPath's cell search (0x6fd06f) and
 * findClosestPath (0x6fb869), take their pops from here (0x6fd9a1, 0x6fdc0c, 0x6fbdb3, 0x6fc060):
 * once the fiber has popped gp_ps_budget cells in this queue run (every search's pops count, 0x6f4af2
 * entry; phase 5's second run, from TheAI's update, shares the phase's count), the search is parked
 * and the run ends. The next run resumes it before serving anything
 * else (after the queue's priority list, at 0x6f24de), so one request at most is in flight.
 *
 * Parked means the pathfinder looks as if no search were running, so the searches the AI makes
 * outside the queue meanwhile (and the move-away floods) find clean lists, and the parked search
 * gets its own state back exactly:
 *   - open heap (pf+0x1d1f0) and closed list (pf+0x34) emptied; each cell's search fields (parent as
 *     a cell, +0xc, costs, flag bits 0/3/4) saved by cell. Closed infos are released the way the
 *     game's clean-up does (0x934806), open ones stay on their cells as the game leaves them;
 *   - saved: start-blocked flag (pf+0x38), ignored obstacle (pf+0x48, set to 0 as doPathfind leaves
 *     it), jump-ahead counter (0xde4b14), via points (pf+0x1c1cc), the zone blocks' corridor flags;
 *   - the unit's waiting-for-path flag (ai+0x3b1, cleared by doPathfind) is set again and its ID put
 *     back at the queue's head: its AI and a saved game see what they saw while it was queued (once
 *     the request is done, that entry finds the flag cleared and costs nothing; a request the unit
 *     makes meanwhile is served by it).
 * Resuming puts it all back by cell (a cell whose info was released meanwhile gets a new one; the
 * goal cell's info too) and restarts the pathfind patch's memo (units have moved). Before that: if
 * the unit is gone (its ID no longer gives the same object) or its request was cancelled (the
 * waiting flag cleared, as destroyPath does), the parked request is dropped, as the game drops a
 * queued request whose unit no longer waits (fiber deleted, hierarchical path released). If the
 * unit asked for another path meanwhile (its request fields changed) the old request finishes and
 * the new one stays queued; otherwise the flag is cleared again as doPathfind left it.
 * Parking is allowed only where every object the fiber's frames hold is the unit: not inside the
 * approach/attack branch (0x6668ca, which keeps the victim pointer), never in searches for other
 * units (move-away floods), attack paths or path patches; those run to their end and count.
 * Counted in popped cells and queue runs, never time: every machine running this build parks and
 * resumes at the same cells, so LAN games stay in step (every player needs the same setting). */
#include "gp_logic.h"
#include <stdlib.h>
#include <string.h>

#define TC __attribute__((thiscall))
#define FA __attribute__((force_align_arg_pointer))
#define U8(p, o)  (*(uint8_t *)((uint8_t *)(p) + (o)))
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define I32(p, o) (*(int32_t *)((uint8_t *)(p) + (o)))
#define PTR(p, o) ((uint8_t *)(uintptr_t)U32(p, o))
#define GFN(t, va) ((t)(uintptr_t)((va) + ps_off))
#define DAT(va) (*(uint32_t *)(uintptr_t)(va))              /* .data is not relocated in the tests */

#define PF_CELLS   0x3c        /* the queue run's cell count */
#define PF_CLOSED  0x34
#define PF_BLOCKED 0x38
#define PF_IGNORE  0x48
#define PF_VIA     0x1c1cc     /* vector of 12-byte via points: begin, end, capacity */
#define PF_QUEUE   0x1c1e0
#define PF_OPEN    0x1d1f0     /* vector of cell pointers (a binary heap): begin, end, capacity */
#define PF_ZONES   0x1be98     /* 0x460 + 0x1ba38: column pointers, columns, rows; 0x44-byte blocks */
#define AI_WAIT    0x3b1
#define JUMP_CTR   0xde4b14
#define FL_SEARCH  0x19        /* info flag bits a search owns: 0, open 0x8, closed 0x10 */

typedef uint8_t *(TC *pop_t)(void *pf);                       /* 0x6f4af2 */
typedef void (TC *alloc_t)(void *cell, const int *pos);       /* 0x6ea019 */
typedef void (TC *close_t)(void *cell, void *head);           /* 0x934594 */
typedef void (TC *unlink_t)(void *info);                      /* 0x6e8074 */
typedef void (TC *release_t)(void *cell);                     /* 0x9347c6 */
typedef void (TC *pushb_t)(void *vec, void *const *v);         /* 0x90be00 vector push_back */
typedef uint8_t (TC *has_t)(void *queue, const uint32_t *id); /* 0x6ec096 */
typedef uint8_t *(TC *byid_t)(void *logic, uint32_t id);      /* 0x449681 */
typedef void (TC *own_t)(void *holder);                       /* 0x6ec1b7 owner pointer: delete */
typedef void (TC *dopf_t)(void *ai, void *pf);                /* doPathfind, vt+0x230 */

uint32_t gp_ps_budget = 1000;          /* popped cells per queue run for the fiber's work */
volatile LONG gp_ps_pops;              /* every pop of every search (0x6f4af2 entry) */
volatile LONG gp_ps_stats[14];
uint32_t gp_ps_pop_cont, gp_ps_loop, gp_ps_exit, gp_ps_reset_cont, gp_ps_approach, gp_ps_ai_ret = 1;
volatile LONG gp_ps_unsafe;            /* > 0 inside doPathfind's approach/attack branch */
volatile uint32_t gp_ps_stack_top;     /* the fiber's stack base (p_stall.c samples it too), 0: none */
static uint32_t ps_off;

enum { J_NONE, J_RUN, J_PARKED, J_DONE };
static struct {
    int state;
    uint8_t *pf, *ai, *obj, *goal, *hp;
    uint32_t id; int gx, gy, runs;
    void (*run)(void *); void *ctx;
    uint8_t marked, queued, req[0x20]; /* we set the waiting flag; we queued the unit; request fields */
} job;

static LPVOID f_main, f_work;
static DWORD f_thread;
static int in_work, broken;
static LONG run_pops, sw_c0;           /* fiber pops in this run; gp_ps_pops when the fiber was entered */
static uint32_t run_budget;

typedef struct { uint8_t *cell, *par; uint32_t c, cost, fl; int32_t x, y; } ent_t;
static ent_t *eo, *ec;                 /* parked open (heap order) and closed (list order) cells */
static uint32_t no, nc, cap_o, cap_c;
static uint8_t s_blocked, *via, *pass;
static uint32_t s_ignore, s_jump, nvia, cap_via, npass, cap_pass, s_zcols, s_zw, s_zh;

static void *grow(void *p, uint32_t *cap, uint32_t need, uint32_t size)
{
    if (need <= *cap) return p;
    uint32_t n = *cap ? *cap : 1024;
    while (n < need) n *= 2;
    void *q = realloc(p, (size_t)n * size);
    if (!q) abort();                   /* the alternative would be a different search on this machine */
    *cap = n;
    return q;
}

static LONG used(void) { return run_pops + (in_work ? gp_ps_pops - sw_c0 : 0); }

static ent_t save(uint8_t *cell, uint8_t *in)
{
    ent_t e = {cell, NULL, U32(in, 0xc), U32(in, 0x10), U32(in, 0x2c) & FL_SEARCH, I32(in, 0), I32(in, 4)};
    if (U32(in, 8)) e.par = PTR(PTR(in, 8), 0x30);           /* parent info -> its cell */
    return e;
}

static void req_fields(uint8_t *ai, uint8_t *out)             /* destination, victim, kind flags */
{
    memcpy(out, ai + 0x144, 0x14); memcpy(out + 0x14, ai + 0x3b2, 4); memcpy(out + 0x18, ai + 0x18c, 8);
}

static void park(uint8_t *pf)
{
    uint8_t *in;
    s_blocked = U8(pf, PF_BLOCKED); s_ignore = U32(pf, PF_IGNORE); s_jump = DAT(JUMP_CTR);
    nvia = (U32(pf, PF_VIA + 4) - U32(pf, PF_VIA)) / 12;
    via = grow(via, &cap_via, nvia + 1, 12);
    memcpy(via, PTR(pf, PF_VIA), 12 * nvia);
    s_zcols = U32(pf, PF_ZONES); s_zw = U32(pf, PF_ZONES + 4); s_zh = U32(pf, PF_ZONES + 8);
    npass = s_zcols ? s_zw * s_zh : 0;
    pass = grow(pass, &cap_pass, npass + 1, 1);
    for (uint32_t i = 0; i < npass; i++) pass[i] = U8(PTR(s_zcols, 4 * (i / s_zh)), 0x44 * (i % s_zh) + 0x34);
    uint32_t *b = (uint32_t *)PTR(pf, PF_OPEN), *e = (uint32_t *)PTR(pf, PF_OPEN + 4);
    no = (uint32_t)(e - b);
    eo = grow(eo, &cap_o, no + 1, sizeof *eo);
    for (uint32_t i = 0; i < no; i++) {                      /* as 0x6f4b1a: open bit cleared, info kept */
        uint8_t *cell = (uint8_t *)(uintptr_t)b[i];
        in = PTR(cell, 0);
        eo[i] = save(cell, in);
        U32(in, 0x2c) &= ~8u;
    }
    U32(pf, PF_OPEN + 4) = U32(pf, PF_OPEN);
    nc = 0;
    for (in = PTR(pf, PF_CLOSED); in; in = PTR(in, 0x34)) {
        ec = grow(ec, &cap_c, nc + 1, sizeof *ec);
        ec[nc++] = save(PTR(in, 0x30), in);
    }
    for (in = PTR(pf, PF_CLOSED); in; ) {                   /* as 0x934806 */
        uint8_t *next = PTR(in, 0x34), *cell = PTR(in, 0x30);
        GFN(unlink_t, 0x6e8074)(in);
        U32(in, 0x2c) &= ~0x10u;
        if (cell) GFN(release_t, 0x9347c6)(cell);
        in = next;
    }
    U32(pf, PF_CLOSED) = 0;
    U32(pf, PF_IGNORE) = 0;
    if (job.ai) {
        job.marked = !U8(job.ai, AI_WAIT);
        U8(job.ai, AI_WAIT) = 1;
        req_fields(job.ai, job.req);
        uint8_t *q = pf + PF_QUEUE;                          /* the unit back at the queue's head, once */
        uint32_t h = (U32(q, 0x800) + 511) & 511;
        if (!job.queued && job.id && h != U32(q, 0x804)) { U32(q, 4 * h) = job.id; U32(q, 0x800) = h; job.queued = 1; }
    }
    gp_ps_stats[1]++;
}

static uint8_t *ensure(uint8_t *cell, int x, int y)
{
    int pos[2] = {x, y};
    GFN(alloc_t, 0x6ea019)(cell, pos);                       /* existing info: only +0xc cleared */
    return PTR(cell, 0);
}

static void unpark(uint8_t *pf)
{
    U8(pf, PF_BLOCKED) = s_blocked; U32(pf, PF_IGNORE) = s_ignore; DAT(JUMP_CTR) = s_jump;
    if ((U32(pf, PF_VIA + 8) - U32(pf, PF_VIA)) / 12 >= nvia) {
        memcpy(PTR(pf, PF_VIA), via, 12 * nvia);
        U32(pf, PF_VIA + 4) = U32(pf, PF_VIA) + 12 * nvia;
    } else gp_ps_stats[10]++;
    if (U32(pf, PF_ZONES) == s_zcols && U32(pf, PF_ZONES + 4) == s_zw && U32(pf, PF_ZONES + 8) == s_zh) {
        for (uint32_t i = 0; i < npass; i++) U8(PTR(s_zcols, 4 * (i / s_zh)), 0x44 * (i % s_zh) + 0x34) = pass[i];
    } else gp_ps_stats[10]++;
    for (uint32_t i = nc; i-- > 0; ) {                      /* head insertion: the list in its old order */
        uint8_t *in = ensure(ec[i].cell, ec[i].x, ec[i].y);
        if (U32(in, 0x2c) & 0x18 || U32(in, 0x38)) gp_ps_stats[10]++;
        U32(in, 0xc) = ec[i].c; U32(in, 0x10) = ec[i].cost;
        U32(in, 0x2c) = (U32(in, 0x2c) & ~FL_SEARCH) | (ec[i].fl & 1);
        GFN(close_t, 0x934594)(ec[i].cell, pf + PF_CLOSED);
    }
    for (uint32_t i = 0; i < no; i++) {                      /* the heap array exactly as it was */
        uint8_t *in = ensure(eo[i].cell, eo[i].x, eo[i].y);
        if (U32(in, 0x2c) & 0x18 || U32(in, 0x38)) gp_ps_stats[10]++;
        U32(in, 0xc) = eo[i].c; U32(in, 0x10) = eo[i].cost;
        U32(in, 0x2c) = (U32(in, 0x2c) & ~FL_SEARCH) | (eo[i].fl & 9);
        GFN(pushb_t, 0x90be00)(pf + PF_OPEN, (void *const *)&eo[i].cell);
    }
    for (int k = 0; k < 2; k++)
        for (uint32_t i = 0, n = k ? no : nc; i < n; i++) {
            ent_t *e = k ? &eo[i] : &ec[i];
            uint8_t *pin = e->par ? PTR(e->par, 0) : NULL;
            if (e->par && !pin) gp_ps_stats[10]++;
            U32(PTR(e->cell, 0), 8) = (uint32_t)(uintptr_t)pin;
        }
    if (job.goal && !PTR(job.goal, 0)) ensure(job.goal, job.gx, job.gy);
    gp_pf_gen++;                                             /* the pathfind memo starts again */
}

static void enter(void)
{
    in_work = 1; sw_c0 = gp_ps_pops;
    SwitchToFiber(f_work);
    run_pops += gp_ps_pops - sw_c0; in_work = 0;
    if (run_pops > gp_ps_stats[7]) gp_ps_stats[7] = run_pops;
}

static void WINAPI FA fiber_proc(void *unused)
{
    (void)unused;
    gp_ps_stack_top = (uint32_t)(uintptr_t)((NT_TIB *)NtCurrentTeb())->StackBase;   /* for the stall sampler */
    for (;;) {
        job.run(job.ctx);
        job.state = J_DONE;
        SwitchToFiber(f_main);
    }
}

static int ready(void)
{
    if (broken) return 0;
    if (!f_main) {
        typedef BOOL (WINAPI *isf_t)(void);
        isf_t isf = (isf_t)GetProcAddress(GetModuleHandleA("kernel32.dll"), "IsThreadAFiber");
        f_main = isf && isf() ? GetCurrentFiber() : ConvertThreadToFiber(NULL);
        if (!f_main) { broken = 1; gp_log("pathsplit: no fiber for the logic thread (%lu); searches run whole", GetLastError()); return 0; }
        f_thread = GetCurrentThreadId();
    }
    if (GetCurrentThreadId() != f_thread) return 0;
    if (!f_work && !(f_work = CreateFiberEx(64 << 10, 1 << 20, 0, fiber_proc, NULL))) {
        broken = 1; gp_log("pathsplit: CreateFiberEx failed (%lu); searches run whole", GetLastError());
        return 0;
    }
    return 1;
}

/* drop the parked request: cells only while the map still exists */
static void drop(int cells)
{
    if (job.hp) { uint8_t *h = job.hp; GFN(own_t, 0x6ec1b7)(&h); }
    if (cells && job.goal && PTR(job.goal, 0)) GFN(release_t, 0x9347c6)(job.goal);
    gp_ps_stack_top = 0;
    DeleteFiber(f_work); f_work = NULL;
    memset(&job, 0, sizeof job);
    gp_ps_unsafe = 0;
}

/* the start of a queue run (0x6f245a, where the run's cell count is reset). ret: where the queue
 * returns to. TheAI's update runs the queue a second time in phase 5 (0x6fec66); that run shares the
 * phase's budget, so no drawn frame pops more than the budget on the fiber. */
FA void gp_ps_runstart(uint8_t *pf, uint32_t ret)
{
    (void)pf;
    if (ret != gp_ps_ai_ret) run_pops = 0;
    uint8_t *logic = (uint8_t *)(uintptr_t)DAT(0xde412c);
    run_budget = gp_ps_budget;
    if (logic && U32(logic, 0x40) < 5 * DAT(0xd9f608)) run_budget *= 100;   /* as the queue's own budget */
}

/* generic: run(ctx) on the fiber for the unit obj (ai: its AI, or NULL); 1 = the run must end */
int gp_ps_serve_fn(uint8_t *pf, uint8_t *obj, uint8_t *ai, void (*run)(void *), void *ctx)
{
    if (job.state != J_NONE || !ready()) { gp_ps_stats[9]++; run(ctx); return used() >= (LONG)run_budget; }
    memset(&job, 0, sizeof job);
    job.pf = pf; job.obj = obj; job.ai = ai; job.id = obj ? U32(obj, 0x74) : 0;
    job.run = run; job.ctx = ctx; job.state = J_RUN;
    gp_ps_stats[0]++;
    enter();
    if (job.state == J_DONE) { job.state = J_NONE; return used() >= (LONG)run_budget; }
    return 1;
}

static void run_dopf(void *ai)
{
    dopf_t f = *(dopf_t *)(uintptr_t)(U32(ai, 0) + 0x230);
    f(ai, job.pf);
}

/* the queue's request call (0x6f2570: call [vtable+0x230] with the pathfinder) */
void TC FA gp_ps_serve(uint8_t *ai, uint8_t *pf)
{
    if (gp_ps_serve_fn(pf, PTR(ai, 8), ai, run_dopf, ai)) I32(pf, PF_CELLS) = 0x40000000;
}

/* after the queue's priority list (0x6f24de): the parked request goes first */
FA void gp_ps_resume(uint8_t *pf)
{
    if (job.state != J_PARKED) return;
    if (used() >= (LONG)run_budget) { I32(pf, PF_CELLS) = 0x40000000; return; }   /* phase 5's second run */
    uint8_t *logic = (uint8_t *)(uintptr_t)DAT(0xde412c);
    uint8_t *o = job.id ? GFN(byid_t, 0x449681)(logic, job.id) : job.obj;
    if (pf != job.pf || o != job.obj || (job.ai && PTR(o, 0x260) != job.ai)) { gp_ps_stats[3]++; drop(1); return; }
    if (job.ai) {
        uint8_t req[sizeof job.req];
        req_fields(job.ai, req);
        if (!U8(job.ai, AI_WAIT)) { gp_ps_stats[4]++; drop(1); return; }   /* cancelled */
        int again = memcmp(req, job.req, sizeof req) != 0 || (!job.queued && GFN(has_t, 0x6ec096)(pf + PF_QUEUE, &job.id));
        if (again) gp_ps_stats[5]++;
        else if (job.marked) U8(job.ai, AI_WAIT) = 0;
    }
    unpark(pf);
    job.state = J_RUN; job.runs++;
    if (job.runs > gp_ps_stats[6]) gp_ps_stats[6] = job.runs;
    gp_ps_stats[2]++;
    enter();
    if (job.state == J_DONE) { job.state = J_NONE; gp_ps_stats[8]++; }
    if (job.state == J_PARKED || used() >= (LONG)run_budget) I32(pf, PF_CELLS) = 0x40000000;
}

/* a pop of a splittable search; parks the fiber first when this run's budget is spent */
FA uint8_t *gp_ps_pop_ctx(uint8_t *pf, uint8_t *obj, uint8_t *goal, uint8_t *hp)
{
    if (in_work && job.state == J_RUN && obj == job.obj && pf == job.pf && !gp_ps_unsafe &&
        used() >= (LONG)run_budget) {
        uint8_t *gin = goal ? PTR(goal, 0) : NULL;
        job.goal = goal; job.hp = hp;
        job.gx = gin ? I32(gin, 0) : 0; job.gy = gin ? I32(gin, 4) : 0;
        park(pf);
        job.state = J_PARKED;
        SwitchToFiber(f_main);                               /* back here once resumed and unparked */
    }
    return GFN(pop_t, 0x6f4af2)(pf);
}

int gp_ps_parked(void) { return job.state == J_PARKED; }

/* Pathfinder::reset (0x6f5a5e): the map goes, so does a parked request */
FA void gp_ps_drop(void)
{
    if (job.state == J_PARKED) { gp_ps_stats[11]++; drop(0); }
}

/* asm: the pop counter, the four pop sites, the run start, the resume point, the reset hook and the
 * approach branch's marker. The replaced code never touches xmm0-7 (the pop's whole call tree
 * neither), so the stubs that call C keep them, and every register the replaced code keeps. */
#define XSAVE "  subl $128, %esp\n  movdqu %xmm0, (%esp)\n  movdqu %xmm1, 16(%esp)\n  movdqu %xmm2, 32(%esp)\n" \
              "  movdqu %xmm3, 48(%esp)\n  movdqu %xmm4, 64(%esp)\n  movdqu %xmm5, 80(%esp)\n  movdqu %xmm6, 96(%esp)\n" \
              "  movdqu %xmm7, 112(%esp)\n"
#define XLOAD "  movdqu (%esp), %xmm0\n  movdqu 16(%esp), %xmm1\n  movdqu 32(%esp), %xmm2\n  movdqu 48(%esp), %xmm3\n" \
              "  movdqu 64(%esp), %xmm4\n  movdqu 80(%esp), %xmm5\n  movdqu 96(%esp), %xmm6\n  movdqu 112(%esp), %xmm7\n" \
              "  addl $128, %esp\n"
void gp_ps_popcount(void), gp_ps_popA(void), gp_ps_popB(void), gp_ps_runstart_stub(void);
void gp_ps_resume_stub(void), gp_ps_reset_stub(void), gp_ps_approach_stub(void);
__asm__(".text\n"
".globl _gp_ps_popcount\n_gp_ps_popcount:\n"
"  lock incl _gp_ps_pops\n  pushl %esi\n  leal 0x1d1f0(%ecx), %esi\n  jmp *_gp_ps_pop_cont\n"
/* 0x6fd06f: obj [ebp+0x68], goal [ebp+0x58], hierarchical path [ebp+0x78] */
".globl _gp_ps_popA\n_gp_ps_popA:\n" XSAVE
"  pushl 0x78(%ebp)\n  pushl 0x58(%ebp)\n  pushl 0x68(%ebp)\n  pushl %ecx\n  call _gp_ps_pop_ctx\n  addl $16, %esp\n" XLOAD "  ret\n"
/* 0x6fb869: obj [ebp+8], goal [ebp-0x34], hierarchical path holder [ebp-0x30] */
".globl _gp_ps_popB\n_gp_ps_popB:\n" XSAVE
"  pushl -0x30(%ebp)\n  pushl -0x34(%ebp)\n  pushl 0x8(%ebp)\n  pushl %ecx\n  call _gp_ps_pop_ctx\n  addl $16, %esp\n" XLOAD "  ret\n"
".globl _gp_ps_runstart_stub\n_gp_ps_runstart_stub:\n"
"  movl %ecx, 0x3c(%ebx)\n  movl %ecx, 0x40(%ebx)\n  movl %ecx, 0x44(%ebx)\n"
"  pushl %eax\n  pushl %ecx\n  pushl %edx\n" XSAVE "  pushl 4(%ebp)\n  pushl %ebx\n  call _gp_ps_runstart\n  addl $8, %esp\n"
XLOAD "  popl %edx\n  popl %ecx\n  popl %eax\n  ret\n"
".globl _gp_ps_resume_stub\n_gp_ps_resume_stub:\n"
"  pushal\n" XSAVE "  pushl %ebx\n  call _gp_ps_resume\n  addl $4, %esp\n" XLOAD "  popal\n"
"  cmpl %esi, 0x3c(%ebx)\n  jge 1f\n  jmp *_gp_ps_loop\n1: jmp *_gp_ps_exit\n"
".globl _gp_ps_reset_stub\n_gp_ps_reset_stub:\n"
"  pushal\n" XSAVE "  call _gp_ps_drop\n" XLOAD "  popal\n"
"  pushl %ecx\n  pushl %ebx\n  pushl %ebp\n  pushl %esi\n  movl %ecx, %esi\n  jmp *_gp_ps_reset_cont\n"
/* doPathfind's call of 0x6668ca (thiscall, 3 args): the victim is held across it */
".globl _gp_ps_approach_stub\n_gp_ps_approach_stub:\n"
"  lock incl _gp_ps_unsafe\n  pushl 0xc(%esp)\n  pushl 0xc(%esp)\n  pushl 0xc(%esp)\n  call *_gp_ps_approach\n"
"  lock decl _gp_ps_unsafe\n  ret $0xc\n");

int gp_patch_pathsplit(void)
{
    static const uint8_t popc[] = {0x56, 0x8d,0xb1,0xf0,0xd1,0x01,0x00};
    static const uint8_t pA1[] = {0xe8,0x4c,0x71,0xff,0xff}, pA2[] = {0xe8,0xe1,0x6e,0xff,0xff};
    static const uint8_t pB1[] = {0xe8,0x3a,0x8d,0xff,0xff}, pB2[] = {0xe8,0x8d,0x8a,0xff,0xff};
    static const uint8_t rs[] = {0x89,0x4b,0x3c, 0x89,0x4b,0x40, 0x89,0x4b,0x44};
    static const uint8_t rm[] = {0x39,0x73,0x3c, 0x0f,0x8d,0x12,0x01,0x00,0x00};
    static const uint8_t sv[] = {0xff,0x90,0x30,0x02,0x00,0x00};
    static const uint8_t rst[] = {0x51, 0x53, 0x55, 0x56, 0x8b,0xf1};
    static const uint8_t apr[] = {0xe8,0x02,0xd8,0xff,0xff};
    gp_site s[28];
    int n = 0;
    gp_site_hash(&s[n++], 0x6f236a, 0x294, GP_FNV_6F236A);   /* the queue (its first 6 bytes: moveawayqueue) */
    gp_site_hash(&s[n++], 0x6fd06f, 0xd76, GP_FNV_6FD06F);
    gp_site_hash(&s[n++], 0x6fb869, 0x925, GP_FNV_6FB869);
    gp_site_hash(&s[n++], 0x6f4af2, 0x28, GP_FNV_6F4AF2);
    gp_site_hash(&s[n++], 0x6f5a5e, 0x152, GP_FNV_6F5A5E);
    gp_site_hash(&s[n++], 0x668e94, 0x75b, GP_FNV_668E94);   /* doPathfind */
    gp_site_hash(&s[n++], 0x6ea019, 0x34, GP_FNV_6EA019);
    gp_site_hash(&s[n++], 0x934594, 0x16, GP_FNV_934594);
    gp_site_hash(&s[n++], 0x6e8074, 0x41, GP_FNV_6E8074);
    gp_site_hash(&s[n++], 0x9347c6, 0x40, GP_FNV_9347C6);
    gp_site_hash(&s[n++], 0x90be00, 0x31, GP_FNV_90BE00);
    gp_site_hash(&s[n++], 0x6ec096, 0x3b, GP_FNV_6EC096);
    gp_site_hash(&s[n++], 0x6ec1b7, 0x4d, GP_FNV_6EC1B7);
    gp_site_hash(&s[n++], 0x93450f, 0x29, GP_FNV_93450F);
    gp_site_hash(&s[n++], 0x6fec66, 5, 0x1f4827906b4a47aaull);  /* TheAI's update: call 0x6f2364 (phase 5) */
    gp_site_init(&s[n], 0x6f4af2, popc, sizeof popc); gp_rel32(&s[n], 0, 0xe9, (void *)gp_ps_popcount);
    s[n].repl[5] = s[n].repl[6] = 0x90; n++;
    gp_site_init(&s[n], 0x6fd9a1, pA1, 5); gp_rel32(&s[n++], 0, 0xe8, (void *)gp_ps_popA);
    gp_site_init(&s[n], 0x6fdc0c, pA2, 5); gp_rel32(&s[n++], 0, 0xe8, (void *)gp_ps_popA);
    gp_site_init(&s[n], 0x6fbdb3, pB1, 5); gp_rel32(&s[n++], 0, 0xe8, (void *)gp_ps_popB);
    gp_site_init(&s[n], 0x6fc060, pB2, 5); gp_rel32(&s[n++], 0, 0xe8, (void *)gp_ps_popB);
    gp_site_init(&s[n], 0x6f245a, rs, sizeof rs); gp_rel32(&s[n], 0, 0xe8, (void *)gp_ps_runstart_stub);
    for (int i = 5; i < 9; i++) s[n].repl[i] = 0x90;
    n++;
    gp_site_init(&s[n], 0x6f24de, rm, sizeof rm); gp_rel32(&s[n], 0, 0xe9, (void *)gp_ps_resume_stub);
    for (int i = 5; i < 9; i++) s[n].repl[i] = 0x90;
    n++;
    gp_site_init(&s[n], 0x6f2570, sv, sizeof sv); gp_rel32(&s[n], 0, 0xe8, (void *)gp_ps_serve);
    s[n].repl[5] = 0x90; n++;
    gp_site_init(&s[n], 0x6f5a5e, rst, sizeof rst); gp_rel32(&s[n], 0, 0xe9, (void *)gp_ps_reset_stub);
    s[n].repl[5] = 0x90; n++;
    gp_site_init(&s[n], 0x6690c3, apr, 5); gp_rel32(&s[n++], 0, 0xe8, (void *)gp_ps_approach_stub);
    ps_off = gp_va_offset;
    gp_ps_pop_cont = 0x6f4af9 + gp_va_offset;
    gp_ps_loop = 0x6f24e7 + gp_va_offset;
    gp_ps_exit = 0x6f25f9 + gp_va_offset;
    gp_ps_reset_cont = 0x6f5a64 + gp_va_offset;
    gp_ps_approach = 0x6668ca + gp_va_offset;
    gp_ps_ai_ret = 0x6fec6b + gp_va_offset;
    if (n > (int)(sizeof s / sizeof s[0])) abort();
    if (!gp_apply("pathsplit", s, n)) return 0;
    gp_log("pathsplit: queued searches stop after %u popped cells per queue run and go on in the next", gp_ps_budget);
    return 1;
}

void gp_ps_exit_log(void)
{
    if (gp_ps_stats[0])
        gp_log("exit: pathsplit requests %ld, parked %ld, resumed %ld, dropped (unit gone %ld, cancelled %ld, map "
               "reset %ld), asked again while parked %ld, finished after parking %ld, most runs for one "
               "request %ld, most fiber pops in one run %ld, run whole %ld, restore anomalies %ld",
               gp_ps_stats[0], gp_ps_stats[1], gp_ps_stats[2], gp_ps_stats[3], gp_ps_stats[4], gp_ps_stats[11],
               gp_ps_stats[5], gp_ps_stats[8], gp_ps_stats[6], gp_ps_stats[7], gp_ps_stats[9], gp_ps_stats[10]);
}
