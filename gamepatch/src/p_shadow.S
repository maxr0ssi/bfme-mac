/* Entry stubs for shadowpar (par_shadow.c), edgemap (p_edgemap.c) and shadowstats (p_shstats.c). Each replaces a few
 * instructions with a jmp here, calls C (which keeps ebx, esi, edi, ebp; the C side realigns its
 * stack), and continues in the game at an address set by the installer (va + gp_va_offset).
 * Every path leaves the registers the game code after it reads exactly as the original would. */
        .intel_syntax noprefix
        .data
        .balign 4
        .globl _gp_sp_loop_cont, _gp_sp_block_orig, _gp_sp_block_tail, _gp_sp_block_done
        .globl _gp_sp_a1_cont, _gp_cv_cont, _gp_shst_rs_cont, _gp_shst_sm_cont
_gp_sp_loop_cont:  .long 0      /* 0x4f4fef: after the caster loop of renderShadows */
_gp_sp_block_orig: .long 0      /* 0x4f330b: the original heavy block, after the replaced pair */
_gp_sp_block_tail: .long 0      /* 0x4f33d7: constructVolume / constructVolumeVB call */
_gp_sp_block_done: .long 0      /* 0x4f33fe: after the block */
_gp_sp_a1_cont:    .long 0      /* 0x4f223d: after the triangle-normal loop */
_gp_cv_cont:       .long 0      /* 0x4ef796: constructVolume after its prologue */
_gp_shst_rs_cont:  .long 0      /* 0x4f43a6: W3DVolumetricShadowManager::renderShadows */
_gp_shst_sm_cont:  .long 0      /* 0x47d5c9: UpdateShadowMap */

        .text
/* 0x4f4fe8 (cmp eax,ebx; mov [ebp+8],eax; jne loop): eax = first caster, [ebp-0x10] = the
 * dynamic task list. The whole loop runs in gp_sp_casters; the original leaves eax = 0 and
 * [ebp+8] = 0 (ebx is 0 throughout renderShadows). */
        .globl _gp_sp_loop_stub
        .balign 16
_gp_sp_loop_stub:
        push    dword ptr [ebp-0x10]
        push    eax
        call    _gp_sp_casters
        add     esp, 8
        xor     eax, eax
        mov     dword ptr [ebp+8], eax
        jmp     dword ptr [_gp_sp_loop_cont]

/* 0x4f3301 in updateMeshVolume (mov eax,[ebp+0x6c]; lea esi,[ebx+eax*2+0x4400]): ebx = shadow,
 * edi = the transform history the code after the block writes. gp_sp_block returns
 * 0 = block done (job queued or verified): continue at 0x4f33fe with esi = &volume slot;
 * 1 = run the original block; 2 = silhouette built inline: continue at the construct call
 * 0x4f33d7 with esi = &volume slot. */
        .globl _gp_sp_block_stub
        .balign 16
_gp_sp_block_stub:
        push    ebp
        push    ebx
        call    _gp_sp_block
        add     esp, 8
        test    eax, eax
        jz      1f
        cmp     eax, 2
        je      2f
        mov     eax, dword ptr [ebp+0x6c]
        lea     esi, [ebx+eax*2+0x4400]
        jmp     dword ptr [_gp_sp_block_orig]
1:      mov     eax, dword ptr [ebp-8]
        lea     esi, [ebx+eax*4+0x80]
        jmp     dword ptr [_gp_sp_block_done]
2:      mov     eax, dword ptr [ebp-8]
        lea     esi, [ebx+eax*4+0x80]
        jmp     dword ptr [_gp_sp_block_tail]

/* 0x4f2221 in buildPolygonNormals (xor edi,edi; cmp [esi+0x1c],edi; jle): esi = mesh,
 * [ebp-0x10] = output. 0x4f223d pops edi and ebx, so their loop values do not matter. */
        .globl _gp_sp_a1_stub
        .balign 16
_gp_sp_a1_stub:
        push    dword ptr [ebp-0x10]
        push    esi
        call    _gp_sp_normals
        add     esp, 8
        jmp     dword ptr [_gp_sp_a1_cont]

/* 0x4ef790 constructVolume entry (push ebp; mov ebp,esp; sub esp,0x40): thiscall, ecx = shadow,
 * [esp+4] light position, [esp+8] extrusion, [esp+12] light index, [esp+16] mesh index. */
        .globl _gp_cv_entry_stub
        .balign 16
_gp_cv_entry_stub:
        push    ecx
        push    dword ptr [esp+0x14]    /* mesh */
        push    dword ptr [esp+0x14]    /* light index */
        push    dword ptr [esp+0x10]    /* light position */
        push    ecx                     /* shadow */
        call    _gp_cv_prepermute
        add     esp, 16
        pop     ecx
        push    ebp
        mov     ebp, esp
        sub     esp, 0x40
        jmp     dword ptr [_gp_cv_cont]

/* shadowstats: the calls at 0x499d83 (thiscall 0x4f43a6: ecx = the volumetric shadow manager, one
 * stack argument) and 0x449df5 (thiscall 0x47d5c9: ecx = the shadow map, one stack argument) come
 * here, count, and jump to the callee with every register, the flags aside, and the stack exactly
 * as the call left them ([esp] = the original return address). */
        .globl _gp_shst_rs_stub
        .balign 16
_gp_shst_rs_stub:
        push    eax
        push    ecx
        push    edx
        push    ecx
        call    _gp_shst_rs
        add     esp, 4
        pop     edx
        pop     ecx
        pop     eax
        jmp     dword ptr [_gp_shst_rs_cont]

        .globl _gp_shst_sm_stub
        .balign 16
_gp_shst_sm_stub:
        push    eax
        push    ecx
        push    edx
        call    _gp_shst_sm
        pop     edx
        pop     ecx
        pop     eax
        jmp     dword ptr [_gp_shst_sm_cont]
