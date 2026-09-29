# Loading time

A RotWK skirmish loads in about 12 s from Play to the map, down from about 190 s. The slow part was
Microsoft's `d3dx9_27.dll` (installed by winetricks) converting textures in x87 code, which Rosetta
emulates slowly. Wine's own `d3dx9_27` does the same work in native-speed code; with
[patches/d3dx9-setrawvalue](../patches/d3dx9-setrawvalue/) it also renders skinned units. Both
are built by `scripts/wine-fixes.sh`; `scripts/install.sh` installs the prebuilt DLL.

The 12 s was timed with Wine's unpatched builtin DLL (units invisible). The patches change effect
parameters, not texture loading, and no clean load time with the final DLL has been recorded.
BFME2 with the patched DLL has not been timed either.

## How it was found (2026-09-23)

| step | finding |
|---|---|
| loading bar decoded from harness captures | RotWK: 0→~64 % within ~5 s of Play, then a linear crawl at ~0.17 %/s to 93 % (BFME2: 56 %, then ~0.08 %/s). ~35 % of the bar is ~97 % of the time |
| CPU during the crawl | ~110 %, flat: one thread busy, the rest idle |
| macOS `sample` | main thread ~99 % in translated 32-bit code, 25/3287 samples in `ntdll.so`: no waits, no I/O, no spin |
| detail level | `StaticGameLOD` VeryLow (1/16 texels): 269 s → 16 s. Cost is proportional to texels |
| TGA → DDS pre-bake (`tools/prebake_textures.py`) | 231 s → 168 s. File format and mipmap generation are only a quarter of it |
| in-guest profiler (`tools/eipsample.c`) | 99.2–99.5 % of the loading thread in Microsoft's `d3dx9_27.dll`, game 0.4 %, wined3d 0.3 %. The hot loop is x87 (707 x87 ops in 3.8 KB) |
| Wine's builtin d3dx9_27 | 12 s Play → map. Units invisible: `ID3DXEffect::SetRawValue` is a stub in 10.0 (~96k calls per load), and the games upload their bone palette through it |
| `patches/d3dx9-setrawvalue/` | SetRawValue with struct support: units render, 0 SetRawValue fixmes |

## Baseline and noise (2026-09-22, RotWK, `WINEDEBUG=-all`)

With Microsoft's DLL: 283 s on a cold first run, 187 s and 198 s warm. `WINEMSYNC=1` gave 182 s and
~176 s, inside the run-to-run spread, so msync is not a loading lever. Wine's debug logging is:
the harness's default `warn+d3d,+seh,err+all` made the same load take 290 s. Compare harness timings
only at equal `WINEDEBUG`.

Levers that did not matter: shader compiles, the wined3d map/lock path (179,637 synchronous map
pairs per load, ~0.3 % of the loading thread) and `WINE_CPU_TOPOLOGY`, which the w10 engine does
not read.

The full investigation, including the experiment matrix, is in
[history/LOAD-TIME-RESEARCH-2026-09-22.md](history/LOAD-TIME-RESEARCH-2026-09-22.md).
