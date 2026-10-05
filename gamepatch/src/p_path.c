/* pathfind: the two per-neighbour scans of the pathfinder's search step, memoised per search.
 *
 * The search step 0x6f9850 (examineNeighboringCells, called once per expanded cell by the seven
 * search loops) calls two functions for each of its 8 neighbours, and both walk a (2r+c)^2 window
 * of cells around the neighbour (r = the unit's cell radius, c = 1 for an odd footprint):
 *   0x6ebaa0 checkForMovement: footprint passability, plus every unit standing in a window cell
 *            (relationship, "is it moving", ally/enemy blockers: up to 5 game calls per unit);
 *   0x6ed21e the crowd cost: every unit heading for a window cell (relationship, two priority
 *            calls, "is it moving", and for movers two x87 distances with CRT sqrt, two x87
 *            divides by locomotor speeds, and a terrain height lookup through two virtual calls).
 * A unit is therefore asked the same questions once per window it falls in, (2r+c)^2 times per
 * search, and every getCell is a call. Nothing the answers depend on changes during one search
 * (searches are synchronous loops on the logic thread; units move only between them).
 *
 * Here both functions are rewritten exactly (the same control flow, the same writes to the
 * movement-info struct, the same results) with three changes that cannot alter a result:
 *   - the ground-layer getCell is inlined (bridge layers still call the game's getCell);
 *   - every per-unit and per-mover answer (relationship, moving, priority, speed, the mover's
 *     footprint parity) is asked once per search and kept in a memo indexed by the unit's object ID
 *     (verified by pointer equality, so a collision only recomputes); no object pointer the memo
 *     keeps is ever dereferenced;
 *   - the crowd distances and divides are SSE single precision: exactly what the x87 code gives in
 *     the game's FPU mode (24-bit precision, round to nearest: every operation is one correctly
 *     rounded float operation either way, on float-sized coordinates). In any other x87 mode the
 *     game's own crowd function runs. The terrain height the original computes and never reads is
 *     not computed.
 * The memo lives for one search: it ends in the clean-up every search ends with (0x6f5519), and a
 * search step entered with at most one cell on the closed list (every search loop closes its start
 * cell, then examines it) or for another mover starts a new one. Results are a function of the game state alone (no addresses, timing or threads), so
 * they are deterministic, and the test (t_path) shows them identical to the original's.
 * Only the call sites inside a search are redirected: the search step's two, and the two in the
 * jump-ahead step 0x6f6d57 that the search step calls every 16th cell; other callers keep the
 * originals. */
#include "gp_logic.h"
#include <string.h>

#define TC __attribute__((thiscall))
#define U8(p, o)  (*(uint8_t *)((uint8_t *)(p) + (o)))
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define I32(p, o) (*(int32_t *)((uint8_t *)(p) + (o)))
#define F32(p, o) (*(float *)((uint8_t *)(p) + (o)))
#define PTR(p, o) ((uint8_t *)(uintptr_t)U32(p, o))
#define GFN(t, va) ((t)(uintptr_t)((va) + pf_off))   /* pf_off: gp_va_offset at install (tests) */

typedef uint8_t *(TC *getcell_t)(void *pf, int layer, int x, int y);   /* 0x5e2e9c */
typedef uint8_t  (TC *cfm_t)(void *pf, void *obj, void *info, const int *ppos);
typedef int      (TC *crowd_t)(void *pf, void *obj, void *cell, const int *pos, int r, int r2, int flag);
typedef int      (TC *rel_t)(void *obj, void *other);                   /* 0x68d7ab */
typedef uint8_t  (TC *is_t)(void *obj);                                 /* 0x68b47f, 0x68b68a */
typedef uint32_t (TC *prio_t)(void *ai, int enemy);                     /* 0x663f48 */
typedef float    (TC *speed_t)(void *loco, void *obj);                  /* 0x5e3f49 */
typedef uint8_t  (TC *b6950_t)(void *obj, void *other, int kind);       /* 0x6950f3 */
typedef void    *(TC *lookup_t)(void *p);                               /* 0x8dbace, 0x668303 */
typedef uint8_t  (*parity_t)(void *obj);                                /* 0x6ecfc5, cdecl, al */

uint32_t gp_pf_gen = 1, gp_pf_cont;
static uint32_t pf_off;
volatile LONG gp_pf_stats[6];        /* memo resets, cfm calls, crowd calls, unit memo misses, crowd
                                      * originals, search steps (logic thread only: plain increments) */
static uint32_t ep, mgen;            /* memo epoch: bumped on every reset */
static void *mobj, *mpf;

/* per-mover answers, valid for the epoch they were taken in */
static struct {
    uint32_t have;                   /* bit: 0 68b68a, 3 parity, 4 speed, 5-6 prio */
    uint8_t is68b68a, parity;
    float speed;
    uint32_t prio[2];
} me;

/* per-unit answers, direct-mapped by object ID */
#define UN 4096
typedef struct {
    uint32_t ep; void *u;
    uint32_t have;                   /* bit: 0 rel, 1 moving, 2 6950f3, 3 speed, 4-5 prio */
    int rel; uint8_t moving, b6950;
    float speed;
    uint32_t prio[2];
} um_t;
static um_t ut[UN];

static void memo_begin(void *pf, void *obj)
{
    if (mgen == gp_pf_gen && mobj == obj && mpf == pf) return;
    mgen = gp_pf_gen; mobj = obj; mpf = pf;
    if (++ep == 0) { memset(ut, 0, sizeof ut); ep = 1; }
    me.have = 0;
    gp_pf_stats[0]++;
}

static um_t *unit(uint8_t *u)
{
    um_t *e = &ut[U32(u, 0x74) & (UN - 1)];
    if (e->ep != ep || e->u != u) { e->ep = ep; e->u = u; e->have = 0; gp_pf_stats[3]++; }
    return e;
}
static int urel(um_t *e, void *obj)
{
    if (!(e->have & 1)) { e->rel = GFN(rel_t, 0x68d7ab)(obj, e->u); e->have |= 1; }
    return e->rel;
}
static int umoving(um_t *e)
{
    if (!(e->have & 2)) { e->moving = GFN(is_t, 0x68b47f)(e->u) != 0; e->have |= 2; }
    return e->moving;
}
static int u6950(um_t *e, void *obj)
{
    if (!(e->have & 4)) { e->b6950 = GFN(b6950_t, 0x6950f3)(obj, e->u, 2) != 0; e->have |= 4; }
    return e->b6950;
}
static uint32_t uprio(um_t *e, void *ai, int enemy)
{
    if (!(e->have & (16u << enemy))) { e->prio[enemy] = GFN(prio_t, 0x663f48)(ai, enemy); e->have |= 16u << enemy; }
    return e->prio[enemy];
}
static float uspeed(um_t *e, void *loco)
{
    if (!(e->have & 8)) { e->speed = GFN(speed_t, 0x5e3f49)(loco, e->u); e->have |= 8; }
    return e->speed;
}

/* the ground-layer path of getCell 0x5e2e9c inlined; bridge layers 2..15 call it */
static inline uint8_t *cellat(uint8_t *pf, int layer, int x, int y)
{
    if (x < I32(pf, 0x14) || x > I32(pf, 0x1c) || y < I32(pf, 0x18) || y > I32(pf, 0x20)) return NULL;
    if (layer > 1 && layer <= 15) return GFN(getcell_t, 0x5e2e9c)(pf, layer, x, y);
    return PTR(PTR(pf, 0x10), 4 * x) + 16 * y;
}

/* 0x6e8200: can the locomotor surfaces s stand on the cell */
static int passable(uint8_t *pf, const uint8_t *s, const uint8_t *cell)
{
    uint32_t f = U32(cell, 0xc), t = f & 0xf;
    if ((f >> 18 & 1) && U8(s, 5)) return 0;
    if (t == 3) { if ((f & 0x3f0) != 0x10) return 0; }
    else if (t == 4) {
        uint8_t *info = PTR(cell, 0);
        if ((info ? U32(info, 0x28) : 0) == U32(pf, 0x48)) return 1;
    }
    if (!(U32(s, 0) & *(uint32_t *)(uintptr_t)(0xda2444 + 4 * t))) return 0;
    if (U8(s, 4) && (f >> 17 & 1)) return 0;
    if (U8(s, 0xc) && !(f >> 22 & 1) && t == 4) return 0;
    if (I32(s, 8) >= 0 && (int)(f >> 19 & 3) > I32(s, 8)) return 0;
    return 1;
}

/* checkForMovement 0x6ebaa0 (thiscall pathfinder; obj, movement info m, parent cell position) */
uint8_t TC gp_pf_cfm(uint8_t *pf, uint8_t *obj, uint8_t *m, const int *pp)
{
    gp_pf_stats[1]++;
    memo_begin(pf, obj);
    U32(m, 0x2c) = 0; U8(m, 0x31) = 0; U8(m, 0x32) = 0; U8(m, 0x30) = 0; U32(m, 0x34) = 0;
    int r = I32(m, 0xc), r2 = r + (U8(m, 0x10) != 0), ml = I32(m, 8);
    uint32_t fl = U8(m, 0x14), lastid = 0;
    for (int x = I32(m, 0) - r; x < I32(m, 0) + r2; x++) {
        int inx = x >= pp[0] - r && x < pp[0] + r2;
        for (int y = I32(m, 4) - r; y < I32(m, 4) + r2; y++) {
            uint8_t *c = cellat(pf, ml, x, y);
            if (!c) return 0;
            uint32_t f = U32(c, 0xc);
            if ((f & 0xf) == 5) U32(m, 0x34)++;
            if (f >> 18 & 1) {
                if (!(me.have & 1)) { me.is68b68a = GFN(is_t, 0x68b68a)(obj) != 0; me.have |= 1; }
                if (me.is68b68a) U32(m, 0x34)++;
            }
            if (fl & 8) {
                int cl = f >> 4 & 0x3f;
                if (ml != cl) {
                    if (ml == 1 && cl != 0x10) U32(m, 0x34)++;
                    else if (ml >= 0x11 && ml <= 0x40 && cl != 0x10) U32(m, 0x34)++;
                }
            }
            if ((fl & 4) && !passable(pf, m + 0x1c, c)) U32(m, 0x34)++;
            if (inx && y >= pp[1] - r && y < pp[1] + r2) continue;      /* inside the parent's footprint */
            uint8_t *info = PTR(c, 0);
            if (!info) continue;
            if (U32(info, 0x14)) U8(m, 0x32) = 1;
            for (uint8_t *n = PTR(info, 0x20); n; n = PTR(n, 0)) {
                uint8_t *u = PTR(n, 8);
                if (u == obj) continue;
                uint32_t id = U32(u, 0x74);
                if (id == U32(m, 0x18) || id == lastid) continue;
                lastid = id;
                um_t *e = unit(u);
                int ally = urel(e, obj) == 2, consider = 0;
                if (ally) U8(m, 0x31) = 1;
                if (U8(m, 0x11)) consider = 1;
                if (!ally && (fl & 0x10)) consider = 1;
                if (umoving(e)) consider = 1;
                if (!consider) continue;
                uint8_t *T = PTR(obj, 4), *TU = PTR(u, 4);
                if (ally && (U32(T, 0x114) & 0x100000) && (U32(TU, 0x114) & 0x100000)) continue;
                if ((U8(T, 0x117) & 0x20) && (U8(TU, 0x109) & 1)) continue;
                if ((ally && (U32(T, 0x11c) & 0x4000000) && !(U32(TU, 0x11c) & 0x4000000)) || (U8(T, 0x11f) & 8)) {
                    U8(m, 0x32) = 0;
                    continue;
                }
                if (ally) {
                    if (!U32(u, 0x260) || (fl & 2)) return 0;
                    U32(m, 0x2c) = 1;
                    if (!(U32(TU, 0x11c) & 0x4000000) || (U32(T, 0x11c) & 0x4000000)) continue;
                    return 0;
                }
                if (u6950(e, obj)) continue;
                if (!(fl & 0x11)) continue;
                uint8_t *A = PTR(obj, 0x260);
                if (!A) return 0;
                uint8_t *v = GFN(lookup_t, 0x8dbace)(PTR(A, 0x30)), *uc = PTR(u, 0x27c);   /* objects: not kept */
                if (v) {
                    if (u == v || uc == v) continue;
                    uint8_t *w = PTR(v, 0x27c);
                    if (w && (u == w || uc == w)) continue;
                }
                v = GFN(lookup_t, 0x668303)(A);
                if (!v) return 0;
                if (u == v || uc == v) continue;
                uint8_t *w = PTR(v, 0x27c);
                if (!w) return 0;
                if (u == w || uc == w) continue;
                return 0;
            }
        }
    }
    return 1;
}

static inline float fdist(const uint8_t *o, float px, float py)
{
    float dx = F32(o, 0x38) - px, dy = F32(o, 0x3c) - py;
    return __builtin_sqrtf(dy * dy + dx * dx);
}

/* the crowd cost 0x6ed21e (thiscall pathfinder; obj, parent cell, neighbour position, r, r2, skip
 * enemies) */
int TC gp_pf_crowd(uint8_t *pf, uint8_t *obj, uint8_t *pcell, const int *pos, int r, int r2, int flag)
{
    uint16_t cw;
    __asm__ volatile("fnstcw %0" : "=m"(cw));
    if ((cw & 0xf00) != 0) {                                /* not the game's FPU mode: the original */
        gp_pf_stats[4]++;
        return GFN(crowd_t, 0x6ed21e)(pf, obj, pcell, pos, r, r2, flag);
    }
    gp_pf_stats[2]++;
    if (!pcell) return 0;
    memo_begin(pf, obj);
    int layer = U32(pcell, 0xc) >> 4 & 0x3f, shift = r >= 4 ? 2 : r > 1 ? 1 : 0, sum = 0, havep = 0;
    float self = -1.0f, px = 0, py = 0;
    uint8_t *A = PTR(obj, 0x260);
    for (int x = pos[0] - r; x < pos[0] + r2; x++)
        for (int y = pos[1] - r; y < pos[1] + r2; y++) {
            uint8_t *c = cellat(pf, layer, x, y), *info;
            if (!c || !(info = PTR(c, 0))) continue;
            for (uint8_t *n = PTR(info, 0x14); n; n = PTR(n, 0)) {
                uint8_t *u = PTR(n, 8);
                if (u == obj || PTR(u, 0x27c) == obj) continue;
                um_t *e = unit(u);
                int enemy = urel(e, obj) == 0;
                if (enemy && (uint8_t)flag) continue;
                uint8_t *B = PTR(u, 0x260);
                if (!A || !B) continue;
                uint32_t pu = uprio(e, B, enemy);
                if (!(me.have & (32u << enemy))) { me.prio[enemy] = GFN(prio_t, 0x663f48)(A, enemy); me.have |= 32u << enemy; }
                if (me.prio[enemy] > pu) continue;
                if (umoving(e)) { sum += 8 >> shift; continue; }
                if (!U32(A, 0x1f0) || !U32(B, 0x1f0)) continue;
                if (!havep) {                               /* 0x6ed049 -> 0x6e8e19: the cell's world x, y */
                    if (!(me.have & 8)) { me.parity = GFN(parity_t, 0x6ecfc5)(obj) != 0; me.have |= 8; }
                    float h = me.parity ? 0.5f : 0.05f;
                    px = ((float)pos[0] + h) * 10.0f; py = ((float)pos[1] + h) * 10.0f;
                    havep = 1;
                }
                if (0.0f > self) {
                    if (!(me.have & 16)) { me.speed = GFN(speed_t, 0x5e3f49)(PTR(A, 0x1f0), obj); me.have |= 16; }
                    self = fdist(obj, px, py) / me.speed;
                }
                float t = fdist(u, px, py) / uspeed(e, PTR(B, 0x1f0));
                if (self > t) sum += 4 >> shift;
            }
        }
    return sum;
}

/* moveawaycap: getMoveAwayFromPath 0x6fb231 (privateMoveAwayFromUnit's flood for a free spot, no
 * cell limit in the game) gets its pops from here: a search ends with no spot found after
 * gp_pf_macap popped cells. A new search is one whose closed list is empty at a pop (only the start
 * is on the open list then). Counts only, so every machine stops at the same cell. */
typedef uint8_t *(TC *pop_t)(void *pf);
uint32_t gp_pf_macap = 800;
volatile LONG gp_pf_ma[3];           /* searches, capped, cells popped */
static uint32_t ma_pops;
uint8_t *TC gp_pf_ma_pop(uint8_t *pf)
{
    if (!U32(pf, 0x34)) { ma_pops = 0; gp_pf_ma[0]++; }
    if (++ma_pops > gp_pf_macap) { if (ma_pops == gp_pf_macap + 1) gp_pf_ma[1]++; return NULL; }
    gp_pf_ma[2]++;
    return GFN(pop_t, 0x6f4af2)(pf);
}

int gp_patch_moveawaycap(void)
{
    static const uint8_t call[] = {0xe8,0xc7,0x94,0xff,0xff};          /* 0x6fb626: call 0x6f4af2 */
    gp_site s[2];
    gp_site_hash(&s[0], 0x6fb231, 0x449, GP_FNV_6FB231);
    gp_site_init(&s[1], 0x6fb626, call, 5);
    gp_rel32(&s[1], 0, 0xe8, (void *)gp_pf_ma_pop);
    pf_off = gp_va_offset;
    if (!gp_apply("moveawaycap", s, 2)) return 0;
    gp_log("moveawaycap: a move-away search stops after %u cells", gp_pf_macap);
    return 1;
}

/* search-step entry: a new search when at most one cell is closed (the closed list head is
 * pathfinder+0x34, linked through info+0x34); then the original's first 11 bytes */
void gp_pf_entry(void);
__asm__(".text\n.globl _gp_pf_entry\n_gp_pf_entry:\n"
"  movl 0x34(%ecx), %eax\n  testl %eax, %eax\n  jz 1f\n  cmpl $0, 0x34(%eax)\n  jne 2f\n"
"1: incl _gp_pf_gen\n"
"2: incl _gp_pf_stats+20\n"
"  pushl %ebp\n  leal -0x50(%esp), %ebp\n  subl $0x94, %esp\n  jmp *_gp_pf_cont\n");

/* the open/closed clean-up 0x6f5519 that ends every search: the memo ends with it. Its first 9
 * bytes (push esi; push edi; mov esi, ecx; call 0x6f4b1a) run here. */
uint32_t gp_pf_clean_cont, gp_pf_clean_call;
void gp_pf_clean(void);
__asm__(".text\n.globl _gp_pf_clean\n_gp_pf_clean:\n"
"  incl _gp_pf_gen\n  pushl %esi\n  pushl %edi\n  movl %ecx, %esi\n  call *_gp_pf_clean_call\n  jmp *_gp_pf_clean_cont\n");

static int on;
int gp_patch_pathfind(void)
{
    static const uint8_t head[] = {0x55, 0x8d,0x6c,0x24,0xb0, 0x81,0xec,0x94,0x00,0x00,0x00};
    static const uint8_t call1[] = {0xe8,0xa5,0x1e,0xff,0xff}, call2[] = {0xe8,0x9c,0x33,0xff,0xff},
        call3[] = {0xe8,0xe7,0x4a,0xff,0xff}, call4[] = {0xe8,0xef,0x61,0xff,0xff};
    static const uint8_t clean[] = {0x56, 0x57, 0x8b,0xf1, 0xe8,0xf8,0xf5,0xff,0xff};
    gp_site s[13];
    gp_site_hash(&s[0], 0x6f9850, 0x721, GP_FNV_6F9850);
    gp_site_hash(&s[1], 0x6ebaa0, 0x3e9, GP_FNV_6EBAA0);
    gp_site_hash(&s[2], 0x6ed21e, 0x24e, GP_FNV_6ED21E);
    gp_site_hash(&s[3], 0x6e8200, 0xb3, GP_FNV_6E8200);
    gp_site_hash(&s[4], 0x5e2e9c, 0x56, GP_FNV_5E2E9C);
    gp_site_hash(&s[5], 0x6ed049, 0x28, GP_FNV_6ED049);
    gp_site_hash(&s[9], 0x6e8e19, 0xba, GP_FNV_6E8E19);
    gp_site_init(&s[6], 0x6f9850, head, sizeof head);
    gp_rel32(&s[6], 0, 0xe9, (void *)gp_pf_entry);
    for (int i = 5; i < 11; i++) s[6].repl[i] = 0x90;
    gp_site_init(&s[7], 0x6f9bf6, call1, 5);
    gp_rel32(&s[7], 0, 0xe8, (void *)gp_pf_cfm);
    gp_site_init(&s[8], 0x6f9e7d, call2, 5);
    gp_rel32(&s[8], 0, 0xe8, (void *)gp_pf_crowd);
    gp_site_init(&s[10], 0x6f6fb4, call3, 5);                  /* the jump-ahead step 0x6f6d57 */
    gp_rel32(&s[10], 0, 0xe8, (void *)gp_pf_cfm);
    gp_site_init(&s[11], 0x6f702a, call4, 5);
    gp_rel32(&s[11], 0, 0xe8, (void *)gp_pf_crowd);
    gp_site_init(&s[12], 0x6f5519, clean, sizeof clean);
    gp_rel32(&s[12], 0, 0xe9, (void *)gp_pf_clean);
    for (int i = 5; i < 9; i++) s[12].repl[i] = 0x90;
    gp_pf_clean_call = 0x6f4b1a + gp_va_offset;
    gp_pf_clean_cont = 0x6f5522 + gp_va_offset;
    gp_pf_cont = 0x6f985b + gp_va_offset;
    pf_off = gp_va_offset;
    if (!gp_apply("pathfind", s, 13)) return 0;
    on = 1;
    return 1;
}

void gp_pf_exit_log(void)
{
    if (gp_pf_ma[0])
        gp_log("exit: moveawaycap searches %ld, stopped at the cap %ld, cells %ld", gp_pf_ma[0], gp_pf_ma[1], gp_pf_ma[2]);
    if (on)
        gp_log("exit: pathfind search steps %ld, memo resets %ld, movement checks %ld, crowd costs %ld "
               "(%ld ran the original), unit memo misses %ld", gp_pf_stats[5], gp_pf_stats[0],
               gp_pf_stats[1], gp_pf_stats[2], gp_pf_stats[4], gp_pf_stats[3]);
}
