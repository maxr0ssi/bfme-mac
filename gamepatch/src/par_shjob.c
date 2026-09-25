/* shadowpar jobs. A job is the heavy part of one updateMeshVolume block: face normals, silhouette,
 * dynamic volume. The main thread captures its inputs when the caster loop reaches the block
 * (after the serial parts: skinning, allocation); gp_sp_flush runs all captured jobs on the pool
 * (item = the consecutive jobs of one shadow, run in order on one thread) and then leaves the
 * shared state exactly as the serial game would have.
 *
 * What a job touches, and why it can run on any thread:
 *  - reads: the mesh's polygons and remap (immutable), its vertices (skinned: copied here from the
 *    scratch 0xdd1850, which the next caster's skinning overwrites; rigid: the model's own),
 *    cached face normals (rigid only; skinned normals are computed by the job);
 *  - writes: the shadow's silhouette arrays and its volume (owned by that shadow), and the flag
 *    byte of every PolyNeighbor of the mesh. The neighbor array belongs to the geometry, shared by
 *    every instance of a model, so each job works on a private copy of the mesh descriptor and of
 *    that array; the game code finds its mesh through shadow->geometry (+0x6c), which points at a
 *    per-thread copy while the job runs.
 *  - effects the serial game leaves behind, replayed after the join: the face-normal scratch
 *    0xdd1868 holds the normals of the last skinned mesh built (its resize happens at capture, in
 *    order), and each shared neighbor array holds the flags of the last job on it. */
#include "par_shadow.h"
#include "parallel.h"
#include <stdlib.h>
#include <string.h>

gp_sp_stats_t gp_sp_stats;
int gp_sp_disabled;
int gp_sp_nslots = 1;                  /* pool workers + main */

typedef struct {
    uint8_t *sh, *geom, *nb;
    int mesh, li, npolys, nnb, nverts, owner;
    float lp[3], extrude;
    uint8_t mcopy[MESH_SIZE];
    int verts_off, normals_off, flags_off, ref_off;   /* arena offsets, -1 = none */
} job_t;

static job_t *J; static int nj, capj;
static int *items; static int nitems, capitems;       /* first job of each item */
static uint8_t *A; static size_t nA, capA;             /* per-flush arena */
typedef struct { uint8_t *geom, *nb; int capnb; } slotbuf;
static slotbuf SB[34];

static int grow(void **p, int *cap, int need, size_t elem)
{
    if (need <= *cap) return 1;
    int n = *cap ? *cap : 64;
    while (n < need) n *= 2;
    void *q = realloc(*p, (size_t)n * elem);
    if (!q) return 0;
    *p = q; *cap = n;
    return 1;
}

static int arena(size_t n)
{
    size_t off = (nA + 15) & ~(size_t)15;
    if (off + n > capA) {
        size_t c = capA ? capA : 1 << 20;
        while (c < off + n) c *= 2;
        uint8_t *q = realloc(A, c);
        if (!q) return -1;
        A = q; capA = c;
    }
    nA = off + n;
    return (int)off;
}

/* Can this block be deferred? The rare cases that are not run inline, as in the original:
 * neighbors not built yet (buildSilhouette builds them lazily from the current normals),
 * rigid face normals not cached yet (allocated on first use), a skinned mesh that was not
 * re-skinned in this updateVolumes call (it reads the scratch vectors as they are). */
int gp_sp_eligible(uint8_t *sh, int mesh, int li)
{
    if (li != 0 || mesh < 0 || mesh >= 0xa0) return 0;
    uint8_t *geom = AT(sh, SH_GEOM, uint8_t *);
    if (!geom) return 0;
    uint8_t *m = geom + GEO_MESH + mesh * MESH_SIZE;
    int np = AT(m, M_NPOLYS, int);
    if (np <= 0 || !AT(m, M_NB, void *) || AT(m, M_NNB, int) < np) return 0;
    if (m[M_SKINNED])
        return !AT(m, M_NORMALS, void *) && AT(m, M_VERTS, void *) == *(void **)G_SKIN_PTR &&
               AT(m, M_NVERTS, int) > 0;
    return AT(m, M_NORMALS, void *) != NULL;
}

/* inputs of the block, before anything in it has run */
void gp_sp_capture(uint8_t *sh, int mesh, int li, const float *light, float extrude)
{
    if (!grow((void **)&J, &capj, nj + 1, sizeof *J) || !grow((void **)&items, &capitems, nitems + 1, sizeof *items))
        abort();
    job_t *j = &J[nj];
    uint8_t *geom = AT(sh, SH_GEOM, uint8_t *), *m = geom + GEO_MESH + mesh * MESH_SIZE;
    j->sh = sh; j->geom = geom; j->mesh = mesh; j->li = li;
    memcpy(j->lp, light, 12); j->extrude = extrude;
    memcpy(j->mcopy, m, MESH_SIZE);
    j->nb = AT(m, M_NB, uint8_t *); j->nnb = AT(m, M_NNB, int); j->npolys = AT(m, M_NPOLYS, int);
    j->owner = m[M_SKINNED] != 0;
    j->verts_off = j->normals_off = j->ref_off = -1;
    j->nverts = AT(m, M_NVERTS, int);
    if (j->owner) {
        j->verts_off = arena((size_t)j->nverts * 12);
        j->normals_off = arena((size_t)j->npolys * 12);
        if (j->verts_off < 0 || j->normals_off < 0) abort();
        memcpy(A + j->verts_off, AT(m, M_VERTS, void *), (size_t)j->nverts * 12);
    }
    if ((j->flags_off = arena((size_t)j->npolys)) < 0) abort();
    if (!nj || J[nj - 1].sh != sh) items[nitems++] = nj;
    nj++;
}

void gp_sp_drop_last(void)
{
    if (!nj) return;
    nj--;
    if (nitems && items[nitems - 1] == nj) nitems--;
}

int gp_sp_pending(void) { return nj; }
void gp_sp_reset_queue(void) { nj = nitems = 0; nA = 0; }

/* verify: the reference outputs of the last captured job, right after the original ran it */
void gp_sp_snapshot_ref(void)
{
    job_t *j = &J[nj - 1];
    uint8_t *vol = AT(j->sh, SH_VOL + (j->li * 0xa0 + j->mesh) * 4, uint8_t *);
    int sn = AT(j->sh, SH_SILN + j->mesh * 2, short), nv = AT(vol, V_NVERTS, int), np = AT(vol, V_NPOLYS, int);
    if (sn < 0) sn = 0;
    size_t len = 16 + (size_t)sn * 2 + (size_t)nv * 12 + (size_t)np * 6;
    int off = arena(len);
    if (off < 0) abort();
    uint8_t *r = A + off;
    int hdr[4] = {sn, AT(j->sh, SH_SILD + j->mesh * 4, int), nv, np};
    memcpy(r, hdr, 16);
    memcpy(r + 16, AT(j->sh, SH_SIL + j->mesh * 4, void *), (size_t)sn * 2);
    memcpy(r + 16 + sn * 2, AT(vol, V_VERTS, void *), (size_t)nv * 12);
    memcpy(r + 16 + sn * 2 + nv * 12, AT(vol, V_POLYS, void *), (size_t)np * 6);
    j->ref_off = off;
}

static void run_job(job_t *j, slotbuf *b)
{
    uint8_t *pm = b->geom + GEO_MESH + j->mesh * MESH_SIZE;
    memcpy(b->geom, j->geom, GEO_MESH);
    AT(b->geom, GEO_NMESH, int) = AT(j->geom, GEO_NMESH, int);
    memcpy(pm, j->mcopy, MESH_SIZE);
    if (j->verts_off >= 0) AT(pm, M_VERTS, void *) = A + j->verts_off;
    memcpy(b->nb, j->nb, (size_t)j->nnb * NB_SIZE);
    AT(pm, M_NB, void *) = b->nb;
    if (j->normals_off >= 0) {                       /* buildPolygonNormals' loop, private output */
        float *out = (float *)(A + j->normals_off);
        AT(pm, M_NORMALS, void *) = NULL;
        for (int i = 0; i < j->npolys; i++) gp_sp.poly_normal(pm, i, out + 3 * i);
        AT(pm, M_NORMALS, void *) = out;
    }
    AT(j->sh, SH_GEOM, void *) = b->geom;            /* the game code reaches the mesh through it */
    AT(j->sh, SH_SILN + j->mesh * 2, short) = 0;     /* resetSilhouette (a retry starts clean) */
    gp_sp.silhouette(j->sh, j->mesh, j->lp);
    gp_sp.construct(j->sh, j->lp, j->extrude, j->li, j->mesh);
    AT(j->sh, SH_GEOM, void *) = j->geom;
    uint8_t *fl = A + j->flags_off;
    for (int i = 0; i < j->npolys; i++) fl[i] = b->nb[i * NB_SIZE + 2];
}

static void run_items(int begin, int end, void *ctx, int slot)
{
    (void)ctx;
    for (int it = begin; it < end; it++) {
        int k1 = it + 1 < nitems ? items[it + 1] : nj;
        for (int k = items[it]; k < k1; k++) run_job(&J[k], &SB[slot]);
    }
}

static int compare_refs(void)
{
    int bad = 0;
    for (int k = 0; k < nj; k++) {
        job_t *j = &J[k];
        if (j->ref_off < 0) continue;
        uint8_t *r = A + j->ref_off, *vol = AT(j->sh, SH_VOL + (j->li * 0xa0 + j->mesh) * 4, uint8_t *);
        int hdr[4]; memcpy(hdr, r, 16);
        int sn = hdr[0], nv = hdr[2], np = hdr[3];
        uint8_t *sil = AT(j->sh, SH_SIL + j->mesh * 4, uint8_t *);
        const char *what = NULL;
        if (AT(j->sh, SH_SILN + j->mesh * 2, short) != sn || AT(j->sh, SH_SILD + j->mesh * 4, int) != hdr[1])
            what = "silhouette count";
        else if (memcmp(sil, r + 16, (size_t)sn * 2)) what = "silhouette indices";
        else if (AT(vol, V_NVERTS, int) != nv || AT(vol, V_NPOLYS, int) != np) what = "volume counts";
        else if (memcmp(AT(vol, V_VERTS, void *), r + 16 + sn * 2, (size_t)nv * 12)) what = "volume vertices";
        else if (memcmp(AT(vol, V_POLYS, void *), r + 16 + sn * 2 + nv * 12, (size_t)np * 6)) what = "volume indices";
        gp_sp_stats.verified_jobs++;
        if (!what) continue;
        if (bad++ < 3)
            gp_log("shadowpar: MISMATCH shadow %p mesh %d (%d polygons): %s differ from the serial "
                   "reference; reference restored", j->sh, j->mesh, j->npolys, what);
        AT(j->sh, SH_SILN + j->mesh * 2, short) = (short)sn;
        AT(j->sh, SH_SILD + j->mesh * 4, int) = hdr[1];
        memcpy(sil, r + 16, (size_t)sn * 2);
        AT(vol, V_NVERTS, int) = nv; AT(vol, V_NPOLYS, int) = np;
        memcpy(AT(vol, V_VERTS, void *), r + 16 + sn * 2, (size_t)nv * 12);
        memcpy(AT(vol, V_POLYS, void *), r + 16 + sn * 2 + nv * 12, (size_t)np * 6);
    }
    return bad;
}

/* the serial game's leftovers: last writer wins. check = compare instead of write (verify: the
 * reference already left the true state) */
static int writeback(int check)
{
    int bad = 0, n = 1;
    while (n < 2 * nj) n *= 2;
    uint8_t **seen = calloc(n, sizeof *seen);
    if (!seen) abort();
    for (int k = nj - 1; k >= 0; k--) {
        job_t *j = &J[k];
        unsigned h = ((uint32_t)(uintptr_t)j->nb >> 4) & (n - 1);
        while (seen[h] && seen[h] != j->nb) h = (h + 1) & (n - 1);
        if (seen[h]) continue;
        seen[h] = j->nb;
        const uint8_t *fl = A + j->flags_off;
        for (int i = 0; i < j->npolys; i++) {
            uint8_t *f = j->nb + i * NB_SIZE + 2;
            if (!check) *f = fl[i];
            else if (*f != fl[i]) { bad = 1; break; }
        }
    }
    free(seen);
    float *scr = *(float **)G_NORM_PTR;
    for (int k = nj - 1, covered = 0; k >= 0; k--) {
        job_t *j = &J[k];
        if (!j->owner || j->npolys <= covered) continue;
        const float *src = (const float *)(A + j->normals_off);
        size_t bytes = (size_t)(j->npolys - covered) * 12;
        if (!check) memcpy(scr + 3 * covered, src + 3 * covered, bytes);
        else if (memcmp(scr + 3 * covered, src + 3 * covered, bytes)) bad |= 2;
        covered = j->npolys;
    }
    if (bad) gp_log("shadowpar: MISMATCH in the shared state left behind (%s)",
                    bad & 1 ? "neighbor flags" : "face-normal scratch");
    return bad != 0;
}

/* verify: 0 = run and leave the serial game's shared state; 1 = compare every output with the
 * serial reference (which already left the shared state) and that state too; 2 = compare the
 * outputs only (the shared state has been overwritten since by a block that ran inline) */
int gp_sp_flush(int verify)
{
    if (!nj) return 0;
    int maxnb = 0, nslots = gp_sp_nslots;
    for (int k = 0; k < nj; k++) if (J[k].nnb > maxnb) maxnb = J[k].nnb;
    for (int s = 0; s < nslots; s++) {                /* worker buffers, allocated here on main */
        slotbuf *b = &SB[s];
        if (!b->geom && !(b->geom = calloc(1, GEO_SIZE))) abort();
        if (b->capnb < maxnb) {
            free(b->nb);
            if (!(b->nb = malloc((size_t)maxnb * NB_SIZE))) abort();
            b->capnb = maxnb;
        }
    }
    LARGE_INTEGER t0, t1, f;
    QueryPerformanceCounter(&t0);
    int faults = par_for(nitems, 1, run_items, NULL);
    QueryPerformanceCounter(&t1); QueryPerformanceFrequency(&f);
    double us = (t1.QuadPart - t0.QuadPart) * 1e6 / f.QuadPart;
    if (verify) gp_sp_stats.par_us += us;
    gp_sp_stats.jobs += nj; gp_sp_stats.items += nitems; gp_sp_stats.flushes++;
    gp_sp_stats.faults += faults;
    if (faults) gp_log("shadowpar: %d job chunks faulted on a worker and were redone on the main thread", faults);
    int bad = verify ? compare_refs() : 0;
    if (verify != 2) bad += writeback(verify);
    gp_sp_stats.mismatches += bad;
    gp_sp_reset_queue();
    return bad + faults;
}
