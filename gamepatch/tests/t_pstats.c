/* t_pstats: particlestats (p_pstats.c/.S) against the original exe.
 *  [1] the patch applies to the original bytes (sites and context hashes) and writes what it should:
 *      a call to its stub at each of the 5 call sites, the stubs' addresses in the two vtable slots,
 *      the continuations at the originals;
 *  [2] the seven timed stubs (manager render cdecl 1 argument, RenderObject draw module thiscall 3
 *      arguments ret 12, colour setters cdecl 4 / 2 / 4 arguments, sorting flush no arguments,
 *      ParticleBufferClass::Render thiscall 1 argument ret 4): the original sees every register,
 *      xmm0-7 and its arguments in order as the caller set them; the caller gets the original's
 *      eax, ecx, edx, xmm0-7 back, ebx esi edi ebp unchanged, the stack as the original leaves it;
 *      one call and a positive time are counted for that kind only, in the pass of byte 0xdd1e44
 *      (and the draw module's eax as its particle count);
 *  [3] the steps before the manager render and the sorting flush read what they should: the armed
 *      flag and the live count (main pass), the system list by draw module kind every 16th main-pass
 *      call only, the sorted nodes waiting in either pass;
 *  [4] the 60 s lines, and the cost of one timed call.
 * usage: t_pstats.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>

static uint32_t OFF;

/* ---- generic caller (up to 4 stack arguments) and recording callees (as t_rstats [4]) ---- */
uint32_t g_target, g_nargs, g_args[4], g_in[7], g_out[7], g_saved_esp; int32_t g_esp_delta;
uint8_t g_xin[128], g_xout[128], g_xret[128], g_xseen[128];
uint32_t c_eax, c_ecx, c_edx, c_args[4];
void g_call(void); void t_callee0(void); void t_callee4(void); void t_callee12(void); void t_null(void);
#define CALLEE_BODY(n) \
        "  mov [_c_eax], eax\n  mov [_c_ecx], ecx\n  mov [_c_edx], edx\n" \
        "  mov eax, [esp+4]\n  mov [_c_args], eax\n  mov eax, [esp+8]\n  mov [_c_args+4], eax\n" \
        "  mov eax, [esp+12]\n  mov [_c_args+8], eax\n  mov eax, [esp+16]\n  mov [_c_args+12], eax\n" \
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
        ".globl _t_callee12\n_t_callee12:\n" CALLEE_BODY("2") "  ret 12\n"
        ".globl _t_null\n_t_null:\n  ret\n"
        ".att_syntax\n");

static void snap(LONG c[PS_N][2], uint64_t t[PS_N][2], gp_pst_t *st)
{
    for (int k = 0; k < PS_N; k++)
        for (int p = 0; p < 2; p++) { c[k][p] = gp_pst.calls[k][p]; t[k][p] = gp_pst_ticks(k, p); }
    *st = gp_pst;
}

/* kind: PS_*; nargs: the original's; pushed: what the caller pushes; callee_pops: bytes the
 * original's ret pops */
static int check_timed(const char *what, void (*stub)(void), uint32_t *cont, void (*callee)(void), unsigned kind,
                       int nargs, int pushed, int callee_pops, int sm)
{
    LONG c0[PS_N][2], c1[PS_N][2]; uint64_t k0[PS_N][2], k1[PS_N][2]; gp_pst_t s0, s1;
    snap(c0, k0, &s0);
    uint32_t keep = *cont;
    *cont = (uint32_t)(uintptr_t)callee;
    for (int i = 0; i < 128; i++) { g_xin[i] = (uint8_t)(0x6b ^ i * 29); g_xret[i] = (uint8_t)(0x17 ^ i * 53); }
    memset(g_xseen, 0, sizeof g_xseen); memset(g_xout, 0, sizeof g_xout);
    static const uint32_t in[7] = {0x11111111, 0x33333333, 0x0c0c0c0c, 0x22222222, 0x55555555, 0x66666666, 0x77777777};
    memcpy(g_in, in, sizeof g_in);
    for (int i = 0; i < 4; i++) g_args[i] = 0x9a000000u + 0x010101u * (i + 1);
    g_nargs = (uint32_t)pushed; c_eax = c_ecx = c_edx = 0; memset(c_args, 0, sizeof c_args);
    g_target = (uint32_t)(uintptr_t)stub;
    *(volatile uint8_t *)0xdd1e44 = (uint8_t)sm;
    g_call();
    *(volatile uint8_t *)0xdd1e44 = 0;
    *cont = keep;
    snap(c1, k1, &s1);
    int bad = c_eax != in[0] || c_ecx != in[2] || c_edx != in[3] || memcmp(g_xseen, g_xin, 128);
    for (int i = 0; i < nargs; i++) bad |= c_args[i] != g_args[i];
    bad |= g_out[0] != 0xa0a0a0a0 || g_out[2] != 0xc0c0c0c0 || g_out[3] != 0xd0d0d0d0 || memcmp(g_xout, g_xret, 128);
    bad |= g_out[1] != in[1] || g_out[4] != in[4] || g_out[5] != in[5] || g_out[6] != in[6];
    bad |= g_esp_delta != callee_pops - 4 * pushed;
    int cbad = 0;
    for (unsigned k = 0; k < PS_N; k++)
        for (int p = 0; p < 2; p++) {
            int hit = k == kind && p == sm;
            cbad |= c1[k][p] - c0[k][p] != hit || (hit ? k1[k][p] <= k0[k][p] : k1[k][p] != k0[k][p]);
        }
    for (int p = 0; p < 2; p++)
        cbad |= s1.robj_particles[p] - s0.robj_particles[p] != (kind == PS_ROBJ && p == sm ? (LONG)0xa0a0a0a0 : 0);
    printf("[2] %-46s shadow-map byte %d: registers, xmm0-7, arguments, stack %s; counted %s\n", what, sm,
           bad ? "WRONG" : "as the original's", cbad ? "WRONG" : "right");
    return bad + cbad;
}

/* ---- [3] a manager with one system per draw module kind, and a sorted-node chain ---- */
static uint8_t mgr[0x100], sysb[12][0x200], modb[12][8], stb[12][0x20];
static uint32_t nodes[16][3], sortn[8], sort_head_alt;
static const uint32_t vts[9] = {0xc326b8, 0xc32724, 0xc32784, 0xc327e0, 0xc32844, 0xc328a8, 0xc3290c, 0, 0x12345678};

static void build_world(void)
{
    /* nodes[0] = the list's sentinel; systems 0-8 one per kind (7 = no draw module, 8 = other
     * vtable with a GPU-like storage), 9 = terrain (type 6), 10 = a node without a system */
    int ns = 11;
    for (int i = 0; i < ns; i++) {
        uint8_t *s = sysb[i];
        memset(s, 0, sizeof sysb[i]);
        *(int *)(s + 0xc) = i == 9 ? 6 : 1;
        uint32_t vt = i < 9 ? vts[i] : vts[0];
        *(uint32_t *)modb[i] = vt;
        *(uint8_t **)(s + 0x1c4) = i == 7 ? NULL : modb[i];
        *(uint32_t *)stb[i] = i == 8 ? 0xc33b48 : 0xc33ae8;
        *(int *)(stb[i] + 0x10) = 10 + i;
        *(uint8_t **)(s + 0xa4) = stb[i];
    }
    for (int i = 0; i <= ns; i++) {
        nodes[i][0] = (uint32_t)(uintptr_t)nodes[(i + 1) % (ns + 1)];
        nodes[i][2] = i ? (i - 1 < 10 ? (uint32_t)(uintptr_t)sysb[i - 1] : 0) : 0;
    }
    *(uint32_t *)(mgr + 0x4c) = (uint32_t)(uintptr_t)nodes[0];
    mgr[0xa8] = 1;
    *(LONG *)(mgr + 0x50) = 1234;
    for (int i = 0; i < 5; i++) sortn[i] = i < 4 ? (uint32_t)(uintptr_t)&sortn[i + 1] : 0;
}

static void call_stub(void (*stub)(void), uint32_t *cont, int pushed, int sm)
{
    uint32_t keep = *cont;
    *cont = (uint32_t)(uintptr_t)t_null;
    g_nargs = (uint32_t)pushed; g_target = (uint32_t)(uintptr_t)stub;
    *(volatile uint8_t *)0xdd1e44 = (uint8_t)sm;
    g_call();
    *(volatile uint8_t *)0xdd1e44 = 0;
    *cont = keep;
}

static int check_pre(void)
{
    int bad = 0;
    build_world();
    volatile uint32_t *mp = (volatile uint32_t *)0xde3744;
    *mp = 0;
    while (gp_pst.calls[PS_MGR][0] & 15) call_stub(gp_pst_mgr_stub, &gp_pst_mgr_cont, 1, 0);
    gp_pst_t a = gp_pst, b;
    *mp = (uint32_t)(uintptr_t)mgr;
    call_stub(gp_pst_mgr_stub, &gp_pst_mgr_cont, 1, 0);        /* 16th: walks */
    b = gp_pst;
    int w = b.walks - a.walks == 1 && b.terrain - a.terrain == 1 && b.armed[0] - a.armed[0] == 1 &&
            b.armed[1] == a.armed[1] && b.live - a.live == 1234 && b.walk_cut == a.walk_cut;
    for (int k = 0; k < PS_KINDS; k++)
        w &= b.systems[k] - a.systems[k] == 1 && b.particles[k] - a.particles[k] == (k == 8 ? 0 : 10 + k);
    printf("[3] main pass, 16th call: armed, live count and the system walk (one system of each of the 9 kinds, "
           "particles of CPU storages only, terrain apart): %s\n", w ? "right" : "WRONG");
    bad |= !w;
    a = gp_pst;
    call_stub(gp_pst_mgr_stub, &gp_pst_mgr_cont, 1, 0);        /* 17th: no walk */
    call_stub(gp_pst_mgr_stub, &gp_pst_mgr_cont, 1, 1);        /* shadow pass: armed only */
    b = gp_pst;
    w = b.walks == a.walks && b.systems[0] == a.systems[0] && b.armed[0] - a.armed[0] == 1 &&
        b.armed[1] - a.armed[1] == 1 && b.live - a.live == 1234;
    printf("[3] main pass, 17th call and a shadow-pass call: armed counted in each pass, live count in the main "
           "pass only, no walk: %s\n", w ? "right" : "WRONG");
    bad |= !w;
    mgr[0xa8] = 0;
    a = gp_pst;
    call_stub(gp_pst_mgr_stub, &gp_pst_mgr_cont, 1, 1);
    b = gp_pst;
    w = b.armed[1] == a.armed[1];
    printf("[3] manager not armed: not counted as armed: %s\n", w ? "right" : "WRONG");
    bad |= !w;
    *mp = 0;
    /* sorted nodes */
    volatile uint32_t *sh = (volatile uint32_t *)(uintptr_t)gp_pst_sort_head_va;
    for (int sm = 0; sm < 2; sm++) {
        a = gp_pst;
        *sh = (uint32_t)(uintptr_t)sortn;
        call_stub(gp_pst_sort_stub, &gp_pst_sort_cont, 0, sm);
        *sh = 0;
        call_stub(gp_pst_sort_stub, &gp_pst_sort_cont, 0, sm);
        b = gp_pst;
        w = b.sort_nodes[sm] - a.sort_nodes[sm] == 5 && b.sort_nodes[!sm] == a.sort_nodes[!sm];
        printf("[3] sorting flush, shadow-map byte %d: 5 waiting nodes, then none: %s\n", sm, w ? "right" : "WRONG");
        bad |= !w;
    }
    return bad;
}

/* [4] cost of one timed call (draw module shape) over a direct call, per call in ns */
void t_null12(void);
__asm__(".intel_syntax noprefix\n.text\n.globl _t_null12\n_t_null12:\n  ret 12\n.att_syntax\n");
static double timed_overhead_ns(void)
{
    const int N = 200000; uint64_t t[2];
    uint32_t keep = gp_pst_robj_cont;
    gp_pst_robj_cont = (uint32_t)(uintptr_t)t_null12;
    g_nargs = 3;
    for (int pass = 0; pass < 2; pass++) {
        g_target = pass ? (uint32_t)(uintptr_t)gp_pst_robj_stub : (uint32_t)(uintptr_t)t_null12;
        uint64_t t0 = now_us();
        for (int i = 0; i < N; i++) g_call();
        t[pass] = now_us() - t0;
    }
    gp_pst_robj_cont = keep;
    return ((double)t[1] - (double)t[0]) * 1000.0 / N;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    static const uint32_t data[] = {0xdd0000, 0xde0000};          /* 0xdd1e44; 0xde3744 */
    for (unsigned i = 0; i < 2; i++) {
        MEMORY_BASIC_INFORMATION mi;
        VirtualQuery((void *)(uintptr_t)data[i], &mi, sizeof mi);
        if (mi.State == MEM_FREE && !VirtualAlloc((void *)(uintptr_t)data[i], 0x10000, MEM_RESERVE, PAGE_READWRITE)) {
            printf("cannot reserve %08x\n", data[i]); return 2;
        }
    }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xdd1000, 0x1000, 0) || orig_map_at(0xde3000, 0x1000, 0)) return 2;
    *(volatile uint8_t *)0xdd1e44 = 0;
    *(volatile uint32_t *)0xde3744 = 0;
    if (orig_map_at(0xd9b000, 0x1000, 0)) {                      /* the sorted-node head, else a stand-in */
        gp_pst_sort_head_va = (uint32_t)(uintptr_t)&sort_head_alt;
        printf("(0xd9b000 not available here: the sorted-node head is read from a stand-in)\n");
    }
    *(volatile uint32_t *)(uintptr_t)gp_pst_sort_head_va = 0;
    if (!(OFF = orig_reserve_image())) return 2;
    static const uint32_t pages[] = {0x44c000, 0x471000, 0x964000, 0x965000, 0x52e000, 0x52f000, 0x5ae000,
                                     0xc32000, 0xbed000};
    for (unsigned i = 0; i < sizeof pages / 4; i++) if (orig_map_at(pages[i], 0x1000, OFF)) return 2;

    int fail = 0;
    gp_va_offset = OFF;
    int ok = gp_patch_particlestats();
    gp_va_offset = 0;
    static const struct { uint32_t va; void (*stub)(void); } calls[] = {
        {0x4716ee, gp_pst_mgr_stub}, {0x4716f4, gp_pst_sort_stub}, {0x965277, gp_pst_c1_stub},
        {0x96528b, gp_pst_c2_stub}, {0x9652cb, gp_pst_c3_stub}};
    const unsigned ncalls = sizeof calls / sizeof calls[0];
    int wrong = 0;
    for (unsigned i = 0; i < ncalls; i++) {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(calls[i].va + OFF);
        int32_t rel; memcpy(&rel, p + 1, 4);
        wrong += p[0] != 0xe8 || (uint32_t)(uintptr_t)(p + 5) + (uint32_t)rel != (uint32_t)(uintptr_t)calls[i].stub;
    }
    uint32_t slot; memcpy(&slot, (const void *)(uintptr_t)(0xc32854 + OFF), 4);
    wrong += slot != (uint32_t)(uintptr_t)gp_pst_robj_stub;
    memcpy(&slot, (const void *)(uintptr_t)(0xbed2a0 + OFF), 4);
    wrong += slot != (uint32_t)(uintptr_t)gp_pst_pbuf_stub;
    wrong += gp_pst_mgr_cont != 0x44c3ea + OFF || gp_pst_sort_cont != 0x52ec60 + OFF || gp_pst_robj_cont != 0x964c00 + OFF ||
             gp_pst_c1_cont != 0x50e040 + OFF || gp_pst_c2_cont != 0x50e244 + OFF || gp_pst_c3_cont != 0x50e413 + OFF ||
             gp_pst_pbuf_cont != 0x5aed50 + OFF;
    printf("[1] particlestats applied to the original bytes: %s; %u calls and the two vtable slots point at the "
           "stubs, continuations at the originals: %s\n", ok ? "yes" : "NO", ncalls, wrong ? "NO" : "yes");
    fail |= !ok || wrong;
    if (!ok) { printf("FAIL\n"); return 1; }

    for (int sm = 0; sm < 2; sm++) {
        fail |= check_timed("manager render (call 0x44c3ea, cdecl 1)", gp_pst_mgr_stub, &gp_pst_mgr_cont, t_callee0,
                            PS_MGR, 1, 1, 0, sm) != 0;
        fail |= check_timed("RenderObject draw module (vtable 0x964c00)", gp_pst_robj_stub, &gp_pst_robj_cont,
                            t_callee12, PS_ROBJ, 3, 3, 12, sm) != 0;
        fail |= check_timed("colour setter (call 0x50e040, cdecl 4)", gp_pst_c1_stub, &gp_pst_c1_cont, t_callee0,
                            PS_COLOR, 4, 4, 0, sm) != 0;
        fail |= check_timed("opacity setter (call 0x50e244, cdecl 2)", gp_pst_c2_stub, &gp_pst_c2_cont, t_callee0,
                            PS_COLOR, 2, 2, 0, sm) != 0;
        fail |= check_timed("colour setter (call 0x50e413, cdecl 4)", gp_pst_c3_stub, &gp_pst_c3_cont, t_callee0,
                            PS_COLOR, 4, 4, 0, sm) != 0;
        fail |= check_timed("sorting flush (call 0x52ec60)", gp_pst_sort_stub, &gp_pst_sort_cont, t_callee0,
                            PS_SORT, 0, 0, 0, sm) != 0;
        fail |= check_timed("ParticleBufferClass::Render (vtable 0x5aed50)", gp_pst_pbuf_stub, &gp_pst_pbuf_cont,
                            t_callee4, PS_PBUF, 1, 1, 4, sm) != 0;
    }
    fail |= check_pre() != 0;
    Sleep(20);
    gp_pst_force_report();                          /* the 60 s lines of this window */
    printf("[4] a timed call costs %.0f ns more than the direct call\n", timed_overhead_ns());
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
