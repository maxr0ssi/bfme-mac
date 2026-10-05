/* t_path world: the game's own pathfinder code (search step 0x6f9850 and everything it calls, the
 * open heap, the closed list, the cell-info pool) runs on a synthetic map. .text runs at its
 * address + OFF, .rdata/.data at their own addresses (as in t_adecode); the exe's imports get
 * what the game gets under Wine with the game patch on (floor, sqrt: the patch's SSE versions;
 * fabs, abs: Wine's msvcr71). Game functions that look at objects outside the pathfinder are
 * replaced at their entry by stand-ins that read fields of the synthetic units: relationship
 * 0x68d7ab, "is moving" 0x68b47f, AI priority 0x663f48, locomotor speed 0x5e3f49, 0x6950f3,
 * the two blocker lookups 0x8dbace / 0x668303 and the footprint parity 0x6ecfc5; the terrain
 * (0xde4690) is an object whose three height methods are stand-ins. Everything else is the
 * game's code: getCell, the passability test, checkForMovement, the crowd cost, the heuristic,
 * the jump-ahead step, the danger grid lookup, the zone check, info allocation and release. */
#include "orig.h"
#include "gp_logic.h"
#include "t_path.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

uint32_t OFF;
uint8_t *gd, *grid, (*tmpl)[0x800];
#define FN(t, va) ((t)(uintptr_t)((va) + OFF))
#define AT(va) ((uint32_t *)(uintptr_t)(va))
#define NINFO 400000
#define HEAPN (1 << 20)

struct pw {
    pw_cfg c;
    uint8_t *pf, *cells, *uinfo, *uinfo0, *pool, *nodes, *mover[4], **units, *slab;
    size_t uinfo_size;
    size_t slab_used, slab_size;
    uint32_t *cols, *heap;
    void *keep[64]; int nkeep;           /* every allocation, for pw_free */
    int nunits;
    int cx[4], cy[4];                    /* battle centres */
};

static uint32_t rng;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static uint32_t lrng;                    /* layout randomness (salt), separate from the map's */
static uint32_t lrnd(void) { lrng ^= lrng << 13; lrng ^= lrng >> 17; lrng ^= lrng << 5; return lrng; }

static void *wal(pw_t *w, size_t n)      /* zeroed, after a salt-sized gap so addresses move */
{
    size_t pad = w->c.salt ? (lrnd() % 64) * 4096 + 64 * (lrnd() % 61) : 0;
    uint8_t *p = calloc(1, n + pad + 64);
    w->keep[w->nkeep++] = p;
    return (void *)(((uintptr_t)p + pad + 63) & ~(uintptr_t)63);
}

/* ---- stand-ins for the object side ----------------------------------------------------------- */
/* unit fields used only by the stand-ins: +0x700 team, +0x704 moving, +0x708 priority,
 * +0x70c speed, +0x710 footprint parity; ai +0x8 = its object */
static int TC s_rel(uint8_t *o, uint8_t *u)
{
    int a = I32(o, 0x700), b = I32(u, 0x700);
    return a == b ? 2 : a == 9 || b == 9 ? 1 : 0;              /* 2 allies, 1 neutral, 0 enemies */
}
static uint8_t TC s_moving(uint8_t *u) { return U8(u, 0x704); }
static uint32_t TC s_prio(uint8_t *ai, int enemy) { (void)enemy; return U32(PTR(ai, 8), 0x708); }
static float TC s_speed(uint8_t *loco, uint8_t *o) { (void)loco; return F32(o, 0x70c); }
static uint8_t TC s_6950(uint8_t *o, uint8_t *u, int k) { (void)o; (void)k; return U32(u, 0x74) % 7 == 0; }
static void *TC s_8dbace(uint8_t *x) { (void)x; return NULL; }
static void *TC s_668303(uint8_t *ai) { return PTR(ai, 0x40); }
static uint8_t s_parity(uint8_t *o) { return U8(o, 0x710); }
/* terrain: vtable +0x18 height(x, y, 0), +0x1c layer height(x, y, layer, 0, 1), +0x4c bridge
 * height(x, y, &z, 0, 0) */
static float TC t_h3(void *t, float x, float y, int z) { (void)t; (void)z; return (x * 0.003f) + (y * 0.002f); }
static float TC t_h5(void *t, float x, float y, int l, int a, int b) { (void)t; (void)l; (void)a; (void)b; return x * 0.003f - y * 0.001f; }
static uint8_t TC t_br(void *t, float x, float y, float *z, int a, int b) { (void)t; (void)x; (void)y; (void)z; (void)a; (void)b; return 0; }
static void *tvt[32], *terrain[4] = {tvt};

static void jmp_to(uint32_t va, void *target)
{
    uint8_t *p = (uint8_t *)(uintptr_t)(va + OFF);
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)target - (va + OFF + 5));
    p[0] = 0xe9; memcpy(p + 1, &rel, 4);
}

static uint8_t site_orig[6][11], site_new[6][11];
static const uint32_t site_va[6] = {0x6f9850, 0x6f9bf6, 0x6f9e7d, 0x6f6fb4, 0x6f702a, 0x6f5519};
static const uint32_t site_len[6] = {11, 5, 5, 5, 5, 9};
static int patched_once;

int pw_patch(int on)
{
    if (on && !patched_once) {
        for (int i = 0; i < 6; i++) memcpy(site_orig[i], (void *)(uintptr_t)(site_va[i] + OFF), site_len[i]);
        gp_va_offset = OFF;
        int ok = gp_patch_pathfind();
        gp_va_offset = 0;
        if (!ok) return 0;
        for (int i = 0; i < 6; i++) memcpy(site_new[i], (void *)(uintptr_t)(site_va[i] + OFF), site_len[i]);
        patched_once = 1;
        return 1;
    }
    if (!patched_once) return !on;
    for (int i = 0; i < 6; i++) memcpy((void *)(uintptr_t)(site_va[i] + OFF), on ? site_new[i] : site_orig[i], site_len[i]);
    return 1;
}

int pw_init(const char *exe)
{
    /* keep the data range free for the image (the 11 MB file buffer could otherwise land on it) */
    if (!VirtualAlloc((void *)0xbd0000, 0xe10000 - 0xbd0000, MEM_RESERVE, PAGE_READWRITE)) {
        printf("cannot reserve the image's data range\n");
        return 1;
    }
    if (orig_load(exe)) return 1;
    if (orig_map_at(0xbd0000, 0x1b9000, 0) || orig_map_at(0xd89000, 0x81000, 0)) return 1;
    if (!(OFF = orig_reserve_image()) || orig_map_at(0x401000, 0x7cf000, OFF)) return 1;
    HMODULE crt = LoadLibraryA("msvcr71.dll");
    if (!crt) { printf("no msvcr71.dll\n"); return 1; }
    gp_floor_orig = (uint32_t)(uintptr_t)GetProcAddress(crt, "floor");
    gp_ceil_orig = (uint32_t)(uintptr_t)GetProcAddress(crt, "ceil");
    gp_sqrt_orig = (uint32_t)(uintptr_t)GetProcAddress(crt, "sqrt");
    *AT(0xbd0580) = (uint32_t)(uintptr_t)gp_floor;          /* as the game patch installs them */
    *AT(0xbd0588) = (uint32_t)(uintptr_t)gp_ceil;
    *AT(0xbd06a0) = (uint32_t)(uintptr_t)gp_sqrt;
    *AT(0xbd06a8) = (uint32_t)(uintptr_t)GetProcAddress(crt, "fabs");
    *AT(0xbd0574) = (uint32_t)(uintptr_t)GetProcAddress(crt, "abs");
    jmp_to(0x68d7ab, (void *)s_rel);    jmp_to(0x68b47f, (void *)s_moving);
    jmp_to(0x663f48, (void *)s_prio);   jmp_to(0x5e3f49, (void *)s_speed);
    jmp_to(0x6950f3, (void *)s_6950);   jmp_to(0x8dbace, (void *)s_8dbace);
    jmp_to(0x668303, (void *)s_668303); jmp_to(0x6ecfc5, (void *)s_parity);
    jmp_to(0x934538, (void *)abort);    /* the info pool never grows here */
    tvt[0x18 / 4] = (void *)t_h3; tvt[0x1c / 4] = (void *)t_h5; tvt[0x4c / 4] = (void *)t_br;
    *AT(0xde4690) = (uint32_t)(uintptr_t)terrain;
    static uint8_t gd_[0x2000]; gd = gd_;
    I32(gd, 0x1210) = 15000; I32(gd, 0x121c) = 25000;
    *AT(0xde4364) = (uint32_t)(uintptr_t)gd;
    unsigned short cw = 0x007f;
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));
    return 0;
}

/* ---- the map --------------------------------------------------------------------------------- */
#define CELL(w, x, y) ((w)->cells + 16 * ((size_t)(x) * (w)->c.h + (y)))
static void settype(pw_t *w, int x, int y, int t)
{
    if (x < 0 || y < 0 || x >= w->c.w || y >= w->c.h) return;
    U32(CELL(w, x, y), 0xc) = (U32(CELL(w, x, y), 0xc) & ~0xfu) | t;
}
static void rect(pw_t *w, int x0, int y0, int dx, int dy, int t)
{
    for (int x = x0; x < x0 + dx; x++) for (int y = y0; y < y0 + dy; y++) settype(w, x, y, t);
}

static uint8_t *info_for(pw_t *w, int x, int y, int *used)
{
    uint8_t *c = CELL(w, x, y);
    if (!U32(c, 0)) {
        uint8_t *in = w->uinfo + 0x3c * (*used)++;
        I32(in, 0) = x; I32(in, 4) = y; U32(in, 0x30) = (uint32_t)(uintptr_t)c;
        U32(c, 0) = (uint32_t)(uintptr_t)in;
    }
    return PTR(c, 0);
}

static uint8_t *new_obj(pw_t *w, uint8_t *tmpl, int id, int team)
{
    /* objects from one slab, a salt-dependent gap before each */
    size_t gap = w->c.salt ? 64 * (lrnd() % 16) : 0;
    if (w->slab_used + gap + 0xc00 > w->slab_size) abort();
    uint8_t *o = w->slab + w->slab_used + gap, *ai = o + 0x800;
    w->slab_used += gap + 0xc00;
    U32(o, 4) = (uint32_t)(uintptr_t)tmpl; U32(o, 0x74) = id; U32(o, 0x260) = (uint32_t)(uintptr_t)ai;
    I32(o, 0x700) = team;
    U32(ai, 8) = (uint32_t)(uintptr_t)o;
    U32(ai, 0x1f0) = (uint32_t)(uintptr_t)ai + 0x300;                 /* a locomotor */
    U32(ai, 0x1cc + 0x10) = 1;                                         /* surfaces: ground */
    return o;
}

void pw_reset_pool(pw_t *w);
pw_t *pw_build(const pw_cfg *cfg)
{
    pw_t *w = calloc(1, sizeof *w);
    w->c = *cfg; rng = cfg->seed | 1; lrng = cfg->salt * 2654435761u | 1;
    int W = cfg->w, H = cfg->h;
    /* allocation order depends on the salt as well as the addresses */
    int order[6] = {0, 1, 2, 3, 4, 5};
    if (cfg->salt) for (int i = 5; i > 0; i--) { int j = lrnd() % (i + 1), t = order[i]; order[i] = order[j]; order[j] = t; }
    for (int k = 0; k < 6; k++) switch (order[k]) {
        case 0: w->pf = wal(w, 0x1d400); break;
        case 1: w->cells = wal(w, (size_t)W * H * 16); w->cols = wal(w, 4 * W); break;
        case 2: w->uinfo_size = 0x3c * ((size_t)cfg->units * 2 + (size_t)W * H / 3 + 16);
                w->uinfo = wal(w, w->uinfo_size); w->uinfo0 = wal(w, w->uinfo_size); break;
        case 3: w->pool = wal(w, 0x3c * (size_t)NINFO); break;
        case 4: w->heap = wal(w, 4 * (size_t)HEAPN); w->nodes = wal(w, 12 * (size_t)(cfg->units * 2 + 16)); break;
        case 5: w->units = wal(w, sizeof(void *) * (cfg->units + 1));
                w->slab_size = (size_t)(cfg->units + 8) * (0xc00 + 1024); w->slab = wal(w, w->slab_size); break;
    }
    uint8_t *P = w->pf;
    for (int x = 0; x < W; x++) w->cols[x] = (uint32_t)(uintptr_t)CELL(w, x, 0);
    U8(P, 8) = 1; U32(P, 0x10) = (uint32_t)(uintptr_t)w->cols;
    I32(P, 0x1c) = W - 1; I32(P, 0x20) = H - 1; I32(P, 0x2c) = W - 1; I32(P, 0x30) = H - 1;
    U32(P, 0x48) = 0xffff;                                             /* no obstacle is ignored */
    /* zone blocks of 16x16 cells (0x937e77): all known */
    int zw = (W + 15) / 16, zh = (H + 15) / 16;
    uint32_t *zc = wal(w, 4 * zw);
    uint8_t *zb = wal(w, 0x44 * (size_t)zw * zh);
    for (int i = 0; i < zw; i++) { zc[i] = (uint32_t)(uintptr_t)(zb + 0x44 * i * zh); for (int j = 0; j < zh; j++) U8(zb, 0x44 * (i * zh + j) + 0x34) = 1; }
    U32(P, 0x460 + 0x1ba38) = (uint32_t)(uintptr_t)zc; I32(P, 0x460 + 0x1ba3c) = zw; I32(P, 0x460 + 0x1ba40) = zh;
    U32(P, 0x1d1f0) = U32(P, 0x1d1f4) = (uint32_t)(uintptr_t)w->heap;
    U32(P, 0x1d1f8) = (uint32_t)(uintptr_t)(w->heap + HEAPN);
    /* the danger grid (0xde46a8): same cells, 0x14 bytes, word +6 > 0 costs 10 */
    static uint8_t grid_[0x100]; grid = grid_;
    uint32_t *gc = wal(w, 4 * W);
    uint8_t *gb = wal(w, 0x14 * (size_t)W * H);
    for (int x = 0; x < W; x++) gc[x] = (uint32_t)(uintptr_t)(gb + 0x14 * (size_t)x * H);
    U32(grid, 0x70) = (uint32_t)(uintptr_t)gc; I32(grid, 0x78) = W; I32(grid, 0x7c) = H;
    *AT(0xde46a8) = (uint32_t)(uintptr_t)grid;
    /* terrain: ground layer everywhere; map edge impassable; lakes, cliffs, buildings, walls */
    for (int x = 0; x < W; x++) for (int y = 0; y < H; y++) U32(CELL(w, x, y), 0xc) = 0x10;
    rect(w, 0, 0, W, 2, 6); rect(w, 0, H - 2, W, 2, 6); rect(w, 0, 0, 2, H, 6); rect(w, W - 2, 0, 2, H, 6);
    for (int i = 0; i < 14; i++) {                                     /* lakes */
        int cx = rnd() % W, cy = rnd() % H, r = 4 + rnd() % 14;
        for (int x = cx - r; x <= cx + r; x++) for (int y = cy - r; y <= cy + r; y++)
            if ((x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r) settype(w, x, y, 1);
    }
    for (int i = 0; i < 40; i++) {                                     /* cliff ridges */
        int x = rnd() % W, y = rnd() % H, n = 10 + rnd() % 40, dx = (int)(rnd() % 3) - 1, dy = (int)(rnd() % 3) - 1;
        for (int k = 0; k < n; k++, x += dx, y += dy) { settype(w, x, y, 2); settype(w, x + 1, y, 2); }
    }
    for (int i = 0; i < 260; i++) rect(w, rnd() % W, rnd() % H, 2 + rnd() % 7, 2 + rnd() % 7, 4);   /* buildings */
    for (int b = 0; b < 8; b++) {                                      /* walled bases, one gate each */
        int x0 = 20 + rnd() % (W - 80), y0 = 20 + rnd() % (H - 80), s = 24 + rnd() % 16;
        rect(w, x0, y0, s, 1, 4); rect(w, x0, y0 + s, s + 1, 1, 4); rect(w, x0, y0, 1, s, 4); rect(w, x0 + s, y0, 1, s, 4);
        if (b) rect(w, x0 + s / 2, y0, 3, 1, 0);                        /* base 0 stays closed */
        else { w->cx[3] = x0 + s / 2; w->cy[3] = y0 + s / 2; rect(w, x0 + 4, y0 + 4, s - 8, s - 8, 0); }
    }
    for (int x = 1; x < W - 1; x++) for (int y = 1; y < H - 1; y++) {   /* pinched, roads */
        uint8_t *c = CELL(w, x, y);
        if ((U32(c, 0xc) & 0xf) != 0) continue;
        int nb = 0;
        for (int k = 0; k < 4; k++) nb += (U32(CELL(w, x + (k == 0) - (k == 1), y + (k == 2) - (k == 3)), 0xc) & 0xf) != 0;
        if (nb >= 2) U32(c, 0xc) |= 1u << 16;
        if (y % 97 == 50 || x % 113 == 60) U32(c, 0xc) |= 1u << 21;
    }
    /* units: four battles, two armies each, plus the closed base's garrison */
    static uint8_t tmpl_[3][0x800]; tmpl = tmpl_;
    I32(tmpl[0], 0x57c) = 4; U8(tmpl[0], 0x644) = 1;
    I32(tmpl[1], 0x57c) = 4; U8(tmpl[1], 0x644) = 1; U32(tmpl[1], 0x114) = 0x100000;
    I32(tmpl[2], 0x57c) = 4; U8(tmpl[2], 0x644) = 1; U8(tmpl[2], 0x109) = 1;
    for (int b = 0; b < 3; b++) { w->cx[b] = W / 5 + rnd() % (3 * W / 5); w->cy[b] = H / 5 + rnd() % (3 * H / 5); }
    int used = 0, packed = 0;
    for (int x = 0; x < W; x++)                                         /* obstacles carry their object's ID */
        for (int y = 0; y < H; y++)
            if ((U32(CELL(w, x, y), 0xc) & 0xf) == 4 && used < W * H / 3) U32(info_for(w, x, y, &used), 0x28) = 1000 + x / 8;
    for (int i = 0; i < cfg->units; i++) {
        int b = i % 4, x, y, tries = 0;
        if (cfg->packed && b == 0) {                                  /* a packed block: one unit per cell, standing */
            int side = 1; while (side * side < cfg->units / 4) side++;
            x = w->cx[0] - side / 2 + packed % side; y = w->cy[0] - side / 2 + packed / side; packed++;
            rect(w, x, y, 1, 1, 0);
            uint8_t *u = new_obj(w, tmpl[0], 100 + i, 0);              /* the movers' own army */
            F32(u, 0x38) = x * 10.0f + 5.0f; F32(u, 0x3c) = y * 10.0f + 5.0f;
            U8(u, 0x704) = 1; I32(u, 0x708) = 5; F32(u, 0x70c) = 20.0f;
            w->units[w->nunits++] = u;
            uint8_t *in = info_for(w, x, y, &used), *n = w->nodes + 12 * (2 * i);
            U32(n, 0) = U32(in, 0x20); U32(n, 8) = (uint32_t)(uintptr_t)u; U32(in, 0x20) = (uint32_t)(uintptr_t)n;
            n += 12; U32(n, 0) = U32(in, 0x14); U32(n, 8) = (uint32_t)(uintptr_t)u; U32(in, 0x14) = (uint32_t)(uintptr_t)n;
            continue;
        }
        do {
            int s = b == 3 ? 8 : 30;
            x = w->cx[b] + (int)(rnd() % (2 * s + 1)) - s; y = w->cy[b] + (int)(rnd() % (2 * s + 1)) - s;
        } while (++tries < 50 && (x < 2 || y < 2 || x >= W - 2 || y >= H - 2 || (U32(CELL(w, x, y), 0xc) & 0xf)));
        if (tries >= 50) continue;
        int team = b == 3 ? 7 : rnd() % 3 == 0 ? 0 : rnd() % 8 == 0 ? 9 : 2 + b;   /* 0 = the movers' side */
        uint8_t *u = new_obj(w, tmpl[rnd() % 3], 100 + i, team);
        F32(u, 0x38) = x * 10.0f + 1.0f + (float)(rnd() % 8); F32(u, 0x3c) = y * 10.0f + 1.0f + (float)(rnd() % 8);
        U8(u, 0x704) = rnd() % 5 < 2; I32(u, 0x708) = rnd() % 3 * 5; F32(u, 0x70c) = 15.0f + (float)(rnd() % 25);
        U8(u, 0x710) = rnd() & 1;
        w->units[w->nunits++] = u;
        uint8_t *in = info_for(w, x, y, &used), *n = w->nodes + 12 * (2 * i);
        U32(n, 0) = U32(in, 0x20); U32(n, 8) = (uint32_t)(uintptr_t)u; U32(in, 0x20) = (uint32_t)(uintptr_t)n;
        int gx = x + (int)(rnd() % 7) - 3, gy = y + (int)(rnd() % 7) - 3;
        if (gx < 2 || gy < 2 || gx >= W - 2 || gy >= H - 2) continue;
        in = info_for(w, gx, gy, &used); n += 12;
        U32(n, 0) = U32(in, 0x14); U32(n, 8) = (uint32_t)(uintptr_t)u; U32(in, 0x14) = (uint32_t)(uintptr_t)n;
        if (b < 3 && rnd() % 3 == 0) U16(gb, 0x14 * ((size_t)x * H + y) + 6) = 1;
    }
    /* movers: footprints of 1, 3, 4 and 9 cells (radius 0 / 1 / 2 / 4, parity 1 / 1 / 0 / 1) */
    static const int rad[4] = {0, 1, 2, 4}, par[4] = {1, 1, 0, 1};   /* 3: a horde's 9-cell footprint */
    for (int m = 0; m < 4; m++) {
        uint8_t *o = w->mover[m] = new_obj(w, tmpl[0], 50 + m, 0);
        U8(o, 0x710) = par[m]; F32(o, 0x70c) = 20.0f + 5 * m; I32(o, 0x708) = 5; I32(o, 0x714) = rad[m];
        if (m == 3 && w->nunits) U32(PTR(o, 0x260), 0x40) = (uint32_t)(uintptr_t)w->units[0];
    }
    memcpy(w->uinfo0, w->uinfo, w->uinfo_size);
    pw_reset_pool(w);
    return w;
}

/* the info pool's free list (0xdea438), all infos fresh, in an order that depends on the salt */
void pw_reset_pool(pw_t *w)
{
    memset(w->pool, 0, 0x3c * (size_t)NINFO);
    *AT(0xdea438) = 0;
    for (int k = 0; k < NINFO; k++) {
        int i = w->c.salt & 1 ? NINFO - 1 - k : k;
        uint8_t *in = w->pool + 0x3c * (size_t)i, *head = PTR(0xdea438, 0);
        U32(in, 0x38) = 0xdea438; U32(in, 0x34) = (uint32_t)(uintptr_t)head;
        if (head) U32(head, 0x38) = (uint32_t)(uintptr_t)in + 0x34;
        *AT(0xdea438) = (uint32_t)(uintptr_t)in;
    }
}

void pw_free(pw_t *w)
{
    for (int i = 0; i < w->nkeep; i++) free(w->keep[i]);
    free(w);
}

void pw_stats(pw_t *w, int *units, int *blocked)
{
    int b = 0;
    for (int x = 0; x < w->c.w; x++) for (int y = 0; y < w->c.h; y++) b += (U32(CELL(w, x, y), 0xc) & 0xf) != 0;
    *units = w->nunits; *blocked = b;
}

static uint64_t mix(uint64_t h, uint32_t v) { h ^= v; h *= 0x100000001b3ull; return h ^ (h >> 29); }

/* ---- one search, the way the game's findPath loop 0x6fd06f runs it --------------------------- */
typedef uint8_t *(TC *getcell_t)(void *, int, int, int);
typedef void (TC *alloc_t)(void *cell, const int *pos);                 /* 0x6ea019 */
typedef uint8_t (TC *start_t)(void *cell, void *goal);                  /* 0x934400 */
typedef void (TC *push_t)(void *pf, void *cell);                        /* 0x6f57a1 */
typedef uint8_t *(TC *pop_t)(void *pf);                                 /* 0x6f4af2 */
typedef void (TC *close_t)(void *cell, void *head);                     /* 0x934594 */
typedef void (TC *layers_t)(void *pf, void *cell, void *obj);           /* 0x6f6286 */
typedef int (TC *exam_t)(void *pf, void *cell, void *goal, void *loco, int bounds, int center, int radius,
                         void *unused, void *obj, int attack, void *waypoint);   /* 0x6f9850 */
typedef uint32_t (TC *ctg_t)(void *pf, void *cell, void *goal);         /* 0x6f1f0d */
typedef void (TC *clean_t)(void *pf);                                   /* 0x6f5519 */
typedef void (TC *release_t)(void *cell);                               /* 0x9347c6 */

/* stand-in for the move-away goal test (checkDestination 0x6f3082 and the other unit's path
 * corridor): no other unit stands in or heads for the mover's footprint there, and the footprint
 * clears a horizontal corridor through the start (the blocked path) */
void *pw_moveaway_pop;
static int free_spot(pw_t *w, int x, int y, int r, int c, int sy, uint8_t *obj)
{
    if (abs(y - sy) <= r + 3) return 0;
    for (int i = x - r; i < x + r + c; i++)
        for (int j = y - r; j < y + r + c; j++) {
            if (i < 0 || j < 0 || i >= w->c.w || j >= w->c.h) return 0;
            uint8_t *in = PTR(CELL(w, i, j), 0);
            if (!in) continue;
            for (int l = 0x14; l <= 0x20; l += 0xc)
                for (uint8_t *n = PTR(in, l); n; n = PTR(n, 0)) if (PTR(n, 8) != obj) return 0;
        }
    return 1;
}

void pw_search(pw_t *w, const pw_query *q, pw_result *r)
{
    uint8_t *P = w->pf, *obj = w->mover[q->mover];
    getcell_t gc = FN(getcell_t, 0x5e2e9c);
    uint8_t *start = gc(P, 1, q->sx, q->sy), *goal = q->moveaway ? NULL : gc(P, 1, q->gx, q->gy);
    int spos[2] = {q->sx, q->sy}, gpos[2] = {q->gx, q->gy};
    memset(r, 0, sizeof *r);
    uint64_t t0 = now_us();
    F32(obj, 0x38) = q->sx * 10.0f + 5.0f; F32(obj, 0x3c) = q->sy * 10.0f + 5.0f;
    int radius = I32(obj, 0x714), center = U8(obj, 0x710);
    U8(P, 0x38) = (U32(start, 0xc) & 0xf) != 0;                       /* as findPath: start blocked */
    *AT(0xde4b14) = 0;                                                 /* as findPath: jump-ahead steps */
    if (goal) FN(alloc_t, 0x6ea019)(goal, gpos);
    FN(alloc_t, 0x6ea019)(start, spos);
    FN(start_t, 0x934400)(start, NULL);
    if (goal) U16(PTR(start, 0), 0x10) = (uint16_t)FN(ctg_t, 0x6f1f0d)(P, start, goal);
    FN(push_t, 0x6f57a1)(P, start);
    uint64_t h = 0xcbf29ce484222325ull;
    uint8_t *c;
    pop_t pop = q->moveaway && pw_moveaway_pop ? (pop_t)pw_moveaway_pop : FN(pop_t, 0x6f4af2);
    while ((c = pop(P))) {
        uint8_t *in = PTR(c, 0);
        r->steps++;
        h = mix(mix(mix(h, I32(in, 0) << 16 | I32(in, 4)), U16(in, 0x10)), U16(in, 0x12) << 8 | (U32(in, 0x2c) & 0xff));
        if (c == goal || (q->moveaway && c != start && free_spot(w, I32(in, 0), I32(in, 4), radius, center, q->sy, obj))) {
            r->found = 1; goal = c; break;
        }
        FN(close_t, 0x934594)(c, P + 0x34);
        if (r->cells > q->limit) break;
        FN(layers_t, 0x6f6286)(P, c, obj);
        r->cells += FN(exam_t, 0x6f9850)(P, c, goal, PTR(obj, 0x260) + 0x1cc, 0, center, radius, NULL, obj, q->attack, NULL);
    }
    r->pops = h;
    h = 0xcbf29ce484222325ull;
    if (r->found) {
        uint8_t *in = PTR(goal, 0);
        r->cost = U16(in, 0x12);
        for (; in; in = PTR(in, 8)) { h = mix(h, I32(in, 0) << 16 | I32(in, 4)); r->pathlen++; }
    }
    r->path = h;
    h = 0xcbf29ce484222325ull;
    for (uint32_t *p = (uint32_t *)(uintptr_t)U32(P, 0x1d1f0); p < (uint32_t *)(uintptr_t)U32(P, 0x1d1f4); p++) {
        uint8_t *in = PTR((uintptr_t)*p, 0);
        h = mix(mix(h, I32(in, 0) << 16 | I32(in, 4)), U32(in, 0x10));
    }
    for (uint8_t *in = PTR(P, 0x34); in; in = PTR(in, 0x34)) h = mix(mix(h, I32(in, 0) << 16 | I32(in, 4)), U32(in, 0x10));
    r->lists = h;
    /* the game releases the closed cells' infos; the open ones stay on their cells (in the game
     * too). Released here so that every search starts from the same state. */
    int nopen = (int)((U32(P, 0x1d1f4) - U32(P, 0x1d1f0)) / 4);
    uint8_t **open = malloc(sizeof *open * (nopen + 1));
    memcpy(open, (void *)(uintptr_t)U32(P, 0x1d1f0), 4 * nopen);
    FN(clean_t, 0x6f5519)(P);
    for (int i = 0; i < nopen; i++) FN(release_t, 0x9347c6)(open[i]);
    free(open);
    if (goal) FN(release_t, 0x9347c6)(goal);
    r->us = now_us() - t0;
    int left = 0;                                                      /* infos no list holds any more */
    for (size_t i = 0; i < (size_t)w->c.w * w->c.h; i++) {
        uint8_t *c = w->cells + 16 * i, *in = PTR(c, 0);
        if (in >= w->pool && in < w->pool + 0x3c * (size_t)NINFO) { FN(release_t, 0x9347c6)(c); left++; }
    }
    r->leftover = left;
    /* the infos that stay (units' and obstacles') keep the costs, parent and flags this search
     * left, and the next search reads some of them (in the game too: its searches depend on the
     * ones before, the same way on every machine). Reset here so each search is independent. */
    memcpy(w->uinfo, w->uinfo0, w->uinfo_size);
}

/* start and goal pairs: [0] across the map, [1] into or through a battle, [2] into the closed base
 * (unreachable: the search runs to its cell limit) */
void pw_queries(pw_t *w, pw_query *q, int n, uint32_t seed)
{
    rng = seed | 1;
    for (int i = 0; i < n; i++) {
        int kind = i % 3, x, y, gx, gy;
        do {
            x = 4 + rnd() % (w->c.w - 8); y = 4 + rnd() % (w->c.h - 8);
            if (kind == 0) { gx = 4 + rnd() % (w->c.w - 8); gy = 4 + rnd() % (w->c.h - 8); }
            else { int b = kind == 1 ? rnd() % 3 : 3; gx = w->cx[b] + (int)(rnd() % 9) - 4; gy = w->cy[b] + (int)(rnd() % 9) - 4; }
        } while ((U32(CELL(w, x, y), 0xc) & 0xf) || (U32(CELL(w, gx, gy), 0xc) & 0xf) || abs(gx - x) + abs(gy - y) < 60);
        q[i] = (pw_query){x, y, gx, gy, (int)(rnd() % 4), (int)(rnd() & 1), 15000, 0};
    }
}

/* [3]: the original checkForMovement / crowd cost against the patch's, called directly on random
 * crowded cells with random movement-info settings; one memo for all calls of a mover (the world
 * does not change), so most calls of the patched versions answer from the memo */
typedef uint8_t (TC *cfm_t)(void *pf, void *obj, void *m, const int *pp);
typedef int (TC *crowd_t)(void *pf, void *obj, void *cell, const int *pos, int r, int r2, int flag);
uint8_t TC gp_pf_cfm(uint8_t *pf, uint8_t *obj, uint8_t *m, const int *pp);
int TC gp_pf_crowd(uint8_t *pf, uint8_t *obj, uint8_t *pcell, const int *pos, int r, int r2, int flag);

int pw_direct(pw_t *w, uint32_t seed, int n, int *bad_cfm, int *bad_crowd)
{
    rng = seed | 1;
    int nonzero = 0;
    *bad_cfm = *bad_crowd = 0;
    for (int i = 0; i < n; i++) {
        int b = rnd() % 4, x = w->cx[b] + (int)(rnd() % 61) - 30, y = w->cy[b] + (int)(rnd() % 61) - 30;
        int pp[2] = {x + (int)(rnd() % 3) - 1, y + (int)(rnd() % 3) - 1}, pos[2] = {x, y};
        uint8_t *obj = w->mover[rnd() % 4], m[2][0x40];
        if (x < 1 || y < 1 || x >= w->c.w - 1 || y >= w->c.h - 1) continue;
        memset(m[0], 0xcd, 0x40);
        I32(m[0], 0) = x; I32(m[0], 4) = y; I32(m[0], 8) = 1; I32(m[0], 0xc) = rnd() % 4;
        U8(m[0], 0x10) = rnd() & 1; U8(m[0], 0x11) = rnd() % 4 == 0;
        static const uint8_t fl[6] = {0x1c, 0x0c, 0x12, 0x03, 0x11, 0x1e};
        U32(m[0], 0x14) = fl[rnd() % 6]; U32(m[0], 0x18) = rnd() % 3 ? 0 : 100 + rnd() % (w->nunits + 1);
        U32(m[0], 0x1c) = 1; U8(m[0], 0x20) = rnd() & 1; U8(m[0], 0x21) = rnd() & 1; I32(m[0], 0x24) = 3;
        U8(m[0], 0x28) = rnd() & 1;
        memcpy(m[1], m[0], 0x40);
        uint8_t ra = FN(cfm_t, 0x6ebaa0)(w->pf, obj, m[0], pp);
        uint8_t rb = gp_pf_cfm(w->pf, obj, m[1], pp);
        if (ra != rb || memcmp(m[0], m[1], 0x40)) { if ((*bad_cfm)++ < 3) printf("  cfm mismatch at %d,%d: %d vs %d\n", x, y, ra, rb); }
        int r = rnd() % 4, r2 = r + (rnd() & 1), flag = rnd() % 5 ? 1 : 0;
        uint8_t *pc = CELL(w, pp[0], pp[1]);
        int ca = FN(crowd_t, 0x6ed21e)(w->pf, obj, pc, pos, r, r2, flag);
        int cb = gp_pf_crowd(w->pf, obj, pc, pos, r, r2, flag);
        nonzero += ca != 0;
        if (ca != cb) { if ((*bad_crowd)++ < 3) printf("  crowd mismatch at %d,%d: %d vs %d\n", x, y, ca, cb); }
    }
    return nonzero;
}

/* move-away searches from units inside the packed block (battle 0), and from its edge */
void pw_moveaways(pw_t *w, pw_query *q, int n, uint32_t seed)
{
    rng = seed | 1;
    int side = 1; while (side * side < w->c.units / 4) side++;
    for (int i = 0; i < n; i++) {
        int d = i / 4 % 2 ? side / 2 - 2 : (int)(rnd() % (side / 2 + 1));  /* every other round: the edge */
        int x = w->cx[0] + (int)(rnd() % (2 * d + 1)) - d, y = w->cy[0] + (rnd() & 1 ? d : -d);
        q[i] = (pw_query){x, y, x, y, i % 4, 0, 1 << 30, 1};
    }
}

/* [7]: aiMoveAwayFromUnit and findObjectByID stood in for; orders logged as (ally ID, mover ID,
 * x, queue run) */
static uint32_t olog[64][4]; static int on_, orun;
static void TC s_order(uint8_t *cmd, uint8_t *mover, const float *pos, int src)
{
    if (on_ < 64) { olog[on_][0] = U32(PTR(cmd - 0x20, 8), 0x74); olog[on_][1] = U32(mover, 0x74); olog[on_][2] = (uint32_t)pos[0]; olog[on_][3] = orun + 10 * src; on_++; }
}
static pw_t *bw;
static int gone = -1;
static uint8_t *TC s_byid(void *logic, uint32_t id)
{
    (void)logic;
    int i = (int)id - 100;
    return i >= 0 && i < bw->nunits && i != gone ? bw->units[i] : NULL;
}
int pw_maq_test(pw_t *w)
{
    bw = w;
    gp_va_offset = OFF;
    int ok = gp_patch_moveawayqueue();
    gp_va_offset = 0;
    if (!ok) return 0;
    jmp_to(0x66c66e, (void *)s_order); jmp_to(0x449681, (void *)s_byid);
    /* mover 110 orders allies 100..105 and mover 111 orders 106..108 in queue run 1; 103 has gone
     * by the time its turn comes. Expected: 2 + 2 at once, then 102 (103 dropped), 104 105, 108 */
    static const uint32_t want[8][4] = {{100, 110, 0, 1}, {101, 110, 1, 1}, {106, 111, 0, 1}, {107, 111, 1, 1},
        {102, 110, 2, 2}, {104, 110, 4, 3}, {105, 110, 5, 3}, {108, 111, 2, 4}};
    for (int pass = 0; pass < 2; pass++) {
        on_ = 0; orun = 0; gone = 3;
        gp_maq_run(); orun++;
        for (int k = 0; k < 9; k++) {
            float pos[3] = {(float)(k < 6 ? k : k - 6), 0, 0};
            gp_maq_order(PTR(w->units[k], 0x260) + 0x20, w->units[k < 6 ? 10 : 11], pos, 2);
        }
        for (int r = 0; r < 4; r++) { orun++; gp_maq_run(); }
        int bad = on_ != 8;
        for (int i = 0; i < on_ && i < 8; i++) bad |= olog[i][0] != want[i][0] || olog[i][1] != want[i][1] ||
                                                     olog[i][2] != want[i][2] || olog[i][3] != want[i][3] + 20;
        if (bad) { for (int i = 0; i < on_; i++) printf("  order %u %u %u %u\n", olog[i][0], olog[i][1], olog[i][2], olog[i][3]); return 0; }
    }
    return 1;
}
