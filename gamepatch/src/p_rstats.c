/* renderstats: counters for the UltraHigh render model (no behaviour change), logged every 60 s,
 * plus one log line per shadow-mode switch and per static LOD change.
 *
 * What the counters test (static analysis):
 * - UpdateShadowMap 0x47d5c9 renders the whole scene a second time (WW3D::Render 0x517c60 from the
 *   light's camera, byte 0xdd1e44 set). The scene pass mode (+0x7ec) is 0 then, so Customized_Render
 *   0x46fe84 runs Visibility_Check (RTS3DScene vt+0x6c = 0x470b83) a second time, and the FX flush
 *   0x574406 runs a second time, CPU skinning included: 0x574148 skins every mesh of its list with
 *   MeshClass::Get_Deformed_Vertices 0x549370 (-> 0x56b750) into a dynamic vertex buffer
 *   (0x573464), once per flush. Legacy (non-FX) meshes skip the shadow pass (0x54b773).
 * - The display switch 0x6bff7b (display+0x18; only caller W3DDisplay vt+0x28 = 0x49d565) turns
 *   shadow mapping off and volume shadows on while set; GameLOD 0x601c62 (only caller 0x6020d1)
 *   is the other writer of those flags in normal play.
 *
 * Sites (every hook runs the original callee with every general register and xmm0-7 as they
 * were, the flags aside; p_rstats.S):
 *   0x44bb00, 0x44bbf5  call 0x449cf8 (render helper: one drawn frame)        -> frames
 *   0xbdc3d4            RTS3DScene vtable slot of Visibility_Check 0x470b83      -> visibility passes
 *   0x57442a            call 0x574113 at the start of the FX flush: the three FX lists (rigid
 *                       +0/+4, CPU-skinned +0xc/+0x10, GPU-skinned +0x18/+0x1c; 32-byte entries)
 *   0x57423b            call 0x573464: one CPU-skinned FX mesh ([esp+4]); vertices [[mesh+0xc4]+0x28]
 *   0x548291            call 0x549370: one CPU-skinned mesh of the DX8 skin container (ecx)
 *   0x49d57e, 0x49d585  call 0x6bff7b (display switch)                           -> log lines
 *   0x6020d1            call 0x601c62 (static LOD level applied)                 -> log lines
 * Timed (time stamp counter before and after the call, p_rstats.S TIMED; the ticks are converted
 * with QueryPerformanceCounter over each 60 s window), per pass:
 *   0x47d70c, 0x518065  call 0x517c60 WW3D::Render (shadow-map pass; RenderViews and reflection)
 *   0xbdc3c4            RTS3DScene vtable slot of Customized_Render 0x46fe84 (visibility, the
 *                       UpdateList loop, terrain and the object loop)
 *   0xbdc3d4            Visibility_Check 0x470b83 (includes the animation its bounding spheres
 *                       evaluate lazily: the first pass of a frame pays for every moved unit)
 *   0x47009f, 0x47010c  call 0x46f48e renderOneObject (light environment + robj->Render queuing)
 *   0x471a3b            call 0x470f44 RTS3DScene::Flush
 *   0x517db2 (call), 0x516d91 (jmp)  0x574406 FX shader flush (effects, skinning, draws)
 * plus the HLod pose evaluations and animdedup skips per pass (p_anim.c gp_ad_pass).
 * Every count is split by 0xdd1e44 (1 = inside the shadow-map pass). */
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>

#define SM_FLAG    0xdd1e44     /* byte: 1 while UpdateShadowMap renders */
#define GD_PTR     0xde4364     /* TheGlobalData: +0x60 volumes, +0x61 decals, +0x62 mapping */
#define DISPLAY    0xde4958     /* TheDisplay: +0x14 mode, +0x18 switch, +0x19 3D view while switched */
#define LOD_MGR    0xde3b84     /* TheGameLODManager: +0x1768 current static level (-1 = none yet) */

typedef struct {
    LONG frames, vis[2], flush[2], rigid[2], cpuskin[2], gpuskin[2];
    LONG fxskin[2], fxverts[2], dxskin[2], dxverts[2];
} rst_t;
static rst_t rs, last;
static DWORD last_tick;
static int on;
/* timed calls: T_* = the kind numbers of p_rstats.S */
enum { T_RENDER, T_CR, T_VIS, T_OBJ, T_FLUSH, T_FX, T_N };
static uint64_t tticks[T_N][2], last_tticks[T_N][2];
static LONG tcalls[T_N][2], last_tcalls[T_N][2];
static LONG last_pose[2][2];
static uint64_t last_tsc, last_qpc;

uint32_t gp_rst_w3r_cont, gp_rst_cr_cont, gp_rst_obj_cont, gp_rst_flush_cont, gp_rst_fx_cont;
uint32_t gp_rst_frame_cont, gp_rst_vis_cont, gp_rst_fxl_cont, gp_rst_fxs_cont, gp_rst_dxs_cont;
uint32_t gp_rst_sw_fn, gp_rst_lod_fn;
LONG gp_rst_logged; uint32_t gp_rst_last_caller; int gp_rst_last_arg;   /* for the tests */

/* the counters in rst_t order: frames, vis[2], flush[2], rigid[2], cpuskin[2], gpuskin[2],
 * fxskin[2], fxverts[2], dxskin[2], dxverts[2] (tests) */
void gp_rst_get(LONG *out, unsigned n)
{
    memcpy(out, &rs, n * sizeof(LONG) < sizeof rs ? n * sizeof(LONG) : sizeof rs);
}

void gp_rst_timer(unsigned kind, int pass, LONG *calls, uint64_t *ticks)
{
    *calls = tcalls[kind][pass]; *ticks = tticks[kind][pass];
}

static int sm(void) { return *(volatile uint8_t *)SM_FLAG != 0; }
static const uint8_t *gd(void) { return *(const uint8_t *const *)GD_PTR; }
static const uint8_t *disp(void) { return *(const uint8_t *const *)DISPLAY; }
static int lod_level(void)
{
    const uint8_t *m = *(const uint8_t *const *)LOD_MGR;
    return m ? *(const int *)(m + 0x1768) : -2;
}
static LONG verts(const uint8_t *mesh)
{
    const uint8_t *model = mesh ? *(const uint8_t *const *)(mesh + 0xc4) : NULL;
    return model ? *(const LONG *)(model + 0x28) : 0;
}

/* "a.bc" per frame, integers only */
static const char *per(char *b, LONG n, LONG f)
{
    unsigned long long x = f > 0 ? ((unsigned long long)(n < 0 ? 0 : n) * 100 + f / 2) / f : 0;
    snprintf(b, 24, "%llu.%02llu", x / 100, x % 100);
    return b;
}

/* "a.bc" ms per frame from ticks, integers only (tpms = ticks per ms, x100) */
static const char *ms(char *b, uint64_t ticks, LONG f, uint64_t tpms100)
{
    unsigned long long x = f > 0 && tpms100 ? (ticks * 10000ull / tpms100 + f / 2) / f : 0;
    snprintf(b, 24, "%llu.%02llu", x / 100, x % 100);
    return b;
}

/* the timing line of one window (f frames); f < 0: start the first window */
static void timing_line(LONG f)
{
    LARGE_INTEGER q, qf;
    QueryPerformanceCounter(&q); QueryPerformanceFrequency(&qf);
    uint64_t tsc = __builtin_ia32_rdtsc(), dq = (uint64_t)q.QuadPart - last_qpc, dt = tsc - last_tsc;
    /* time stamp counter ticks per ms, x100 */
    uint64_t tpms100 = f >= 0 && dq ? (uint64_t)((double)dt * (double)qf.QuadPart / (double)dq / 10.0) : 0;
    uint64_t d[T_N][2]; LONG c[T_N][2], pe[2][2];
    for (int k = 0; k < T_N; k++)
        for (int p = 0; p < 2; p++) {
            d[k][p] = tticks[k][p] - last_tticks[k][p]; c[k][p] = tcalls[k][p] - last_tcalls[k][p];
            last_tticks[k][p] = tticks[k][p]; last_tcalls[k][p] = tcalls[k][p];
        }
    for (int p = 0; p < 2; p++)
        for (int i = 0; i < 2; i++) { pe[p][i] = gp_ad_pass[p][i] - last_pose[p][i]; last_pose[p][i] = gp_ad_pass[p][i]; }
    last_qpc = (uint64_t)q.QuadPart; last_tsc = tsc;
    if (!tpms100) return;
    char b[16][24];
    gp_log("renderstats: ms per frame, main passes | shadow-map pass: WW3D::Render %s | %s (%s | %s calls), of "
           "which Customized_Render %s | %s, in it Visibility_Check %s | %s and renderOneObject %s | %s (%s | %s "
           "objects); Flush %s | %s; FX shader flushes %s | %s",
           ms(b[0], d[T_RENDER][0], f, tpms100), ms(b[1], d[T_RENDER][1], f, tpms100), per(b[2], c[T_RENDER][0], f),
           per(b[3], c[T_RENDER][1], f), ms(b[4], d[T_CR][0], f, tpms100), ms(b[5], d[T_CR][1], f, tpms100),
           ms(b[6], d[T_VIS][0], f, tpms100), ms(b[7], d[T_VIS][1], f, tpms100), ms(b[8], d[T_OBJ][0], f, tpms100),
           ms(b[9], d[T_OBJ][1], f, tpms100), per(b[10], c[T_OBJ][0], f), per(b[11], c[T_OBJ][1], f),
           ms(b[12], d[T_FLUSH][0], f, tpms100), ms(b[13], d[T_FLUSH][1], f, tpms100), ms(b[14], d[T_FX][0], f, tpms100),
           ms(b[15], d[T_FX][1], f, tpms100));
    gp_log("renderstats: HLod pose evaluations per frame, main passes | shadow-map pass: %s | %s; Render "
           "re-evaluations skipped by animdedup %s | %s (time stamp counter %llu.%02llu ticks per us)",
           per(b[0], pe[0][0], f), per(b[1], pe[1][0], f), per(b[2], pe[0][1], f), per(b[3], pe[1][1], f),
           (unsigned long long)(tpms100 / 100000), (unsigned long long)(tpms100 / 1000 % 100));
}

static void periodic(void)
{
    DWORD t = GetTickCount();
    if (!last_tick) { last_tick = t; last = rs; timing_line(-1); return; }
    if (t - last_tick < 60000) return;
    rst_t d;
    LONG *a = (LONG *)&d; const LONG *x = (const LONG *)&rs, *y = (const LONG *)&last;
    for (unsigned i = 0; i < sizeof d / sizeof(LONG); i++) a[i] = x[i] - y[i];
    LONG f = d.frames;
    char b[10][24];
    gp_log("renderstats: last %lu s, %ld frames; per frame, main passes | shadow-map pass: visibility passes "
           "%s | %s; FX flushes %s | %s; FX draws rigid %s | %s, CPU-skinned %s | %s, GPU-skinned %s | %s",
           (unsigned long)((t - last_tick) / 1000), f, per(b[0], d.vis[0], f), per(b[1], d.vis[1], f),
           per(b[2], d.flush[0], f), per(b[3], d.flush[1], f), per(b[4], d.rigid[0], f), per(b[5], d.rigid[1], f),
           per(b[6], d.cpuskin[0], f), per(b[7], d.cpuskin[1], f), per(b[8], d.gpuskin[0], f), per(b[9], d.gpuskin[1], f));
    gp_log("renderstats: CPU skinning per frame, main | shadow-map pass: FX meshes %s | %s (%s | %s vertices), "
           "DX8 skin meshes %s | %s (%s | %s vertices)", per(b[0], d.fxskin[0], f), per(b[1], d.fxskin[1], f),
           per(b[2], d.fxverts[0], f), per(b[3], d.fxverts[1], f), per(b[4], d.dxskin[0], f),
           per(b[5], d.dxskin[1], f), per(b[6], d.dxverts[0], f), per(b[7], d.dxverts[1], f));
    timing_line(f);
    last = rs; last_tick = t;
}

/* tests: end the current 60 s window now */
void gp_rst_force_report(void)
{
    if (last_tick) last_tick = GetTickCount() - 60000;
    periodic();
}

/* called from p_rstats.S (main thread only: the render helper and everything under it) */
__attribute__((force_align_arg_pointer)) void gp_rst_frame(void) { rs.frames++; periodic(); if (gp_mon_on) gp_mon_frame(); }
__attribute__((force_align_arg_pointer))
void gp_rst_timed(unsigned kind, uint32_t t0lo, uint32_t t0hi, uint32_t t1lo, uint32_t t1hi)
{
    int s = sm();
    uint64_t t0 = (uint64_t)t0hi << 32 | t0lo, t1 = (uint64_t)t1hi << 32 | t1lo;
    if (kind >= T_N) return;
    tcalls[kind][s]++;
    if (t1 > t0) tticks[kind][s] += t1 - t0;
    if (kind == T_VIS) rs.vis[s]++;
}
__attribute__((force_align_arg_pointer)) void gp_rst_fxlists(const uint32_t *l)
{
    int s = sm();
    rs.flush[s]++;
    rs.rigid[s] += (LONG)((l[1] - l[0]) / 32);
    rs.cpuskin[s] += (LONG)((l[4] - l[3]) / 32);
    rs.gpuskin[s] += (LONG)((l[7] - l[6]) / 32);
}
__attribute__((force_align_arg_pointer)) void gp_rst_skin_fx(const uint8_t *mesh)
{
    int s = sm();
    rs.fxskin[s]++; rs.fxverts[s] += verts(mesh);
}
__attribute__((force_align_arg_pointer)) void gp_rst_skin_dx8(const uint8_t *mesh)
{
    int s = sm();
    rs.dxskin[s]++; rs.dxverts[s] += verts(mesh);
}

static void flags(char *b, size_t n)
{
    const uint8_t *g = gd(), *d = disp();
    snprintf(b, n, "switch %d, 3D view %d, display mode %d; volumes %d, decals %d, mapping %d; static LOD level %d",
             d ? d[0x18] : -1, d ? d[0x19] : -1, d ? *(const int *)(d + 0x14) : -1, g ? g[0x60] : -1,
             g ? g[0x61] : -1, g ? g[0x62] : -1, lod_level());
}
__attribute__((force_align_arg_pointer)) void gp_rst_sw_before(int arg, uint32_t caller)
{
    char b[160];
    flags(b, sizeof b);
    gp_rst_logged++; gp_rst_last_caller = caller; gp_rst_last_arg = arg;
    gp_log("renderstats: display switch %d requested (W3DDisplay vt+0x28 called from %08lx, frame %ld); before: %s",
           arg & 0xff, (unsigned long)caller, rs.frames, b);
}
__attribute__((force_align_arg_pointer)) void gp_rst_lod_before(int level, uint32_t caller)
{
    char b[160];
    flags(b, sizeof b);
    gp_rst_logged++; gp_rst_last_caller = caller; gp_rst_last_arg = level;
    gp_log("renderstats: static LOD level %d applied (setStaticLODLevel called from %08lx, frame %ld); before: %s",
           level, (unsigned long)caller, rs.frames, b);
}
__attribute__((force_align_arg_pointer)) void gp_rst_after(void)
{
    char b[160];
    flags(b, sizeof b);
    gp_rst_logged++;
    gp_log("renderstats:   after: %s", b);
}

void gp_rst_exit_log(void)
{
    if (!on) return;
    gp_log("exit: renderstats: %ld frames; visibility passes %ld main, %ld shadow-map; CPU-skinned FX meshes %ld "
           "main, %ld shadow-map; renderOneObject %ld main, %ld shadow-map", rs.frames, rs.vis[0], rs.vis[1],
           rs.fxskin[0], rs.fxskin[1], tcalls[T_OBJ][0], tcalls[T_OBJ][1]);
}

int gp_patch_renderstats(void)
{
    static const uint8_t c44bb00[] = {0xe8,0xf3,0xe1,0xff,0xff}, c44bbf5[] = {0xe8,0xfe,0xe0,0xff,0xff};
    static const uint8_t c57442a[] = {0xe8,0xe4,0xfc,0xff,0xff}, c57423b[] = {0xe8,0x24,0xf2,0xff,0xff};
    static const uint8_t c548291[] = {0xe8,0xda,0x10,0x00,0x00};
    static const uint8_t c49d57e[] = {0xe8,0xf8,0x29,0x22,0x00}, c49d585[] = {0xe8,0xf1,0x29,0x22,0x00};
    static const uint8_t c6020d1[] = {0xe8,0x8c,0xfb,0xff,0xff};
    static const uint8_t c47d70c[] = {0xe8,0x4f,0xa5,0x09,0x00}, c518065[] = {0xe8,0xf6,0xfb,0xff,0xff};
    static const uint8_t c47009f[] = {0xe8,0xea,0xf3,0xff,0xff}, c47010c[] = {0xe8,0x7d,0xf3,0xff,0xff};
    static const uint8_t c471a3b[] = {0xe8,0x04,0xf5,0xff,0xff}, c517db2[] = {0xe8,0x4f,0xc6,0x05,0x00};
    static const uint8_t j516d91[] = {0xe9,0x70,0xd6,0x05,0x00};
    static const uint8_t vt[] = {0x83,0x0b,0x47,0x00};                      /* 0x470b83 */
    static const uint8_t vtcr[] = {0x84,0xfe,0x46,0x00};                    /* 0x46fe84 */
    const struct { uint32_t va; const uint8_t *orig; void (*stub)(void); } calls[] = {
        {0x44bb00, c44bb00, gp_rst_frame_stub}, {0x44bbf5, c44bbf5, gp_rst_frame_stub},
        {0x57442a, c57442a, gp_rst_fxl_stub}, {0x57423b, c57423b, gp_rst_fxs_stub},
        {0x548291, c548291, gp_rst_dxs_stub}, {0x49d57e, c49d57e, gp_rst_sw_stub},
        {0x49d585, c49d585, gp_rst_sw_stub}, {0x6020d1, c6020d1, gp_rst_lod_stub},
        {0x47d70c, c47d70c, gp_rst_w3r_stub}, {0x518065, c518065, gp_rst_w3r_stub},
        {0x47009f, c47009f, gp_rst_obj_stub}, {0x47010c, c47010c, gp_rst_obj_stub},
        {0x471a3b, c471a3b, gp_rst_flush_stub}, {0x517db2, c517db2, gp_rst_fx_stub}};
    gp_site s[40];
    int n = 0;
    /* the callees' conventions the timed stubs rely on (argument count, ret n) and the callers */
    gp_site_hash(&s[n++], 0x517c60, 0x18, 0x3f76ea4c1d0072fdull);   /* WW3D::Render head */
    gp_site_hash(&s[n++], 0x46fe84, 0x13, 0x3e07a522438504c0ull);   /* Customized_Render head */
    gp_site_hash(&s[n++], 0x470b83, 0x10, 0x2f3db3554bba74f6ull);   /* Visibility_Check head */
    gp_site_hash(&s[n++], 0x46f48e, 0x13, 0x7f4b03652a989f60ull);   /* renderOneObject head */
    gp_site_hash(&s[n++], 0x470f44, 0x15, 0x3927fc86108aaeb6ull);   /* Flush head */
    gp_site_hash(&s[n++], 0x47d6f6, 0x20, 0x0195f8063ca4a1c6ull);   /* UpdateShadowMap at its Render */
    gp_site_hash(&s[n++], 0x518050, 0x20, 0x4cb453b98e998163ull);   /* the Render wrapper */
    gp_site_hash(&s[n++], 0x470095, 0x20, 0xc19a11eef08c9c55ull);   /* the object loop's two calls */
    gp_site_hash(&s[n++], 0x470102, 0x18, 0xc898a87dc40fb0a6ull);
    gp_site_hash(&s[n++], 0x471a2c, 0x15, 0xa6f4ceef020ba833ull);   /* RTS3DScene::Render tail */
    gp_site_hash(&s[n++], 0x517d9d, 0x1a, 0x25c916805e790adaull);   /* WW3D::Render at its flushes */
    gp_site_hash(&s[n++], 0x516d80, 0x16, 0x927621a45a0dc155ull);   /* the DX8 flush wrapper */
    gp_site_hash(&s[n++], 0x49d565, 0x9a, 0xfad25945c7928645ull);   /* W3DDisplay vt+0x28: its frame at the calls */
    gp_site_hash(&s[n++], 0x6020b4, 0x33, 0x9c4a8979da632b2aull);   /* setStaticLODLevel */
    gp_site_hash(&s[n++], 0x574406, 0x40, 0x4da72649c371464eull);   /* FX flush head: ecx = the lists */
    gp_site_hash(&s[n++], 0x574148, 0x16f, 0xab8eb9ec73a740adull);  /* CPU-skinned FX list: [esp+4] = mesh */
    gp_site_hash(&s[n++], 0x548271, 0x25, 0x32e15f21f2172a4bull);   /* DX8 skin container: ecx = mesh */
    gp_site_hash(&s[n++], 0x44bafd, 0x08, 0x90dd18e4b7cf63cbull);   /* W3DDisplay::draw -> render helper */
    gp_site_hash(&s[n++], 0x44bbf0, 0x0a, 0xaa2583ab532e2737ull);
    for (unsigned i = 0; i < sizeof calls / sizeof calls[0]; i++, n++) {
        gp_site_init(&s[n], calls[i].va, calls[i].orig, 5);
        gp_rel32(&s[n], 0, 0xe8, (void *)calls[i].stub);
    }
    gp_site_init(&s[n], 0x516d91, j516d91, 5);
    gp_rel32(&s[n++], 0, 0xe9, (void *)gp_rst_fx_stub);
    gp_site_init(&s[n], 0xbdc3d4, vt, 4);
    uint32_t stub = (uint32_t)(uintptr_t)gp_rst_vis_stub;
    memcpy(s[n++].repl, &stub, 4);
    gp_site_init(&s[n], 0xbdc3c4, vtcr, 4);
    stub = (uint32_t)(uintptr_t)gp_rst_cr_stub;
    memcpy(s[n++].repl, &stub, 4);
    gp_rst_w3r_cont = 0x517c60 + gp_va_offset;
    gp_rst_cr_cont = 0x46fe84 + gp_va_offset;
    gp_rst_obj_cont = 0x46f48e + gp_va_offset;
    gp_rst_flush_cont = 0x470f44 + gp_va_offset;
    gp_rst_fx_cont = 0x574406 + gp_va_offset;
    gp_rst_frame_cont = 0x449cf8 + gp_va_offset;
    gp_rst_vis_cont = 0x470b83 + gp_va_offset;
    gp_rst_fxl_cont = 0x574113 + gp_va_offset;
    gp_rst_fxs_cont = 0x573464 + gp_va_offset;
    gp_rst_dxs_cont = 0x549370 + gp_va_offset;
    gp_rst_sw_fn = 0x6bff7b + gp_va_offset;
    gp_rst_lod_fn = 0x601c62 + gp_va_offset;
    if (!gp_apply("renderstats", s, n)) return 0;
    on = 1;
    return 1;
}
