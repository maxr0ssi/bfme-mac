/* t_spellfire: firecircle (p_spellfire.c) against the original, both running the exe's own fire-logic
 * circle 0x6878d7 and row function 0x687059. Two relocated copies of .text (one patched by the
 * installer, with its byte and hash checks; one untouched); .rdata/.data at their own addresses, the
 * CRT floor/ceil imports from Wine's msvcr71. Each copy gets its own fire grid, built from the same seed:
 * 510 columns x 470 rows of 20-byte cells (burn rate u16 at +6, flags at +0xb), as FireLogic keeps
 * them (column pointers at +0x70, columns +0x78, rows +0x7c, the burning-cell set at +0x84).
 * Stand-ins (the same in both copies): TheTerrainLogic->isUnderwater (vt+0x4c: water in two river bands
 * and a lake, every call counted), the burning-cell key and set (0x6862b6 key, 0x686939 find,
 * 0x6867f4 erase, 0x686311 key destructor: every find and erase logged with the key; find reports
 * "found" for a fixed half of the keys).
 *   [0] the patch applies; the cell branch and both row calls go to its stubs
 *   [1] the weather spells' shot (radius 999999, amount -100, flag 0, at random places on the map)
 *       between fires lit and fed by small circles (amounts > 0, flags 0/1): after every call all
 *       cells, the grid object and the find/erase logs are identical; burning cells must be damped
 *       and put out (else the test proves nothing)
 *   [2] 20,000 random circles: radius 0-3000 or huge, centre on, near or far off the map (negative
 *       too), amount -300..300 (0 too), flag 0/1: identical after each
 *   [3] sensitivity: the patched copy with its cell stub skipping burning cells too -> cells differ
 *   [4] per shot: row-function calls and terrain queries, time original -> patched
 * usage: t_spellfire.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include "p_spell.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#define TC __attribute__((thiscall))
#define AT(va) ((uint32_t *)(uintptr_t)(va))
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
enum { COLS = 510, ROWS = 470, CELL = 20, LOGN = 1 << 16 };


static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }

static uint32_t off[2];                  /* 0: original, 1: patched */
static int cur;                          /* the copy running now */
static long nwater[2];
typedef struct { int n; uint32_t e[LOGN][3]; } log_t;   /* op (1 find, 2 erase), x, y */
static log_t lg[2];
static void logop(uint32_t op, uint32_t x, uint32_t y)
{
    log_t *l = &lg[cur];
    if (l->n < LOGN) { l->e[l->n][0] = op; l->e[l->n][1] = x; l->e[l->n][2] = y; }
    l->n++;
}

/* TheTerrainLogic: isUnderwater(x, y, waterZ*, terrainZ*, flag*) */
static int TC underwater(void *tl, float x, float y, float *wz, float *tz, uint8_t *f)
{
    (void)tl;
    nwater[cur]++;
    if (wz) *wz = 0;
    if (tz) *tz = 0;
    if (f) *f = 0;
    float dx = x - 3200, dy = y - 1500;
    return (y > 900 && y < 1150) || (x > 3900 && x < 4050) || dx * dx + dy * dy < 400 * 400;
}
static void *tl_vt[0x40];
static void *tl_obj[4] = {tl_vt};

/* the burning-cell key and set */
typedef struct { uint32_t vt0, vt1, x, y, z; } key_t;
static TC key_t *key_ctor(key_t *k, uint32_t x, uint32_t y) { k->vt0 = 1; k->vt1 = 2; k->x = x; k->y = y; k->z = ~0u; return k; }
static TC void key_dtor(key_t *k) { (void)k; }
static TC uint32_t set_find(uint32_t *set, key_t *k)
{
    logop(1, k->x, k->y);
    return ((k->x * 7 + k->y * 13) / 10) & 1 ? set[0] : set[1];   /* set[0] = end: not found */
}
static TC void set_erase(uint32_t *set, uint32_t it) { (void)set; logop(2, it, 0); }

typedef struct { uint8_t obj[0x100]; uint8_t *cells; uint32_t cols[COLS]; } grid;
static void build(grid *g)
{
    memset(g->obj, 0, sizeof g->obj);
    g->cells = calloc(COLS * ROWS, CELL);
    for (int x = 0; x < COLS; x++) g->cols[x] = (uint32_t)(uintptr_t)(g->cells + (size_t)x * ROWS * CELL);
    U32(g->obj, 0x70) = (uint32_t)(uintptr_t)g->cols;
    U32(g->obj, 0x78) = COLS; U32(g->obj, 0x7c) = ROWS;
    U32(g->obj, 0x84) = 0xe0d0e0d0u; U32(g->obj, 0x88) = 0xf0f0f0f0u;   /* end, "found" iterator */
    for (int i = 0; i < COLS * ROWS * CELL; i++) g->cells[i] = (uint8_t)(i * 37 + 11);   /* other fields: noise */
    for (int i = 0; i < COLS * ROWS; i++) { g->cells[i * CELL + 6] = 0; g->cells[i * CELL + 7] = 0; g->cells[i * CELL + 0xb] &= ~0x40; }
}
static void seed_fires(grid *g, uint32_t seed)
{
    rs = seed;
    for (int i = 0; i < 2500; i++) {
        uint8_t *c = g->cells + (size_t)(rnd() % (COLS * ROWS)) * CELL;
        uint16_t r = (uint16_t)(1 + rnd() % 900);
        memcpy(c + 6, &r, 2);
        if (rnd() & 1) c[0xb] |= 0x40;
    }
}
static int same(grid *a, grid *b)
{
    if (memcmp(a->cells, b->cells, (size_t)COLS * ROWS * CELL)) return 0;
    if (memcmp(a->obj, b->obj, 0x70) || memcmp(a->obj + 0x74, b->obj + 0x74, 0x100 - 0x74)) return 0;
    if (lg[0].n != lg[1].n) return 0;
    int n = lg[0].n < LOGN ? lg[0].n : LOGN;
    return !memcmp(lg[0].e, lg[1].e, (size_t)n * 12);
}
static int burning(grid *g)
{
    int n = 0;
    for (int i = 0; i < COLS * ROWS; i++) n += g->cells[i * CELL + 6] || g->cells[i * CELL + 7];
    return n;
}

typedef void (TC *circle_t)(void *fl, const float *pos, float r, int amount, int flag);
static void circle(int k, grid *g, const float *pos, float r, int amount, int flag)
{
    cur = k;
    ((circle_t)(uintptr_t)(0x6878d7 + off[k]))(g->obj, pos, r, amount, flag);
}

static void jmp_to(uint32_t va, void *target)
{
    uint8_t *p = (uint8_t *)(uintptr_t)va;
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)target - (va + 5));
    p[0] = 0xe9; memcpy(p + 1, &rel, 4);
}
static uint32_t rel_target(uint32_t va)
{
    const uint8_t *p = (const uint8_t *)(uintptr_t)va;
    int32_t rel; memcpy(&rel, p + 1, 4);
    return va + 5 + rel;
}
static LONG WINAPI crash(EXCEPTION_POINTERS *e)
{
    printf("exception %08lx at %p\nFAIL\n", e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress);
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
    if (orig_map_at(0xbd0000, 0x1b9000, 0) || orig_map_at(0xd89000, 0x81000, 0)) return 2;
    for (int k = 0; k < 2; k++)
        if (!(off[k] = orig_reserve_image()) || orig_map_at(0x401000, 0x7cf000, off[k])) return 2;
    HMODULE crt = LoadLibraryA("msvcr71.dll");
    if (!crt) { printf("no msvcr71.dll\nFAIL\n"); return 2; }
    *AT(0xbd0580) = (uint32_t)(uintptr_t)GetProcAddress(crt, "floor");   /* the imports, as the loader fills them */
    *AT(0xbd0588) = (uint32_t)(uintptr_t)GetProcAddress(crt, "ceil");
    tl_vt[0x4c / 4] = (void *)underwater;
    *AT(0xde4690) = (uint32_t)(uintptr_t)tl_obj;
    unsigned short cw = 0x007f;                          /* the game's FPU mode: 24-bit, nearest */
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));

    gp_va_offset = off[1];
    int ok = gp_patch_firecircle();
    gp_va_offset = 0;
    uint32_t c = rel_target(0x6870cf + off[1]), r1 = rel_target(0x6879a5 + off[1]), r2 = rel_target(0x6879c1 + off[1]);
    ok = ok && c == (uint32_t)(uintptr_t)gp_fc_cell && r1 == (uint32_t)(uintptr_t)gp_fc_rowcall && r2 == r1
         && rel_target(0x6879a5 + off[0]) == 0x687059 + off[0];
    verdict(!ok, "[0] firecircle: %s (cell -> %08x, rows -> %08x %08x)\n", ok ? "applied" : "NOT applied", c, r1, r2);
    if (!ok) { printf("FAIL\n"); return 1; }
    for (int k = 0; k < 2; k++) {
        jmp_to(0x6862b6 + off[k], (void *)key_ctor); jmp_to(0x686311 + off[k], (void *)key_dtor);
        jmp_to(0x686939 + off[k], (void *)set_find); jmp_to(0x6867f4 + off[k], (void *)set_erase);
    }

    static grid ga, gb;
    build(&ga); build(&gb); seed_fires(&ga, 0x1234567u); seed_fires(&gb, 0x1234567u);
    int mism = 0, b0 = burning(&ga), ndamped = 0;
    double ta = 0, tb = 0; long wa = 0, wb = 0; LONG rows = 0;
    enum { SHOTS = 24 };
    for (int s = 0; s < SHOTS; s++) {
        rs = 0x9e3779b9u + s * 7919;
        for (int f = 0; f < 6; f++) {                     /* small fires lit / fed between the shots */
            float px = (float)(rnd() % (COLS * 10));
            float p[3] = {px, (float)(rnd() % (ROWS * 10)), 0};
            int amt = 20 + (int)(rnd() % 200), fl = rnd() & 1;
            float r = 30.0f + rnd() % 120;
            circle(0, &ga, p, r, amt, fl); circle(1, &gb, p, r, amt, fl);
        }
        float px = (float)(rnd() % (COLS * 10));
        float p[3] = {px, (float)(rnd() % (ROWS * 10)), 0};
        int before = burning(&ga);
        long w0 = nwater[0], w1 = nwater[1];
        LONG k0 = gp_fc_stats[2];
        uint64_t t0 = now_us();
        circle(0, &ga, p, 999999.0f, -100, 0);
        ta += now_us() - t0; t0 = now_us();
        circle(1, &gb, p, 999999.0f, -100, 0);
        tb += now_us() - t0;
        rows += gp_fc_stats[2] - k0;
        wa += nwater[0] - w0; wb += nwater[1] - w1;
        ndamped += before - burning(&ga);
        if (!same(&ga, &gb)) { if (mism++ < 3) printf("  MISMATCH after shot %d at %.0f,%.0f\n", s, p[0], p[1]); }
    }
    verdict(mism || b0 == 0 || ndamped <= 0, "[1] %d weather shots (r 999999, -100, flag 0) between small fires: %d mismatches; "
            "%d cells burning at the start, %d put out by the shots; find/erase calls %d\n",
            SHOTS, mism, b0, ndamped, lg[0].n);

    mism = 0;
    enum { NRAND = 20000 };
    for (int i = 0; i < NRAND; i++) {
        rs = 0x51ed2701u + i * 104729;
        float span = (rnd() & 3) ? COLS * 10.0f : 60000.0f;
        float px = ((int)(rnd() % 20000) - 4000) * span / 12000.0f;
        float p[3] = {px, ((int)(rnd() % 20000) - 4000) * span / 12000.0f, 0};
        float r = (rnd() % 8) ? (float)(rnd() % 3000) + (rnd() % 100) / 100.0f : (float)(rnd() % 2000000);
        int amt = (int)(rnd() % 601) - 300, fl = rnd() & 1;
        if (rnd() % 40 == 0) amt = 0;
        if (i % 512 == 0) { seed_fires(&ga, 77 + i); seed_fires(&gb, 77 + i); }
        circle(0, &ga, p, r, amt, fl); circle(1, &gb, p, r, amt, fl);
        if (!same(&ga, &gb)) { if (mism++ < 3) printf("  MISMATCH at circle %d (%.0f,%.0f r %.0f amount %d flag %d)\n", i, p[0], p[1], r, amt, fl); }
    }
    verdict(mism != 0, "[2] %d random circles (radius 0-3000 or up to 2e6, centres on and off the map, amounts -300..300, "
            "flags 0/1): %d mismatches; logs %d entries\n", NRAND, mism, lg[0].n);

    /* sensitivity: a stub that skips burning cells too must be caught */
    uint8_t *sb = (uint8_t *)(uintptr_t)gp_fc_cell;
    static uint8_t bad[64];
    memcpy(bad, sb, sizeof bad);
    DWORD old;
    VirtualProtect(sb, 64, PAGE_EXECUTE_READWRITE, &old);
    for (int i = 0; i + 6 < 64; i++)                        /* cmpw $0,6(%esi); jne -> nops: burning cells skipped too */
        if (sb[i] == 0x66 && sb[i + 1] == 0x83 && sb[i + 2] == 0x7e && sb[i + 3] == 0x06 && sb[i + 5] == 0x75) { sb[i + 5] = 0x90; sb[i + 6] = 0x90; break; }
    seed_fires(&ga, 99); seed_fires(&gb, 99);
    float p[3] = {2000, 2000, 0};
    circle(0, &ga, p, 999999.0f, -100, 0); circle(1, &gb, p, 999999.0f, -100, 0);
    int caught = !same(&ga, &gb);
    memcpy(sb, bad, sizeof bad);
    verdict(!caught, "[3] sensitivity: a cell stub that also skips burning cells is %s\n", caught ? "caught" : "NOT caught");

    verdict(0, "[4] per weather shot (%d columns x %d rows): row-function calls 200001 -> %ld, terrain queries %ld -> %ld; "
            "time %.2f -> %.2f ms (the stand-in terrain query costs ~nothing; in the game each is a height and water lookup)\n",
            COLS, ROWS, rows / SHOTS, wa / SHOTS, wb / SHOTS, ta / SHOTS / 1000.0, tb / SHOTS / 1000.0);
    printf("%s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
