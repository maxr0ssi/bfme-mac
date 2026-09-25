/* hittest entry: replaces 0xb0dfe0 (APT button shape hit test, stdcall 4 args, returns al).
 * Checks the FPU modes (same conditions as invsqrt), clears the MXCSR exception flags, calls
 * gp_hittest_c, and if that raised invalid / divide-by-zero / overflow / underflow (the only
 * ways an SSE single result can differ from the game's 24-bit x87 result, see p_hittest.c)
 * throws its answer away and runs the original x87 function instead. MXCSR is restored exactly.
 * Registers: the original changes eax, ecx, edx and no SSE register; the exe was built with
 * whole-program optimisation, so callers may rely on that. xmm0-7 are saved and restored here.
 * gp_hittest_c returns 0/1, or 2 to ask for the original. */
        .intel_syntax noprefix
        .data
        .globl _gp_hittest_cont
        .balign 4
_gp_hittest_cont:
        .long 0x00b0dfe7

        .text
        .globl _gp_hittest
        .balign 16
_gp_hittest:
        sub     esp, 140               /* [0] cw  [4] saved mxcsr  [8] work  [12..139] xmm0-7 */
        fnstcw  word ptr [esp]
        movzx   eax, word ptr [esp]
        and     eax, 0x0f3f
        cmp     eax, 0x003f
        jne     2f
        stmxcsr dword ptr [esp+4]
        mov     eax, dword ptr [esp+4]
        and     eax, 0xffc0
        cmp     eax, 0x1f80
        jne     2f
        movups  [esp+12], xmm0
        movups  [esp+28], xmm1
        movups  [esp+44], xmm2
        movups  [esp+60], xmm3
        movups  [esp+76], xmm4
        movups  [esp+92], xmm5
        movups  [esp+108], xmm6
        movups  [esp+124], xmm7
        mov     eax, dword ptr [esp+4]
        and     eax, 0xffffffc0
        mov     dword ptr [esp+8], eax
        ldmxcsr dword ptr [esp+8]      /* flags cleared */
        push    dword ptr [esp+156]    /* iy */
        push    dword ptr [esp+156]    /* ix */
        push    dword ptr [esp+156]    /* matrix */
        push    dword ptr [esp+156]    /* shape */
        call    _gp_hittest_c@16
        stmxcsr dword ptr [esp+8]
        ldmxcsr dword ptr [esp+4]      /* caller's mode and sticky flags back */
        movups  xmm0, [esp+12]
        movups  xmm1, [esp+28]
        movups  xmm2, [esp+44]
        movups  xmm3, [esp+60]
        movups  xmm4, [esp+76]
        movups  xmm5, [esp+92]
        movups  xmm6, [esp+108]
        movups  xmm7, [esp+124]
        test    byte ptr [esp+8], 0x1d /* IE ZE OE UE */
        jnz     1f
        cmp     eax, 2
        je      1f
        add     esp, 140
        ret     16
1:      lock inc dword ptr [_gp_hittest_stats+12]
2:      add     esp, 140
        sub     esp, 0x1c              /* the two instructions the jmp replaced */
        fild    dword ptr [esp+0x28]
        jmp     dword ptr [_gp_hittest_cont]
