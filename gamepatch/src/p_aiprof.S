/* aiprof stubs (p_aiprof.c). Counters only. A site's `call target` becomes `call _gp_ap_sK`: the stub
 * reads the time stamp counter, calls the target with copies of its stack arguments and the caller's
 * eax, ecx, edx (xmm and x87 untouched), adds the ticks and a call to site K, and returns the target's
 * eax and edx, popping the arguments when the target does. ebx, esi, edi, ebp are never touched. An
 * exception through a stub only loses that one count (no state is kept outside the stub's frame).
 * _gp_ap_state replaces `mov ebx, ecx; call [eax+0x18]` in StateMachine::updateStateMachine (the
 * current state's update) and adds the ticks under the state's vtable. */
        .intel_syntax noprefix
        .text

/* SITE k, n, pops: n stack arguments, pops = 1 if the target pops them (ret 4n) */
.macro SITE k, n, pops
        .globl _gp_ap_s\k
        .balign 16
_gp_ap_s\k:
        push    eax
        push    edx
        rdtsc
        push    edx                     /* t0: [esp] low, [esp+4] high; the caller's edx [esp+8], eax [esp+12] */
        push    eax
        mov     eax, [esp+12]
        mov     edx, [esp+8]
        .rept   \n
        push    dword ptr [esp+20+4*(\n-1)]
        .endr
        call    dword ptr [_gp_ap_target+4*\k]
        .if \pops == 0 && \n > 0
        add     esp, 4*\n
        .endif
        mov     [esp+12], eax
        mov     [esp+8], edx
        rdtsc
        sub     eax, [esp]
        sbb     edx, [esp+4]
        add     dword ptr [_gp_ap_ticks+8*\k], eax
        adc     dword ptr [_gp_ap_ticks+8*\k+4], edx
        inc     dword ptr [_gp_ap_calls+4*\k]
        add     esp, 8
        pop     edx
        pop     eax
        .if \pops
        ret     4*\n
        .else
        ret
        .endif
.endm

        SITE    0, 0, 0                 /* AnimalAI: AIUpdateInterface::update */
        SITE    1, 1, 1                 /* AnimalAI: isReachableLayer */
        SITE    2, 4, 1                 /* AnimalAI: flee scan */
        SITE    3, 4, 1                 /* AnimalAI: wander emitter scan */
        SITE    4, 2, 1                 /* AnimalAI: move order */
        SITE    5, 0, 0                 /* AI: 0x6695ef */
        SITE    6, 0, 0                 /* AI: 0x66c748 */
        SITE    7, 0, 0                 /* AI: 0x665921 */
        SITE    8, 0, 0                 /* AI: 0x66217e */
        SITE    9, 1, 1                 /* AI: 0x756cd7, first */
        SITE    10, 1, 1                /* AI: 0x756cd7, second */
        SITE    11, 2, 1                /* AI: setStatus, first */
        SITE    12, 2, 1                /* AI: setStatus, second */
        SITE    13, 2, 1                /* AI main: 0x6658d3 */
        SITE    14, 0, 0                /* AI main: 0x663e32 */
        SITE    15, 2, 1                /* FireWeaponUpdate: forceFireWeapon */
        SITE    16, 2, 1                /* FireWeaponUpdate: forceFireWeapon, nugget list */
        SITE    17, 6, 1                /* DamageNugget: radius scan */
        SITE    18, 0, 0                /* AI: 0x664f93 */
        SITE    19, 0, 0                /* AI main: the state machine's update (vt+0x10, by the caller's site) */
        SITE    20, 3, 0                /* test only: a cdecl target with three arguments */

/* StateMachine::updateStateMachine 0x8db70b: mov ebx, ecx; call [eax+0x18] (eax = the state's vtable) */
        .globl _gp_ap_state
        .balign 16
_gp_ap_state:
        mov     ebx, ecx                /* the replaced instruction: ebx is the caller's */
        push    eax                     /* [esp+12] after the next three: the vtable, then the result */
        push    edx
        rdtsc
        push    edx
        push    eax
        mov     eax, [esp+12]
        mov     edx, [esp+8]
        call    dword ptr [eax+0x18]
        mov     [esp+8], edx
        mov     edx, [esp+12]           /* the vtable */
        mov     [esp+12], eax
        push    ecx
        push    edx                     /* vt */
        rdtsc
        sub     eax, [esp+8]
        sbb     edx, [esp+12]
        push    edx
        push    eax
        call    _gp_ap_state_acc        /* (lo, hi, vt) cdecl */
        add     esp, 12
        pop     ecx
        add     esp, 8
        pop     edx
        pop     eax
        ret
