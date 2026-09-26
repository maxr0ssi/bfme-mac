/* particlestats stubs (p_pstats.c). Each replaces a call to a game function (or its vtable slot):
 * optionally a counting step first (gp_pst_pre, with eax/ecx/edx and xmm0-7 saved around it), then
 * the time stamp counter, the original called with the registers and stack arguments the caller
 * gave it (nargs arguments pushed again; the original sees its own return address inside the
 * stub), the counter again, and gp_pst_timed(kind, t0, t1, eax) accounts the interval and the
 * original's eax to the pass in effect (byte 0xdd1e44). The original's eax, ecx, edx and xmm0-7
 * reach the caller unchanged; ebx, esi, edi, ebp are never touched (C keeps them); only the flags
 * differ, which no caller reads across a call. pop = 1 for cdecl (the stub pops its copies),
 * retn = what the original's ret pops for its caller. Same scheme as p_rstats.S TIMED. */
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

.macro TIMED name, kind, nargs, pop, retn, cont, pre
        .globl _\name
        .balign 16
_\name:
        .if \pre
        SAVE
        push    \kind
        call    _gp_pst_pre
        add     esp, 4
        RESTORE
        .endif
        sub     esp, 8                  /* t0; afterwards the caller's [esp+k] is at [esp+8+k] */
        push    eax
        push    edx
        rdtsc
        mov     [esp+8], eax
        mov     [esp+12], edx
        pop     edx
        pop     eax
        .rept \nargs                    /* the last argument first; each push moves the next up */
        push    dword ptr [esp+12+4*(\nargs-1)]
        .endr
        call    dword ptr [\cont]
        .if \pop
        add     esp, 4*\nargs
        .endif
        SAVE                            /* t0 is now at [esp+140], the original's eax at [esp+8] */
        push    dword ptr [esp+8]       /* ret; t0 now at [esp+144] */
        rdtsc
        push    edx                     /* t1 hi */
        push    eax                     /* t1 lo; t0 lo/hi at [esp+152]/[esp+156] */
        push    dword ptr [esp+156]     /* t0 hi */
        push    dword ptr [esp+156]     /* t0 lo */
        push    \kind
        call    _gp_pst_timed
        add     esp, 24
        RESTORE
        add     esp, 8
        .if \retn
        ret     \retn
        .else
        ret
        .endif
.endm

/* kinds (gp_render.h PS_*): 0 manager render, 1 RenderObject draw module, 2 its colour setters,
 * 3 sorting-renderer flush, 4 ParticleBufferClass::Render */
/* 0x4716ee: call 0x44c3ea (cdecl, 1 argument: the render info; the caller pops it) */
        TIMED   gp_pst_mgr_stub, 0, 1, 1, 0, _gp_pst_mgr_cont, 1
/* vtable slot 0xc32854: 0x964c00 (thiscall, 3 arguments, ret 12; eax = particles processed) */
        TIMED   gp_pst_robj_stub, 1, 3, 0, 12, _gp_pst_robj_cont, 0
/* 0x965277: call 0x50e040, 0x96528b: call 0x50e244, 0x9652cb: call 0x50e413 (cdecl, 4 / 2 / 4
 * arguments, the caller pops them; al = result) */
        TIMED   gp_pst_c1_stub, 2, 4, 1, 0, _gp_pst_c1_cont, 0
        TIMED   gp_pst_c2_stub, 2, 2, 1, 0, _gp_pst_c2_cont, 0
        TIMED   gp_pst_c3_stub, 2, 4, 1, 0, _gp_pst_c3_cont, 0
/* 0x4716f4: call 0x52ec60 (no arguments, plain ret) */
        TIMED   gp_pst_sort_stub, 3, 0, 0, 0, _gp_pst_sort_cont, 1
/* vtable slot 0xbed2a0: 0x5aed50 (thiscall, 1 argument, ret 4) */
        TIMED   gp_pst_pbuf_stub, 4, 1, 0, 4, _gp_pst_pbuf_cont, 0
