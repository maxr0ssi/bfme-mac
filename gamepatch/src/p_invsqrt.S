/* invsqrt: SSE replacement for the game's fast inverse square root at 0x441c56 (219 callers), and
 * for the x87 "multiply the vector by it" tails of its two hottest callers.
 *
 * Original 0x441c56 (x87, stdcall float x -> st0):
 *   y  = float_bits((0xbe6eb508 - bits(x)) >> 1);  xh = float_bits(bits(x) - 0x800000)  (= x/2)
 *   A = (y*y)*xh; t1 = 1.5-A; B = (A*t1)*t1; y1 = y*t1; t2 = 1.5-B; C = (B*t2)*t2; y2 = y1*t2
 *   return y2 * (1.5 - C)
 * The game runs the x87 unit at 24-bit precision, round to nearest (_controlfp(_PC_24|_RC_NEAR)
 * at 0x440809). In that mode each x87 operation rounds its exact result to a 24-bit significand
 * with an extended exponent range, which is IEEE single rounding whenever the result is a normal
 * float. So the same operations in SSE single precision give the same value as long as nothing
 * leaves the normal float range; the input range [LO, HI] that guarantees that is checked over
 * all 2^32 inputs by gamepatch/tests/t_invsqrt.c (80-bit results compared bit for bit).
 *
 * Fast path only when: x87 control word PC=24, RC=nearest, all exceptions masked; MXCSR
 * RC=nearest, all exceptions masked, no FTZ/DAZ; LO <= bits(x) <= HI. Anything else runs the
 * original x87 code. Registers as the original: only eax and flags change (xmm0-2 restored).
 *
 * Tails (callers that do v[i] = fl(r * v[i]) in x87 right after the call): 0x4f1710 (triangle
 * normal, 3 floats at esi, len^2 at [ebp+8]) and 0xb2b875 (quaternion nlerp, 4 floats at esi,
 * len^2 in eax). The products are done in SSE with the MXCSR flags cleared; if one overflowed or
 * underflowed they are redone in x87 from the same (exact) r, else the original sequence runs. */
#include "isqrt_range.h"
        .intel_syntax noprefix
        .set LO, GP_ISQRT_LO
        .set HI, GP_ISQRT_HI

        .data
        .balign 4
        .globl _gp_invsqrt_cont, _gp_invsqrt_fn
_gp_invsqrt_cont: .long 0x00441c5b    /* original + 5, after the replaced mov eax, imm32 */
_gp_invsqrt_fn:   .long 0x00441c56    /* what the tails call on their x87 path */

        .section .rdata,"dr"
        .balign 4
c15:    .long 0x3fc00000               /* 1.5f */

        .text
/* ISQRT eax=bits(x) (in range), [mem]=scratch dword -> xmm0 = result; uses xmm1, xmm2, eax */
.macro ISQRT scratch
        mov     dword ptr \scratch, eax
        sub     dword ptr \scratch, 0x800000   /* xh */
        neg     eax
        add     eax, 0xbe6eb508
        shr     eax, 1
        movd    xmm0, eax               /* y */
        movaps  xmm1, xmm0
        mulss   xmm1, xmm1              /* y*y */
        mulss   xmm1, dword ptr \scratch /* A = y*y*xh */
        movss   xmm2, dword ptr [c15]
        subss   xmm2, xmm1              /* t1 */
        mulss   xmm1, xmm2
        mulss   xmm1, xmm2              /* B */
        mulss   xmm0, xmm2              /* y1 */
        movss   xmm2, dword ptr [c15]
        subss   xmm2, xmm1              /* t2 */
        mulss   xmm1, xmm2
        mulss   xmm0, xmm2              /* y2 */
        mulss   xmm1, xmm2              /* C */
        movss   xmm2, dword ptr [c15]
        subss   xmm2, xmm1              /* t3 */
        mulss   xmm0, xmm2              /* y3 */
.endm

/* MODES scratch, fail: jump to fail unless x87 and SSE are in the game's mode. Uses eax. */
.macro MODES scratch, fail
        fnstcw  word ptr \scratch
        movzx   eax, word ptr \scratch
        and     eax, 0x0f3f
        cmp     eax, 0x003f             /* PC=24, RC=near, all exceptions masked */
        jne     \fail
        stmxcsr dword ptr \scratch
        mov     eax, dword ptr \scratch
        and     eax, 0xffc0
        cmp     eax, 0x1f80             /* RC=near, all masked, no FTZ/DAZ */
        jne     \fail
.endm

        .globl _gp_invsqrt
        .balign 16
_gp_invsqrt:
        sub     esp, 56                 /* [0] scratch  [4] result  [8..55] xmm0-2 */
        MODES   [esp], 1f
        mov     eax, dword ptr [esp+60]
        sub     eax, LO
        cmp     eax, HI - LO
        ja      1f
        movups  [esp+8], xmm0
        movups  [esp+24], xmm1
        movups  [esp+40], xmm2
        mov     eax, dword ptr [esp+60]
        ISQRT   [esp+60]                /* xh in the argument slot and eax = bits(y), as the original */
        movss   dword ptr [esp+4], xmm0
        movups  xmm0, [esp+8]
        movups  xmm1, [esp+24]
        movups  xmm2, [esp+40]
        fld     dword ptr [esp+4]
        add     esp, 56
        ret     4
1:      add     esp, 56
        mov     eax, 0xbe6eb508         /* the instruction the jmp replaced */
        jmp     dword ptr [_gp_invsqrt_cont]

/* norm_fast: eax = bits(len^2), ecx = float v[n], [esp+4] = n (3 or 4; caller pops).
 * v[i] = fl(invsqrt(len^2) * v[i]). Returns eax = 1 when done, 0 when the caller must run its
 * original x87 code (nothing written). Changes eax, ecx, xmm0-4 and flags only: both call sites'
 * functions change those themselves, and 0xb2b720 leaves edx and xmm5-7 alone. */
        .balign 16
norm_fast:
        sub     esp, 16                 /* [0] scratch  [4] saved mxcsr  [8] work  [12] xh */
        push    eax
        MODES   [esp+4], 8f
        pop     eax
        cmp     eax, LO
        jb      9f
        cmp     eax, HI
        ja      9f
        ISQRT   [esp+12]                /* xmm0 = r, exactly the x87 result */
        stmxcsr dword ptr [esp+4]
        mov     eax, dword ptr [esp+4]
        and     eax, 0xffffffc0
        mov     dword ptr [esp+8], eax
        ldmxcsr dword ptr [esp+8]       /* flags cleared */
        movss   xmm1, dword ptr [ecx]
        mulss   xmm1, xmm0
        movss   xmm2, dword ptr [ecx+4]
        mulss   xmm2, xmm0
        movss   xmm3, dword ptr [ecx+8]
        mulss   xmm3, xmm0
        cmp     dword ptr [esp+20], 4
        jne     2f
        movss   xmm4, dword ptr [ecx+12]
        mulss   xmm4, xmm0
2:      stmxcsr dword ptr [esp+8]
        ldmxcsr dword ptr [esp+4]
        test    byte ptr [esp+8], 0x1d  /* IE ZE OE UE: a product left the float range */
        jnz     3f
        movss   dword ptr [ecx], xmm1
        movss   dword ptr [ecx+4], xmm2
        movss   dword ptr [ecx+8], xmm3
        cmp     dword ptr [esp+20], 4
        jne     4f
        movss   dword ptr [ecx+12], xmm4
        jmp     4f
3:      movss   dword ptr [esp+8], xmm0 /* x87 products from the same r, as the original */
        fld     dword ptr [esp+8]
        fld     st(0)
        fmul    dword ptr [ecx]
        fstp    dword ptr [ecx]
        fld     st(0)
        fmul    dword ptr [ecx+4]
        fstp    dword ptr [ecx+4]
        cmp     dword ptr [esp+20], 4
        jne     5f
        fld     st(0)
        fmul    dword ptr [ecx+8]
        fstp    dword ptr [ecx+8]
        fmul    dword ptr [ecx+12]
        fstp    dword ptr [ecx+12]
        jmp     4f
5:      fmul    dword ptr [ecx+8]
        fstp    dword ptr [ecx+8]
4:      mov     eax, 1
        add     esp, 16
        ret
8:      pop     eax
9:      xor     eax, eax
        add     esp, 16
        ret

/* 0x4f1710: call here, then jmp 0x4f1730. Original: fld [ebp+8]; push ecx; fstp [esp];
 * call 0x441c56; fld st0; fmul [esi]; fstp [esi]; fld st0; fmul [esi+4]; fstp [esi+4];
 * fmul [esi+8]; fstp [esi+8] */
        .globl _gp_norm_4f1710
        .balign 16
_gp_norm_4f1710:
        mov     eax, dword ptr [ebp+8]
        mov     ecx, esi
        push    3
        call    norm_fast
        add     esp, 4
        test    eax, eax
        jz      1f
        ret
1:      fld     dword ptr [ebp+8]
        push    ecx
        fstp    dword ptr [esp]
        call    dword ptr [_gp_invsqrt_fn]
        fld     st(0)
        fmul    dword ptr [esi]
        fstp    dword ptr [esi]
        fld     st(0)
        fmul    dword ptr [esi+4]
        fstp    dword ptr [esi+4]
        fmul    dword ptr [esi+8]
        fstp    dword ptr [esi+8]
        ret

/* 0xb2b875 (after mov eax, [esp+8]): call here, then jmp 0xb2b897. Original: push eax;
 * call 0x441c56; then fld st0 / fmul / fstp for [esi], [esi+4], [esi+8]; fmul/fstp [esi+12] */
        .globl _gp_norm_b2b875
        .balign 16
_gp_norm_b2b875:
        push    eax
        mov     ecx, esi
        push    4
        call    norm_fast
        add     esp, 4
        test    eax, eax
        pop     eax
        jz      1f
        ret
1:      push    eax
        call    dword ptr [_gp_invsqrt_fn]
        fld     st(0)
        fmul    dword ptr [esi]
        fstp    dword ptr [esi]
        fld     st(0)
        fmul    dword ptr [esi+4]
        fstp    dword ptr [esi+4]
        fld     st(0)
        fmul    dword ptr [esi+8]
        fstp    dword ptr [esi+8]
        fmul    dword ptr [esi+12]
        fstp    dword ptr [esi+12]
        ret
