/* phasebalance stubs (p_phasebal.c). Each patched site in GameLogic::update 0x62e4e8 is a `jmp` to
 * one of these; each ends in a `jmp` to one of the original continuations (gp_pb_cont, relocated).
 * The function keeps GameLogic in esi, the phase argument at [ebp+8], the list index at [ebp-0x18],
 * the end list at [ebp-0x20], the list vector (begin, end, capacity) in edi inside the list loop
 * and the element index at [ebp-0x1c]. At every site the original code clobbers eax, ecx and edx
 * and nothing after the site reads them (checked per site in p_phasebal.c), so the stubs may too;
 * ebx, esi, edi, ebp are kept (the C functions are cdecl and preserve them). GameLogic::update holds
 * nothing in x87 or xmm registers. */
        .intel_syntax noprefix
        .text

/* 0x62e982 (0x48 bytes: phase <= 2 test and the phase -> lists dispatch). Sets edi, [ebp-0x18]
 * = first list and [ebp-0x20] = end list and goes to the list loop 0x62e9ca, or to the AI test. */
        .globl _gp_pb_s_lists
        .balign 16
_gp_pb_s_lists:
        sub     esp, 8                  /* out[0] first, out[1] end */
        mov     eax, esp
        push    eax
        push    dword ptr [ebp+8]
        push    esi
        call    _gp_pb_c_lists
        add     esp, 12
        pop     edi
        pop     edx
        test    eax, eax
        jz      _gp_pb_s_ai
        mov     [ebp-0x18], edi
        mov     [ebp-0x20], edx
        jmp     dword ptr [_gp_pb_cont+0]      /* 0x62e9ca */

/* 0x62e9d4 (22 bytes: the start index by phase). eax = start - 1, then 0x62e9ea. */
        .globl _gp_pb_s_start
        .balign 16
_gp_pb_s_start:
        push    dword ptr [ebp-0x18]
        push    edi
        push    dword ptr [ebp+8]
        push    esi
        call    _gp_pb_c_start
        add     esp, 16
        dec     eax
        jmp     dword ptr [_gp_pb_cont+4]      /* 0x62e9ea */

/* 0x62ea09 (27 bytes: phase 3 stops list 0 at size / 2). eax = the element index. The stores and
 * the compare are the fast path (one per update-list element); past gp_pb_stop_at the C side
 * decides and records where the pass stopped. */
        .globl _gp_pb_s_stop
        .balign 16
_gp_pb_s_stop:
        mov     [ebp-0x1c], eax
        cmp     eax, [_gp_pb_stop_at]
        jae     1f
        jmp     dword ptr [_gp_pb_cont+8]      /* 0x62ea24: update this element */
1:      push    eax
        push    edi
        push    dword ptr [ebp-0x18]
        push    dword ptr [ebp+8]
        push    esi
        call    _gp_pb_c_stop
        add     esp, 20
        test    eax, eax
        jnz     2f
        jmp     dword ptr [_gp_pb_cont+8]      /* 0x62ea24 */
2:      jmp     dword ptr [_gp_pb_cont+12]     /* 0x62eb51: next list, no clean-up */

/* 0x62eadf (6 bytes: clean-up when phase > 3). The pass reached the list's end. */
        .globl _gp_pb_s_end
        .balign 16
_gp_pb_s_end:
        push    edi
        push    dword ptr [ebp-0x18]
        push    dword ptr [ebp+8]
        push    esi
        call    _gp_pb_c_end
        add     esp, 16
        test    eax, eax
        jz      1f
        jmp     dword ptr [_gp_pb_cont+16]     /* 0x62eae5: move sleepers to the sleep list */
1:      jmp     dword ptr [_gp_pb_cont+12]     /* 0x62eb51 */

/* 0x62eb63 (6 bytes: TheAI update in phase 5). 2: TheAI then the pending-object pass 0x629da6,
 * 1: only 0x629da6, 0: neither. */
        .globl _gp_pb_s_ai
        .balign 16
_gp_pb_s_ai:
        push    dword ptr [ebp+8]
        push    esi
        call    _gp_pb_c_ai
        add     esp, 8
        cmp     eax, 1
        ja      2f
        je      1f
        jmp     _gp_pb_s_sub
1:      jmp     dword ptr [_gp_pb_cont+24]     /* 0x62eb74: mov ecx, esi; call 0x629da6 */
2:      jmp     dword ptr [_gp_pb_cont+20]     /* 0x62eb69: TheAI, then 0x629da6 */

/* 0x62eb7b (10 bytes: the twelve phase-5 subsystems). */
        .globl _gp_pb_s_sub
        .balign 16
_gp_pb_s_sub:
        push    dword ptr [ebp+8]
        push    esi
        call    _gp_pb_c_sub
        add     esp, 8
        test    eax, eax
        jz      _gp_pb_s_reenter
        jmp     dword ptr [_gp_pb_cont+28]     /* 0x62eb85 */

/* 0x62ec10 (7 bytes: mov ecx, esi; call 0x441b60). A second round of the list loop (list 3 after
 * the subsystems) when the plan asks for one, else the replaced instructions. */
        .globl _gp_pb_s_reenter
        .balign 16
_gp_pb_s_reenter:
        sub     esp, 8
        mov     eax, esp
        push    eax
        push    dword ptr [ebp+8]
        push    esi
        call    _gp_pb_c_reenter
        add     esp, 12
        pop     edx
        pop     ecx
        test    eax, eax
        jz      1f
        mov     edi, edx
        mov     [ebp-0x18], edx
        mov     [ebp-0x20], ecx
        jmp     dword ptr [_gp_pb_cont+0]      /* 0x62e9ca */
1:      mov     ecx, esi
        call    dword ptr [_gp_pb_cont+36]     /* 0x441b60 */
        jmp     dword ptr [_gp_pb_cont+32]     /* 0x62ec17 */
