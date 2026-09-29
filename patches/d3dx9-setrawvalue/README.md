# d3dx9-setrawvalue — fast loading with Wine's own d3dx9_27

Applied on top of `wine-10.0` by `scripts/wine-fixes.sh`, which builds
`dlls/d3dx9_27/i386-windows/d3dx9_27.dll` and installs it into the engine.

| patch | author | what |
|---|---|---|
| 0001 | Connor McAdams (upstream, in 11.x) | Partially implement `ID3DXEffect::SetRawValue()` (4-component vectors) |
| 0002 | Connor McAdams (upstream, in 11.x) | 4x4 row-major matrices in `SetRawValue()` |
| 0003 | local | Import `windowscodecs` directly instead of delay-loading it |
| 0004 | local | Struct parameters in `SetRawValue()` |
| 0005 | local | Preshader instructions run through direct register pointers (`WINE_D3DX9_FXOPT` bit 0x1) |
| 0006 | local | Only the preshader instructions whose inputs changed are rerun (bit 0x2) |
| 0007 | local | Parameter handles checked without a `strncmp()` call |
| 0008 | local | CommitChanges() skips constant states that cannot set anything; `WINE_D3DX9_FXOPT` read once (bit 0x4) |

**Why.** With Microsoft's native d3dx9_27 (installed by winetricks) the second half of the
loading bar is D3DX turning textures into GPU formats in x87 floating-point code, which
Rosetta emulates slowly: 99 % of the load's main-thread samples land in one x87 loop inside
`d3dx9_27.dll` (`tools/eipsample.c`). Wine's own d3dx9_27 does the same work in ~12 s instead
of ~190 s, but in Wine 10.0 `SetRawValue` is a stub, and both games upload their skinning
palette through it — `struct { float4 Rotation; float4 Translation_Zero; } [90]` in
`defaultw3d.fxo` (100 in `normalmapped.fxo`) — so every skinned unit rendered invisible.

**0003** is a toolchain workaround, not a Wine bug: with Homebrew's mingw-w64 binutils the
delay-load import table lands in the read-only `.idata` section, and the first WIC call
(`D3DXGetImageInfoFromFileInMemory` on a non-DDS image) faults in `_delayLoadHelper2`.

**0004** walks struct members and array elements in shader-register layout (every scalar,
vector and matrix row starts a new 16-byte register) and copies each leaf into the packed
storage the effect keeps; 4x4 row-major matrices reuse 0002's transpose. Covers every struct
in the games' `.fxo` files: the bone palettes, `{float3 Color; float3 Direction}` lights
(32 bytes raw, 24 stored) and the fog/particle structs with scalar members.

Known leftover: `d3dx_load_pixels_from_pixels Unhandled filter` (~2.6k per load) — a
resampling mode Wine's D3DX falls back from; cosmetic at most.

**0005–0007: the effect framework's main-thread cost.** Per batch the game re-sets every
engine-bound parameter (camera, lights, fog, shadow, time) and per mesh the per-object ones
(world matrix, bones, point lights) before `CommitChanges()`
([PERFORMANCE.md](../../docs/PERFORMANCE.md) §11). Each set marks the parameter dirty, so the
vertex shader preshaders (~70 instructions in `defaultw3d.fxo`) ran again on every `BeginPass()` and `CommitChanges()`, through a generic
interpreter: ~70 % of the effect framework's time. 0005 gives each directly addressed instruction
pointers to its registers and inlines the common operations (same registers, same order, same
double operations: bit-identical). 0006 keeps a copy of each preshader's input registers: no
change, no run; otherwise only the instructions depending on changed registers run, plus the
writers of the values they read and the last writer of each output they touch (only for
preshaders that never read a temporary or output before writing it). 0007 replaces the
`strncmp()` in every handle check with an inline compare of the same bytes.

`tools/d3dx9fxbench.c` replays the game's call pattern on the real `.fxo` files: 600 batches a
frame (shadow-map pass + main view) went from 10.9 to 3.3 ms, `BeginPass` 9.5 → 2.0 µs,
`CommitChanges` 2.9 → 0.7 µs; every device call the effects issue (hashed through an
`ID3DXEffectStateManager`) is identical, and Wine's d3dx9_36 effect tests pass unchanged
(233,887 tests, 0 failures, 26 todo). `WINE_D3DX9_FXOPT=0` restores the old paths at run time.

0008 leaves out ~12 constant states per pass that never make a device call, and reads
`WINE_D3DX9_FXOPT` once (it was read on every call when unset): CommitChanges 0.45 → 0.39 µs per
mesh.
