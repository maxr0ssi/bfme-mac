/* t_stall: the stall sampler (p_stall.c) on this test's own main thread (no game code needed).
 *  [1] frames every 5 ms for 0.6 s: no samples;
 *  [2] a 600 ms frame spinning in spin_here(): samples every ~2 ms after the first 150 ms, nearly all
 *      with EIP inside spin_here and its return address into main on the stack scan, all with the
 *      same "since" and the logic frame of the last frame; an X line first;
 *  [3] a 600 ms frame sleeping in sleep_here(): EIP outside the exe, an M line for its module, and
 *      sleep_here's return address into main on the stack;
 *  [4] a 2 s frame: at most max_ms / every_ms samples (the cap);
 *  [5] cost: how long each sample holds the main thread (mean, max).
 * usage: t_stall.exe [ignored] */
#include "p_stall.h"
#include "orig.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static volatile uint32_t sink, ret_spin, ret_sleep;
static LONGLONG freq;
static LONGLONG qpc(void) { LARGE_INTEGER x; QueryPerformanceCounter(&x); return x.QuadPart; }
static void frame(uint32_t logic) { gp_stall_last_logic = logic; __atomic_store_n(&gp_stall_last_q, qpc(), __ATOMIC_RELAXED); }

__attribute__((noinline)) static void spin_here(int ms)
{
    ret_spin = (uint32_t)(uintptr_t)__builtin_return_address(0);
    LONGLONG end = qpc() + freq * ms / 1000;
    while (qpc() < end)
        for (int i = 0; i < 200000; i++) sink = sink * 1664525u + 1013904223u;
}
__attribute__((noinline)) static void sleep_here(int ms)
{
    ret_sleep = (uint32_t)(uintptr_t)__builtin_return_address(0);
    Sleep(ms);
    sink++;
}

static char buf[4 << 20];
typedef struct { long long q, since; unsigned long logic, eip; unsigned held; int phase, nret; unsigned long ret[64]; } ev;
static ev evs[4096];
static int nev, nx, nm;
static char mline[256];

static void drain(void)
{
    Sleep(50);
    int n = gp_stall_drain(buf, sizeof buf - 1);
    buf[n] = 0;
    nev = 0;
    for (char *l = strtok(buf, "\n"); l; l = strtok(NULL, "\n")) {
        if (l[0] == 'X') nx++;
        if (l[0] == 'M') { nm++; snprintf(mline, sizeof mline, "%s", l); }
        if (l[0] != 'e' || nev == 4096) continue;
        ev *e = &evs[nev++];
        int k = 0;
        sscanf(l, "e %lld %lld %lu %lx %u %d%n", &e->q, &e->since, &e->logic, &e->eip, &e->held, &e->phase, &k);
        e->nret = 0;
        for (char *p = l + k; e->nret < 64 && *p; ) {
            char *end; unsigned long v = strtoul(p, &end, 16);
            if (end == p) break;
            e->ret[e->nret++] = v; p = end;
        }
    }
}
static int has(const ev *e, unsigned long a) { for (int i = 0; i < e->nret; i++) if (e->ret[i] == a) return 1; return 0; }

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    LARGE_INTEGER f; QueryPerformanceFrequency(&f); freq = f.QuadPart;
    LONGLONG q0 = qpc();
    int fail = 0;
    if (!gp_stall_start(q0, freq, 150, 2, 1000)) { printf("gp_stall_start failed\nFAIL\n"); return 1; }

    /* [1] */
    for (int i = 0; i < 120; i++) { frame(10); Sleep(5); }
    frame(10); drain();
    printf("[1] frames every 5 ms: %d samples: %s\n", nev, nev ? "WRONG" : "ok");
    fail |= nev != 0;

    /* [2] */
    frame(21); spin_here(600); frame(22); drain();
    uintptr_t lo = (uintptr_t)spin_here;
    int in = 0, withret = 0, same = 1, logic = 1;
    for (int i = 0; i < nev; i++) {
        in += evs[i].eip >= lo && evs[i].eip < lo + 0x200;
        withret += has(&evs[i], ret_spin);
        same &= evs[i].since == evs[0].since;
        logic &= evs[i].logic == 21 && evs[i].phase == -1;
    }
    int ok2 = nev >= 100 && nev <= 260 && in * 10 >= nev * 9 && withret * 10 >= nev * 9 && same && logic && nx == 1;
    printf("[2] 600 ms spin: %d samples (expect ~225), EIP in spin_here %d, its return address on the stack %d, one stall %s, "
           "logic/phase %s, X lines %d: %s\n", nev, in, withret, same ? "yes" : "NO", logic ? "ok" : "WRONG", nx, ok2 ? "ok" : "WRONG");
    fail |= !ok2;

    /* [3] */
    frame(31); sleep_here(600); frame(32); drain();
    HMODULE self = GetModuleHandleA(NULL);
    uintptr_t ilo = (uintptr_t)self, ihi = ilo + ((IMAGE_NT_HEADERS *)(ilo + ((IMAGE_DOS_HEADER *)self)->e_lfanew))->OptionalHeader.SizeOfImage;
    int outside = 0; withret = 0;
    for (int i = 0; i < nev; i++) { outside += evs[i].eip < ilo || evs[i].eip >= ihi; withret += has(&evs[i], ret_sleep); }
    int ok3 = nev >= 100 && outside * 10 >= nev * 9 && withret * 10 >= nev * 9 && nm >= 1;
    printf("[3] 600 ms sleep: %d samples, EIP outside the exe %d, return address on the stack %d, M lines %d (%s): %s\n",
           nev, outside, withret, nm, mline, ok3 ? "ok" : "WRONG");
    fail |= !ok3;

    /* [4] */
    frame(41); spin_here(2000); frame(42); drain();
    int ok4 = nev >= 300 && nev <= 500;
    printf("[4] 2 s spin with a 1000 ms cap: %d samples (at most 500): %s\n", nev, ok4 ? "ok" : "WRONG");
    fail |= !ok4;

    /* [5] */
    LONG st, sa, lost, hm, hx;
    gp_stall_stats(&st, &sa, &lost, &hm, &hx);
    printf("[5] %ld stalls, %ld samples, %ld lost; the main thread held %ld us per sample (mean), %ld max\n", st, sa, lost, hm, hx);
    fail |= st != 3 || lost != 0 || hm > 2000;
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
