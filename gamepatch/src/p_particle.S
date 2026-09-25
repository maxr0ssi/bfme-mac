/* particlevtx entry: replaces 0x579da0..0x579e22, the per-vertex ARGB pack inside the particle /
 * point-group vertex write loop (PointGroupClass 0x5793f0; also used by W3D model emitters).
 * Original, per vertex: fstcw; set RC = chop; fldcw; r g b a (floats at [esi], [esi+4], [esi+8]
 * and [ebp-0xf0]; esi = [ebp-0x104]) times 255.0 (the local [ebp-0xf4]) with x87 fmul, fistp
 * each; restore the control word; eax = a<<24 | r<<16 | g<<8 | b.
 *
 * Exactness: with RC = chop the x87 product p = x*255 is rounded toward zero to the precision
 * control (24 bits in the game, >= 24 in any mode), and fistp truncates it. For |p| < 2^24 every
 * integer is representable, so rounding toward zero never crosses one and the result is trunc(p)
 * of the exact product. Here p is formed exactly in double (24 x 8 significant bits) and
 * cvttsd2si truncates it: the same integer, in every x87 and MXCSR mode (the exact product and
 * the truncation do not depend on rounding; DAZ only turns a denormal x into 0, and x87 gives 0
 * for it as well). NaN gives 0x80000000 on both. The loop clamps colours to [0, 1] beforehand
 * (NaN can pass the SSE clamp); anything else (|x| > 1, infinities) or a multiplier other than
 * 255.0 goes to the original x87 code. Every register is left as the original leaves it:
 * eax ecx edx ebx as computed, esi = [ebp-0x104], edi = (CW & 0xc00) - 0xc00 (the original's
 * "did I change the CW" difference), xmm0 = [ebp-0xf0] (the loop loaded it from there; upper
 * lanes zero both ways), xmm1-7 untouched, x87 stack and control word unchanged. */
        .intel_syntax noprefix
        .data
        .balign 8
c255d:  .double 255.0
        .globl _gp_ptclvtx_cont, _gp_ptclvtx_x87, _gp_ptclvtx_fallbacks
        .balign 4
_gp_ptclvtx_cont:
        .long 0x00579e23
_gp_ptclvtx_x87:
        .long 0x00579da9
_gp_ptclvtx_fallbacks:
        .long 0

        .text
/* in range for the exact path: |x| <= 1.0 or NaN; else jump to the x87 original */
.macro GUARD src
        mov     eax, dword ptr \src
        and     eax, 0x7fffffff
        cmp     eax, 0x3f800000
        jbe     1f
        cmp     eax, 0x7f800000
        jbe     9f
1:
.endm
/* reg = trunc(x * 255) */
.macro PACK src, reg
        cvtss2sd xmm0, dword ptr \src
        mulsd   xmm0, qword ptr [c255d]
        cvttsd2si \reg, xmm0
.endm

        .globl _gp_ptclvtx
        .balign 16
_gp_ptclvtx:
        cmp     dword ptr [ebp-0xf4], 0x437f0000   /* the multiplier is 255.0f */
        jne     9f
        mov     esi, dword ptr [ebp-0x104]
        GUARD   [esi]
        GUARD   [esi+4]
        GUARD   [esi+8]
        GUARD   [ebp-0xf0]
        PACK    [ebp-0xf0], ecx        /* alpha */
        PACK    [esi+8], eax           /* blue */
        PACK    [esi+4], edx           /* green */
        PACK    [esi], ebx             /* red */
        shl     ecx, 24
        shl     ebx, 16
        shl     edx, 8
        or      eax, ecx
        or      eax, ebx
        or      eax, edx
        sub     esp, 4
        fnstcw  word ptr [esp]
        movzx   edi, word ptr [esp]
        add     esp, 4
        and     edi, 0xc00
        sub     edi, 0xc00
        movss   xmm0, dword ptr [ebp-0xf0]
        jmp     dword ptr [_gp_ptclvtx_cont]
9:      lock inc dword ptr [_gp_ptclvtx_fallbacks]
        sub     esp, 0x14                          /* the original's first instructions */
        fwait
        fstcw   word ptr [esp+0x10]
        jmp     dword ptr [_gp_ptclvtx_x87]
