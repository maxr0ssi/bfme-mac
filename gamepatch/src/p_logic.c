/* Game-logic x87 replacements: installers, counters and the 60 s log line (code in p_logic.S).
 *
 * Why the SSE versions give the same bits: in the game's FPU mode (PC_24, round to nearest) every
 * x87 add/sub/mul/div/sqrt rounds its exact result to a 24-bit significand with the x87's wider
 * exponent range, i.e. exactly like the SSE single operation whenever the result is a normal
 * float (or an exact zero/denormal). The only differences are results that overflow or are
 * inexact below FLT_MIN (MXCSR OE / UE), invalid operations (IE) and which NaN payload
 * propagates; each entry clears the MXCSR flags, and on OE/UE/IE/ZE or a NaN result runs the
 * original x87 instructions on the same inputs. Constants: the originals use 1.0f, 0.5 and 1.0 as
 * doubles, 0.1f, 0.0f; a double 0.5/1.0 times or plus a 24-bit value rounds like the float one.
 *
 *   mat2quat  0xb2bd10 Matrix3D -> Quaternion (Build_Quaternion; 21 call sites in 12 functions:
 *             HAnim / HTree blending code and 0xb27c80). tr = m00+m11+m22 (SSE in the original);
 *             tr > 0: s = sqrt(tr+1), w = s*0.5, (x,y,z) = (m21-m12, m02-m20, m10-m01) * (0.5/s);
 *             else the classic largest-diagonal branch: s = sqrt(m_ii - (m_kk+m_jj) + 1),
 *             q_i = s*0.5, f = s ? 0.5/s : s, then the original's own SSE code for the rest.
 *   distcalc  PartitionManager distance procs (table 0xdbdaf8, called per candidate object in
 *             iterateObjects 0xa3bdb0, 0xa3c5xx): 0xa3a7a0 centre 2D = dx*dx + dy*dy and
 *             0xa3ae50 bounding circle 2D: d = sqrt(dx*dx+dy*dy) - radius, returns d*d or -(d*d).
 *             Results are returned in st0 (not stored), so a value outside the float range would
 *             stay finite in x87: that is the overflow the flags catch.
 *   bsphere   0x59bc50 (a render object's bounding sphere from its box, virtual) computes the
 *             radius^2 in SSE and only the root in x87 (flds/fsqrt/fstps, 9 bytes at 0x59bcb9):
 *             sqrtss is exact for all 2^32 inputs (t_logic [3]).
 *   worldcell 0x6e8ce6 (81 call sites in the pathfinder): cell = (int)floor(v * 0.1f [+ 0.5f])
 *             via x87 multiply, msvcr71 floor (a double), fstp float, fistp. floor is exact and
 *             the float/fistp steps are exact for integral values, so roundss(floor) +
 *             cvtss2si gives the same ints and the same float in the argument slot.
 *   ftol2     0xa3cfa4, the CRT's x87 _ftol2: integer emulation in p_ftol2.S.
 * Tests: t_logic.c, t_ftol2.c (every entry against the original bytes of the exe on disk). */
#include "gp_logic.h"
#include <stdio.h>
#include <cpuid.h>

DWORD gp_lm_period_ms = 60000;
extern volatile LONG gp_lm_slots[16][16];   /* p_logic.S: per line [0..4] calls, [5..9] x87 runs */

LONG gp_lm_count(int x87, int k)
{
    LONG n = 0;
    for (int i = 0; i < 16; i++) n += gp_lm_slots[i][5 * x87 + k];
    return n;
}
static DWORD last_tick;
static LONG last_calls[LM_N], last_x87[LM_N], busy;
static int on_m2q, on_dc, on_bsph, on_wcell, on_ftol2;
static LONG last_ftol2[2];
static LONG ftol2_count(int x87)
{
    LONG n = 0;
    for (int i = 0; i < 16; i++) n += gp_ftol2_calls[i][x87];
    return n;
}

static void start_clock(void) { if (!last_tick) last_tick = GetTickCount() | 1; }

__attribute__((force_align_arg_pointer)) void gp_lm_periodic(void)
{
    DWORD t = GetTickCount();
    if (!last_tick || t - last_tick < gp_lm_period_ms) return;
    if (InterlockedExchange(&busy, 1)) return;
    LONG c[LM_N], x[LM_N];
    for (int i = 0; i < LM_N; i++) {
        c[i] = gp_lm_count(0, i) - last_calls[i]; x[i] = gp_lm_count(1, i) - last_x87[i];
        last_calls[i] += c[i]; last_x87[i] += x[i];
    }
    LONG fc = ftol2_count(0) - last_ftol2[0], fx = ftol2_count(1) - last_ftol2[1];
    last_ftol2[0] += fc; last_ftol2[1] += fx;
    char a[LM_N + 1][48];
    #define PART(k, on, i) (on ? (snprintf(a[k], sizeof a[k], "%ld (%ld x87)", c[i], x[i]), a[k]) : "off")
    gp_log("logicmath: last %lu s, calls: mat2quat %s | distcalc centre %s, circle %s | bsphere %s | "
           "worldcell %s | ftol2 %s", (t - last_tick) / 1000, PART(0, on_m2q, LM_M2Q), PART(1, on_dc, LM_DCC),
           PART(2, on_dc, LM_DCB), PART(3, on_bsph, LM_BSPH), PART(4, on_wcell, LM_WCELL),
           on_ftol2 ? (snprintf(a[LM_N], sizeof a[LM_N], "%ld (%ld x87)", fc, fx), a[LM_N]) : "off");
    #undef PART
    last_tick = t;
    InterlockedExchange(&busy, 0);
}

void gp_logic_exit_log(void)
{
    if (!(on_m2q | on_dc | on_bsph | on_wcell | on_ftol2)) return;
    gp_log("exit: logicmath calls (x87 fallbacks): mat2quat %ld (%ld), distcalc centre %ld (%ld), circle "
           "%ld (%ld), bsphere %ld (%ld), worldcell %ld (%ld), ftol2 %ld (%ld)", gp_lm_count(0, LM_M2Q), gp_lm_count(1, LM_M2Q),
           gp_lm_count(0, LM_DCC), gp_lm_count(1, LM_DCC), gp_lm_count(0, LM_DCB), gp_lm_count(1, LM_DCB),
           gp_lm_count(0, LM_BSPH), gp_lm_count(1, LM_BSPH), gp_lm_count(0, LM_WCELL), gp_lm_count(1, LM_WCELL),
           ftol2_count(0), ftol2_count(1));
}

/* a check-only site for a constant the original reads */
static void konst(gp_site *s, uint32_t va, const uint8_t *bytes, uint32_t n)
{
    gp_site_init(s, va, bytes, n);
    s->wlen = 0;
}
static const uint8_t k_one_f[] = {0x00,0x00,0x80,0x3f}, k_zero_f[] = {0,0,0,0},
    k_half_f[] = {0x00,0x00,0x00,0x3f}, k_tenth_f[] = {0xcd,0xcc,0xcc,0x3d},
    k_half_d[] = {0,0,0,0,0,0,0xe0,0x3f}, k_one_d[] = {0,0,0,0,0,0,0xf0,0x3f}, k_zero_d[8] = {0};

/* ---- mat2quat ---------------------------------------------------------------------------- */
int gp_patch_mat2quat(void)
{
    static const uint8_t head[] = {0x83,0xec,0x10, 0x8b,0x4c,0x24,0x18};   /* sub esp,16; mov ecx,[esp+0x18] */
    static const uint8_t next[] = {1,0,0,0, 2,0,0,0, 0,0,0,0};
    gp_site s[8];
    gp_site_hash(&s[0], 0xb2bd10, 0x168, GP_FNV_B2BD10);
    konst(&s[1], 0xc1b594, k_zero_f, 4);
    konst(&s[2], 0xbd1908, k_one_f, 4);
    konst(&s[3], 0xbd86a0, k_half_d, 8);
    konst(&s[4], 0xbd2c98, k_one_d, 8);
    konst(&s[5], 0xbd1c50, k_zero_d, 8);
    konst(&s[6], 0xdc39b8, next, sizeof next);
    gp_site_init(&s[7], 0xb2bd10, head, sizeof head);
    gp_rel32(&s[7], 0, 0xe9, (void *)gp_m2q);
    s[7].repl[5] = 0x90; s[7].repl[6] = 0x90;
    gp_m2q_cont = 0xb2bd17 + gp_va_offset;
    if (!gp_apply("mat2quat", s, 8)) return 0;
    on_m2q = 1; start_clock();
    return 1;
}

/* ---- distcalc ---------------------------------------------------------------------------- */
int gp_patch_distcalc(void)
{
    static const uint8_t hc[] = {0x8b,0x4c,0x24,0x08, 0x8b,0x01};             /* mov ecx,[esp+8]; mov eax,[ecx] */
    static const uint8_t hb[] = {0x56, 0x8b,0x74,0x24,0x0c, 0x8b,0x06};       /* push esi; mov esi,[esp+0xc]; mov eax,[esi] */
    gp_site s[5];
    gp_site_hash(&s[0], 0xa3a7a0, 0x26, GP_FNV_A3A7A0);
    gp_site_hash(&s[1], 0xa3ae50, 0x53, GP_FNV_A3AE50);
    konst(&s[2], 0xc1b594, k_zero_f, 4);
    gp_site_init(&s[3], 0xa3a7a0, hc, sizeof hc);
    gp_rel32(&s[3], 0, 0xe9, (void *)gp_dc_center2d);
    s[3].repl[5] = 0x90;
    gp_site_init(&s[4], 0xa3ae50, hb, sizeof hb);
    gp_rel32(&s[4], 0, 0xe9, (void *)gp_dc_bound2d);
    s[4].repl[5] = 0x90; s[4].repl[6] = 0x90;
    gp_dcc_cont = 0xa3a7a6 + gp_va_offset; gp_dcc_x87 = 0xa3a7a9 + gp_va_offset;
    gp_dcb_cont = 0xa3ae57 + gp_va_offset;
    gp_dcb_tail = 0xa3ae82 + gp_va_offset;
    if (!gp_apply("distcalc", s, 5)) return 0;
    on_dc = 1; start_clock();
    return 1;
}

/* ---- bsphere ----------------------------------------------------------------------------- */
int gp_patch_bsphere(void)
{
    static const uint8_t code[] = {0xd9,0x44,0x24,0x20, 0xd9,0xfa, 0xd9,0x1c,0x24}; /* flds [esp+0x20]; fsqrt; fstps [esp] */
    gp_site s[2];
    gp_site_hash(&s[0], 0x59bc50, 0x82, GP_FNV_59BC50);
    gp_site_init(&s[1], 0x59bcb9, code, sizeof code);
    gp_rel32(&s[1], 0, 0xe8, (void *)gp_bsph);
    s[1].repl[5] = 0x0f; s[1].repl[6] = 0x1f; s[1].repl[7] = 0x40; s[1].repl[8] = 0x00;  /* 4-byte nop */
    if (!gp_apply("bsphere", s, 2)) return 0;
    on_bsph = 1; start_clock();
    return 1;
}

/* ---- worldcell --------------------------------------------------------------------------- */
int gp_patch_worldcell(void)
{
    static const uint8_t head[] = {0x55, 0x8b,0xec, 0x51, 0x80,0x7d,0x0c,0x00};  /* push ebp; mov ebp,esp; push ecx; cmp byte [ebp+0xc],0 */
    unsigned a, b, c, d;
    if (!__get_cpuid(1, &a, &b, &c, &d) || !(c & bit_SSE4_1)) {
        gp_log("worldcell: CPU has no SSE4.1; patch skipped");
        return 0;
    }
    gp_site s[4];
    gp_site_hash(&s[0], 0x6e8ce6, 0xa2, GP_FNV_6E8CE6);
    konst(&s[1], 0xbd83d4, k_tenth_f, 4);
    konst(&s[2], 0xbd869c, k_half_f, 4);
    gp_site_init(&s[3], 0x6e8ce6, head, sizeof head);
    gp_rel32(&s[3], 0, 0xe9, (void *)gp_wcell);
    s[3].repl[5] = s[3].repl[6] = s[3].repl[7] = 0x90;
    gp_wcell_cont = 0x6e8cee + gp_va_offset;
    if (!gp_apply("worldcell", s, 4)) return 0;
    on_wcell = 1; start_clock();
    return 1;
}

/* ---- ftol2 (code in p_ftol2.S) --------------------------------------------------------------- */
int gp_patch_ftol2(void)
{
    static const uint8_t head[] = {0x55, 0x8b,0xec, 0x83,0xec,0x20};           /* push ebp; mov ebp,esp; sub esp,0x20 */
    gp_site s[2];
    gp_site_hash(&s[0], 0xa3cfa4, 0x75, GP_FNV_A3CFA4);
    gp_site_init(&s[1], 0xa3cfa4, head, sizeof head);
    gp_rel32(&s[1], 0, 0xe9, (void *)gp_ftol2);
    s[1].repl[5] = 0x90;
    gp_ftol2_cont = 0xa3cfaa + gp_va_offset;
    if (!gp_apply("ftol2", s, 2)) return 0;
    on_ftol2 = 1; start_clock();
    return 1;
}
