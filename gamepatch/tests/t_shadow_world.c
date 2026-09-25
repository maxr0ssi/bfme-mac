/* t_shadow worlds: shadow casters over shared shadow geometries, driven frame by frame through the
 * game's own updateMeshVolume (and everything it calls) at its address in the code copy. Only the
 * parts around it are stand-ins: fake_update does what updateVolumes does around the call
 * (skinning into the scratch vector 0xdd184c with a deterministic pose, the task-list push),
 * fake_render and fake_construct_vb record what RenderVolume / constructVolumeVB would get.
 * Meshes: the skinned meshes of a few unit models from the game's own W3D.big (when found next to
 * the exe) plus synthetic closed, open and multi-part meshes; every model also has a rigid copy. */
#include "t_shadow.h"
#include "orig.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

tmodel models[32];
int nmodels;
static uint32_t rs = 12345;
uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }
float frnd(float lo, float hi) { return lo + (hi - lo) * (float)(rnd() & 0xffffff) / 16777216.0f; }
uint64_t fnv(uint64_t h, const void *p, size_t n)
{
    for (size_t i = 0; i < n; i++) { h ^= ((const uint8_t *)p)[i]; h *= 0x100000001b3ull; }
    return h;
}

/* ---- meshes ---------------------------------------------------------------------------------- */
static tmesh *mesh_from(const char *name, const float *rv, int nr, const uint32_t *tri, int nt, int skinned)
{
    tmesh *m = calloc(1, sizeof *m);
    snprintf(m->name, sizeof m->name, "%s", name);
    m->verts = malloc(nr * 12); m->remap = malloc(nr * 2); m->tris = malloc(nt * 6);
    for (int i = 0; i < nr; i++) {                 /* weld identical positions, like initFromMesh */
        int k = 0;
        while (k < m->nverts && memcmp(m->verts + 3 * k, rv + 3 * i, 12)) k++;
        if (k == m->nverts) memcpy(m->verts + 3 * m->nverts++, rv + 3 * i, 12);
        m->remap[i] = (uint16_t)k;
    }
    for (int i = 0; i < nt * 3; i++) m->tris[i] = (uint16_t)tri[i];
    m->ntris = nt; m->nrender = nr; m->skinned = skinned;
    return m;
}

static uint32_t be32(const uint8_t *p) { return (uint32_t)p[0] << 24 | p[1] << 16 | p[2] << 8 | p[3]; }
static uint8_t *big_member(FILE *f, const char *member, uint32_t *len)
{
    uint8_t h[16];
    fseek(f, 0, SEEK_SET);
    if (fread(h, 1, 16, f) != 16 || (memcmp(h, "BIGF", 4) && memcmp(h, "BIG4", 4))) return NULL;
    uint32_t n = be32(h + 8), first = be32(h + 12);
    uint8_t *idx = malloc(first), *res = NULL;
    fseek(f, 0, SEEK_SET);
    if (fread(idx, 1, first, f) != first) { free(idx); return NULL; }
    const uint8_t *p = idx + 16;
    for (uint32_t i = 0; i < n && p + 8 < idx + first; i++) {
        const char *nm = (const char *)p + 8;
        if (!_stricmp(nm, member)) {
            *len = be32(p + 4); res = malloc(*len);
            fseek(f, be32(p), SEEK_SET);
            if (fread(res, 1, *len, f) != *len) { free(res); res = NULL; }
            break;
        }
        p += 8 + strlen(nm) + 1;
    }
    free(idx);
    return res;
}

static void w3d_model(const uint8_t *d, uint32_t len, const char *name)
{
    tmodel *md = &models[nmodels];
    snprintf(md->name, sizeof md->name, "%s", name);
    md->nmesh = 0;
    for (uint32_t o = 0; o + 8 <= len && md->nmesh < 4;) {
        uint32_t t, s; memcpy(&t, d + o, 4); memcpy(&s, d + o + 4, 4); s &= 0x7fffffff;
        if (t == 0) {                                   /* MESH */
            const float *v = NULL; const uint8_t *tr = NULL; int nv = 0, nt = 0, skin = 0; char mn[17] = "";
            for (uint32_t q = o + 8; q + 8 <= o + 8 + s;) {
                uint32_t t2, s2; memcpy(&t2, d + q, 4); memcpy(&s2, d + q + 4, 4); s2 &= 0x7fffffff;
                if (t2 == 0x1f) memcpy(mn, d + q + 16, 16);
                else if (t2 == 0x02) { v = (const float *)(d + q + 8); nv = s2 / 12; }
                else if (t2 == 0x20) { tr = d + q + 8; nt = s2 / 32; }
                else if (t2 == 0x0e) skin = 1;
                q += 8 + s2;
            }
            if (skin && v && tr && nt >= 60 && nt <= 5400 && nv < 65000) {
                uint32_t *ti = malloc(nt * 12);
                for (int i = 0; i < nt; i++) memcpy(ti + 3 * i, tr + 32 * i, 12);
                md->mesh[md->nmesh++] = mesh_from(mn, v, nv, ti, nt, 1);
                free(ti);
            }
        }
        o += 8 + s;
    }
    if (md->nmesh) nmodels++;
}

int load_w3d_models(const char *exe)
{
    static const char *want[] = {"art\\w3d\\ku\\kuorcwar_skn.w3d", "art\\w3d\\ku\\kudirewolf_skn.w3d",
        "art\\w3d\\eu\\eurivenarch_skn.w3d", "art\\w3d\\ch\\chss_or_c_skn.w3d", "art\\w3d\\ch\\char_fe_u_skn.w3d",
        "art\\w3d\\ch\\chcm_cm_u_skn.w3d", "art\\w3d\\ch\\chtl_ht_c_skn.w3d"};
    char path[MAX_PATH];
    snprintf(path, sizeof path, "%s", exe);
    char *sl = strrchr(path, '\\');
    if (!sl) return 0;
    strcpy(sl + 1, "W3D.big");
    FILE *f = fopen(path, "rb");
    if (!f) { printf("  (no %s: synthetic meshes only)\n", path); return 0; }
    int n0 = nmodels;
    for (unsigned i = 0; i < sizeof want / sizeof want[0]; i++) {
        uint32_t len; uint8_t *d = big_member(f, want[i], &len);
        if (d) { w3d_model(d, len, strrchr(want[i], '\\') + 1); free(d); }
    }
    fclose(f);
    return nmodels - n0;
}

static void grid_mesh(tmodel *md, const char *nm, int nu, int nv, int closed_u, int torus, int skinned)
{
    int nr = (nu + 1) * (nv + 1), nt = 2 * nu * nv;
    float *rv = malloc(nr * 12); uint32_t *tri = malloc(nt * 12);
    for (int i = 0; i <= nu; i++)
        for (int j = 0; j <= nv; j++) {
            float u = 6.2831853f * i / nu, w = (torus ? 6.2831853f : 3.1415927f) * j / nv, *p = rv + 3 * (i * (nv + 1) + j);
            if (torus) { p[0] = (8 + 3 * cosf(w)) * cosf(u); p[1] = (8 + 3 * cosf(w)) * sinf(u); p[2] = 3 * sinf(w) + 12; }
            else if (closed_u) { p[0] = 6 * sinf(w) * cosf(u); p[1] = 6 * sinf(w) * sinf(u); p[2] = 6 * cosf(w) + 8; }
            else { p[0] = i - nu / 2.0f; p[1] = j - nv / 2.0f; p[2] = 4 + sinf(i * 0.7f) * cosf(j * 0.4f); }
        }
    if (closed_u && !torus)                            /* collapse the poles exactly */
        for (int i = 0; i <= nu; i++) {
            memcpy(rv + 3 * (i * (nv + 1)), rv, 12);
            memcpy(rv + 3 * (i * (nv + 1) + nv), rv + 3 * nv, 12);
        }
    for (int i = 0, k = 0; i < nu; i++)
        for (int j = 0; j < nv; j++) {
            uint32_t a = i * (nv + 1) + j, b = a + nv + 1;
            tri[k++] = a; tri[k++] = b; tri[k++] = a + 1;
            tri[k++] = b; tri[k++] = b + 1; tri[k++] = a + 1;
        }
    md->mesh[md->nmesh++] = mesh_from(nm, rv, nr, tri, nt, skinned);
    free(rv); free(tri);
}

void add_synthetic_models(void)
{
    tmodel *md = &models[nmodels++];
    strcpy(md->name, "synthetic sphere+grid");
    grid_mesh(md, "SPHERE", 24, 16, 1, 0, 1);
    grid_mesh(md, "GRID", 12, 9, 0, 0, 1);
    md = &models[nmodels++];
    strcpy(md->name, "synthetic torus+strip");
    grid_mesh(md, "TORUS", 30, 12, 1, 1, 1);
    grid_mesh(md, "STRIP", 40, 1, 0, 0, 1);
    md = &models[nmodels++];
    strcpy(md->name, "synthetic big sphere");
    grid_mesh(md, "BIGSPHERE", 64, 40, 1, 0, 1);
}

/* ---- world ----------------------------------------------------------------------------------- */
typedef struct { uint8_t *geom; tmodel *md; int rigid; } tgeom;
typedef struct { uint8_t *sh; tgeom *g; float rot0, rotv, tx, ty, tz, phase; } tcaster;
static tgeom G[64]; static int ng;
static tcaster *C; static int nc;
static uint8_t tasklist[16];
static float lightmgr[8];
static int frame;
static uint64_t TR, TV; static long long ncalls;
static const float ident[12] = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
#define CASTER_ID 0x49f0                      /* test bookkeeping past the game's shadow fields */
typedef void (__attribute__((thiscall)) *umv_t)(void *sh, int mesh, int li, const float *xf, const float *box, float floorz);
typedef char (__attribute__((thiscall)) *alloc_t)(void *sh, int li, int mesh, int flags);
typedef char (__attribute__((thiscall)) *resize_t)(void *vec, int n, int keep);

static uint8_t *geometry(tmodel *md, int rigid)
{
    for (int i = 0; i < ng; i++) if (G[i].md == md && G[i].rigid == rigid) return G[i].geom;
    uint8_t *g = calloc(1, GEO_SIZE);
    AT(g, GEO_NMESH, int) = md->nmesh;
    for (int j = 0; j < md->nmesh; j++) {
        tmesh *tm = md->mesh[j];
        uint8_t *m = g + GEO_MESH + j * MESH_SIZE, *obj = calloc(1, 16);
        AT(obj, 0xc, void *) = tm->tris;
        AT(m, 0, void *) = obj;
        AT(m, 0xc, int) = j;
        AT(m, 0x14, int) = AT(m, M_NVERTS, int) = tm->nverts;
        AT(m, M_NPOLYS, int) = tm->ntris;
        AT(m, 0x20, void *) = tm->remap;
        m[M_SKINNED] = !rigid;
        if (rigid) { float *v = malloc(tm->nverts * 12); memcpy(v, tm->verts, tm->nverts * 12); AT(m, M_VERTS, float *) = v; }
    }
    G[ng++] = (tgeom){g, md, rigid};
    return g;
}

void world_build(const world_cfg *c)
{
    rs = c->seed; ng = 0; nc = c->ncasters;
    C = calloc(nc, sizeof *C);
    memset((void *)0xdd184c, 0, 0x14); memset((void *)0xdd1864, 0, 0x14);   /* scratch vectors: empty */
    *(void **)0xdcb83c = lightmgr;
    for (int i = 0; i < nc; i++) {
        tcaster *k = &C[i];
        tmodel *md = &models[rnd() % nmodels];
        int rigid = (int)(rnd() % 100) < c->rigid_pct;
        uint8_t *sh = calloc(1, 0x4a00);
        k->sh = sh; k->g = NULL;
        AT(sh, SH_GEOM, uint8_t *) = geometry(md, rigid);
        for (int q = 0; q < ng; q++) if (G[q].geom == AT(sh, SH_GEOM, uint8_t *)) k->g = &G[q];
        sh[4] = 1;
        AT(sh, 0x74, float) = rnd() % 4 == 0 ? 0.6f : 0.0f;               /* shadow length clamp */
        AT(sh, CASTER_ID, int) = i;
        if (i) AT(C[i - 1].sh, SH_NEXT, uint8_t *) = sh;
        k->rot0 = frnd(0, 6.28f); k->rotv = rigid && rnd() % 3 == 0 ? 0 : frnd(0.02f, 0.2f);
        k->tx = frnd(-400, 400); k->ty = frnd(-400, 400); k->tz = frnd(0, 30); k->phase = frnd(0, 6);
        for (int j = 0; j < md->nmesh; j++) {
            int maxsil = md->mesh[j]->ntris * 6 > 32000 ? 32000 : md->mesh[j]->ntris * 6;
            AT(sh, SH_SIL + j * 4, void *) = calloc(maxsil + 8, 2);
            AT(sh, 0x4540 + j * 2, short) = (short)maxsil;
            sh[0x800 + j * 0xc + 8] = (uint8_t)j;
            if (rigid && rnd() % 2) ((alloc_t)(uintptr_t)(0x4f114e + OFF))(sh, 0, j, 1);  /* a CPU volume */
        }
    }
}

void world_free(void) { free(C); C = NULL; nc = 0; }

static void pose(const tcaster *c, const tmesh *tm, float *dst)
{
    float a = c->rot0 + c->rotv * frame, ca = cosf(a), sa = sinf(a);
    for (int i = 0; i < tm->nverts; i++) {
        const float *v = tm->verts + 3 * i;
        float x = v[0] + 0.08f * sinf(v[2] * 0.3f + 0.7f * frame + c->phase), y = v[1], z = v[2];
        dst[3 * i] = ca * x - sa * y + c->tx; dst[3 * i + 1] = sa * x + ca * y + c->ty; dst[3 * i + 2] = z + c->tz;
    }
}

__attribute__((force_align_arg_pointer))
void __attribute__((thiscall)) fake_update(uint8_t *sh, int force)
{
    (void)force;
    tcaster *c = &C[AT(sh, CASTER_ID, int)];
    uint8_t *geom = AT(sh, SH_GEOM, uint8_t *);
    for (int j = 0; j < AT(geom, GEO_NMESH, int); j++) {
        uint8_t *m = geom + GEO_MESH + j * MESH_SIZE;
        tmesh *tm = c->g->md->mesh[j];
        float xf[12], box[6], lo[3] = {1e30f, 1e30f, 1e30f}, hi[3] = {-1e30f, -1e30f, -1e30f};
        const float *x = ident, *pts;
        float *tmp = NULL;
        if (m[M_SKINNED]) {                             /* updateVolumes' skinning, then +8/+0x10 */
            if (*(int *)0xdd1854 < tm->nverts) ((resize_t)(uintptr_t)(0x4f0619 + OFF))((void *)0xdd184c, tm->nverts, 0);
            float *dst = *(float **)0xdd1850;
            pose(c, tm, dst);
            AT(m, M_VERTS, float *) = dst; AT(m, M_NORMALS, void *) = NULL;
            pts = dst;
        } else {
            float a = c->rot0 + c->rotv * frame, ca = cosf(a), sa = sinf(a);
            float r[12] = {ca, -sa, 0, c->tx, sa, ca, 0, c->ty, 0, 0, 1, c->tz};
            memcpy(xf, r, sizeof xf); x = xf;
            tmp = malloc(tm->nverts * 12);
            for (int i = 0; i < tm->nverts; i++) {
                const float *v = tm->verts + 3 * i;
                for (int k = 0; k < 3; k++) tmp[3 * i + k] = r[4 * k] * v[0] + r[4 * k + 1] * v[1] + r[4 * k + 2] * v[2] + r[4 * k + 3];
            }
            pts = tmp;
        }
        for (int i = 0; i < tm->nverts; i++)
            for (int k = 0; k < 3; k++) { float v = pts[3 * i + k]; if (v < lo[k]) lo[k] = v; if (v > hi[k]) hi[k] = v; }
        for (int k = 0; k < 3; k++) { box[k] = (lo[k] + hi[k]) * 0.5f; box[3 + k] = (hi[k] - lo[k]) * 0.5f; }
        free(tmp);
        ((umv_t)(uintptr_t)(0x4f28e9 + OFF))(sh, j, 0, x, box, lo[2] - 0.5f);
        uint8_t *vol = AT(sh, SH_VOL + j * 4, uint8_t *);
        if (!vol) continue;
        if (AT(vol, 0x44, int) == 8) AT(vol, 0x44, int) = 2;   /* "parent visible" */
        if (AT(vol, 0x44, int) == 2 && !AT(sh, SH_VB + j * 4, void *)) {
            uint8_t *task = sh + 0x800 + j * 0xc;
            AT(task, 0, void *) = AT(tasklist, 4, void *);
            AT(tasklist, 4, void *) = task;
        }
    }
}

static uint64_t hash_mesh_state(uint64_t h, uint8_t *sh, int j)
{
    short sn = AT(sh, SH_SILN + j * 2, short);
    h = fnv(h, &sn, 2);
    h = fnv(h, sh + SH_SILD + j * 4, 4);
    if (sn > 0) h = fnv(h, AT(sh, SH_SIL + j * 4, void *), sn * 2);
    uint8_t *vol = AT(sh, SH_VOL + j * 4, uint8_t *);
    if (vol) {
        int nv = AT(vol, V_NVERTS, int), np = AT(vol, V_NPOLYS, int);
        h = fnv(h, vol + V_NPOLYS, 12);
        h = fnv(h, vol + 0x44, 4);
        if (nv > 0) h = fnv(h, AT(vol, V_VERTS, void *), nv * 12);
        if (np > 0) h = fnv(h, AT(vol, V_POLYS, void *), np * 6);
    }
    return h;
}

__attribute__((force_align_arg_pointer))
void __attribute__((thiscall)) fake_render(uint8_t *sh, int mesh, int li)
{
    int id = AT(sh, CASTER_ID, int), rec[3] = {id, mesh, li};
    TR = fnv(TR, rec, 12);
    TR = hash_mesh_state(TR, sh, mesh);
    ncalls++;
}

__attribute__((force_align_arg_pointer))
void __attribute__((thiscall)) fake_construct_vb(uint8_t *sh, const float *lp, float ext, int li, int mesh)
{
    int id = AT(sh, CASTER_ID, int), rec[3] = {id, mesh, li};
    short sn = AT(sh, SH_SILN + mesh * 2, short);
    TV = fnv(TV, rec, 12); TV = fnv(TV, lp, 12); TV = fnv(TV, &ext, 4); TV = fnv(TV, &sn, 2);
    if (sn > 0) TV = fnv(TV, AT(sh, SH_SIL + mesh * 4, void *), sn * 2);
    ncalls++;
}

static uint64_t digest(void)
{
    uint64_t h = 0xcbf29ce484222325ull;
    for (int i = 0; i < nc; i++) {
        uint8_t *sh = C[i].sh;
        for (int j = 0; j < C[i].g->md->nmesh; j++) h = hash_mesh_state(h, sh, j);
    }
    for (int i = 0; i < ng; i++)
        for (int j = 0; j < G[i].md->nmesh; j++) {
            uint8_t *m = G[i].geom + GEO_MESH + j * MESH_SIZE;
            if (AT(m, M_NB, void *)) h = fnv(h, AT(m, M_NB, void *), AT(m, M_NNB, int) * NB_SIZE);
            int st = !AT(m, M_NORMALS, void *) ? 0 : AT(m, M_NORMALS, void *) == *(void **)0xdd1868 ? 1 : 2;
            h = fnv(h, &st, 4);
            if (st == 2) h = fnv(h, AT(m, M_NORMALS, void *), AT(m, M_NPOLYS, int) * 12);
        }
    for (int v = 0; v < 2; v++) {                       /* both scratch vectors, whole capacity */
        uint8_t *vec = (uint8_t *)(v ? 0xdd1864 : 0xdd184c);
        int cap = AT(vec, 8, int);
        h = fnv(h, &cap, 4);
        if (cap > 0) h = fnv(h, AT(vec, 4, void *), cap * 12);
    }
    return h;
}

void (*world_runner)(uint8_t *first, uint8_t *list) = run_caster_loop;

void world_run(const world_cfg *c, world_out *o)
{
    TR = TV = 0xcbf29ce484222325ull; ncalls = 0;
    o->loop_us = 0;
    for (frame = 0; frame < c->frames; frame++) {
        lightmgr[3] = -2000 + 10.0f * frame; lightmgr[4] = 1500; lightmgr[5] = 3000;
        AT(tasklist, 4, void *) = NULL;
        uint64_t t0 = now_us();
        world_runner(C[0].sh, tasklist);
        if (frame) o->loop_us += now_us() - t0;      /* frame 0 builds the neighbor arrays */
        o->frame_digest[frame] = digest();
    }
    o->draws = TR; o->builds = TV; o->ncalls = ncalls;
}
