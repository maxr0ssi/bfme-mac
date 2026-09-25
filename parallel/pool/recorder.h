/* R5 deferred-effect recorder (research prototype). Cloned game code runs on workers; its calls
 * with shared side effects (list pushes, D3D/COM methods, game functions that write shared state)
 * are retargeted to per-site stubs that RECORD the call instead of making it. After the join the
 * main thread replays every record in item order, then in call order within an item, so the side
 * effects happen in exactly the order the serial game would have made them.
 *
 * A clone's `call rel32 <target>` is retargeted to rec_site_stub(id) by the clone installer; a COM
 * call `call [reg+off]` is redirected by pointing the object pointer the clone loads (a redirected
 * global) at a proxy whose vtable slots are site stubs (rec_proxy_*). See parallel/DESIGN.md §3. */
#ifndef RECORDER_H
#define RECORDER_H
#include <stdint.h>

enum { REC_CDECL = 0, REC_STDCALL = 1, REC_THISCALL = 2 };
#define REC_MAXARGS 8
#define REC_COPYMAX 64

/* Register a deferred call site. target: the real function (replayed on main). conv/nargs: its
 * convention and stack argument count (this not counted). retval: what the stub returns to the
 * clone (the cloner must prove eax is dead after the call, or that this constant is what the
 * code expects, e.g. S_OK). copy_arg/copy_bytes: argument index whose pointee (<= REC_COPYMAX
 * bytes) is deep-copied at record time, because it points to worker-local memory (stack or
 * redirected scratch) that will be gone at replay; -1 = none. Returns the site id (< 0 on error). */
int   rec_site_add(uint32_t target, int conv, int nargs, uint32_t retval, int copy_arg, int copy_bytes);
void *rec_site_stub(int site);          /* executable stub to retarget a call site to */

void  rec_begin_item(int item);         /* called by the job before each item (per thread) */
void  rec_reset(void);                  /* clear all logs (before a par_for) */
int   rec_overflowed(void);             /* a log filled up: discard, run the region serially */
int   rec_replay(void);                 /* main thread: replay in (item, seq) order; returns count */
uint64_t rec_digest(void);              /* FNV-1a over the record stream in replay order */
uint32_t rec_count(void);

#endif
