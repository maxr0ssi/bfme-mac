# Agent instructions

Read [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) before editing.

- Never launch the game or run the hands-free benches; the player installs, plays and reports.
  Read `logs/` afterwards. Attach read-only probes to a session only when asked.
- Work the plan out from code first (disassembly, Wine source, standalone benches) and get a go
  before anything needs the game. Batch game-dependent checks into one play session.
- Game patches are bit-exact against the original in the game's FPU mode, with a test in
  `gamepatch/tests/` that runs the game's own code original against patched.
- No visual downgrades. Offer image-changing trade-offs as an explicit choice; never ship one.
- Every number goes into `docs/PERFORMANCE.md` with date, build and scene. Counts only outside
  the run-to-run spread. Correct overturned claims in place and keep dead ends.
- Confirm a code path runs at the player's settings before optimising it.
- Every patch checks original bytes and has a switch; every install script can undo itself
  (`--revert`; `scripts/install.sh --uninstall`).
- No game or Wine binaries in git. Never bypass the harness hooks.
- Every script gets a line in `docs/REFERENCE.md`. No code file over 600 lines.
- Nothing installs into the game without the player's review (art is shown before/after first).
- Ask before changing measured claims, the multiplayer contract (`MULTIPLAYER.md`) or harness limits.
