/* moveawayqueue: at most two move-away orders at once per path, the rest a little later.
 *
 * When a new path runs through idle allies, Pathfinder::moveAllies 0x6f503b walks the path's
 * cells and its cell callback 0x6f53af orders every idle ally it finds there to step aside
 * (aiMoveAwayFromUnit 0x66c66e, AI command 0x34). Each order runs the ally's move-away flood
 * (getMoveAwayFromPath 0x6fb231) at once, so a path through K allies costs K floods in one logic
 * phase (docs/PERFORMANCE.md §18). Here the callback's order call (0x6f550b) goes through
 * gp_maq_order: per mover and pathfind-queue run, the first gp_maq_limit orders are given as
 * before; later ones wait in a FIFO (object IDs, not pointers) and gp_maq_limit of them are given
 * at the start of each later queue run (0x6f2364 runs at the top of every logic phase), after
 * looking both objects up again by ID (an ally or mover that has gone is dropped). Everything is
 * counted in orders and queue runs, never time, so every machine gives the same orders at the same
 * logic step. Saved games do not keep the waiting orders (they are lost on load). */
#include "gp_logic.h"

#define TC __attribute__((thiscall))
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define PTR(p, o) ((uint8_t *)(uintptr_t)U32(p, o))
#define GFN(t, va) ((t)(uintptr_t)((va) + maq_off))

typedef void (TC *order_t)(void *cmd, void *mover, const float *pos, int source);   /* 0x66c66e */
typedef uint8_t *(TC *byid_t)(void *logic, uint32_t id);                             /* 0x449681 */

uint32_t gp_maq_limit = 2;
volatile LONG gp_maq_stats[4];           /* orders, waited, given later, dropped */
uint32_t gp_maq_cont;
static uint32_t maq_off, runs, key_run;
static void *key_mover;
static uint32_t given;

#define MQ 512
static struct { uint32_t ally, mover, source; float pos[3]; } fifo[MQ];
static int head, count;

void TC gp_maq_order(uint8_t *cmd, uint8_t *mover, const float *pos, int source)
{
    gp_maq_stats[0]++;
    if (key_run != runs || key_mover != mover) { key_run = runs; key_mover = mover; given = 0; }
    if (given < gp_maq_limit) { given++; GFN(order_t, 0x66c66e)(cmd, mover, pos, source); return; }
    if (count == MQ) { gp_maq_stats[3]++; return; }
    uint8_t *ally = PTR(cmd - 0x20, 8);                /* cmd = the ally's AIUpdateInterface + 0x20 */
    int i = (head + count++) % MQ;
    fifo[i].ally = U32(ally, 0x74); fifo[i].mover = U32(mover, 0x74); fifo[i].source = source;
    fifo[i].pos[0] = pos[0]; fifo[i].pos[1] = pos[1]; fifo[i].pos[2] = pos[2];
    gp_maq_stats[1]++;
}

/* the start of a pathfind-queue run: give up to gp_maq_limit waiting orders */
__attribute__((force_align_arg_pointer)) void gp_maq_run(void)
{
    runs++;
    for (uint32_t n = 0; n < gp_maq_limit && count; n++) {
        int i = head; head = (head + 1) % MQ; count--;
        void *logic = *(void **)(uintptr_t)0xde412c;
        uint8_t *ally = GFN(byid_t, 0x449681)(logic, fifo[i].ally);
        uint8_t *mover = GFN(byid_t, 0x449681)(logic, fifo[i].mover);
        uint8_t *ai = ally ? PTR(ally, 0x260) : NULL;
        if (!mover || !ai) { gp_maq_stats[3]++; continue; }
        gp_maq_stats[2]++;
        GFN(order_t, 0x66c66e)(ai + 0x20, mover, fifo[i].pos, (int)fifo[i].source);
    }
}

void gp_maq_entry(void);
__asm__(".text\n.globl _gp_maq_entry\n_gp_maq_entry:\n"
"  pushl %ecx\n  call _gp_maq_run\n  popl %ecx\n"
"  pushl %ebp\n  movl %esp, %ebp\n  subl $0x4c, %esp\n  jmp *_gp_maq_cont\n");

int gp_patch_moveawayqueue(void)
{
    static const uint8_t call[] = {0xe8,0x5e,0x71,0xf7,0xff}, head6[] = {0x55, 0x8b,0xec, 0x83,0xec,0x4c};
    gp_site s[5];
    gp_site_hash(&s[0], 0x6f53af, 0x16a, GP_FNV_6F53AF);      /* the callback whose order is redirected */
    gp_site_hash(&s[1], 0x66c66e, 0x40, GP_FNV_66C66E);       /* aiMoveAwayFromUnit (its start) */
    gp_site_hash(&s[2], 0x449681, 0x25, GP_FNV_449681);       /* findObjectByID */
    gp_site_init(&s[3], 0x6f550b, call, 5);
    gp_rel32(&s[3], 0, 0xe8, (void *)gp_maq_order);
    gp_site_init(&s[4], 0x6f2364, head6, 6);
    gp_rel32(&s[4], 0, 0xe9, (void *)gp_maq_entry);
    s[4].repl[5] = 0x90;
    maq_off = gp_va_offset;
    gp_maq_cont = 0x6f236a + gp_va_offset;
    if (!gp_apply("moveawayqueue", s, 5)) return 0;
    gp_log("moveawayqueue: at most %u move-away orders at once per path, the rest %u per queue run", gp_maq_limit, gp_maq_limit);
    return 1;
}

void gp_maq_exit_log(void)
{
    if (gp_maq_stats[0])
        gp_log("exit: moveawayqueue orders %ld, waited %ld, given later %ld, dropped %ld", gp_maq_stats[0],
               gp_maq_stats[1], gp_maq_stats[2], gp_maq_stats[3]);
}
