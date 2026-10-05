/* t_flatlight: flattenlight (p_flatlight.c) against the original, both running the exe's own code.
 * Two relocated copies of .text (one patched by the installer, with its byte and hash checks; one
 * untouched); .rdata/.data at their own addresses. Each copy gets its own world, built from the same
 * seed: a 510x510 height grid (16-bit, border 5, smooth hills), 531 road segments of 60-180 units
 * along random walks (~13,600 vertices, as the road points of "mp eastfarthing hills" give), a scene
 * light list (point lights and one directional), three global lights and the height tint. The game's
 * code runs everything from setRawMapHeight 0x49172d through staticLightingChanged 0x4e0b69 /
 * 0x467bf9, W3DRoadBuffer::updateLighting 0x4d4297, updateSegLighting 0x4d3e5f, the terrain diffuse
 * 0x46acd7 (normal 0x46a250, doTheLight 0x468cc0, light iterator, Get_Position) to the vertex colour.
 * Stand-ins: flattenTerrain 0x684cba (a test function with the original's per-cell order: the cell,
 * then its 8 neighbours, target = min(rounded mean height, centre height)), the memory allocator,
 * no terrain tiles (0x3890 = 0), no water (0xdc7a40 = 0), 0xde3c24 = 0.
 *   [0] the patch applies; both flattenTerrain call sites and the relight call go to its stubs
 *   [1] 16 flattens on roads, lights moved between them, per light count 0 / 16: after each, heights,
 *       every road vertex (all 36 bytes), the render object and the road buffer are identical;
 *       relights counted; the flattens must change some road colours, and (16 lights) changing the
 *       lights must change some (else the test proves nothing)
 *   [2] a flatten that lowers nothing; setRawMapHeight outside a flatten (relit at once)
 *   [3] sensitivity: the end-of-flatten relight suppressed -> road colours differ
 *   [4] time per flatten, original -> patched
 * usage: t_flatlight.exe <path to lotrbfme2ep1.exe 2.02> [flattens per light count, 16] */
#include "orig.h"
#include "gp_render.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>

#define TC __attribute__((thiscall))
#define AT(va) ((uint32_t *)(uintptr_t)(va))
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define F32(p, o) (*(float *)((uint8_t *)(p) + (o)))
enum { W = 510, BORDER = 5, NSEG = 531, MAXL = 17, RSIZE = 0x4000, NFL = 16 };
static int NFLAT = NFL;

static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
static float frand(float a, float b) { return a + (b - a) * (rnd() % 100000) / 100000.0f; }

static uint32_t off[2];                  /* 0: original, 1: patched */
static LONG nrel[2];
typedef void (TC *slc_t)(void *r, int arg);
typedef void (TC *setraw_t)(void *tv, int *cell, int h);
typedef void (TC *flat_t)(void *tl, void *req);
static void TC slc0(void *r, int a) { nrel[0]++; ((slc_t)(uintptr_t)(0x4e0b69 + off[0]))(r, a); }
static void TC slc1(void *r, int a) { nrel[1]++; ((slc_t)(uintptr_t)(0x4e0b69 + off[1]))(r, a); }

typedef struct {
    int k, nl, nvert;
    uint8_t *R, *H, *TV, *S, *RB, *segs, *verts, *nodes, *lights;
    uint16_t *hts;
    void *rvt[0x100], *tvt[0x40], *lvt[0x20];
} world;
typedef struct { int cx, cy, half; world *w; int lowered, keep; } fl_req;   /* keep: target above all */

static void *__cdecl t_alloc(uint32_t n, int a, int b) { (void)a; (void)b; return calloc(1, n); }
static void __cdecl t_free(void *p, int a) { (void)a; free(p); }

/* the stand-in for flattenTerrain 0x684cba: same calls of setRawMapHeight, same order */
static void TC flatten(void *tl, fl_req *q)
{
    (void)tl;
    world *w = q->w;
    double sum = 0; int n = 0;
    for (int y = q->cy - q->half; y < q->cy + q->half; y++)
        for (int x = q->cx - q->half; x < q->cx + q->half; x++) { sum += w->hts[(y + BORDER) * W + x + BORDER]; n++; }
    int target = (int)floor(sum / n + 0.5), c = w->hts[(q->cy + BORDER) * W + q->cx + BORDER];
    if (c < target) target = c;
    if (q->keep) target = 0xffff;
    static const int d[9][2] = {{0,0},{-1,0},{1,0},{0,-1},{0,1},{-1,-1},{1,1},{1,-1},{-1,1}};
    for (int y = q->cy - q->half; y < q->cy + q->half; y++)
        for (int x = q->cx - q->half; x < q->cx + q->half; x++)
            for (int k = 0; k < 9; k++) {
                int cell[2] = {x + d[k][0], y + d[k][1]};
                if (w->hts[(cell[1] + BORDER) * W + cell[0] + BORDER] > target) q->lowered++;
                ((setraw_t)w->tvt[0x88 / 4])(w->TV, cell, target);
            }
}

static void jmp_to(uint32_t va, void *target)
{
    uint8_t *p = (uint8_t *)(uintptr_t)va;
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)target - (va + 5));
    p[0] = 0xe9; memcpy(p + 1, &rel, 4);
}
static uint32_t call_target(uint32_t va)
{
    const uint8_t *p = (const uint8_t *)(uintptr_t)va;
    int32_t rel; memcpy(&rel, p + 1, 4);
    return p[0] == 0xe8 ? va + 5 + rel : 0;
}

static float height_at(float x, float y)  /* raw 16-bit units; ~0.04 world units each */
{
    return 1900 + 700 * sinf(x * 0.031f) + 500 * cosf(y * 0.043f) + 300 * sinf((x + y) * 0.087f)
           + 120 * sinf(x * 0.29f) * cosf(y * 0.23f);
}

static void build(world *w, int k, int nl, uint32_t seed)
{
    memset(w, 0, sizeof *w);
    w->k = k; w->nl = nl; rs = seed;
    w->hts = calloc(W * W, 2);
    for (int y = 0; y < W; y++) for (int x = 0; x < W; x++)
        w->hts[y * W + x] = (uint16_t)(height_at(x, y) + rnd() % 40);
    w->H = calloc(1, 0x40);
    U32(w->H, 8) = W; U32(w->H, 0xc) = W; U32(w->H, 0x10) = BORDER; U32(w->H, 0x20) = W * W;
    U32(w->H, 0x24) = (uint32_t)(uintptr_t)w->hts;
    /* roads: chains of straight segments, two vertices (the edges) per 10 units of length */
    w->segs = calloc(NSEG, 0xbc);
    w->verts = calloc(NSEG * 2 * (MAXL + 2), 0x24);
    float x = 0, y = 0, a = 0, lim = (W - 2 * BORDER) * 10.0f - 40;
    for (int s = 0; s < NSEG; s++) {
        if (s % 10 == 0) { x = frand(200, lim - 200); y = frand(200, lim - 200); a = frand(0, 6.283f); }
        a += frand(-0.5f, 0.5f);
        float len = frand(60, 180), dx = cosf(a), dy = sinf(a);
        if (x + dx * len < 40 || x + dx * len > lim || y + dy * len < 40 || y + dy * len > lim) { a += 3.1416f; dx = -dx; dy = -dy; }
        int cols = (int)(len / 10) + 1;
        uint8_t *seg = w->segs + 0xbc * s, *v0 = w->verts + 0x24 * w->nvert;
        for (int c = 0; c < cols; c++) {
            float t = len * c / (cols - 1), px = x + dx * t, py = y + dy * t;
            for (int e = 0; e < 2; e++) {
                uint8_t *v = w->verts + 0x24 * w->nvert++;
                F32(v, 0) = px + (e ? 15 : -15) * -dy; F32(v, 4) = py + (e ? 15 : -15) * dx;
                F32(v, 0x1c) = t / 64; F32(v, 0x20) = (float)e;
            }
        }
        U32(seg, 0x58) = 2 * cols; U32(seg, 0x5c) = (uint32_t)(uintptr_t)v0;
        x += dx * len; y += dy * len;
    }
    w->RB = calloc(1, 0x80);
    U32(w->RB, 4) = (uint32_t)(uintptr_t)w->segs; U32(w->RB, 8) = NSEG; ((uint8_t *)w->RB)[0xc] = 1;
    /* the scene's light list: node +4 next, +0xc the light + 8; the list's end is list + 4 */
    w->S = calloc(1, 0x200);
    w->lights = calloc(nl + 1, 0x200);
    w->nodes = calloc(nl + 1, 0x10);
    for (int i = 0; i < 0x20; i++) w->lvt[i] = (void *)(uintptr_t)(0x53b320 + off[k]);   /* the transform check */
    uint8_t *list = w->S + 0x8c, *prev = NULL;
    for (int i = 0; i <= nl; i++) {
        uint8_t *L = w->lights + 0x200 * i, *n = w->nodes + 0x10 * i;
        U32(L, 0) = (uint32_t)(uintptr_t)w->lvt;
        U32(L, 0xc4) = i == nl ? 1 : (i % 3 == 2 ? 2 : 0);              /* point, spot, directional */
        F32(L, 0x24) = frand(500, lim - 500); F32(L, 0x34) = frand(500, lim - 500); F32(L, 0x44) = frand(60, 200);
        F32(L, 0x20) = 0.3f; F32(L, 0x30) = -0.5f; F32(L, 0x40) = -0.8f;
        F32(L, 0x100) = frand(10, 60); F32(L, 0x104) = frand(150, 600);
        for (int c = 0; c < 3; c++) {                    /* dim: the sum stays below saturation */
            F32(L, 0xd4 + 4 * c) = i == nl ? 0 : frand(0, 0.02f); F32(L, 0xe0 + 4 * c) = i == nl ? 0.1f : frand(0.05f, 0.3f);
        }
        U32(n, 0xc) = (uint32_t)(uintptr_t)(L + 8);
        if (prev) U32(prev, 4) = (uint32_t)(uintptr_t)n; else U32(list, 8) = (uint32_t)(uintptr_t)n;
        prev = n;
    }
    U32(prev, 4) = (uint32_t)(uintptr_t)(list + 4);
    /* the terrain render object and the terrain visual */
    w->R = calloc(1, RSIZE);
    w->rvt[0x224 / 4] = k ? (void *)slc1 : (void *)slc0;
    w->rvt[0x244 / 4] = (void *)(uintptr_t)(0x46a575 + off[k]);
    w->rvt[0x24c / 4] = (void *)(uintptr_t)(0x4e0f5d + off[k]);
    U32(w->R, 0) = (uint32_t)(uintptr_t)w->rvt;
    U32(w->R, 0x78) = (uint32_t)(uintptr_t)w->S;
    U32(w->R, 0x37c0) = (uint32_t)(uintptr_t)w->H;
    U32(w->R, 0x386c) = (uint32_t)(uintptr_t)w->RB;
    ((uint8_t *)w->R)[0x37c4] = 1;
    F32(w->R, 0x37c8) = 0.3f; F32(w->R, 0x37cc) = 0.4f; F32(w->R, 0x37d0) = 0.5f;
    w->TV = calloc(1, 0x40);
    w->tvt[0x88 / 4] = (void *)(uintptr_t)(0x49172d + off[k]);
    U32(w->TV, 0) = (uint32_t)(uintptr_t)w->tvt;
    U32(w->TV, 0x14) = (uint32_t)(uintptr_t)w->R; U32(w->TV, 0x1c) = (uint32_t)(uintptr_t)w->H;
}
static void unbuild(world *w)
{
    free(w->hts); free(w->H); free(w->segs); free(w->verts); free(w->RB); free(w->S); free(w->lights);
    free(w->nodes); free(w->R); free(w->TV);
}
static void use(world *w) { *AT(0xdc78ec) = (uint32_t)(uintptr_t)w->R; }
static void relight_all(world *w) { use(w); ((slc_t)w->rvt[0x224 / 4])(w->R, 0); }

static int same(world *a, world *b)
{
    if (memcmp(a->hts, b->hts, W * W * 2) || a->nvert != b->nvert || memcmp(a->verts, b->verts, 0x24 * a->nvert)) return 0;
    for (int o = 4; o < RSIZE; o += 4)
        if (o != 0x78 && o != 0x37c0 && o != 0x386c && U32(a->R, o) != U32(b->R, o)) return 0;
    for (int o = 0; o < 0x80; o += 4) if (o != 4 && U32(a->RB, o) != U32(b->RB, o)) return 0;
    return 1;
}
static void move_lights(world *w, uint32_t seed)
{
    rs = seed;
    for (int i = 0; i < w->nl; i++) if (rnd() % 3 == 0) {
        uint8_t *L = w->lights + 0x200 * i;
        F32(L, 0x24) += frand(-80, 80); F32(L, 0x34) += frand(-80, 80); F32(L, 0x104) = frand(150, 600);
    }
}

static int flat_call(world *w, fl_req *q, int site)
{
    q->w = w; q->lowered = 0; use(w);
    uint32_t fn = w->k ? call_target((site ? 0x8ad801 : 0x88d5ab) + off[1]) : 0x684cba + off[0];
    ((flat_t)(uintptr_t)fn)((void *)0x1234, q);
    return q->lowered;
}

static LONG WINAPI crash(EXCEPTION_POINTERS *e)
{
    CONTEXT *c = e->ContextRecord;
    printf("CRASH %08lx at %p (off %08x / %08x) eax %08lx ecx %08lx esi %08lx edi %08lx\nFAIL\n",
           e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress, off[0], off[1], c->Eax,
           c->Ecx, c->Esi, c->Edi);
    ExitProcess(3);
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    SetUnhandledExceptionFilter(crash);
    if (!VirtualAlloc((void *)0xbd0000, 0xe10000 - 0xbd0000, MEM_RESERVE, PAGE_READWRITE)) {
        printf("cannot reserve the image's data range\nFAIL\n"); return 2;
    }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (argc > 2 && atoi(argv[2]) > 0) NFLAT = atoi(argv[2]);
    if (orig_map_at(0xbd0000, 0x1b9000, 0) || orig_map_at(0xd89000, 0x81000, 0)) return 2;
    for (int k = 0; k < 2; k++)
        if (!(off[k] = orig_reserve_image()) || orig_map_at(0x401000, 0x7cf000, off[k])) return 2;
    *AT(0xdc5e44) = (uint32_t)(uintptr_t)t_alloc; *AT(0xdc5e3c) = (uint32_t)(uintptr_t)t_free;
    *AT(0xde3c24) = 0; *AT(0xdc7a40) = 0;
    static uint8_t gd[0x1000];                           /* TheGlobalData: three lights, ambient */
    U32(gd, 0x988) = 3;
    static const float dir[3][3] = {{-0.6f, 0.4f, -0.7f}, {0.5f, 0.6f, -0.62f}, {0.1f, -0.9f, -0.42f}};
    static const float dif[3][3] = {{0.45f, 0.42f, 0.38f}, {0.15f, 0.15f, 0.2f}, {0.1f, 0.12f, 0.1f}};
    for (int i = 0; i < 3; i++) for (int c = 0; c < 3; c++) {
        F32(gd, 0x920 + 12 * i + 4 * c) = dir[i][c]; F32(gd, 0x8fc + 12 * i + 4 * c) = dif[i][c];
        F32(gd, 0x944 + 4 * c) = 0.9f; F32(gd, 0x8d8 + 4 * c) = 0.18f + 0.02f * c;   /* below saturation */
    }
    F32(gd, 0x74) = 12.0f;                               /* the height tint: the lowest vertices only */
    *AT(0xde4364) = (uint32_t)(uintptr_t)gd;
    unsigned short cw = 0x007f;                          /* the game's FPU mode: 24-bit, nearest */
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));

    gp_va_offset = off[1];
    int ok = gp_patch_flattenlight();
    gp_va_offset = 0;
    uint32_t t1 = call_target(0x88d5ab + off[1]), t2 = call_target(0x8ad801 + off[1]), t3 = call_target(0x491772 + off[1]);
    ok = ok && t1 == (uint32_t)(uintptr_t)gp_fl_flatten && t2 == t1 && t3 == (uint32_t)(uintptr_t)gp_fl_relight
         && gp_fl_fn == 0x684cba + off[1];
    verdict(!ok, "[0] flattenlight: %s (call sites -> %08x %08x, relight -> %08x)\n", ok ? "applied" : "NOT applied", t1, t2, t3);
    if (!ok) { printf("FAIL\n"); return 1; }
    for (int k = 0; k < 2; k++) jmp_to(0x684cba + off[k], (void *)flatten);

    static world wa, wb;
    for (int cfg = 0; cfg < 2; cfg++) {
        int nl = cfg ? 16 : 0;
        build(&wa, 0, nl, 0x9e3779b9u); build(&wb, 1, nl, 0x9e3779b9u);
        relight_all(&wa); relight_all(&wb);
        int bad = !same(&wa, &wb), changed = 0, lowered = 0, mism = 0, nlow = 0;
        LONG r0 = nrel[0], r1 = nrel[1];
        double ta = 0, tb = 0, maxa = 0, maxb = 0;
        uint32_t *before = malloc(4 * wa.nvert);
        for (int f = 0; f < NFLAT; f++) {
            rs = 0x51ed2701u + f * 7919;
            uint8_t *v = wa.verts + 0x24 * (rnd() % wa.nvert);
            fl_req q = {(int)(F32(v, 0) / 10), (int)(F32(v, 4) / 10), 3 + (int)(rnd() % 4), NULL, 0, 0};
            for (int i = 0; i < wa.nvert; i++) before[i] = U32(wa.verts, 0x24 * i + 0x18);
            uint64_t t0 = now_us();
            int lw = flat_call(&wa, &q, 0);
            lowered += lw; nlow += lw > 0;
            double d = (now_us() - t0) / 1000.0; ta += d; if (d > maxa) maxa = d;
            t0 = now_us();
            flat_call(&wb, &q, f & 1);
            d = (now_us() - t0) / 1000.0; tb += d; if (d > maxb) maxb = d;
            for (int i = 0; i < wa.nvert; i++) changed += before[i] != U32(wa.verts, 0x24 * i + 0x18);
            if (!same(&wa, &wb)) { if (mism++ < 3) printf("  MISMATCH after flatten %d at %d,%d\n", f, q.cx, q.cy); bad = 1; }
            move_lights(&wa, 77 + f); move_lights(&wb, 77 + f);
        }
        free(before);
        LONG ra = nrel[0] - r0, rb = nrel[1] - r1;
        int lit = 0;                                     /* the relight reads the scene lights */
        if (nl) {
            uint32_t *c0 = malloc(4 * wa.nvert);
            for (int i = 0; i < wa.nvert; i++) c0[i] = U32(wa.verts, 0x24 * i + 0x18);
            for (int i = 0; i < nl; i++) F32(wa.lights + 0x200 * i, 0x104) *= 0.5f;
            relight_all(&wa);
            for (int i = 0; i < wa.nvert; i++) lit += c0[i] != U32(wa.verts, 0x24 * i + 0x18);
            free(c0);
        }
        if (nl) verdict(!lit, "    the scene lights' ranges halved and relit: %d road colours change\n", lit);
        verdict(bad || changed == 0 || rb != nlow || gp_fl_obj || gp_fl_depth,
                "[1] %d scene lights, %d road vertices: %d flattens (footprints 6-12 cells square on roads, lights "
                "moved between): %d mismatches; relights %ld -> %ld (%d cells lowered); %d vertex colours changed\n",
                nl, wa.nvert, NFLAT, mism, ra, rb, lowered, changed);
        verdict(0, "[4] %d scene lights: per flatten %.1f -> %.1f ms (slowest %.0f -> %.1f ms); one relight %.1f ms\n",
                nl, ta / NFLAT, tb / NFLAT, maxa, maxb, ta / ra);

        if (cfg == 0) {
            /* [2] a flatten whose target is above every cell (all 9 calls per cell, nothing lowered); then a single setRawMapHeight outside a flatten */
            rs = 0x51ed2701u + (NFLAT - 1) * 7919;
            uint8_t *v = wa.verts + 0x24 * (rnd() % wa.nvert);
            fl_req q = {(int)(F32(v, 0) / 10), (int)(F32(v, 4) / 10), 3 + (int)(rnd() % 4), NULL, 0, 0};
            r0 = nrel[0]; r1 = nrel[1];
            q.keep = 1; flat_call(&wa, &q, 0); flat_call(&wb, &q, 1); q.keep = 0;
            int nothing = nrel[0] == r0 && nrel[1] == r1 && same(&wa, &wb);
            int cell[2] = {q.cx + 20, q.cy}, h = wa.hts[(q.cy + BORDER) * W + q.cx + 20 + BORDER] - 50;
            LONG once = gp_fl_stats[3];
            use(&wa); ((setraw_t)wa.tvt[0x88 / 4])(wa.TV, cell, h);
            use(&wb); ((setraw_t)wb.tvt[0x88 / 4])(wb.TV, cell, h);
            int direct = nrel[0] - r0 == 1 && nrel[1] - r1 == 1 && gp_fl_stats[3] == once + 1 && same(&wa, &wb);
            verdict(!nothing || !direct, "[2] a flatten that lowers nothing: %s; setRawMapHeight outside a flatten: %s\n",
                    nothing ? "no relight, identical" : "DIFFERENT", direct ? "relit at once, identical" : "DIFFERENT");

            /* [3] sensitivity: the relight at the flatten's end left out (until a flatten changes a colour) */
            int diff = 0, tries = 0;
            while (!diff && tries < 20) {
                v = wa.verts + 0x24 * ((wa.nvert / 20) * tries++ + 7);
                q.cx = (int)(F32(v, 0) / 10); q.cy = (int)(F32(v, 4) / 10);
                flat_call(&wa, &q, 0);
                gp_fl_depth = 1; flat_call(&wb, &q, 0); gp_fl_depth = 0; gp_fl_obj = NULL;
                for (int i = 0; i < wa.nvert; i++) diff += U32(wa.verts, 0x24 * i + 0x18) != U32(wb.verts, 0x24 * i + 0x18);
            }
            verdict(diff == 0, "[3] sensitivity: without the end relight %d of %d road colours differ (try %d)\n",
                    diff, wa.nvert, tries);
        }
        unbuild(&wa); unbuild(&wb);
    }
    printf("stats: %ld flattens, %ld relights folded into %ld, %ld at once\n", gp_fl_stats[0], gp_fl_stats[1],
           gp_fl_stats[2], gp_fl_stats[3]);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
