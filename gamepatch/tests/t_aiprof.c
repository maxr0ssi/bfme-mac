/* t_aiprof: the aiprof diagnostic (p_aiprof.c / .S). Counters only, so the proof is that every stub
 * hands its target exactly what the caller would have, returns exactly what the target returns, and
 * leaves the stack as the original call would.
 *   [0] the patch applies to the original bytes (a relocated copy of the pages with its 21 sites): each
 *       site becomes a call to its stub, each stub's target is the site's original target
 *   [1] each site stub with a mock target of its signature (0, 1, 2, 4, 6 arguments popped by the
 *       target; 3 left to the caller): the target sees the caller's ecx, eax, edx and argument words
 *       (random values), the caller gets the target's eax and edx back with esp as after the original
 *       call, ebx/esi/edi/ebp unchanged, and the site's call count advances by one
 *   [2] the state stub (replaces `mov ebx, ecx; call [eax+0x18]`): ebx = ecx afterwards, the state's
 *       update called with the caller's ecx, eax, edx; its eax/edx returned
 *   [3] the state machine stub (replaces `mov [ebp-4], edi; call [eax+0x10]`): the store done in the
 *       caller's frame, the vtable's target called and timed as site 19
 *   [4] sensitivity: the checks see a wrong edx and a wrong argument word
 *   [5] overhead per timed call
 * usage: t_aiprof.exe <path to lotrbfme2ep1.exe 2.02> [thousands of calls] */
#include "orig.h"
#include "gp.h"
#include "p_ai.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t rs = 0x1234567;
static uint32_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 17; rs ^= rs << 5; return rs; }

/* what a mock target saw, and what it returns */
uint32_t m_ecx, m_eax, m_edx, m_args[8], m_ret_eax, m_ret_edx;
/* h_in = {stub, nargs, ecx, eax, edx, ebx, esi, edi, ebp, args[8]}; h_out = {eax, edx, esp delta, ebx, esi, edi, ebp} */
uint32_t h_in[17], h_out[7], h_esp;
void call_stub(void);
void mock_bad(void), mock_p0(void), mock_p4(void), mock_p8(void), mock_p16(void), mock_p24(void), mock_c(void), mock_state(void);
__asm__(".intel_syntax noprefix\n.text\n"
".macro MOCK name, pop\n.globl _\\name\n_\\name:\n"
"  mov dword ptr [_m_ecx], ecx\n  mov dword ptr [_m_eax], eax\n  mov dword ptr [_m_edx], edx\n"
"  push esi\n  push edi\n  lea esi, [esp+12]\n  lea edi, [_m_args]\n  mov ecx, 8\n  rep movsd\n  pop edi\n  pop esi\n"
"  mov eax, dword ptr [_m_ret_eax]\n  mov edx, dword ptr [_m_ret_edx]\n  mov ecx, 0x5a5a5a5a\n"
"  ret \\pop\n.endm\n"
".globl _mock_bad\n_mock_bad:\n  mov eax, dword ptr [_m_ret_eax]\n  mov edx, dword ptr [_m_ret_edx]\n  inc edx\n  ret\n"
"MOCK mock_p0, 0\nMOCK mock_p4, 4\nMOCK mock_p8, 8\nMOCK mock_p16, 16\nMOCK mock_p24, 24\nMOCK mock_c, 0\n"
".globl _mock_state\n_mock_state:\n  mov dword ptr [_m_ecx], ecx\n  mov dword ptr [_m_eax], eax\n  mov dword ptr [_m_edx], edx\n"
"  mov eax, dword ptr [_m_ret_eax]\n  mov edx, dword ptr [_m_ret_edx]\n  ret\n"
".globl _call_stub\n_call_stub:\n"
"  push ebp\n  push ebx\n  push esi\n  push edi\n"
"  mov dword ptr [_h_esp], esp\n"
"  mov ecx, dword ptr [_h_in+4]\n"
"1: test ecx, ecx\n  jz 2f\n  push dword ptr [_h_in+32+4*ecx]\n  dec ecx\n  jmp 1b\n"
"2: mov eax, dword ptr [_h_in+12]\n  mov edx, dword ptr [_h_in+16]\n  mov ebx, dword ptr [_h_in+20]\n"
"  mov esi, dword ptr [_h_in+24]\n  mov edi, dword ptr [_h_in+28]\n  mov ebp, dword ptr [_h_in+32]\n"
"  mov ecx, dword ptr [_h_in+8]\n"
"  call dword ptr [_h_in]\n"
"  mov dword ptr [_h_out], eax\n  mov dword ptr [_h_out+4], edx\n  mov dword ptr [_h_out+12], ebx\n"
"  mov dword ptr [_h_out+16], esi\n  mov dword ptr [_h_out+20], edi\n  mov dword ptr [_h_out+24], ebp\n"
"  mov eax, esp\n  sub eax, dword ptr [_h_esp]\n  mov dword ptr [_h_out+8], eax\n"
"  mov esp, dword ptr [_h_esp]\n"
"  pop edi\n  pop esi\n  pop ebx\n  pop ebp\n  ret\n"
".att_syntax prefix\n");

/* site signatures, as SITE k, n, pops in p_aiprof.S */
static const int SIG_N[21] = {0, 1, 4, 4, 2, 0, 0, 0, 0, 1, 1, 2, 2, 2, 0, 2, 2, 6, 0, 0, 3};
static const int SIG_POP[21] = {0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0};
static void *mock_for(int k)
{
    if (!SIG_POP[k]) return SIG_N[k] ? (void *)mock_c : (void *)mock_p0;
    switch (SIG_N[k]) { case 1: return mock_p4; case 2: return mock_p8; case 4: return mock_p16; default: return mock_p24; }
}
static void randomize(void)
{
    for (int i = 2; i < 17; i++) h_in[i] = rnd();
    m_ret_eax = rnd(); m_ret_edx = rnd();
}

static LONG WINAPI crash(EXCEPTION_POINTERS *e)
{
    printf("CRASH %08lx at %p\nFAIL\n", e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress);
    ExitProcess(3);
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    SetUnhandledExceptionFilter(crash);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    long nc = (argc > 2 ? atol(argv[2]) : 200) * 1000;
    if (orig_map_at(0xde4000, 0x1000, 0)) return 2;            /* TheGameLogic pointer (0: no logic frame) */
    uint32_t off = orig_reserve_image();
    static const uint32_t pages[] = {0x669000, 0x66e000, 0x882000, 0x88f000, 0x8db000, 0x90d000};
    for (unsigned i = 0; i < sizeof pages / sizeof pages[0]; i++) if (orig_map_at(pages[i], 0x1000, off)) return 2;

    /* [0] */
    static const uint32_t SITE_VA[20] = {0x882094, 0x882106, 0x882398, 0x8825f1, 0x882ad7, 0x66e70c, 0x66e702, 0x66e73a,
        0x66e890, 0x66e5b0, 0x66e65d, 0x66e5c3, 0x66e8ca, 0x6698ba, 0x66964d, 0x88f5cb, 0x88f6d7, 0x90dfb9, 0x66e732, 0x669746};
    static const uint32_t TARGET[20] = {0x66e58f, 0x881fcc, 0xa39090, 0xa39090, 0x66c4ca, 0x6695ef, 0x66c748, 0x665921,
        0x66217e, 0x756cd7, 0x756cd7, 0x62684d, 0x62684d, 0x6658d3, 0x663e32, 0x6cf3d2, 0x6cf3d2, 0xa39340, 0x664f93, 0};
    gp_va_offset = off;
    int ok = gp_patch_aiprof();
    gp_va_offset = 0;
    int bad = !ok;
    for (int k = 0; k < 20 && ok; k++) {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(SITE_VA[k] + off);
        int32_t rel; memcpy(&rel, p + 1, 4);
        uint32_t to = SITE_VA[k] + off + 5 + (uint32_t)rel;
        void *want = k == 19 ? NULL : (void *)gp_ap_stub[k];
        if (p[0] != 0xe8 || (k < 19 && (to != (uint32_t)(uintptr_t)want || gp_ap_target[k] != TARGET[k] + off))) bad++;
        if (k == 19 && p[5] != 0x90) bad++;
    }
    {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(0x8db70b + off);
        int32_t rel; memcpy(&rel, p + 1, 4);
        if (p[0] != 0xe8 || 0x8db70b + off + 5 + (uint32_t)rel != (uint32_t)(uintptr_t)gp_ap_state) bad++;
    }
    verdict(bad != 0, "[0] aiprof: %s to the original bytes (relocated copy); %d of 21 sites wrong\n", ok ? "applied" : "NOT applied", bad);

    /* [1] */
    bad = 0; long n = 0;
    for (long it = 0; it < nc; it++) {
        int k = (int)(rnd() % 21);
        if (k == 19 && rnd() % 2) k = 20;
        gp_ap_target[k] = (uint32_t)(uintptr_t)mock_for(k);
        randomize();
        h_in[0] = (uint32_t)(uintptr_t)gp_ap_stub[k]; h_in[1] = (uint32_t)SIG_N[k];
        memset(m_args, 0, sizeof m_args);
        LONG c0 = gp_ap_calls[k];
        call_stub();
        int e = m_ecx != h_in[2] || m_eax != h_in[3] || m_edx != h_in[4] || h_out[0] != m_ret_eax || h_out[1] != m_ret_edx
                || h_out[3] != h_in[5] || h_out[4] != h_in[6] || h_out[5] != h_in[7] || h_out[6] != h_in[8]
                || (int32_t)h_out[2] != (SIG_POP[k] ? 0 : -4 * SIG_N[k]) || gp_ap_calls[k] != c0 + 1;
        for (int a = 0; a < SIG_N[k]; a++) e |= m_args[a] != h_in[9 + a];
        if (e && bad < 5) printf("  MISMATCH site %d: esp %d, eax %08x/%08x\n", k, (int32_t)h_out[2], h_out[0], m_ret_eax);
        bad += e; n++;
    }
    verdict(bad != 0, "[1] %ld calls through the 21 site stubs with random registers and arguments: %d wrong\n", n, bad);

    /* [2] */
    static uint32_t vtable[16];
    vtable[6] = (uint32_t)(uintptr_t)mock_state;                   /* +0x18 */
    bad = 0; n = 0;
    for (long it = 0; it < nc / 10; it++) {
        randomize();
        h_in[0] = (uint32_t)(uintptr_t)gp_ap_state; h_in[1] = 0; h_in[3] = (uint32_t)(uintptr_t)vtable;
        call_stub();
        int e = h_out[3] != h_in[2] || m_ecx != h_in[2] || m_eax != h_in[3] || m_edx != h_in[4] || h_out[0] != m_ret_eax
                || h_out[1] != m_ret_edx || h_out[4] != h_in[6] || h_out[5] != h_in[7] || h_out[6] != h_in[8] || h_out[2] != 0;
        bad += e; n++;
    }
    verdict(bad != 0, "[2] %ld calls through the state stub: %d wrong (ebx = ecx, registers, result, stack)\n", n, bad);

    /* [3] */
    static uint32_t frame[4], smvt[8];
    smvt[4] = (uint32_t)(uintptr_t)mock_p0;                       /* +0x10 */
    void (*sm)(void) = NULL;
    {   /* the stub the site 0x669746 now calls */
        const uint8_t *p = (const uint8_t *)(uintptr_t)(0x669746 + off);
        int32_t rel; memcpy(&rel, p + 1, 4);
        sm = (void (*)(void))(uintptr_t)(0x669746 + off + 5 + (uint32_t)rel);
    }
    bad = 0; n = 0;
    for (long it = 0; it < nc / 10; it++) {
        randomize();
        h_in[0] = (uint32_t)(uintptr_t)sm; h_in[1] = 0; h_in[3] = (uint32_t)(uintptr_t)smvt;
        h_in[8] = (uint32_t)(uintptr_t)&frame[2];                  /* ebp: [ebp-4] = frame[1] */
        frame[1] = 0;
        LONG c0 = gp_ap_calls[19];
        call_stub();
        int e = frame[1] != h_in[7] || m_ecx != h_in[2] || h_out[0] != m_ret_eax || h_out[1] != m_ret_edx || h_out[2] != 0
                || gp_ap_calls[19] != c0 + 1 || gp_ap_target[19] != (uint32_t)(uintptr_t)mock_p0;
        bad += e; n++;
    }
    verdict(bad != 0, "[3] %ld calls through the state machine stub: %d wrong\n", n, bad);

    /* [4] sensitivity: the checks above must see a wrong edx or a lost argument */
    {
        int seen = 0;
        gp_ap_target[5] = (uint32_t)(uintptr_t)mock_bad;           /* returns edx + 1 */
        randomize(); h_in[0] = (uint32_t)(uintptr_t)gp_ap_stub[5]; h_in[1] = 0;
        call_stub();
        seen += h_out[1] != m_ret_edx;
        gp_ap_target[2] = (uint32_t)(uintptr_t)mock_p16;
        randomize(); h_in[0] = (uint32_t)(uintptr_t)gp_ap_stub[2]; h_in[1] = 4;
        call_stub();
        h_in[9 + 3] ^= 1;                                         /* as if the stub had passed a wrong last word */
        seen += m_args[3] != h_in[12];
        verdict(seen != 2, "[4] sensitivity: a wrong edx and a wrong argument word are seen by the checks (%d of 2)\n", seen);
    }

    /* [5] */
    gp_ap_target[5] = (uint32_t)(uintptr_t)mock_p0;
    double ns[2];
    for (int k = 0; k < 2; k++) {
        h_in[0] = k ? (uint32_t)(uintptr_t)gp_ap_stub[5] : (uint32_t)(uintptr_t)mock_p0; h_in[1] = 0;
        uint64_t t0 = now_us();
        for (int i = 0; i < 1000000; i++) call_stub();
        ns[k] = (now_us() - t0) / 1000.0;
    }
    printf("[5] a timed call costs %.1f ns more than the call itself (%.1f against %.1f ns)\n", ns[1] - ns[0], ns[1], ns[0]);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
