/* aiclosest: the partition manager's closest-object search, getClosestObject 0xa3bdb0 (test t_aiclose,
 * docs/PERFORMANCE.md §30).
 *
 * 102 call sites reach it through the wrappers 0xa39090 / 0xa390c0 / 0xa390f0: AnimalAIUpdate's flee
 * scan every UpdateTimer frames and its wander scan for emitters (5 % of an idle animal's frames), the
 * EmotionTracker, the AI's closest-target and closest-repulsor asks. The original:
 *   - puts the root of each of the 21 quadtrees its filters' mask allows into a function-static heap
 *     vector of 24-byte elements {cell distance, node, child subtree size, x, y, size} (STLport heap,
 *     a max-heap on the distance: the farthest node comes out first, EA's choice);
 *   - bound = (ceil(r x cells/size) + 1)^2 (x87 and CRT ceil), the query cell by 0xa3ad30 / 0xa3ada0
 *     (CRT floor each);
 *   - while the heap's top is within the bound: pops it (__pop_heap 0xa3b780 / __adjust_heap 0xa3b140,
 *     elements copied through the stack), runs each object of the node through the query's distance
 *     function from the table 0xdbdaf8 (types 0-3), an x87 fsts / fcomps / fnstsw against the best
 *     distance so far (ties win: the later object), the region test, getObject, the filter chain; an
 *     improvement re-derives the bound from the object's bounding circle (four CRT floors); then pushes
 *     each non-empty child whose cell box is within the bound (__push_heap 0xa3b0a0);
 *   - returns the best object.
 * The replacement does the same search in the same order with the same heap algorithm (on its own
 * array), the same getter, filter and mask calls in the same order, and:
 *   - the 2D distances (centre 0xa3a7a0, bounding circle 0xa3ae50) inline in SSE after the same getter
 *     calls, exact where every square stays a normal float (else x87 replicas of the originals, as
 *     scantree, §19); other distance functions through the table;
 *   - the compare against the best distance in SSE where the value is the float the original stores
 *     (inline path), else the original's x87 compare;
 *   - the improvement bound by the original's x87 sequences and the same CRT floor and 0xa3ada0 calls.
 * Any other FPU mode (x87 not 24-bit / nearest, MXCSR not the default), or a map whose cell count is not
 * in 1..2^24: the original runs. Exact: deterministic across machines, LAN-safe even against a player
 * without it. */
#include "gp.h"
#include "p_ai.h"
#include <stdlib.h>
#include <string.h>

#define GP_FNV_A3BDB0 0xb2abae5279f15682ull   /* getClosestObject, 0x724 bytes */
#define GP_FNV_A3B0A0 0x1b07967b560538bdull   /* __push_heap, 0x91 */
#define GP_FNV_A3B140 0x0ceeb496d72ad71eull   /* __adjust_heap, 0xdf */
#define GP_FNV_A3B780 0x981f8dd7cfb9b397ull   /* __pop_heap, 0x85 */
#define GP_FNV_A3AD30 0x58496a467a66c964ull   /* cell x of a coordinate, 0x62 */
#define GP_FNV_A3ADA0 0x906f88b462394deaull   /* cell y, 0x63 */
#define GP_FNV_A39450 0x2b33a7e2098eeeb1ull   /* filter chain allow, 0x31 */
#define GP_FNV_A39490 0x251b8d4a2c0fa427ull   /* filter chain mask, 0x25 */
#define GP_FNV_A3A7A8 0x4740fed2064e99a0ull   /* centre 2D after its first 8 bytes (distcalc writes 6) */
#define GP_FNV_A3AE58 0xee8b229e037841faull   /* bounding circle 2D after its first 8 bytes (distcalc writes 7) */

volatile LONG gp_ac_stats[6];
uint32_t gp_ac_sens;
uint32_t gp_ac_cont;                          /* 0xa3bdb6: the original after the bytes the jmp replaced */
static uint32_t dc0, dc1, va_index_x, va_index_y, va_allow, va_mask;
static int on;

typedef struct { void **vt; } iface;
typedef struct entry { uint32_t pad0; iface *it; uint32_t pad[3]; struct entry *next; } entry;   /* next at +0x14 */
typedef struct filt { void **vt; struct filt *next; } filt;
typedef struct { int32_t key; uint32_t *node; uint32_t stride; int32_t x, y, size; } helem;
typedef const float *(__attribute__((thiscall)) *getpos_fn)(iface *);
typedef const uint8_t *(__attribute__((thiscall)) *getgeom_fn)(iface *);
typedef void *(__attribute__((thiscall)) *getobj_fn)(iface *);
typedef char (__attribute__((thiscall)) *allow_fn)(filt *, void *);
typedef uint32_t (__attribute__((thiscall)) *mask_fn)(filt *);
typedef int32_t (__attribute__((thiscall)) *index_fn)(void *pm, float v);
typedef void *(__attribute__((thiscall)) *closest_fn)(void *pm, const float *pos, float r, const float *region, int type,
                                                        filt *filters);

void *__attribute__((thiscall)) gp_ac_orig(void *pm, const float *pos, float r, const float *region, int type, filt *f);
/* x87, as the original: the table's distance function with (pos, iface, 0), or the arithmetic of
 * 0xa3a7a0 / 0xa3ae50 on the getters' results; then fsts *d2; fcomps best. 1 = not farther than best */
int gp_ac_tab(void *fn, const float *pos, iface *it, uint32_t best, float *d2);
int gp_ac_x0(const float *p, const float *pos, uint32_t best, float *d2);
int gp_ac_x1(const float *p, const float *pos, const float *rad, uint32_t best, float *d2);
/* x87, as the original's improvement step: floor(((p.x - rad) - x0) * cells * inv) (plus = 0) or
 * floor(((rad + p.x) - x0) * cells * inv) (plus = 1) through the CRT floor, clamped to the grid */
int32_t gp_ac_cellx(const float *px, const float *rad, const void *pm, int plus);
float gp_ac_sub(const float *a, const float *b);  /* flds a; fsubs b; fstps */
float gp_ac_add(const float *a, const float *b);  /* flds a; fadds b; fstps */
__asm__(".intel_syntax noprefix\n.text\n"
".globl _gp_ac_orig\n.balign 16\n_gp_ac_orig:\n"
"  push ebp\n  mov ebp, esp\n  and esp, -8\n  jmp dword ptr [_gp_ac_cont]\n"
".globl _gp_ac_tab\n.balign 16\n_gp_ac_tab:\n"
"  push 0\n  push dword ptr [esp+16]\n  push dword ptr [esp+16]\n  call dword ptr [esp+16]\n  add esp, 12\n"
"  mov eax, dword ptr [esp+20]\n  fst dword ptr [eax]\n  fcomp dword ptr [esp+16]\n  jmp 8f\n"
".globl _gp_ac_x0\n.balign 16\n_gp_ac_x0:\n"
"  mov eax, dword ptr [esp+4]\n  mov ecx, dword ptr [esp+8]\n"
"  fld dword ptr [eax+4]\n  fsub dword ptr [ecx+4]\n  fld dword ptr [eax]\n  fsub dword ptr [ecx]\n  fld st(0)\n  fmul st, st(1)\n"
"  fld st(2)\n  fmul st, st(3)\n  faddp st(1), st\n  fstp st(2)\n  fstp st(0)\n"
"  mov eax, dword ptr [esp+16]\n  fst dword ptr [eax]\n  fcomp dword ptr [esp+12]\n  jmp 8f\n"
".globl _gp_ac_x1\n.balign 16\n_gp_ac_x1:\n"
"  mov eax, dword ptr [esp+4]\n  mov ecx, dword ptr [esp+8]\n  mov edx, dword ptr [esp+20]\n"
"  fld dword ptr [eax+4]\n  fsub dword ptr [ecx+4]\n  fld dword ptr [eax]\n  fsub dword ptr [ecx]\n  fld st(0)\n  fmul st, st(1)\n"
"  fld st(2)\n  fmul st, st(3)\n  faddp st(1), st\n  fstp dword ptr [edx]\n  fstp st(0)\n  fstp st(0)\n"
"  fld dword ptr [edx]\n  fsqrt\n  mov ecx, dword ptr [esp+12]\n  fsub dword ptr [ecx]\n  fcom dword ptr [_gp_ac_zero]\n  fld st(0)\n"
"  fnstsw ax\n  test ah, 5\n  jp 1f\n  fmulp st(1), st\n  fchs\n  jmp 2f\n1: fmulp st(1), st\n"
"2: mov eax, edx\n  fst dword ptr [eax]\n  fcomp dword ptr [esp+16]\n"
"8: fnstsw ax\n  test ah, 0x41\n  setnz al\n  movzx eax, al\n  ret\n"
".globl _gp_ac_cellx\n.balign 16\n_gp_ac_cellx:\n"
"  push esi\n  sub esp, 16\n"                         /* [esp] the double argument, [esp+8] float, [esp+12] int */
"  mov eax, dword ptr [esp+24]\n  mov ecx, dword ptr [esp+28]\n  mov esi, dword ptr [esp+32]\n"
"  cmp dword ptr [esp+36], 0\n  jne 1f\n"
"  fld dword ptr [eax]\n  fsub dword ptr [ecx]\n  jmp 2f\n"
"1: fld dword ptr [ecx]\n  fadd dword ptr [eax]\n"
"2: fsub dword ptr [esi]\n  fild dword ptr [esi+0x11c]\n"
"  cmp dword ptr [esi+0x11c], 0\n  jge 3f\n  fadd dword ptr [_gp_ac_two32]\n"
"3: fmulp st(1), st\n  fmul dword ptr [esi+0x118]\n  fstp qword ptr [esp]\n"
"  call dword ptr ds:[0xbd0580]\n"                         /* the CRT floor, as the original */
"  fstp dword ptr [esp+8]\n  fld dword ptr [esp+8]\n  fistp dword ptr [esp+12]\n"
"  mov eax, dword ptr [esp+12]\n  test eax, eax\n  jge 4f\n  xor eax, eax\n  jmp 5f\n"
"4: mov ecx, dword ptr [esi+0x11c]\n  cmp eax, ecx\n  jb 5f\n  lea eax, [ecx-1]\n"
"5: add esp, 16\n  pop esi\n  ret\n"
".globl _gp_ac_sub\n_gp_ac_sub:\n  mov eax, dword ptr [esp+4]\n  mov ecx, dword ptr [esp+8]\n"
"  fld dword ptr [eax]\n  fsub dword ptr [ecx]\n  fstp dword ptr [esp+4]\n  fld dword ptr [esp+4]\n  ret\n"
".globl _gp_ac_add\n_gp_ac_add:\n  mov eax, dword ptr [esp+4]\n  mov ecx, dword ptr [esp+8]\n"
"  fld dword ptr [eax]\n  fadd dword ptr [ecx]\n  fstp dword ptr [esp+4]\n  fld dword ptr [esp+4]\n  ret\n"
".data\n.balign 4\n_gp_ac_zero: .long 0\n_gp_ac_two32: .long 0x4f800000\n.text\n.att_syntax prefix\n");

static inline uint32_t bits(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }
/* |v| < 2^62 (finite) and (v == 0 or |v| >= 2^-62): its square is a normal float or zero */
static inline int sq_ok(float v) { uint32_t e = (bits(v) >> 23) & 0xff; return e < 127 + 62 && (e >= 127 - 62 || !(bits(v) << 1)); }
static inline int small(float v) { return ((bits(v) >> 23) & 0xff) < 127 + 62; }

static helem *heap;
static uint32_t hcap;
static int grow(uint32_t n)
{
    if (n <= hcap) return 1;
    uint32_t c = hcap ? hcap * 2 : 1024;
    while (c < n) c *= 2;
    helem *h = realloc(heap, c * sizeof *h);
    if (!h) return 0;
    heap = h; hcap = c;
    return 1;
}
/* STLport's __push_heap / __adjust_heap with less<> on the key, as 0xa3b0a0 / 0xa3b140 */
static void push_heap_(helem *f, int hole, int top, const helem *v)
{
    int parent = (hole - 1) / 2;
    while (hole > top && f[parent].key < v->key) { f[hole] = f[parent]; hole = parent; parent = (hole - 1) / 2; }
    f[hole] = *v;
}
static void adjust_heap_(helem *f, int hole, int len, const helem *v)
{
    int top = hole, second = 2 * hole + 2;
    while (second < len) {
        if (f[second].key < f[second - 1].key) second--;
        f[hole] = f[second]; hole = second; second = 2 * second + 2;
    }
    if (second == len) { f[hole] = f[second - 1]; hole = second - 1; }
    push_heap_(f, hole, top, v);
}

/* 1 if the object is not farther than the best so far; *d2 the float the original stores */
static int dist(void *fn, const float *pos, iface *it, float best, float *d2)
{
    int k = fn == (void *)(uintptr_t)dc0 ? 0 : fn == (void *)(uintptr_t)dc1 ? 1 : -1;
    if (k < 0) { gp_ac_stats[4]++; return gp_ac_tab(fn, pos, it, bits(best), d2); }
    const float *p = ((getpos_fn)it->vt[1])(it);
    const float *rad = k ? (const float *)(((getgeom_fn)it->vt[0])(it) + 0x10) : NULL;
    if (small(p[0]) && small(p[1]) && small(pos[0]) && small(pos[1])) {
        float dx = p[0] - pos[0], dy = p[1] - pos[1];
        if (sq_ok(dx) && sq_ok(dy)) {
            float q = dx * dx + dy * dy;
            if (k) {
                float d = __builtin_sqrtf(q) - *rad;
                if (!small(*rad) || !sq_ok(d)) goto x87;
                q = d * d;
                if (bits(d) > 0x80000000u) q = -q;             /* d < 0 (not -0): -(d*d) */
            }
            gp_ac_stats[3]++; *d2 = q;
            return !(q > best);
        }
    }
x87:
    gp_ac_stats[4]++;
    return k ? gp_ac_x1(p, pos, rad, bits(best), d2) : gp_ac_x0(p, pos, bits(best), d2);
}

void *__attribute__((thiscall)) gp_ac_closest(void *pm_, const float *pos, float r, const float *region, int type, filt *filters)
{
    uint8_t *pm = pm_;
    uint16_t cw; uint32_t mx;
    __asm__ volatile("fnstcw %0\n\tstmxcsr %1" : "=m"(cw), "=m"(mx));
    int32_t cells = *(int32_t *)(pm + 0x11c);
    float inv = *(float *)(pm + 0x118);
    if ((cw & 0xf3f) != 0x3f || (mx & 0xffc0) != 0x1f80 || cells < 1 || cells > (1 << 24) || !(inv > 0x1p-60f && inv < 0x1p40f)) {
        gp_ac_stats[5]++;
        return gp_ac_orig(pm, pos, r, region, type, filters);
    }
    if (!grow(32)) { gp_ac_stats[5]++; return gp_ac_orig(pm, pos, r, region, type, filters); }
    gp_ac_stats[0]++;
    if (type != 0 && type != 2 && type != 1 && type != 3) type = 0;
    void *fn = (void *)(uintptr_t)((uint32_t *)(uintptr_t)0xdbdaf8)[type];
    uint32_t mask = filters ? 2 * ((mask_fn)(uintptr_t)va_mask)(filters) + 1 : 0xffffffffu;
    uint32_t n = 0;
    uint32_t *t0 = (uint32_t *)(pm + 0x18);
    uint32_t stride0 = (uint32_t)((int32_t)(t0[1] - t0[0]) >> 3) >> 2;    /* tree 0's, for every tree */
    for (int t = 0; t < 21; t++, mask >>= 1)
        if (mask & 1) heap[n++] = (helem){0, (uint32_t *)(uintptr_t)t0[3 * t], stride0, 0, 0, cells};
    if (r < 1e-5f) return NULL;                                           /* 0xbde0b4; NaN goes on */
    float scale = (float)cells * inv;                                    /* in 2^-60 .. 2^64: no underflow below */
    if (r * scale > 32766.0f) r = 32766.0f / scale;
    float best_d2 = r * r, sr = scale * r;
    void *best = NULL;
    int32_t ci;                                    /* ceil(sr) through float, fistp: sr <= 32766 or NaN */
    if (sr != sr) ci = (int32_t)0x80000000;
    else { ci = (int32_t)sr; if ((float)ci < sr) ci++; }
    int32_t bound = (int32_t)((uint32_t)(ci + 1) * (uint32_t)(ci + 1));
    int32_t cx = ((index_fn)(uintptr_t)va_index_x)(pm, pos[0]), cy = ((index_fn)(uintptr_t)va_index_y)(pm, pos[1]);
    int32_t rx0 = 0, rx1 = 0, ry0 = 0, ry1 = 0;
    if (region) {
        rx0 = ((index_fn)(uintptr_t)va_index_x)(pm, region[0]); rx1 = ((index_fn)(uintptr_t)va_index_x)(pm, region[3]);
        ry0 = ((index_fn)(uintptr_t)va_index_y)(pm, region[1]); ry1 = ((index_fn)(uintptr_t)va_index_y)(pm, region[4]);
    }
    LONG pops = 0, cands = 0;
    while (n && heap[0].key <= bound) {
        helem e = heap[0], v = heap[n - 1];
        heap[n - 1] = heap[0];
        adjust_heap_(heap, 0, (int)n - 1, &v);
        n--; pops++;
        uint32_t *node = e.node;
        for (entry *en = (entry *)(uintptr_t)node[1]; en; en = en->next) {
            iface *it = en->it;
            float d2;
            cands++;
            if (!dist(fn, pos, it, best_d2, &d2)) continue;
            if (region) {
                const float *p = ((getpos_fn)it->vt[1])(it);
                if (p[0] < region[0] || p[1] < region[1] || p[0] > region[3] || p[1] > region[4]) continue;
            }
            void *obj = ((getobj_fn)it->vt[3])(it);
            if (!obj) continue;
            if (filters && !((allow_fn)(uintptr_t)va_allow)(filters, obj)) continue;
            if (gp_ac_sens == 1 && best && d2 == best_d2) continue;           /* test only: ties keep the first */
            best_d2 = d2; best = obj;
            const uint8_t *g = ((getgeom_fn)it->vt[0])(it);
            const float *p = ((getpos_fn)it->vt[1])(it);
            const float *rad = (const float *)(g + 0x10);
            int32_t dx0 = gp_ac_cellx(p, rad, pm, 0) - cx, dx1 = gp_ac_cellx(p, rad, pm, 1) - cx;
            float y0 = gp_ac_sub(&p[1], rad), y1 = gp_ac_add(rad, &p[1]);
            int32_t dy0 = ((index_fn)(uintptr_t)va_index_y)(pm, y0) - cy;
            int32_t dy1 = ((index_fn)(uintptr_t)va_index_y)(pm, y1) - cy;
            uint32_t ex = (uint32_t)dx1 > (uint32_t)dx0 ? (uint32_t)dx1 : (uint32_t)dx0;
            uint32_t ey = (uint32_t)dy1 > (uint32_t)dy0 ? (uint32_t)dy1 : (uint32_t)dy0;
            bound = (int32_t)(ey * ey + ex * ex);
        }
        if (!node[0]) continue;
        int32_t half = e.size / 2;
        uint32_t *child = node + 2;
        for (int k = 0; k < 4; k++, child += 2 * e.stride) {
            if (!child[1] && !child[0]) continue;
            int32_t kx = e.x + ((k & 1) ? half : 0), ky = e.y + ((k & 2) ? half : 0);
            uint32_t ux = cx < kx ? (uint32_t)(kx - cx - 1) : cx < kx + half ? 0 : (uint32_t)(cx - kx - half);
            uint32_t uy = cy < ky ? (uint32_t)(ky - cy - 1) : cy < ky + half ? 0 : (uint32_t)(cy - ky - half);
            int32_t d = (int32_t)(ux * ux + uy * uy);              /* imul and add, wrapping as the original */
            if (d > bound) continue;
            if (region && (kx > rx1 || ky > ry1 || kx + half < rx0 || ky + half < ry0)) continue;
            if (!grow(n + 1)) continue;                    /* out of memory (a few KB): not seen in practice */
            helem c = {d, child, e.stride >> 2, kx, ky, half};
            heap[n++] = c;
            push_heap_(heap, (int)n - 1, 0, &c);
        }
    }
    gp_ac_stats[1] += pops; gp_ac_stats[2] += cands;
    return best;
}

void gp_ac_exit_log(void)
{
    if (on) gp_log("exit: aiclosest %ld searches, %ld heap pops, %ld candidates (%ld distances inline, %ld through the "
                   "table or x87), %ld by the original", gp_ac_stats[0], gp_ac_stats[1], gp_ac_stats[2], gp_ac_stats[3],
                   gp_ac_stats[4], gp_ac_stats[5]);
}

int gp_patch_aiclosest(void)
{
    static const uint8_t head[] = {0x55, 0x8b, 0xec, 0x83, 0xe4, 0xf8};   /* push ebp; mov ebp, esp; and esp, -8 */
    static const uint8_t floor_ceil[] = {0xff, 0x15, 0x80, 0x05, 0xbd, 0x00};   /* 0xa3c1b8: call [0xbd0580] (floor) */
    gp_site s[12];
    gp_site_hash(&s[0], 0xa3bdb0, 0x724, GP_FNV_A3BDB0);
    gp_site_hash(&s[1], 0xa3b0a0, 0x91, GP_FNV_A3B0A0);
    gp_site_hash(&s[2], 0xa3b140, 0xdf, GP_FNV_A3B140);
    gp_site_hash(&s[3], 0xa3b780, 0x85, GP_FNV_A3B780);
    gp_site_hash(&s[4], 0xa3ad30, 0x62, GP_FNV_A3AD30);
    gp_site_hash(&s[5], 0xa3ada0, 0x63, GP_FNV_A3ADA0);
    gp_site_hash(&s[6], 0xa39450, 0x31, GP_FNV_A39450);
    gp_site_hash(&s[7], 0xa39490, 0x25, GP_FNV_A39490);
    gp_site_hash(&s[8], 0xa3a7a8, 0x1e, GP_FNV_A3A7A8);
    gp_site_hash(&s[9], 0xa3ae58, 0x4b, GP_FNV_A3AE58);
    gp_site_init(&s[10], 0xa3c1b8, floor_ceil, sizeof floor_ceil); s[10].wlen = 0;
    gp_site_init(&s[11], 0xa3bdb0, head, sizeof head);
    gp_rel32(&s[11], 0, 0xe9, (void *)gp_ac_closest);
    s[11].repl[5] = 0x90;
    gp_ac_cont = 0xa3bdb6 + gp_va_offset;
    dc0 = 0xa3a7a0 + gp_va_offset; dc1 = 0xa3ae50 + gp_va_offset;
    va_index_x = 0xa3ad30 + gp_va_offset; va_index_y = 0xa3ada0 + gp_va_offset;
    va_allow = 0xa39450 + gp_va_offset; va_mask = 0xa39490 + gp_va_offset;
    if (!gp_apply("aiclosest", s, 12)) return 0;
    on = 1;
    return 1;
}
