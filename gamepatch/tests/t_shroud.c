/* t_shroud: shroudspan (p_shroud.c) against the original span updaters, both run from the exe's bytes.
 * Two relocated copies of the shroud code (0xb4e000-0xb53000 and the predicate page 0x587000): one
 * patched by the installer (byte and hash checks as in the game), one untouched. Each runs on its own
 * copy of the same mock shroud grid (64 x 48 cells of 0xa8 bytes: 20 player words with counts biased
 * to the status edges 0, 1, 0xfffe, 0xffff, layer words, object lists in some cells), and afterwards
 * the grids, the objects' cached-status words, and the logs of every refresh callback and predicate
 * call (arguments and order) must be identical.
 *   [0] the patch applies to the original bytes (relocated copy)
 *   [1] random spans (+1, -1, layer add): any x0/x1/y incl. outside the grid and x1 < x0, any mask,
 *       the constant-true predicate and a recording, sometimes-false one, amounts past both clamps
 *   [2] whole circles through the original raster 0xb50100 (which calls the span updater), radius 0-20
 *   [3] time: one span of 21 cells; one circle of radius 10 and 15 (1 and 4 player bits)
 * usage: t_shroud.exe <path to lotrbfme2ep1.exe 2.02> [thousands of random spans] */
#include "orig.h"
#include "gp_scale.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs = 0x2545f491;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }

enum { W = 64, H = 48, NOBJ = 300 };
typedef struct { uint8_t mgr[0x80]; uint8_t el[W * H][0xa8]; uint8_t obj[NOBJ][0x80]; uint32_t node[NOBJ][4];
                 uint32_t log[4096]; int nlog; } world;
static world *wa, *wb, *cur;

static void __cdecl refresh(int x, int y, int status)
{
    if (cur->nlog + 3 <= 4096) { cur->log[cur->nlog++] = x; cur->log[cur->nlog++] = y; cur->log[cur->nlog++] = status; }
}
static char __attribute__((thiscall)) pred_some(void *self, int x, int y)
{
    (void)self;
    if (cur->nlog + 3 <= 4096) { cur->log[cur->nlog++] = 0x70000000u | (x & 0xfff); cur->log[cur->nlog++] = y; cur->nlog++; }
    return ((x * 7 + y * 13) % 5) != 0;
}
static void *vt_some[1] = {(void *)pred_some};
static void *vt_true[1];               /* the relocated 0x5879b0 of the patched copy */

static uint16_t edgy(void)
{
    static const uint16_t e[] = {0, 1, 2, 0xfffd, 0xfffe, 0xffff};
    return rnd() & 1 ? e[rnd() % 6] : (uint16_t)rnd();
}
static void fill(world *w)
{
    memset(w, 0, sizeof *w);
    *(int *)(w->mgr + 0x24) = W; *(int *)(w->mgr + 0x28) = H;
    *(uint8_t **)(w->mgr + 0x2c) = &w->el[0][0];
    *(int *)(w->mgr + 0x64) = rnd() % 4;
    *(void **)(w->mgr + 0x6c) = (void *)refresh;
    for (int c = 0; c < W * H; c++) for (int k = 4; k < 0xa8; k += 2) *(uint16_t *)&w->el[c][k] = edgy();
    for (int i = 0; i < NOBJ; i++) {                   /* node: [1] object, [3] next */
        int c = rnd() % (W * H);
        memset(w->obj[i], 0x5a, sizeof w->obj[i]);
        w->node[i][1] = (uint32_t)(uintptr_t)w->obj[i];
        w->node[i][3] = *(uint32_t *)w->el[c];
        *(uint32_t *)w->el[c] = (uint32_t)(uintptr_t)w->node[i];
    }
}
/* the same world at another address: pointers rebased */
static void clone(world *d, const world *s)
{
    memcpy(d, s, sizeof *d);
    intptr_t delta = (uint8_t *)d - (const uint8_t *)s;
    *(uint8_t **)(d->mgr + 0x2c) += delta;
    for (int c = 0; c < W * H; c++) if (*(uint32_t *)d->el[c]) *(uint32_t *)d->el[c] += delta;
    for (int i = 0; i < NOBJ; i++) { d->node[i][1] += delta; if (d->node[i][3]) d->node[i][3] += delta; }
}
static int same(void)
{
    if (wa->nlog != wb->nlog || memcmp(wa->log, wb->log, wa->nlog * 4)) return 0;
    for (int c = 0; c < W * H; c++) if (memcmp(wa->el[c] + 4, wb->el[c] + 4, 0xa8 - 4)) return 0;
    return !memcmp(wa->obj, wb->obj, sizeof wa->obj);
}

typedef uint32_t (__attribute__((thiscall)) *span_fn)(void *v, int x0, int x1, int y);
typedef char (__cdecl *raster_fn)(int x, int y, int r, void *vt, void *mgr, uint32_t mask);
static uint32_t offa, offb;      /* a: original, b: patched */

static uint32_t call_span(int which, int patched, void *v, int x0, int x1, int y)
{
    static const uint32_t va[3] = {0xb4fc80, 0xb4fd20, 0xb4fdc0};
    span_fn f = (span_fn)(uintptr_t)(va[which] + (patched ? offb : offa));
    return f(v, x0, x1, y);
}

static LONG WINAPI crash(EXCEPTION_POINTERS *e)
{
    CONTEXT *c = e->ContextRecord;
    printf("CRASH %08lx at %p (a %08x b %08x) eax %08lx ecx %08lx edx %08lx esi %08lx edi %08lx\nFAIL\n",
           e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress, offa, offb, c->Eax, c->Ecx,
           c->Edx, c->Esi, c->Edi);
    ExitProcess(3);
}
static int randint(int lo, int hi) { return lo + (int)(rnd() % (uint32_t)(hi - lo + 1)); }

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    SetUnhandledExceptionFilter(crash);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    long nspans = (argc > 2 ? atol(argv[2]) : 400) * 1000;
    offa = orig_reserve_image(); offb = orig_reserve_image();
    if (!offa || !offb) return 2;
    for (int k = 0; k < 2; k++) {
        uint32_t off = k ? offb : offa;
        if (orig_map_at(0xb4e000, 0x5000, off) || orig_map_at(0x587000, 0x1000, off)) return 2;
    }
    gp_va_offset = offb;
    int ok = gp_patch_shroudspan();
    gp_va_offset = 0;
    verdict(!ok, "[0] shroudspan: %s to the original bytes (relocated copy)\n", ok ? "applied" : "NOT applied");
    if (!ok) { printf("FAIL\n"); return 1; }
    vt_true[0] = (void *)(uintptr_t)(0x5879b0 + offb);
    wa = VirtualAlloc(NULL, sizeof(world), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    wb = VirtualAlloc(NULL, sizeof(world), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);

    /* [1] random spans */
    long bad = 0, n = 0, changes0 = gp_shr_stats[2];
    for (long it = 0; it < nspans; it++) {
        if (it % 2000 == 0) { fill(wa); clone(wb, wa); }
        int which = rnd() % 3, x0, x1, y = randint(-3, H + 2);
        x0 = randint(-6, W + 4); x1 = rnd() % 4 ? x0 + randint(-2, 30) : randint(-6, W + 4);
        uint32_t mask = rnd() % 3 ? (1u << (rnd() % 20)) | (rnd() % 2 ? 1u << (rnd() % 20) : 0) : rnd() & 0xfffff;
        if (rnd() % 16 == 0) mask = 0;                  /* callers pass mask & 0xfffff: 20 players */
        uint32_t r[2], usevt = rnd() % 4, layer = rnd() % 3, amount = (uint32_t)randint(-70000, 70000);
        for (int k = 0; k < 2; k++) {
            world *w = k ? wb : wa; cur = w;
            uint32_t v[4];
            if (which < 2) { v[0] = (uint32_t)(uintptr_t)(usevt ? vt_true : vt_some); v[1] = (uint32_t)(uintptr_t)w->mgr; v[2] = mask; }
            else { v[0] = (uint32_t)(uintptr_t)w->mgr; v[1] = mask; v[2] = layer; v[3] = amount; }
            r[k] = call_span(which, k, v, x0, x1, y);
        }
        n++;
        if (r[0] != r[1] || !same()) {
            if (bad++ < 5) printf("  MISMATCH span %d x0 %d x1 %d y %d mask %08x (ret %u/%u)\n", which, x0, x1, y, mask, r[0], r[1]);
            fill(wa); clone(wb, wa);
        }
        wa->nlog = wb->nlog = 0;
    }
    verdict(bad != 0, "[1] %ld random spans (+1, -1, layer add; clipped, empty, reversed, any mask, two predicates): "
            "%ld mismatches; %ld status changes ran the original per-cell code\n", n, bad, gp_shr_stats[2] - changes0);

    /* [2] whole circles through the original raster */
    bad = 0; n = 0;
    for (int it = 0; it < 20000; it++) {
        if (it % 500 == 0) { fill(wa); clone(wb, wa); }
        int x = randint(-10, W + 10), y = randint(-10, H + 10), r = randint(0, 20);
        uint32_t mask = rnd() % 2 ? 1u << (rnd() % 20) : rnd() & 0xfffff;
        void *vt = rnd() % 4 ? (void *)vt_true : (void *)vt_some;
        for (int k = 0; k < 2; k++) {
            world *w = k ? wb : wa; cur = w;
            raster_fn f = (raster_fn)(uintptr_t)(0xb50100 + (k ? offb : offa));
            f(x, y, r, vt, w->mgr, mask);
        }
        n++;
        if (!same()) { if (bad++ < 5) printf("  MISMATCH circle %d,%d r %d mask %08x\n", x, y, r, mask); fill(wa); clone(wb, wa); }
        wa->nlog = wb->nlog = 0;
    }
    verdict(bad != 0, "[2] %ld circles (radius 0-20, partly off the grid) through the raster 0xb50100: %ld mismatches\n", n, bad);

    /* [3] timing */
    fill(wa); clone(wb, wa);
    for (int k = 0; k < 2; k++) {
        world *w = k ? wb : wa; cur = w;
        for (int c = 0; c < W * H; c++) for (int p = 0; p < 20; p++) *(uint16_t *)(w->el[c] + 4 + 8 * p) = 100;
    }
    double t[2][3];
    for (int k = 0; k < 2; k++) {
        world *w = k ? wb : wa; cur = w;
        uint32_t v[3] = {(uint32_t)(uintptr_t)vt_true, (uint32_t)(uintptr_t)w->mgr, 1};
        uint64_t t0 = now_us();
        for (int i = 0; i < 200000; i++) { call_span(i & 1, k, v, 20, 40, 10 + (i & 15)); }
        t[k][0] = (now_us() - t0) * 1000.0 / 200000;
        raster_fn f = (raster_fn)(uintptr_t)(0xb50100 + (k ? offb : offa));
        for (int m = 0; m < 2; m++) {
            uint32_t mask = m ? 0x0f : 0x01;
            t0 = now_us();
            for (int i = 0; i < 20000; i++) { f(32, 24, m ? 15 : 10, vt_true, w->mgr, mask); }
            t[k][1 + m] = (now_us() - t0) * 1000.0 / 20000;
        }
    }
    printf("[3] time: span of 21 cells, 1 bit %.0f -> %.0f ns; circle r=10, 1 bit %.2f -> %.2f us; "
           "circle r=15, 4 bits %.2f -> %.2f us\n", t[0][0], t[1][0], t[0][1] / 1000, t[1][1] / 1000,
           t[0][2] / 1000, t[1][2] / 1000);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
