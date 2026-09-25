/* t_shadow: shared between t_shadow.c (the checks) and t_shadow_world.c (models, casters, the
 * stand-ins for the game parts around the shadow code). */
#ifndef T_SHADOW_H
#define T_SHADOW_H
#include "par_shadow.h"

typedef struct {                  /* one mesh: welded positions, render triangles, remap */
    char name[40];
    int nverts, ntris, skinned;
    float *verts;                 /* nverts * 3 (bind pose / rigid) */
    uint16_t *tris;               /* ntris * 3 render-vertex indices */
    uint16_t *remap;              /* render vertex -> welded vertex */
    int nrender;
} tmesh;
typedef struct { char name[48]; int nmesh; tmesh *mesh[8]; } tmodel;

extern tmodel models[32];
extern int nmodels;
int  load_w3d_models(const char *exe_path);   /* from W3D.big next to the exe; returns count */
void add_synthetic_models(void);

/* a world: casters (shadow objects) over shared geometries, run for frames */
typedef struct {
    int ncasters, frames, rigid_pct;
    unsigned seed;
} world_cfg;
typedef struct {
    uint64_t *frame_digest;       /* per frame: every silhouette, volume, shared scratch/flags */
    uint64_t draws, builds;       /* RenderVolume / constructVolumeVB calls in order, with their data */
    long long ncalls;
    double loop_us;               /* caster loop wall time, frames 1.. */
} world_out;
void world_build(const world_cfg *c);
void world_run(const world_cfg *c, world_out *o);
void world_free(void);

/* installed in the code copy by t_shadow.c */
extern uint32_t OFF;
void __attribute__((thiscall)) fake_update(uint8_t *sh, int force);
void __attribute__((thiscall)) fake_render(uint8_t *sh, int mesh, int li);
void __attribute__((thiscall)) fake_construct_vb(uint8_t *sh, const float *lp, float ext, int li, int mesh);
void run_caster_loop(uint8_t *first, uint8_t *list);     /* asm: the loop at its game address */
extern void (*world_runner)(uint8_t *first, uint8_t *list);   /* how world_run runs a frame's loop */
extern volatile int corrupt_on_workers;       /* negative test: jobs on workers write one wrong float */
extern DWORD main_tid;

uint64_t fnv(uint64_t h, const void *p, size_t n);
uint32_t rnd(void);
float frnd(float lo, float hi);
#endif
