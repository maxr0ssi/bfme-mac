/* Full-state call harness for t_logic: runs a function from a given machine state (general
 * registers, xmm0-7, x87 control word, MXCSR, stack arguments) and records everything it leaves:
 * general registers, xmm0-7, the stack pointer, the argument slots (callees may write them) plus
 * two canaries above them, MXCSR and the complete x87 state (fnsave). Two runs compare with
 * lm_same(): every general register (except those in a mask, with the reason in the caller),
 * all 128 bits of xmm0-7, esp, argument slots and canaries, MXCSR control bits (the sticky
 * exception flags are not compared: the game reads them nowhere but once at startup), x87
 * control word, stack top, tags, and all 80 bits of every non-empty x87 register. */
#ifndef LM_HARNESS_H
#define LM_HARNESS_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>

typedef struct {
    uint32_t fn, nargs, args[8];            /*   0,   4,   8 */
    uint32_t in[7], out[7];                 /*  40,  68: eax ebx ecx edx esi edi ebp */
    uint8_t xin[128], xout[128];            /*  96, 224 */
    int32_t esp_delta;                      /* 352 */
    uint32_t argsout[10];                   /* 356: arguments, then the two canaries */
    uint32_t cw, mxcsr, mxcsr_out;          /* 396, 400, 404 */
    uint8_t fpu[108];                       /* 408 */
} hc_t;
_Static_assert(offsetof(hc_t, xout) == 224 && offsetof(hc_t, esp_delta) == 352 &&
               offsetof(hc_t, cw) == 396 && offsetof(hc_t, fpu) == 408, "hc_t layout");

hc_t *hc_cur; uint32_t hc_argbase, hc_target, hc_eax;
__asm__(".text\n"
"_hc_call:\n"
"  pushl %ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n"
"  movl 20(%esp), %eax\n  movl %eax, _hc_cur\n"
"  fninit\n  fldcw 396(%eax)\n  ldmxcsr 400(%eax)\n"
"  movups 96(%eax), %xmm0\n  movups 112(%eax), %xmm1\n  movups 128(%eax), %xmm2\n  movups 144(%eax), %xmm3\n"
"  movups 160(%eax), %xmm4\n  movups 176(%eax), %xmm5\n  movups 192(%eax), %xmm6\n  movups 208(%eax), %xmm7\n"
"  pushl $0xc0ffee01\n  pushl $0xc0ffee02\n"
"  movl 4(%eax), %ecx\n"
"1: testl %ecx, %ecx\n  jz 2f\n  pushl 4(%eax,%ecx,4)\n  decl %ecx\n  jmp 1b\n"
"2: movl %esp, _hc_argbase\n  movl (%eax), %ecx\n  movl %ecx, _hc_target\n"
"  movl 44(%eax), %ebx\n  movl 48(%eax), %ecx\n  movl 52(%eax), %edx\n  movl 56(%eax), %esi\n"
"  movl 60(%eax), %edi\n  movl 64(%eax), %ebp\n  movl 40(%eax), %eax\n"
"  call *_hc_target\n"
"  movl %eax, _hc_eax\n  movl _hc_cur, %eax\n"
"  movl %ebx, 72(%eax)\n  movl %ecx, 76(%eax)\n  movl %edx, 80(%eax)\n  movl %esi, 84(%eax)\n"
"  movl %edi, 88(%eax)\n  movl %ebp, 92(%eax)\n  movl _hc_eax, %ecx\n  movl %ecx, 68(%eax)\n"
"  movl %esp, %ecx\n  subl _hc_argbase, %ecx\n  movl %ecx, 352(%eax)\n"
"  movl _hc_argbase, %esi\n  leal 356(%eax), %edi\n  movl 4(%eax), %ecx\n  addl $2, %ecx\n  cld\n  rep movsl\n"
"  movups %xmm0, 224(%eax)\n  movups %xmm1, 240(%eax)\n  movups %xmm2, 256(%eax)\n  movups %xmm3, 272(%eax)\n"
"  movups %xmm4, 288(%eax)\n  movups %xmm5, 304(%eax)\n  movups %xmm6, 320(%eax)\n  movups %xmm7, 336(%eax)\n"
"  stmxcsr 404(%eax)\n  fnsave 408(%eax)\n"
"  movl 4(%eax), %ecx\n  movl _hc_argbase, %esp\n  leal 8(%esp,%ecx,4), %esp\n"
"  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n");
void hc_call(hc_t *c);

static const char *hc_rn[7] = {"eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"};

/* why two runs differ ("" = identical); gp_ok / x_ok: general registers (bit r as in hc_rn) /
 * xmm registers (bit x) not compared */
static const char *hc_diff(const hc_t *a, const hc_t *b, unsigned gp_ok, unsigned x_ok)
{
    static char why[96];
    for (int r = 0; r < 7; r++)
        if (!(gp_ok >> r & 1) && a->out[r] != b->out[r]) { snprintf(why, sizeof why, "%s %08x vs %08x", hc_rn[r], a->out[r], b->out[r]); return why; }
    for (int x = 0; x < 8; x++)
        if (!(x_ok >> x & 1) && memcmp(a->xout + 16 * x, b->xout + 16 * x, 16)) { snprintf(why, sizeof why, "xmm%d", x); return why; }
    if (a->esp_delta != b->esp_delta) return "esp";
    if (memcmp(a->argsout, b->argsout, 4 * (a->nargs + 2))) return "argument slots";
    if ((a->mxcsr_out & 0xffc0) != (b->mxcsr_out & 0xffc0)) return "MXCSR control";
    const uint8_t *fa = a->fpu, *fb = b->fpu;
    if (*(const uint16_t *)fa != *(const uint16_t *)fb) return "x87 control word";
    unsigned ta = fa[5] >> 3 & 7, tb = fb[5] >> 3 & 7;
    if (ta != tb) return "x87 stack top";
    uint16_t twa = *(const uint16_t *)(fa + 8), twb = *(const uint16_t *)(fb + 8);
    for (int i = 0; i < 8; i++) {
        unsigned p = (ta + i) & 7, ga = twa >> 2 * p & 3, gb = twb >> 2 * p & 3;
        if ((ga == 3) != (gb == 3)) { snprintf(why, sizeof why, "x87 st(%d) empty in one run only", i); return why; }
        if (ga != 3 && memcmp(fa + 28 + 10 * i, fb + 28 + 10 * i, 10)) { snprintf(why, sizeof why, "x87 st(%d)", i); return why; }
    }
    return "";
}

/* a starting state: register patterns, the game's FPU mode unless cw/mxcsr are set after */
static void hc_init(hc_t *c, uint32_t fn, unsigned nargs)
{
    memset(c, 0, sizeof *c);
    c->fn = fn; c->nargs = nargs;
    for (int r = 0; r < 7; r++) c->in[r] = 0x11111111u * (r + 1);
    for (int i = 0; i < 128; i++) c->xin[i] = (uint8_t)(0x5a ^ i * 37);
    c->cw = 0x007f; c->mxcsr = 0x1f80;
}
#endif
