/* Game-logic x87 replacements (see p_logic.c for what each original computes and why the SSE
 * version gives the same bits). Common scheme, as in p_quat.S / p_hittest.S:
 *   - SSE only in the game's FPU mode: x87 CW & 0xf3f == 0x3f (PC_24, nearest, all masked) and
 *     MXCSR & 0xffc0 == 0x1f80; otherwise the original x87 code runs;
 *   - MXCSR exception flags cleared first; invalid / divide-by-zero / overflow / underflow, or a
 *     NaN result, means an SSE single result could differ from the 24-bit x87 one, so the
 *     original x87 instructions run instead (on the same inputs; nothing was written yet);
 *   - MXCSR and every xmm register the original does not change are restored; general registers
 *     as the original leaves them (details per entry);
 *   - every call counted; every 64 k calls of an entry, lm_tick calls gp_lm_periodic (60 s log
 *     line) with every register, xmm, x87 and MXCSR state saved around it. */
        .intel_syntax noprefix

        .data
        .balign 4
        .globl _gp_m2q_cont, _gp_m2q_next, _gp_dcc_cont, _gp_dcb_cont, _gp_wcell_cont
        .globl _gp_dcc_x87, _gp_dcb_tail
        .globl _gp_lm_slots
_gp_m2q_cont:   .long 0x00b2bd17    /* after sub esp,0x10; mov ecx,[esp+0x18] */
_gp_m2q_next:   .long 0x00dc39b8    /* the game's next[3] = {1, 2, 0} */
_gp_dcc_cont:   .long 0x00a3a7a6    /* after mov ecx,[esp+8]; mov eax,[ecx] */
_gp_dcb_cont:   .long 0x00a3ae57    /* after push esi; mov esi,[esp+0xc]; mov eax,[esi] */
_gp_wcell_cont: .long 0x006e8cee    /* after push ebp; mov ebp,esp; push ecx; cmp byte [ebp+0xc],0 */
_gp_dcc_x87:    .long 0x00a3a7a9    /* 0xa3a7a0 after its getter call (eax = position) */
_gp_dcb_tail:   .long 0x00a3ae82    /* 0xa3ae50 after its second getter call */
        .balign 64
_gp_lm_slots:   .fill 16*64, 1, 0   /* 16 cache lines: [0..4] calls, [5..9] x87 runs; slot = thread */
        .section .rdata
        .balign 4
lm_one:   .long 0x3f800000          /* 1.0f  (0xbd1908; 1.0 double at 0xbd2c98) */
lm_half:  .long 0x3f000000          /* 0.5f  (0xbd869c; 0.5 double at 0xbd86a0) */
lm_tenth: .long 0x3dcccccd          /* 0.1f  (0xbd83d4) */

        .set LM_M2Q, 0
        .set LM_DCC, 1
        .set LM_DCB, 2
        .set LM_BSPH, 3
        .set LM_WCELL, 4

/* Counters live in one of 16 cache lines chosen by the thread id (TEB+0x24), so threads calling
 * the same entry (the exhaustive tests) do not fight over one line; p_logic.c adds them up.
 * eax = this thread's line */
.macro LMSLOT
        mov     eax, dword ptr fs:[0x24]
        shr     eax, 2
        and     eax, 15
        shl     eax, 6
.endm
/* count a call; every 65536th (per line) runs the periodic logger. Changes eax and EFLAGS */
.macro LMCOUNT k
        LMSLOT
        inc     dword ptr [_gp_lm_slots+eax+4*\k]
        test    word ptr [_gp_lm_slots+eax+4*\k], 0xffff
        jnz     77f
        call    lm_tick
77:
.endm
/* count a run of the x87 original; preserves every register (changes EFLAGS) */
.macro LMX87 k
        push    eax
        LMSLOT
        inc     dword ptr [_gp_lm_slots+eax+20+4*\k]
        pop     eax
.endm

/* game FPU mode or jump to \fail; [esp+\cw] word, [esp+\mx] dword; uses eax */
.macro MODECHECK cw, mx, fail
        fnstcw  word ptr [esp+\cw]
        movzx   eax, word ptr [esp+\cw]
        and     eax, 0x0f3f
        cmp     eax, 0x003f
        jne     \fail
        stmxcsr dword ptr [esp+\mx]
        mov     eax, dword ptr [esp+\mx]
        and     eax, 0xffc0
        cmp     eax, 0x1f80
        jne     \fail
.endm

        .text
/* ---- lm_tick: C call with the whole machine state preserved -------------------------------- */
        .balign 16
lm_tick:
        pushfd
        pushad
        mov     ebp, esp
        sub     esp, 272
        and     esp, -16
        movaps  [esp], xmm0
        movaps  [esp+16], xmm1
        movaps  [esp+32], xmm2
        movaps  [esp+48], xmm3
        movaps  [esp+64], xmm4
        movaps  [esp+80], xmm5
        movaps  [esp+96], xmm6
        movaps  [esp+112], xmm7
        stmxcsr dword ptr [esp+128]
        fnsave  [esp+144]              /* 108 bytes; leaves the FPU initialised */
        call    _gp_lm_periodic
        frstor  [esp+144]
        ldmxcsr dword ptr [esp+128]
        movaps  xmm0, [esp]
        movaps  xmm1, [esp+16]
        movaps  xmm2, [esp+32]
        movaps  xmm3, [esp+48]
        movaps  xmm4, [esp+64]
        movaps  xmm5, [esp+80]
        movaps  xmm6, [esp+96]
        movaps  xmm7, [esp+112]
        mov     esp, ebp
        popad
        popfd
        ret

/* ---- mat2quat: 0xb2bd10, cdecl (Quaternion *ret, const Matrix3D *m), returns eax = ret --------
 * The original leaves eax = ecx = ret, edx = the w bits, xmm0 = (tr, 0, 0, 0) on the trace > 0
 * path or (0.5/s or s, 0, 0, 0) on the other, xmm1 = (the last q[k], 0, 0, 0) on the other path
 * (untouched on the first), and a float in its matrix-pointer argument slot (tr, or s / 0.5/s).
 * All of that is reproduced; ebx esi edi ebp xmm2-7 are preserved.
 * frame: [0] cw [4] mxcsr [8] work [12] slot value [16..31] q [32] esi [36] edi [48..111] xmm0-3
 * args: [esp+116] ret, [esp+120] m */
        .globl _gp_m2q
        .balign 16
_gp_m2q:
        LMCOUNT LM_M2Q
        sub     esp, 112
        MODECHECK 0, 4, 9f
        movups  [esp+48], xmm0
        movups  [esp+64], xmm1
        movups  [esp+80], xmm2
        movups  [esp+96], xmm3
        mov     eax, dword ptr [esp+4]
        and     eax, 0xffffffc0
        mov     dword ptr [esp+8], eax
        ldmxcsr dword ptr [esp+8]      /* flags cleared */
        mov     ecx, dword ptr [esp+120]
        movss   xmm0, dword ptr [ecx+0x14]
        addss   xmm0, dword ptr [ecx]
        addss   xmm0, dword ptr [ecx+0x28]      /* tr = m11 + m00 + m22 (SSE in the original too) */
        xorps   xmm1, xmm1
        comiss  xmm0, xmm1
        jbe     2f                              /* tr <= 0 or NaN */
        movss   dword ptr [esp+12], xmm0
        movaps  xmm2, xmm0
        addss   xmm2, dword ptr [lm_one]
        sqrtss  xmm2, xmm2                      /* s = sqrt(tr + 1) */
        movss   xmm3, dword ptr [lm_half]
        mulss   xmm3, xmm2
        movss   dword ptr [esp+28], xmm3        /* w = s * 0.5 */
        movss   xmm3, dword ptr [lm_half]
        divss   xmm3, xmm2                      /* 0.5 / s */
        movss   xmm2, dword ptr [ecx+0x24]
        subss   xmm2, dword ptr [ecx+0x18]
        mulss   xmm2, xmm3
        movss   dword ptr [esp+16], xmm2        /* x = (m21 - m12) * 0.5/s */
        movss   xmm2, dword ptr [ecx+0x08]
        subss   xmm2, dword ptr [ecx+0x20]
        mulss   xmm2, xmm3
        movss   dword ptr [esp+20], xmm2        /* y = (m02 - m20) * 0.5/s */
        movss   xmm2, dword ptr [ecx+0x10]
        subss   xmm2, dword ptr [ecx+0x04]
        mulss   xmm2, xmm3
        movss   dword ptr [esp+24], xmm2        /* z = (m10 - m01) * 0.5/s */
        movups  xmm1, [esp+64]                  /* this path leaves xmm1 alone */
        jmp     5f
2:      mov     dword ptr [esp+32], esi
        mov     dword ptr [esp+36], edi
        xor     edx, edx                        /* i: the largest diagonal element */
        movss   xmm0, dword ptr [ecx+0x14]
        comiss  xmm0, dword ptr [ecx]
        jbe     3f
        mov     edx, 1
3:      movss   xmm0, dword ptr [ecx+0x28]
        lea     eax, [edx+edx*4]
        comiss  xmm0, dword ptr [ecx+eax*4]
        jbe     4f
        mov     edx, 2
4:      mov     eax, dword ptr [_gp_m2q_next]
        mov     esi, dword ptr [eax+edx*4]      /* j */
        mov     edi, dword ptr [eax+esi*4]      /* k */
        lea     eax, [edi+edi*4]
        movss   xmm1, dword ptr [ecx+eax*4]
        lea     eax, [esi+esi*4]
        addss   xmm1, dword ptr [ecx+eax*4]     /* m_kk + m_jj */
        lea     eax, [edx+edx*4]
        movss   xmm2, dword ptr [ecx+eax*4]
        subss   xmm2, xmm1                      /* m_ii - (m_kk + m_jj) */
        addss   xmm2, dword ptr [lm_one]
        sqrtss  xmm2, xmm2                      /* s */
        movss   xmm3, dword ptr [lm_half]
        mulss   xmm3, xmm2
        movss   dword ptr [esp+16+edx*4], xmm3  /* q[i] = s * 0.5 */
        movaps  xmm0, xmm2
        xorps   xmm3, xmm3
        ucomiss xmm2, xmm3
        jp      6f
        je      7f                              /* s == 0: the original skips the division */
6:      movss   xmm0, dword ptr [lm_half]
        divss   xmm0, xmm2                      /* 0.5 / s */
7:      movss   dword ptr [esp+12], xmm0
        lea     eax, [esi+edi*4]                /* from here the original's own SSE code */
        movss   xmm1, dword ptr [ecx+eax*4]
        lea     eax, [edi+esi*4]
        subss   xmm1, dword ptr [ecx+eax*4]
        mulss   xmm1, xmm0
        movss   dword ptr [esp+28], xmm1        /* w = (m_kj - m_jk) * f */
        lea     eax, [edx+esi*4]
        movss   xmm1, dword ptr [ecx+eax*4]
        lea     eax, [esi+edx*4]
        addss   xmm1, dword ptr [ecx+eax*4]
        mulss   xmm1, xmm0
        movss   dword ptr [esp+16+esi*4], xmm1  /* q[j] = (m_ji + m_ij) * f */
        lea     eax, [edx+edi*4]
        movss   xmm1, dword ptr [ecx+eax*4]
        lea     eax, [edi+edx*4]
        addss   xmm1, dword ptr [ecx+eax*4]
        mulss   xmm1, xmm0
        movss   dword ptr [esp+16+edi*4], xmm1  /* q[k] = (m_ki + m_ik) * f */
        mov     esi, dword ptr [esp+32]
        mov     edi, dword ptr [esp+36]
5:      stmxcsr dword ptr [esp+8]
        test    byte ptr [esp+8], 0x1d          /* IE ZE OE UE */
        jnz     8f
        movups  xmm2, [esp+16]
        cmpunordps xmm2, xmm2
        movmskps eax, xmm2
        test    eax, eax
        jnz     8f                              /* a NaN result: payload rules differ */
        ldmxcsr dword ptr [esp+4]
        movups  xmm2, [esp+80]
        movups  xmm3, [esp+96]
        mov     eax, dword ptr [esp+116]
        mov     edx, dword ptr [esp+16]
        mov     dword ptr [eax], edx
        mov     edx, dword ptr [esp+20]
        mov     dword ptr [eax+4], edx
        mov     edx, dword ptr [esp+24]
        mov     dword ptr [eax+8], edx
        mov     edx, dword ptr [esp+28]
        mov     dword ptr [eax+12], edx
        mov     ecx, dword ptr [esp+12]
        mov     dword ptr [esp+120], ecx
        mov     ecx, eax
        add     esp, 112
        ret
8:      ldmxcsr dword ptr [esp+4]
        movups  xmm0, [esp+48]
        movups  xmm1, [esp+64]
        movups  xmm2, [esp+80]
        movups  xmm3, [esp+96]
9:      LMX87 LM_M2Q
        add     esp, 112
        sub     esp, 0x10                       /* the two instructions the jmp replaced */
        mov     ecx, dword ptr [esp+0x18]
        jmp     dword ptr [_gp_m2q_cont]

/* ---- distcalc centre 2D: 0xa3a7a0, cdecl (const Coord3D *p, const Object *obj, int) -> st0 ------
 * dx*dx + dy*dy of obj->getPosition() (vtable slot 1) - p. The original leaves eax = position,
 * ecx = p, edx = the getter's edx: the same here (nothing after the getter touches edx).
 * frame: [0] cw [4] mxcsr [8] work [12] result [16] xmm0 [32] xmm1; args [esp+52] p, [esp+56] obj */
        .globl _gp_dc_center2d
        .balign 16
_gp_dc_center2d:
        LMCOUNT LM_DCC
        sub     esp, 48
        MODECHECK 0, 4, 9f
        mov     eax, dword ptr [esp+4]
        and     eax, 0xffffffc0
        mov     dword ptr [esp+8], eax
        mov     ecx, dword ptr [esp+56]
        mov     eax, dword ptr [ecx]
        call    dword ptr [eax+4]               /* getPosition */
        mov     ecx, dword ptr [esp+52]
        movups  [esp+16], xmm0
        movups  [esp+32], xmm1
        ldmxcsr dword ptr [esp+8]
        movss   xmm0, dword ptr [eax+4]
        subss   xmm0, dword ptr [ecx+4]         /* dy */
        movss   xmm1, dword ptr [eax]
        subss   xmm1, dword ptr [ecx]           /* dx */
        mulss   xmm1, xmm1
        mulss   xmm0, xmm0
        addss   xmm1, xmm0                      /* dx*dx + dy*dy */
        ucomiss xmm1, xmm1
        jp      8f
        stmxcsr dword ptr [esp+8]
        test    byte ptr [esp+8], 0x1d
        jnz     8f
        movss   dword ptr [esp+12], xmm1
        ldmxcsr dword ptr [esp+4]
        movups  xmm0, [esp+16]
        movups  xmm1, [esp+32]
        fld     dword ptr [esp+12]
        add     esp, 48
        ret
8:      ldmxcsr dword ptr [esp+4]               /* the original's x87 code after its getter call */
        movups  xmm0, [esp+16]
        movups  xmm1, [esp+32]
        LMX87 LM_DCC
        add     esp, 48
        jmp     dword ptr [_gp_dcc_x87]         /* eax = position, as there */
9:      LMX87 LM_DCC
        add     esp, 48
        mov     ecx, dword ptr [esp+8]          /* the two instructions the jmp replaced */
        mov     eax, dword ptr [ecx]
        jmp     dword ptr [_gp_dcc_cont]

/* ---- distcalc bounding circle 2D: 0xa3ae50, cdecl (const Coord3D *p, const Object *obj, int) ---
 * d = sqrt(dx*dx + dy*dy) - obj->getGeometryInfo()->radius (vtable slot 0, +0x10); returns
 * d*d, negated when d < 0. Both getters are called first, in the original order and the same
 * way; everything after them is left as the original leaves it: ecx, edx and xmm0-7 as the
 * second getter left them, d2 in the object-pointer argument slot, esi. eax: the original leaves
 * the FPU status word of its sign test in ax, here eax = the geometry pointer; 0xa3ae50 is only
 * called through the distance-proc table 0xdbdaf8 (never directly), so no caller can use it.
 * Fallbacks: the original's own x87 d2 instructions (0xa3ae5c..0xa3ae7e without the getter
 * call) and/or its tail after the second getter (0xa3ae82).
 * frame: [0] cw [4] mxcsr [8] work [12] esi [16] position [20] result [24] xmm0 [40] xmm1
 *        [56] ecx [60] edx [64] tmp; args [esp+72] p, [esp+76] obj */
        .globl _gp_dc_bound2d
        .balign 16
_gp_dc_bound2d:
        LMCOUNT LM_DCB
        sub     esp, 68
        MODECHECK 0, 4, 9f
        mov     eax, dword ptr [esp+4]
        and     eax, 0xffffffc0
        mov     dword ptr [esp+8], eax
        mov     dword ptr [esp+12], esi
        mov     esi, dword ptr [esp+76]
        mov     eax, dword ptr [esi]
        mov     ecx, esi
        call    dword ptr [eax+4]               /* getPosition */
        mov     dword ptr [esp+16], eax
        mov     edx, dword ptr [esi]
        mov     ecx, esi
        call    dword ptr [edx]                 /* getGeometryInfo: eax */
        mov     dword ptr [esp+56], ecx
        mov     dword ptr [esp+60], edx
        movups  [esp+24], xmm0
        movups  [esp+40], xmm1
        ldmxcsr dword ptr [esp+8]
        mov     edx, dword ptr [esp+16]
        mov     ecx, dword ptr [esp+72]
        movss   xmm0, dword ptr [edx+4]
        subss   xmm0, dword ptr [ecx+4]         /* dy */
        movss   xmm1, dword ptr [edx]
        subss   xmm1, dword ptr [ecx]           /* dx */
        mulss   xmm1, xmm1
        mulss   xmm0, xmm0
        addss   xmm1, xmm0                      /* d2 */
        ucomiss xmm1, xmm1
        jp      7f
        stmxcsr dword ptr [esp+64]
        test    byte ptr [esp+64], 0x1d
        jnz     7f
        movss   dword ptr [esp+76], xmm1        /* d2 into the object-pointer slot, as the original */
        sqrtss  xmm0, xmm1
        subss   xmm0, dword ptr [eax+0x10]      /* d */
        movaps  xmm1, xmm0
        mulss   xmm1, xmm0                      /* d*d */
        ucomiss xmm1, xmm1
        jp      6f
        stmxcsr dword ptr [esp+64]
        test    byte ptr [esp+64], 0x1d
        jnz     6f
        movss   dword ptr [esp+64], xmm0
        movss   dword ptr [esp+20], xmm1
        cmp     dword ptr [esp+64], 0x80000000  /* d < 0 (sign set, not -0; NaN excluded above) */
        jbe     5f
        xor     byte ptr [esp+23], 0x80
5:      ldmxcsr dword ptr [esp+4]
        movups  xmm0, [esp+24]
        movups  xmm1, [esp+40]
        mov     ecx, dword ptr [esp+56]
        mov     edx, dword ptr [esp+60]
        mov     esi, dword ptr [esp+12]
        fld     dword ptr [esp+20]
        add     esp, 68
        ret
7:      ldmxcsr dword ptr [esp+4]               /* d2 as the original computes it */
        movups  xmm0, [esp+24]
        movups  xmm1, [esp+40]
        mov     edx, dword ptr [esp+16]
        mov     ecx, dword ptr [esp+72]
        fld     dword ptr [edx+4]
        fsub    dword ptr [ecx+4]
        fld     dword ptr [edx]
        fsub    dword ptr [ecx]
        fld     st(0)
        fmul    st, st(1)
        fld     st(2)
        fmul    st, st(3)
        faddp   st(1), st
        fstp    dword ptr [esp+76]
        fstp    st(0)
        fstp    st(0)
        jmp     8f
6:      ldmxcsr dword ptr [esp+4]
        movups  xmm0, [esp+24]
        movups  xmm1, [esp+40]
8:      LMX87 LM_DCB
        mov     ecx, dword ptr [esp+56]
        mov     edx, dword ptr [esp+60]
        mov     esi, dword ptr [esp+12]
        add     esp, 68
        push    esi                             /* the tail pops it */
        jmp     dword ptr [_gp_dcb_tail]        /* eax = geometry, d2 in the slot */
9:      LMX87 LM_DCB
        add     esp, 68
        push    esi                             /* the three instructions the jmp replaced */
        mov     esi, dword ptr [esp+0xc]
        mov     eax, dword ptr [esi]
        jmp     dword ptr [_gp_dcb_cont]

/* ---- bsphere: called from 0x59bcb9 in place of flds [esp+0x20]; fsqrt; fstps [esp] -----------
 * Preserves every register and MXCSR; xmm0's low float is the root (the next original
 * instruction reloads xmm0 from [esp] anyway). sqrtss is the correctly rounded single root,
 * as is fsqrt at 24-bit precision for every float input (NaN, negative, denormal included). */
        .globl _gp_bsph
        .balign 16
_gp_bsph:
        push    eax
        LMCOUNT LM_BSPH
        sub     esp, 8                          /* r2 at [esp+0x30], the result at [esp+0x10] */
        MODECHECK 0, 4, 1f
        sqrtss  xmm0, dword ptr [esp+0x30]
        movss   dword ptr [esp+0x10], xmm0
        ldmxcsr dword ptr [esp+4]
        add     esp, 8
        pop     eax
        ret
1:      LMX87 LM_BSPH
        fld     dword ptr [esp+0x30]
        fsqrt
        fstp    dword ptr [esp+0x10]
        add     esp, 8
        pop     eax
        ret

/* ---- worldcell: 0x6e8ce6, cdecl (int out[2], bool exact, const Coord3D *p) -------------------
 * out = (int)floor(x * 0.1f [+ 0.5f]), same for y (+ 0.5f when exact == 0). The original
 * leaves eax = out, ecx = out[1], edx = whatever floor left (gp_floor: untouched, as here), and
 * floor(y) as a float in its `exact` argument slot.
 * floor of an integral-valued float and its round-to-nearest conversion are exact; an
 * out-of-range or NaN value gives 0x80000000 in both fistp and cvtss2si (NaN still goes to the
 * original: its float in the argument slot depends on the CRT's floor).
 * frame: [0] cw [4] mxcsr [8] work [12] xmm0 [28] xmm1; args [esp+48] out, [esp+52] exact, [esp+56] p */
        .globl _gp_wcell
        .balign 16
_gp_wcell:
        LMCOUNT LM_WCELL
        sub     esp, 44
        MODECHECK 0, 4, 9f
        mov     eax, dword ptr [esp+4]
        and     eax, 0xffffffc0
        mov     dword ptr [esp+8], eax
        movups  [esp+12], xmm0
        movups  [esp+28], xmm1
        ldmxcsr dword ptr [esp+8]
        mov     eax, dword ptr [esp+56]
        movss   xmm0, dword ptr [eax]
        mulss   xmm0, dword ptr [lm_tenth]
        movss   xmm1, dword ptr [eax+4]
        mulss   xmm1, dword ptr [lm_tenth]
        cmp     byte ptr [esp+52], 0
        jne     1f
        addss   xmm0, dword ptr [lm_half]
        addss   xmm1, dword ptr [lm_half]
1:      ucomiss xmm0, xmm0
        jp      8f
        ucomiss xmm1, xmm1
        jp      8f
        stmxcsr dword ptr [esp+8]
        test    byte ptr [esp+8], 0x1d
        jnz     8f
        roundss xmm0, xmm0, 9                   /* floor, no precision exception */
        roundss xmm1, xmm1, 9
        movss   dword ptr [esp+52], xmm1
        mov     eax, dword ptr [esp+48]
        cvtss2si ecx, xmm0
        mov     dword ptr [eax], ecx
        cvtss2si ecx, xmm1
        mov     dword ptr [eax+4], ecx
        ldmxcsr dword ptr [esp+4]
        movups  xmm0, [esp+12]
        movups  xmm1, [esp+28]
        add     esp, 44
        ret
8:      ldmxcsr dword ptr [esp+4]
        movups  xmm0, [esp+12]
        movups  xmm1, [esp+28]
9:      LMX87 LM_WCELL
        add     esp, 44
        push    ebp                             /* the four instructions the jmp replaced */
        mov     ebp, esp
        push    ecx
        cmp     byte ptr [ebp+0xc], 0
        jmp     dword ptr [_gp_wcell_cont]

