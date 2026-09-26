# BFME on Apple Silicon

Scripts, Wine patches and a game patch for running *The Battle for Middle-earth II* (1.06) and
*Rise of the Witch-king* (2.02) on Apple Silicon Macs.

[Play guide](docs/PLAYING.md) · [Multiplayer](MULTIPLAYER.md) · [Performance record](docs/PERFORMANCE.md) ·
[Development](docs/DEVELOPMENT.md)

The games are 32-bit DirectX 9 programs from 2006. On a Mac they run through Wine: Direct3D 9 is
translated to OpenGL by Wine's wined3d, OpenGL runs on Metal, and all the x86 code runs under
Rosetta 2. With a stock Wine build, RotWK ran at 8–11 FPS in an empty base and took about three
minutes to load a skirmish. The fixes here are in two places: patches to Wine, and a patch
applied to the game in memory at startup. The game patch is written to give bit-identical results
to the original code, so that patched and unpatched players stay in sync over LAN.

The code was written with Claude Code. The agents did not run the game; they worked from logs,
profiles, disassembly and standalone tests, and the games were tested by playing them.

## Results

RotWK 2.02 with the HD Edition, 3024×1964, UltraHigh, on a MacBook Pro with an M3 Max
(macOS 26). Measured in play sessions; details in [docs/PERFORMANCE.md](docs/PERFORMANCE.md) §2
and [docs/LOAD-TIME.md](docs/LOAD-TIME.md).

| | Before | After |
| --- | --- | --- |
| Skirmish load | ~3 min | ~12 s |
| Own base, no fighting | 8–11 FPS | 30 FPS (engine cap) |
| Small battle | ~11 FPS | 22–30 FPS |
| Large battle | not measured | 17–25 FPS (40–60 ms frames) |

Large battles are the open problem. Only one machine has been tested.

## Setup

You need your own copy of the games. EA no longer sells them. They can be installed from the
original discs, or with the community [All-in-One BFME Launcher](https://www.bfmeladder.com/download)
(Windows, needs a CD key). This repo does not download them.

Install (RotWK needs BFME2 as well; Git and Python come with Apple's Command Line Tools):

```sh
git clone https://github.com/maxr0ssi/bfme-mac.git && cd bfme-mac
scripts/install.sh --bfme2 <your BFME2 folder> --rotwk <your RotWK folder>
scripts/play-rotwk.sh
```

The installer downloads the latest release of the fixes from this repo, the Wine engine and
AutoHotkey (pinned versions, checksums verified),
copies your game folders into its own Wine prefix without changing the originals, asks for your
CD keys, and puts app bundles in /Applications. `scripts/install.sh --status` shows what is
installed; `--uninstall` removes it.

Settings and known issues: [docs/PLAYING.md](docs/PLAYING.md). LAN over the internet (ZeroTier),
Mac or PC: [MULTIPLAYER.md](MULTIPLAYER.md).

## What is changed

| Part | Changes | Code |
| --- | --- | --- |
| Wine d3dx9 | Wine's d3dx9_27 can replace Microsoft's (the load-time fix); faster effect/preshader execution | [patches/d3dx9-setrawvalue](patches/d3dx9-setrawvalue/) |
| Wine wined3d | 21 patches: dynamic buffer locks no longer wait for the render thread, locked data is written directly to GPU buffers, redundant state updates removed, GLSL programs built ahead of first use, only changed shader constants uploaded | [patches/wined3d-wow64-buffers](patches/wined3d-wow64-buffers/) |
| Game patch | A proxy `dinput8.dll` that replaces hot functions in memory (inverse square root, UI hit test, quaternion and particle maths, animation) with SSE versions, each tested bit-exact against the original | [gamepatch](gamepatch/) |
| Worker pool | Multi-core framework with self-verification. Not yet used for a speed-up | [parallel](parallel/) |

Each game patch checks the original bytes before writing, can be switched off in
`gamepatch.ini`, and has a test in `gamepatch/tests/`. The install scripts have `--revert`.
Measurements that didn't pan out are kept in [docs/PERFORMANCE.md](docs/PERFORMANCE.md).

[sagekit](sagekit/) and [assets](assets/) are an art pipeline (Blender to the game's W3D format)
used for new Dwarven buildings. In progress.

## Repository

| Path | Contents |
| --- | --- |
| `scripts/` | launch, install and measurement scripts |
| `patches/` | Wine patches and bug reports |
| `gamepatch/` | game patch and tests |
| `parallel/` | worker pool ([design](parallel/DESIGN.md)) |
| `sagekit/`, `assets/` | art pipeline and building recipes |
| `tools/` | archive tools, profilers, benchmarks |
| `harness/` | commit checks |
| `docs/` | [play guide](docs/PLAYING.md), [performance](docs/PERFORMANCE.md), [load time](docs/LOAD-TIME.md), [modding](docs/MODDING.md), [script index](docs/REFERENCE.md) |

## Development

```sh
git config core.hooksPath .githooks
python3 harness/harness.py tree
scripts/game-patch.sh --test
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

[Wine](https://www.winehq.org/); Mac Wine builds by Gcenx and [Sikarugir](https://github.com/Sikarugir-App);
[DrewHoo/battle-for-middle-earth-apple-silicon](https://github.com/DrewHoo/battle-for-middle-earth-apple-silicon)
([attribution](tools/ATTRIBUTION.md)); the [OpenSAGE](https://github.com/OpenSAGE) Blender add-on;
Open-BFME-1; EA's released *Command & Conquer: Generals* source.

## License

MIT ([LICENSE](LICENSE)). The Wine patches in `patches/` are LGPL-2.1-or-later
([patches/COPYING.LIB](patches/COPYING.LIB)). Unofficial; not affiliated with EA, Warner Bros. or
the Tolkien Estate. No game files are included.
