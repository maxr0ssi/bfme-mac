/* quatmat entry: replaces 0xb26100 (quaternion -> 3x3 part of a 3x4 matrix; thiscall, ecx = matrix,
 * [esp+4] = quaternion, ret 4; 3 callers in the animation code). Same scheme as p_hittest.S: FPU
 * mode check, MXCSR flags cleared, gp_quat2mat_c, original x87 code if a flag says an SSE result
 * could differ. The original changes only eax (ecx is used by its callers right after the call),
 * so ecx, edx and xmm0-7 are preserved here. */
        .intel_syntax noprefix
        .data
        .globl _gp_quat2mat_cont
        .balign 4
_gp_quat2mat_cont:
        .long 0x00b26107

        .text
        .globl _gp_quat2mat
        .balign 16
_gp_quat2mat:
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
        push    ecx
        push    edx
        push    dword ptr [esp+152]    /* quaternion */
        push    ecx                    /* matrix */
        call    _gp_quat2mat_c@8
        pop     edx
        pop     ecx
        stmxcsr dword ptr [esp+8]
        ldmxcsr dword ptr [esp+4]
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
        mov     eax, dword ptr [esp+144] /* eax = quaternion pointer, as the original leaves it */
        add     esp, 140
        ret     4
1:      lock inc dword ptr [_gp_quat2mat_fallbacks]
2:      add     esp, 140
        mov     eax, dword ptr [esp+4] /* the two instructions the jmp replaced */
        fld     dword ptr [eax+8]
        jmp     dword ptr [_gp_quat2mat_cont]
