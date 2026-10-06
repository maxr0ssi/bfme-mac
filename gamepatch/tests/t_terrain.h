/* Shared by t_terrain32.c and t_terrainshot.c: the game's own terrain-tile bake run on a fake
 * WorldHeightMap built from a map's terrain data (a scene file, build/terrain-preview/NAME.scene, made
 * by a helper from the map and its TGA art; or a synthetic one), plus a PNG writer. */
#ifndef T_TERRAIN_H
#define T_TERRAIN_H
#define COBJMACROS
#include "orig.h"
#include "p_mipfilter.h"
#include "p_terrain.h"

typedef struct {
    int width, height, border, n;
    int16_t *tile, *blend, *extra;
    int nblend;
    struct { int32_t ndx; uint8_t f[6]; int32_t custom; } *be;   /* horiz vert rdiag ldiag inverted longdiag */
    int ntiles;
    struct { int32_t slot; int hasnrm; uint8_t *bgra, *nrm; } *src;
} t_scene;

int  t_scene_load(t_scene *s, const char *path);       /* 0 = ok */
void t_scene_synth(t_scene *s, uint32_t seed);         /* 64 x 64 cells, random tiles and blends */

/* the world: maps the exe's code (at +off) and data, applies mipfilter, terrainbox and terrain32 to
 * the copy, builds the WorldHeightMap and TileData (through gp_t32_fill: 16-bit + 8-bit shadows) */
uint32_t t_world_init(const char *exe);                  /* returns the code offset, 0 on failure */
void *t_world_build(const t_scene *s);                   /* the fake WorldHeightMap */
void  t_world_set_shadows(void *hm, int on);             /* turn every TileData's 8-bit shadow on / off */
void  t_world_shadows_from16(void *hm);                  /* shadows := the 16-bit pixels expanded (v<<3|v>>2) */
void  t_world_shadows_real(void *hm, const t_scene *s);  /* shadows := the real 8-bit averages */

/* one tile's texture through the game's bake (0x4eec82, A1R5G5B5, or 0x4eee64, DXT1) or terrain32's
 * (X8R8G8B8); the bake ends in whatever D3DXFilterTexture its call site calls */
gp_fake_tex *t_bake(void *hm, D3DFORMAT fmt, int x0, int y0, int cells, int ppc, int layer, double *ms);

/* pixels of a level as 0x00RRGGBB (A1R5G5B5 bit-replicated, X8R8G8B8, DXT1 decoded) */
uint32_t *t_level_rgb(gp_fake_tex *t, UINT level, UINT *w, UINT *h);
int t_png(const char *path, const uint32_t *rgb, UINT w, UINT h);       /* 0 = ok */
#endif
