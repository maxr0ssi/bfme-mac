/* renderstats stubs (p_rstats.c). Each replaces a call to a game function (or its vtable slot),
 * counts, and runs the original with eax, ecx, edx and xmm0-7 as they were (C keeps ebx, esi,
 * edi, ebp and realigns its stack); only the flags differ, which no caller reads across a call.
 * The counting stubs jump to the callee with the stack exactly as the call left it
 * ([esp] = the original return address); the two logging stubs and the timed stubs call the
 * original themselves and return as it does with its eax, ecx, edx and xmm0-7. */
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

/* 0x44bb00 / 0x44bbf5: call 0x449cf8 (thiscall, one argument) */
        .globl _gp_rst_frame_stub
        .balign 16
_gp_rst_frame_stub:
        SAVE
        call    _gp_rst_frame
        RESTORE
        jmp     dword ptr [_gp_rst_frame_cont]

/* Timed calls: the stub reads the time stamp counter, calls the original with the registers and
 * stack arguments the caller gave it (nargs arguments pushed again; the original sees its own
 * return address inside the stub), reads the counter again and has gp_rst_timed(kind, t0, t1)
 * account the interval to the pass in effect (byte 0xdd1e44). The original's eax, ecx, edx and
 * xmm0-7 reach the caller unchanged; ebx, esi, edi, ebp are never touched; rdtsc clobbers only
 * eax/edx, which are restored before the call. pop = 1 for cdecl (the stub pops the copies),
 * retn = what the original's ret pops for its caller. t0 lives in the stub's own frame, so
 * nesting (WW3D::Render > Customized_Render > Visibility_Check) and unwinding need no state. */
.macro TIMED name, kind, nargs, pop, retn, cont
        .globl _\name
        .balign 16
_\name:
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
        SAVE                            /* t0 is now at [esp+140] */
        rdtsc
        push    edx                     /* t1 hi */
        push    eax                     /* t1 lo */
        push    dword ptr [esp+152]     /* t0 hi */
        push    dword ptr [esp+152]     /* t0 lo */
        push    \kind
        call    _gp_rst_timed
        add     esp, 20
        RESTORE
        add     esp, 8
        .if \retn
        ret     \retn
        .else
        ret
        .endif
.endm

/* kinds (p_rstats.c T_*): 0 WW3D::Render, 1 Customized_Render, 2 Visibility_Check,
 * 3 renderOneObject, 4 RTS3DScene::Flush, 5 FX shader flush */
/* 0x47d70c (UpdateShadowMap), 0x518065 (the RenderViews / reflection wrapper 0x518000): call
 * 0x517c60, WW3D::Render(scene, rinfo), cdecl, returns al */
        TIMED   gp_rst_w3r_stub, 0, 2, 1, 0, _gp_rst_w3r_cont
/* vtable slot 0xbdc3c4: Customized_Render 0x46fe84 (thiscall, one argument, ret 4) */
        TIMED   gp_rst_cr_stub, 1, 1, 0, 4, _gp_rst_cr_cont
/* vtable slot 0xbdc3d4: Visibility_Check 0x470b83 (thiscall, one argument, ret 4) */
        TIMED   gp_rst_vis_stub, 2, 1, 0, 4, _gp_rst_vis_cont
/* 0x47009f, 0x47010c (the object loop of Customized_Render): call 0x46f48e, renderOneObject
 * (thiscall, four arguments, ret 16) */
        TIMED   gp_rst_obj_stub, 3, 4, 0, 16, _gp_rst_obj_cont
/* 0x471a3b (RTS3DScene::Render): call 0x470f44, Flush (thiscall, one argument, ret 4) */
        TIMED   gp_rst_flush_stub, 4, 1, 0, 4, _gp_rst_flush_cont
/* 0x517db2 (WW3D::Render) call and 0x516d91 (the DX8 flush wrapper 0x516d80) jmp: 0x574406, the
 * FX shader flush (thiscall, no arguments, ret); from the jmp site the stub returns to the
 * wrapper's caller, whose argument stays for it to pop */
        TIMED   gp_rst_fx_stub, 5, 0, 0, 0, _gp_rst_fx_cont

/* 0x57442a: call 0x574113 (thiscall, ecx = the FX renderer and its lists) */
        .globl _gp_rst_fxl_stub
        .balign 16
_gp_rst_fxl_stub:
        SAVE
        push    ecx
        call    _gp_rst_fxlists
        add     esp, 4
        RESTORE
        jmp     dword ptr [_gp_rst_fxl_cont]

/* 0x57423b: call 0x573464 (thiscall, [esp+4] = the mesh, [esp+8] = its vertices) */
        .globl _gp_rst_fxs_stub
        .balign 16
_gp_rst_fxs_stub:
        SAVE
        push    dword ptr [esp+144]
        call    _gp_rst_skin_fx
        add     esp, 4
        RESTORE
        jmp     dword ptr [_gp_rst_fxs_cont]

/* 0x548291: call 0x549370 (thiscall, ecx = the mesh) */
        .globl _gp_rst_dxs_stub
        .balign 16
_gp_rst_dxs_stub:
        SAVE
        push    ecx
        call    _gp_rst_skin_dx8
        add     esp, 4
        RESTORE
        jmp     dword ptr [_gp_rst_dxs_cont]

/* 0x49d57e / 0x49d585 in 0x49d565: call 0x6bff7b (thiscall, ecx = display, [esp+4] = on, ret 4).
 * 0x49d565 pushed ebx and esi before the argument, so [esp+0x10] is its own return address. */
        .globl _gp_rst_sw_stub
        .balign 16
_gp_rst_sw_stub:
        SAVE
        push    dword ptr [esp+156]     /* who called W3DDisplay vt+0x28 */
        push    dword ptr [esp+148]     /* on */
        call    _gp_rst_sw_before
        add     esp, 8
        RESTORE
        push    dword ptr [esp+4]
        call    dword ptr [_gp_rst_sw_fn]
        SAVE
        call    _gp_rst_after
        RESTORE
        ret     4

/* 0x6020d1 in 0x6020b4: call 0x601c62 (thiscall, ecx = the LOD manager, [esp+4] = level, ret 4).
 * 0x6020b4 pushed esi and edi before the argument, so [esp+0x10] is its own return address. */
        .globl _gp_rst_lod_stub
        .balign 16
_gp_rst_lod_stub:
        SAVE
        push    dword ptr [esp+156]     /* who called setStaticLODLevel */
        push    dword ptr [esp+148]     /* level */
        call    _gp_rst_lod_before
        add     esp, 8
        RESTORE
        push    dword ptr [esp+4]
        call    dword ptr [_gp_rst_lod_fn]
        SAVE
        call    _gp_rst_after
        RESTORE
        ret     4
