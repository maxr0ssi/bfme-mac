/* t_regs: register discipline. The exe was built with whole-program optimisation, so a caller may
 * keep values in registers a callee is known not to touch. For each replacement, run the original
 * and the replacement from the same register state (all general registers and xmm0-7 set to
 * patterns) and require every register the original leaves unchanged to be unchanged by the
 * replacement too, and the same stack pointer on return.
 * usage: t_regs.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <xmmintrin.h>

typedef struct {
    uint32_t fn, nargs, args[4];   /*   0,   4,   8 */
    uint32_t in[7], out[7];        /*  24,  52: eax ebx ecx edx esi edi ebp */
    uint8_t xin[128], xout[128];   /*  80, 208 */
    int32_t esp_delta;             /* 336 */
} ctx_t;
_Static_assert(offsetof(ctx_t, xout) == 208 && offsetof(ctx_t, esp_delta) == 336, "layout");
ctx_t *cur; uint32_t saved_esp, target;

__asm__(".text\n"
"_regcall:\n"
"  pushl %ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n"
"  movl 20(%esp), %eax\n  movl %eax, _cur\n  movl %esp, _saved_esp\n"
"  movups 80(%eax), %xmm0\n  movups 96(%eax), %xmm1\n  movups 112(%eax), %xmm2\n  movups 128(%eax), %xmm3\n"
"  movups 144(%eax), %xmm4\n  movups 160(%eax), %xmm5\n  movups 176(%eax), %xmm6\n  movups 192(%eax), %xmm7\n"
"  movl 4(%eax), %ecx\n"
"1: testl %ecx, %ecx\n  jz 2f\n  pushl 4(%eax,%ecx,4)\n  decl %ecx\n  jmp 1b\n"
"2: movl (%eax), %ecx\n  movl %ecx, _target\n"
"  movl 28(%eax), %ebx\n  movl 32(%eax), %ecx\n  movl 36(%eax), %edx\n  movl 40(%eax), %esi\n"
"  movl 44(%eax), %edi\n  movl 48(%eax), %ebp\n  movl 24(%eax), %eax\n"
"  call *_target\n"
"  pushl %eax\n  movl _cur, %eax\n  popl 52(%eax)\n"
"  movl %ebx, 56(%eax)\n  movl %ecx, 60(%eax)\n  movl %edx, 64(%eax)\n  movl %esi, 68(%eax)\n"
"  movl %edi, 72(%eax)\n  movl %ebp, 76(%eax)\n"
"  movups %xmm0, 208(%eax)\n  movups %xmm1, 224(%eax)\n  movups %xmm2, 240(%eax)\n  movups %xmm3, 256(%eax)\n"
"  movups %xmm4, 272(%eax)\n  movups %xmm5, 288(%eax)\n  movups %xmm6, 304(%eax)\n  movups %xmm7, 320(%eax)\n"
"  movl %esp, %ecx\n  subl _saved_esp, %ecx\n  movl %ecx, 336(%eax)\n"
"  movl _saved_esp, %esp\n"
"  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n");
void regcall(ctx_t *c);

static const char *rn[7] = {"eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"};
static int fails;

static void game_modes(void)
{
    unsigned short cw = 0x007f;
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));
    _mm_setcsr(0x1f80);
}

/* run orig and repl from the same state; everything orig preserves, repl must preserve, except
 * registers in gp_ok / x_ok (bit r = general register r, bit x = xmm x): for the two normalize
 * tails, the registers their enclosing function writes on every path to the tail anyway */
static void compare_m(const char *name, void *orig, void *repl, ctx_t *base, unsigned gp_ok, unsigned x_ok)
{
    ctx_t a = *base, b = *base;
    for (int i = 0; i < 128; i++) a.xin[i] = b.xin[i] = (uint8_t)(0x5a ^ i * 37);
    a.fn = (uint32_t)(uintptr_t)orig; b.fn = (uint32_t)(uintptr_t)repl;
    game_modes(); regcall(&a);
    game_modes(); regcall(&b);
    game_modes();
    int bad = 0;
    for (int r = 0; r < 7; r++)
        if (a.out[r] == a.in[r] && b.out[r] != b.in[r] && !(gp_ok >> r & 1)) { printf("  %s: %s changed (original keeps it)\n", name, rn[r]); bad++; }
    for (int x = 0; x < 8; x++)
        if (!memcmp(a.xout + 16 * x, a.xin + 16 * x, 16) && memcmp(b.xout + 16 * x, b.xin + 16 * x, 16) &&
            !(x_ok >> x & 1)) {
            printf("  %s: xmm%d changed (original keeps it)\n", name, x); bad++;
        }
    if (a.esp_delta != b.esp_delta) { printf("  %s: esp %+d vs %+d\n", name, a.esp_delta, b.esp_delta); bad++; }
    printf("[regs] %-28s %s\n", name, bad ? "DIFFERS" : "same preserved registers and stack");
    fails += bad;
}
static void compare(const char *name, void *orig, void *repl, ctx_t *base) { compare_m(name, orig, repl, base, 0, 0); }

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xbd2000, 0x1000, 0)) return 2;              /* constants used by 0xb26100 */
    void *isq = orig_copy(0x441c56, 0x52, 0);
    gp_invsqrt_cont = (uint32_t)(uintptr_t)isq + 5; gp_invsqrt_fn = (uint32_t)(uintptr_t)isq;
    uint8_t *ht = VirtualAlloc(NULL, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(ht, orig_bytes(0xb0dfe0, 0x110), 0x110); memcpy(ht + 0x110, orig_bytes(0xb0deb0, 0x130), 0x130);
    orig_fix_rel32(ht, 0xb0dfe0, 0xb0e0b4, ht + 0x110);
    gp_hittest_cont = (uint32_t)(uintptr_t)ht + 7;
    void *qm = orig_copy(0xb26100, 0xcd, 0);
    gp_quat2mat_cont = (uint32_t)(uintptr_t)qm + 7;
    uint8_t *t3 = orig_copy(0x4f1710, 0x20, 1), *t4 = orig_copy(0xb2b875, 0x22, 1);
    orig_fix_rel32(t3, 0x4f1710, 0x4f1717, isq); orig_fix_rel32(t4, 0xb2b875, 0xb2b876, isq);
    t3[0x20] = 0xc3; t4[0x22] = 0xc3;

    ctx_t c; memset(&c, 0, sizeof c);
    for (int r = 0; r < 7; r++) c.in[r] = 0x11111111u * (r + 1);
    static float v[4] = {3, 4, 12, 5}, frame[8], m[12], q[4] = {0.1f, 0.2f, 0.3f, 0.927f};
    static float V[8] = {0, 0, 100, 0, 0, 100, 100, 100}; static int16_t I[6] = {0, 1, 2, 1, 3, 2};
    static struct { uint8_t hdr[0x14]; int count; int pad; float *v; int16_t *idx; } sh = {{0}, 2, 0, V, I};
    static float mat[6] = {1, 0, 0, 1, 10, 10};

    for (int k = 0; k < 3; k++) {       /* SSE path, x87 fallback input, and a special */
        static const uint32_t xs[3] = {0x40490fdb, 0x7f000000, 0x80000001};
        c.nargs = 1; c.args[0] = xs[k];
        char name[64]; snprintf(name, sizeof name, "invsqrt (x=%08x)", xs[k]);
        compare(name, isq, (void *)gp_invsqrt, &c);
    }
    c.nargs = 4; c.args[0] = (uint32_t)(uintptr_t)&sh; c.args[1] = (uint32_t)(uintptr_t)mat;
    c.args[2] = 50; c.args[3] = 30;  compare("hittest (inside)", ht, (void *)gp_hittest, &c);
    c.args[2] = 500; c.args[3] = 30; compare("hittest (outside)", ht, (void *)gp_hittest, &c);
    c.nargs = 1; c.args[0] = (uint32_t)(uintptr_t)q; c.in[2] = (uint32_t)(uintptr_t)m;
    compare("quatmat", qm, (void *)gp_quat2mat, &c);
    c.in[2] = 0x33333333;
    c.nargs = 0; c.in[4] = (uint32_t)(uintptr_t)v; c.in[6] = (uint32_t)(uintptr_t)frame;
    for (int k = 0; k < 2; k++) {
        union { float f; uint32_t u; } l = { k ? 1e38f : 169.0f };
        memcpy(&frame[2], &l.u, 4);                   /* [ebp+8] */
        char name[64]; snprintf(name, sizeof name, "normtail 0x4f1710 (%s)", k ? "x87 path" : "SSE path");
        /* 0x4f1613 writes ecx, edx and xmm0-7 before reaching 0x4f1710 */
        compare_m(name, t3, (void *)gp_norm_4f1710, &c, 1 << 2 | 1 << 3, 0xff);
        c.in[0] = l.u;
        snprintf(name, sizeof name, "normtail 0xb2b875 (%s)", k ? "x87 path" : "SSE path");
        /* 0xb2b720 writes ecx and xmm0-5 before reaching 0xb2b875; edx and xmm6-7 must survive */
        compare_m(name, t4, (void *)gp_norm_b2b875, &c, 1 << 2, 0x3f);
    }
    printf("%s\n", fails ? "FAIL" : "PASS");
    return fails != 0;
}
