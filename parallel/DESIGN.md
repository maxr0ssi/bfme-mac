# R5 parallel framework (research prototype)

Shared machinery for spreading RotWK's client-side per-frame work across cores from the in-memory
patch DLL (gamepatch/). Not wired into anything. Measured under Wine 10 (w10 engine, new WoW64,
`WINEMSYNC=1`) on an M3 Max (12 P + 4 E cores) in the isolated prefix `build/prefix-research`.

| Piece | Where | State |
|---|---|---|
| Worker pool, `par_for` | `pool/parallel.[ch]` | prototyped, measured (`pool/bench.c`) |
| Core placement probe | `pool/place.c` | measured |
| Deferred-effect recorder | `pool/recorder.[ch]` | prototyped, tested (`pool/rectest.c`) |
| Function cloner | `build/rotwk-re/research-r5/cloner.py` (needs `build/re-venv`: capstone, pefile; lives in the ignored research area because it copies game code) | prototyped on the shadow chain |
| Serial-vs-parallel checker | §4 | designed; the pieces it compares (output digests, `rec_digest`) are implemented and tested |

Build and run any test: `parallel/pool/build-and-run.sh bench|rectest|place [args]` (bounded by
`DEADLINE` seconds; refuses to run while a game is live).

## 1. Worker pool

API (`parallel.h`): `par_init(n)`, `par_for(n, grain, fn, ctx)` with `fn(begin, end, ctx, slot)`,
`par_prewake()`, `par_park_now()`, `par_refresh_fpu()`, `par_slot()`, `par_get_stats()`,
`par_shutdown()`. Environment variables: `PAR_WORKERS`, `PAR_IDLE_US`.

- **Threads:** persistent, default 7 workers plus the main thread. Stack 256 KB; check it against
  the deepest cloned chain.
- **Publishing a job:** write the job fields, then the claim word, then `gen`.
- **Claiming a chunk:** one CAS on a single word `{gen:16 | index:16}`. A late worker holding an
  older `gen` can never claim, or count down, a chunk of a newer job.
- **The earlier hang:** `forkjoin.c` mode 2, and this pool's first version, reset
  `next`/`remaining` while a late worker was still inside `drain()`. Its decrement was lost, so
  `remaining` never reached 0. The claim word above is the fix.
- **Parking:** arm-then-recheck with a per-worker auto-reset event. A worker that disarms too late
  takes in the signal main is about to send, so no stale wake is left behind.
- **Spin, then park:** a worker spins for `idle_park_us` after its last job (default 200 µs), then
  parks. `par_prewake()` at the start of a frame's parallel region overlaps the kernel wake with
  serial work. `par_park_now()` at its end (for example before Present) stops the spinning between
  frames.
- **FPU:** `par_for` snapshots the caller's x87 control word (the game sets PC_24 at 0x440809) and
  MXCSR. Every participant loads that snapshot before running chunks. `bench verify` sets PC_24 and
  FTZ|DAZ and gets identical results byte for byte.
- **Nesting and reentrancy:** only the main thread (slot 0) goes parallel. `par_for` called from a
  worker, from any other thread, or while a `par_for` is already running on main runs serially
  inline. Tested: 6,878 nested calls ran serially, with no deadlock and no wrong items.
- **Faults:** a vectored exception handler catches a hardware fault (codes 0xC…) raised inside a
  guarded chunk on a pool slot. It restores `fs:[0]`, the SEH chain the game's MSVC EH frames push,
  and `longjmp`s back to the guard. The chunk is then retried serially on main. If the retry also
  faults, the fault is not caught, so the game crashes exactly as it would have without the patch;
  nothing ever hangs. Tested with 50 jobs, each with a NULL write on a worker: every fault was
  caught and 0 items were wrong. A job must be idempotent per item for the retry to be valid:
  outputs per item, side effects deferred.
- **Wine traps:** `__thread` TLS makes the exe fail to load under this Wine (exit code 53 before
  `main`), so per-thread state uses `TlsAlloc` plus static per-slot arrays. mingw GCC has no
  `__try`, hence the VEH-based guard.

### Measurements (quiet machine, load 5-11)

| What | 3 workers | 7 workers |
|---|---|---|
| fork/join round trip, hot (one chunk per participant) | 1.3 µs median, p99 8 µs | 2.4 µs, p99 39 µs |
| first job after all workers parked (event wake) | 12 µs median, p99 73 µs | 30 µs, p99 530 µs |
| 64 tiny chunks (claim contention) | 11 µs (0.18 µs/chunk) | 19 µs (0.30 µs/chunk) |
| QueryPerformanceCounter | 0.08 µs | |

Overhead vs grain, 7 workers, N = 65,536 items:

| per item | serial | grain 64 | grain 256 | grain 1024 | grain 4096 | grain 16384 (4 chunks) |
|---|---|---|---|---|---|---|
| light (~2 ns) | 134 µs | 0.51x | 2.98x | 4.56x | 4.61x | 2.94x |
| 15 ns | 1003 µs | 6.09x | 6.88x | 6.99x | 7.10x | 3.54x |
| 130 ns | 8471 µs | 6.94x | 6.97x | 7.00x | 6.93x | 3.44x |

Rule of thumb: chunks should carry at least ~10-20 µs of work, and there should be at least ~4
chunks per participant (32 with 8 participants). Below ~50 µs of total work, run serially.

CPU cost per simulated 30 ms frame (7 workers, 4 bursts of ~375 µs serial work, 2 ms apart):

| idle budget | CPU | parallel time per frame |
|---|---|---|
| 0 (park immediately) | 0.36 cores | 521 µs |
| 200 µs | 0.52 | 496 |
| 2 ms (covers the gaps) | 2.01 | 346 |
| always spin | 6.90 | 310 |
| 2 ms + prewake + park_now | 2.29 (includes a 1 ms prewake lead) | 308 |

Spinning costs roughly (width of the parallel window / frame time) × workers. Use the hooks with a
budget that covers the gaps between parallel sections within a frame, and nothing between frames.

### Core placement (`place.c`)

- `SetThreadPriority` has no effect on this Wine build. `ps -M` shows Mach priority 31 for
  LOWEST, NORMAL, ABOVE_NORMAL and HIGHEST alike. The priority → QoS mapping
  (`wine/src/server/thread.c apply_thread_priority`) is in the Wine 11 source, not in w10.
- With ≤ 11 busy threads, all run at the same rate (P-cores). At 14-16, macOS time-shares threads
  across P and E cores, so rates flatten to 0.87-0.94 of max rather than splitting in two.
- macOS has no hard affinity. Keep workers + main + the game's other busy threads (~1.5) at or
  below 12: 6-7 workers. A background-QoS launch (`taskpolicy -b`) puts everything on E-cores
  (PERFORMANCE.md §8); nothing in-process can undo that.

## 2. Function cloner (`build/rotwk-re/research-r5/cloner.py`)

`cloner.py <disk.exe> --config X.json [--emit out.bin [--verify-install]] [--survey VA]`

- Config fields: `entries`, `redirect` ranges, `leaf_ok` (callees allowed to stay original),
  `stop` (never followed).
- Every function is decoded with capstone, with boundaries from `funcs.txt`.
- A callee is **cloned** when it transitively touches a redirected global. Otherwise it is
  **called in place**, with its rel32 rebased to the original address.
- **Emitted relocations:**
  - `rel32`: `intra` → the clone copy (so the redirect holds along the whole chain); otherwise the
    original VA.
  - `redirect_refs`: disp32/imm32 fields to patch to the per-worker base.
- **Validation:**
  - Absolute references into mutable sections outside the redirect set are listed as hazards.
    The section is judged by name: this exe's `.rdata` carries the PE WRITE bit, so it is treated
    as read-only (const pools, IAT).
  - Indirect calls are listed for the recorder.
- `--survey` walks the full rel32 closure and lists every mutable global per function, with a
  collapsed range table.
- `--verify-install` applies the relocations at a fake base, re-disassembles, and checks every
  target.

Shadow chain results:

| Entry | Closure | Mutable globals | Indirect calls | Verdict |
|---|---|---|---|---|
| buildPolygonNormals 0x4f21b2 | 7 funcs | 0xdd1864-0xdd186c only | 0 | clone, 12-byte redirect |
| buildSilhouette 0x4f2614 | 16 funcs; 4 cloned (21b2, 2252, 25eb, 2614; 1,165 bytes), 12 in place incl. buildPolygonNormal 0x4f1613, GetPolygonIndex, addSilhouetteEdge, addNeighborlessEdges | 0xdd1864-0xdd186c only | 0 | clean. 22 rel32 (6 intra) + 3 redirects; install check 25/25 |
| constructVolume 0x4ef790 | 2 funcs | none | 0 | no clone needed: run in place if each item owns its volume object |
| updateVolumes 0x4f3626 | 242 funcs | 103 in 34 ranges | 7 (vtable 0x180/0x228/0x184/0x50/0xc/0x14/0x108) | too wide: allocator, containers |
| Update 0x4f3906 | 245 funcs | 119 in 36 ranges | many | too wide |

Globals in the `updateVolumes`/`Update` closures fall into two groups:

- **Shadow-private scratch** (redirectable): 0xdd1700-0xdd1744, 0xdd1848-0xdd1870,
  0xdd19d4-0xdd1a18, 0xdc3628, 0xdc78ec, 0xdcb83c.
- **Shared infrastructure** (never redirectable): the allocator 0xdc5e38/3c/44 (operator new
  0x42f6e0/0x42f720), 0xdc62c0 (9 functions), 0xdc1340…, CRT 0xd89000…

The per-item parallel unit is therefore buildSilhouette (+ normals) + constructVolume. The
allocation, VB fill and list work in updateVolumes/Update stay on main, or go through the recorder.

The task's redirect list (0xdd184c-54, 0xdd1864-6c, 0xdd19d4, 0xdd19ec) is incomplete for
updateVolumes. It also writes 0xdd19d8/dc/f0/f4/f8/fc, 0xdd1718, 0xdd1740, 0xdd1854 and 0xdc3628,
reads 0xdd1848, and 0xdd1700-0xdd1720 belong to Update.

## 3. Deferred-effect recorder (`pool/recorder.[ch]`)

- **Direct calls** (`call rel32` to a shared-effect function): the installer retargets the clone's
  rel32 to a 17-byte per-site stub: `push ecx; push site; call rec_common; add esp,8; ret n|ret`.
  `rec_common` appends `{item, seq, site, ecx, args[≤8], optional deep copy ≤64 bytes of one
  pointer argument}` to the calling slot's log, and returns the site's configured value in eax.
- **COM/vtable calls** (`call [reg+off]`): they can't be retargeted. Redirect the global the clone
  loads the object pointer from, per worker, to a proxy whose vtable slots are site stubs
  (stdcall, `this` + n args). Only methods whose results are ignored or constant can be proxied.
  `Lock` style methods get a staging buffer: record the copy, and do the real Lock/copy/Unlock at
  replay.
- **Replay:** after the join, main k-way-merges the per-slot logs by (item, seq). Each slot's log
  is already ordered, because a slot processes whole ascending chunks and claims are monotonic.
  Each record is invoked with its real convention (cdecl, stdcall, or GCC `thiscall` typedefs), so
  side effects happen in serial order.
- **Digest:** `rec_digest()` hashes the stream. It skips ecx for non-thiscall sites and the raw
  value of deep-copied pointer arguments.
- **Test (`rectest`):** 56,677 records across cdecl, stdcall-with-stack-pointer and thiscall sites.
  Replayed effects are identical to the direct serial reference, and the digest is equal serial vs
  parallel. Recording costs are negligible; replay costs **0.11 µs/record** on main. That is the
  budget: ~9,000 records per ms of main-thread time.
- **Log size:** 65,536 records per slot, allocated on first use (~6 MB each). Overflow sets a flag
  and the region must re-run serially.

Rules for what can be deferred:
1. The call's return value is unused, or is a constant the code expects (S_OK, a bool). The cloner
   still needs an eax-liveness check at each deferred site (capstone `regs_access` forward scan to
   the first read or write of eax); not implemented yet.
2. No code in the parallel region reads state the call writes: no push-then-read-length, no
   allocate-then-use.
3. Pointer arguments point to memory that is stable until replay (game objects), or they are
   deep-copied (stack and redirected scratch).
4. **Never deferrable:** allocation whose result is used (operator new 0x42f720, the allocator at
   0xdc5e44), Lock/Map results that are dereferenced, anything that must be read back in the same
   item. Hoist these into a serial prepare pass (pre-size or pre-allocate per item), or keep that
   stage serial.
5. Order: replay is item order, then call order within an item. The item order must be the
   original loop order, so `par_for` indices must equal the game's iteration order.

## 4. Verification harness (design)

Each parallel site is a *region* with an adapter: `snapshot(ctx)`, `restore(ctx)` and
`digest(ctx)` over the outputs it mutates. For the shadow region that is the per-mesh normal and
silhouette arrays plus the per-worker scratch.

- **Check mode**, the first `PAR_CHECK` calls (default 300, about 10 s of play):
  1. snapshot, then run serially with deferral → output digest + `rec_digest`;
  2. restore, then run with `par_for` → both digests again;
  3. compare the two pairs;
  4. replay the records once.
- **Switch:** if every check matches, the region switches to parallel only.
- **Disabling:** a mismatch, a fault, or a log overflow disables the region for the session
  (serial from then on). This is logged with the region, call index and which digest differed.
- **Switches:** `PAR_<REGION>=0` disables a region, and a gamepatch switch (for example
  `GAMEPATCH_PARALLEL=0`) turns the whole thing off.
- **Session log** (through `gp_log` into `logs/gamepatch.log`), one line per region every ~600
  calls and at exit: calls, % parallel, mean µs parallel vs the serial mean from check mode,
  records per call, faults, overflows, mismatches, disabled reason. `par_get_stats()` adds wakes
  and mean fork/join time.

Already demonstrated in the prototypes:
- `bench verify`: serial == parallel byte-for-byte under PC_24 + FTZ.
- `rectest`: identical record digest serial vs parallel, and identical replayed effects.

Not yet built: the region wrapper itself (a check.c). It's ~120 lines on top of `par_for` +
`rec_*`, and needs adapters written per region by R1-R4.

## 5. Limits and risks

- **Thread safety of in-place callees:** they are only checked for global writes. Writes through
  pointers into shared objects (for example a shared mesh model used by two instances) are
  invisible to the cloner. Each region needs an ownership argument per item: shadow volumes are
  per instance, but the geometry model may be shared, so normals must go to per-instance buffers.
- **Code the gamepatch rewrote:** in-place callees can land in gamepatch replacements (invsqrt
  0x441c56, quatmat…). Those must be reentrant; they are pure today, but the hittest/quatmat
  statistics counters use Interlocked.
- **CRT callees:** rand, errno, strtok and the static CRT's lazily allocated per-thread data. List
  them in `stop` and never run them from workers unless proven.
- **Tail latency:** the tail after parking (p99 0.5 ms with 7 workers) is real. Prewake before the
  region, or accept serial for regions under ~200 µs.
- **Main-thread replay cost** (0.11 µs/record) comes off the gain. Regions that emit one record per
  vertex will not pay off; record per item or per batch.
- **Game restrictions:** D3D stays on main (wined3d is not created MULTITHREADED). Nothing
  lockstep-relevant may be parallelised: client-side only, so patched and unpatched players stay
  in sync.
- **Harness:** `pool/build-and-run.sh` must be added to README.md's index before committing (tree
  rule).
