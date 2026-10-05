/* shroudspan: the three span updaters of the shroud manager, as tight loops (test t_shroud).
 *
 * Every time a unit crosses a partition cell (40 units), its vision is redrawn: the old circle is
 * queued for undo and the new one revealed, plus up to three counter-layer circles; a vision of
 * 300-600 units is a circle of 8-15 cells radius, 200-700 cells (docs/PERFORMANCE.md §18). Each
 * circle is drawn row by row; for each row ("span") the original runs, per player bit of the
 * vision mask and per cell: a virtual predicate call (0x5879b0, `mov al,1`) and a call to the
 * per-cell update (0xb52e10 / 0xb52ec0 / 0xb52bf0). These replacements do the same per cell inline:
 *   0xb4fc80  reveal count +1 (16-bit, 0 -> 1 on wrap) per set bit p, element + 4 + 8p
 *   0xb4fd20  reveal count -1
 *   0xb4fdc0  layer word (element + 6 + 2 * (layer + 4p)) += amount, clamped to 0..0xffff
 * The visible status of a cell (2 = count 0xffff, 1 = count 0, 0 = else) changes only at the counts
 * 0, 1, 0xfffe, 0xffff; there the original's per-cell function runs (it clears the cached shroud
 * status of the objects in the cell and calls the client's refresh callback for the local player),
 * in the same order. Any other predicate than the constant-true one is called as the original does.
 * So memory, call order and arguments are the original's; integer code only. */
#include "gp_scale.h"
#include <stdio.h>

uint32_t gp_shr_slow_inc, gp_shr_slow_dec, gp_shr_true_pred;
volatile LONG gp_shr_stats[3];
DWORD gp_scale_period_ms = 60000;
static int on;
static DWORD last_tick;
static LONG last[3], ncalls;

typedef struct { void **vt; uint8_t *mgr; uint32_t mask; } span_visitor;          /* +1 / -1 */
typedef struct { uint8_t *mgr; uint32_t mask; int layer; int amount; } layer_visitor;
typedef char (__attribute__((thiscall)) *pred_fn)(void *self, int x, int y);
typedef uint32_t (__attribute__((thiscall)) *cell_fn)(uint8_t *elem, uint8_t *mgr, int p);

static void periodic(void)
{
    if (++ncalls & 1023) return;
    DWORD t = GetTickCount();
    if (t - last_tick < gp_scale_period_ms) return;
    LONG d[3];
    for (int i = 0; i < 3; i++) { d[i] = gp_shr_stats[i] - last[i]; last[i] = gp_shr_stats[i]; }
    gp_log("shroudspan: last %lu s, %ld spans, %ld cell updates (%ld status changes, by the original code)",
           (t - last_tick) / 1000, d[0], d[1], d[2]);
    last_tick = t;
}

/* 0xb4e460: [begin, end) of row y clipped to the grid; both 0 when the row or span is outside */
static void row_range(uint8_t *mgr, int x0, int x1, int y, uint8_t **b, uint8_t **e)
{
    int w = *(int *)(mgr + 0x24);
    if (x1 < 0 || x0 >= w || y < 0 || y >= *(int *)(mgr + 0x28)) { *b = *e = NULL; return; }
    uint8_t *row = *(uint8_t **)(mgr + 0x2c) + (uint32_t)(w * y) * 0xa8;
    int hi = x1 < x0 ? x0 : x1;
    *b = x0 > 0 ? row + x0 * 0xa8 : row;
    *e = row + (hi < w ? hi + 1 : w) * 0xa8;
}

static uint32_t span(span_visitor *v, int x0, int x1, int y, int dir)
{
    uint8_t *b, *e, *mgr = v->mgr;
    row_range(mgr, x0, x1, y, &b, &e);
    uint32_t mask = v->mask;
    pred_fn pred = (pred_fn)v->vt[0];
    int trivial = (uint32_t)(uintptr_t)pred == gp_shr_true_pred;
    cell_fn slow = (cell_fn)(uintptr_t)(dir > 0 ? gp_shr_slow_inc : gp_shr_slow_dec);
    LONG cells = 0, changes = 0;
    for (int p = 0; mask; mask >>= 1, p++) {
        if (!(mask & 1) || b == e) continue;
        int x = x0;
        for (uint8_t *c = b; c != e; c += 0xa8, x++) {
            if (!trivial && !pred(v, x, y)) continue;
            uint16_t *w = (uint16_t *)(c + 4 + 8 * p);
            cells++;
            if (dir > 0) {
                if ((uint16_t)(*w - 1) < 0xfffd) { *w = *w + 1; continue; }   /* 1..0xfffd: no status change */
            } else if ((uint16_t)(*w - 2) < 0xfffd) { *w = *w - 1; continue; } /* 2..0xfffe */
            changes++;
            slow(c, mgr, p);
        }
    }
    gp_shr_stats[0]++; gp_shr_stats[1] += cells; gp_shr_stats[2] += changes;
    periodic();
    return 1;
}

uint32_t __attribute__((thiscall)) gp_shr_inc(void *v, int x0, int x1, int y) { return span(v, x0, x1, y, 1); }
uint32_t __attribute__((thiscall)) gp_shr_dec(void *v, int x0, int x1, int y) { return span(v, x0, x1, y, -1); }

uint32_t __attribute__((thiscall)) gp_shr_add(void *vp, int x0, int x1, int y)
{
    layer_visitor *v = vp;
    uint8_t *b, *e;
    row_range(v->mgr, x0, x1, y, &b, &e);
    LONG cells = 0;
    for (uint32_t mask = v->mask, p = 0; mask; mask >>= 1, p++) {
        if (!(mask & 1) || b == e) continue;
        uint32_t off = 6 + 2 * (v->layer + 4 * p);
        for (uint8_t *c = b; c != e; c += 0xa8) {
            uint16_t *w = (uint16_t *)(c + off);
            int s = (int)((uint32_t)*w + (uint32_t)v->amount);
            *w = (uint16_t)(s < 0 ? 0 : s > 0xffff ? 0xffff : s);
        }
        cells += (LONG)(e - b) / 0xa8;
    }
    gp_shr_stats[0]++; gp_shr_stats[1] += cells;
    periodic();
    return 1;
}

void gp_shroud_exit_log(void)
{
    if (on) gp_log("exit: shroudspan %ld spans, %ld cell updates, %ld status changes", gp_shr_stats[0],
                   gp_shr_stats[1], gp_shr_stats[2]);
}

int gp_patch_shroudspan(void)
{
    static const uint8_t head_a[] = {0x83,0xec,0x0c, 0x8b,0x44,0x24,0x18};   /* sub esp,12; mov eax,[esp+0x18] */
    static const uint8_t head_c[] = {0x8b,0x44,0x24,0x0c, 0x8b,0x54,0x24,0x04}; /* mov eax,[esp+12]; mov edx,[esp+4] */
    static const uint8_t ret_true[] = {0xb0,0x01, 0xc2,0x08,0x00};            /* mov al,1; ret 8 */
    gp_site s[11];
    gp_site_hash(&s[0], 0xb4fc80, 0x9f, GP_FNV_B4FC80);
    gp_site_hash(&s[1], 0xb4fd20, 0x9f, GP_FNV_B4FD20);
    gp_site_hash(&s[2], 0xb4fdc0, 0x75, GP_FNV_B4FDC0);
    gp_site_hash(&s[3], 0xb4e460, 0x87, GP_FNV_B4E460);
    gp_site_hash(&s[4], 0xb52e10, 0xa5, GP_FNV_B52E10);
    gp_site_hash(&s[5], 0xb52ec0, 0x95, GP_FNV_B52EC0);
    gp_site_hash(&s[6], 0xb52bf0, 0x37, GP_FNV_B52BF0);
    gp_site_init(&s[7], 0x5879b0, ret_true, sizeof ret_true); s[7].wlen = 0;
    gp_site_init(&s[8], 0xb4fc80, head_a, 5);
    gp_rel32(&s[8], 0, 0xe9, (void *)gp_shr_inc);
    gp_site_init(&s[9], 0xb4fd20, head_a, 5);
    gp_rel32(&s[9], 0, 0xe9, (void *)gp_shr_dec);
    gp_site_init(&s[10], 0xb4fdc0, head_c, 5);
    gp_rel32(&s[10], 0, 0xe9, (void *)gp_shr_add);
    gp_shr_slow_inc = 0xb52e10 + gp_va_offset;
    gp_shr_slow_dec = 0xb52ec0 + gp_va_offset;
    gp_shr_true_pred = 0x5879b0 + gp_va_offset;
    if (!gp_apply("shroudspan", s, 11)) return 0;
    on = 1; last_tick = GetTickCount();
    return 1;
}
