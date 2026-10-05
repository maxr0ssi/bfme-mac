/* Game-logic math, second batch (installers and the log line in p_lmath2.c; test t_lmath2).
 *
 * crtsqrt: the exe's import of msvcr71!sqrt (IAT 0xbd06a0; the thunk 0xa3cf96 and every direct
 * call go through it) redirected to an SSE version that returns the same bits as Wine's builtin
 * msvcr71 sqrt. Installed only when the msvcr71 loaded is Wine's builtin and an install-time
 * self-test agrees (p_lmath2.c); on Windows the patch stays off.
 *
 * Wine's sqrt (dlls/msvcrt/math.c, i386) for a positive finite non-zero double x: _dclass(x),
 * then fldl x; fsqrt with the x87 precision control left as it is (the game: 24 bits) and the
 * rounding forced to nearest; returns st0. So the result is sqrt(x) rounded once to a 24-bit
 * significand with the x87's wide exponent. Here: sqrtsd (rounded to 53 bits) and then rounded to
 * 24 bits, nearest-even, in integer arithmetic on the double's bits. Rounding twice gives the
 * once-rounded result except when the 53-bit result is itself a 24-bit midpoint m: every m is a
 * 53-bit number and rounding is monotone, so sqrt(x) < m gives a 53-bit result <= m and
 * sqrt(x) > m one >= m, with equality only when the 53-bit rounding lands on m; those inputs
 * (low 29 bits of the result exactly 0x10000000; about 1 in 2^29 doubles) run Wine's sqrt.
 * (For float arguments rounding twice is always innocuous, 53 >= 2*24 + 2, but double arguments
 * do reach the midpoints: t_lmath2 [2].) The result (2^-537 <= sqrt(x) < 2^512) is a normal
 * double, so fld qword gives the 80-bit value fsqrt left.
 *
 * Registers as Wine's code leaves them on that path: eax = 0xffff0000 | x87 control word (its
 * _dclass returned -1 or -2, then `mov ax, cw`), ecx = high dword of x, edx = 0, xmm0 = x in the
 * low half and 0 in the high half (movsd load), other xmm untouched; the argument slot holds x.
 * Not reproduced: the x87 status word's precision flag (fsqrt sets it) and MXCSR's (sqrtsd sets
 * it): sticky flags the game never reads.
 *
 * Fast path only in the game's FPU mode (x87 CW & 0xf3f == 0x3f: 24-bit, nearest, all masked;
 * MXCSR & 0xffc0 == 0x1f80); zero, negative, infinite or NaN x, or another mode: Wine's sqrt. */
        .intel_syntax noprefix
        .data
        .balign 4
        .globl _gp_sqrt_orig, _gp_oct_cont
_gp_sqrt_orig:  .long 0
_gp_oct_cont:   .long 0x007658ca    /* 0x7658c3 after push ebp; mov ebp,esp; push esi; mov esi,[ebp+8] */
        .balign 64
        .globl _gp_l2_slots
_gp_l2_slots: .fill 16*64, 1, 0   /* per thread line (TEB+0x24): calls, fallbacks: [0] [1] sqrt, [2] [3] octile */

        .section .rdata
        .balign 16
oct_abs:  .long 0x7fffffff, 0x7fffffff, 0x7fffffff, 0x7fffffff
oct_q:    .long 0x3e800000          /* 0.25f (0xbd1904) */

        .text
        .globl _gp_sqrt
        .balign 16
_gp_sqrt:
        mov     eax, dword ptr fs:[0x24]
        shr     eax, 2
        and     eax, 15
        shl     eax, 6
        inc     dword ptr [_gp_l2_slots+eax]
        test    word ptr [_gp_l2_slots+eax], 0xffff
        jz      9f                          /* every 64 k calls: the 60 s log line */
1:      mov     ecx, dword ptr [esp+8]      /* high dword of x */
        cmp     ecx, 0x7ff00000
        jae     8f                          /* negative, infinite, NaN */
        test    ecx, ecx
        jnz     2f
        cmp     dword ptr [esp+4], 0
        je      8f                          /* +0 */
2:      sub     esp, 12
        fnstcw  word ptr [esp+8]
        movzx   eax, word ptr [esp+8]
        and     eax, 0x0f3f
        cmp     eax, 0x003f
        jne     7f
        stmxcsr dword ptr [esp]
        mov     eax, dword ptr [esp]
        and     eax, 0xffc0
        cmp     eax, 0x1f80
        jne     7f
        movsd   xmm0, qword ptr [esp+16]
        sqrtsd  xmm0, xmm0
        movsd   qword ptr [esp], xmm0
        mov     eax, dword ptr [esp]        /* round the low 29 bits away, nearest-even */
        mov     edx, eax
        and     edx, 0x1fffffff
        cmp     edx, 0x10000000
        je      7f                          /* a 24-bit midpoint: which side sqrt(x) is on is lost */
        mov     edx, eax
        shr     edx, 29
        and     edx, 1
        add     edx, 0x0fffffff
        add     eax, edx
        adc     dword ptr [esp+4], 0
        and     eax, 0xe0000000
        mov     dword ptr [esp], eax
        fld     qword ptr [esp]
        movsd   xmm0, qword ptr [esp+16]
        movzx   eax, word ptr [esp+8]
        or      eax, 0xffff0000
        xor     edx, edx                    /* ecx = high dword of x already */
        add     esp, 12
        ret
7:      add     esp, 12
8:      mov     eax, dword ptr fs:[0x24]
        shr     eax, 2
        and     eax, 15
        shl     eax, 6
        inc     dword ptr [_gp_l2_slots+eax+4]
        jmp     dword ptr [_gp_sqrt_orig]
9:      call    sq_tick
        jmp     1b

/* C call with the whole machine state preserved */
        .balign 16
sq_tick:
        pushfd
        pushad
        mov     ebp, esp
        sub     esp, 272
        and     esp, -16
        movaps  [esp], xmm0
        movaps  [esp+16], xmm1
        movaps  [esp+32], xmm2
        movaps  [esp+48], xmm3
        movaps  [esp+64], xmm4
        movaps  [esp+80], xmm5
        movaps  [esp+96], xmm6
        movaps  [esp+112], xmm7
        stmxcsr dword ptr [esp+128]
        fnsave  [esp+144]
        call    _gp_sqrt_periodic
        frstor  [esp+144]
        ldmxcsr dword ptr [esp+128]
        movaps  xmm0, [esp]
        movaps  xmm1, [esp+16]
        movaps  xmm2, [esp+32]
        movaps  xmm3, [esp+48]
        movaps  xmm4, [esp+64]
        movaps  xmm5, [esp+80]
        movaps  xmm6, [esp+96]
        movaps  xmm7, [esp+112]
        mov     esp, ebp
        popad
        popfd
        ret

/* ---- octile: 0x7658c3, the cost of one path segment (summed by 0x765972 over a path; called from
 * the AI update modules and HordeContain) ---------------------------------------------------------
 * cdecl (const Coord2D *a, const Coord2D *b) -> st0. The original, all in x87 at 24-bit precision:
 *   dx = a.x - b.x, dy = a.y - b.y; |dx|, |dy| as floats through the CRT's fabs (4 calls);
 *   big = |dx| > |dy| ? dx : dy (float), small = the other one's absolute value (float);
 *   result = |big| + small * 0.25 (two x87 roundings to 24 bits).
 * The same in SSE single precision: the same bits whenever no subtraction, product or sum
 * overflows or underflows (MXCSR OE/UE/IE/ZE then send it to the original) and no input is NaN.
 * Left as the original leaves them: the argument slots hold big and small (it stores its floats
 * there), ecx = high dword of (double)big (its last two pops), eax / edx = what Wine's fabs leaves
 * for that argument (low dword, high dword without the sign); xmm0-7 and MXCSR unchanged; st0 the
 * result, the x87 stack otherwise empty as on entry. */
        .globl _gp_octile
        .balign 16
_gp_octile:
        mov     eax, dword ptr fs:[0x24]
        shr     eax, 2
        and     eax, 15
        shl     eax, 6
        inc     dword ptr [_gp_l2_slots+eax+8]
        sub     esp, 96                     /* 0 MXCSR, 4 flags, 8 CW, 16 double, 32.. xmm0-3 */
        fnstcw  word ptr [esp+8]
        movzx   eax, word ptr [esp+8]
        and     eax, 0x0f3f
        cmp     eax, 0x003f
        jne     8f
        stmxcsr dword ptr [esp]
        mov     eax, dword ptr [esp]
        and     eax, 0xffc0
        cmp     eax, 0x1f80
        jne     8f
        movups  [esp+32], xmm0
        movups  [esp+48], xmm1
        movups  [esp+64], xmm2
        movups  [esp+80], xmm3
        mov     dword ptr [esp+4], 0x1f80
        ldmxcsr dword ptr [esp+4]           /* flags cleared */
        mov     eax, dword ptr [esp+100]    /* a */
        mov     edx, dword ptr [esp+104]    /* b */
        movss   xmm0, dword ptr [eax]
        subss   xmm0, dword ptr [edx]       /* dx */
        movss   xmm1, dword ptr [eax+4]
        subss   xmm1, dword ptr [edx+4]     /* dy */
        ucomiss xmm0, xmm0
        jp      7f
        ucomiss xmm1, xmm1
        jp      7f
        movaps  xmm2, xmm0
        andps   xmm2, [oct_abs]             /* |dx| */
        movaps  xmm3, xmm1
        andps   xmm3, [oct_abs]             /* |dy| */
        comiss  xmm2, xmm3
        ja      1f
        movaps  xmm0, xmm1                  /* |dx| <= |dy|: big = dy, small = |dx| */
        movaps  xmm3, xmm2
1:      movss   dword ptr [esp+4], xmm3     /* small (to the b slot) */
        mulss   xmm3, [oct_q]
        movaps  xmm2, xmm0
        andps   xmm2, [oct_abs]
        addss   xmm2, xmm3                  /* |big| + small * 0.25 */
        stmxcsr dword ptr [esp+12]
        test    dword ptr [esp+12], 0x1d    /* IE ZE OE UE */
        jnz     7f
        mov     ecx, dword ptr [esp+4]
        mov     dword ptr [esp+104], ecx
        movss   dword ptr [esp+100], xmm0   /* big (to the a slot) */
        movss   dword ptr [esp+4], xmm2
        fld     dword ptr [esp+4]
        cvtss2sd xmm0, xmm0
        movsd   qword ptr [esp+16], xmm0
        mov     eax, dword ptr [esp+16]
        mov     ecx, dword ptr [esp+20]
        mov     edx, ecx
        and     edx, 0x7fffffff
        ldmxcsr dword ptr [esp]
        movups  xmm0, [esp+32]
        movups  xmm1, [esp+48]
        movups  xmm2, [esp+64]
        movups  xmm3, [esp+80]
        add     esp, 96
        ret
7:      ldmxcsr dword ptr [esp]             /* nothing written yet: the original */
        movups  xmm0, [esp+32]
        movups  xmm1, [esp+48]
        movups  xmm2, [esp+64]
        movups  xmm3, [esp+80]
8:      add     esp, 96
        mov     eax, dword ptr fs:[0x24]
        shr     eax, 2
        and     eax, 15
        shl     eax, 6
        inc     dword ptr [_gp_l2_slots+eax+12]
        push    ebp
        mov     ebp, esp
        push    esi
        mov     esi, dword ptr [ebp+8]
        jmp     dword ptr [_gp_oct_cont]
