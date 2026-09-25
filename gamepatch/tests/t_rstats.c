/* t_rstats: renderstats (p_rstats.c/.S) against the original exe.
 *  [1] the patch applies to the original bytes (sites and context hashes) and writes what it should:
 *      a call to its stub at each of the 8 call sites, the stub's address in vtable slot 0xbdc3d4;
 *  [2] the five counting stubs hand eax, ecx, edx, xmm0-7, the stack and the return address to the
 *      callee unchanged (ebx, esi, edi, ebp too) and count into the right slot (shadow-map pass
 *      byte 0xdd1e44 clear or set, vertex counts read through the mesh);
 *  [3] the two logging stubs (display switch, static LOD) pass the argument to the original, see the
 *      caller of the wrapper 16 bytes up the stack, return as the original does (ret 4) with its
 *      eax, ecx, edx and xmm0-7, and keep ebx, esi, edi, ebp;
 *  [4] the six timed stubs (WW3D::Render cdecl 2 arguments, Customized_Render / Visibility_Check /
 *      Flush thiscall 1 argument ret 4, renderOneObject thiscall 4 arguments ret 16, the FX flush
 *      thiscall 0 arguments, also entered by the wrapper's jmp): the original sees every register,
 *      xmm0-7 and its arguments in order as the caller set them; the caller gets the original's
 *      eax, ecx, edx, xmm0-7 back, ebx esi edi ebp unchanged, the stack as the original leaves it;
 *      one call and a positive time are counted for that kind only, in the pass of byte 0xdd1e44.
 * usage: t_rstats.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>

static uint32_t OFF;

/* ---- harness: magic registers in, call a stub as the game's call would, record what arrives ---- */
uint32_t h_target, h_ecx, h_arg1, h_out[4], h_saved_esp, h_esp_after;
uint8_t h_xin[128], h_xseen[128], h_xout[128];
uint32_t s_eax, s_ecx, s_edx, s_ret, s_a1, s_a2, s_a3;
void h_call(void); void h_after(void); void h_frame(void); void h_frame_after(void);
void standin(void); void standin_orig(void);
__asm__(".intel_syntax noprefix\n.text\n"
        /* h_call: push 0x44444444, h_arg1; call the stub with magic registers (a call site) */
        ".globl _h_call\n_h_call:\n  push ebx\n  push esi\n  push edi\n  push ebp\n  mov [_h_saved_esp], esp\n"
        "  movups xmm0, [_h_xin]\n  movups xmm1, [_h_xin+16]\n  movups xmm2, [_h_xin+32]\n  movups xmm3, [_h_xin+48]\n"
        "  movups xmm4, [_h_xin+64]\n  movups xmm5, [_h_xin+80]\n  movups xmm6, [_h_xin+96]\n  movups xmm7, [_h_xin+112]\n"
        "  push 0x44444444\n  push dword ptr [_h_arg1]\n"
        "  mov eax, 0x11111111\n  mov ecx, [_h_ecx]\n  mov edx, 0x22222222\n  mov ebx, 0x33333333\n"
        "  mov esi, 0x55555555\n  mov edi, 0x66666666\n  mov ebp, 0x77777777\n"
        "  call dword ptr [_h_target]\n.globl _h_after\n_h_after:\n"
        "  mov [_h_out], ebx\n  mov [_h_out+4], esi\n  mov [_h_out+8], edi\n  mov [_h_out+12], ebp\n"
        "  mov [_h_esp_after], esp\n  mov esp, [_h_saved_esp]\n  pop ebp\n  pop edi\n  pop esi\n  pop ebx\n  ret\n"
        /* h_frame: the frame of 0x49d565 / 0x6020b4 at their calls: caller's return, two saved
         * registers, the argument; returns with eax/ecx/edx/xmm as the stub left them */
        ".globl _h_frame\n_h_frame:\n  push ebx\n  push esi\n  push edi\n  push ebp\n  mov [_h_saved_esp], esp\n"
        "  movups xmm0, [_h_xin]\n  movups xmm7, [_h_xin+112]\n"
        "  push 0x12345678\n  push 0xaaaa0010\n  push 0xbbbb0020\n  push 0xcccc0030\n  push dword ptr [_h_arg1]\n"
        "  mov eax, 0x11111111\n  mov ecx, [_h_ecx]\n  mov edx, 0x22222222\n  mov ebx, 0x33333333\n"
        "  mov esi, 0x55555555\n  mov edi, 0x66666666\n  mov ebp, 0x77777777\n"
        "  call dword ptr [_h_target]\n.globl _h_frame_after\n_h_frame_after:\n"
        "  mov [_s_a3], eax\n  mov [_s_a2], ecx\n  mov [_h_arg1], edx\n"
        "  movups [_h_xout], xmm0\n  movups [_h_xout+112], xmm7\n"
        "  mov [_h_out], ebx\n  mov [_h_out+4], esi\n  mov [_h_out+8], edi\n  mov [_h_out+12], ebp\n"
        "  mov [_h_esp_after], esp\n  mov esp, [_h_saved_esp]\n  pop ebp\n  pop edi\n  pop esi\n  pop ebx\n  ret\n"
        /* standin: the callee of a counting stub; records and returns to h_after */
        ".globl _standin\n_standin:\n  mov [_s_eax], eax\n  mov [_s_ecx], ecx\n  mov [_s_edx], edx\n"
        "  mov eax, [esp]\n  mov [_s_ret], eax\n  mov eax, [esp+4]\n  mov [_s_a1], eax\n  mov eax, [esp+8]\n  mov [_s_a2], eax\n"
        "  movups [_h_xseen], xmm0\n  movups [_h_xseen+16], xmm1\n  movups [_h_xseen+32], xmm2\n  movups [_h_xseen+48], xmm3\n"
        "  movups [_h_xseen+64], xmm4\n  movups [_h_xseen+80], xmm5\n  movups [_h_xseen+96], xmm6\n  movups [_h_xseen+112], xmm7\n"
        "  ret\n"
        /* standin_orig: the switch / LOD function (thiscall, ret 4); clobbers what a callee may */
        ".globl _standin_orig\n_standin_orig:\n  mov [_s_ecx], ecx\n  mov eax, [esp+4]\n  mov [_s_a1], eax\n"
        "  mov eax, [esp]\n  mov [_s_ret], eax\n"
        "  mov eax, 0x5a5a5a5a\n  mov ecx, 0x7c7c7c7c\n  mov edx, 0x6b6b6b6b\n  pcmpeqb xmm0, xmm0\n  xorps xmm7, xmm7\n"
        "  ret 4\n.att_syntax\n");

/* ---- [4] timed stubs: generic caller (up to 4 stack arguments) and a recording callee ---- */
uint32_t g_target, g_nargs, g_args[4], g_in[7], g_out[7], g_saved_esp; int32_t g_esp_delta;
uint8_t g_xin[128], g_xout[128], g_xret[128], g_xseen[128];
uint32_t c_eax, c_ecx, c_edx, c_args[4];
void g_call(void); void t_callee0(void); void t_callee4(void); void t_callee16(void);
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
        ".globl _t_callee16\n_t_callee16:\n" CALLEE_BODY("2") "  ret 16\n"
        ".globl _t_null16\n_t_null16:\n  ret 16\n"
        ".att_syntax\n");
void t_null16(void);

/* [5] cost of one timed call (renderOneObject shape) over a direct call, per call in ns */
static double timed_overhead_ns(void)
{
    const int N = 200000; uint64_t t[2];
    uint32_t keep = gp_rst_obj_cont;
    gp_rst_obj_cont = (uint32_t)(uintptr_t)t_null16;
    g_nargs = 4;
    for (int pass = 0; pass < 2; pass++) {
        g_target = pass ? (uint32_t)(uintptr_t)gp_rst_obj_stub : (uint32_t)(uintptr_t)t_null16;
        uint64_t t0 = now_us();
        for (int i = 0; i < N; i++) g_call();
        t[pass] = now_us() - t0;
    }
    gp_rst_obj_cont = keep;
    return ((double)t[1] - (double)t[0]) * 1000.0 / N;
}

/* kind: p_rstats.S TIMED number; nargs: the original's; pushed: what the caller pushes (the FX
 * flush entered by the DX8 wrapper's jmp: the wrapper's own cdecl argument, left to its caller);
 * callee_pops: bytes the original's ret pops; cdecl: the caller pops its arguments */
static int check_timed(const char *what, void (*stub)(void), uint32_t *cont, void (*callee)(void), unsigned kind,
                       int nargs, int pushed, int callee_pops, int sm)
{
    LONG c0[6][2], c1[6][2], v0[19], v1[19]; uint64_t k0[6][2], k1[6][2];
    for (unsigned k = 0; k < 6; k++) for (int p = 0; p < 2; p++) gp_rst_timer(k, p, &c0[k][p], &k0[k][p]);
    gp_rst_get(v0, 19);
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
    for (unsigned k = 0; k < 6; k++) for (int p = 0; p < 2; p++) gp_rst_timer(k, p, &c1[k][p], &k1[k][p]);
    gp_rst_get(v1, 19);
    int bad = c_eax != in[0] || c_ecx != in[2] || c_edx != in[3] || memcmp(g_xseen, g_xin, 128);
    for (int i = 0; i < nargs; i++) bad |= c_args[i] != g_args[i];
    bad |= g_out[0] != 0xa0a0a0a0 || g_out[2] != 0xc0c0c0c0 || g_out[3] != 0xd0d0d0d0 || memcmp(g_xout, g_xret, 128);
    bad |= g_out[1] != in[1] || g_out[4] != in[4] || g_out[5] != in[5] || g_out[6] != in[6];
    bad |= g_esp_delta != callee_pops - 4 * pushed;
    int cbad = 0;
    for (unsigned k = 0; k < 6; k++)
        for (int p = 0; p < 2; p++) {
            int hit = k == kind && p == sm;
            cbad |= c1[k][p] - c0[k][p] != hit || (hit ? k1[k][p] <= k0[k][p] : k1[k][p] != k0[k][p]);
        }
    for (int i = 0; i < 19; i++) cbad |= v1[i] - v0[i] != (kind == 2 && i == 1 + sm);   /* vis[sm] only */
    printf("[4] %-44s shadow-map byte %d: registers, xmm0-7, arguments, stack %s; counted %s\n", what, sm,
           bad ? "WRONG" : "as the original's", cbad ? "WRONG" : "right");
    return bad + cbad;
}

/* want: the expected change of each counter (rst_t order: frames, vis[2], flush[2], rigid[2],
 * cpuskin[2], gpuskin[2], fxskin[2], fxverts[2], dxskin[2], dxverts[2]) */
static int check_counting(const char *what, void (*stub)(void), uint32_t *cont, uint32_t ecx, uint32_t arg1,
                          const LONG want[19], int sm)
{
    LONG before[19], after[19];
    uint32_t keep = *cont;
    *cont = (uint32_t)(uintptr_t)standin;
    for (int i = 0; i < 128; i++) h_xin[i] = (uint8_t)(0x5d ^ i * 13);
    memset(h_xseen, 0, sizeof h_xseen);
    h_target = (uint32_t)(uintptr_t)stub; h_ecx = ecx; h_arg1 = arg1;
    *(volatile uint8_t *)0xdd1e44 = (uint8_t)sm;
    gp_rst_get(before, 19);
    h_call();
    gp_rst_get(after, 19);
    *(volatile uint8_t *)0xdd1e44 = 0;
    *cont = keep;
    int bad = s_eax != 0x11111111 || s_ecx != ecx || s_edx != 0x22222222 || s_ret != (uint32_t)(uintptr_t)h_after ||
              s_a1 != arg1 || s_a2 != 0x44444444 || memcmp(h_xseen, h_xin, 128) || h_out[0] != 0x33333333 ||
              h_out[1] != 0x55555555 || h_out[2] != 0x66666666 || h_out[3] != 0x77777777 ||
              h_esp_after != h_saved_esp - 8;
    int cbad = 0;
    for (int i = 0; i < 19; i++) cbad |= after[i] - before[i] != want[i];
    printf("[2] %-36s shadow-map byte %d: registers, xmm0-7, stack and return address %s; counted %s\n", what, sm,
           bad ? "CHANGED" : "unchanged", cbad ? "WRONG" : "right");
    return bad + cbad;
}

static int check_logging(const char *what, void (*stub)(void), uint32_t *fn, uint32_t ecx, int arg)
{
    uint32_t keep = *fn;
    LONG l0 = gp_rst_logged;
    *fn = (uint32_t)(uintptr_t)standin_orig;
    for (int i = 0; i < 128; i++) h_xin[i] = (uint8_t)(0x3a ^ i * 7);
    memset(h_xout, 0x99, sizeof h_xout);
    h_target = (uint32_t)(uintptr_t)stub; h_ecx = ecx; h_arg1 = (uint32_t)arg;
    s_ecx = s_a1 = 0;
    h_frame();
    *fn = keep;
    static const uint8_t ones[16] = {0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff};
    static const uint8_t zeros[16];
    int bad = s_ecx != ecx || s_a1 != (uint32_t)arg || s_a3 != 0x5a5a5a5a || s_a2 != 0x7c7c7c7c ||
              h_arg1 != 0x6b6b6b6b || memcmp(h_xout, ones, 16) || memcmp(h_xout + 112, zeros, 16) ||
              h_out[0] != 0x33333333 || h_out[1] != 0x55555555 || h_out[2] != 0x66666666 || h_out[3] != 0x77777777 ||
              h_esp_after != h_saved_esp - 16 || gp_rst_logged - l0 != 2 || gp_rst_last_caller != 0xaaaa0010 ||
              gp_rst_last_arg != arg;
    printf("[3] %-34s argument %d reaches the original, caller %08lx seen, returns as the original "
           "(eax/ecx/edx/xmm of the original, ret 4, callee-saved kept), 2 log lines: %s\n", what, arg,
           (unsigned long)gp_rst_last_caller, bad ? "NO" : "yes");
    return bad;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    static const uint32_t data[] = {0xdd0000, 0xde0000};          /* 0xdd1e44; 0xde3b84, 0xde4364, 0xde4958 */
    for (unsigned i = 0; i < 2; i++) {
        MEMORY_BASIC_INFORMATION mi;
        VirtualQuery((void *)(uintptr_t)data[i], &mi, sizeof mi);
        if (mi.State == MEM_FREE && !VirtualAlloc((void *)(uintptr_t)data[i], 0x10000, MEM_RESERVE, PAGE_READWRITE)) {
            printf("cannot reserve %08x\n", data[i]); return 2;
        }
    }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xdd1000, 0x1000, 0) || orig_map_at(0xde3000, 0x2000, 0)) return 2;
    *(volatile uint8_t *)0xdd1e44 = 0;
    if (!(OFF = orig_reserve_image())) return 2;
    static const uint32_t pages[] = {0x44b000, 0x49d000, 0x548000, 0x574000, 0x602000, 0xbdc000, 0x517000, 0x46f000,
                                     0x470000, 0x471000, 0x47d000, 0x518000, 0x516000};
    for (unsigned i = 0; i < sizeof pages / 4; i++) if (orig_map_at(pages[i], 0x1000, OFF)) return 2;

    int fail = 0;
    gp_va_offset = OFF;
    int ok = gp_patch_renderstats();
    gp_va_offset = 0;
    static const struct { uint32_t va; void (*stub)(void); uint8_t op; } calls[] = {
        {0x44bb00, gp_rst_frame_stub, 0xe8}, {0x44bbf5, gp_rst_frame_stub, 0xe8}, {0x57442a, gp_rst_fxl_stub, 0xe8},
        {0x57423b, gp_rst_fxs_stub, 0xe8}, {0x548291, gp_rst_dxs_stub, 0xe8}, {0x49d57e, gp_rst_sw_stub, 0xe8},
        {0x49d585, gp_rst_sw_stub, 0xe8}, {0x6020d1, gp_rst_lod_stub, 0xe8}, {0x47d70c, gp_rst_w3r_stub, 0xe8},
        {0x518065, gp_rst_w3r_stub, 0xe8}, {0x47009f, gp_rst_obj_stub, 0xe8}, {0x47010c, gp_rst_obj_stub, 0xe8},
        {0x471a3b, gp_rst_flush_stub, 0xe8}, {0x517db2, gp_rst_fx_stub, 0xe8}, {0x516d91, gp_rst_fx_stub, 0xe9}};
    const unsigned ncalls = sizeof calls / sizeof calls[0];
    int wrong = 0;
    for (unsigned i = 0; i < ncalls; i++) {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(calls[i].va + OFF);
        int32_t rel; memcpy(&rel, p + 1, 4);
        wrong += p[0] != calls[i].op || (uint32_t)(uintptr_t)(p + 5) + (uint32_t)rel != (uint32_t)(uintptr_t)calls[i].stub;
    }
    uint32_t slot; memcpy(&slot, (const void *)(uintptr_t)(0xbdc3d4 + OFF), 4);
    wrong += slot != (uint32_t)(uintptr_t)gp_rst_vis_stub;
    memcpy(&slot, (const void *)(uintptr_t)(0xbdc3c4 + OFF), 4);
    wrong += slot != (uint32_t)(uintptr_t)gp_rst_cr_stub;
    wrong += gp_rst_frame_cont != 0x449cf8 + OFF || gp_rst_vis_cont != 0x470b83 + OFF || gp_rst_fxl_cont != 0x574113 + OFF ||
             gp_rst_fxs_cont != 0x573464 + OFF || gp_rst_dxs_cont != 0x549370 + OFF || gp_rst_sw_fn != 0x6bff7b + OFF ||
             gp_rst_lod_fn != 0x601c62 + OFF || gp_rst_w3r_cont != 0x517c60 + OFF || gp_rst_cr_cont != 0x46fe84 + OFF ||
             gp_rst_obj_cont != 0x46f48e + OFF || gp_rst_flush_cont != 0x470f44 + OFF || gp_rst_fx_cont != 0x574406 + OFF;
    printf("[1] renderstats applied to the original bytes: %s; %u calls/jmps and the two vtable slots point at the "
           "stubs, continuations at the originals: %s\n", ok ? "yes" : "NO", ncalls, wrong ? "NO" : "yes");
    fail |= !ok || wrong;
    if (!ok) { printf("FAIL\n"); return 1; }

    /* [2] counters: frames 0, vis 1-2, flush 3-4, rigid 5-6, cpuskin 7-8, gpuskin 9-10, fxskin 11-12,
     * fxverts 13-14, dxskin 15-16, dxverts 17-18 (rst_t order) */
    static uint32_t model[16], mesh[64], lists[8];
    model[0x28 / 4] = 123; mesh[0xc4 / 4] = (uint32_t)(uintptr_t)model;
    static uint8_t buf[1024];
    lists[0] = (uint32_t)(uintptr_t)buf; lists[1] = lists[0] + 3 * 32;           /* 3 rigid */
    lists[3] = (uint32_t)(uintptr_t)buf; lists[4] = lists[3] + 2 * 32;           /* 2 CPU-skinned */
    lists[6] = (uint32_t)(uintptr_t)buf; lists[7] = lists[6] + 5 * 32;           /* 5 GPU-skinned */
    for (int sm = 0; sm < 2; sm++) {
        LONG w[5][19] = {{0}};
        w[0][0] = 1;                                              /* frame */
        w[1][1 + sm] = 1;                                         /* visibility pass */
        w[2][3 + sm] = 1; w[2][5 + sm] = 3; w[2][7 + sm] = 2; w[2][9 + sm] = 5;   /* FX flush and its lists */
        w[3][11 + sm] = 1; w[3][13 + sm] = 123;                   /* FX CPU skinning */
        w[4][15 + sm] = 1; w[4][17 + sm] = 123;                   /* DX8 skinning */
        fail |= check_counting("frame (call 0x449cf8)", gp_rst_frame_stub, &gp_rst_frame_cont, 0x0f0f0f0f, 0x12121212, w[0], sm) != 0;
        fail |= check_counting("FX lists (call 0x574113)", gp_rst_fxl_stub, &gp_rst_fxl_cont, (uint32_t)(uintptr_t)lists,
                               0x14141414, w[2], sm) != 0;
        fail |= check_counting("CPU-skinned FX mesh (call 0x573464)", gp_rst_fxs_stub, &gp_rst_fxs_cont, 0x0d0d0d0d,
                               (uint32_t)(uintptr_t)mesh, w[3], sm) != 0;
        fail |= check_counting("DX8 skin mesh (call 0x549370)", gp_rst_dxs_stub, &gp_rst_dxs_cont, (uint32_t)(uintptr_t)mesh,
                               0x15151515, w[4], sm) != 0;
    }
    /* [4] */
    for (int sm = 0; sm < 2; sm++) {
        fail |= check_timed("WW3D::Render (call 0x517c60, cdecl 2)", gp_rst_w3r_stub, &gp_rst_w3r_cont, t_callee0, 0, 2, 2, 0, sm) != 0;
        fail |= check_timed("Customized_Render (vtable 0x46fe84)", gp_rst_cr_stub, &gp_rst_cr_cont, t_callee4, 1, 1, 1, 4, sm) != 0;
        fail |= check_timed("Visibility_Check (vtable 0x470b83)", gp_rst_vis_stub, &gp_rst_vis_cont, t_callee4, 2, 1, 1, 4, sm) != 0;
        fail |= check_timed("renderOneObject (call 0x46f48e, 4 args)", gp_rst_obj_stub, &gp_rst_obj_cont, t_callee16, 3, 4, 4, 16, sm) != 0;
        fail |= check_timed("Flush (call 0x470f44)", gp_rst_flush_stub, &gp_rst_flush_cont, t_callee4, 4, 1, 1, 4, sm) != 0;
        fail |= check_timed("FX flush (call 0x574406)", gp_rst_fx_stub, &gp_rst_fx_cont, t_callee0, 5, 0, 0, 0, sm) != 0;
        fail |= check_timed("FX flush (jmp from the DX8 flush wrapper)", gp_rst_fx_stub, &gp_rst_fx_cont, t_callee0, 5, 0, 1, 0, sm) != 0;
    }
    Sleep(20);
    gp_rst_force_report();                          /* the three per-frame lines of this window */
    printf("[5] a timed call costs %.0f ns more than the direct call (~830 a frame in a big battle: "
           "renderOneObject in both passes plus ~30 others)\n", timed_overhead_ns());
    /* [3] */
    fail |= check_logging("display switch (call 0x6bff7b)", gp_rst_sw_stub, &gp_rst_sw_fn, 0x0c0c0c0c, 1) != 0;
    fail |= check_logging("display switch (call 0x6bff7b)", gp_rst_sw_stub, &gp_rst_sw_fn, 0x0c0c0c0c, 0) != 0;
    fail |= check_logging("static LOD (call 0x601c62)", gp_rst_lod_stub, &gp_rst_lod_fn, 0x0b0b0b0b, 4) != 0;
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
