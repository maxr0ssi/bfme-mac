/* flattenlight: one terrain relight per building placement instead of one per lowered cell.
 *
 * When a structure is placed (a worker's or builder's AI state creates it; also 0x8ad6a4),
 * TerrainLogic::flattenTerrain 0x684cba levels the ground under its footprint: for every footprint
 * cell it calls TheTerrainVisual->setRawMapHeight (vt+0x88, 0x49172d) on the cell and its 8
 * neighbours. setRawMapHeight lowers a cell that is higher than the target and then calls the
 * terrain render object's staticLightingChanged (vt+0x224, 0x4e0b69 -> 0x467bf9), which relights
 * every road vertex on the map (W3DRoadBuffer::updateLighting 0x4d4297: per vertex the terrain
 * normal, the global lights and every light in the scene's light list, 0x46acd7 / 0x468cc0) and
 * marks the terrain for a full rebuild. A 10x10 footprint on a hilly map lowers 30-100 cells, so
 * one placement relit all roads 30-100 times in one logic phase: the 0.2-1.4 s freezes of
 * docs/PERFORMANCE.md §22.
 *
 * Each relight recomputes every road vertex from the current heights and lights and overwrites it;
 * the rest of staticLightingChanged sets flags and releases the terrain tiles' buffers (a second
 * release finds nothing). Nothing in flattenTerrain's loop reads what a relight writes, and nothing
 * draws until it returns. So only the last relight's result is ever seen. Here the two calls of
 * flattenTerrain (0x88d5ab, 0x8ad801) go through gp_fl_flatten, and setRawMapHeight's relight call
 * (0x491772) through gp_fl_relight: inside flattenTerrain the relight is noted, and done once, with
 * the same argument, when flattenTerrain returns, i.e. with the same heights and lights as the
 * original's last one. Outside flattenTerrain it runs at once, as before. Client side only: no game
 * logic value changes (the heights are set exactly as before). Test: t_flatlight. */
#include "gp_render.h"

uint32_t gp_fl_fn;                       /* flattenTerrain 0x684cba (+ test offset) */
volatile LONG gp_fl_depth;               /* > 0 while flattenTerrain runs */
void *volatile gp_fl_obj;                /* the render object whose relight is pending, or NULL */
volatile LONG gp_fl_arg;                 /* its argument (always 0 from setRawMapHeight) */
volatile LONG gp_fl_stats[4];            /* flattens, relights noted, relights done at the end, run at once */

/* setRawMapHeight's `call *0x224(%eax)` (ecx = the render object, the argument pushed) */
__asm__(".text\n.globl _gp_fl_relight\n_gp_fl_relight:\n"
"  cmpl $0, _gp_fl_depth\n  je 2f\n"
"  movl _gp_fl_obj, %eax\n  testl %eax, %eax\n  jz 1f\n"
"  cmpl %eax, %ecx\n  jne 2f\n"                 /* another object (never in the game): at once */
"  movl 4(%esp), %eax\n  cmpl %eax, _gp_fl_arg\n  jne 2f\n"
"  incl _gp_fl_stats+4\n  ret $4\n"
"1:movl %ecx, _gp_fl_obj\n  movl 4(%esp), %eax\n  movl %eax, _gp_fl_arg\n"
"  incl _gp_fl_stats+4\n  ret $4\n"
"2:incl _gp_fl_stats+12\n  movl (%ecx), %eax\n  jmp *0x224(%eax)\n"
/* the call sites of flattenTerrain: thiscall (ecx = TheTerrainLogic, the object on the stack) */
".globl _gp_fl_flatten\n_gp_fl_flatten:\n"
"  incl _gp_fl_stats\n  incl _gp_fl_depth\n"
"  pushl 4(%esp)\n  call *_gp_fl_fn\n"
"  decl _gp_fl_depth\n  jnz 1f\n"
"  movl _gp_fl_obj, %ecx\n  testl %ecx, %ecx\n  jz 1f\n"
"  pushl %eax\n  movl $0, _gp_fl_obj\n  incl _gp_fl_stats+8\n"
"  pushl _gp_fl_arg\n  movl (%ecx), %eax\n  call *0x224(%eax)\n"
"  popl %eax\n"
"1:ret $4\n");

int gp_patch_flattenlight(void)
{
    static const uint8_t vcall[] = {0xff, 0x90, 0x24, 0x02, 0x00, 0x00};      /* call *0x224(%eax) */
    static const uint8_t site1[] = {0xe8, 0x0a, 0x77, 0xdf, 0xff};            /* 0x88d5ab: call 0x684cba */
    static const uint8_t site2[] = {0xe8, 0xb4, 0x74, 0xdd, 0xff};            /* 0x8ad801: call 0x684cba */
    gp_site s[10];
    gp_site_hash(&s[0], 0x49172d, 0x51, GP_FNV_49172D);   /* setRawMapHeight */
    gp_site_hash(&s[1], 0x684cba, 0x537, GP_FNV_684CBA);  /* flattenTerrain: nothing but heights in its loop */
    gp_site_hash(&s[2], 0x4e0b69, 0xb1, GP_FNV_4E0B69);   /* staticLightingChanged: base + tiles */
    gp_site_hash(&s[3], 0x467bf9, 0x29, GP_FNV_467BF9);   /* base: flags, roads */
    gp_site_hash(&s[4], 0x4d4297, 0x31, GP_FNV_4D4297);   /* W3DRoadBuffer::updateLighting */
    gp_site_hash(&s[5], 0x4d3e5f, 0xbb, GP_FNV_4D3E5F);   /* RoadSegment::updateSegLighting */
    gp_site_hash(&s[6], 0x511c06, 0x38, GP_FNV_511C06);   /* a tile's buffers released */
    gp_site_init(&s[7], 0x491772, vcall, 6);
    gp_rel32(&s[7], 0, 0xe8, (void *)gp_fl_relight);
    s[7].repl[5] = 0x90;
    gp_site_init(&s[8], 0x88d5ab, site1, 5);
    gp_rel32(&s[8], 0, 0xe8, (void *)gp_fl_flatten);
    gp_site_init(&s[9], 0x8ad801, site2, 5);
    gp_rel32(&s[9], 0, 0xe8, (void *)gp_fl_flatten);
    gp_fl_fn = 0x684cba + gp_va_offset;
    if (!gp_apply("flattenlight", s, 10)) return 0;
    gp_log("flattenlight: one terrain relight per flattenTerrain call (at its end) instead of one per lowered cell");
    return 1;
}

void gp_fl_exit_log(void)
{
    if (gp_fl_stats[0] || gp_fl_stats[3])
        gp_log("exit: flattenlight %ld flattens, %ld relights folded into %ld, %ld run at once (outside a flatten)",
               gp_fl_stats[0], gp_fl_stats[1], gp_fl_stats[2], gp_fl_stats[3]);
}
