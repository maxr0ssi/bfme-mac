# Development

The code is written by Claude Code sessions, often several in parallel; the repo owner plays and
tests the games. These are the rules the work follows and the reasons for them.
[AGENTS.md](../AGENTS.md) is the checklist form and [CONTRIBUTING.md](../CONTRIBUTING.md) the
on-ramp for people. The rules apply to human contributors as well.

## Running the game

- Agents don't launch the game. No hands-free runs (`scripts/test-skirmish.sh`, `bench-battle.sh`,
  `bench-matchstart.sh` stay unused unless the player asks). A game run takes over the player's
  screen and costs minutes. The player installs, plays and reports; you read `logs/` afterwards.
- Work the mechanism out from code: disassembly, Wine's source, EA's released *Generals* source for
  the shared engine, standalone benchmarks. Lay out the full plan with measured costs and get a go.
  Batch what needs the game into one play session.
- Frame-time logging and samplers may attach to the player's session when they agree
  (`scripts/measure-session.sh`); nothing that suspends or steers it.
- Nothing is installed without review. New art is rendered before/after and shown first.

## Correctness

- A game patch must give the same bits as the original in the game's FPU mode (24-bit x87
  precision, round-to-nearest), so patched and unpatched players stay in lockstep over LAN. Prove
  it with a test in `gamepatch/tests/` that runs the game's own code, original against patched,
  over all inputs where feasible (2³² for single-float functions).
- No visual downgrades: a trade-off that changes the picture (e.g. turning a pass off) is offered
  to the player as a separate, explicit choice, never shipped.
- Wine changes are checked without the game: Wine's d3d9 visual tests, `tools/d3d9lockcheck.c`,
  and `--crc` / `--hash` image and call checksums in the benches.
- Parallel code checks itself: compute serial and parallel, compare byte for byte for the
  first frames, switch off on any difference (`parallel/DESIGN.md`).

## Evidence

- A change counts only when its effect is outside the run-to-run spread. Every number goes into
  `docs/PERFORMANCE.md` (or `docs/LOAD-TIME.md`) with the date, build and scene.
- When a later measurement overturns an earlier claim, mark the correction where the claim was;
  keep dead ends and say why they died.
- Check the code path is live at the settings the player plays (UltraHigh uses shadow maps, not
  shadow volumes) before optimising it.

## Safety

- Every game patch checks the exact original bytes first and has a switch (`gamepatch.ini`,
  `GAMEPATCH_<NAME>=0`); every install script can undo itself (`--revert`; `scripts/install.sh
  --uninstall`) and keeps `.orig` / `.bak` copies.
- No game or Wine binaries in git. The harness blocks them with no override.
- Everyone in a LAN game must run identical game data (the group pack and the art packs,
  `MULTIPLAYER.md`); retail compatibility is not a goal.

## The harness

`harness/` checks every edit (a Claude Code hook) and every commit and push (git hooks): the
copyright gate, script syntax and Wine hygiene, no touched code file over 600 lines, a commit budget (warn at
400 changed lines, block at 600), and a one-line entry in `docs/REFERENCE.md` for every script.
When it blocks, fix the cause; its message says how. Details: `harness/README.md`. CI
(`.github/workflows/checks.yml`) runs `harness.py tree` and `diff` against the previous commit on
every push and pull request, no game or Wine build needed.

## Checks

```sh
git config core.hooksPath .githooks          # once per clone
python3 harness/harness.py diff --staged     # what pre-commit sees
python3 harness/harness.py tree              # repo-wide invariants
scripts/game-patch.sh --test                 # gamepatch bit-exactness tests (throwaway prefix)
parallel/pool/build-and-run.sh bench         # worker-pool tests, never beside a running game
```

## Where things are

`README.md` is the landing page; `docs/REFERENCE.md` indexes every script and tool;
`docs/PERFORMANCE.md` is the measured record; `assets/README.md` has the art pipeline's rules.
