/* perfmarker and passtimers: the game's D3DPERF render-pass markers.
 *
 * Every render pass ("RenderViews", "RenderWater", "RenderTerrain", ... 26 sites) and every mesh
 * draw ("Rendering mesh\tDX8Render\t<mesh>", "Rendering mesh\tFXShader\t<mesh>") opens a PerfTimer
 * (0x517690) and closes it (0x517740). They call D3DPERF_BeginEvent / EndEvent through the
 * pointers 0xdd361c / 0xdd3620, which DX8Wrapper::Init (0x5251b5) fills only when
 * D3DPERF_GetStatus() != 0, i.e. with PIX attached; under Wine and in normal play they stay null.
 *
 * perfmarker (p_perf.S): while the pointer is null, the begin marker returns at once and the four
 *   per-draw callers skip building the name (string copies, sprintf for FX batches) that nothing
 *   reads then. Exact: see p_perf.S; test: tests/t_perf.c.
 * passtimers (diagnostic, off by default): puts D3DPERF-compatible functions into the two pointers
 *   at DLL load (Init leaves them alone when GetStatus() is 0; Shutdown clears them). Every named
 *   event on the main thread is timed with rdtsc: inclusive and self time and a count per name
 *   (the text up to the last tab, so all mesh draws of a kind share one bucket), summarised in the
 *   log every 5 s per frame (a frame = one top-level "RenderViews"). Events nested in another
 *   top-level pass carry its name ("UpdateShadowMap/RenderTerrain": the shadow-map pass renders
 *   the scene again; "UpdateWaterReflection/..."), so the second scene pass is not mixed into the
 *   main pass's buckets; events under RenderViews keep their plain names. Game results are unchanged
 *   (the markers only feed these functions), but the frame gets slower by the marker overhead
 *   (name copies + widening in the game, ~0.3-0.5 us per event here). With passtimers on the
 *   pointer is non-null, so perfmarker's early return never triggers: all markers run. */
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <x86intrin.h>

DWORD gp_render_tid;

/* ---- perfmarker ----------------------------------------------------------------------------- */
/* the callers' name-building blocks skipped while the pointer is null (p_perf.S) */
extern uint32_t gp_pm_addr[8];
void gp_pm_dx8a(void); void gp_pm_dx8b(void); void gp_pm_fx1(void); void gp_pm_fxn(void);
static const struct { uint32_t va, len, resume; uint64_t fnv; uint8_t head[8]; uint8_t hlen; void (*stub)(void); }
    blocks[4] = {
    {0x543170, 0x77, 0x543175, 0x76937b1a4fa92fccull, {0xb9,0x06,0,0,0}, 5, gp_pm_dx8a},             /* mov ecx,6 */
    {0x5432b0, 0x76, 0x5432b5, 0x7d9b37062f857665ull, {0xb9,0x08,0,0,0}, 5, gp_pm_dx8b},             /* mov ecx,8 */
    {0x573d3a, 0x60, 0x573d40, 0x1791e6d51b110a75ull, {0x8d,0x85,0xcc,0xfe,0xff,0xff}, 6, gp_pm_fx1}, /* lea eax,[ebp-0x134] */
    {0x573dc6, 0x57, 0x573dce, 0x4e7066248d487ddcull, {0x8b,0x07,0x8b,0x88,0xc4,0,0,0}, 8, gp_pm_fxn}};

int gp_patch_perfmarker(void)
{
    static const uint8_t head[] = {0x8b,0x44,0x24,0x04, 0x85,0xc0};   /* mov eax,[esp+4]; test eax,eax */
    gp_site s[12];
    gp_site_hash(&s[0], 0x517690, 0xa7, GP_FNV_517690);   /* the whole begin function */
    gp_site_hash(&s[1], 0x51ece0, 0x80, GP_FNV_51ECE0);   /* the only reader of 0xdd361c */
    gp_site_hash(&s[2], 0x51ed60, 0x0c, GP_FNV_51ED60);   /* end: null check on 0xdd3620 */
    gp_site_init(&s[3], 0x517690, head, sizeof head);
    gp_rel32(&s[3], 0, 0xe9, (void *)gp_perfmark);
    s[3].repl[5] = 0x90;
    for (int i = 0; i < 4; i++) {                        /* the block up to the resume point, then its head */
        gp_site_hash(&s[4 + 2 * i], blocks[i].va, blocks[i].len, blocks[i].fnv);
        gp_site_init(&s[5 + 2 * i], blocks[i].va, blocks[i].head, blocks[i].hlen);
        memset(s[5 + 2 * i].repl, 0x90, blocks[i].hlen);
        gp_rel32(&s[5 + 2 * i], 0, 0xe9, (void *)blocks[i].stub);
        gp_pm_addr[2 * i] = blocks[i].resume + gp_va_offset;
        gp_pm_addr[2 * i + 1] = blocks[i].va + blocks[i].len + gp_va_offset;
    }
    gp_perfmark_cont = 0x517696 + gp_va_offset;
    gp_render_tid = GetCurrentThreadId();
    return gp_apply("perfmarker", s, 12);
}

/* ---- passtimers ------------------------------------------------------------------------------ */
uint32_t gp_pt_ptr_va = 0xdd361c;
DWORD gp_pt_period_ms = 5000;
gp_pt_sink_t gp_pt_sink;

#define NB 256                     /* buckets (open addressing); bucket 0 = "(other)" when full */
#define MAXD 64
typedef struct { uint32_t hash; char name[64]; uint64_t incl, self; uint32_t count; } bucket_t;
static bucket_t bk[NB];
static struct { uint32_t b; uint64_t t0, child; } stk[MAXD];
static int depth;
static uint32_t frames, events, overflows, frame_hash, frame_bucket = NB;   /* bucket of "RenderViews" */
static uint64_t tsc0;
static LARGE_INTEGER qpc0;
static DWORD tick0;

static uint32_t fnv32(const char *s)
{
    uint32_t h = 0x811c9dc5u;
    for (; *s; s++) { h ^= (uint8_t)*s; h *= 0x01000193u; }
    return h ? h : 1;
}

/* bucket for a wide event name: the text before the last tab (mesh draws carry the mesh name
 * after it), low bytes of the characters as the game widened them (0x51ece0: movsbw), after
 * "<top>/" when the event is nested in a top-level pass other than RenderViews */
static uint32_t bucket_of(const WCHAR *name, const char *top)
{
    char key[64];
    int n = 0, cut = -1;
    if (!name) name = L"(null)";
    if (top && ((n = snprintf(key, 24, "%s/", top)) < 0 || n > 23)) n = 23;
    for (int i = 0; i < 256 && name[i]; i++) if (name[i] == '\t') cut = i;
    for (int i = 0; n < (int)sizeof key - 1 && name[i] && (cut < 0 || i < cut); i++) {
        uint8_t c = (uint8_t)name[i];
        key[n++] = c == '\t' ? ' ' : (c < 32 || c > 126) ? '?' : (char)c;
    }
    key[n] = 0;
    uint32_t h = fnv32(key);
    for (uint32_t i = 1, k = h % (NB - 1) + 1; i < NB; i++, k = k % (NB - 1) + 1) {
        if (bk[k].hash == h && !strcmp(bk[k].name, key)) return k;
        if (!bk[k].hash) { bk[k].hash = h; memcpy(bk[k].name, key, n + 1); return k; }
    }
    return 0;
}

int WINAPI gp_pt_begin(DWORD color, const WCHAR *name)
{
    (void)color;
    if (GetCurrentThreadId() != gp_render_tid) return 0;
    const char *top = depth > 0 && depth <= MAXD && stk[0].b != frame_bucket ? bk[stk[0].b].name : NULL;
    uint32_t b = bucket_of(name, top);
    events++;
    if (depth >= MAXD) { depth++; overflows++; return 0; }
    if (depth == 0 && bk[b].hash == frame_hash && !strcmp(bk[b].name, "RenderViews")) { frames++; frame_bucket = b; }
    stk[depth].b = b; stk[depth].child = 0;
    stk[depth].t0 = __rdtsc();                       /* last: our own work is not in this event */
    return depth++;
}

int WINAPI gp_pt_end(void)
{
    uint64_t now = __rdtsc();
    if (GetCurrentThreadId() != gp_render_tid || depth == 0) return 0;
    if (--depth >= MAXD) return 0;
    uint64_t d = now - stk[depth].t0;
    bucket_t *e = &bk[stk[depth].b];
    e->incl += d; e->self += d > stk[depth].child ? d - stk[depth].child : 0; e->count++;
    if (depth) stk[depth - 1].child += d;
    else if (GetTickCount() - tick0 >= gp_pt_period_ms) gp_pt_report();
    return 0;
}

static void emit(const char *line)
{
    if (gp_pt_sink) gp_pt_sink(line); else gp_log("%s", line);
}

static int by_incl(const void *a, const void *b)
{
    const bucket_t *x = *(bucket_t *const *)a, *y = *(bucket_t *const *)b;
    return x->incl < y->incl ? 1 : x->incl > y->incl ? -1 : 0;
}

void gp_pt_report(void)
{
    LARGE_INTEGER q, f;
    QueryPerformanceCounter(&q); QueryPerformanceFrequency(&f);
    uint64_t tsc = __rdtsc();
    double ms = (double)(q.QuadPart - qpc0.QuadPart) * 1000.0 / (double)f.QuadPart;
    double tpm = ms > 0 ? (double)(tsc - tsc0) / ms : 1;       /* rdtsc ticks per ms */
    double per = frames ? 1.0 / frames : 1000.0 / (ms > 0 ? ms : 1);   /* per frame, else per s */
    const char *unit = frames ? "frame" : "s";
    char line[480];
    snprintf(line, sizeof line, "passtimers: %.1f s, %lu frames (%.1f ms/frame), %.0f markers/%s%s; "
             "per %s: pass inclusive/self ms (calls)", ms / 1000, (unsigned long)frames,
             frames ? ms / frames : 0.0, events * per, unit, overflows ? ", NESTING OVERFLOW" : "", unit);
    emit(line);
    bucket_t *order[NB]; int n = 0;
    for (int i = 0; i < NB; i++) if (bk[i].count) order[n++] = &bk[i];
    qsort(order, n, sizeof order[0], by_incl);
    int len = 0;
    for (int i = 0; i < n; i++) {
        char item[120];
        snprintf(item, sizeof item, "%s %.2f/%.2f (%.4g)", order[i]->name[0] ? order[i]->name : "(other)",
                 order[i]->incl * per / tpm, order[i]->self * per / tpm, order[i]->count * per);
        if (len && len + 3 + (int)strlen(item) > 400) { emit(line); len = 0; }
        len += snprintf(line + len, sizeof line - len, "%s%s", len ? " | " : "  ", item);
    }
    if (len) emit(line);
    for (int i = 0; i < NB; i++) { bk[i].incl = bk[i].self = 0; bk[i].count = 0; }
    frames = events = overflows = 0;
    QueryPerformanceCounter(&qpc0); tsc0 = __rdtsc(); tick0 = GetTickCount();
}

int gp_patch_passtimers(void)
{
    gp_site s[2];
    gp_site_hash(&s[0], 0x51ece0, 0x80, GP_FNV_51ECE0);   /* calls *0xdd361c as (color, wname) */
    gp_site_hash(&s[1], 0x51ed60, 0x0c, GP_FNV_51ED60);   /* jmp *0xdd3620 */
    if (!gp_check("passtimers", s, 2)) return 0;
    volatile uint32_t *p = (volatile uint32_t *)(uintptr_t)gp_pt_ptr_va;
    if (p[0] || p[1]) {
        gp_log("passtimers: the D3DPERF pointers are already set (%08lx %08lx: PIX?); not installed",
               (unsigned long)p[0], (unsigned long)p[1]);
        return 0;
    }
    DWORD old;
    if (!VirtualProtect((void *)p, 8, PAGE_READWRITE, &old)) {
        gp_log("passtimers: VirtualProtect(%08x) failed (%lu); not installed", gp_pt_ptr_va, GetLastError());
        return 0;
    }
    memset(bk, 0, sizeof bk); depth = 0;
    frames = events = overflows = 0;
    frame_hash = fnv32("RenderViews");
    gp_render_tid = GetCurrentThreadId();
    QueryPerformanceCounter(&qpc0); tsc0 = __rdtsc(); tick0 = GetTickCount();
    p[0] = (uint32_t)(uintptr_t)gp_pt_begin;
    p[1] = (uint32_t)(uintptr_t)gp_pt_end;
    VirtualProtect((void *)p, 8, old, &old);
    gp_log("passtimers: D3DPERF Begin/End at %08x/%08x -> %p/%p; render passes are timed on thread %lu, "
           "summary every %lu ms (the markers now run, so perfmarker's early return is inactive)",
           gp_pt_ptr_va, gp_pt_ptr_va + 4, (void *)gp_pt_begin, (void *)gp_pt_end, gp_render_tid,
           gp_pt_period_ms);
    return 1;
}
