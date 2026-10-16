/* aiprof: where AnimalAIUpdate, AIUpdateInterface::update and FireWeaponUpdate spend their time
 * (diagnostic, OFF by default; counters only, no behaviour change; test t_aiprof; docs/PERFORMANCE.md §30).
 *
 * logicstats (§14) times each update-module class as a whole: in the 8-player sessions AIUpdateInterface
 * 4.7-5.3 ms per logic step, AnimalAIUpdate 1.2-3.6, FireWeaponUpdate up to 1.5 ms in one call. This
 * times the calls inside them, inclusive, and every AI state's update by state class:
 *   AnimalAIUpdate::update 0x882058: the AIUpdateInterface::update it runs first (and returns 1, so an
 *     animal is updated every logic step), isReachableLayer (every step), the flee and emitter scans
 *     (getClosestObject), the move order;
 *   AIUpdateInterface::update 0x66e58f: its main update 0x6695ef (or 0x66c748), 0x665921, 0x664f93,
 *     0x66217e, the two object-event-map calls 0x756cd7 and the two setStatus calls around it; in
 *     0x6695ef: 0x663e32, 0x6658d3 and the state machine's update (vt+0x10 at 0x669749);
 *   StateMachine::updateStateMachine 0x8db6d5: the current state's update, by state vtable (named from
 *     the state's getName when that is `mov eax, string; ret`);
 *   FireWeaponUpdate 0x88f554: its two forceFireWeapon calls; DamageNugget's radius scan 0x90dfb9.
 * Every 30 s an `aiprof:` line with ms and calls per logic step per site, and one with the 12 most
 * expensive AI states. Each site's original bytes (the call and its target) are checked first. */
#include "gp.h"
#include "p_ai.h"
#include <stdio.h>
#include <string.h>

#define NSITE 21
#define NSTATE 256
#define PERIOD_MS 30000

typedef struct { uint32_t site, target; uint8_t len, kind; const char *label; } site_t;   /* kind 0 call, 1 call [eax+0x10] */
static const site_t SITES[NSITE - 1] = {
    {0x882094, 0x66e58f, 5, 0, "animal: AIUpdateInterface::update"},
    {0x882106, 0x881fcc, 5, 0, "animal: isReachableLayer"},
    {0x882398, 0xa39090, 5, 0, "animal: flee scan"},
    {0x8825f1, 0xa39090, 5, 0, "animal: emitter scan"},
    {0x882ad7, 0x66c4ca, 5, 0, "animal: move order"},
    {0x66e70c, 0x6695ef, 5, 0, "ai: main 0x6695ef"},
    {0x66e702, 0x66c748, 5, 0, "ai: main 0x66c748"},
    {0x66e73a, 0x665921, 5, 0, "ai: 0x665921"},
    {0x66e890, 0x66217e, 5, 0, "ai: 0x66217e"},
    {0x66e5b0, 0x756cd7, 5, 0, "ai: event map 1"},
    {0x66e65d, 0x756cd7, 5, 0, "ai: event map 2"},
    {0x66e5c3, 0x62684d, 5, 0, "ai: setStatus 1"},
    {0x66e8ca, 0x62684d, 5, 0, "ai: setStatus 2"},
    {0x6698ba, 0x6658d3, 5, 0, "ai main: 0x6658d3"},
    {0x66964d, 0x663e32, 5, 0, "ai main: 0x663e32"},
    {0x88f5cb, 0x6cf3d2, 5, 0, "fireweapon: fire"},
    {0x88f6d7, 0x6cf3d2, 5, 0, "fireweapon: fire (nuggets)"},
    {0x90dfb9, 0xa39340, 5, 0, "damage nugget: radius scan"},
    {0x66e732, 0x664f93, 5, 0, "ai: 0x664f93"},
    {0x669746, 0, 6, 1, "ai main: state machine"},
};
void gp_ap_s0(void), gp_ap_s1(void), gp_ap_s2(void), gp_ap_s3(void), gp_ap_s4(void), gp_ap_s5(void), gp_ap_s6(void),
     gp_ap_s7(void), gp_ap_s8(void), gp_ap_s9(void), gp_ap_s10(void), gp_ap_s11(void), gp_ap_s12(void), gp_ap_s13(void),
     gp_ap_s14(void), gp_ap_s15(void), gp_ap_s16(void), gp_ap_s17(void), gp_ap_s18(void), gp_ap_s19(void), gp_ap_s20(void),
     gp_ap_state(void), gp_ap_sm(void);
void (*const gp_ap_stub[NSITE])(void) = {gp_ap_s0, gp_ap_s1, gp_ap_s2, gp_ap_s3, gp_ap_s4, gp_ap_s5, gp_ap_s6, gp_ap_s7,
    gp_ap_s8, gp_ap_s9, gp_ap_s10, gp_ap_s11, gp_ap_s12, gp_ap_s13, gp_ap_s14, gp_ap_s15, gp_ap_s16, gp_ap_s17, gp_ap_s18,
    gp_ap_s19, gp_ap_s20};
uint32_t gp_ap_target[NSITE];
volatile uint64_t gp_ap_ticks[NSITE];
volatile LONG gp_ap_calls[NSITE];

typedef struct { uint32_t vt; uint64_t ticks; LONG calls; } state_t;
static state_t states[NSTATE], lstates[NSTATE];
static uint64_t lticks[NSITE]; static LONG lcalls[NSITE];
static uint64_t t_report, q_report;
static uint32_t frame_report;
static DWORD tick_report;
static int on;

/* the state machine's call at 0x669746 (`mov [ebp-4], edi; call [eax+0x10]`): its own stub, which
 * does the store and calls site 19 with the vtable's target */
__asm__(".intel_syntax noprefix\n.text\n.globl _gp_ap_sm\n.balign 16\n_gp_ap_sm:\n"
        "  mov dword ptr [ebp-4], edi\n"                 /* the caller's frame: the replaced store */
        "  push dword ptr [eax+0x10]\n  pop dword ptr [_gp_ap_target+4*19]\n"
        "  jmp _gp_ap_s19\n.att_syntax prefix\n");

static const char *state_name(uint32_t vt, char *buf)
{
    const uint8_t *fn = *(const uint8_t *const *)(uintptr_t)(vt + 8);
    MEMORY_BASIC_INFORMATION mi;
    if (VirtualQuery(fn, &mi, sizeof mi) && mi.State == MEM_COMMIT && fn[0] == 0xb8 && fn[5] == 0xc3) {
        const char *s = *(const char *const *)(fn + 1);
        if (VirtualQuery(s, &mi, sizeof mi) && mi.State == MEM_COMMIT) { snprintf(buf, 40, "%.39s", s); return buf; }
    }
    snprintf(buf, 40, "vt %06x", vt);
    return buf;
}

static void report(void)
{
    LARGE_INTEGER q, f; QueryPerformanceCounter(&q); QueryPerformanceFrequency(&f);
    uint64_t t = __builtin_ia32_rdtsc(), dq = (uint64_t)q.QuadPart - q_report, dt = t - t_report;
    double tpms = q_report && dq ? (double)dt * (double)f.QuadPart / (double)dq / 1000.0 : 0;
    const uint8_t *gl = *(const uint8_t *const *)(uintptr_t)0xde412c;
    uint32_t frame = gl ? *(const uint32_t *)(gl + 0x40) : 0;
    long steps = (long)(frame - frame_report);
    t_report = t; q_report = (uint64_t)q.QuadPart; frame_report = frame;
    if (tpms <= 0 || steps <= 0) goto done;
    char b[500]; int k = snprintf(b, sizeof b, "aiprof: last %lu s, %ld logic steps; ms per step / calls per step:",
                                  (unsigned long)(PERIOD_MS / 1000), steps);
    for (int i = 0; i < NSITE - 1 && k < (int)sizeof b - 48; i++) {
        uint64_t d = gp_ap_ticks[i] - lticks[i]; LONG c = gp_ap_calls[i] - lcalls[i];
        if (!c) continue;
        k += snprintf(b + k, sizeof b - k, " %s %.3f/%.1f;", SITES[i].label, d / tpms / steps, (double)c / steps);
    }
    gp_log("%s", b);
    k = snprintf(b, sizeof b, "aiprof: AI states (update, inclusive), ms per step / calls per step:");
    static uint8_t used[NSTATE];
    memset(used, 0, sizeof used);
    for (int r = 0; r < 12 && k < (int)sizeof b - 64; r++) {
        int bi = -1; uint64_t bt = 0;
        for (int i = 0; i < NSTATE; i++) {
            uint64_t d = states[i].ticks - lstates[i].ticks;
            if (states[i].vt && !used[i] && d > bt) { bt = d; bi = i; }
        }
        if (bi < 0) break;
        used[bi] = 1;
        char nb[40];
        k += snprintf(b + k, sizeof b - k, " %s %.3f/%.1f;", state_name(states[bi].vt, nb), bt / tpms / steps,
                      (double)(states[bi].calls - lstates[bi].calls) / steps);
    }
    gp_log("%s", b);
done:
    for (int i = 0; i < NSITE; i++) { lticks[i] = gp_ap_ticks[i]; lcalls[i] = gp_ap_calls[i]; }
    memcpy(lstates, states, sizeof states);
}

__attribute__((force_align_arg_pointer)) void __cdecl gp_ap_state_acc(uint32_t lo, uint32_t hi, uint32_t vt)
{
    uint32_t h = (vt >> 2) * 2654435761u >> 24;        /* 8 bits */
    for (int i = 0; i < NSTATE; i++, h = (h + 1) & (NSTATE - 1)) {
        state_t *s = &states[h];
        if (!s->vt) s->vt = vt;
        if (s->vt == vt) { s->ticks += (uint64_t)hi << 32 | lo; s->calls++; break; }
    }
    DWORD now = GetTickCount();
    if (!tick_report) { tick_report = now; report(); return; }
    if (now - tick_report >= PERIOD_MS) { report(); tick_report = now; }
}

void gp_ap_exit_log(void)
{
    if (!on) return;
    report();
    long ns = 0;
    for (int i = 0; i < NSTATE; i++) ns += states[i].calls;
    gp_log("exit: aiprof %ld state updates timed; calls: animal AI %ld, AI main %ld, state machine %ld, fire %ld, damage "
           "scans %ld", ns, gp_ap_calls[0], gp_ap_calls[5] + gp_ap_calls[6], gp_ap_calls[19], gp_ap_calls[15] + gp_ap_calls[16],
           gp_ap_calls[17]);
}

int gp_patch_aiprof(void)
{
    static uint8_t orig[NSITE][8];
    static const uint8_t sm[6] = {0x89, 0x7d, 0xfc, 0xff, 0x50, 0x10};    /* mov [ebp-4], edi; call [eax+0x10] */
    static const uint8_t st[5] = {0x8b, 0xd9, 0xff, 0x50, 0x18};          /* mov ebx, ecx; call [eax+0x18] */
    gp_site s[NSITE + 1];
    int n = 0;
    for (int i = 0; i < NSITE - 1; i++) {
        const site_t *t = &SITES[i];
        if (t->kind == 0) {
            int32_t rel = (int32_t)(t->target - (t->site + 5));
            orig[i][0] = 0xe8; memcpy(&orig[i][1], &rel, 4);
            gp_site_init(&s[n], t->site, orig[i], 5);
            gp_rel32(&s[n], 0, 0xe8, (void *)gp_ap_stub[i]);
            gp_ap_target[i] = t->target + gp_va_offset;
        } else {
            gp_site_init(&s[n], t->site, sm, sizeof sm);
            gp_rel32(&s[n], 0, 0xe8, (void *)gp_ap_sm);
            s[n].repl[5] = 0x90;
        }
        n++;
    }
    gp_site_init(&s[n], 0x8db70b, st, sizeof st);
    gp_rel32(&s[n], 0, 0xe8, (void *)gp_ap_state);
    n++;
    if (!gp_apply("aiprof", s, n)) return 0;
    on = 1;
    gp_log("aiprof: %d call sites and the AI state update timed; a line every %d s", n, PERIOD_MS / 1000);
    return 1;
}
