/* t_phasebal: the game's GameLogic::update on a synthetic world (t_phasebal_world.c). */
#ifndef T_PHASEBAL_H
#define T_PHASEBAL_H
#include <stdint.h>

/* one event of a logic step, in the order the game's code made it */
enum { EV_MOD, EV_Q, EV_D, EV_SUB, EV_AI, EV_P2, EV_PEND, EV_SUBCALL };
typedef struct { uint16_t step; uint8_t phase, kind; uint32_t id, aux; } pb_ev;

typedef struct {
    uint32_t seed, salt;       /* world, memory layout (0 = none) */
    int mutate;                /* 1: wake-ups between passes, creations, destructions, cross wakes */
    int nobj;                  /* objects at the start (each 1-3 update modules) */
} pb_cfg;

typedef struct pb_world pb_world;
extern uint32_t OFF;
int  pb_init(const char *exe);                 /* map the image, stand-ins; 0 = ok */
int  pb_patch(int mode);                       /* 0 original bytes, 1 balanced, 2 EA's split by the hooks */
pb_world *pb_build(const pb_cfg *c);
void pb_free(pb_world *w);
/* run steps logic steps (phases 2-6 through the game's code; phase 1's frame +1 by the test); the
 * events go to ev (at most max), returns their number. Per step: due[] counts the modules due at the
 * step's start that were not updated in it (missed), twice[] those updated twice. */
int  pb_run(pb_world *w, int steps, pb_ev *ev, int max, int *missed, int *twice, int *unordered);
void pb_counts(pb_world *w, int *modules, int *lists);   /* modules alive; list sizes summed */
double pb_us_per_step(pb_world *w, int steps);           /* timing of phases 2-6 only, in us */
void *pb_iface_vt(void);                                 /* the update modules' interface vtable */
#endif
