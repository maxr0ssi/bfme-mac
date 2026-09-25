/* animdedup and animdecode entries (the logic is in p_anim.c) and the helpers that call the
 * game's thiscall functions from C. Every entry keeps what its original keeps: ebx esi edi ebp
 * (C code preserves them), and the decoder entries also ecx (this) and xmm1-7 (the 8-bit decoders
 * use only xmm0, the 4-bit ones xmm0 and xmm1). */
        .intel_syntax noprefix
        .data
        .globl _gp_ad_skip, _gp_ad_usot_orig, _gp_adq_dtor_cont
        .balign 4
_gp_ad_skip:                    /* object whose next Animatable USOT is skipped (main thread) */
        .long 0
_gp_ad_usot_orig:
        .long 0x005a5050
_gp_adq_dtor_cont:
        .long 0x005b1904

        .text
/* 0x5a4dfc (in Animatable3DObjClass::Render): call Single_Anim_Progress, thiscall, no args */
        .globl _gp_ad_progress
        .balign 16
_gp_ad_progress:
        push    ecx
        call    _gp_ad_progress_c@4
        ret

/* 0x59cd79 (first call in HLodClass::USOT): call Animatable3DObjClass::USOT, thiscall, no
 * args. Skipped for the object gp_ad_progress_c just marked: its pose is already this frame's
 * (valid is set, as the original's end would). Otherwise its snapshot is dropped (only the single
 * animation path of this very call records a new one) and the original runs. */
        .globl _gp_ad_usot_base
        .balign 16
_gp_ad_usot_base:
        cmp     ecx, dword ptr [_gp_ad_skip]
        jne     1f
        mov     eax, dword ptr fs:[0x24]        /* TEB ClientId.UniqueThread */
        cmp     eax, dword ptr [_gp_render_tid]
        jne     1f
        mov     dword ptr [_gp_ad_skip], 0
        mov     byte ptr [ecx+0xf4], 1
        ret
1:      push    ecx
        push    ecx
        call    _gp_ad_forget@4
        pop     ecx
        jmp     dword ptr [_gp_ad_usot_orig]

/* 0x5a512c (single-animation path of Animatable3DObjClass::USOT): call 0x5a3f70, thiscall
 * (&transform, anim, frame), ret 12: runs it, then snapshots its inputs */
        .globl _gp_ad_single
        .balign 16
_gp_ad_single:
        push    dword ptr [esp+12]
        push    dword ptr [esp+12]
        push    dword ptr [esp+12]
        push    ecx
        call    _gp_ad_single_c@16
        ret     12

/* the six from-frame-0 decoder calls (motion channel Get_* with no cache stream): thiscall
 * (src, srcFrame, dstFrame, outA, outB), ret 20 */
.macro ADQ_SITE k
        .globl _gp_adq_site\k
        .balign 16
_gp_adq_site\k:
        push    \k
        jmp     adq_common
.endm
        ADQ_SITE 0
        ADQ_SITE 1
        ADQ_SITE 2
        ADQ_SITE 3
        ADQ_SITE 4
        ADQ_SITE 5
        .balign 16
adq_common:                         /* [esp] = k, [esp+4] = return, [esp+8] = args; ecx = channel */
        sub     esp, 112
        movups  [esp], xmm1
        movups  [esp+16], xmm2
        movups  [esp+32], xmm3
        movups  [esp+48], xmm4
        movups  [esp+64], xmm5
        movups  [esp+80], xmm6
        movups  [esp+96], xmm7
        push    ecx                     /* the decoders keep ecx (this) */
        lea     eax, [esp+124]
        push    eax
        push    ecx
        push    dword ptr [esp+124]
        call    _gp_adq_c@12
        pop     ecx
        movups  xmm1, [esp]
        movups  xmm2, [esp+16]
        movups  xmm3, [esp+32]
        movups  xmm4, [esp+48]
        movups  xmm5, [esp+64]
        movups  xmm6, [esp+80]
        movups  xmm7, [esp+96]
        add     esp, 116
        ret     20

/* 0x5b18fe (motion channel base destructor): forget the channel, then the 6 replaced bytes */
        .globl _gp_adq_dtor
        .balign 16
_gp_adq_dtor:
        push    eax
        push    ecx
        push    edx
        push    ecx
        call    _gp_adq_evict@4
        pop     edx
        pop     ecx
        pop     eax
        push    esi
        mov     esi, ecx
        push    dword ptr [esi+0x28]
        jmp     dword ptr [_gp_adq_dtor_cont]

/* ---- helpers for C (cdecl) ---- */
/* uint32_t gp_ad_call_ccf(fn, this, uint32_t *dir): Compute_Current_Frame, float bits of st0 */
        .globl _gp_ad_call_ccf
        .balign 16
_gp_ad_call_ccf:
        mov     eax, dword ptr [esp+4]
        mov     ecx, dword ptr [esp+8]
        push    dword ptr [esp+12]
        call    eax
        sub     esp, 4
        fstp    dword ptr [esp]
        pop     eax
        ret

/* void gp_call_this0(fn, this) */
        .globl _gp_call_this0
        .balign 16
_gp_call_this0:
        mov     eax, dword ptr [esp+4]
        mov     ecx, dword ptr [esp+8]
        jmp     eax

/* void gp_call_this3(fn, this, a, b, c) */
        .globl _gp_call_this3
        .balign 16
_gp_call_this3:
        mov     eax, dword ptr [esp+4]
        mov     ecx, dword ptr [esp+8]
        push    dword ptr [esp+20]
        push    dword ptr [esp+20]
        push    dword ptr [esp+20]
        call    eax
        ret

/* void gp_call_dec(fn, this, src, srcFrame, dst, outA, outB) */
        .globl _gp_call_dec
        .balign 16
_gp_call_dec:
        mov     eax, dword ptr [esp+4]
        mov     ecx, dword ptr [esp+8]
        push    dword ptr [esp+28]
        push    dword ptr [esp+28]
        push    dword ptr [esp+28]
        push    dword ptr [esp+28]
        push    dword ptr [esp+28]
        call    eax
        ret
