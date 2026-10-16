/* framesplit stubs (p_framesplit.c). Timers only: every stub runs the original with eax, ecx, edx
 * and xmm0-7 as the caller left them and returns the original's eax, ecx, edx and xmm0-7; ebx, esi,
 * edi, ebp are never touched (same scheme as p_lstats.S). The C side reads the clock (QPC). */
        .intel_syntax noprefix
        .text
.macro SAVE
        sub     esp, 128
        movups  [esp], xmm0
        movups  [esp+16], xmm1
        movups  [esp+32], xmm2
        movups  [esp+48], xmm3
        movups  [esp+64], xmm4
        movups  [esp+80], xmm5
        movups  [esp+96], xmm6
        movups  [esp+112], xmm7
        push    eax
        push    ecx
        push    edx
.endm
.macro RESTORE
        pop     edx
        pop     ecx
        pop     eax
        movups  xmm0, [esp]
        movups  xmm1, [esp+16]
        movups  xmm2, [esp+32]
        movups  xmm3, [esp+48]
        movups  xmm4, [esp+64]
        movups  xmm5, [esp+80]
        movups  xmm6, [esp+96]
        movups  xmm7, [esp+112]
        add     esp, 128
.endm
.macro MARK what, arg                   /* gp_fs_mark(what, arg), all registers kept */
        SAVE
        push    \arg
        push    \what
        call    _gp_fs_mark
        add     esp, 8
        RESTORE
.endm

/* GameEngine vt+0x9c, the client pass 0x632409 (thiscall, no arguments): slots 0xbd857c, 0xbfe2fc */
        .globl _gp_fs_s_client
        .balign 16
_gp_fs_s_client:
        MARK    0, 0
        call    dword ptr [_gp_fs_cont+0]
        MARK    1, 0
        ret

/* GameEngine vt+0x98, the engine step 0x6329b0 (thiscall, the phase, ret 4): slots 0xbd8578, 0xbfe2f8 */
        .globl _gp_fs_s_step
        .balign 16
_gp_fs_s_step:
        MARK    2, "dword ptr [esp+144]"  /* after SAVE the caller's [esp+4] (the phase) is at [esp+144] */
        push    dword ptr [esp+4]
        call    dword ptr [_gp_fs_cont+4]
        MARK    3, 0
        ret     4

/* W3DDisplay vt slot 0xbd9c58, W3DDisplay::draw 0x44b788 (thiscall, no arguments) */
        .globl _gp_fs_s_draw
        .balign 16
_gp_fs_s_draw:
        MARK    4, 0
        call    dword ptr [_gp_fs_cont+8]
        MARK    5, 0
        ret

/* 0x52264b (8 bytes: push ebx x4; push eax; call [edx+0x44]) -> call here; 3-byte nop. The device's
 * Present(device, NULL, NULL, NULL, NULL) at the end of a drawn frame (DX8Wrapper, after EndScene). */
        .globl _gp_fs_s_present
        .balign 16
_gp_fs_s_present:
        MARK    6, 0
        push    ebx
        push    ebx
        push    ebx
        push    ebx
        push    eax
        call    dword ptr [edx+0x44]
        MARK    7, 0
        ret

/* 0x63a196 (6 bytes: call [timeGetTime]) -> call here; nop. The frame limiter's path starts: mark,
 * then timeGetTime returns to the nop. */
        .globl _gp_fs_s_wait
        .balign 16
_gp_fs_s_wait:
        MARK    8, 0
        mov     eax, [_gp_fs_cont+12]   /* the IAT slot */
        jmp     dword ptr [eax]

/* 0x63a21f (6 bytes: mov ecx, [0xde42f8]) -> call here; nop. The end of one engine iteration (both
 * the limited and the unlimited path pass here). */
        .globl _gp_fs_s_iter
        .balign 16
_gp_fs_s_iter:
        MARK    9, 0
        mov     ecx, [_gp_fs_cont+16]
        mov     ecx, [ecx]
        ret
