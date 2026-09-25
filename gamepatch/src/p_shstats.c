/* shadowstats: counters for the shadow paths, logged every 60 s (no behaviour change).
 *
 * Per frame the stencil shadow volumes are built in one place only:
 *   RTS3DScene::Flush 0x470f44 ("RenderVolumeShadows", pass mode 0, scene+0x18 == 0)
 *   -> W3DShadowManager::renderShadows 0x499d6d (needs TheW3DVolumetricShadowManager 0xdd1718 and
 *      the manager's shadow-scene byte, set by Customized_Render at 0x47014b)
 *   -> W3DVolumetricShadowManager::renderShadows 0x4f43a6, which returns before its caster loop
 *      when the caster list is empty (0x4f4451), when TheGlobalData+0x60 (UseShadowVolumes) is 0
 *      (0x4f445e) or without a D3D device (0x4f4467), and otherwise always reaches the caster loop
 *      (jmp 0x4f4fe8 at 0x4f4fa3): the only per-frame caller of Update 0x4f3906, hence of
 *      updateVolumes, updateMeshVolume, buildSilhouette and constructVolume.
 * GameLOD (0x601c62, at 0x601d4f) clears UseShadowVolumes and UseShadowDecals whenever
 * UseShadowMapping is on (EA's UltraHigh level sets all three); then no volume shadow is created
 * (0x4f24d2) and the shadows come from the shadow-map pass UpdateShadowMap 0x47d5c9 (called every
 * frame from 0x449df5; it works only with TheGlobalData+0x62 set). A display switch (0x6bff7b via
 * W3DDisplay vtable +0x28 = 0x49d565) swaps shadow mapping for volumes while display+0x18 is set.
 *
 * Sites: the calls at 0x499d83 (-> 0x4f43a6) and 0x449df5 (-> 0x47d5c9) go through a counting stub
 * that then jumps to the original callee with every register as it was. The 60 s lines also carry
 * those flags, the number of volume casters and the edgemap / shadowpar counters. */
#include "par_shadow.h"

#define GD_PTR     0xde4364     /* TheGlobalData */
#define GD_VOLUMES 0x60         /* UseShadowVolumes */
#define GD_DECALS  0x61         /* UseShadowDecals */
#define GD_MAPPING 0x62         /* UseShadowMapping */
#define VOL_MGR    0xdd1718     /* TheW3DVolumetricShadowManager: [0] = first caster */
#define DX_DEVICE  0xdd3474     /* the D3D device renderShadows tests */
#define DISPLAY    0xde4958     /* TheDisplay (inferred: set from the display factory at 0x646edd) */

gp_shst_t gp_shst;
static gp_shst_t last;
static DWORD last_tick;
static int on;

static const uint8_t *gd(void) { return *(const uint8_t *const *)GD_PTR; }

/* the same tests, in the same order, as 0x4f444e..0x4f446d */
__attribute__((force_align_arg_pointer))
void gp_shst_rs(const uint8_t *mgr)
{
    const uint8_t *g = gd();
    gp_shst.rs_calls++;
    if (!*(void *const *)mgr) gp_shst.rs_empty++;
    else if (!g || !g[GD_VOLUMES]) gp_shst.rs_voloff++;
    else if (!*(void *const *)DX_DEVICE) gp_shst.rs_nodev++;
    else gp_shst.rs_reach++;
    gp_shadow_periodic();
}

__attribute__((force_align_arg_pointer))
void gp_shst_sm(void)
{
    const uint8_t *g = gd();
    gp_shst.sm_calls++;
    if (g && g[GD_MAPPING]) gp_shst.sm_on++;
    gp_shadow_periodic();
}

/* main thread only (the stubs above, p_anim's periodic): the caster list is only changed there */
void gp_shadow_periodic(void)
{
    if (!on && !gp_cv_on && !gp_sp_on) return;
    DWORD t = GetTickCount();
    gp_shst.cv_calls = gp_cv_calls; gp_shst.cv_chained = gp_cv_chained;
    gp_shst.sp_loops = gp_sp_loops; gp_shst.sp_jobs = gp_sp_stats.jobs;
    gp_shst.sp_inline = gp_sp_stats.inline_blocks;
    if (!last_tick) { last_tick = t; last = gp_shst; return; }
    if (t - last_tick < 60000) return;
    const uint8_t *g = gd(), *mgr = *(const uint8_t *const *)VOL_MGR, *disp = *(const uint8_t *const *)DISPLAY;
    int casters = 0, enabled = 0;
    if (mgr)
        for (const uint8_t *s = *(const uint8_t *const *)mgr; s && casters < 1000000; s = AT(s, SH_NEXT, const uint8_t *)) {
            casters++;
            enabled += s[4] && !s[5];
        }
    unsigned long secs = (t - last_tick) / 1000;
    gp_log("shadows: last %lu s: LOD flags volumes %d decals %d shadow-mapping %d (display switch %d); "
           "shadow-map pass %ld calls, %ld with mapping on; renderShadows %ld calls: %ld reached the caster "
           "loop, returned early %ld with no casters, %ld with volumes off, %ld without a device; volume "
           "manager %s, %d casters (%d enabled)", secs, g ? g[GD_VOLUMES] : -1, g ? g[GD_DECALS] : -1,
           g ? g[GD_MAPPING] : -1, disp ? disp[0x18] : -1, gp_shst.sm_calls - last.sm_calls,
           gp_shst.sm_on - last.sm_on, gp_shst.rs_calls - last.rs_calls, gp_shst.rs_reach - last.rs_reach,
           gp_shst.rs_empty - last.rs_empty, gp_shst.rs_voloff - last.rs_voloff, gp_shst.rs_nodev - last.rs_nodev,
           mgr ? "present" : "absent", casters, enabled);
    gp_log("shadows: last %lu s: edgemap %ld constructVolume calls (%ld with edges to chain)%s; shadowpar %lld "
           "caster loops, %lld volumes on the pool, %lld blocks inline%s", secs,
           gp_shst.cv_calls - last.cv_calls, gp_shst.cv_chained - last.cv_chained, gp_cv_on ? "" : " [edgemap off]",
           gp_shst.sp_loops - last.sp_loops, gp_shst.sp_jobs - last.sp_jobs, gp_shst.sp_inline - last.sp_inline,
           !gp_sp_on ? " [shadowpar off]" : gp_sp_disabled ? " [shadowpar switched itself off]" : "");
    last = gp_shst;
    last_tick = t;
}

void gp_shadow_exit_log(void)
{
    if (!on && !gp_cv_on && !gp_sp_on) return;
    gp_log("exit: shadows: renderShadows %ld calls, %ld reached the caster loop (early: %ld no casters, %ld "
           "volumes off, %ld no device); shadow-map pass %ld calls, %ld with mapping on; edgemap %ld "
           "constructVolume calls; shadowpar %lld caster loops, %lld volumes on the pool", gp_shst.rs_calls,
           gp_shst.rs_reach, gp_shst.rs_empty, gp_shst.rs_voloff, gp_shst.rs_nodev, gp_shst.sm_calls,
           gp_shst.sm_on, (long)gp_cv_calls, gp_sp_loops, gp_sp_stats.jobs);
}

int gp_patch_shadowstats(void)
{
    static const uint8_t rs[] = {0xe8,0x1e,0xa6,0x05,0x00};   /* 0x499d83 call 0x4f43a6 */
    static const uint8_t sm[] = {0xe8,0xcf,0x37,0x03,0x00};   /* 0x449df5 call 0x47d5c9 */
    gp_site s[6];
    gp_site_hash(&s[0], 0x499d6d, 0x22, 0x7e63552ca4deb27aull);   /* W3DShadowManager::renderShadows */
    gp_site_hash(&s[1], 0x4f43a6, 0xcd, 0x947b4b8e54779eceull);   /* renderShadows up to its early-outs */
    gp_site_hash(&s[2], 0x4f4f95, 0x10, 0xc82602f5c3b13599ull);   /* ... and its jump into the caster loop */
    gp_site_hash(&s[3], 0x47d5c9, 0x25, 0x16dda85b86831e90ull);   /* UpdateShadowMap's UseShadowMapping test */
    gp_site_init(&s[4], 0x499d83, rs, sizeof rs);
    gp_rel32(&s[4], 0, 0xe8, (void *)gp_shst_rs_stub);
    gp_site_init(&s[5], 0x449df5, sm, sizeof sm);
    gp_rel32(&s[5], 0, 0xe8, (void *)gp_shst_sm_stub);
    gp_shst_rs_cont = 0x4f43a6 + gp_va_offset;
    gp_shst_sm_cont = 0x47d5c9 + gp_va_offset;
    if (!gp_apply("shadowstats", s, 6)) return 0;
    on = 1;
    return 1;
}
