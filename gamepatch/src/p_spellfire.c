/* firecircle: the weather spells' fire-damping circle without the 260,000 terrain-height queries.
 *
 * Angmar's Freezing Rain (SpellBookFreezingRain) and Blizzard (SpellBookFreezingBlizzard) leave a
 * caster object that fires a weapon every 2 s for the spell's 150 s (ConstantFreezingRain,
 * ConstantBlizzard, weapon.ini). Besides the debuff, the weapon has a FireLogicNugget
 * DECREASE_BURN_RATE with Radius 999999: "damp every fire on the map". The nugget (0x9120e6, type 1)
 * calls the fire logic's circle 0x6878d7(pos, radius, amount, flag 0), a midpoint filled circle in
 * fire cells of 10 units: r = 100,000 cells, so 2r + 1 = 200,001 calls of the row function 0x687059
 * (x0, x1, y, amount, flag), one per row from cy + r down to cy - r. All but ~510 rows are off the
 * map and return at once (after an SEH frame); each row on the map is clamped to the map and walks
 * all its ~510 cells. With flag 0, every cell first asks TheTerrainLogic->isUnderwater (vt+0x4c,
 * 0x67dae6: ground height 0x462355 -> 0x46a575 with four CRT floors, then the water areas' polygons
 * 0x681f0a); only then does it look at the cell's burn rate, and with amount <= 0 a cell whose rate is
 * 0 is left as it is whether it is under water or not (under water: rate = 0, already 0; on land:
 * `rate <= 0` -> next cell). So one shot is ~260,000 terrain queries for the few cells that burn.
 * The 2026-10-05 8-player session (logs/sessions/20261005-182416) shows it: a stall of 160-190 ms
 * every 10 logic frames (2 s) for 150 s from logic frame ~14286, 50-90 % of each stall's samples
 * under 0x6878d7 (isUnderwater, 0x46a575, 0x687059 innermost). docs/PERFORMANCE.md §24.
 *
 * Two changes, both leaving every cell, flag and set operation exactly as before:
 *  - 0x6870cf (the cell loop's `cmpb $0,flag; je water`): with flag 0, amount <= 0 and the cell's
 *    rate 0, go to the next cell without the terrain query (it changes nothing there, see above;
 *    isUnderwater and its callees write only their NULL out-parameters' targets, read statically).
 *    Any other cell takes the original path.
 *  - the circle's two row calls (0x6879a5, 0x6879c1): a row the row function would reject at its
 *    first four tests (y < 0, y >= rows, x0 >= columns, x1 < 0, signed, before it touches anything)
 *    is not called. The circle's own loop is unchanged, so the rows that are called get the same
 *    x0, x1 in the same order.
 * Deterministic and LAN-safe even against players without it (no logic value changes).
 * Test: t_spellfire (both versions run the exe's own 0x6878d7 / 0x687059 on the same fire grids). */
#include "gp.h"
#include "p_spell.h"

#define GP_FNV_687059 0xfc60828f99fc5229ull   /* fire logic row function, 0x18e bytes */
#define GP_FNV_6878D7 0x5c3040dc85cb766full   /* fire logic filled circle, 0x116 bytes */

uint32_t gp_fc_row, gp_fc_flagpath, gp_fc_water, gp_fc_next;   /* 0x687059, 0x6870d5, 0x6870e7, 0x6870dc */
volatile LONG gp_fc_stats[3];            /* rows skipped, cells skipped, rows called */

__asm__(".text\n"
/* in 0x687059's cell loop: esi = the cell (rate u16 at +6), ebp = its frame (amount +0x14, flag +0x18) */
".globl _gp_fc_cell\n_gp_fc_cell:\n"
"  cmpb $0, 0x18(%ebp)\n  jne 1f\n"
"  cmpl $0, 0x14(%ebp)\n  jg 2f\n"
"  cmpw $0, 6(%esi)\n  jne 2f\n"
"  incl _gp_fc_stats+4\n"
"  jmp *_gp_fc_next\n"
"1:jmp *_gp_fc_flagpath\n"
"2:jmp *_gp_fc_water\n"
/* the circle's row calls: thiscall (ecx = the fire logic: columns +0x78, rows +0x7c), x0, x1, y,
 * amount, flag on the stack, callee pops 0x14 */
".globl _gp_fc_rowcall\n_gp_fc_rowcall:\n"
"  movl 12(%esp), %eax\n"
"  testl %eax, %eax\n  jl 1f\n"
"  cmpl 0x7c(%ecx), %eax\n  jge 1f\n"
"  movl 4(%esp), %eax\n  cmpl 0x78(%ecx), %eax\n  jge 1f\n"
"  cmpl $0, 8(%esp)\n  jl 1f\n"
"  incl _gp_fc_stats+8\n"
"  jmp *_gp_fc_row\n"
"1:incl _gp_fc_stats\n"
"  ret $0x14\n");

int gp_patch_firecircle(void)
{
    static const uint8_t cell[] = {0x80, 0x7d, 0x18, 0x00, 0x74, 0x12};    /* cmpb $0,0x18(%ebp); je 0x6870e7 */
    static const uint8_t row1[] = {0xe8, 0xaf, 0xf6, 0xff, 0xff};          /* 0x6879a5: call 0x687059 */
    static const uint8_t row2[] = {0xe8, 0x93, 0xf6, 0xff, 0xff};          /* 0x6879c1: call 0x687059 */
    gp_site s[5];
    gp_site_hash(&s[0], 0x687059, 0x18e, GP_FNV_687059);
    gp_site_hash(&s[1], 0x6878d7, 0x116, GP_FNV_6878D7);
    gp_site_init(&s[2], 0x6870cf, cell, 6);
    gp_rel32(&s[2], 0, 0xe9, (void *)gp_fc_cell);
    s[2].repl[5] = 0x90;
    gp_site_init(&s[3], 0x6879a5, row1, 5);
    gp_rel32(&s[3], 0, 0xe8, (void *)gp_fc_rowcall);
    gp_site_init(&s[4], 0x6879c1, row2, 5);
    gp_rel32(&s[4], 0, 0xe8, (void *)gp_fc_rowcall);
    gp_fc_row = 0x687059 + gp_va_offset;
    gp_fc_flagpath = 0x6870d5 + gp_va_offset;
    gp_fc_water = 0x6870e7 + gp_va_offset;
    gp_fc_next = 0x6870dc + gp_va_offset;
    if (!gp_apply("firecircle", s, 5)) return 0;
    gp_log("firecircle: fire-logic circles skip the off-map rows and, when damping, the terrain query of cells that do not burn");
    return 1;
}

void gp_fc_exit_log(void)
{
    if (gp_fc_stats[0] || gp_fc_stats[1] || gp_fc_stats[2])
        gp_log("exit: firecircle %ld off-map rows not called, %ld rows called, %ld non-burning cells without a terrain query",
               gp_fc_stats[0], gp_fc_stats[2], gp_fc_stats[1]);
}
