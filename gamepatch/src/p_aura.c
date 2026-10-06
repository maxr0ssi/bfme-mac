/* aura3d: the two 3D distance functions of the partition manager's range scans in SSE.
 *
 * The map-wide spell pulses (AttributeModifierNugget 0x90ee10: Darkness, Freezing Rain / Blizzard,
 * Cloud Break, the weather-button disablers, radius 999999 or 1e12) and the auras that scan in 3D ask
 * the range query 0xa39300 -> iterateObjectsInRange 0xa3c4e0 for distance type 3, so every object on
 * the map runs the type's function from the table 0xdbdaf8 (scantree, p_scan.c, calls it through its
 * thunk; 2D types 0-1 it inlines). Types 2 and 3 are only reached through that table (from 0xa3c4e0's
 * walk and getClosestObject 0xa3bdb0); both callers consume st0 only (fsts d2; fcomps r2; fnstsw ax).
 *   0xa3a7d0 centre 3D, cdecl (const Coord3D *q, iface *obj, int): p = obj->getPosition() (vt slot 1);
 *            (dx*dx + dy*dy) + dz*dz in x87 registers. Leaves eax = p, ecx = q, edx the getter's.
 *   0xa3aeb0 bounding sphere 3D: p = getPosition(); dx, dy, dz0 = p - q rounded to floats (all read
 *            before the next call); h = getGeometryInfo()->+0x20 (vt slot 0, then 0xb4e370 `flds
 *            [ecx+0x20]`); dz = float(h + dz0); g = getGeometryInfo() again; d = sqrt((dy*dy + dx*dx)
 *            + dz*dz) - g->+0x14; returns d*d, negated when d < 0 (not for -0 or NaN). Leaves eax = g
 *            with the FPU status word of its sign test in ax, ecx / edx as the last getter left them.
 * The replacements make the same getter calls in the same order with the same ecx, read the same
 * fields at the same points (copies taken where the original reads them), and compute in SSE single
 * precision, which gives the 24-bit x87 result bit for bit as long as no step overflows, underflows
 * inexactly or meets a NaN: MXCSR's flags (invalid, divide, overflow, underflow) are cleared first and
 * tested after, and a NaN or infinite result also counts. Then, and in any FPU mode but the game's
 * (x87 PC_24 / nearest / masked, MXCSR 0x1f80), the original's x87 code runs: from the top before any
 * getter call (other modes), or from the getter results (0xa3a7d0: its own code after the call;
 * 0xa3aeb0: dx, dy, dz by the original's x87 instructions into a frame laid out as its own, then its
 * own tail 0xa3af04). xmm0/xmm1 and MXCSR are restored; registers as the original leaves them, except
 * eax's low 16 bits after 0xa3aeb0's SSE path (the status word: every caller overwrites ax with its
 * own fnstsw before reading it) and the x87 / MXCSR sticky exception flags.
 * Exact, so deterministic across machines and LAN-safe even against a player without it.
 * Test: t_aura (the exe's own functions and range query, original against patched). §27. */
#include "gp.h"
#include "p_aura.h"

#define GP_FNV_A3A7D0 0xaa8d80ef8c2f85c9ull   /* centre 3D, 0x34 bytes */
#define GP_FNV_A3AEB0 0x8e1ac5ace78f9c85ull   /* bounding sphere 3D, 0x91 bytes */

volatile LONG gp_au_stats[4];
uint32_t gp_au_sens;
uint32_t gp_au_c3_cont, gp_au_c3_x87, gp_au_b3_cont, gp_au_b3_tail;  /* 0xa3a7d6, 0xa3a7d9, 0xa3aeb8, 0xa3af04 */
static int on;

__asm__(".intel_syntax noprefix\n"
".text\n"
/* game FPU mode or jump to \\fail; [esp+\\cw] word, [esp+\\mx] dword; uses eax */
".macro AUMODE cw, mx, fail\n"
"  fnstcw word ptr [esp+\\cw]\n  movzx eax, word ptr [esp+\\cw]\n  and eax, 0x0f3f\n  cmp eax, 0x003f\n  jne \\fail\n"
"  stmxcsr dword ptr [esp+\\mx]\n  mov eax, dword ptr [esp+\\mx]\n  and eax, 0xffc0\n  cmp eax, 0x1f80\n  jne \\fail\n"
".endm\n"

/* ---- centre 3D (0xa3a7d0). frame: [0] cw [4] mxcsr [8] work [12] result [16] xmm0 [32] xmm1;
 *      args [esp+52] q, [esp+56] obj */
".globl _gp_au_c3\n.balign 16\n_gp_au_c3:\n"
"  sub esp, 48\n"
"  AUMODE 0, 4, 9f\n"
"  inc dword ptr [_gp_au_stats]\n"
"  mov eax, dword ptr [esp+4]\n  and eax, 0xffffffc0\n  mov dword ptr [esp+8], eax\n"
"  mov ecx, dword ptr [esp+56]\n  mov eax, dword ptr [ecx]\n  call dword ptr [eax+4]\n"   /* getPosition: eax */
"  mov ecx, dword ptr [esp+52]\n"
"  movups [esp+16], xmm0\n  movups [esp+32], xmm1\n"
"  ldmxcsr dword ptr [esp+8]\n"
"  movss xmm0, dword ptr [eax]\n  subss xmm0, dword ptr [ecx]\n  mulss xmm0, xmm0\n"         /* dx*dx */
"  movss xmm1, dword ptr [eax+4]\n  subss xmm1, dword ptr [ecx+4]\n  mulss xmm1, xmm1\n"     /* dy*dy */
"  cmp dword ptr [_gp_au_sens], 0\n  jne 3f\n"
"  addss xmm0, xmm1\n"
"  movss xmm1, dword ptr [eax+8]\n  subss xmm1, dword ptr [ecx+8]\n  mulss xmm1, xmm1\n"     /* dz*dz */
"  addss xmm0, xmm1\n  jmp 4f\n"
"3: movss dword ptr [esp+12], xmm0\n"                                     /* test only: dx2 + (dy2 + dz2) */
"  movss xmm0, dword ptr [eax+8]\n  subss xmm0, dword ptr [ecx+8]\n  mulss xmm0, xmm0\n"
"  addss xmm0, xmm1\n  addss xmm0, dword ptr [esp+12]\n"
"4: movss dword ptr [esp+12], xmm0\n"
"  stmxcsr dword ptr [esp+8]\n  test byte ptr [esp+8], 0x1d\n  jnz 8f\n"   /* IE ZE OE UE */
"  mov ecx, dword ptr [esp+12]\n  and ecx, 0x7f800000\n  cmp ecx, 0x7f800000\n  je 8f\n"  /* inf / NaN */
"  mov ecx, dword ptr [esp+52]\n"
"  ldmxcsr dword ptr [esp+4]\n  movups xmm0, [esp+16]\n  movups xmm1, [esp+32]\n"
"  fld dword ptr [esp+12]\n"
"  add esp, 48\n  ret\n"
"8: ldmxcsr dword ptr [esp+4]\n  movups xmm0, [esp+16]\n  movups xmm1, [esp+32]\n"
"  inc dword ptr [_gp_au_stats+8]\n"
"  add esp, 48\n  jmp dword ptr [_gp_au_c3_x87]\n"                          /* eax = position, as there */
"9: inc dword ptr [_gp_au_stats+8]\n"
"  add esp, 48\n"
"  mov ecx, dword ptr [esp+8]\n  mov eax, dword ptr [ecx]\n"              /* the two instructions replaced */
"  jmp dword ptr [_gp_au_c3_cont]\n"

/* ---- bounding sphere 3D (0xa3aeb0). frame: [0] cw [4] mxcsr [8] work [12] esi [16] px [20] py
 *      [24] pz [28] qx [32] qy [36] qz [40] h [44] g [48] ecx [52] edx [56] result [60] d
 *      [64] xmm0 [80] xmm1 [96..112) the original's own frame for its tail: esi, dx, dy, dz;
 *      args [esp+116] q, [esp+120] obj */
".globl _gp_au_b3\n.balign 16\n_gp_au_b3:\n"
"  sub esp, 112\n"
"  AUMODE 0, 4, 9f\n"
"  inc dword ptr [_gp_au_stats+4]\n"
"  mov eax, dword ptr [esp+4]\n  and eax, 0xffffffc0\n  mov dword ptr [esp+8], eax\n"
"  mov dword ptr [esp+12], esi\n"
"  mov esi, dword ptr [esp+120]\n"
"  mov eax, dword ptr [esi]\n  mov ecx, esi\n  call dword ptr [eax+4]\n"   /* getPosition */
"  mov ecx, dword ptr [eax]\n  mov dword ptr [esp+16], ecx\n"
"  mov ecx, dword ptr [eax+4]\n  mov dword ptr [esp+20], ecx\n"
"  mov ecx, dword ptr [eax+8]\n  mov dword ptr [esp+24], ecx\n"
"  mov eax, dword ptr [esp+116]\n"
"  mov ecx, dword ptr [eax]\n  mov dword ptr [esp+28], ecx\n"
"  mov ecx, dword ptr [eax+4]\n  mov dword ptr [esp+32], ecx\n"
"  mov ecx, dword ptr [eax+8]\n  mov dword ptr [esp+36], ecx\n"
"  mov edx, dword ptr [esi]\n  mov ecx, esi\n  call dword ptr [edx]\n"     /* getGeometryInfo */
"  mov ecx, dword ptr [eax+0x20]\n  mov dword ptr [esp+40], ecx\n"           /* 0xb4e370: flds [ecx+0x20] */
"  mov eax, dword ptr [esi]\n  mov ecx, esi\n  call dword ptr [eax]\n"     /* getGeometryInfo again: eax */
"  mov dword ptr [esp+44], eax\n  mov dword ptr [esp+48], ecx\n  mov dword ptr [esp+52], edx\n"
"  movups [esp+64], xmm0\n  movups [esp+80], xmm1\n"
"  ldmxcsr dword ptr [esp+8]\n"
"  movss xmm0, dword ptr [esp+24]\n  subss xmm0, dword ptr [esp+36]\n  addss xmm0, dword ptr [esp+40]\n"
"  movss dword ptr [esp+56], xmm0\n"                                        /* dz = (pz - qz) + h */
"  movss xmm0, dword ptr [esp+16]\n  subss xmm0, dword ptr [esp+28]\n  mulss xmm0, xmm0\n"  /* dx*dx */
"  movss xmm1, dword ptr [esp+20]\n  subss xmm1, dword ptr [esp+32]\n  mulss xmm1, xmm1\n"  /* dy*dy */
"  cmp dword ptr [_gp_au_sens], 0\n  jne 3f\n"
"  addss xmm1, xmm0\n"
"  movss xmm0, dword ptr [esp+56]\n  mulss xmm0, xmm0\n  addss xmm1, xmm0\n  jmp 4f\n"
"3: movss dword ptr [esp+60], xmm1\n"                                     /* test only: (dz2 + dx2) + dy2 */
"  movss xmm1, dword ptr [esp+56]\n  mulss xmm1, xmm1\n  addss xmm1, xmm0\n  addss xmm1, dword ptr [esp+60]\n"
"4: sqrtss xmm1, xmm1\n"
"  subss xmm1, dword ptr [eax+0x14]\n"                                      /* d */
"  movss dword ptr [esp+60], xmm1\n"
"  mulss xmm1, xmm1\n  movss dword ptr [esp+56], xmm1\n"                   /* d*d */
"  stmxcsr dword ptr [esp+8]\n  test byte ptr [esp+8], 0x1d\n  jnz 8f\n"
"  mov ecx, dword ptr [esp+56]\n  and ecx, 0x7f800000\n  cmp ecx, 0x7f800000\n  je 8f\n"
"  cmp dword ptr [esp+60], 0x80000000\n  jbe 5f\n"                        /* d < 0 (not -0): -(d*d) */
"  xor byte ptr [esp+59], 0x80\n"
"5: ldmxcsr dword ptr [esp+4]\n  movups xmm0, [esp+64]\n  movups xmm1, [esp+80]\n"
"  mov ecx, dword ptr [esp+48]\n  mov edx, dword ptr [esp+52]\n  mov esi, dword ptr [esp+12]\n"
"  fld dword ptr [esp+56]\n"
"  add esp, 112\n  ret\n"
"8: ldmxcsr dword ptr [esp+4]\n  movups xmm0, [esp+64]\n  movups xmm1, [esp+80]\n"
"  inc dword ptr [_gp_au_stats+12]\n"
/* dx, dy, dz as the original's x87 code makes them, into its frame; then its own tail */
"  fld dword ptr [esp+16]\n  fsub dword ptr [esp+28]\n  fstp dword ptr [esp+100]\n"
"  fld dword ptr [esp+20]\n  fsub dword ptr [esp+32]\n  fstp dword ptr [esp+104]\n"
"  fld dword ptr [esp+24]\n  fsub dword ptr [esp+36]\n  fstp dword ptr [esp+108]\n"
"  fld dword ptr [esp+40]\n  fadd dword ptr [esp+108]\n  fstp dword ptr [esp+108]\n"
"  mov eax, dword ptr [esp+12]\n  mov dword ptr [esp+96], eax\n"          /* the esi it pushed */
"  mov esi, eax\n  mov eax, dword ptr [esp+44]\n"
"  mov ecx, dword ptr [esp+48]\n  mov edx, dword ptr [esp+52]\n"
"  add esp, 96\n  jmp dword ptr [_gp_au_b3_tail]\n"                         /* eax = geometry */
"9: inc dword ptr [_gp_au_stats+12]\n"
"  add esp, 112\n"
"  sub esp, 0xc\n  push esi\n  mov esi, dword ptr [esp+0x18]\n"         /* the three instructions replaced */
"  jmp dword ptr [_gp_au_b3_cont]\n"
".att_syntax prefix\n");

void gp_au_exit_log(void)
{
    if (on) gp_log("exit: aura3d distances centre 3D %ld (%ld by the x87 original), bounding sphere 3D %ld (%ld)",
                   gp_au_stats[0], gp_au_stats[2], gp_au_stats[1], gp_au_stats[3]);
}

int gp_patch_aura3d(void)
{
    static const uint8_t hc[] = {0x8b,0x4c,0x24,0x08, 0x8b,0x01};                  /* mov ecx,[esp+8]; mov eax,[ecx] */
    static const uint8_t hb[] = {0x83,0xec,0x0c, 0x56, 0x8b,0x74,0x24,0x18};       /* sub esp,0xc; push esi; mov esi,[esp+0x18] */
    static const uint8_t ht[] = {0xd9,0x41,0x20, 0xc3};                            /* 0xb4e370: flds [ecx+0x20]; ret */
    gp_site s[5];
    gp_site_hash(&s[0], 0xa3a7d0, 0x34, GP_FNV_A3A7D0);
    gp_site_hash(&s[1], 0xa3aeb0, 0x91, GP_FNV_A3AEB0);
    gp_site_init(&s[2], 0xb4e370, ht, sizeof ht); s[2].wlen = 0;
    gp_site_init(&s[3], 0xa3a7d0, hc, sizeof hc);
    gp_rel32(&s[3], 0, 0xe9, (void *)gp_au_c3);
    s[3].repl[5] = 0x90;
    gp_site_init(&s[4], 0xa3aeb0, hb, sizeof hb);
    gp_rel32(&s[4], 0, 0xe9, (void *)gp_au_b3);
    s[4].repl[5] = 0x90; s[4].repl[6] = 0x90; s[4].repl[7] = 0x90;
    gp_au_c3_cont = 0xa3a7d6 + gp_va_offset; gp_au_c3_x87 = 0xa3a7d9 + gp_va_offset;
    gp_au_b3_cont = 0xa3aeb8 + gp_va_offset; gp_au_b3_tail = 0xa3af04 + gp_va_offset;
    if (!gp_apply("aura3d", s, 5)) return 0;
    on = 1;
    return 1;
}
