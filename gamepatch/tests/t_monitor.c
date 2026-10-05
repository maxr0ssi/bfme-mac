/* t_monitor: monitor (p_monitor.c) against the original exe.
 *  [1] the patch applies to the original bytes (8 thunks checked, nothing written there) and turns each
 *      of the 12 call sites into a call to its wrapper; the wrappers call the thunk the site called;
 *  [2] each wrapper hands its arguments in order to the callee, returns the callee's eax, pops exactly
 *      what the import pops (stdcall, Wine's d3dx9_27.spec), keeps ebx, esi, edi, ebp, and counts one
 *      call of its kind with a positive time;
 *  [3] frame records: one "f" line per frame with the D3DX calls since the previous frame, an "s" line
 *      with the object count of a fake TheGameLogic list, -2 (no fault) when a next pointer leads to
 *      unmapped memory, "t" and "m" lines;
 *  [4] costs: the frame hook, the object walk (3000 objects) and the address-space walk.
 * usage: t_monitor.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* h_calln(fn, n, args): push args (last first), call fn with magic ebx/esi/edi/ebp, record eax, the
 * callee-saved registers and how far esp is from where it was before the pushes */
uint32_t h_ret, h_regs[4], h_saved_ebp; int32_t h_espdiff;
uint32_t h_calln(void *fn, int n, const uint32_t *args);
__asm__(".intel_syntax noprefix\n.text\n.globl _h_calln\n_h_calln:\n"
        "  push ebp\n  mov ebp, esp\n  push ebx\n  push esi\n  push edi\n"
        "  mov ecx, [ebp+12]\n  mov esi, [ebp+16]\n"
        "1:\n  test ecx, ecx\n  jz 2f\n  push dword ptr [esi+ecx*4-4]\n  dec ecx\n  jmp 1b\n"
        "2:\n  mov eax, [ebp+8]\n  mov [_h_saved_ebp], ebp\n  mov ebx, 0x33333333\n  mov esi, 0x55555555\n  mov edi, 0x66666666\n"
        "  mov ebp, 0x77777777\n  call eax\n  mov [_h_regs+12], ebp\n  mov ebp, [_h_saved_ebp]\n"
        "  mov [_h_ret], eax\n  mov [_h_regs], ebx\n  mov [_h_regs+4], esi\n  mov [_h_regs+8], edi\n"
        "  lea eax, [ebp-12]\n  sub eax, esp\n  mov [_h_espdiff], eax\n"
        "  lea esp, [ebp-12]\n  pop edi\n  pop esi\n  pop ebx\n  pop ebp\n  ret\n.att_syntax\n");

/* fakes with the imports' arities: record the arguments, spin a little, return a tag */
static uint32_t seen[16]; static int seen_n;
static void spin(void) { uint64_t t = now_us(); while (now_us() - t < 50) ; }
#define F(n, ...) static HRESULT WINAPI fake##n(__VA_ARGS__)
typedef uint32_t A;
F(8, A a, A b, A c, A d, A e, A f, A g, A h)
{ A v[] = {a, b, c, d, e, f, g, h}; memcpy(seen, v, sizeof v); seen_n = 8; spin(); return 0x1008; }
F(9, A a, A b, A c, A d, A e, A f, A g, A h, A i)
{ A v[] = {a, b, c, d, e, f, g, h, i}; memcpy(seen, v, sizeof v); seen_n = 9; spin(); return 0x1009; }
F(14, A a, A b, A c, A d, A e, A f, A g, A h, A i, A j, A k, A l, A m, A n)
{ A v[] = {a, b, c, d, e, f, g, h, i, j, k, l, m, n}; memcpy(seen, v, sizeof v); seen_n = 14; spin(); return 0x100e; }
F(15, A a, A b, A c, A d, A e, A f, A g, A h, A i, A j, A k, A l, A m, A n, A o)
{ A v[] = {a, b, c, d, e, f, g, h, i, j, k, l, m, n, o}; memcpy(seen, v, sizeof v); seen_n = 15; spin(); return 0x100f; }
F(16, A a, A b, A c, A d, A e, A f, A g, A h, A i, A j, A k, A l, A m, A n, A o, A p)
{ A v[] = {a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p}; memcpy(seen, v, sizeof v); seen_n = 16; spin(); return 0x1010; }

#define gp_mon_texload gp_mon_wrappers[0]
#define gp_mon_surfload gp_mon_wrappers[1]
#define gp_mon_cubeload gp_mon_wrappers[2]
#define gp_mon_volload gp_mon_wrappers[3]
#define gp_mon_create gp_mon_wrappers[4]
#define gp_mon_volcreate gp_mon_wrappers[5]
#define gp_mon_fx gp_mon_wrappers[6]
#define gp_mon_fxfile gp_mon_wrappers[7]

static int count_lines(const char *path, char kind, char *last, size_t n)
{
    FILE *f = fopen(path, "r"); char l[256]; int c = 0;
    if (!f) return -1;
    while (fgets(l, sizeof l, f)) if (l[0] == kind && l[1] == ' ') { c++; if (last) snprintf(last, n, "%s", l); }
    fclose(f);
    return c;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    MEMORY_BASIC_INFORMATION mi;
    VirtualQuery((void *)0xde0000, &mi, sizeof mi);
    if (mi.State == MEM_FREE && !VirtualAlloc((void *)0xde0000, 0x10000, MEM_RESERVE, PAGE_READWRITE)) {
        printf("cannot reserve 00de0000\n"); return 2;
    }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xde4000, 0x1000, 0)) return 2;
    uint32_t OFF = orig_reserve_image();
    if (!OFF) return 2;
    static const uint32_t pages[] = {0x520000, 0x530000, 0x531000, 0x551000, 0xa3e000};
    for (unsigned i = 0; i < sizeof pages / 4; i++) if (orig_map_at(pages[i], 0x1000, OFF)) return 2;
    char path[MAX_PATH];
    GetTempPathA(sizeof path, path); strcat(path, "t_monitor-game.txt");
    SetEnvironmentVariableA("GAMEPATCH_MONITOR", path);
    gp_mon_start_writer = 0;
    int fail = 0;

    /* [1] */
    const struct { uint32_t va, thunk; void *fn; } sites[] = {
        {0x530ef3, 0xa3ecea, gp_mon_texload}, {0x53117e, 0xa3ecea, gp_mon_texload}, {0x530ec2, 0xa3ecf0, gp_mon_surfload},
        {0x531515, 0xa3ed0e, gp_mon_cubeload}, {0x53147c, 0xa3ed08, gp_mon_volload}, {0x5200d6, 0xa3ece4, gp_mon_create},
        {0x520112, 0xa3ece4, gp_mon_create}, {0x530e8c, 0xa3ece4, gp_mon_create}, {0x531100, 0xa3ece4, gp_mon_create},
        {0x53132e, 0xa3ed02, gp_mon_volcreate}, {0x551356, 0xa3ed20, gp_mon_fx}, {0x5513a3, 0xa3ed1a, gp_mon_fxfile}};
    uint8_t th[0x60]; memcpy(th, (void *)(uintptr_t)(0xa3ece4 + OFF), sizeof th);
    gp_va_offset = OFF;
    int ok = gp_patch_monitor();
    gp_va_offset = 0;
    int wrong = memcmp(th, (void *)(uintptr_t)(0xa3ece4 + OFF), sizeof th) != 0;
    for (unsigned i = 0; i < 12; i++) {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(sites[i].va + OFF);
        int32_t rel; memcpy(&rel, p + 1, 4);
        wrong += p[0] != 0xe8 || (uint32_t)(uintptr_t)(p + 5) + (uint32_t)rel != (uint32_t)(uintptr_t)sites[i].fn;
    }
    static const uint32_t thunk_of[8] = {0xa3ecea, 0xa3ecf0, 0xa3ed0e, 0xa3ed08, 0xa3ece4, 0xa3ed02, 0xa3ed20, 0xa3ed1a};
    for (int i = 0; i < 8; i++) wrong += gp_mon_fn[i] != thunk_of[i] + OFF;
    printf("[1] patch applied %d, 12 sites and 8 thunk targets: %s\n", ok, wrong ? "WRONG" : "ok");
    fail |= !ok || wrong;

    /* [2] */
    const struct { void *w; void *fake; int n, kind; uint32_t ret; } ws[] = {
        {gp_mon_texload, fake15, 15, 0, 0x100f}, {gp_mon_surfload, fake9, 9, 0, 0x1009}, {gp_mon_cubeload, fake14, 14, 0, 0x100e},
        {gp_mon_volload, fake16, 16, 0, 0x1010}, {gp_mon_create, fake8, 8, 1, 0x1008}, {gp_mon_volcreate, fake9, 9, 1, 0x1009},
        {gp_mon_fx, fake9, 9, 2, 0x1009}, {gp_mon_fxfile, fake8, 8, 2, 0x1008}};
    for (int i = 0; i < 8; i++) gp_mon_fn[i] = (uint32_t)(uintptr_t)ws[i].fake;
    int bad2 = 0;
    for (int i = 0; i < 8; i++) {
        uint32_t args[16];
        for (int k = 0; k < 16; k++) args[k] = 0xa0000000u + i * 0x100 + k;
        seen_n = 0; memset(seen, 0, sizeof seen);
        h_calln(ws[i].w, ws[i].n, args);
        int b = h_ret != ws[i].ret || h_espdiff != 0 || seen_n != ws[i].n || memcmp(seen, args, 4 * ws[i].n) ||
                h_regs[0] != 0x33333333 || h_regs[1] != 0x55555555 || h_regs[2] != 0x66666666 || h_regs[3] != 0x77777777;
        if (b) printf("    wrapper %d: ret %08x esp %+d args %d regs %08x %08x %08x %08x\n", i, h_ret, h_espdiff, seen_n,
                      h_regs[0], h_regs[1], h_regs[2], h_regs[3]);
        bad2 += b;
    }
    printf("[2] 8 wrappers: arguments, return value, stack and callee-saved registers: %s\n", bad2 ? "WRONG" : "ok");
    fail |= bad2 != 0;

    /* [3] a fake TheGameLogic with 3000 objects (next at +0x8c) */
    enum { NOBJ = 3000 };
    uint8_t *gl = VirtualAlloc(NULL, 0x1000, MEM_COMMIT, PAGE_READWRITE);
    uint8_t *objs = VirtualAlloc(NULL, NOBJ * 0x400, MEM_COMMIT, PAGE_READWRITE);
    for (int i = 0; i < NOBJ; i++) *(uint32_t *)(objs + i * 0x400 + 0x8c) = i + 1 < NOBJ ? (uint32_t)(uintptr_t)(objs + (i + 1) * 0x400) : 0;
    *(uint32_t *)(gl + 0xac) = (uint32_t)(uintptr_t)objs; *(uint32_t *)(gl + 0x40) = 1234; *(uint32_t *)(gl + 0x110) = 3;
    *(volatile uint32_t *)0xde412c = (uint32_t)(uintptr_t)gl;
    gp_mon_frame(); gp_mon_flush(0);
    h_calln(gp_mon_texload, 15, (uint32_t[16]){0}); h_calln(gp_mon_create, 8, (uint32_t[16]){0});
    Sleep(1100);
    gp_mon_frame(); gp_mon_frame(); gp_mon_flush(1);
    char last_f[256] = "", last_s[256] = "", last_m[256] = "";
    int nf = count_lines(path, 'f', last_f, sizeof last_f), ns = count_lines(path, 's', last_s, sizeof last_s);
    int nt = count_lines(path, 't', NULL, 0), nm = count_lines(path, 'm', last_m, sizeof last_m);
    long long q; unsigned long lg; long ln, lt, cn, ct, fn, ft, so, sm;
    int okf = 0, oks = 0;
    FILE *f = fopen(path, "r"); char l[256];
    while (f && fgets(l, sizeof l, f)) {   /* the first frame after the two calls carries them */
        if (sscanf(l, "f %lld %lu %ld %ld %ld %ld %ld %ld", &q, &lg, &ln, &lt, &cn, &ct, &fn, &ft) == 8 && ln == 1)
            okf = lg == 1234 && cn == 1 && fn == 0 && lt > 0 && ct > 0;
        if (sscanf(l, "s %lld %ld %ld", &q, &so, &sm) == 3) oks = so == NOBJ && sm == 3;
    }
    if (f) fclose(f);
    printf("[3] lines f %d, s %d, t %d, m %d; frame with the calls %s; objects %s\n    %s    %s    %s", nf, ns, nt, nm,
           okf ? "ok" : "WRONG", oks ? "ok" : "WRONG", last_f, last_s, last_m);
    fail |= nf != 2 || ns < 1 || nt < 1 || nm < 1 || !okf || !oks;
    /* a next pointer into unmapped memory ends the walk with -2 */
    *(uint32_t *)(objs + 10 * 0x400 + 0x8c) = 0x7ff00000;
    Sleep(1100); gp_mon_frame(); gp_mon_flush(0);
    count_lines(path, 's', last_s, sizeof last_s);
    int okbad = sscanf(last_s, "s %lld %ld", &q, &so) == 2 && so == -2;
    printf("    unmapped next pointer: %s (%s", okbad ? "ok" : "WRONG", last_s);
    fail |= !okbad;
    *(uint32_t *)(objs + 10 * 0x400 + 0x8c) = (uint32_t)(uintptr_t)(objs + 11 * 0x400);

    /* [4] costs */
    uint64_t t0 = now_us();
    for (int i = 0; i < 4000; i++) { gp_mon_frame(); if ((i & 1023) == 1023) gp_mon_flush(0); }
    double frame_us = (now_us() - t0) / 4000.0;
    Sleep(1100); gp_mon_frame(); gp_mon_flush(0);
    count_lines(path, 's', last_s, sizeof last_s);
    long walk_us = 0; sscanf(last_s, "s %lld %ld %ld %lu %ld", &q, &so, &sm, &lg, &walk_us);
    LONG v[7]; gp_mon_vm(v);
    printf("[4] frame hook %.2f us per frame (incl. the writer); object walk %ld us for %d objects (once a second); "
           "address-space walk %ld us, %ld regions (every 2 s, writer thread): committed %ld MB, reserved %ld, free %ld, "
           "largest free %ld, of %ld MB\n", frame_us, walk_us, NOBJ, v[5], v[4], v[0], v[1], v[2], v[3], v[6]);
    fail |= frame_us > 50 || v[0] <= 0 || v[2] <= 0;
    gp_mon_exit();
    DeleteFileA(path);
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
