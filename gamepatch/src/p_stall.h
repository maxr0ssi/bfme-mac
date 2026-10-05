/* stall sampler (p_stall.c): where the main thread is while a frame takes too long. Shared by the game
 * patch (p_monitor.c) and tools/d3d9bench.c --monitor (which includes p_stall.c), so it needs nothing
 * but Windows. */
#ifndef P_STALL_H
#define P_STALL_H
#include <windows.h>
#include <stdint.h>

/* The frame hook stores the time (QueryPerformanceCounter) and logic frame of the last frame here. */
extern volatile LONGLONG gp_stall_last_q;
extern volatile uint32_t gp_stall_last_logic;
/* Optional: the game logic phase the main thread is in (logicstats), read at each sample; -1 = unknown. */
extern int (*gp_stall_phase)(void);

/* Call on the main thread: samples it from a watchdog thread whenever no frame came for stall_ms,
 * every every_ms, at most max_ms per stall. q0 and freq are the caller's clock (lines are us since q0).
 * Returns 1 when the watchdog runs. */
int gp_stall_start(LONGLONG q0, LONGLONG freq, int stall_ms, int every_ms, int max_ms);
/* Formats the samples taken since the last call as game.txt lines into buf (at most cap bytes);
 * returns the bytes written. One consumer thread only. */
int gp_stall_drain(char *buf, int cap);
/* stalls seen, samples kept, samples lost (ring full), mean and max us the main thread was held */
void gp_stall_stats(LONG *stalls, LONG *samples, LONG *lost, LONG *held_mean_us, LONG *held_max_us);

#endif
