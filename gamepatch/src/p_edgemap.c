/* edgemap: constructVolume 0x4ef790 (dynamic shadow volume from a silhouette) chains the
 * silhouette's edges into loops with a linear search: for each edge, find the first later edge
 * that starts where this one ends and swap it into the next slot (hot loop at 0x4ef8d5), O(E^2)
 * per volume. The silhouette array (shorts, one edge = start, end at an even position) is
 * permuted in place as it goes.
 *
 * The patch computes that same permutation up front with an index (for every start vertex, the
 * unconsumed positions that start there, in position order: the head is exactly what the linear
 * search finds), writes it back into the silhouette, then runs the original code. On the
 * pre-permuted array the original's search always succeeds at its first candidate or finds
 * nothing, so its scan is cut to that one comparison (0x4ef8db: "not found" = set j = count and
 * go to the not-found branch at 0x4ef916, as the original's scan leaves it). Result, including
 * the permuted silhouette, is bit-identical (gamepatch/tests/t_shadow.c). Per-thread index buffers
 * (the shadowpar workers run this too); any other thread uses the linear version of the
 * permutation (same result). */
#include "par_shadow.h"
#include "parallel.h"
#include <string.h>

#define GP_FNV_4EF790 0xcaef2ce916d3c685ull   /* constructVolume, 0x45b bytes */
#define EM_SLOTS 33                            /* pool slots 0..32 (parallel.c MAXW) */
#define NIL 0xffff
static uint16_t *em_head[EM_SLOTS], *em_next[EM_SLOTS];
static volatile char em_busy[EM_SLOTS];      /* set while a permutation runs: a fault mid-way
                                                (pool retry) leaves heads to clear */
static volatile LONG em_main_tid;
extern int gp_sp_pool_up;
volatile LONG gp_cv_calls, gp_cv_chained;   /* for the shadowstats line (any thread) */
int gp_cv_on;

/* 0 = the render thread (first caller) or pool slot; -1 = unknown thread */
int gp_cv_slot(void)
{
    if (gp_sp_pool_up) return par_slot();
    LONG t = (LONG)GetCurrentThreadId();
    InterlockedCompareExchange(&em_main_tid, t, 0);
    return em_main_tid == t ? 0 : -1;
}

static void swap_pair(uint16_t *a, uint16_t *b)
{
    uint32_t x, y;
    memcpy(&x, a, 4); memcpy(&y, b, 4);
    memcpy(a, &y, 4); memcpy(b, &x, 4);
}

/* the original's own order of operations, for when there is no index */
static void permute_linear(uint16_t *sil, int count)
{
    for (int s = 2; s < count; s += 2) {
        uint16_t end = sil[s - 1];
        for (int j = s; j < count; j += 2)
            if (sil[j] == end) { if (j != s) swap_pair(sil + s, sil + j); break; }
    }
}

void gp_cv_permute(uint16_t *sil, int count, int slot)
{
    if (count <= 2) return;                       /* the chaining loop runs for s = 2.. < count */
    int npos = (count - 1) >> 1;                  /* candidate positions 2k, k = 1..npos */
    if (slot < 0 || slot >= EM_SLOTS || npos >= 0x8000) { permute_linear(sil, count); return; }
    if (!em_head[slot]) {
        uint16_t *m = VirtualAlloc(NULL, 0x20000 + 0x10000, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
        if (!m) { permute_linear(sil, count); return; }
        memset(m, 0xff, 0x20000);
        em_next[slot] = m + 0x10000;
        em_head[slot] = m;
    }
    uint16_t *head = em_head[slot], *next = em_next[slot];
    if (em_busy[slot]) memset(head, 0xff, 0x20000);
    em_busy[slot] = 1;
    for (int k = npos; k >= 1; k--) {             /* lists in ascending position order */
        uint16_t key = sil[2 * k];
        next[k] = head[key];
        head[key] = (uint16_t)k;
    }
    /* invariant at step s: the lists hold exactly the positions >= s, and k = s/2 is the head of
     * the list of sil[s]; every step removes k, so all heads are NIL again at the end */
    for (int s = 2; s < count; s += 2) {
        int k = s >> 1;
        uint16_t end = sil[s - 1];
        uint16_t h = head[end];
        if (h == NIL) { head[sil[s]] = next[k]; continue; }   /* no match: s just consumed */
        head[end] = next[h];
        if (h == k) continue;                                  /* already in place */
        uint16_t w = sil[s];                                   /* the edge that moves to 2h */
        swap_pair(sil + s, sil + 2 * h);
        head[w] = next[k];
        uint16_t *pp = &head[w];
        while (*pp != NIL && *pp < h) pp = &next[*pp];
        next[h] = *pp;
        *pp = h;
    }
    em_busy[slot] = 0;
}

/* called from the entry stub with constructVolume's arguments; the same early-outs as the
 * original, so the silhouette is only touched when the chaining loop will run */
__attribute__((force_align_arg_pointer))
void gp_cv_prepermute(uint8_t *sh, const void *light, int li, int mesh)
{
    InterlockedIncrement(&gp_cv_calls);
    if (li < 0 || li >= 1 || !light) return;
    if (!AT(sh, SH_VOL + (li * 0xa0 + mesh) * 4, void *)) return;
    int count = AT(sh, SH_SILD + mesh * 4, int);
    if (count <= 2) return;
    InterlockedIncrement(&gp_cv_chained);
    gp_cv_permute(AT(sh, SH_SIL + mesh * 4, uint16_t *), count, gp_cv_slot());
}

int gp_patch_edgemap(void)
{
    static const uint8_t entry[] = {0x55, 0x8b,0xec, 0x83,0xec,0x40};   /* push ebp; mov ebp,esp; sub esp,0x40 */
    static const uint8_t scan[] = {0x8b,0x45,0xd8, 0x41, 0x41, 0x3b,0x4d,0xe4, 0x89,0x4d,0xe0, 0x7c,0xea};
    /* mov ecx,[ebp-0x1c] (count); mov [ebp-0x20],ecx; jmp 0x4ef916; nop x5 */
    static const uint8_t cut[] = {0x8b,0x4d,0xe4, 0x89,0x4d,0xe0, 0xeb,0x33, 0x90,0x90,0x90,0x90,0x90};
    gp_site s[3];
    gp_site_hash(&s[0], 0x4ef790, 0x45b, GP_FNV_4EF790);
    gp_site_init(&s[1], 0x4ef790, entry, sizeof entry);
    gp_rel32(&s[1], 0, 0xe9, (void *)gp_cv_entry_stub);
    s[1].repl[5] = 0x90;
    gp_site_init(&s[2], 0x4ef8db, scan, sizeof scan);
    memcpy(s[2].repl, cut, sizeof cut);
    gp_cv_cont = 0x4ef796 + gp_va_offset;
    if (!gp_apply("edgemap", s, 3)) return 0;
    gp_cv_on = 1;
    return 1;
}
