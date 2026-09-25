/* animdedup and animdecode: animation evaluation done once instead of again with the same result.
 *
 * animdedup. Animatable3DObjClass::Render (0x5a4dd0; HLodClass::Render calls it for every drawn
 * unit, in every pass that draws it) runs Single_Anim_Progress and then, because progress always
 * clears the pose-valid flag (+0xf4), the whole evaluation USOT (vt+0xa8 = HLodClass::USOT
 * 0x59cd70 -> Animatable3DObjClass::USOT 0x5a5050 -> 0x5a3f70 -> HTree Anim_Update, then the
 * pose is copied to every sub-mesh of every LOD). A unit whose pose was already evaluated at this
 * sync time (Visibility_Check's bounding sphere -> Get_Bone_Transform evaluates every unit that
 * moved this frame; the shadow-map and reflection passes Render again) is evaluated again with the
 * same inputs. Here, at Render's progress call (0x5a4dfc), the Anim_Update part is skipped when:
 *   - main thread; the object is an HLod (vtable 0xbec7f0 whose USOT slot is still 0x59cd70);
 *     no master (+0xfc; slaves copy another object's pose); pose valid; sub-objects not dirty;
 *   - last sync time (+0x114) == WW3D::SyncTime (0xdd1e0c), so progress would not write it;
 *   - Compute_Current_Frame (0x5a4770, the original, called here) returns the stored frame
 *     (+0x108) and direction (+0x118) bit for bit, so progress would change nothing but clear the
 *     valid flag (the original evaluation already ran progress twice at this sync time);
 *   - a snapshot of Anim_Update's inputs, taken when the single-animation path last evaluated this
 *     object (0x5a512c, at this same sync time), equals the current ones bit for bit: animation,
 *     frame, the object's transform (48 bytes), the HTree pointer and its header +0x10..+0x33
 *     (pivot count and array, scale, the bone-control list, which must be empty, the cached motion
 *     and decode stream). Any other evaluation of the object (0x5a5050 entered by any path) drops
 *     the snapshot first; valid is set only by that function family (checked: 0x5a3f40, 0x5a3f70,
 *     0x5a3fe0, 0x5a4020, 0x5a5050), and every mutator clears it (Set_Transform 0x5a4280/0x59ae20
 *     also sets the dirty bit, Set_Position 0x5a42a0, Set_Animation 0x5a4320/0x5a4340/0x5a4460/
 *     0x5a44e0, Control_Bone 0x5a4670; Capture/Release_Bone 0x5a4610/0x5a4630 do not, which is
 *     why the control list is compared).
 *   - the animation is a compressed one with channels (class 1, +0x58) and the integer frame is
 *     below every channel's frame count: the per-HTree decode stream then gives the same values
 *     for the same frame again (AdaptiveDelta adds the same deltas in the same order from any cached
 *     frame below the count; from a cached frame at or past it the decoder returns the cached value
 *     as is, which would not repeat the first evaluation, see animdecode).
 * Anim_Update is a function of exactly those inputs plus read-only data (the channels), so the
 * pivots it would write are the ones already there. Everything else still runs as before: Render clears valid as progress would,
 * calls HLodClass::USOT, whose first call (0x59cd79) is answered by setting valid, and then the
 * pose is copied to every sub-object (Set_Transform, animation-hidden, fade, their USOT) exactly as
 * the original does, so sub-object writes made by other code in between are overwritten as before
 * (the fade/hidden question R1 left open does not arise). Test: tests/t_anim.c.
 *
 * animdecode. A motion channel queried without a cache stream (the second animation of a blend
 * via HAnim Get_Translation/Get_Orientation 0x58fe70/0x5904c0, and other direct HAnim queries)
 * decodes from frame 0 on every call (O(frame)). The six decoders (0x5b19c0 0x5b1aba 0x5b1c00:
 * 4-bit deltas, 1/3/4 components; 0x5b1d49 0x5b1e2b 0x5b1f5b: 8-bit) continue from any (frame,
 * value) pair they produced themselves: that is how the game's own per-HTree stream uses them
 * (Get_QuatVector 0x5b22a8: decode(rec.A, rec.frame, f, &rec.A, &rec.B)); the value at frame f is
 * the same chain of float additions whatever the starting point, and a start past f restarts from
 * frame 0. One exception, found by the test: a start frame at or past the channel's frame count
 * (+0xc) returns the start value at once, while from frame 0 the last block is decoded to its end,
 * so a cached frame is used only while it is below the count. Here those six from-zero call sites use a small cache keyed by channel instead of the
 * stream (main thread; entries are dropped when a channel is destroyed, 0x5b18fe, and also checked
 * against its vtable, data pointer and frame count). Test: tests/t_adecode.c. */
#include "gp.h"
#include "gp_render.h"
#include <string.h>
#include <emmintrin.h>

uint32_t gp_ad_vt_hlod = 0xbec7f0;
uint32_t gp_ad_synctime_va = 0xdd1e0c;
volatile LONG gp_ad_stats[4];
volatile LONG gp_adq_stats[3];
volatile LONG gp_ad_pass[2][2];              /* renderstats: per pass (byte 0xdd1e44), evaluations, skips */
#define AD_PASS (*(volatile uint8_t *)0xdd1e44 != 0)
extern uint32_t gp_ad_skip, gp_ad_usot_orig, gp_adq_dtor_cont;
uint32_t gp_ad_call_ccf(uint32_t fn, void *self, uint32_t *dir);
uint32_t gp_call_this0(uint32_t fn, void *self);
void gp_call_this3(uint32_t fn, void *self, uint32_t a, uint32_t b, uint32_t c);
void gp_call_dec(uint32_t fn, const void *self, const void *src, uint32_t f0, uint32_t dst, void *a, void *b);

#define U32(p, o) (*(volatile uint32_t *)((uint8_t *)(uintptr_t)(p) + (o)))
#define U8(p, o) (*(volatile uint8_t *)((uint8_t *)(uintptr_t)(p) + (o)))
static uint32_t fn_progress, fn_ccf, fn_single, fn_usot_hlod;
static int dedup_on, decode_on;

/* ---- periodic summary (main thread) ---- */
static DWORD last_tick;
static LONG last_ad[4], last_adq[3];
static LONG usot_count;
static void anim_detail(DWORD secs);
static void periodic(void)
{
    gp_shadow_periodic();
    DWORD t = GetTickCount();
    if (!last_tick) { last_tick = t; return; }
    if (t - last_tick < 60000) return;
    LONG a0 = gp_ad_stats[0] - last_ad[0], a1 = gp_ad_stats[1] - last_ad[1];
    LONG q0 = gp_adq_stats[0] - last_adq[0], q1 = gp_adq_stats[1] - last_adq[1];
    if (dedup_on && a0)
        gp_log("animdedup: last %lu s: %ld renders with a running animation, %ld re-evaluations skipped (%.0f%%)",
               (t - last_tick) / 1000, a0, a1, 100.0 * a1 / a0);
    if (decode_on && q0)
        gp_log("animdecode: last %lu s: %ld from-frame-0 decodes, %ld continued from the cache (%.0f%%)",
               (t - last_tick) / 1000, q0, q1, 100.0 * q1 / q0);
    if (dedup_on) anim_detail((t - last_tick) / 1000);
    last_tick = t;
    memcpy((void *)last_ad, (const void *)gp_ad_stats, sizeof last_ad);
    memcpy((void *)last_adq, (const void *)gp_adq_stats, sizeof last_adq);
}

void gp_render_exit_log(void)
{
    if (dedup_on)
        gp_log("exit: animdedup %ld of %ld Render evaluations skipped (%ld snapshots, %ld frame changed)",
               gp_ad_stats[1], gp_ad_stats[0], gp_ad_stats[2], gp_ad_stats[3]);
    if (decode_on)
        gp_log("exit: animdecode %ld of %ld from-frame-0 decodes continued from the cache (%ld channels "
               "destroyed while cached)", gp_adq_stats[1], gp_adq_stats[0], gp_adq_stats[2]);
    if (gp_ptclvtx_fallbacks) gp_log("exit: particlevtx x87 fallbacks %ld", gp_ptclvtx_fallbacks);
}

/* ---- animdedup ---- */
typedef struct { uint32_t obj, sync, anim, frame, htree, ht[9], xf[12]; } snap_t;
#define NSNAP 4096
static snap_t snaps[NSNAP];
static inline snap_t *snap_of(const void *obj)
{
    return &snaps[((uint32_t)(uintptr_t)obj >> 3) * 2654435761u >> 20];
}

/* why a Render progress call was not skipped (the first failing test), for the 60 s detail line */
enum { W_CLASS, W_MASTER, W_INVALID, W_DIRTY, W_SYNC, W_NOSNAP, W_ANIM, W_POSE, W_MOVED, W_FORMAT, W_END, W_N };
static LONG why[W_N], last_why[W_N];

/* HLod pose evaluations seen at 0x59cd79 (main thread), by the object's motion mode: slave, base
 * pose, single animation manual (+0x110 == 0) or playing, blend, combo, other; and how many of them
 * had exactly the inputs of that object's previous single-animation evaluation (anim, frame,
 * transform, HTree header), whatever the sync time: the re-evaluations a dedup of manual-mode units
 * could save (measured only, nothing is skipped here) */
enum { E_SLAVE, E_BASE, E_MANUAL, E_PLAYING, E_BLEND, E_COMBO, E_OTHER, E_SAME, E_N };
static LONG evals[E_N], last_evals[E_N];

static void anim_detail(DWORD secs)
{
    LONG e[E_N], w[W_N], ne = 0;
    for (int i = 0; i < E_N; i++) { e[i] = evals[i] - last_evals[i]; last_evals[i] = evals[i]; if (i < E_SAME) ne += e[i]; }
    for (int i = 0; i < W_N; i++) { w[i] = why[i] - last_why[i]; last_why[i] = why[i]; }
    if (!ne) return;
    gp_log("animdedup detail: last %lu s: %ld HLod pose evaluations: single animation %ld manual + %ld playing, "
           "blend %ld, combo %ld, base pose %ld, slave %ld, other %ld; %ld had the same inputs as the object's "
           "previous evaluation", secs, ne, e[E_MANUAL], e[E_PLAYING], e[E_BLEND], e[E_COMBO], e[E_BASE],
           e[E_SLAVE], e[E_OTHER], e[E_SAME]);
    gp_log("animdedup detail: Render progress calls not skipped because: not an HLod %ld, slave %ld, pose not "
           "valid %ld, sub-objects dirty %ld, other sync time %ld, no snapshot at this sync time %ld, anim/frame "
           "changed %ld, transform/HTree changed %ld, frame moved %ld, not a compressed anim %ld, frame past a "
           "channel %ld", w[W_CLASS], w[W_MASTER], w[W_INVALID], w[W_DIRTY], w[W_SYNC], w[W_NOSNAP], w[W_ANIM],
           w[W_POSE], w[W_MOVED], w[W_FORMAT], w[W_END]);
}

__attribute__((force_align_arg_pointer))
void WINAPI gp_ad_forget(const void *obj)
{
    snap_t *s = snap_of(obj);
    if (GetCurrentThreadId() == gp_render_tid) {
        const uint8_t *o = obj;
        uint32_t mode = U32(o, 0x100);
        int e = U32(o, 0xfc) ? E_SLAVE : mode == 1 ? E_BASE : mode == 2 ? (U32(o, 0x110) ? E_PLAYING : E_MANUAL)
              : mode == 3 ? E_BLEND : mode == 4 ? E_COMBO : E_OTHER;
        evals[e]++;
        gp_ad_pass[AD_PASS][0]++;
        const uint8_t *h = (const uint8_t *)(uintptr_t)U32(o, 0xf8);
        if (s->obj == (uint32_t)(uintptr_t)obj && mode == 2 && h && s->htree == (uint32_t)(uintptr_t)h &&
            s->anim == U32(o, 0x104) && s->frame == U32(o, 0x108) && !memcmp(s->ht, h + 0x10, sizeof s->ht) &&
            !memcmp(s->xf, o + 0x18, sizeof s->xf))
            evals[E_SAME]++;
        if (!(++usot_count & 0xfff)) periodic();
    }
    if (s->obj == (uint32_t)(uintptr_t)obj) s->obj = 0;
}

__attribute__((force_align_arg_pointer))
void WINAPI gp_ad_single_c(uint8_t *obj, uint32_t xf, uint32_t anim, uint32_t frame)
{
    gp_call_this3(fn_single, obj, xf, anim, frame);
    if (GetCurrentThreadId() != gp_render_tid) return;
    uint8_t *h = (uint8_t *)(uintptr_t)U32(obj, 0xf8);
    snap_t *s = snap_of(obj);
    s->obj = 0;
    if (!h || xf != (uint32_t)(uintptr_t)obj + 0x18 || U32(h, 0x1c) != U32(h, 0x20)) return;
    s->sync = U32(gp_ad_synctime_va, 0); s->anim = anim; s->frame = frame;
    s->htree = (uint32_t)(uintptr_t)h;
    memcpy(s->ht, h + 0x10, sizeof s->ht);
    memcpy(s->xf, obj + 0x18, sizeof s->xf);
    s->obj = (uint32_t)(uintptr_t)obj;
    gp_ad_stats[2]++;
}

static int skippable(uint8_t *obj)
{
    uint32_t vt = U32(obj, 0);
    if (vt != gp_ad_vt_hlod || U32(vt, 0xa8) != fn_usot_hlod) return W_CLASS;
    if (U32(obj, 0xfc)) return W_MASTER;
    if (!U8(obj, 0xf4)) return W_INVALID;
    if (U32(obj, 0x10) & 0x200000) return W_DIRTY;
    uint32_t sync = U32(gp_ad_synctime_va, 0);
    if (U32(obj, 0x114) != sync) return W_SYNC;
    snap_t *s = snap_of(obj);
    uint8_t *h = (uint8_t *)(uintptr_t)U32(obj, 0xf8);
    if (s->obj != (uint32_t)(uintptr_t)obj || s->sync != sync) return W_NOSNAP;
    if (s->anim != U32(obj, 0x104) || s->frame != U32(obj, 0x108) || s->htree != (uint32_t)(uintptr_t)h) return W_ANIM;
    if (memcmp(s->ht, h + 0x10, sizeof s->ht) || memcmp(s->xf, obj + 0x18, sizeof s->xf)) return W_POSE;
    uint32_t dir = 0, f = gp_ad_call_ccf(fn_ccf, obj, &dir);
    if (f != U32(obj, 0x108) || dir != U32(obj, 0x118)) { gp_ad_stats[3]++; return W_MOVED; }
    /* the per-HTree decode stream repeats a frame bit for bit only below each channel's frame
     * count: from a cached frame at or past it the decoders return the cached value unchanged */
    uint32_t anim = U32(obj, 0x104);
    if (!anim) return -1;                                  /* 0x5a3f70 does nothing then */
    if (gp_call_this0(U32(U32(anim, 0), 0x54), (void *)(uintptr_t)anim) != 1) return W_FORMAT;
    uint32_t tab = U32(anim, 0x58), np = gp_call_this0(U32(U32(anim, 0), 0x34), (void *)(uintptr_t)anim);
    if (!tab) return W_FORMAT;
    uint32_t fi = (uint32_t)_mm_cvttss_si32(_mm_castsi128_ps(_mm_cvtsi32_si128((int)f)));
    for (uint32_t p = 1; p < np; p++)
        for (int c = 0; c < 5; c++) {
            uint32_t ch = U32(tab, p * 0x18 + 4 * c);
            if (ch && fi >= U32(ch, 0xc)) return W_END;
        }
    return -1;
}

__attribute__((force_align_arg_pointer))
void WINAPI gp_ad_progress_c(uint8_t *obj)
{
    if (GetCurrentThreadId() == gp_render_tid) {
        if (!(++gp_ad_stats[0] & 0xfff)) periodic();
        int w = skippable(obj);
        if (w >= 0) why[w]++;
        else {
            U8(obj, 0xf4) = 0;                      /* as progress leaves it */
            gp_ad_skip = (uint32_t)(uintptr_t)obj;
            gp_ad_stats[1]++;
            gp_ad_pass[AD_PASS][1]++;
            return;
        }
    }
    gp_call_this0(fn_progress, obj);
}

int gp_patch_animdedup(void)
{
    static const uint8_t vtslot[] = {0x70,0xcd,0x59,0x00};          /* HLod vt+0xa8 = 0x59cd70 */
    static const uint8_t c1[] = {0xe8,0x6f,0xfc,0xff,0xff};          /* 0x5a4dfc call 0x5a4a70 */
    static const uint8_t c2[] = {0xe8,0xd2,0x82,0x00,0x00};          /* 0x59cd79 call 0x5a5050 */
    static const uint8_t c3[] = {0xe8,0x3f,0xee,0xff,0xff};          /* 0x5a512c call 0x5a3f70 */
    gp_site s[10];
    gp_site_hash(&s[0], 0x5a4dd0, 0x53, GP_FNV_5A4DD0);
    gp_site_hash(&s[1], 0x5a4a70, 0x33, GP_FNV_5A4A70);
    gp_site_hash(&s[2], 0x5a4770, 0x2e2, GP_FNV_5A4770);
    gp_site_hash(&s[3], 0x5a5050, 0x145, GP_FNV_5A5050);
    gp_site_hash(&s[4], 0x59cd70, 0x10, GP_FNV_59CD70);
    gp_site_hash(&s[5], 0x5a3f70, 0x6e, GP_FNV_5A3F70);
    gp_site_init(&s[6], 0xbec898, vtslot, 4); s[6].wlen = 0;
    gp_site_init(&s[7], 0x5a4dfc, c1, 5); gp_rel32(&s[7], 0, 0xe8, (void *)gp_ad_progress);
    gp_site_init(&s[8], 0x59cd79, c2, 5); gp_rel32(&s[8], 0, 0xe8, (void *)gp_ad_usot_base);
    gp_site_init(&s[9], 0x5a512c, c3, 5); gp_rel32(&s[9], 0, 0xe8, (void *)gp_ad_single);
    fn_progress = 0x5a4a70 + gp_va_offset; fn_ccf = 0x5a4770 + gp_va_offset;
    fn_single = 0x5a3f70 + gp_va_offset; fn_usot_hlod = 0x59cd70 + gp_va_offset;
    gp_ad_usot_orig = 0x5a5050 + gp_va_offset;
    gp_ad_skip = 0;
    memset(snaps, 0, sizeof snaps);
    gp_render_tid = GetCurrentThreadId();
    if (!gp_apply("animdedup", s, 10)) return 0;
    dedup_on = 1;
    return 1;
}

/* ---- animdecode ---- */
#define GP_FNV_5B19C0 0x4806393971f5b37eull   /* the six decoders and the Get_* functions, 0xbb4 bytes */
static const uint32_t adq_va[6] = {0x5b19c0, 0x5b1aba, 0x5b1c00, 0x5b1d49, 0x5b1e2b, 0x5b1f5b};
static const uint32_t adq_site[6] = {0x5b2131, 0x5b2218, 0x5b22eb, 0x5b2396, 0x5b247d, 0x5b2550};
static const uint8_t adq_n[6] = {1, 3, 4, 1, 3, 4};
static uint32_t adq_fn[6];
typedef struct { uint32_t chan, frame, k, data, cnt, vt; float a[4]; } adq_t;
#define NSET 4096
static adq_t adq[NSET][2];
static uint8_t adq_rr[NSET];
static inline uint32_t set_index(const void *chan)
{
    return ((uint32_t)(uintptr_t)chan >> 3) * 2654435761u >> 20;
}

__attribute__((force_align_arg_pointer))
void WINAPI gp_adq_c(uint32_t k, uint8_t *chan, uint32_t *a)   /* a: src, srcFrame, dst, outA, outB */
{
    uint32_t dst = a[2];
    void *outA = (void *)(uintptr_t)a[3], *outB = (void *)(uintptr_t)a[4];
    if (GetCurrentThreadId() != gp_render_tid) {
        gp_call_dec(adq_fn[k], chan, (void *)(uintptr_t)a[0], a[1], dst, outA, outB);
        return;
    }
    if (!(++gp_adq_stats[0] & 0xfff)) periodic();
    uint32_t si = set_index(chan);
    adq_t *w = adq[si], *e = NULL;
    uint32_t c = (uint32_t)(uintptr_t)chan, data = U32(chan, 0x28), cnt = U32(chan, 0xc), vt = U32(chan, 0);
    for (int i = 0; i < 2; i++) {
        if (w[i].chan != c || w[i].k != k || w[i].data != data || w[i].cnt != cnt || w[i].vt != vt) continue;
        if (!e || (w[i].frame <= dst && w[i].frame < cnt && (e->frame > dst || e->frame >= cnt || w[i].frame > e->frame)))
            e = &w[i];
    }
    /* dst = 0xffffffff (a frame in [-2,-1)): the decoder never stores A then (dst + 1 wraps), and
     * from a cached frame it would store nothing at all; always from frame 0, never cached */
    if (e && e->frame <= dst && e->frame < cnt && dst != 0xffffffffu) {
        gp_adq_stats[1]++;                          /* continue from the cached frame */
        e->chan = 0;
        gp_call_dec(adq_fn[k], chan, e->a, e->frame, dst, outA, outB);
    } else {                                        /* from frame 0, exactly as the original */
        if (!e) e = &w[adq_rr[si]++ & 1];
        e->chan = 0;
        gp_call_dec(adq_fn[k], chan, (void *)(uintptr_t)a[0], a[1], dst, outA, outB);
        if (dst == 0xffffffffu) return;
    }
    memcpy(e->a, outA, adq_n[k] * 4);               /* the decoder's A: the value at dst */
    e->frame = dst; e->k = k; e->data = data; e->cnt = cnt; e->vt = vt;
    e->chan = c;
}

void WINAPI gp_adq_evict(const void *chan)
{
    adq_t *w = adq[set_index(chan)];
    for (int i = 0; i < 2; i++)
        if (w[i].chan == (uint32_t)(uintptr_t)chan) { w[i].chan = 0; InterlockedIncrement(&gp_adq_stats[2]); }
}

int gp_patch_animdecode(void)
{
    static void (*const entry[6])(void) = {gp_adq_site0, gp_adq_site1, gp_adq_site2, gp_adq_site3,
                                           gp_adq_site4, gp_adq_site5};
    static const uint8_t dtor[] = {0x56, 0x8b,0xf1, 0xff,0x76,0x28};  /* push esi; mov esi,ecx; push [esi+0x28] */
    uint8_t call[6][5];
    gp_site s[9];
    gp_site_hash(&s[0], 0x5b19c0, 0xbb4, GP_FNV_5B19C0);
    gp_site_hash(&s[1], 0x5b18fe, 0x1a, GP_FNV_5B18FE);
    for (int k = 0; k < 6; k++) {
        int32_t rel = (int32_t)(adq_va[k] - (adq_site[k] + 5));
        call[k][0] = 0xe8; memcpy(&call[k][1], &rel, 4);
        gp_site_init(&s[2 + k], adq_site[k], call[k], 5);
        gp_rel32(&s[2 + k], 0, 0xe8, (void *)entry[k]);
        adq_fn[k] = adq_va[k] + gp_va_offset;
    }
    gp_site_init(&s[8], 0x5b18fe, dtor, sizeof dtor);
    gp_rel32(&s[8], 0, 0xe9, (void *)gp_adq_dtor);
    s[8].repl[5] = 0x90;
    gp_adq_dtor_cont = 0x5b1904 + gp_va_offset;
    memset(adq, 0, sizeof adq);
    gp_render_tid = GetCurrentThreadId();
    if (!gp_apply("animdecode", s, 9)) return 0;
    decode_on = 1;
    return 1;
}
