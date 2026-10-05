/* t_path: the game's own pathfinder search (RotWK 2.02) on a synthetic map, shared declarations
 * between the world (t_path_world.c) and the tests (t_path.c). */
#ifndef T_PATH_H
#define T_PATH_H
#include <stdint.h>

#define TC __attribute__((thiscall))
#define U8(p, o)  (*(uint8_t *)((uint8_t *)(p) + (o)))
#define U16(p, o) (*(uint16_t *)((uint8_t *)(p) + (o)))
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define I32(p, o) (*(int32_t *)((uint8_t *)(p) + (o)))
#define F32(p, o) (*(float *)((uint8_t *)(p) + (o)))
#define PTR(p, o) ((uint8_t *)(uintptr_t)U32(p, o))

extern uint32_t OFF;                     /* where the game's .text runs: va + OFF */

typedef struct {
    int w, h;                            /* map size in cells (10 world units each) */
    int units;                           /* units on the map, in battle clusters */
    uint32_t seed;                       /* map and units */
    uint32_t salt;                       /* memory layout only: padding, allocation and pool order */
    int packed;                          /* battle 0 is a packed block, one standing unit per cell */
} pw_cfg;

typedef struct pw pw_t;                  /* a built world (map, pathfinder, units, info pool) */

typedef struct {
    int sx, sy, gx, gy;                  /* start and goal cells */
    int mover;                           /* 0..3: footprint 1, 3, 4, 9 cells (9: a horde) */
    int attack;                          /* the search step's 9th argument (0 or 1) */
    int limit;                           /* cells allocated before giving up (MaxCellsFindPathLimit) */
    int moveaway;                        /* 1: no goal; stop at the first free spot off the start's row */
} pw_query;

typedef struct {
    int found, steps, cells, pathlen, cost;
    uint64_t pops;                       /* hash of every popped cell: position, total cost, cost so far */
    uint64_t path;                       /* hash of the path cells from the goal back to the start */
    uint64_t lists;                      /* hash of the open and closed lists' cells and costs at the end */
    uint64_t us;                         /* time of the search and its clean-up */
    int leftover;                        /* infos left on cells outside any list (released afterwards) */
    int kept;                            /* units' and obstacles' infos whose parent is pw_stale at the end */
} pw_result;

int    pw_init(const char *exe);         /* map the image, imports, stand-ins; 0 = ok */
pw_t  *pw_build(const pw_cfg *c);
void   pw_free(pw_t *w);
void   pw_search(pw_t *w, const pw_query *q, pw_result *r);
void   pw_queries(pw_t *w, pw_query *q, int n, uint32_t seed);   /* reachable, crowded, unreachable */
extern void *pw_moveaway_pop;            /* pop used by move-away searches (NULL: the game's 0x6f4af2) */
void   pw_moveaways(pw_t *w, pw_query *q, int n, uint32_t seed);  /* from inside the packed block */
int    pw_patch(int on);                 /* 1: apply gp_patch_pathfind (first time) or restore it;
                                          * 0: put the original bytes back. 1 = ok */
/* direct calls of one function, original or patched, on the world's cells (for [3]) */
int    pw_direct(pw_t *w, uint32_t seed, int n, int *mismatch_cfm, int *mismatch_crowd);
void   pw_stats(pw_t *w, int *units, int *blocked);
int    pw_maq_test(pw_t *w);              /* [7]; 1 = as expected */
/* [8] pathsplit (t_path_split.c) */
extern uint64_t pw_scan_us;             /* time in pw_search's clean-up scans (not the game's) */
extern uint8_t *(*pw_split_pop)(uint8_t *pf, uint8_t *obj, uint8_t *goal);   /* pop of non-move-away searches */
uint8_t *pw_pf(pw_t *w);
uint8_t *pw_mover(pw_t *w, int m);
void   pw_center(pw_t *w, int battle, int *x, int *y);    /* battle 0: the packed block; 3: the closed base */
int    pw_split_test(const pw_cfg *cfg, int nq);           /* 1 = pass */
extern uint32_t pw_stale;                /* parent (+0x8) planted in the units' and obstacles' infos, 0: none */
void   pw_plant(pw_t *w, uint32_t parent);   /* as an earlier search leaves them (the game does not reset) */
#endif
