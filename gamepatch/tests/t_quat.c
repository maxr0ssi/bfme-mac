/* t_quat: gp_quat2mat (replacing 0xb26100, quaternion -> matrix) against the original x87 bytes:
 * unit quaternions as the animation code produces, random and wide-range floats, specials; all
 * 12 floats of the output matrix compared (the translation column must stay untouched).
 * usage: t_quat.exe <path to lotrbfme2ep1.exe 2.02> [millions] */
#include "orig.h"
#include "gp.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <xmmintrin.h>

__asm__(".text\n"
"_call_this1:\n"          /* cdecl (fn, this, arg): thiscall with one stack argument */
"  movl 4(%esp), %eax\n  movl 8(%esp), %ecx\n"
"  pushl 12(%esp)\n"
"  call *%eax\n"
"  ret\n");
void call_this1(void *fn, void *self, void *arg);

static uint32_t rng = 777;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static float fbits(uint32_t u) { union { uint32_t u; float f; } c = { u }; return c.f; }

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    double millions = argc > 2 ? atof(argv[2]) : 20;
    const uint8_t *code = orig_bytes(0xb26100, 0xcd);
    if (gp_fnv1a(code, 0xcd) != GP_FNV_B26100) { printf("quaternion code differs\n"); return 2; }
    if (orig_map_at(0xbd2000, 0x1000, 0)) return 2;              /* the double 1.0 at 0xbd2c98 */
    void *orig = orig_copy(0xb26100, 0xcd, 0);
    gp_quat2mat_cont = (uint32_t)(uintptr_t)orig + 7;
    unsigned short cw = 0x007f;
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));
    _mm_setcsr(0x1f80);
    uint64_t n = 0, bad = 0, total = (uint64_t)(millions * 1e6);
    for (uint64_t it = 0; it < total; it++) {
        float q[4], a[12], b[12];
        int kind = rnd() % 5;
        for (int k = 0; k < 4; k++) {
            if (kind <= 1) q[k] = (float)((int)(rnd() % 20001) - 10000) / 10000.0f;
            else if (kind == 2) q[k] = fbits((rnd() & 0x807fffff) | ((uint32_t)(40 + rnd() % 175) << 23));
            else if (kind == 3) q[k] = fbits(rnd());
            else q[k] = rnd() % 3 ? fbits((rnd() & 0x807fffff) | ((uint32_t)(110 + rnd() % 30) << 23)) : 0.0f;
        }
        if (kind == 0) {   /* normalise, like the game's own quaternions */
            float l = sqrtf(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
            if (l > 0) for (int k = 0; k < 4; k++) q[k] /= l;
        }
        for (int k = 0; k < 12; k++) a[k] = b[k] = fbits(0x7fc00000u + k);
        call_this1(orig, a, q);
        call_this1((void *)gp_quat2mat, b, q);
        n++;
        if (memcmp(a, b, sizeof a)) {
            if (bad < 5) printf("  MISMATCH q = %08x %08x %08x %08x\n", *(uint32_t *)&q[0], *(uint32_t *)&q[1],
                                *(uint32_t *)&q[2], *(uint32_t *)&q[3]);
            bad++;
        }
    }
    printf("[1] %llu quaternions: %llu mismatches (12 floats each); %ld ran the x87 original (flags)\n",
           n, bad, gp_quat2mat_fallbacks);
    {
        float q[4] = {0.1f, 0.2f, 0.3f, 0.927f}, m[12]; const int N = 1000000;
        uint64_t s0 = now_us(); for (int i = 0; i < N; i++) call_this1(orig, m, q);
        uint64_t s1 = now_us(); for (int i = 0; i < N; i++) call_this1((void *)gp_quat2mat, m, q);
        uint64_t s2 = now_us();
        printf("[2] per call: original %.0f ns, replacement %.0f ns\n", (s1 - s0) * 1000.0 / N, (s2 - s1) * 1000.0 / N);
    }
    printf("%s\n", bad ? "FAIL" : "PASS");
    return bad != 0;
}
