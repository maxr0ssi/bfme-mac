/* floor/ceil: the exe's imports of msvcr71!floor (0xbd0580, 417 call sites) and ceil (0xbd0588,
 * 145) redirected to SSE4.1 roundsd. Both functions are exact (the result is the unique integer
 * value, sign of zero kept), so any correct implementation returns the same double; the fast
 * path takes only normal finite inputs and leaves zeros, denormals, infinities and NaNs to the
 * CRT. The result is returned in st0 like the CRT's (a double load is exact at any precision).
 * Installed only if the CPU has SSE4.1 (Rosetta 2 does). */
        .intel_syntax noprefix
        .data
        .balign 4
        .globl _gp_floor_orig, _gp_ceil_orig
_gp_floor_orig: .long 0
_gp_ceil_orig:  .long 0

        .text
.macro ROUNDFN name, imm, orig
        .globl \name
        .balign 16
\name:
        mov     eax, dword ptr [esp+8]  /* high dword of the double argument */
        and     eax, 0x7ff00000
        jz      1f                      /* zero or denormal: CRT */
        cmp     eax, 0x7ff00000
        je      1f                      /* inf or NaN: CRT */
        sub     esp, 24
        movups  [esp+8], xmm0
        movsd   xmm0, qword ptr [esp+28]
        roundsd xmm0, xmm0, \imm
        movsd   qword ptr [esp], xmm0
        fld     qword ptr [esp]
        movups  xmm0, [esp+8]
        add     esp, 24
        ret
1:      jmp     dword ptr [\orig]
.endm

        ROUNDFN _gp_floor, 9, _gp_floor_orig     /* round down, no precision exception */
        ROUNDFN _gp_ceil, 10, _gp_ceil_orig      /* round up */
