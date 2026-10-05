/* t_lstats: logicstats (p_lstats.c/.S) against the original exe.
 *  [1] the patch applies to the original bytes (GameLogic::update by hash, the 19 subsystem call
 *      sequences, the 6 direct calls, the update-module call, the two vtable slots) and writes a
 *      call to its stub at each call site (+ a 2-byte nop at the module site) and the logic stub
 *      into both vtable slots; the continuations are the originals;
 *  [2] the logic stub (thiscall, phase argument, ret 4): the original sees every register, xmm0-7
 *      and the phase as the caller set them; the caller gets the original's eax, ecx, edx, xmm0-7,
 *      ebx esi edi ebp unchanged and the stack as the original leaves it; one call and a positive
 *      time in that phase; the first call hooks vt+0x28 of the objects in the subsystem globals
 *      (two globals sharing one vtable are hooked once);
 *  [3] the subsystem stubs (through the hooked slots) and the six direct-call stubs: the same
 *      register/stack contract (0 arguments ret, 0x6260e1 1 argument ret 4), counted in the phase
 *      in effect;
 *  [4] the module stub: the callee gets eax = the vtable, ecx = ebx+0x10, edx and xmm0-7 as the
 *      caller had them, exactly as the original lea/mov/call; the caller gets the callee's eax, ecx,
 *      edx, xmm0-7, ebx esi edi ebp unchanged, esp unchanged; counted under that vtable;
 *  [5] the cost of one timed module call over the original sequence, in ns.
 * usage: t_lstats.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include "gp_logic.h"
#include <stdio.h>
#include <string.h>

static uint32_t OFF;
void gp_lst_begin(int ph);
void gp_lst_end(uint32_t, uint32_t, uint32_t, uint32_t);

/* ---- generic caller (up to 4 stack arguments) and recording callees (as t_rstats [4]) ---- */
uint32_t g_target, g_nargs, g_args[4], g_in[7], g_out[7], g_saved_esp; int32_t g_esp_delta;
uint8_t g_xin[128], g_xout[128], g_xret[128], g_xseen[128];
uint32_t c_eax, c_ecx, c_edx, c_args[4];
void g_call(void); void t_callee0(void); void t_callee4(void); void t_null0(void); void t_mod_orig(void);
#define CALLEE_BODY(n) \
        "  mov [_c_eax], eax\n  mov [_c_ecx], ecx\n  mov [_c_edx], edx\n" \
        "  mov eax, [esp+4]\n  mov [_c_args], eax\n  mov eax, [esp+8]\n  mov [_c_args+4], eax\n" \
        "  movups [_g_xseen], xmm0\n  movups [_g_xseen+16], xmm1\n  movups [_g_xseen+32], xmm2\n" \
        "  movups [_g_xseen+48], xmm3\n  movups [_g_xseen+64], xmm4\n  movups [_g_xseen+80], xmm5\n" \
        "  movups [_g_xseen+96], xmm6\n  movups [_g_xseen+112], xmm7\n" \
        "  mov ecx, 20000\n1" n ": dec ecx\n  jnz 1" n "b\n" \
        "  movups xmm0, [_g_xret]\n  movups xmm1, [_g_xret+16]\n  movups xmm2, [_g_xret+32]\n" \
        "  movups xmm3, [_g_xret+48]\n  movups xmm4, [_g_xret+64]\n  movups xmm5, [_g_xret+80]\n" \
        "  movups xmm6, [_g_xret+96]\n  movups xmm7, [_g_xret+112]\n" \
        "  mov eax, 0xa0a0a0a0\n  mov ecx, 0xc0c0c0c0\n  mov edx, 0xd0d0d0d0\n"
__asm__(".intel_syntax noprefix\n.text\n"
        ".globl _g_call\n_g_call:\n  push ebx\n  push esi\n  push edi\n  push ebp\n  mov [_g_saved_esp], esp\n"
        "  movups xmm0, [_g_xin]\n  movups xmm1, [_g_xin+16]\n  movups xmm2, [_g_xin+32]\n  movups xmm3, [_g_xin+48]\n"
        "  movups xmm4, [_g_xin+64]\n  movups xmm5, [_g_xin+80]\n  movups xmm6, [_g_xin+96]\n  movups xmm7, [_g_xin+112]\n"
        "  mov ecx, [_g_nargs]\n"
        "2: test ecx, ecx\n  jz 3f\n  push dword ptr [_g_args-4+ecx*4]\n  dec ecx\n  jmp 2b\n"
        "3: mov eax, [_g_in]\n  mov ebx, [_g_in+4]\n  mov ecx, [_g_in+8]\n  mov edx, [_g_in+12]\n"
        "  mov esi, [_g_in+16]\n  mov edi, [_g_in+20]\n  mov ebp, [_g_in+24]\n"
        "  call dword ptr [_g_target]\n"
        "  mov [_g_out], eax\n  mov [_g_out+4], ebx\n  mov [_g_out+8], ecx\n  mov [_g_out+12], edx\n"
        "  mov [_g_out+16], esi\n  mov [_g_out+20], edi\n  mov [_g_out+24], ebp\n"
        "  movups [_g_xout], xmm0\n  movups [_g_xout+16], xmm1\n  movups [_g_xout+32], xmm2\n  movups [_g_xout+48], xmm3\n"
        "  movups [_g_xout+64], xmm4\n  movups [_g_xout+80], xmm5\n  movups [_g_xout+96], xmm6\n  movups [_g_xout+112], xmm7\n"
        "  mov eax, esp\n  sub eax, [_g_saved_esp]\n  mov [_g_esp_delta], eax\n"
        "  mov esp, [_g_saved_esp]\n  pop ebp\n  pop edi\n  pop esi\n  pop ebx\n  ret\n"
        ".globl _t_callee0\n_t_callee0:\n" CALLEE_BODY("0") "  ret\n"
        ".globl _t_callee4\n_t_callee4:\n" CALLEE_BODY("1") "  ret 4\n"
        ".globl _t_null0\n_t_null0:\n  ret\n"
        /* the original module-call sequence at 0x62ea97, for [5] */
        ".globl _t_mod_orig\n_t_mod_orig:\n  lea ecx, [ebx+0x10]\n  mov eax, [ecx]\n  call dword ptr [eax]\n  ret\n"
        ".att_syntax\n");

static const uint32_t in[7] = {0x11111111, 0x33333333, 0x0c0c0c0c, 0x22222222, 0x55555555, 0x66666666, 0x77777777};

static void setup(uint32_t target, int pushed)
{
    for (int i = 0; i < 128; i++) { g_xin[i] = (uint8_t)(0x6b ^ i * 29); g_xret[i] = (uint8_t)(0x17 ^ i * 53); }
    memset(g_xseen, 0, sizeof g_xseen); memset(g_xout, 0, sizeof g_xout);
    memcpy(g_in, in, sizeof g_in);
    for (int i = 0; i < 4; i++) g_args[i] = 0x9a000000u + 0x010101u * (i + 1);
    g_nargs = (uint32_t)pushed; c_eax = c_ecx = c_edx = 0; memset(c_args, 0, sizeof c_args);
    g_target = target;
}

/* the contract of a timed stub: callee sees the caller's registers/args, caller gets the callee's */
static int contract(int nargs, int callee_pops, uint32_t want_eax, uint32_t want_ecx, uint32_t want_edx)
{
    int bad = c_eax != want_eax || c_ecx != want_ecx || c_edx != want_edx || memcmp(g_xseen, g_xin, 128);
    for (int i = 0; i < nargs; i++) bad |= c_args[i] != g_args[i];
    bad |= g_out[0] != 0xa0a0a0a0 || g_out[2] != 0xc0c0c0c0 || g_out[3] != 0xd0d0d0d0 || memcmp(g_xout, g_xret, 128);
    bad |= g_out[1] != g_in[1] || g_out[4] != in[4] || g_out[5] != in[5] || g_out[6] != in[6];
    bad |= g_esp_delta != callee_pops - 4 * nargs;
    return bad;
}

static int counted(int kind, int ph, LONG c0, uint64_t t0)
{
    LONG c1; uint64_t t1;
    gp_lst_get(kind, ph, &c1, &t1);
    return c1 == c0 + 1 && t1 > t0;
}

static uint32_t fake_vt[19][16], fake_obj[19][4];

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    MEMORY_BASIC_INFORMATION mi;
    VirtualQuery((void *)0xde0000, &mi, sizeof mi);
    if (mi.State == MEM_FREE && !VirtualAlloc((void *)0xde0000, 0x10000, MEM_RESERVE, PAGE_READWRITE)) {
        printf("cannot reserve 00de0000\n"); return 2;
    }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xde3000, 0x6000, 0)) return 2;            /* the subsystem globals */
    if (!(OFF = orig_reserve_image())) return 2;
    static const uint32_t pages[] = {0x62e000, 0xbd8000, 0xbfd000};
    for (unsigned i = 0; i < sizeof pages / 4; i++) if (orig_map_at(pages[i], 0x1000, OFF)) return 2;
    static const uint32_t globals[19] = {0xde3bac, 0xde7804, 0xde7cd8, 0xde46a8, 0xde772c, 0xde4354, 0xde4360,
        0xde4b40, 0xde4358, 0xde435c, 0xde8200, 0xde3be8, 0xde4a1c, 0xde369c, 0xde89ac, 0xde8ac0, 0xde4938,
        0xde7924, 0xde8304};
    for (int i = 0; i < 19; i++) {     /* objects 5 and 6 share one class (vtable 5) */
        int v = i == 6 ? 5 : i;
        fake_vt[v][0x28 / 4] = (uint32_t)(uintptr_t)t_callee0;
        fake_obj[i][0] = (uint32_t)(uintptr_t)fake_vt[v];
        *(uint32_t *)(uintptr_t)globals[i] = (uint32_t)(uintptr_t)fake_obj[i];
    }

    int fail = 0;
    gp_va_offset = OFF;
    int ok = gp_patch_logicstats();
    gp_va_offset = 0;
    static const uint32_t calls[6] = {0x62e8cf, 0x62e8da, 0x62e96f, 0x62eb76, 0x62ebb3, 0x62ebea};
    static const uint32_t callees[6] = {0x820ef0, 0x81be85, 0x6260e1, 0x629da6, 0x62a2c9, 0x80f4d3};
    void (*const cstub[6])(void) = {gp_lst_call0, gp_lst_call1, gp_lst_call2, gp_lst_call3, gp_lst_call4, gp_lst_call5};
    int wrong = 0;
    for (int i = 0; i < 6; i++) {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(calls[i] + OFF);
        int32_t rel; memcpy(&rel, p + 1, 4);
        wrong += p[0] != 0xe8 || (uint32_t)(uintptr_t)(p + 5) + (uint32_t)rel != (uint32_t)(uintptr_t)cstub[i];
        wrong += gp_lst_cont[24 + i] != callees[i] + OFF;
    }
    const uint8_t *m = (const uint8_t *)(uintptr_t)(0x62ea97 + OFF);
    int32_t rel; memcpy(&rel, m + 1, 4);
    wrong += m[0] != 0xe8 || (uint32_t)(uintptr_t)(m + 5) + (uint32_t)rel != (uint32_t)(uintptr_t)gp_lst_mod_stub ||
             m[5] != 0x66 || m[6] != 0x90;
    uint32_t slot;
    memcpy(&slot, (const void *)(uintptr_t)(0xbd85c4 + OFF), 4); wrong += slot != (uint32_t)(uintptr_t)gp_lst_logic_stub;
    memcpy(&slot, (const void *)(uintptr_t)(0xbfdb9c + OFF), 4); wrong += slot != (uint32_t)(uintptr_t)gp_lst_logic_stub;
    wrong += gp_lst_logic_cont != 0x62e4e8 + OFF;
    printf("[1] logicstats applied to the original bytes: %s; 7 call sites and 2 vtable slots point at the stubs, "
           "continuations at the originals: %s\n", ok ? "yes" : "NO", wrong ? "NO" : "yes");
    fail |= !ok || wrong;
    if (!ok) { printf("FAIL\n"); return 1; }

    /* [2] the logic stub, phases 1..6 (the original replaced by a recording callee) */
    uint32_t keep = gp_lst_logic_cont;
    gp_lst_logic_cont = (uint32_t)(uintptr_t)t_callee4;
    int bad = 0, cbad = 0;
    for (int ph = 1; ph <= 6; ph++) {
        LONG c0; uint64_t t0;
        gp_lst_get(-1, ph, &c0, &t0);
        setup((uint32_t)(uintptr_t)gp_lst_logic_stub, 1);
        g_args[0] = (uint32_t)ph;
        g_call();
        bad |= contract(1, 4, in[0], in[2], in[3]);
        cbad |= !counted(-1, ph, c0, t0);
    }
    gp_lst_logic_cont = keep;
    int hooked = 0;
    for (int i = 0; i < 19; i++) {
        int v = i == 6 ? 5 : i;
        hooked += gp_lst_sub_slot[i] == (uint32_t)(uintptr_t)&fake_vt[v][10] &&
                  (i == 6 || (fake_vt[v][10] != (uint32_t)(uintptr_t)t_callee0 && gp_lst_cont[i] == (uint32_t)(uintptr_t)t_callee0));
    }
    printf("[2] logic stub, phases 1-6: registers, xmm0-7, phase argument, stack %s; counted per phase %s; "
           "subsystem slots hooked %d of 19 (one shared)\n", bad ? "WRONG" : "as the original's", cbad ? "WRONG" : "right", hooked);
    fail |= bad || cbad || hooked != 19;

    /* [3] subsystem stubs through the hooked slots, and the direct-call stubs, inside phase 5 */
    bad = cbad = 0;
    for (int i = 0; i < 19; i++) {
        if (i == 6) continue;
        LONG c0; uint64_t t0;
        gp_lst_get(i, 5, &c0, &t0);
        gp_lst_begin(5);
        setup(fake_vt[i][10], 0);
        g_call();
        gp_lst_end(0, 0, 0, 0);
        bad |= contract(0, 0, in[0], in[2], in[3]);
        cbad |= !counted(i, 5, c0, t0);
    }
    for (int i = 0; i < 6; i++) {
        int na = i == 2;
        uint32_t k = gp_lst_cont[24 + i];
        gp_lst_cont[24 + i] = (uint32_t)(uintptr_t)(na ? t_callee4 : t_callee0);
        LONG c0; uint64_t t0;
        gp_lst_get(24 + i, 2, &c0, &t0);
        gp_lst_begin(2);
        setup((uint32_t)(uintptr_t)cstub[i], na);
        g_call();
        gp_lst_end(0, 0, 0, 0);
        gp_lst_cont[24 + i] = k;
        bad |= contract(na, na ? 4 : 0, in[0], in[2], in[3]);
        cbad |= !counted(24 + i, 2, c0, t0);
    }
    printf("[3] 18 subsystem stubs and 6 direct-call stubs: registers, xmm0-7, arguments, stack %s; counted in the "
           "phase in effect %s\n", bad ? "WRONG" : "as the original's", cbad ? "WRONG" : "right");
    fail |= bad || cbad;

    /* [4] the module stub: ebx = the list entry, [ebx+0x10] = the module's vtable */
    static uint32_t mvt[4], entry[8];
    mvt[0] = (uint32_t)(uintptr_t)t_callee0;
    entry[4] = (uint32_t)(uintptr_t)mvt;
    LONG c0 = gp_lst_mod_calls((uint32_t)(uintptr_t)mvt), mc0; uint64_t mt0;
    gp_lst_get(-2, 3, &mc0, &mt0);
    gp_lst_begin(3);
    setup((uint32_t)(uintptr_t)gp_lst_mod_stub, 0);
    g_in[1] = (uint32_t)(uintptr_t)entry;               /* ebx */
    g_call();
    gp_lst_end(0, 0, 0, 0);
    bad = contract(0, 0, (uint32_t)(uintptr_t)mvt, (uint32_t)(uintptr_t)entry + 0x10, in[3]);
    cbad = gp_lst_mod_calls((uint32_t)(uintptr_t)mvt) != c0 + 1 || !counted(-2, 3, mc0, mt0);
    printf("[4] module stub: callee got eax = vtable, ecx = ebx+0x10, edx, xmm0-7 as the original sequence gives; "
           "caller state %s; counted under its vtable %s\n", bad ? "WRONG" : "as the original's", cbad ? "WRONG" : "right");
    fail |= bad || cbad;

    /* [5] overhead per module call */
    mvt[0] = (uint32_t)(uintptr_t)t_null0;
    const int N = 200000; uint64_t tt[2];
    for (int pass = 0; pass < 2; pass++) {
        setup(pass ? (uint32_t)(uintptr_t)gp_lst_mod_stub : (uint32_t)(uintptr_t)t_mod_orig, 0);
        g_in[1] = (uint32_t)(uintptr_t)entry;
        uint64_t t0 = now_us();
        for (int i = 0; i < N; i++) g_call();
        tt[pass] = now_us() - t0;
    }
    printf("[5] a timed update-module call costs %.0f ns more than the original sequence\n",
           ((double)tt[1] - (double)tt[0]) * 1000.0 / N);
    gp_lst_begin(1); gp_lst_end(0, 0, 1000, 0);  /* one more logic step, so the window has one */
    gp_lst_period_ms = 1;
    Sleep(5);
    gp_lst_force_report();
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
