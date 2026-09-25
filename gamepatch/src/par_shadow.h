/* Stencil shadow volumes on several cores (shadowpar), the O(n) edge chaining (edgemap) and the
 * shadow counters (shadowstats, p_shstats.c).
 * Game side (RotWK 2.02), per frame, for every shadow caster (W3DVolumetricShadowManager::
 * renderShadows 0x4f43a6, caster loop 0x4f4fa5; reached only while UseShadowVolumes is on, which
 * GameLOD turns off whenever UseShadowMapping is on, e.g. at UltraHigh): Update 0x4f3906 ->
 * updateVolumes 0x4f3626 (CPU skinning into the scratch vector 0xdd184c) -> updateMeshVolume 0x4f28e9 -> [buildPolygonNormals 0x4f21b2,
 * buildSilhouette 0x4f2614, allocateShadowVolume 0x4f114e, constructVolume 0x4ef790], then the
 * loop renders the caster's new dynamic volumes (RenderVolume 0x4f42bf).
 * par_shadow.c: hooks and the caster loop; par_shjob.c: the jobs; p_edgemap.c; p_shadow.S. */
#ifndef PAR_SHADOW_H
#define PAR_SHADOW_H
#include "gp.h"

/* game layout (W3DVolumetricShadow = "shadow", W3DShadowGeometry = "geometry",
 * W3DShadowGeometryMesh = "mesh", Geometry = the shadow volume) */
#define SH_NEXT      0x68     /* next caster in the manager's list */
#define SH_GEOM      0x6c     /* W3DShadowGeometry* (shared by every instance of a model) */
#define SH_VOL       0x80     /* Geometry* [light*0xa0 + mesh] */
#define SH_VB        0x300    /* static VB slot per volume (0 = none) */
#define SH_SIL       0x4180   /* short* silhouette index array per mesh (owned by the shadow) */
#define SH_SILN      0x4400   /* short  silhouette index count per mesh */
#define SH_SILD      0x4680   /* int    indices added by the last buildSilhouette per mesh */
#define GEO_MESH     0x14     /* meshes, 0x34 bytes each */
#define GEO_NMESH    0x2094
#define GEO_SIZE     0x2098
#define MESH_SIZE    0x34
#define M_VERTS      0x08     /* Vector3* (skinned: the scratch 0xdd1850) */
#define M_NORMALS    0x10     /* Vector3* per polygon (0 = not built; skinned: scratch 0xdd1868) */
#define M_NVERTS     0x18
#define M_NPOLYS     0x1c
#define M_NB         0x24     /* PolyNeighbor[], 0x16 bytes each, flags byte at +2 */
#define M_NNB        0x28
#define M_SKINNED    0x30     /* byte */
#define NB_SIZE      0x16
#define V_VERTS      0x00     /* volume: Vector3* */
#define V_POLYS      0x04     /* volume: 3 shorts per polygon */
#define V_NPOLYS     0x10
#define V_NVERTS     0x14
#define V_FLAGS      0x18     /* bit 0: dynamic (built on the CPU by constructVolume) */
#define G_SKIN_PTR   0xdd1850 /* skinned-vertex scratch vector 0xdd184c: data, capacity */
#define G_NORM_VEC   0xdd1864 /* face-normal scratch vector: data 0xdd1868, capacity 0xdd186c */
#define G_NORM_PTR   0xdd1868
#define G_NORM_CAP   0xdd186c
#define AT(p, off, T) (*(T *)((uint8_t *)(p) + (off)))

/* game functions (va + gp_va_offset, set by gp_sp_bind; the tests may point them elsewhere) */
typedef void *(__attribute__((thiscall)) *gpf_poly_normal)(void *mesh, int poly, float *out);
typedef void (__attribute__((thiscall)) *gpf_normals)(void *mesh);
typedef void (__attribute__((thiscall)) *gpf_silhouette)(void *sh, int mesh, const float *light);
typedef void (__attribute__((thiscall)) *gpf_construct)(void *sh, const float *light, float extrude,
                                                         int li, int mesh);
typedef char (__attribute__((thiscall)) *gpf_alloc)(void *sh, int li, int mesh, int flags);
typedef void (__attribute__((thiscall)) *gpf_reset)(void *sh, int li, int mesh);
typedef char (__attribute__((thiscall)) *gpf_resize)(void *vec, int n, int keep);
typedef void (__attribute__((thiscall)) *gpf_update)(void *sh, int force);
typedef void (__attribute__((thiscall)) *gpf_render)(void *sh, int mesh, int li);
typedef struct {
    gpf_poly_normal poly_normal;  /* 0x4f1613 */
    gpf_normals     normals;      /* 0x4f21b2 */
    gpf_silhouette  silhouette;   /* 0x4f2614 */
    gpf_construct   construct;    /* 0x4ef790 */
    gpf_alloc       alloc;        /* 0x4f114e */
    gpf_reset       reset;        /* 0x4f00e8 */
    gpf_resize      resize;       /* 0x4f0619 */
    gpf_update      update;       /* 0x4f3906 */
    gpf_render      render;       /* 0x4f42bf */
    gpf_construct   construct_vb; /* 0x4efbeb constructVolumeVB (static volume, D3D) */
} gp_sp_fns;
extern gp_sp_fns gp_sp;
void gp_sp_bind(void);

/* settings: gamepatch.ini [patches] shadowpar_<key>, or GAMEPATCH_SHADOWPAR_<KEY> */
typedef struct {
    int verify;      /* first N caster loops with jobs: serial reference + parallel, compared */
    int workers;     /* 0 = auto (cores - 1, at most 7) */
    int a1_min;      /* the triangle-normal loop goes parallel from this many triangles */
    int log_every;   /* caster loops between two summary lines */
    int sample;      /* every Nth caster loop runs serially, for the timing line (0 = never) */
} gp_sp_config;
extern gp_sp_config gp_spc;

/* par_shjob.c: the job queue (main thread, except the item runner) */
typedef struct {
    long long jobs, items, inline_blocks, flushes, faults, mismatches, verified_jobs;
    double ref_us, par_us;           /* verify loops: serial reference vs parallel, summed */
} gp_sp_stats_t;
extern gp_sp_stats_t gp_sp_stats;
extern int gp_sp_disabled;           /* a mismatch or fault: serial for the rest of the session */
extern int gp_sp_nslots;             /* pool participants (workers + main); 1 without the pool */
int  gp_sp_eligible(uint8_t *sh, int mesh, int li);
void gp_sp_capture(uint8_t *sh, int mesh, int li, const float *light, float extrude);
void gp_sp_snapshot_ref(void);       /* verify: keep the reference outputs of the last capture */
void gp_sp_drop_last(void);          /* the captured block was not a dynamic volume after all */
int  gp_sp_pending(void);
int  gp_sp_flush(int verify);        /* run the pending jobs (0, or verify 1/2); mismatches + faults */
void gp_sp_reset_queue(void);

/* par_shadow.c: entry points called from p_shadow.S */
int  gp_sp_block(uint8_t *sh, uint8_t *frame);
void gp_sp_casters(uint8_t *first, uint8_t *list);
void gp_sp_normals(uint8_t *mesh, float *out);
extern int gp_sp_collecting, gp_sp_verifying;
extern long long gp_sp_loops;        /* caster loops run through gp_sp_casters */
extern int gp_sp_on;                 /* shadowpar installed */
int  gp_patch_shadowpar(void);

/* p_edgemap.c */
void gp_cv_prepermute(uint8_t *sh, const void *light, int li, int mesh);
void gp_cv_permute(uint16_t *sil, int count, int slot);   /* slot < 0: linear search, no index */
int  gp_cv_slot(void);
int  gp_patch_edgemap(void);
extern volatile LONG gp_cv_calls, gp_cv_chained;   /* constructVolume calls; those with > 2 indices */
extern int gp_cv_on;

/* p_shstats.c */
typedef struct {
    LONG rs_calls, rs_reach, rs_empty, rs_voloff, rs_nodev;   /* 0x4f43a6 entries by outcome */
    LONG sm_calls, sm_on;                                     /* 0x47d5c9 entries; with mapping on */
    LONG cv_calls, cv_chained;                                /* copies, at the last periodic */
    long long sp_loops, sp_jobs, sp_inline;
} gp_shst_t;
extern gp_shst_t gp_shst;
void gp_shst_rs(const uint8_t *mgr);
void gp_shst_sm(void);
void gp_shadow_periodic(void);       /* main thread; logs every 60 s */
void gp_shadow_exit_log(void);
int  gp_patch_shadowstats(void);

/* p_shadow.S */
void gp_sp_loop_stub(void);
void gp_sp_block_stub(void);
void gp_sp_a1_stub(void);
void gp_cv_entry_stub(void);
void gp_shst_rs_stub(void);
void gp_shst_sm_stub(void);
extern uint32_t gp_sp_loop_cont, gp_sp_block_orig, gp_sp_block_tail, gp_sp_block_done,
                gp_sp_a1_cont, gp_cv_cont, gp_shst_rs_cont, gp_shst_sm_cont;
#endif
