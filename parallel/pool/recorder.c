/* Deferred-effect recorder. See recorder.h and parallel/DESIGN.md §3.
 *
 * Per-site stub (17 bytes, generated at rec_site_add, lives in RWX memory):
 *     51                push ecx            ; thiscall 'this' (harmless for other conventions)
 *     68 <site>         push site
 *     E8 <rec_common>   call rec_common     ; cdecl: (site, ecx, clone_ret, args...)
 *     83 C4 08          add esp, 8
 *     C2 <n*4> / C3     ret n*4 (stdcall/thiscall: callee cleans) / ret (cdecl)
 * rec_common appends {item, site, ecx, args[, copied pointee]} to the calling thread's log and
 * returns the site's configured retval in eax. edx is clobbered (caller-saved in every x86
 * convention); ebx/esi/edi/ebp are preserved by the C function. */
#include "recorder.h"
#include "parallel.h"
#include <windows.h>
#include <string.h>

#define MAXSITES 256
#define MAXSLOTS 33
#define LOGCAP   65536          /* records per slot; overflow => the region runs serially */

typedef struct {
    uint32_t target, retval;
    uint8_t  conv, nargs;
    int8_t   copy_arg;
    uint8_t  copy_bytes;
    uint8_t *stub;
} site_t;

typedef struct {
    int32_t  item;
    uint16_t site;
    uint16_t seq;               /* order within the item */
    uint32_t ecx;
    uint32_t args[REC_MAXARGS];
    uint8_t  copy[REC_COPYMAX];
} rec_t;

typedef struct {
    rec_t   *r;
    uint32_t n;
    int32_t  item;
    uint16_t seq;
    uint8_t  overflow;
} slotlog_t;

static site_t    g_site[MAXSITES];
static int       g_nsites;
static uint8_t  *g_stubmem;
static slotlog_t g_log[MAXSLOTS];

int par_slot(void);                   /* parallel.c: 0 = main, 1..n = workers */

static uint32_t __attribute__((cdecl, noinline, used))
rec_common(uint32_t site, uint32_t ecx, uint32_t clone_ret)
{
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Warray-bounds"
    const uint32_t *args = &clone_ret + 1;         /* the clone's stack arguments (caller's frame) */
    int slot = par_slot();
    if (slot < 0) slot = 0;
    slotlog_t *L = &g_log[slot];
    site_t *s = &g_site[site];
    if (!L->r) L->r = VirtualAlloc(NULL, LOGCAP * sizeof(rec_t), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (L->n >= LOGCAP || !L->r) { L->overflow = 1; return s->retval; }
    rec_t *r = &L->r[L->n++];
    r->item = L->item; r->site = (uint16_t)site; r->seq = L->seq++; r->ecx = ecx;
    memcpy(r->args, args, s->nargs * 4);
    if (s->copy_arg >= 0 && args[s->copy_arg])
        memcpy(r->copy, (const void *)(uintptr_t)args[s->copy_arg], s->copy_bytes);
    return s->retval;
#pragma GCC diagnostic pop
}

int rec_site_add(uint32_t target, int conv, int nargs, uint32_t retval, int copy_arg, int copy_bytes)
{
    if (g_nsites >= MAXSITES || nargs > REC_MAXARGS || copy_bytes > REC_COPYMAX) return -1;
    if (!g_stubmem) g_stubmem = VirtualAlloc(NULL, MAXSITES * 32, MEM_COMMIT | MEM_RESERVE,
                                             PAGE_EXECUTE_READWRITE);
    int id = g_nsites++;
    site_t *s = &g_site[id];
    s->target = target; s->conv = (uint8_t)conv; s->nargs = (uint8_t)nargs; s->retval = retval;
    s->copy_arg = (int8_t)copy_arg; s->copy_bytes = (uint8_t)copy_bytes;
    uint8_t *p = s->stub = g_stubmem + id * 32;
    p[0] = 0x51;
    p[1] = 0x68; memcpy(p + 2, &id, 4);
    p[6] = 0xE8; int32_t rel = (int32_t)((uintptr_t)rec_common - (uintptr_t)(p + 11)); memcpy(p + 7, &rel, 4);
    p[11] = 0x83; p[12] = 0xC4; p[13] = 0x08;
    if (conv == REC_CDECL) { p[14] = 0xC3; }
    else { uint16_t n = (uint16_t)(nargs * 4); p[14] = 0xC2; memcpy(p + 15, &n, 2); }
    FlushInstructionCache(GetCurrentProcess(), p, 32);
    return id;
}

void *rec_site_stub(int site) { return site >= 0 && site < g_nsites ? g_site[site].stub : NULL; }

void rec_begin_item(int item)
{
    int slot = par_slot(); if (slot < 0) slot = 0;
    g_log[slot].item = item; g_log[slot].seq = 0;
}

void rec_reset(void)
{
    for (int i = 0; i < MAXSLOTS; i++) { g_log[i].n = 0; g_log[i].overflow = 0; g_log[i].seq = 0; }
}

int rec_overflowed(void)
{
    for (int i = 0; i < MAXSLOTS; i++) if (g_log[i].overflow) return 1;
    return 0;
}

uint32_t rec_count(void)
{
    uint32_t n = 0; for (int i = 0; i < MAXSLOTS; i++) n += g_log[i].n; return n;
}

/* ---- replay ------------------------------------------------------------------------------- */
typedef uint32_t (__attribute__((cdecl)) *cd8)(uint32_t, uint32_t, uint32_t, uint32_t,
                                                uint32_t, uint32_t, uint32_t, uint32_t);
#define A(i) a[i]
static uint32_t invoke(const site_t *s, uint32_t ecx, const uint32_t *a)
{
    void *f = (void *)(uintptr_t)s->target;
    if (s->conv == REC_CDECL)           /* the caller cleans, so passing 8 is always safe */
        return ((cd8)f)(A(0), A(1), A(2), A(3), A(4), A(5), A(6), A(7));
#define SC(T, ...) return ((uint32_t (__attribute__((stdcall)) *) T)f)(__VA_ARGS__)
#define TC(T, ...) return ((uint32_t (__attribute__((thiscall)) *) T)f)(ecx, ##__VA_ARGS__)
    typedef uint32_t u;
    if (s->conv == REC_STDCALL) switch (s->nargs) {
        case 0: SC((void)); case 1: SC((u), A(0)); case 2: SC((u,u), A(0),A(1));
        case 3: SC((u,u,u), A(0),A(1),A(2)); case 4: SC((u,u,u,u), A(0),A(1),A(2),A(3));
        case 5: SC((u,u,u,u,u), A(0),A(1),A(2),A(3),A(4));
        case 6: SC((u,u,u,u,u,u), A(0),A(1),A(2),A(3),A(4),A(5));
        case 7: SC((u,u,u,u,u,u,u), A(0),A(1),A(2),A(3),A(4),A(5),A(6));
        default: SC((u,u,u,u,u,u,u,u), A(0),A(1),A(2),A(3),A(4),A(5),A(6),A(7));
    }
    switch (s->nargs) {
        case 0: TC((u)); case 1: TC((u,u), A(0)); case 2: TC((u,u,u), A(0),A(1));
        case 3: TC((u,u,u,u), A(0),A(1),A(2)); case 4: TC((u,u,u,u,u), A(0),A(1),A(2),A(3));
        case 5: TC((u,u,u,u,u,u), A(0),A(1),A(2),A(3),A(4));
        case 6: TC((u,u,u,u,u,u,u), A(0),A(1),A(2),A(3),A(4),A(5));
        case 7: TC((u,u,u,u,u,u,u,u), A(0),A(1),A(2),A(3),A(4),A(5),A(6));
        default: TC((u,u,u,u,u,u,u,u,u), A(0),A(1),A(2),A(3),A(4),A(5),A(6),A(7));
    }
}

/* k-way merge of the per-slot logs by (item, seq). Each slot's log is already in that order:
 * a slot processes whole chunks, each an ascending item range, and chunks are claimed in
 * ascending order by any one slot. */
typedef void (*visit_fn)(const rec_t *r, void *u);
static int merge(visit_fn v, void *u)
{
    uint32_t pos[MAXSLOTS] = { 0 }; int n = 0;
    for (;;) {
        int best = -1;
        for (int i = 0; i < MAXSLOTS; i++) {
            if (pos[i] >= g_log[i].n) continue;
            const rec_t *r = &g_log[i].r[pos[i]];
            if (best < 0) { best = i; continue; }
            const rec_t *b = &g_log[best].r[pos[best]];
            if (r->item < b->item || (r->item == b->item && r->seq < b->seq)) best = i;
        }
        if (best < 0) return n;
        v(&g_log[best].r[pos[best]++], u); n++;
    }
}

static void do_replay(const rec_t *r, void *u)
{
    (void)u;
    const site_t *s = &g_site[r->site];
    uint32_t a[REC_MAXARGS];
    memcpy(a, r->args, sizeof a);
    if (s->copy_arg >= 0 && a[s->copy_arg]) a[s->copy_arg] = (uint32_t)(uintptr_t)r->copy;
    invoke(s, r->ecx, a);
}
int rec_replay(void) { return merge(do_replay, NULL); }

static void do_hash(const rec_t *r, void *u)
{
    uint64_t *h = (uint64_t *)u;
    const site_t *s = &g_site[r->site];
    uint32_t a[REC_MAXARGS];
    memcpy(a, r->args, sizeof a);
    if (s->copy_arg >= 0) a[s->copy_arg] = 0;   /* a worker-local address; hash its copy instead */
    const uint8_t *p[] = { (const uint8_t *)&r->item, (const uint8_t *)&r->site,
                           (const uint8_t *)&r->ecx, (const uint8_t *)a, r->copy };
    uint32_t l[] = { 4, 2, s->conv == REC_THISCALL ? 4u : 0u,   /* ecx is only meaningful for thiscall */
                     (uint32_t)s->nargs * 4, s->copy_arg >= 0 ? s->copy_bytes : 0u };
    for (int k = 0; k < 5; k++)
        for (uint32_t i = 0; i < l[k]; i++) { *h ^= p[k][i]; *h *= 0x100000001b3ull; }
}
uint64_t rec_digest(void) { uint64_t h = 0xcbf29ce484222325ull; merge(do_hash, &h); return h; }
