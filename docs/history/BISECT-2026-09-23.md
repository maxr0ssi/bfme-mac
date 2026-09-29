# Bisecting the WoW64 `syscall_32to64` fault (2026-09-23)

Goal: find the commit between `wine-10.0` (assumed good) and `wine-11.0` (bad) that introduced the
fault described in `patches/WINE-BUG-REPORT.md`.

**Result: there is no such commit. The bisect cannot be run, because there is no good end.**
The fault is present in *every* commit of Wine that can be built and booted on this machine, the
oldest of which is 2025-03-25. Everything older than that does not start at all on macOS 26.3, for
an unrelated reason. Details and numbers below.

## The predicate

Discovered by the lead: the 32-bit d3d9 test suite `visual` dies a few seconds in, with no test
output, in a fraction of runs. A dying run prints exactly the bug-report symptom:

```
0320:err:seh:call_seh_handlers invalid frame 000000000032B4B0 (0000000100102000-00000001001FFD20)
0320:err:seh:NtRaiseException Exception frame is not in stack limits => unable to dispatch exception.
```

`0x32B4B0` is a 32-bit stack address being checked against the **64-bit** thread's stack limits:
the 32-bit exception is being dispatched on the 64-bit side, which is the same
`syscall_32to64`-executed-as-32-bit-code failure as in the game.

One run:

```sh
WINEPREFIX=<throwaway under build/> WINEDEBUG=-all,err+seh WINEDLLOVERRIDES="mscoree,mshtml=" \
  perl -e 'alarm 45; exec @ARGV' -- \
  <engine>/bin/wine <build>/dlls/d3d9/tests/i386-windows/d3d9_test.exe visual
```

* `WINEDEBUG=-all` **alone is wrong**: it suppresses the `err:seh` line too, and an aborting run then
  produces zero bytes, indistinguishable from a run that hung before starting. `-all,err+seh` keeps
  the one channel that carries the evidence and costs nothing.
* ABORT = the marker line appears (always at 1–3 s, exit code 41).
* SURVIVED = the run gets past the startup window. How far it then gets varies by commit — wine-11.0
  runs the whole suite in ~34 s, wine-10.5 fails to create a d3d9 device and stops after ~15 s — so
  the predicate must *not* require the "tests executed" summary line.
* 12 runs per commit. Harness: `build/bisect-run.sh` (also usable as a `git bisect run` script;
  `PREDICATE_ONLY=1 ENGINE=… BUILD=… PREFIX_DIR=… TAG=…` runs only the measurement).

## Measurements

| commit | what it is | date | aborts / 12 |
|---|---|---|---|
| `db11d0fe6a1` | **wine-11.0** (`engines/src-11.0`, `wine/build-11.0`) | 2026-01-13 | **4** (and 4/12 again in a second campaign, 2/12 in a third) |
| `f3843ea16b8` | **wine-10.5** | 2025-04-04 | **3** |
| `8fd49c4d8e9` | ntdll: Don't use private writable mappings on macOS (wine-10.4-30) | 2025-03-25 | **9** |
| `aae9ba21cef` | its parent, wow64: Skip memcpy for null pointer | 2025-03-21 | **does not boot** |
| `b0738596750` | **wine-10.0** | 2025-01-21 | **does not boot** |

"Does not boot" means: `wineboot -u` creates the directory and then every process dies with

```
wine: Unhandled page fault on write access to 0000000140021AD8 at address 00006FFFFFC15270
wine: could not load kernel32.dll, status c0000135
```

i.e. the loader cannot write to the image it just mapped. No `syswow64\cmd.exe` is ever installed,
so the prefix is empty and nothing 32-bit can run. This is
[bug 58008](https://bugs.winehq.org/show_bug.cgi?id=58008), fixed by `8fd49c4d8e9`
("ntdll: Don't use private writable mappings on macOS", Alexandre Julliard, 2025-03-25, first
released in wine-10.5). That commit is therefore the **floor**: it is the oldest commit in
`wine-10.0..wine-11.0` that runs at all here, and it already fails the predicate — more often than
wine-11.0 does.

The fix does not back-port trivially: `map_file_into_view()` in wine-10.0 is structured differently
(`get_unix_prot( vprot | VPROT_COMMITTED )`, `MAP_PRIVATE` only for `VPROT_WRITECOPY`) and
`git cherry-pick 8fd49c4d8e9` conflicts. Making wine-10.0 boot here is its own porting project,
and it would only tell us about a tree that nobody will ship.

### Consequence

```
wine-10.0 ........ aae9ba21cef   does not run on macOS 26.3  (untestable)
8fd49c4d8e9 ...... wine-11.0     runs, and fails the predicate everywhere we sampled
```

`git bisect start wine-11.0 wine-10.0` would mark the entire older half as `skip` and terminate
without a culprit. **Not run**, therefore; there is no `git bisect log` to paste.

The rate is not constant — 9/12 at the floor, 3/12 at wine-10.5, 2–4/12 at wine-11.0 — so something
in the 236 commits of `8fd49c4d8e9..wine-10.5` made the race markedly *less* likely without fixing
it. The obvious candidate is `3a16aabbf55` "ntdll: On macOS x86_64, swap GSBASE between the TEB and
macOS TSD when entering/leaving PE code" (in wine-10.5), together with `928eb3a9b70` and
`245e8cedf05`, which rework exactly the 64-bit syscall dispatcher's `%gs` handling.

## What this means for the bug

The symptom is that the CPU is still in 32-bit mode (`cs` = the 32-bit selector) when
`wow64cpu!syscall_32to64` is entered, so the 64-bit entry bytes are decoded as 32-bit instructions.
The measurements say this is **not a regression introduced between 10.0 and 11.0** but a
long-standing defect in Wine's macOS/Rosetta WoW64 support, whose *probability* drifts with
unrelated changes — which is exactly what a race in mode switching looks like. The places where the
64→32 transition state lives on macOS, and therefore the places to instrument, are:

* `dlls/ntdll/unix/signal_x86_64.c` — the macOS GSBASE swap (`3a16aabbf55`,
  `3aa28e45201` "Don't swap GSBASE on macOS in `user_mode_callback_return()`", wine-10.9), the
  syscall dispatcher's `%gs` access (`928eb3a9b70`, `245e8cedf05`), `check_invalid_gsbase()`
  (`94447cee619`, `a3e3c0a1172`) and `86b886788ba` "Ensure `%cs` is correct in sigcontext on x86_64
  macOS" (wine-10.13) — the last one is the only commit in the range that is explicitly about the
  register that is wrong in our dump.
* `dlls/wow64cpu/` — `syscall_32to64` / `BTCpuSimulate`, and the late-2025 series that started
  storing the real segment registers in the WoW64 context (`1df5fbf31e3`, `9393214fd61`,
  `5881f2bdfb1`, wine-10.16), all of which are already in wine-11.0.
* `KiUserCallbackDispatcher` return path: the game's trigger is ~15,000 64→32 callbacks, and the
  d3d9 `visual` test aborts during its window/message-pump startup, i.e. the same path.

## Reverting

Not applicable — there is no culprit commit to revert. The `git checkout wine-11.0 && git revert`
proof step was skipped for that reason.

## Proposed addition to `patches/WINE-BUG-REPORT.md`

> **Reproducer without the game.** The fault also hits Wine's own 32-bit test suite. On this host,
> `wine dlls/d3d9/tests/i386-windows/d3d9_test.exe visual` (WoW64, `WINEDEBUG=-all,err+seh`) aborts
> within 1–3 s, with no test output and
> `err:seh:call_seh_handlers invalid frame 00000000003XXXXX (<64-bit stack range>)` followed by
> `err:seh:NtRaiseException Exception frame is not in stack limits`, in 2 to 4 runs out of 12
> (wine-11.0 built from source, `--enable-archs=i386,x86_64`, mingw-w64 GCC PE side, x86_64 host
> side under Rosetta 2, macOS 26.3.1 / M3 Max). The same test survives the other runs and completes
> all 211,245 checks in ~34 s, so this is a race, not a deterministic failure of a particular test.
>
> **Not a 10.0→11.0 regression.** We attempted to bisect it. The oldest commit in
> `wine-10.0..wine-11.0` that can run at all on macOS 26.3 is `8fd49c4d8e9` ("ntdll: Don't use
> private writable mappings on macOS", the fix for bug 58008; everything older dies with
> `could not load kernel32.dll` before a prefix is usable), and that commit already reproduces the
> fault at 9 aborts out of 12 — a higher rate than wine-11.0's 4/12. wine-10.5 gives 3/12. So the
> defect predates the whole bisectable window and its probability merely drifts; the drop between
> `8fd49c4d8e9` and wine-10.5 coincides with the macOS GSBASE-swap rework (`3a16aabbf55`,
> `928eb3a9b70`, `245e8cedf05`).

## Reproducing this investigation

```sh
cd wine/src && git checkout --detach <commit>
build/bisect-run.sh                      # build + install + 12 predicate runs, prints a verdict
# or, against an existing build:
PREDICATE_ONLY=1 TAG=bad11 ENGINE=$PWD/engines/src-11.0 BUILD=$PWD/wine/build-11.0 \
  PREFIX_DIR=$PWD/build/prefix-bisect11 RUNS=12 build/bisect-run.sh
```

Logs: `build/calib-bad.log`, `build/calib-bad2.log` (wine-11.0), `build/calib-good-10.5.log`,
`build/calib-good-8fd49c4.log`, `build/probe-parent.log`, `build/calib-good.log` (the invalid first
wine-10.0 campaign — kept as the example of what a silently-broken prefix looks like), and
per-run logs in `build/bisect-logs/`.

Two things the harness learned the hard way, both now enforced in `build/bisect-run.sh`:

1. **Verify the prefix before trusting a "good" result.** The first wine-10.0 campaign reported
   12/12 survived; in reality wineboot had crashed, the prefix had no `syswow64`, and every run sat
   there doing nothing until the timeout killed it. The script now requires
   `syswow64\cmd.exe /c ver` to print "Microsoft Windows" and exits 125 otherwise.
2. **Build with `make -k`.** Older trees fail to link `dwrite_test.exe` with mingw-w64 GCC
   (`undefined reference to truncf`), which stops a plain `make` before anything else is built. The
   script keeps going and then demands that `dlls/d3d9/tests/i386-windows/d3d9_test.exe` and
   `make install` succeed, so a genuinely broken commit is still detected (exit 125 → skip).

## State left behind

* `wine/src` is on a **detached HEAD at `aae9ba21cef`** (the last commit probed), working tree
  clean, no bisect in progress. Restore your work with `cd wine/src && git checkout
  lock-whole-buffer` — the branch itself was never touched.
* `wine/build-bisect` and `engines/src-bisect` therefore hold that same commit, which **does not
  boot**. Before using `engines/src-bisect` for anything, check out a usable commit and re-run
  `build/bisect-run.sh` (or `scripts/build-wine.sh bisect`).
* `engines/src-11.0`, `wine/build-11.0`, `engines/stable`, `engines/w10`, `prefixes/` and the
  `lock-whole-buffer*` branches were not modified. Throwaway prefixes created here:
  `build/prefix-bisect`, `build/prefix-bisect11`.

## What to do next

1. **Report it upstream as-is.** The d3d9 `visual` reproducer is far stronger than the game trace:
   stock Wine, stock test suite, no mod, no game data, 12-run script. Append the section above to
   `patches/WINE-BUG-REPORT.md` and drop the "introduced between 10.0 and 11.0" framing.
2. **Do not spend more machine time on bisecting this range.** If a last-good point is still wanted,
   it is before wine-10.0 and can only be reached by first making those trees boot on macOS 26
   (back-porting the bug-58008 fix), or by running an older macOS.
3. **A bisect that *is* possible and probably useful:** `8fd49c4d8e9..wine-10.5` (236 commits,
   ~8 steps) with an inverted predicate (bad = ≥ 8 aborts/12, good = ≤ 4/12, more runs per step to
   beat the noise) to identify what lowered the rate from 9/12 to 3/12. Whatever it is, it touches
   the machinery that decides the mode-switch state, which is where a real fix would go.
4. **For the game specifically:** the abort rate is a race, so mitigations that change timing
   (thread count, `WINE_CPU_TOPOLOGY`, forcing single-threaded load) have already been ruled out in
   the bug report. The next experiment with real leverage is instrumenting `syscall_32to64` entry
   (log `%cs` / gsbase on every entry under `+seh`) in `engines/src-bisect` and running
   `scripts/setup-prefix.sh src-bisect` + the harness to catch the transition that goes wrong.
