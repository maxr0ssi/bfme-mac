/* shadowpar: stencil shadow volumes built on several cores (switch "shadowpar", off by default).
 *
 * A2, per caster: the caster loop of renderShadows (0x4f4fa5) is replaced by gp_sp_casters. It
 * calls Update for every caster in the original order, but inside updateMeshVolume the heavy block
 * (0x4f3301..0x4f33fe: normals, silhouette, volume) is captured as a job instead of run
 * (gp_sp_block; the serial parts - skinning, scratch resize, volume allocation - still happen
 * there, in order). After the last Update the jobs run on the worker pool (parallel/pool), the
 * shared state is brought to what the serial game leaves (par_shjob.c), and then the casters'
 * volumes are rendered in the original order (RenderVolume per new dynamic task). The only
 * reordering: caster N's volumes are drawn after caster N+1's Update rather than before it;
 * Update does no drawing and reads nothing a draw writes.
 * A1, per mesh: the triangle-normal loop of buildPolygonNormals (0x4f2221) on the pool when a mesh
 * has at least shadowpar_a1_min triangles and the call comes from the main thread (on a worker, or
 * inside a parallel region, it runs serially).
 * Anything unusual in a block (see gp_sp_eligible, static VB volumes) first runs the pending jobs,
 * then the block inline as in the original. Verify mode (shadowpar_verify=N): for the first N
 * caster loops with jobs, every block runs the original way first; the job then recomputes it on
 * the pool and every output is compared byte for byte (mismatch: reference restored, shadowpar
 * off for the session; a fault on a worker also turns it off). Logs to gamepatch.log. */
#include "par_shadow.h"
#include "parallel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

gp_sp_fns gp_sp;
gp_sp_config gp_spc = {300, 0, 1024, 900, 0};
int gp_sp_collecting, gp_sp_verifying, gp_sp_pool_up;

static int64_t qpc(void) { LARGE_INTEGER t; QueryPerformanceCounter(&t); return t.QuadPart; }
static double us_per_tick;

void gp_sp_bind(void)
{
    uint32_t o = gp_va_offset;
    gp_sp.poly_normal = (gpf_poly_normal)(uintptr_t)(0x4f1613 + o);
    gp_sp.normals = (gpf_normals)(uintptr_t)(0x4f21b2 + o);
    gp_sp.silhouette = (gpf_silhouette)(uintptr_t)(0x4f2614 + o);
    gp_sp.construct = (gpf_construct)(uintptr_t)(0x4ef790 + o);
    gp_sp.alloc = (gpf_alloc)(uintptr_t)(0x4f114e + o);
    gp_sp.reset = (gpf_reset)(uintptr_t)(0x4f00e8 + o);
    gp_sp.resize = (gpf_resize)(uintptr_t)(0x4f0619 + o);
    gp_sp.update = (gpf_update)(uintptr_t)(0x4f3906 + o);
    gp_sp.render = (gpf_render)(uintptr_t)(0x4f42bf + o);
    gp_sp.construct_vb = (gpf_construct)(uintptr_t)(0x4efbeb + o);
}

/* ---- the heavy block of updateMeshVolume ----------------------------------------------------
 * frame = updateMeshVolume's ebp: [+0x6c] mesh, [+0x70] light, [+0x78] extrusion (float),
 * [-8] volume index, [-0x60] allocation flags, [+0x63] mesh rotated, [+0x62] light moved,
 * [-0x1c] light position in object space. */
#define F_MESH(f)   AT(f, 0x6c, int)
#define F_LIGHT(f)  AT(f, 0x70, int)
#define F_EXT(f)    AT(f, 0x78, float)
#define F_VOL(f)    AT(f, -8, int)
#define F_AFLAG(f)  AT(f, -0x60, int)
#define F_ROT(f)    AT(f, 0x63, uint8_t)
#define F_LMOVE(f)  AT(f, 0x62, uint8_t)
#define F_LPOS(f)   ((float *)((f) - 0x1c))

/* allocateShadowVolume and, for a volume with a static VB, the switch to a CPU volume
 * (0x4f3332..0x4f33d2) */
static void alloc_part(uint8_t *sh, uint8_t *f)
{
    int li = F_LIGHT(f), mesh = F_MESH(f), v = F_VOL(f);
    if (!AT(sh, SH_VOL + v * 4, void *)) gp_sp.alloc(sh, li, mesh, F_AFLAG(f));
    if (!AT(sh, SH_VB + v * 4, void *)) return;
    if (F_ROT(f)) AT(AT(sh, SH_VOL + v * 4, uint8_t *), V_FLAGS, uint32_t) |= 1;
    else if (!F_LMOVE(f)) return;
    gp_sp.reset(sh, li, mesh);
    gp_sp.alloc(sh, li, mesh, 0);
}

/* the original block 0x4f3301..0x4f33fe, in C (verify reference) */
static void block_serial(uint8_t *sh, uint8_t *f)
{
    int mesh = F_MESH(f), li = F_LIGHT(f);
    uint8_t *m = AT(sh, SH_GEOM, uint8_t *) + GEO_MESH + mesh * MESH_SIZE;
    if (AT(sh, SH_SILN + mesh * 2, short)) gp_sp.normals(m);
    AT(sh, SH_SILN + mesh * 2, short) = 0;
    gp_sp.silhouette(sh, mesh, F_LPOS(f));
    alloc_part(sh, f);
    uint8_t *vol = AT(sh, SH_VOL + F_VOL(f) * 4, uint8_t *);
    if (vol[V_FLAGS] & 1) gp_sp.construct(sh, F_LPOS(f), F_EXT(f), li, mesh);
    else gp_sp.construct_vb(sh, F_LPOS(f), F_EXT(f), li, mesh);
}

/* 0 = done (continue at 0x4f33fe), 1 = run the original block, 2 = continue at the construct
 * call 0x4f33d7 (silhouette built here) */
__attribute__((force_align_arg_pointer))
int gp_sp_block(uint8_t *sh, uint8_t *f)
{
    if (!gp_sp_collecting || gp_sp_disabled) return 1;
    int mesh = F_MESH(f), li = F_LIGHT(f);
    if (!gp_sp_eligible(sh, mesh, li)) {
        gp_sp_stats.inline_blocks++;
        if (gp_sp_pending() && gp_sp_flush(gp_sp_verifying)) gp_sp_disabled = 1;
        return 1;
    }
    gp_sp_capture(sh, mesh, li, F_LPOS(f), F_EXT(f));
    if (gp_sp_verifying) {
        int64_t t0 = qpc();
        block_serial(sh, f);
        gp_sp_stats.ref_us += (qpc() - t0) * us_per_tick;
        uint8_t *vol = AT(sh, SH_VOL + F_VOL(f) * 4, uint8_t *);
        if (vol[V_FLAGS] & 1) { gp_sp_snapshot_ref(); return 0; }
        /* a static volume: its silhouette has just overwritten the shared neighbor flags (and a
         * skinned one the normal scratch) after the pending jobs' references; compare their
         * outputs now, but not that shared state */
        gp_sp_drop_last();
        if (gp_sp_pending() && gp_sp_flush(2)) gp_sp_disabled = 1;
        return 0;
    }
    uint8_t *m = AT(sh, SH_GEOM, uint8_t *) + GEO_MESH + mesh * MESH_SIZE;
    int np = AT(m, M_NPOLYS, int);
    if (m[M_SKINNED]) {             /* buildPolygonNormals' effects, in order: resize, pointer */
        if (*(int *)G_NORM_CAP < np) gp_sp.resize((void *)G_NORM_VEC, np, 0);
        AT(m, M_NORMALS, void *) = *(void **)G_NORM_PTR;
    }
    AT(sh, SH_SILN + mesh * 2, short) = 0;
    alloc_part(sh, f);
    uint8_t *vol = AT(sh, SH_VOL + F_VOL(f) * 4, uint8_t *);
    if (vol && (vol[V_FLAGS] & 1)) return 0;
    /* a static-VB volume (or none): constructVolumeVB needs the silhouette now */
    gp_sp_drop_last();
    gp_sp_stats.inline_blocks++;
    if (gp_sp_pending() && gp_sp_flush(0)) gp_sp_disabled = 1;
    if (m[M_SKINNED]) { AT(m, M_NORMALS, void *) = NULL; gp_sp.normals(m); }
    gp_sp.silhouette(sh, mesh, F_LPOS(f));
    return 2;
}

/* ---- A1: buildPolygonNormals' loop ---------------------------------------------------------- */
typedef struct { uint8_t *mesh; float *out; } a1_ctx;
static void a1_chunk(int b, int e, void *c, int slot)
{
    a1_ctx *x = c;
    (void)slot;
    for (int i = b; i < e; i++) gp_sp.poly_normal(x->mesh, i, x->out + 3 * i);
}

__attribute__((force_align_arg_pointer))
void gp_sp_normals(uint8_t *mesh, float *out)
{
    int n = AT(mesh, M_NPOLYS, int);
    if (n >= gp_spc.a1_min && gp_sp_pool_up && !gp_sp_disabled) {
        a1_ctx c = {mesh, out};
        par_for(n, 256, a1_chunk, &c);         /* serial when nested or on another thread */
        return;
    }
    for (int i = 0; i < n; i++) gp_sp.poly_normal(mesh, i, out + 3 * i);
}

/* ---- the caster loop ------------------------------------------------------------------------ */
typedef struct { uint8_t *sh; void *head, *old; } rec_t;
static rec_t *recs; static int caprec;
long long gp_sp_loops;
int gp_sp_on;
static long long par_loops, ser_loops, job_loops;
static double par_loop_us, ser_loop_us;
static long long last_jobs, last_inline;

static void start_pool(void)
{
    int n = par_init(gp_spc.workers);
    gp_sp_nslots = n + 1;
    gp_sp_pool_up = 1;
    gp_log("shadowpar: pool of %d workers + the main thread (spin %u us, then park); verifying the "
           "first %d frames with shadow volumes", n, par_cfg.idle_park_us, gp_spc.verify);
}

static void summary(void)
{
    const par_stats *ps = par_get_stats();
    long long nj = gp_sp_stats.jobs - last_jobs, ni = gp_sp_stats.inline_blocks - last_inline;
    gp_log("shadowpar: last %d frames: %.0f volumes/frame on the pool, %.1f inline; shadow caster loop "
           "%.0f us/frame parallel (%lld frames) vs %.0f us serial (%lld sampled); verified so far %lld "
           "volumes, serial %.0f us vs parallel %.0f us; wakes %llu, faults %lld, mismatches %lld%s",
           gp_spc.log_every, par_loops ? (double)nj / par_loops : 0.0, par_loops ? (double)ni / par_loops : 0.0,
           par_loops ? par_loop_us / par_loops : 0.0, par_loops, ser_loops ? ser_loop_us / ser_loops : 0.0,
           ser_loops, gp_sp_stats.verified_jobs, gp_sp_stats.ref_us, gp_sp_stats.par_us,
           (unsigned long long)ps->wakes, gp_sp_stats.faults, gp_sp_stats.mismatches,
           gp_sp_disabled ? "; OFF (serial) for this session" : "");
    last_jobs = gp_sp_stats.jobs; last_inline = gp_sp_stats.inline_blocks;
    par_loops = ser_loops = 0; par_loop_us = ser_loop_us = 0;
}

__attribute__((force_align_arg_pointer))
void gp_sp_casters(uint8_t *s, uint8_t *list)
{
    int64_t t0 = qpc();
    gp_sp_loops++;
    int par = !gp_sp_disabled && !(gp_spc.sample > 0 && gp_sp_loops % gp_spc.sample == 0);
    if (par && !gp_sp_pool_up) start_pool();
    if (!par) {                                            /* the original loop */
        for (; s; s = AT(s, SH_NEXT, uint8_t *)) {
            if (!s[4] || s[5]) continue;
            void *old = AT(list, 4, void *);
            gp_sp.update(s, 0);
            for (uint8_t *t = AT(list, 4, uint8_t *); t != old; t = *(uint8_t **)t) gp_sp.render(s, t[8], t[9]);
        }
        ser_loops++; ser_loop_us += (qpc() - t0) * us_per_tick;
    } else {
        int nrec = 0;
        gp_sp_verifying = job_loops < gp_spc.verify;
        double ref0 = gp_sp_stats.ref_us, par0 = gp_sp_stats.par_us;
        long long j0 = gp_sp_stats.jobs;
        gp_sp_collecting = 1;
        for (; s; s = AT(s, SH_NEXT, uint8_t *)) {
            if (!s[4] || s[5]) continue;
            void *old = AT(list, 4, void *);
            gp_sp.update(s, 0);
            if (nrec >= caprec) {
                caprec = caprec ? caprec * 2 : 256;
                if (!(recs = realloc(recs, caprec * sizeof *recs))) abort();
            }
            recs[nrec++] = (rec_t){s, AT(list, 4, void *), old};
        }
        if (gp_sp_flush(gp_sp_verifying)) gp_sp_disabled = 1;
        gp_sp_collecting = 0;
        par_park_now();
        for (int i = 0; i < nrec; i++)
            for (uint8_t *t = recs[i].head; t != recs[i].old; t = *(uint8_t **)t)
                gp_sp.render(recs[i].sh, t[8], t[9]);
        par_loops++; par_loop_us += (qpc() - t0) * us_per_tick;
        if (gp_sp_stats.jobs > j0 && gp_sp_verifying) {
            job_loops++;
            if (job_loops % 30 == 1 || job_loops == gp_spc.verify || gp_sp_disabled)
                gp_log("shadowpar verify frame %lld: %d casters, %lld volumes; serial %.0f us, parallel "
                       "%.0f us; %s", job_loops, nrec, gp_sp_stats.jobs - j0, gp_sp_stats.ref_us - ref0,
                       gp_sp_stats.par_us - par0, gp_sp_disabled ? "MISMATCH - shadowpar off" : "identical");
        }
        if (gp_sp_disabled) gp_log("shadowpar: switched off for this session (see above); shadows are "
                                   "built serially as without the patch");
    }
    if (gp_spc.log_every > 0 && gp_sp_loops % gp_spc.log_every == 0) summary();
}

/* ---- install -------------------------------------------------------------------------------- */
static int cfg(const char *key, int def)
{
    char var[64], val[32], ini[MAX_PATH + 32], k[64];
    snprintf(var, sizeof var, "GAMEPATCH_SHADOWPAR_%s", key);
    for (char *p = var; *p; p++) if (*p >= 'a' && *p <= 'z') *p -= 32;
    if (GetEnvironmentVariableA(var, val, sizeof val)) return atoi(val);
    HMODULE self = NULL;
    GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                       (LPCSTR)(uintptr_t)cfg, &self);
    DWORD n = GetModuleFileNameA(self, ini, MAX_PATH);
    while (n && ini[n - 1] != '\\') n--;
    strcpy(ini + n, "gamepatch.ini");
    snprintf(k, sizeof k, "shadowpar_%s", key);
    return GetPrivateProfileIntA("patches", k, def, ini);
}

int gp_patch_shadowpar(void)
{
    static const uint8_t loop[] = {0x3b,0xc3, 0x89,0x45,0x08, 0x75,0xb6};    /* cmp eax,ebx; mov [ebp+8],eax; jne */
    static const uint8_t blk[] = {0x8b,0x45,0x6c, 0x8d,0xb4,0x43,0x00,0x44,0x00,0x00};
    static const uint8_t a1[] = {0x33,0xff, 0x39,0x7e,0x1c, 0x7e,0x15};
    static const struct { uint32_t va, len; uint64_t fnv; } ctx[] = {
        {0x4f4fa5, 0x4a, 0x38f2d6615a1e68a2ull},    /* the caster loop */
        {0x4f3301, 0x10f, 0x0cbdd580abbb12cfull},   /* the heavy block of updateMeshVolume */
        {0x4f36e5, 0x91, 0x70314d3aeeaacc8eull},    /* updateVolumes: skinning into the scratch */
        {0x4f21b2, 0xa0, 0xccb91ccd0b8c9b33ull},    /* buildPolygonNormals */
        {0x4f2614, 0x1a6, 0x22b7133be1e8ff57ull},   /* buildSilhouette */
        {0x4f114e, 0x9e, 0xd8b9e4c8a8d95787ull},    /* allocateShadowVolume */
        {0x4f00e8, 0x75, 0x5ea7469b69d23fd7ull},    /* resetShadowVolume */
    };
    gp_site s[10];
    for (int i = 0; i < 7; i++) gp_site_hash(&s[i], ctx[i].va, ctx[i].len, ctx[i].fnv);
    gp_site_init(&s[7], 0x4f4fe8, loop, sizeof loop);
    gp_rel32(&s[7], 0, 0xe9, (void *)gp_sp_loop_stub);
    s[7].repl[5] = s[7].repl[6] = 0x90;
    gp_site_init(&s[8], 0x4f3301, blk, sizeof blk);
    gp_rel32(&s[8], 0, 0xe9, (void *)gp_sp_block_stub);
    memset(s[8].repl + 5, 0x90, 5);
    gp_site_init(&s[9], 0x4f2221, a1, sizeof a1);
    gp_rel32(&s[9], 0, 0xe9, (void *)gp_sp_a1_stub);
    s[9].repl[5] = s[9].repl[6] = 0x90;
    uint32_t o = gp_va_offset;
    gp_sp_loop_cont = 0x4f4fef + o; gp_sp_block_orig = 0x4f330b + o; gp_sp_block_tail = 0x4f33d7 + o;
    gp_sp_block_done = 0x4f33fe + o; gp_sp_a1_cont = 0x4f223d + o;
    gp_sp_bind();
    LARGE_INTEGER f; QueryPerformanceFrequency(&f);
    us_per_tick = 1e6 / f.QuadPart;
    gp_spc.verify = cfg("verify", gp_spc.verify);
    gp_spc.workers = cfg("workers", gp_spc.workers);
    gp_spc.a1_min = cfg("a1_min", gp_spc.a1_min);
    gp_spc.log_every = cfg("log_every", gp_spc.log_every);
    gp_spc.sample = cfg("sample", gp_spc.sample);
    if (!gp_apply("shadowpar", s, 10)) return 0;
    gp_sp_on = 1;
    gp_log("shadowpar: verify %d frames, workers %d (0 = auto), parallel triangle normals from %d "
           "triangles, serial sample every %d frames, summary every %d", gp_spc.verify, gp_spc.workers,
           gp_spc.a1_min, gp_spc.sample, gp_spc.log_every);
    return 1;
}
