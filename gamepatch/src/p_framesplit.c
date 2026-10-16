/* framesplit: where each drawn frame's time goes (diagnostic; on with the monitor, which writes it).
 *
 * Why (docs/FPS-ROADMAP.md §1, §4 step 0; docs/PERFORMANCE.md §28): the 30 FPS frames of an
 * 8-player battle have slack on average but not on the heavy logic phases, and only 5-60 s
 * windows were measured. This times every engine iteration (one drawn frame and one logic phase):
 *   client   GameEngine vt+0x9c, the client pass 0x632409 (GameClient::update, the draw, input,
 *            audio, network), inclusive
 *   draw     W3DDisplay::draw 0x44b788, inclusive (inside the client pass)
 *   present  the device's Present at 0x522650 (inside the draw; the wait for Wine's render thread
 *            shows here)
 *   logic    GameEngine vt+0x98, the engine step 0x6329b0 (the network's go in phase 1, then
 *            GameLogic::update for the phase), inclusive; phases = a bit per phase that ran logic
 *            (bit 7: a phase-1 step the network refused)
 *   wait     the frame limiter: from 0x63a196 (its timeGetTime) to the iteration's end; 0 when the
 *            game does not limit (6 frames after a skipped one, or no limit)
 *   iter     from the end of the previous iteration (0x63a21f) to the end of this one
 * The six times go into the monitor's frame record of the iteration that drew (p_monitor.c
 * gp_mon_split); iterations without a draw (a skipped client frame) carry over into the next record
 * (iters > 1). Hooks: four vtable slots, two call sites in the engine loop, one at Present. Each site
 * is checked against its original bytes. No game state is written; only the clock is read. */
#include "gp.h"
#include "p_fps.h"
#include <string.h>

uint32_t gp_fs_cont[8];
static LONGLONG freq, q_prev, t0[4], acc[FS_N];
static int wait_on, on, phase;
static LONG records, carried;

static LONGLONG qpc(void) { LARGE_INTEGER x; QueryPerformanceCounter(&x); return x.QuadPart; }
static uint32_t us(LONGLONG d) { return d > 0 ? (uint32_t)(d * 1000000 / freq) : 0; }

/* called from p_framesplit.S, main thread only: 0/1 client pass start/end, 2/3 engine step
 * start (arg = phase) / end, 4/5 draw, 6/7 Present, 8 limiter start, 9 iteration end */
__attribute__((force_align_arg_pointer)) void gp_fs_mark(int what, int arg)
{
    LONGLONG q = qpc();
    switch (what) {
    case 0: t0[0] = q; break;
    case 1: acc[FS_CLIENT] += q - t0[0]; break;
    case 2: t0[1] = q; phase = arg; break;
    case 3: {
        acc[FS_LOGIC] += q - t0[1];
        const uint8_t *gc = *(const uint8_t *const *)(uintptr_t)0xde4388;  /* TheGameClient: +0xc8 logic advanced */
        int ran = gc ? gc[0xc8] != 0 : 1, ph = phase;
        if (ph >= 1 && ph <= 6) acc[FS_PHASES] |= ran ? 1 << ph : 0x80;
        break;
    }
    case 4: t0[2] = q; break;
    case 5: acc[FS_DRAW] += q - t0[2]; break;
    case 6: t0[3] = q; break;
    case 7: acc[FS_PRESENT] += q - t0[3]; break;
    case 8: if (!wait_on) { wait_on = 1; acc[FS_WAIT] -= q; } break;   /* + the end time below */
    case 9: {
        if (wait_on) { acc[FS_WAIT] += q; wait_on = 0; }
        if (q_prev) acc[FS_ITER] += q - q_prev;
        q_prev = q;
        acc[FS_ITERS]++;
        uint32_t v[FS_N];
        v[FS_CLIENT] = us(acc[FS_CLIENT]); v[FS_DRAW] = us(acc[FS_DRAW]); v[FS_PRESENT] = us(acc[FS_PRESENT]);
        v[FS_LOGIC] = us(acc[FS_LOGIC]); v[FS_PHASES] = (uint32_t)acc[FS_PHASES]; v[FS_WAIT] = us(acc[FS_WAIT]);
        v[FS_ITER] = us(acc[FS_ITER]); v[FS_ITERS] = (uint32_t)acc[FS_ITERS];
        if (gp_mon_split(v)) { memset(acc, 0, sizeof acc); records++; }
        else carried++;
        break;
    }
    }
}

/* tests */
void gp_fs_reset(void) { memset(acc, 0, sizeof acc); memset(t0, 0, sizeof t0); q_prev = 0; wait_on = 0; }
LONG gp_fs_count(int carried_ones) { return carried_ones ? carried : records; }

void gp_fs_exit_log(void)
{
    if (!on) return;
    gp_log("exit: framesplit: %ld frame records with a split, %ld engine iterations without a drawn frame (carried over)",
           records, carried);
}

int gp_patch_framesplit(void)
{
    extern int gp_mon_on;
    if (!gp_mon_on) { gp_log("framesplit: off (it writes into the monitor's frame records; the monitor is off)"); return 0; }
    static const uint8_t vt_client[] = {0x09, 0x24, 0x63, 0x00}, vt_step[] = {0xb0, 0x29, 0x63, 0x00},
                         vt_draw[] = {0x88, 0xb7, 0x44, 0x00};
    static const uint8_t present[] = {0x53, 0x53, 0x53, 0x53, 0x50, 0xff, 0x52, 0x44};
    static const uint8_t wait[] = {0xff, 0x15, 0x20, 0x09, 0xbd, 0x00}, iter[] = {0x8b, 0x0d, 0xf8, 0x42, 0xde, 0x00};
    /* context: EndScene just before Present; the limiter's skip test before 0x63a196 */
    static const uint8_t endscene[] = {0xff, 0x91, 0xa8, 0x00, 0x00, 0x00};
    static const uint8_t limtest[] = {0x38, 0x1d, 0x20, 0x43, 0xde, 0x00, 0x74, 0x6a};
    gp_site s[12];
    int n = 0;
    uint32_t a;
    a = (uint32_t)(uintptr_t)gp_fs_s_client;
    gp_site_init(&s[n], 0xbd857c, vt_client, 4); memcpy(s[n++].repl, &a, 4);
    gp_site_init(&s[n], 0xbfe2fc, vt_client, 4); memcpy(s[n++].repl, &a, 4);
    a = (uint32_t)(uintptr_t)gp_fs_s_step;
    gp_site_init(&s[n], 0xbd8578, vt_step, 4); memcpy(s[n++].repl, &a, 4);
    gp_site_init(&s[n], 0xbfe2f8, vt_step, 4); memcpy(s[n++].repl, &a, 4);
    a = (uint32_t)(uintptr_t)gp_fs_s_draw;
    gp_site_init(&s[n], 0xbd9c58, vt_draw, 4); memcpy(s[n++].repl, &a, 4);
    gp_site_init(&s[n], 0x522628, endscene, sizeof endscene); s[n++].wlen = 0;
    gp_site_init(&s[n], 0x52264b, present, sizeof present);
    memset(s[n].repl, 0x90, sizeof present); gp_rel32(&s[n++], 0, 0xe8, (void *)gp_fs_s_present);
    gp_site_init(&s[n], 0x63a18e, limtest, sizeof limtest); s[n++].wlen = 0;
    gp_site_init(&s[n], 0x63a196, wait, sizeof wait);
    s[n].repl[5] = 0x90; gp_rel32(&s[n++], 0, 0xe8, (void *)gp_fs_s_wait);
    gp_site_init(&s[n], 0x63a21f, iter, sizeof iter);
    s[n].repl[5] = 0x90; gp_rel32(&s[n++], 0, 0xe8, (void *)gp_fs_s_iter);
    gp_fs_cont[0] = 0x632409 + gp_va_offset;
    gp_fs_cont[1] = 0x6329b0 + gp_va_offset;
    gp_fs_cont[2] = 0x44b788 + gp_va_offset;
    gp_fs_cont[3] = 0xbd0920;               /* timeGetTime's IAT slot and the global at 0x63a21f: data, */
    gp_fs_cont[4] = 0xde42f8;               /* at their own addresses in the tests too */
    LARGE_INTEGER f; QueryPerformanceFrequency(&f); freq = f.QuadPart;
    if (!gp_apply("framesplit", s, n)) return 0;
    gp_mon_split_on = on = 1;
    gp_log("framesplit: on (per drawn frame: client pass, draw, Present, logic phase, limiter wait -> monitor 'f' records)");
    return 1;
}
