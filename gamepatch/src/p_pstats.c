/* particlestats: counters and timers for the "RenderParticles" pass (no behaviour change), logged
 * every 60 s, split by pass (byte 0xdd1e44: 1 = inside the shadow-map pass UpdateShadowMap).
 *
 * What runs under the RenderParticles marker (RTS3DScene::Flush 0x470f44, 0x4716c7..0x471708;
 * static analysis, docs/PERFORMANCE.md s10.4):
 *   0x4716ee call 0x44c3ea -> W3DFXParticleSystemManager::render 0x44c84a (scene mode 0 with
 *            scene+0x18 clear; it works only when armed, mgr+0xa8, which Customized_Render sets at
 *            0x47016c in both passes). Per system: a temporary handle, the "SMUD" (heat smudge)
 *            test, then the CAT_DRAW module's vtable slot +0x10. Six of the seven draw modules
 *            (default, streak, quad, butterfly, lightning, gpu) return 0 at their first test when
 *            0xdd1e44 is set (0x961e09 0x9624c9 0x962a41 0x963491 0x963db0 0x9658c7): no gather, no
 *            point-group vertices, no VB lock, no draw in the shadow pass. The RenderObject module
 *            0x964c00 has no such test: per particle inside the pass camera's box it sets the
 *            particle's render object transform (vt+0x54), its colour/opacity through 0x50e040 /
 *            0x50e244 / 0x50e413 (per mesh: an FX parameter found by name and the material's
 *            parameter block recorded again, under the DX lock) and un-hides it. Those objects are
 *            ordinary scene objects that the main pass culls and draws BEFORE its own
 *            RenderParticles, so these writes are not dead in the shadow pass.
 *   0x4716f4 call 0x52ec60 -> SortingRendererClass::Flush: draws every sorted (alpha-blended)
 *            polygon inserted since the last flush in this pass, e.g. from W3D emitter buffers
 *            (ParticleBufferClass::Render 0x5aed50 has no shadow-pass test) that the object loop
 *            rendered; in the shadow pass into the R32F shadow map, with their own shader.
 * Sites (every stub runs the original with every general register, xmm0-7 and its arguments as
 * the caller left them and returns the original's eax, ecx, edx, xmm0-7; p_pstats.S):
 *   0x4716ee  call 0x44c3ea (cdecl, 1 arg)             timed; before it: armed flag, live count and,
 *                                                      every 16th main-pass call, a read-only walk of
 *                                                      the system list by draw module kind
 *   0xc32854  RenderObject draw module vtable slot +0x10 -> 0x964c00 (thiscall, 3 args, ret 12;
 *             returns the number of particles it processed)   timed
 *   0x965277, 0x96528b, 0x9652cb  its calls of 0x50e040 (4 args), 0x50e244 (2), 0x50e413 (4), cdecl:
 *             timed together as "colour setters"
 *   0x4716f4  call 0x52ec60 (no args)                  timed; before it: sorted nodes waiting
 *   0xbed2a0  ParticleBufferClass vtable slot +0x30 Render -> 0x5aed50 (thiscall, 1 arg, ret 4):
 *             timed (W3D model emitters; they render in Customized_Render's object loop) */
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>

#define SM_FLAG    0xdd1e44     /* byte: 1 while UpdateShadowMap renders */
#define MGR_PTR    0xde3744     /* TheFXParticleSystemManager */
#define CPU_STORE  0xc33ae8u    /* CPU particle storage vtable: count at +0x10 */

/* draw module kinds of the system walk (vtables of the CAT_DRAW modules), then none / other */
static const uint32_t draw_vt[7] = {0xc326b8, 0xc32724, 0xc32784, 0xc327e0, 0xc32844, 0xc328a8, 0xc3290c};
static const char *const draw_name[PS_KINDS] = {"default", "streak", "quad", "butterfly", "renderobject",
                                                "lightning", "gpu", "none", "other"};
enum { K_NONE = 7, K_OTHER = 8 };

gp_pst_t gp_pst;
static gp_pst_t last;
static uint64_t ticks[PS_N][2], last_ticks[PS_N][2];
static DWORD last_tick;
static uint64_t last_tsc, last_qpc;
static int on;
uint32_t gp_pst_sort_head_va = 0xd9b2bc;   /* SortingRendererClass: first sorted node ([node] = next) */
uint32_t gp_pst_mgr_cont, gp_pst_robj_cont, gp_pst_c1_cont, gp_pst_c2_cont, gp_pst_c3_cont;
uint32_t gp_pst_sort_cont, gp_pst_pbuf_cont;

static int sm(void) { return *(volatile uint8_t *)SM_FLAG != 0; }

/* the manager's system list (std::list at mgr+0x4c: [head] = first node, node+8 = the system), in
 * the order 0x44c926..0x44cbe7 walks it; read only */
static void walk(const uint8_t *mgr)
{
    const uint8_t *head = *(const uint8_t *const *)(mgr + 0x4c);
    if (!head) return;
    int n = 0;
    gp_pst.walks++;
    for (const uint8_t *node = *(const uint8_t *const *)head; node && node != head;
         node = *(const uint8_t *const *)node) {
        if (++n > 200000) { gp_pst.walk_cut++; break; }
        const uint8_t *sys = *(const uint8_t *const *)(node + 8);
        if (!sys) continue;
        if (*(const int *)(sys + 0xc) == 6) { gp_pst.terrain++; continue; }   /* drawn with the terrain */
        const uint8_t *mod = *(const uint8_t *const *)(sys + 0x1c4);
        int k = K_NONE;
        if (mod) {
            uint32_t vt = *(const uint32_t *)mod;
            k = 0;
            while (k < 7 && draw_vt[k] != vt) k++;
            if (k == 7) k = K_OTHER;
        }
        gp_pst.systems[k]++;
        const uint8_t *st = *(const uint8_t *const *)(sys + 0xa4);
        if (st && *(const uint32_t *)st == CPU_STORE) gp_pst.particles[k] += *(const int *)(st + 0x10);
    }
}

/* before a timed call (p_pstats.S, the stubs with a pre step): PS_MGR or PS_SORT */
__attribute__((force_align_arg_pointer)) void gp_pst_pre(unsigned kind)
{
    int s = sm();
    if (kind == PS_MGR) {
        const uint8_t *mgr = *(const uint8_t *const *)MGR_PTR;
        if (!mgr) return;
        gp_pst.armed[s] += mgr[0xa8] != 0;
        if (!s) {
            gp_pst.live += *(const LONG *)(mgr + 0x50);
            if ((gp_pst.calls[PS_MGR][0] & 15) == 0) walk(mgr);
        }
    } else if (kind == PS_SORT) {
        int n = 0;
        for (const uint8_t *node = *(const uint8_t *const *)(uintptr_t)gp_pst_sort_head_va; node && n < 1000000;
             node = *(const uint8_t *const *)node) n++;
        gp_pst.sort_nodes[s] += n;
    }
}

static void report(void);

/* after a timed call: t0/t1 time stamps, ret = the original's eax */
__attribute__((force_align_arg_pointer))
void gp_pst_timed(unsigned kind, uint32_t t0lo, uint32_t t0hi, uint32_t t1lo, uint32_t t1hi, uint32_t ret)
{
    int s = sm();
    uint64_t t0 = (uint64_t)t0hi << 32 | t0lo, t1 = (uint64_t)t1hi << 32 | t1lo;
    if (kind >= PS_N) return;
    gp_pst.calls[kind][s]++;
    if (t1 > t0) ticks[kind][s] += t1 - t0;
    if (kind == PS_ROBJ) gp_pst.robj_particles[s] += (LONG)ret;
    if (kind == PS_MGR && !s && GetTickCount() - last_tick >= 60000) report();
}

uint64_t gp_pst_ticks(unsigned kind, int pass) { return ticks[kind][pass]; }

/* "a.bc" per frame, integers only */
static const char *per(char *b, LONG n, LONG f)
{
    unsigned long long x = f > 0 ? ((unsigned long long)(n < 0 ? 0 : n) * 100 + f / 2) / f : 0;
    snprintf(b, 24, "%llu.%02llu", x / 100, x % 100);
    return b;
}
/* "a.bc" ms per frame (tpms100 = time stamp ticks per ms, x100) */
static const char *ms(char *b, uint64_t t, LONG f, uint64_t tpms100)
{
    unsigned long long x = f > 0 && tpms100 ? (t * 10000ull / tpms100 + f / 2) / f : 0;
    snprintf(b, 24, "%llu.%02llu", x / 100, x % 100);
    return b;
}

static void report(void)
{
    LARGE_INTEGER q, qf;
    QueryPerformanceCounter(&q); QueryPerformanceFrequency(&qf);
    uint64_t tsc = __builtin_ia32_rdtsc(), dq = (uint64_t)q.QuadPart - last_qpc, dt = tsc - last_tsc;
    DWORD t = GetTickCount();
    int first = !last_tick;
    uint64_t tpms100 = !first && dq ? (uint64_t)((double)dt * (double)qf.QuadPart / (double)dq / 10.0) : 0;
    gp_pst_t d;
    LONG *a = (LONG *)&d; const LONG *x = (const LONG *)&gp_pst, *y = (const LONG *)&last;
    for (unsigned i = 0; i < sizeof d / sizeof(LONG); i++) a[i] = x[i] - y[i];
    uint64_t dtk[PS_N][2];
    for (int k = 0; k < PS_N; k++)
        for (int p = 0; p < 2; p++) { dtk[k][p] = ticks[k][p] - last_ticks[k][p]; last_ticks[k][p] = ticks[k][p]; }
    unsigned long secs = (t - last_tick) / 1000;
    last = gp_pst; last_tick = t ? t : 1; last_qpc = (uint64_t)q.QuadPart; last_tsc = tsc;
    if (first || !tpms100) return;
    LONG f = d.calls[PS_MGR][0], w = d.walks;
    char b[22][24];
    gp_log("particlestats: last %lu s, %ld main-view particle renders (= frames), %ld in the shadow-map pass; per "
           "frame, main | shadow-map: manager render %s | %s ms (armed %s | %s); RenderObject draw module %s | %s ms "
           "(%s | %s systems, %s | %s particles), of which colour setters %s | %s ms (%s | %s calls); sorting-renderer "
           "flush %s | %s ms (%s | %s sorted nodes); W3D emitter buffers %s | %s ms (%s | %s renders)",
           secs, f, d.calls[PS_MGR][1], ms(b[0], dtk[PS_MGR][0], f, tpms100), ms(b[1], dtk[PS_MGR][1], f, tpms100),
           per(b[2], d.armed[0], f), per(b[3], d.armed[1], f), ms(b[4], dtk[PS_ROBJ][0], f, tpms100),
           ms(b[5], dtk[PS_ROBJ][1], f, tpms100), per(b[6], d.calls[PS_ROBJ][0], f), per(b[7], d.calls[PS_ROBJ][1], f),
           per(b[8], d.robj_particles[0], f), per(b[9], d.robj_particles[1], f), ms(b[10], dtk[PS_COLOR][0], f, tpms100),
           ms(b[11], dtk[PS_COLOR][1], f, tpms100), per(b[12], d.calls[PS_COLOR][0], f),
           per(b[13], d.calls[PS_COLOR][1], f), ms(b[14], dtk[PS_SORT][0], f, tpms100),
           ms(b[15], dtk[PS_SORT][1], f, tpms100), per(b[16], d.sort_nodes[0], f), per(b[17], d.sort_nodes[1], f),
           ms(b[18], dtk[PS_PBUF][0], f, tpms100), ms(b[19], dtk[PS_PBUF][1], f, tpms100),
           per(b[20], d.calls[PS_PBUF][0], f), per(b[21], d.calls[PS_PBUF][1], f));
    char line[480]; int n = 0;
    n += snprintf(line + n, sizeof line - n, "particlestats: live particles %s per frame; systems per sampled frame "
                  "(%ld samples), by draw module: ", per(b[0], d.live, f), w);
    for (int k = 0; k < PS_KINDS && n < (int)sizeof line - 1; k++)
        n += snprintf(line + n, sizeof line - n, "%s %s (%s particles)%s", draw_name[k], per(b[1], d.systems[k], w),
                      per(b[2], d.particles[k], w), k + 1 < PS_KINDS ? ", " : "");
    if (n < (int)sizeof line - 1)
        snprintf(line + n, sizeof line - n, "; terrain %s%s", per(b[3], d.terrain, w), d.walk_cut ? "; LIST WALK CUT" : "");
    gp_log("%s", line);
}

void gp_pst_force_report(void)   /* tests: close the current window now */
{
    if (!last_tick) report();
    last_tick = GetTickCount() - 60000;
    report();
}

void gp_pst_exit_log(void)
{
    if (!on) return;
    gp_log("exit: particlestats: manager renders %ld main, %ld shadow-map; RenderObject module particles %ld main, "
           "%ld shadow-map", gp_pst.calls[PS_MGR][0], gp_pst.calls[PS_MGR][1], gp_pst.robj_particles[0],
           gp_pst.robj_particles[1]);
}

int gp_patch_particlestats(void)
{
    static const uint8_t c4716ee[] = {0xe8,0xf7,0xac,0xfd,0xff}, c4716f4[] = {0xe8,0x67,0xd5,0x0b,0x00};
    static const uint8_t c965277[] = {0xe8,0xc4,0x8d,0xba,0xff}, c96528b[] = {0xe8,0xb4,0x8f,0xba,0xff};
    static const uint8_t c9652cb[] = {0xe8,0x43,0x91,0xba,0xff};
    static const uint8_t vrobj[] = {0x00,0x4c,0x96,0x00}, vpbuf[] = {0x50,0xed,0x5a,0x00};
    gp_site s[16];
    int n = 0;
    gp_site_hash(&s[n++], 0x44c3ea, 0x14, 0x2c1a5847a0dbcb22ull);   /* manager render wrapper (cdecl, 1 arg) */
    gp_site_hash(&s[n++], 0x4716c7, 0x41, 0x414d958367cb524full);   /* the RenderParticles block */
    gp_site_hash(&s[n++], 0x964c00, 0x20, 0x3b134b3024aafc46ull);   /* RenderObject draw module head */
    gp_site_hash(&s[n++], 0x96530f, 0x0d, 0x3ef83f20715be5a0ull);   /* ... its ret 12 */
    gp_site_hash(&s[n++], 0x965240, 0x93, 0x5830f11525e2172full);   /* ... its three colour calls */
    gp_site_hash(&s[n++], 0x52ec60, 0x20, 0xf3cb1f7b0f1dec5aull);   /* sorting flush head */
    gp_site_hash(&s[n++], 0x52f740, 0x28, 0x5b299dbeee3bcb14ull);   /* ... and its ret */
    gp_site_hash(&s[n++], 0x5aed50, 0x9d, 0x3f32d07eeb1a6764ull);   /* ParticleBufferClass::Render (ret 4) */
    const struct { uint32_t va; const uint8_t *orig; void (*stub)(void); } calls[] = {
        {0x4716ee, c4716ee, gp_pst_mgr_stub}, {0x4716f4, c4716f4, gp_pst_sort_stub},
        {0x965277, c965277, gp_pst_c1_stub}, {0x96528b, c96528b, gp_pst_c2_stub}, {0x9652cb, c9652cb, gp_pst_c3_stub}};
    for (unsigned i = 0; i < sizeof calls / sizeof calls[0]; i++, n++) {
        gp_site_init(&s[n], calls[i].va, calls[i].orig, 5);
        gp_rel32(&s[n], 0, 0xe8, (void *)calls[i].stub);
    }
    uint32_t p = (uint32_t)(uintptr_t)gp_pst_robj_stub;
    gp_site_init(&s[n], 0xc32854, vrobj, 4); memcpy(s[n++].repl, &p, 4);
    p = (uint32_t)(uintptr_t)gp_pst_pbuf_stub;
    gp_site_init(&s[n], 0xbed2a0, vpbuf, 4); memcpy(s[n++].repl, &p, 4);
    gp_pst_mgr_cont = 0x44c3ea + gp_va_offset;
    gp_pst_sort_cont = 0x52ec60 + gp_va_offset;
    gp_pst_robj_cont = 0x964c00 + gp_va_offset;
    gp_pst_c1_cont = 0x50e040 + gp_va_offset;
    gp_pst_c2_cont = 0x50e244 + gp_va_offset;
    gp_pst_c3_cont = 0x50e413 + gp_va_offset;
    gp_pst_pbuf_cont = 0x5aed50 + gp_va_offset;
    if (!gp_apply("particlestats", s, n)) return 0;
    on = 1;
    return 1;
}
