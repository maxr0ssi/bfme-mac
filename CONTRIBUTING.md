# Contributing

## Test reports

Everything so far was measured on one M3 Max. Results from other Apple Silicon Macs are useful.
With the game running and a fight on screen:

```sh
scripts/measure-session.sh on             # diagnostics on (~2 ms per frame)
scripts/measure-session.sh summary        # frame-time distribution, per-pass times
scripts/measure-session.sh off
```

(`measure-session.sh sample` needs a local profiler build and the game's function map, which are
not in the repo; leave it out.)

Open an issue with your Mac model, macOS version, resolution, the settings you play at, and the
`summary` output.

## Performance work

In large battles a frame takes 42–51 ms, 25–32 ms of it in the game's own code
([PERFORMANCE.md](docs/PERFORMANCE.md) §8). Game-side changes
must not change what the game computes:

1. Find the cost with a measurement (`docs/PERFORMANCE.md` has the tools and the current map).
2. Replace it in `gamepatch/`: check the original bytes, add a switch in `gamepatch.ini`.
3. Prove it in `gamepatch/tests/`: run the game's own code original against patched over every
   input you can (all 2³² for a single-float function), in the game's FPU mode.
4. Record the before/after numbers in `docs/PERFORMANCE.md`.

Wine changes go in `patches/` as `git format-patch` files against Wine 10.0, checked with Wine's
d3d9 tests and the benches in `tools/` (`--crc` for images, `--hash` for device calls). Wine
patches are LGPL-2.1-or-later, like Wine itself; terms in [NOTICE](NOTICE) and
`patches/COPYING.LIB`.

## Art

New art is a recipe tree in `assets/<faction>/` built by `python3 -m sagekit`. A faction reuses
the Dwarven tree with its own palette (`style.py`), shapes (`shapes.py`) and atlas (`atlas.py`).
Rules: [assets/README.md](assets/README.md).

## General

Follow [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and keep the harness hooks on
(`git config core.hooksPath .githooks`). Measurements that show no gain are worth recording too.
