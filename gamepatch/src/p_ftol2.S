/* ftol2: the CRT's x87 _ftol2 at 0xa3cfa4 (584 call sites: every float -> integer cast of the
 * exe) without the x87 conversions. The original: n = fistp(x) (round to nearest, as int64),
 * diff = x - n at 24-bit precision stored as a float, then n +/- 1 from the sign of diff so that
 * edx:eax = trunc(x); ecx = the float bits of diff, sign-adjusted, + 0x7fffffff (the carry is the
 * correction); if n is 0 or 0x8000000000000000 (|x| < 0.5 ... , or the integer indefinite for
 * |x| >= 2^63, inf, NaN) it returns hi:0 at once and ecx is untouched.
 * Here, in the game's x87 mode (CW & 0xf3f == 0x3f) only: fstp tbyte pops x exactly, and the
 * same n, diff, ecx and result are computed in integer arithmetic from the 64-bit significand
 * (round to nearest even for n; diff rounded to 24 bits, nearest even, is the float the original
 * stores: |diff| is 0 or in [2^-64, 0.5]). Other modes: the original. Preserves ebx esi edi ebp
 * and every xmm register (it uses none); x87: pops st0 like the original. Test: t_ftol2.c. */
        .intel_syntax noprefix
        .data
        .balign 4
        .globl _gp_ftol2_cont
_gp_ftol2_cont: .long 0x00a3cfaa        /* after push ebp; mov ebp,esp; sub esp,0x20 */
        .globl _gp_ftol2_calls, _gp_ftol2_x87
        .balign 64
_gp_ftol2_calls: .fill 16*16, 4, 0      /* per thread line (TEB+0x24): [0] calls, [1] x87 runs */
_gp_ftol2_x87 = _gp_ftol2_calls + 4

        .text
        .globl _gp_ftol2
        .balign 16
/* frame: [0] cw [4..13] x (tbyte) [16] ebx [20] esi [24] edi [28] sign/exponent word
 *        [32] float exponent of diff [36] caller's ecx */
_gp_ftol2:
        mov     eax, dword ptr fs:[0x24]
        shr     eax, 2
        and     eax, 15
        shl     eax, 6
        inc     dword ptr [_gp_ftol2_calls+eax]
        sub     esp, 40
        fnstcw  word ptr [esp]
        movzx   eax, word ptr [esp]
        and     eax, 0x0f3f
        cmp     eax, 0x003f
        jne     90f
        fstp    tbyte ptr [esp+4]
        mov     dword ptr [esp+16], ebx
        mov     dword ptr [esp+20], esi
        mov     dword ptr [esp+24], edi
        mov     dword ptr [esp+36], ecx
        mov     esi, dword ptr [esp+4]          /* significand M = edi:esi */
        mov     edi, dword ptr [esp+8]
        movzx   ebx, word ptr [esp+12]
        mov     dword ptr [esp+28], ebx
        mov     eax, ebx
        and     eax, 0x7fff
        jz      80f                             /* zero, denormal: n = 0 */
        test    edi, edi
        jns     81f                             /* unnormal: fistp gives the indefinite */
        sub     eax, 16383                      /* E: |x| = M * 2^(E-63) */
        cmp     eax, 63
        jge     81f                             /* |x| >= 2^63, inf, NaN */
        cmp     eax, -1
        jl      80f                             /* |x| < 0.5: n = 0 */
        mov     ebx, eax
        jne     15f
        xor     eax, eax                        /* E = -1: integer part 0, fraction F = M */
        xor     edx, edx
        jmp     3f
15:     mov     ecx, 63                         /* integer part = M >> (63 - E) */
        sub     ecx, ebx
        mov     eax, esi
        mov     edx, edi
        cmp     ecx, 32
        jb      1f
        mov     eax, edx
        xor     edx, edx
1:      shrd    eax, edx, cl
        shr     edx, cl
        lea     ecx, [ebx+1]                    /* fraction F = M << (E + 1), a 64-bit fixed point */
        cmp     ecx, 32
        jb      2f
        mov     edi, esi
        xor     esi, esi
2:      shld    edi, esi, cl
        shl     esi, cl
3:      xor     ebx, ebx                        /* round to nearest even: up if F > 1/2, or = 1/2 and odd */
        cmp     edi, 0x80000000
        ja      4f
        jb      5f
        test    esi, esi
        jnz     4f
        test    al, 1
        jz      5f
4:      add     eax, 1
        adc     edx, 0
        neg     esi                             /* D = 1 - F: |x| - |n|, negative */
        adc     edi, 0
        neg     edi
        mov     ebx, 0x8000
5:      cmp     edx, 0x80000000                 /* |n| = 2^63: indefinite (x > 0) or -2^63, same bits */
        jne     6f
        test    eax, eax
        jz      81f
6:      test    byte ptr [esp+29], 0x80
        jz      7f
        neg     eax                             /* n = -|n| */
        adc     edx, 0
        neg     edx
7:      test    eax, eax
        jnz     10f
        test    edx, 0x7fffffff
        jz      82f                             /* n = 0: returned at once, like the original */
10:     xor     ecx, ecx                        /* diff = +0 when D = 0 */
        test    edi, edi
        jnz     11f
        test    esi, esi
        jz      20f
        mov     edi, esi
        xor     esi, esi
        mov     dword ptr [esp+32], 126 - 32
        jmp     12f
11:     mov     dword ptr [esp+32], 126         /* D * 2^-64 with the top bit at 63: 2^-1 */
12:     bsr     ecx, edi
        neg     ecx
        add     ecx, 31                         /* leading zeros */
        sub     dword ptr [esp+32], ecx
        shld    edi, esi, cl
        shl     esi, cl
        mov     ecx, edi
        shr     ecx, 8                          /* 24-bit significand */
        test    edi, 0x80
        jz      14f
        test    edi, 0x7f
        jnz     13f
        test    esi, esi
        jnz     13f
        test    cl, 1
        jz      14f
13:     inc     ecx
        cmp     ecx, 0x1000000
        jb      14f
        shr     ecx, 1
        inc     dword ptr [esp+32]
14:     and     ecx, 0x7fffff
        mov     edi, dword ptr [esp+32]
        shl     edi, 23
        or      ecx, edi
        mov     edi, dword ptr [esp+28]         /* sign of diff: x's, flipped when rounded up */
        xor     edi, ebx
        and     edi, 0x8000
        shl     edi, 16
        or      ecx, edi
20:     test    byte ptr [esp+29], 0x80         /* the original's correction, on its sign of x */
        jz      21f
        xor     ecx, 0x80000000
        add     ecx, 0x7fffffff
        adc     eax, 0
        adc     edx, 0
        jmp     30f
21:     add     ecx, 0x7fffffff
        sbb     eax, 0
        sbb     edx, 0
30:     mov     ebx, dword ptr [esp+16]
        mov     esi, dword ptr [esp+20]
        mov     edi, dword ptr [esp+24]
        add     esp, 40
        ret
80:     xor     eax, eax                        /* n = 0 */
        xor     edx, edx
        jmp     82f
81:     xor     eax, eax                        /* the integer indefinite */
        mov     edx, 0x80000000
82:     mov     ecx, dword ptr [esp+36]         /* ecx untouched on this path */
        jmp     30b
90:     mov     eax, dword ptr fs:[0x24]        /* other x87 mode: the original */
        shr     eax, 2
        and     eax, 15
        shl     eax, 6
        inc     dword ptr [_gp_ftol2_x87+eax]
        add     esp, 40
        push    ebp                             /* the three instructions the jmp replaced */
        mov     ebp, esp
        sub     esp, 0x20
        jmp     dword ptr [_gp_ftol2_cont]
