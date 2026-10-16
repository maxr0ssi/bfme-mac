/* t_fsplit: framesplit (p_framesplit.c/.S, the monitor's records in p_monitor.c) against the original exe.
 *  [1] it refuses without the monitor; after it, it applies to the original bytes: the client-pass
 *      and engine-step slots of both engine vtables and W3DDisplay::draw's slot point at the stubs,
 *      the Present, limiter and iteration-end sites call them; the continuations are the originals;
 *  [2] every stub hands the original the caller's eax, ecx, edx and arguments and gives back the
 *      original's eax, ecx, edx, with ebx, esi, edi, ebp and the stack as the original leaves them;
 *      Present gets (device, 0, 0, 0, 0) through the device's vtable; the limiter stub returns
 *      timeGetTime's value; the iteration-end stub loads ecx from 0xde42f8;
 *  [3] scripted engine iterations (a client pass with a draw and a Present inside, a logic phase, a
 *      limiter wait; one without a draw; a refused phase 1): the monitor's "f" lines carry the
 *      split, each part at least as long as the spin in it (less 1-2 % for the clocks' rounding), an undrawn iteration carried into the
 *      next record (iters 2, both phases' bits, the refused one as bit 7);
 *  [4] the cost of one iteration's marks.
 * usage: t_fsplit.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include "gp_render.h"
#include "p_fps.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void gp_fs_reset(void);
static uint32_t OFF;

/* h_call(fn, n, args): push args, set eax/ecx/edx from h_in, ebx/esi/edi/ebp magic, call; record
 * eax ecx edx ebx esi edi ebp and how far esp is from before the pushes */
uint32_t h_in[3], h_out[7], h_saved_ebp, h_fn; int32_t h_espdiff;
void h_call(void *fn, int n, const uint32_t *args);
__asm__(".intel_syntax noprefix\n.text\n.globl _h_call\n_h_call:\n"
        "  push ebp\n  mov ebp, esp\n  push ebx\n  push esi\n  push edi\n"
        "  mov ecx, [ebp+12]\n  mov esi, [ebp+16]\n"
        "1:\n  test ecx, ecx\n  jz 2f\n  push dword ptr [esi+ecx*4-4]\n  dec ecx\n  jmp 1b\n"
        "2:\n  mov [_h_saved_ebp], ebp\n  mov eax, [ebp+8]\n  mov [_h_fn], eax\n  mov eax, [_h_in]\n  mov ecx, [_h_in+4]\n  mov edx, [_h_in+8]\n"
        "  mov ebx, 0x33333333\n  mov esi, 0x55555555\n  mov edi, 0x66666666\n  mov ebp, 0x77777777\n"
        "  call dword ptr [_h_fn]\n"
        "  mov [_h_out], eax\n  mov [_h_out+4], ecx\n  mov [_h_out+8], edx\n  mov [_h_out+12], ebx\n  mov [_h_out+16], esi\n"
        "  mov [_h_out+20], edi\n  mov [_h_out+24], ebp\n  mov ebp, [_h_saved_ebp]\n"
        "  lea eax, [ebp-12]\n  sub eax, esp\n  mov [_h_espdiff], eax\n"
        "  lea esp, [ebp-12]\n  pop edi\n  pop esi\n  pop ebx\n  pop ebp\n  ret\n.att_syntax\n");

/* recording callees: what they saw, then a spin, then known return registers */
uint32_t c_regs[3], c_args[5]; static int spin_us;
static void spin(int us) { uint64_t t = now_us(); while ((int)(now_us() - t) < us) ; }
static void c_body(void) { spin(spin_us); }
#define CALLEE(name, pops) \
    void name(void); \
    __asm__(".intel_syntax noprefix\n.text\n.globl _" #name "\n_" #name ":\n" \
            "  mov [_c_regs], eax\n  mov [_c_regs+4], ecx\n  mov [_c_regs+8], edx\n" \
            "  mov eax, [esp+4]\n  mov [_c_args], eax\n  mov eax, [esp+8]\n  mov [_c_args+4], eax\n" \
            "  mov eax, [esp+12]\n  mov [_c_args+8], eax\n  mov eax, [esp+16]\n  mov [_c_args+12], eax\n" \
            "  mov eax, [esp+20]\n  mov [_c_args+16], eax\n" \
            "  call _c_spin\n  mov eax, 0xa0a0a0a0\n  mov ecx, 0xc0c0c0c0\n  mov edx, 0xd0d0d0d0\n  ret " #pops "\n.att_syntax\n");
void c_spin(void) { c_body(); }
CALLEE(t_callee0, 0)
CALLEE(t_callee4, 4)
CALLEE(t_present20, 20)

/* the engine's parts for [3]: the client pass calls the draw stub, the draw records a monitor frame
 * and calls the Present stub (as at 0x52264b: eax = device, edx = its vtable, ebx = 0) */
/* the stubs with the signatures of what they replace */
void __attribute__((thiscall)) client_tc(void *self) __asm__("_gp_fs_s_client");
void __attribute__((thiscall)) draw_tc(void *self) __asm__("_gp_fs_s_draw");
void __attribute__((thiscall)) step_tc(void *self, int phase) __asm__("_gp_fs_s_step");
static int with_draw = 1, client_us = 2000, draw_us = 1000, present_us = 500, step_us = 3000, ran = 1;
static uint8_t gclient[0x100];
void t_present_site(void *dev);     /* asm: push regs as the game's code has them and call the stub */
__asm__(".intel_syntax noprefix\n.text\n.globl _t_present_site\n_t_present_site:\n"
        "  push ebx\n  mov eax, [esp+8]\n  mov edx, [eax]\n  xor ebx, ebx\n  call _gp_fs_s_present\n  pop ebx\n  ret\n.att_syntax\n");
static HRESULT WINAPI f_present(void *dev, void *a, void *b, void *c, void *d) { (void)dev; (void)a; (void)b; (void)c; (void)d; spin(present_us); return 0; }
static void *dev_vt[32] = {[0x44 / 4] = (void *)f_present}, *device[1] = {dev_vt};
static void __attribute__((thiscall)) f_draw(void *self) { (void)self; spin(draw_us); gp_mon_frame(); t_present_site(device); }
static void __attribute__((thiscall)) f_client(void *self)
{
    spin(client_us);
    if (with_draw) draw_tc(self);
}
static void __attribute__((thiscall)) f_step(void *self, int phase) { (void)self; (void)phase; gclient[0xc8] = (uint8_t)ran; spin(step_us); }
static DWORD WINAPI f_time(void) { return 0x7e57; }
static void iteration(int phase, int wait_us)
{
    client_tc(NULL);
    step_tc(NULL, phase);
    if (wait_us >= 0) { h_call((void *)gp_fs_s_wait, 0, NULL); spin(wait_us); }
    h_call((void *)gp_fs_s_iter, 0, NULL);
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    for (uint32_t r = 0xbd0000; r <= 0xde0000; r += 0x210000) {
        MEMORY_BASIC_INFORMATION mi;
        VirtualQuery((void *)(uintptr_t)r, &mi, sizeof mi);
        if (mi.State == MEM_FREE && !VirtualAlloc((void *)(uintptr_t)r, 0x10000, MEM_RESERVE, PAGE_READWRITE)) {
            printf("cannot reserve %08x\n", r); return 2;
        }
    }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xbd0000, 0x1000, 0) || orig_map_at(0xde4000, 0x1000, 0)) return 2;   /* IAT, globals */
    if (!(OFF = orig_reserve_image())) return 2;
    static const uint32_t pages[] = {0x520000, 0x522000, 0x530000, 0x531000, 0x551000, 0xa3e000, 0x63a000,
                                     0xbd8000, 0xbd9000, 0xbfe000};
    for (unsigned i = 0; i < sizeof pages / 4; i++) if (orig_map_at(pages[i], 0x1000, OFF)) return 2;
    char path[MAX_PATH];
    GetTempPathA(sizeof path, path); strcat(path, "t_fsplit-game.txt");
    SetEnvironmentVariableA("GAMEPATCH_MONITOR", path);
    SetEnvironmentVariableA("GAMEPATCH_STALL_MS", "100000");
    gp_mon_start_writer = 0;
    int fail = 0;

    /* [1] */
    gp_va_offset = OFF;
    int before = gp_patch_framesplit(), okm = gp_patch_monitor(), ok = gp_patch_framesplit();
    gp_va_offset = 0;
    int wrong = 0;
    static const struct { uint32_t va; void *stub; } slots[] = {{0xbd857c, gp_fs_s_client}, {0xbfe2fc, gp_fs_s_client},
        {0xbd8578, gp_fs_s_step}, {0xbfe2f8, gp_fs_s_step}, {0xbd9c58, gp_fs_s_draw}};
    for (int i = 0; i < 5; i++) wrong += *(uint32_t *)(uintptr_t)(slots[i].va + OFF) != (uint32_t)(uintptr_t)slots[i].stub;
    static const struct { uint32_t va; void *stub; int nops; } calls[] = {{0x52264b, gp_fs_s_present, 3},
        {0x63a196, gp_fs_s_wait, 1}, {0x63a21f, gp_fs_s_iter, 1}};
    for (int i = 0; i < 3; i++) {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(calls[i].va + OFF);
        int32_t rel; memcpy(&rel, p + 1, 4);
        wrong += p[0] != 0xe8 || (uint32_t)(uintptr_t)(p + 5) + (uint32_t)rel != (uint32_t)(uintptr_t)calls[i].stub;
        for (int k = 0; k < calls[i].nops; k++) wrong += p[5 + k] != 0x90;
    }
    wrong += gp_fs_cont[0] != 0x632409 + OFF || gp_fs_cont[1] != 0x6329b0 + OFF || gp_fs_cont[2] != 0x44b788 + OFF ||
             gp_fs_cont[3] != 0xbd0920 || gp_fs_cont[4] != 0xde42f8;
    printf("[1] without the monitor: %s; monitor %s; framesplit applied to the original bytes: %s; 5 vtable slots, 3 call "
           "sites, continuations: %s\n", before ? "APPLIED" : "refused", okm ? "on" : "OFF", ok ? "yes" : "NO", wrong ? "WRONG" : "right");
    if (before || !okm || !ok || wrong) { printf("FAIL\n"); return 1; }

    /* [2] */
    uint32_t keep[3] = {gp_fs_cont[0], gp_fs_cont[1], gp_fs_cont[2]};
    int bad = 0;
    struct { void *stub; int idx, nargs; void *callee; } vs[] = {{gp_fs_s_client, 0, 0, t_callee0},
        {gp_fs_s_step, 1, 1, t_callee4}, {gp_fs_s_draw, 2, 0, t_callee0}};
    spin_us = 0;
    for (int i = 0; i < 3; i++) {
        gp_fs_cont[vs[i].idx] = (uint32_t)(uintptr_t)vs[i].callee;
        uint32_t args[1] = {0x9a000004};
        h_in[0] = 0x11111111; h_in[1] = 0x0c0c0c0c; h_in[2] = 0x22222222;
        memset(c_regs, 0, sizeof c_regs); memset(c_args, 0, sizeof c_args);
        h_call(vs[i].stub, vs[i].nargs, args);
        int b = c_regs[0] != 0x11111111 || c_regs[1] != 0x0c0c0c0c || c_regs[2] != 0x22222222 ||
                (vs[i].nargs && c_args[0] != 0x9a000004) || h_out[0] != 0xa0a0a0a0 || h_out[1] != 0xc0c0c0c0 ||
                h_out[2] != 0xd0d0d0d0 || h_out[3] != 0x33333333 || h_out[4] != 0x55555555 || h_out[5] != 0x66666666 ||
                h_out[6] != 0x77777777 || h_espdiff != 0;
        if (b) printf("    stub %d: in %08x %08x %08x args %08x out %08x %08x %08x esp %+d\n", i, c_regs[0], c_regs[1],
                      c_regs[2], c_args[0], h_out[0], h_out[1], h_out[2], h_espdiff);
        bad += b;
        gp_fs_cont[vs[i].idx] = keep[vs[i].idx];
    }
    static void *pvt[32]; static void *pdev[1] = {pvt};
    pvt[0x44 / 4] = (void *)t_present20;
    h_in[0] = (uint32_t)(uintptr_t)pdev; h_in[1] = 0x0c0c0c0c; h_in[2] = (uint32_t)(uintptr_t)pvt;
    memset(c_args, 0, sizeof c_args);
    h_call((void *)gp_fs_s_present, 0, NULL);    /* ebx = 0x33333333 here: Present gets ebx x 4 */
    int bp = c_args[0] != (uint32_t)(uintptr_t)pdev || c_args[1] != 0x33333333 || c_args[4] != 0x33333333 ||
             h_out[0] != 0xa0a0a0a0 || h_out[3] != 0x33333333 || h_espdiff != 0;
    uint32_t iat = *(uint32_t *)0xbd0920;
    *(uint32_t *)0xbd0920 = (uint32_t)(uintptr_t)f_time;
    h_call((void *)gp_fs_s_wait, 0, NULL);
    int bw = h_out[0] != 0x7e57 || h_out[3] != 0x33333333 || h_espdiff != 0;
    *(uint32_t *)0xde42f8 = 0x5eed0042;
    h_in[0] = 0x11111111; h_in[2] = 0x22222222;
    h_call((void *)gp_fs_s_iter, 0, NULL);
    int bi = h_out[1] != 0x5eed0042 || h_out[0] != 0x11111111 || h_out[2] != 0x22222222 || h_out[3] != 0x33333333 || h_espdiff != 0;
    printf("[2] client pass, engine step, draw: registers, argument, stack %s; Present %s; limiter %s; iteration end %s\n",
           bad ? "WRONG" : "as the original's", bp ? "WRONG" : "(device, ebx x 4) through vt+0x44",
           bw ? "WRONG" : "returns timeGetTime's value", bi ? "WRONG" : "ecx = [0xde42f8]");
    fail |= bad || bp || bw || bi;

    /* [3] */
    gp_fs_cont[0] = (uint32_t)(uintptr_t)f_client; gp_fs_cont[1] = (uint32_t)(uintptr_t)f_step;
    gp_fs_cont[2] = (uint32_t)(uintptr_t)f_draw;
    *(uint32_t *)0xde4388 = (uint32_t)(uintptr_t)gclient;
    gp_fs_reset();
    client_us = draw_us = present_us = step_us = 100;
    iteration(3, 100);                 /* warm-up: the monitor prints a record from the second on */
    client_us = 2000; draw_us = 1000; present_us = 500; step_us = 3000;
    iteration(4, 4000);                /* drawn, limited */
    with_draw = 0; client_us = 1000; step_us = 1000;
    iteration(5, -1);                  /* no draw, no limit */
    with_draw = 1; ran = 0; client_us = 2000; step_us = 500;
    iteration(1, 2000);                /* drawn; the network refused phase 1 */
    ran = 1;
    gp_mon_flush(1);
    FILE *f = fopen(path, "r"); char l[512]; int nrec = 0, okr = 0;
    unsigned long v[16];
    while (f && fgets(l, sizeof l, f)) {
        long long q;
        int k = sscanf(l, "f %lld %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu %lu", &q, &v[0], &v[1], &v[2],
                       &v[3], &v[4], &v[5], &v[6], &v[7], &v[8], &v[9], &v[10], &v[11], &v[12], &v[13], &v[14]);
        if (k != 16) continue;
        unsigned long *s = &v[7];   /* client draw present logic phases wait iter iters */
        nrec++;
        printf("    record %d: client %lu us, draw %lu, present %lu, logic %lu, phases %#lx, wait %lu, iter %lu, iters %lu\n",
               nrec, s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]);
        if (nrec == 1)
            okr += s[0] >= 3450 && s[1] >= 1450 && s[2] >= 480 && s[3] >= 2950 && s[4] == 0x10 && s[5] >= 3950 &&
                   s[6] >= s[0] + s[3] + s[5] && s[7] == 1 && s[2] <= s[1] && s[1] <= s[0];
        if (nrec == 2)
            okr += s[0] >= 4450 && s[3] >= 1450 && s[4] == (0x20 | 0x80) && s[5] >= 1950 && s[5] < 4000 &&
                   s[6] >= s[0] + s[3] + s[5] && s[7] == 2;
    }
    if (f) fclose(f);
    printf("[3] %d frame records with a split (expected 2 after the warm-up): %s\n", nrec, okr == 2 && nrec == 2 ? "as scripted" : "WRONG");
    fail |= okr != 2 || nrec != 2;

    /* [4] */
    client_us = draw_us = present_us = step_us = 0;
    uint64_t t0 = now_us();
    for (int i = 0; i < 20000; i++) { iteration(2, 0); if ((i & 1023) == 1023) gp_mon_flush(0); }
    double per = (now_us() - t0) / 20000.0;
    printf("[4] one engine iteration through the stubs (10 marks, a frame record): %.2f us\n", per);
    fail |= per > 50;
    *(uint32_t *)0xbd0920 = iat;
    gp_mon_exit();
    DeleteFileA(path);
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
