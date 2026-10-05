/* logicstats stubs (p_lstats.c). Counters only: every stub runs the original with eax, ecx, edx
 * and xmm0-7 as the caller left them and returns the original's eax, ecx, edx and xmm0-7; ebx,
 * esi, edi, ebp are never touched. rdtsc clobbers only eax/edx, which are restored before the
 * original runs. Same scheme as p_rstats.S. */
        .intel_syntax noprefix
        .text
.macro SAVE                             /* afterwards the caller's [esp+k] is at [esp+140+k] */
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

/* GameLogic::update 0x62e4e8 (thiscall, [esp+4] = phase 1..6, ret 4), entered through its two
 * vtable slots 0xbd85c4 / 0xbfdb9c. gp_lst_begin(phase) first (frame interval, lazy subsystem
 * hooks), then the timed call, then gp_lst_end(t0, t1). */
        .globl _gp_lst_logic_stub
        .balign 16
_gp_lst_logic_stub:
        SAVE
        push    dword ptr [esp+144]     /* phase */
        call    _gp_lst_begin
        add     esp, 4
        RESTORE
        sub     esp, 8                  /* t0; the caller's [esp+k] is now at [esp+8+k] */
        push    eax
        push    edx
        rdtsc
        mov     [esp+8], eax
        mov     [esp+12], edx
        pop     edx
        pop     eax
        push    dword ptr [esp+12]      /* the phase again, for the original */
        call    dword ptr [_gp_lst_logic_cont]
        SAVE                            /* t0 at [esp+140] */
        rdtsc
        push    edx
        push    eax
        push    dword ptr [esp+152]     /* t0 hi */
        push    dword ptr [esp+152]     /* t0 lo */
        call    _gp_lst_end
        add     esp, 16
        RESTORE
        add     esp, 8
        ret     4

/* Timed call to *[cont], nargs stack arguments pushed again, ret retn; accounted to kind. */
.macro TIMED name, kind, nargs, retn, cont
        .globl _\name
        .balign 16
_\name:
        sub     esp, 8
        push    eax
        push    edx
        rdtsc
        mov     [esp+8], eax
        mov     [esp+12], edx
        pop     edx
        pop     eax
        .rept \nargs
        push    dword ptr [esp+12+4*(\nargs-1)]
        .endr
        call    dword ptr [\cont]
        SAVE
        rdtsc
        push    edx
        push    eax
        push    dword ptr [esp+152]
        push    dword ptr [esp+152]
        push    \kind
        call    _gp_lst_timed
        add     esp, 20
        RESTORE
        add     esp, 8
        .if \retn
        ret     \retn
        .else
        ret
        .endif
.endm

/* subsystem update functions, vtable slot +0x28 of the singletons GameLogic::update calls
 * (thiscall, no arguments, ret); slots hooked at run time by gp_lst_begin */
        TIMED   gp_lst_sub0, 0, 0, 0, _gp_lst_cont+0
        TIMED   gp_lst_sub1, 1, 0, 0, _gp_lst_cont+4
        TIMED   gp_lst_sub2, 2, 0, 0, _gp_lst_cont+8
        TIMED   gp_lst_sub3, 3, 0, 0, _gp_lst_cont+12
        TIMED   gp_lst_sub4, 4, 0, 0, _gp_lst_cont+16
        TIMED   gp_lst_sub5, 5, 0, 0, _gp_lst_cont+20
        TIMED   gp_lst_sub6, 6, 0, 0, _gp_lst_cont+24
        TIMED   gp_lst_sub7, 7, 0, 0, _gp_lst_cont+28
        TIMED   gp_lst_sub8, 8, 0, 0, _gp_lst_cont+32
        TIMED   gp_lst_sub9, 9, 0, 0, _gp_lst_cont+36
        TIMED   gp_lst_sub10, 10, 0, 0, _gp_lst_cont+40
        TIMED   gp_lst_sub11, 11, 0, 0, _gp_lst_cont+44
        TIMED   gp_lst_sub12, 12, 0, 0, _gp_lst_cont+48
        TIMED   gp_lst_sub13, 13, 0, 0, _gp_lst_cont+52
        TIMED   gp_lst_sub14, 14, 0, 0, _gp_lst_cont+56
        TIMED   gp_lst_sub15, 15, 0, 0, _gp_lst_cont+60
        TIMED   gp_lst_sub16, 16, 0, 0, _gp_lst_cont+64
        TIMED   gp_lst_sub17, 17, 0, 0, _gp_lst_cont+68
        TIMED   gp_lst_sub18, 18, 0, 0, _gp_lst_cont+72
/* direct calls in GameLogic::update (p_lstats.c CALLS[]): 0x820ef0, 0x81be85, 0x629da6, 0x62a2c9,
 * 0x80f4d3 (thiscall, no arguments, ret) and 0x6260e1 (thiscall, one argument, ret 4) */
        TIMED   gp_lst_call0, 24, 0, 0, _gp_lst_cont+96
        TIMED   gp_lst_call1, 25, 0, 0, _gp_lst_cont+100
        TIMED   gp_lst_call2, 26, 1, 4, _gp_lst_cont+104
        TIMED   gp_lst_call3, 27, 0, 0, _gp_lst_cont+108
        TIMED   gp_lst_call4, 28, 0, 0, _gp_lst_cont+112
        TIMED   gp_lst_call5, 29, 0, 0, _gp_lst_cont+116

/* 0x62ea97 (7 bytes: lea ecx,[ebx+0x10]; mov eax,[ecx]; call [eax]) -> call stub; 2-byte nop.
 * The update module's update (thiscall, no arguments, ret), timed per module vtable. On return
 * eax = its result, ecx/edx/xmm as it left them, exactly what the original sequence leaves. */
        .globl _gp_lst_mod_stub
        .balign 16
_gp_lst_mod_stub:
        lea     ecx, [ebx+0x10]
        sub     esp, 12                 /* [esp] t0 lo, [esp+4] t0 hi, [esp+8] vtable */
        push    edx                     /* the caller's edx, for the callee */
        mov     eax, [ecx]
        mov     [esp+12], eax
        rdtsc
        mov     [esp+4], eax
        mov     [esp+8], edx
        pop     edx
        mov     eax, [esp+8]            /* eax, ecx, edx as the original sequence leaves them */
        call    dword ptr [eax]
        SAVE                            /* t0 lo at [esp+140], t0 hi [esp+144], vtable [esp+148] */
        rdtsc
        push    edx
        push    eax
        push    dword ptr [esp+152]     /* t0 hi */
        push    dword ptr [esp+152]     /* t0 lo */
        push    dword ptr [esp+164]     /* vtable */
        call    _gp_lst_mod
        add     esp, 20
        RESTORE
        add     esp, 12
        ret
