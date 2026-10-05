/* Game-logic math, second batch (code and proofs in p_lmath2.S; test t_lmath2). Both target
 * logic phase 5 (docs/PERFORMANCE.md §17), which runs update lists 1-2 (PHYSICS and NORMAL: most
 * update modules, HordeContain, PhysicsBehavior), the pathfinder queue and twelve subsystems.
 *
 * crtsqrt: msvcr71!sqrt (IAT 0xbd06a0) -> SSE with Wine's exact result.
 *
 * Why (docs/PERFORMANCE.md §17): the single hottest instruction of the game logic left after the
 * logicmath patches is the fsqrt inside Wine's sqrt (msvcr71+0x7054, 1.3-1.5 % of the main thread
 * in both 2026-09-24 battle profiles). The exe calls sqrt from 104 call sites, among them the
 * pathfinder, the horde formation code (HordeContain, update list 1) and the physics and AI code
 * that logic phases 3-5 run. Under Rosetta one call costs ~240 ns (x87 fsqrt at 24-bit precision,
 * fnstcw, the _dclass call).
 *
 * Only Wine's builtin msvcr71 is replaced (its header carries "Wine builtin DLL"): on Windows the
 * game's own msvcr71 may compute sqrt differently, and a patched player must compute exactly what
 * the unpatched one on the same machine computes. Before the IAT is written, both versions run on
 * 4096 inputs in the game's FPU mode and must agree bit for bit (st0 and every register). */
#include "gp_logic.h"
#include <stdio.h>
#include <string.h>

extern uint32_t gp_sqrt_orig;
extern volatile LONG gp_l2_slots[16][16];
DWORD gp_sqrt_period_ms = 60000;
static DWORD last_tick;
static LONG last_c, last_x, busy;

static int on_sqrt, on_oct;
static LONG last_oc, last_ox;

LONG gp_l2_count(int k)
{
    LONG n = 0;
    for (int i = 0; i < 16; i++) n += gp_l2_slots[i][k];
    return n;
}
LONG gp_sqrt_count(int fallback) { return gp_l2_count(fallback); }

__attribute__((force_align_arg_pointer)) void gp_sqrt_periodic(void)
{
    DWORD t = GetTickCount();
    if (!last_tick || t - last_tick < gp_sqrt_period_ms) return;
    if (InterlockedExchange(&busy, 1)) return;
    LONG c = gp_l2_count(0) - last_c, x = gp_l2_count(1) - last_x;
    LONG oc = gp_l2_count(2) - last_oc, ox = gp_l2_count(3) - last_ox;
    last_c += c; last_x += x; last_oc += oc; last_ox += ox;
    gp_log("lmath2: last %lu s, calls: crtsqrt %lu (%lu ran Wine's sqrt) | octile %lu (%lu x87)",
           (t - last_tick) / 1000, (unsigned long)c, (unsigned long)x, (unsigned long)oc, (unsigned long)ox);
    last_tick = t;
    InterlockedExchange(&busy, 0);
}

void gp_l2_exit_log(void)
{
    if (on_sqrt | on_oct)
        gp_log("exit: lmath2 calls (fallbacks): crtsqrt %lu (%lu), octile %lu (%lu)", (unsigned long)gp_l2_count(0),
               (unsigned long)gp_l2_count(1), (unsigned long)gp_l2_count(2), (unsigned long)gp_l2_count(3));
}

/* one call in the game's FPU mode: st0 as 80 bits, eax/ecx/edx, xmm0 */
typedef struct { uint8_t st[10]; uint32_t r[3]; uint8_t x0[16]; } sq_out;
__asm__(".text\n_sq_call:\n"
"  pushl %ebp\n  movl %esp, %ebp\n  pushl %ebx\n  subl $16, %esp\n"
"  fnstcw 8(%esp)\n  stmxcsr 12(%esp)\n  movw $0x007f, (%esp)\n  fldcw (%esp)\n"
"  movl $0x1f80, (%esp)\n  ldmxcsr (%esp)\n"
"  movl 16(%ebp), %eax\n  movl 12(%ebp), %ecx\n  movl %eax, 4(%esp)\n  movl %ecx, (%esp)\n"
"  movl $0x5a5a5a5a, %eax\n  movl %eax, %ecx\n  movl %eax, %edx\n  movd %eax, %xmm0\n"
"  call *8(%ebp)\n"
"  movl 20(%ebp), %ebx\n  fstpt (%ebx)\n  movl %eax, 12(%ebx)\n  movl %ecx, 16(%ebx)\n  movl %edx, 20(%ebx)\n"
"  movups %xmm0, 24(%ebx)\n  fldcw 8(%esp)\n  ldmxcsr 12(%esp)\n  addl $16, %esp\n  popl %ebx\n  popl %ebp\n  ret\n");
void sq_call(void *fn, uint32_t lo, uint32_t hi, sq_out *o);

int gp_sqrt_selftest(void *crt)
{
    uint32_t s = 0x9e3779b9u;
    for (int i = 0; i < 4096; i++) {
        s ^= s << 13; s ^= s >> 17; s ^= s << 5;
        uint32_t lo = s * 0x2545f491u, hi;
        switch (i & 3) {                   /* any double; float-valued; near-integers; tiny */
        case 0:  hi = s & 0x7fefffffu; break;
        case 1:  hi = 0x38000000u + (s & 0x0fffffffu); lo &= 0xe0000000u; break;
        case 2:  hi = 0x3ff00000u + (s & 0x03ffffffu); lo = 0; break;
        default: hi = s & 0x000fffffu; break;
        }
        sq_out a, b;
        memset(&a, 0, sizeof a); memset(&b, 0, sizeof b);
        sq_call(crt, lo, hi, &a);
        sq_call((void *)gp_sqrt, lo, hi, &b);
        if (memcmp(&a, &b, sizeof a)) return 0;
    }
    return 1;
}

int gp_patch_crtsqrt(void)
{
    HMODULE crt = GetModuleHandleA("msvcr71.dll");
    FARPROC f = crt ? GetProcAddress(crt, "sqrt") : NULL;
    if (!f) { gp_log("crtsqrt: msvcr71 sqrt not found; patch skipped"); return 0; }
    if (memcmp((const char *)crt + 0x40, "Wine builtin DLL", 16)) {
        gp_log("crtsqrt: msvcr71 is not Wine's builtin (Windows?); patch skipped");
        return 0;
    }
    gp_sqrt_orig = (uint32_t)(uintptr_t)f;
    if (!gp_sqrt_selftest((void *)f)) {
        gp_log("crtsqrt: self-test against Wine's sqrt failed; patch skipped");
        return 0;
    }
    static uint32_t of; of = (uint32_t)(uintptr_t)f;
    uint32_t nf = (uint32_t)(uintptr_t)gp_sqrt;
    gp_site s;
    gp_site_init(&s, 0xbd06a0, (const uint8_t *)&of, 4);
    memcpy(s.repl, &nf, 4);
    if (!gp_apply("crtsqrt", &s, 1)) return 0;
    on_sqrt = 1; last_tick = GetTickCount() | 1;
    return 1;
}

/* octile: 0x7658c3 (path segment cost, 0x82 bytes) -> SSE. Its x87 fallback calls the CRT's fabs
 * through 0xa3cf8a, and the registers it leaves (eax, edx) are Wine's fabs's, so like crtsqrt it is
 * installed only when the fabs import is Wine's builtin. */
int gp_patch_octile(void)
{
    static const uint8_t head[] = {0x55, 0x8b,0xec, 0x56, 0x8b,0x75,0x08};   /* push ebp; mov ebp,esp; push esi; mov esi,[ebp+8] */
    static const uint8_t quarter[] = {0x00,0x00,0x80,0x3e}, thunk[] = {0xff,0x25,0xa8,0x06,0xbd,0x00};
    HMODULE crt = GetModuleHandleA("msvcr71.dll");
    FARPROC f = crt ? GetProcAddress(crt, "fabs") : NULL;
    if (!f || memcmp((const char *)crt + 0x40, "Wine builtin DLL", 16)) {
        gp_log("octile: msvcr71 is not Wine's builtin (Windows?); patch skipped");
        return 0;
    }
    static uint32_t of; of = (uint32_t)(uintptr_t)f;
    gp_site s[5];
    gp_site_hash(&s[0], 0x7658c3, 0x82, GP_FNV_7658C3);
    gp_site_init(&s[1], 0xbd1904, quarter, 4); s[1].wlen = 0;
    gp_site_init(&s[2], 0xa3cf8a, thunk, 6); s[2].wlen = 0;         /* jmp [0xbd06a8] */
    gp_site_init(&s[3], 0xbd06a8, (const uint8_t *)&of, 4); s[3].wlen = 0;   /* -> Wine's fabs */
    gp_site_init(&s[4], 0x7658c3, head, sizeof head);
    gp_rel32(&s[4], 0, 0xe9, (void *)gp_octile);
    s[4].repl[5] = s[4].repl[6] = 0x90;
    gp_oct_cont = 0x7658ca + gp_va_offset;
    if (!gp_apply("octile", s, 5)) return 0;
    on_oct = 1; if (!last_tick) last_tick = GetTickCount() | 1;
    return 1;
}
