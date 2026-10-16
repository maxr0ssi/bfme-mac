/* t_phasebal world: the game's own GameLogic::update 0x62e4e8 (phases 2-6), its list loop, the
 * clean-up, setWakeFrame 0x62b921, vector push_back 0x90be00 and the disabled-module test run on
 * synthetic objects and update modules. .text runs at its address + OFF, .rdata/.data at their own
 * addresses (as t_path). Stood in at their entry: the pathfind queue 0x6f2364 (it wakes sleeping
 * modules: list growth between passes), the pending-object pass 0x629da6 (logs the objects),
 * the destroy list 0x62a2c9 (removes a destroyed object's modules as the game does: swap with the
 * last), the phase-2 per-object update 0x6260e1, 0x80f4d3, setFPMode 0x440809, the vector erase
 * 0x5ff9d3; the 15 subsystems are objects whose vt+0x28 logs. Update modules log, return a sleep
 * time from a hash of (seed, id, frame) and, in a mutating world, wake other modules, destroy
 * objects, create objects and mark objects as having changed cell. Nothing reads an address. */
#include "orig.h"
#include "gp.h"
#include "p_fps.h"
#include "t_phasebal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

uint32_t OFF;
#define TC __attribute__((thiscall))
#define AT(va) ((uint32_t *)(uintptr_t)(va))
#define FN(t, va) ((t)(uintptr_t)((va) + OFF))
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define PTR(p, o) (*(uint8_t **)((uint8_t *)(p) + (o)))
#define MAXM 40000
#define MAXO 20000
#define VCAP 65536
#define SENTINEL 0x80000000u           /* pending objects added by the subsystems: never processed */

struct pb_world {
    pb_cfg c;
    uint8_t *gl, *mods[MAXM], *objs[MAXO], *dq[MAXO];
    int nmods, nobjs, ndq;
    uint32_t lrng, frame0;
    uint8_t cnt[MAXM];                  /* updates in the current step */
    uint8_t due[MAXM];
    int last_idx[4];
    void *keep[MAXM + MAXO + 64]; int nkeep;
};

static pb_world *W;                     /* the world being run (the stand-ins' context) */
static pb_ev *EV; static int NEV, MAXEV, STEP, PHASE, UNORD;

static uint32_t mix(uint32_t a, uint32_t b, uint32_t c)
{
    uint32_t h = a * 0x9e3779b1u ^ (b + 0x7f4a7c15u) * 0x85ebca6bu ^ (c + 0x165667b1u) * 0xc2b2ae35u;
    h ^= h >> 15; h *= 0x2c1b3c6du; h ^= h >> 12; h *= 0x297a2d39u; h ^= h >> 15;
    return h;
}
static uint32_t lrnd(pb_world *w) { w->lrng ^= w->lrng << 13; w->lrng ^= w->lrng >> 17; w->lrng ^= w->lrng << 5; return w->lrng; }
static void *wal(pb_world *w, size_t n)  /* zeroed, after a salt-sized gap so addresses move */
{
    size_t pad = w->c.salt ? (lrnd(w) % 32) * 4096 + 64 * (lrnd(w) % 61) : 0;
    uint8_t *p = calloc(1, n + pad + 64);
    w->keep[w->nkeep++] = p;
    return (void *)(((uintptr_t)p + pad + 63) & ~(uintptr_t)63);
}
static void ev(int kind, uint32_t id, uint32_t aux)
{
    if (NEV < MAXEV) { pb_ev *e = &EV[NEV]; e->step = (uint16_t)STEP; e->phase = (uint8_t)PHASE; e->kind = (uint8_t)kind; e->id = id; e->aux = aux; }
    NEV++;
}
static uint32_t *vec(int k) { return (uint32_t *)(W->gl + (k < 4 ? 0xc8 + 12 * k : k == 4 ? 0xf8 : 0x164)); }
static uint32_t vsz(const uint32_t *v) { return (v[1] - v[0]) / 4; }
static uint32_t frame(void) { return U32(W->gl, 0x40); }

/* ---- the game functions the stand-ins and modules call ---------------------------------------- */
typedef void (TC *push_t)(uint32_t *v, void *pval);              /* 0x90be00 vector<T*>::push_back */
typedef void (TC *wake_t)(uint8_t *gl, uint8_t *obj, uint8_t *mod, uint32_t frame);   /* 0x62b921 */
typedef void (TC *upd_t)(uint8_t *gl, int phase);                 /* 0x62e4e8 GameLogic::update */
static void push(uint32_t *v, void *p) { FN(push_t, 0x90be00)(v, &p); }

static void pend(uint32_t obj_or_sentinel)    /* as 0x62abc7: an object that changed cell, once */
{
    uint32_t *v = vec(5);
    for (uint32_t i = 0; i < vsz(v); i++) if (*(uint32_t *)(uintptr_t)U32(v[0] + 4 * i, 0) == obj_or_sentinel) return;
    static uint32_t box[4096]; static int nb;
    uint32_t *b = &box[nb++ & 4095]; *b = obj_or_sentinel;   /* the vector holds pointers: to a box with the id */
    push(v, b);
}

/* ---- update modules: primary vtable (+0x30: the list), update interface (vt[0] update, vt[1] the
 * disabled-type mask) ---------------------------------------------------------------------------- */
static int TC list0(void *m) { (void)m; return 0; }
static int TC list1(void *m) { (void)m; return 1; }
static int TC list2(void *m) { (void)m; return 2; }
static int TC list3(void *m) { (void)m; return 3; }
static void *pvt[4][16];
static uint8_t *new_object(pb_world *w, int nm, uint32_t h, int at_start);

static uint32_t TC m_update(uint8_t *iface)
{
    uint8_t *m = iface - 0x10;
    uint32_t id = U32(m, 0x20), list = U32(m, 0x1c), idx = U32(m, 0x18), fr = frame();
    ev(EV_MOD, id, list << 24 | idx);
    if (W->cnt[id] < 255) W->cnt[id]++;
    if (list < 4) { if ((int)idx <= W->last_idx[list]) UNORD++; W->last_idx[list] = (int)idx; }
    uint32_t h = mix(W->c.seed, id, fr);
    uint32_t sleep = h % 100 < (W->c.mutate ? 3u : 1u) ? 0x3fffffffu : 1 + (h >> 8) % 3;
    if (W->c.mutate) {
        uint32_t a = (h >> 16) % 211;
        if (a < 3) {                        /* wake a sleeping module, now or next frame */
            uint8_t *t = W->mods[mix(h, 1, 2) % (uint32_t)W->nmods], *o = PTR(t, 8);
            if (U32(t, 0x1c) == 0xffffffffu && U32(t, 0x18) != 0xffffffffu && !(U32(o, 0x94) & 1))
                FN(wake_t, 0x62b921)(W->gl, o, t, fr + (a & 1));
        } else if (a < 5) {                 /* destroy an object (its modules leave at the destroy list) */
            uint8_t *o = W->objs[mix(h, 3, 4) % (uint32_t)W->nobjs];
            if (!(U32(o, 0x94) & 1) && W->ndq < MAXO) { U32(o, 0x94) |= 1; W->dq[W->ndq++] = o; }
        } else if (a < 7) {                 /* a new object, 1-3 modules, due now */
            if (W->nobjs < MAXO - 1 && W->nmods < MAXM - 4) new_object(W, 1 + (int)(h >> 28) % 3, mix(h, 5, 6), 0);
        } else if (a < 30) pend(U32(PTR(m, 8), 0x400));   /* its object changed cell */
    }
    return sleep;
}
static uint32_t *TC m_mask(uint8_t *iface, void *tmp) { (void)tmp; return (uint32_t *)(iface - 0x10 + 0x28); }
static void *ivt[4] = {(void *)m_update, (void *)m_mask};
void *pb_iface_vt(void) { return ivt; }

static uint8_t *new_object(pb_world *w, int nm, uint32_t h, int at_start)
{
    uint8_t *o = wal(w, 0x500), *head = PTR(w->gl, 0xac);
    U32(o, 0x400) = (uint32_t)w->nobjs;
    U32(o, 0x188) = 0;
    if (h % 53 == 0) U32(o, 0x1c8) = 0x40;   /* disabled (a type its modules' masks do not all cover) */
    w->objs[w->nobjs++] = o;
    PTR(o, 0x8c) = head; if (head) PTR(head, 0x90) = o; PTR(w->gl, 0xac) = o;
    for (int i = 0; i < nm; i++) {
        uint8_t *m = wal(w, 0x40);
        uint32_t r = mix(h, (uint32_t)i, 9) % 100, k = r < 60 ? 0 : r < 65 ? 1 : r < 90 ? 2 : 3;
        U32(m, 0) = (uint32_t)(uintptr_t)pvt[k];
        PTR(m, 8) = o;
        U32(m, 0x10) = (uint32_t)(uintptr_t)ivt;
        U32(m, 0x20) = (uint32_t)w->nmods;
        U32(m, 0x28) = mix(h, (uint32_t)i, 11) % 2 ? 0x40 : 0x01;
        uint32_t fr = U32(w->gl, 0x40);
        if (at_start && mix(h, (uint32_t)i, 13) % 100 < 15) {   /* asleep for good */
            U32(m, 0x14) = 0x3fffffff; U32(m, 0x1c) = 0xffffffffu; U32(m, 0x18) = vsz(vec(4));
            push(vec(4), m);
        } else {
            U32(m, 0x14) = at_start ? fr + mix(h, (uint32_t)i, 17) % 3 : fr;
            U32(m, 0x1c) = k; U32(m, 0x18) = vsz(vec((int)k));
            push(vec((int)k), m);
        }
        PTR(o, 0x408 + 4 * i) = m; U32(o, 0x404) = (uint32_t)(i + 1);
        w->mods[w->nmods++] = m;
    }
    return o;
}

/* ---- stand-ins ------------------------------------------------------------------------------- */
static void TC s_queue(void *pf)             /* 0x6f2364: wakes sleeping modules (list growth) */
{
    (void)pf;
    ev(EV_Q, 0, 0);
    if (!W->c.mutate) return;
    uint32_t fr = frame(), k = mix(W->c.seed, fr, (uint32_t)PHASE) % 7;
    for (uint32_t i = 0; i < k; i++) {
        uint8_t *t = W->mods[mix(fr, (uint32_t)PHASE, i) % (uint32_t)W->nmods], *o = PTR(t, 8);
        if (U32(t, 0x1c) == 0xffffffffu && U32(t, 0x18) != 0xffffffffu && !(U32(o, 0x94) & 1))
            FN(wake_t, 0x62b921)(W->gl, o, t, fr);
    }
}
static void TC s_pending(uint8_t *gl)        /* 0x629da6: process the objects that changed cell, empty */
{
    uint32_t *v = (uint32_t *)(gl + 0x164);
    ev(EV_D, vsz(v), 0);
    for (uint32_t i = 0; i < vsz(v); i++) ev(EV_PEND, *(uint32_t *)(uintptr_t)U32(v[0] + 4 * i, 0), 0);
    v[1] = v[0];
}
static void TC s_destroy(uint8_t *gl)        /* 0x62a2c9: as the game removes a destroyed object's modules */
{
    ev(EV_SUBCALL, 100, (uint32_t)W->ndq);
    for (int d = 0; d < W->ndq; d++) {
        uint8_t *o = W->dq[d];
        for (uint32_t i = 0; i < U32(o, 0x404); i++) {
            uint8_t *m = PTR(o, 0x408 + 4 * i);
            uint32_t idx = U32(m, 0x18), k = U32(m, 0x1c);
            if (idx == 0xffffffffu) continue;
            U32(m, 0x18) = U32(m, 0x1c) = 0xffffffffu;
            uint32_t *v = vec(k == 0xffffffffu ? 4 : (int)k), n = vsz(v);
            if (idx < n - 1) {
                uint8_t *last = (uint8_t *)(uintptr_t)U32(v[0] + 4 * (n - 1), 0);
                U32(v[0] + 4 * idx, 0) = (uint32_t)(uintptr_t)last;
                U32(last, 0x18) = idx; U32(last, 0x1c) = k;
            }
            v[1] -= 4;
        }
        uint8_t *nx = PTR(o, 0x8c), *pv = PTR(o, 0x90);       /* out of the object list */
        if (pv) PTR(pv, 0x8c) = nx; else PTR(gl, 0xac) = nx;
        if (nx) PTR(nx, 0x90) = pv;
        PTR(o, 0x8c) = PTR(o, 0x90) = NULL;
    }
    W->ndq = 0;
}
static void TC s_p2(uint8_t *o, uint32_t fr) { ev(EV_P2, U32(o, 0x400), 0); U32(o, 0x188) = fr; }
static void TC s_80f4d3(void *x) { (void)x; ev(EV_SUBCALL, 101, 0); }
static void s_setfp(void) { }
static uint32_t TC s_erase(uint32_t *v, uint32_t first, uint32_t last)   /* 0x5ff9d3 */
{
    uint32_t n = v[1] - last;
    memmove((void *)(uintptr_t)first, (void *)(uintptr_t)last, n);
    v[1] = first + n;
    return first;
}
static void s_never(void) { printf("a vector grew or an assertion ran: the world is too big for its vectors\n"); exit(3); }

/* the subsystems: 0-1 phase 2, 2 TheAI, 3-14 the twelve after it */
static const uint32_t SUBG[15] = {0xde4354, 0xde4360, 0xde4b40, 0xde4358, 0xde435c, 0xde8200, 0xde3be8, 0xde4a1c,
                                  0xde369c, 0xde89ac, 0xde8ac0, 0xde4938, 0xde7924, 0xde8304, 0};
static void sub_ev(int i)
{
    if (i == 2) { ev(EV_AI, 2, 0); return; }
    ev(EV_SUB, (uint32_t)i, 0);
    if (i == 3) { pend(SENTINEL | frame()); pend(SENTINEL | 0x10000000u | frame()); }  /* shroud: never processed */
    if (i == 7) pend(SENTINEL | 0x20000000u | frame());
}
#define SUBF(i) static void TC sub##i(void *o) { (void)o; sub_ev(i); }
SUBF(0) SUBF(1) SUBF(2) SUBF(3) SUBF(4) SUBF(5) SUBF(6) SUBF(7) SUBF(8) SUBF(9) SUBF(10) SUBF(11) SUBF(12) SUBF(13)
static void *const SUBFN[14] = {sub0, sub1, sub2, sub3, sub4, sub5, sub6, sub7, sub8, sub9, sub10, sub11, sub12, sub13};
static void *subvt[14][16];
static uint32_t subobj[14][8];

static void jmp_to(uint32_t va, void *target)
{
    uint8_t *p = (uint8_t *)(uintptr_t)(va + OFF);
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)target - (va + OFF + 5));
    p[0] = 0xe9; memcpy(p + 1, &rel, 4);
}

int pb_init(const char *exe)
{
    if (!VirtualAlloc((void *)0xbd0000, 0xe10000 - 0xbd0000, MEM_RESERVE, PAGE_READWRITE)) {
        printf("cannot reserve the image's data range\n");
        return 1;
    }
    if (orig_load(exe)) return 1;
    if (orig_map_at(0xbd0000, 0x1b9000, 0) || orig_map_at(0xd89000, 0x81000, 0)) return 1;
    if (!(OFF = orig_reserve_image()) || orig_map_at(0x401000, 0x7cf000, OFF)) return 1;
    if (orig_map_at(0xbd8000, 0x1000, OFF) || orig_map_at(0xbfd000, 0x1000, OFF)) return 1;   /* logicstats' vtable slots ([6]) */
    jmp_to(0x6f2364, (void *)s_queue);  jmp_to(0x629da6, (void *)s_pending);
    jmp_to(0x62a2c9, (void *)s_destroy); jmp_to(0x6260e1, (void *)s_p2);
    jmp_to(0x80f4d3, (void *)s_80f4d3); jmp_to(0x440809, (void *)s_setfp);
    jmp_to(0x5ff9d3, (void *)s_erase);  jmp_to(0x8ea106, (void *)s_never);
    jmp_to(0x4380c0, (void *)s_never);  /* setWakeFrame's assertion */
    for (int k = 0; k < 4; k++) pvt[k][0x30 / 4] = (void *)(k == 0 ? list0 : k == 1 ? list1 : k == 2 ? list2 : list3);
    for (int i = 0; i < 14; i++) {
        subvt[i][0x28 / 4] = SUBFN[i];
        subobj[i][0] = (uint32_t)(uintptr_t)subvt[i];
        *AT(SUBG[i]) = (uint32_t)(uintptr_t)subobj[i];
    }
    static uint32_t pf[64], gc[128], gd[0x1000];
    subobj[2][4] = (uint32_t)(uintptr_t)pf;              /* TheAI +0x10: the pathfinder (the queue's this) */
    *AT(0xde4388) = (uint32_t)(uintptr_t)gc;            /* TheGameClient (paused path only) */
    *AT(0xde4364) = (uint32_t)(uintptr_t)gd;
    *(uint8_t *)(uintptr_t)0xde4148 = 0;
    *AT(0xde7cd8) = 0; *AT(0xde8a98) = 0;
    return 0;
}

pb_world *pb_build(const pb_cfg *c)
{
    pb_world *w = calloc(1, sizeof *w);
    w->c = *c; w->lrng = c->salt * 2654435761u + 1;
    W = w;
    w->gl = wal(w, 0x400);
    *AT(0xde412c) = (uint32_t)(uintptr_t)w->gl;
    U32(w->gl, 0x40) = w->frame0 = 2000;
    U32(w->gl, 0x110) = 4;                 /* 0x441b60 false: no frame-0x400 message */
    U32(w->gl, 0x1b4) = 0;
    for (int k = 0; k < 6; k++) {          /* begin, end, capacity: big enough never to grow */
        uint32_t *v = vec(k), *mem = wal(w, 4 * VCAP);
        v[0] = v[1] = (uint32_t)(uintptr_t)mem; v[2] = v[0] + 4 * VCAP;
    }
    for (int i = 0; i < c->nobj; i++) new_object(w, 1 + (int)(mix(c->seed, (uint32_t)i, 77) % 3), mix(c->seed, (uint32_t)i, 78), 1);
    return w;
}

void pb_free(pb_world *w)
{
    for (int i = 0; i < w->nkeep; i++) free(w->keep[i]);
    free(w);
}

int pb_run(pb_world *w, int steps, pb_ev *e, int max, int *missed, int *twice, int *unordered)
{
    W = w; EV = e; MAXEV = max; NEV = 0; UNORD = 0;
    *AT(0xde412c) = (uint32_t)(uintptr_t)w->gl;
    *missed = *twice = 0;
    for (int s = 0; s < steps; s++) {
        STEP = s;
        U32(w->gl, 0x40)++;                 /* phase 1: the logic frame +1 */
        uint32_t fr = frame();
        memset(w->cnt, 0, sizeof w->cnt);
        for (int k = 0; k < 4; k++) w->last_idx[k] = -1;
        for (int i = 0; i < w->nmods; i++) {   /* due now: in an update list, awake, object alive and enabled */
            uint8_t *m = w->mods[i], *o = PTR(m, 8);
            w->due[i] = U32(m, 0x1c) < 4 && U32(m, 0x14) <= fr && !(U32(o, 0x94) & 1) && !U32(o, 0x1c8);
        }
        int n0 = w->nmods;
        for (int ph = 2; ph <= 6; ph++) { PHASE = ph; FN(upd_t, 0x62e4e8)(w->gl, ph); }
        for (int i = 0; i < n0; i++) {
            uint8_t *o = PTR(w->mods[i], 8);
            if (w->due[i] && !w->cnt[i] && !(U32(o, 0x94) & 1)) (*missed)++;
            if (w->cnt[i] > 1) (*twice)++;
        }
    }
    *unordered = UNORD;
    return NEV;
}

void pb_counts(pb_world *w, int *modules, int *lists)
{
    *modules = w->nmods; *lists = 0;
    W = w;
    for (int k = 0; k < 4; k++) *lists += (int)vsz(vec(k));
}

double pb_us_per_step(pb_world *w, int steps)
{
    static pb_ev junk[1];
    int a, b, c;
    uint64_t t0 = now_us();
    pb_run(w, steps, junk, 0, &a, &b, &c);
    return (double)(now_us() - t0) / steps;
}

/* the patch, in the relocated copy: original bytes, or the stubs with gp_pb_mode 1 / 2 */
static const uint32_t RVA[7] = {0x62e982, 0x62e9d4, 0x62ea09, 0x62eadf, 0x62eb63, 0x62eb7b, 0x62ec10};
static const uint32_t RLEN[7] = {0x48, 22, 27, 6, 6, 10, 7};
static uint8_t r_orig[7][0x48], r_new[7][0x48];
static int saved;
int pb_patch(int mode)
{
    if (!saved) {
        for (int i = 0; i < 7; i++) memcpy(r_orig[i], (void *)(uintptr_t)(RVA[i] + OFF), RLEN[i]);
        gp_va_offset = OFF;
        int ok = gp_patch_phasebalance();
        gp_va_offset = 0;
        if (!ok) return 0;
        for (int i = 0; i < 7; i++) memcpy(r_new[i], (void *)(uintptr_t)(RVA[i] + OFF), RLEN[i]);
        saved = 1;
    }
    for (int i = 0; i < 7; i++) memcpy((void *)(uintptr_t)(RVA[i] + OFF), mode ? r_new[i] : r_orig[i], RLEN[i]);
    FlushInstructionCache(GetCurrentProcess(), NULL, 0);
    gp_pb_mode = mode ? mode : 1;
    return 1;
}
