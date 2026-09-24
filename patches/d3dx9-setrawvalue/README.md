# d3dx9-setrawvalue — fast loading with Wine's own d3dx9_27

Applied on top of `wine-10.0` by `scripts/d3dx9-fix.sh`, which builds only
`dlls/d3dx9_27/i386-windows/d3dx9_27.dll` and installs it into the engine.

| patch | author | what |
|---|---|---|
| 0001 | Connor McAdams (upstream, in 11.x) | Partially implement `ID3DXEffect::SetRawValue()` (4-component vectors) |
| 0002 | Connor McAdams (upstream, in 11.x) | 4x4 row-major matrices in `SetRawValue()` |
| 0003 | local | Import `windowscodecs` directly instead of delay-loading it |
| 0004 | local | Struct parameters in `SetRawValue()` |

**Why.** With Microsoft's native d3dx9_27 (installed by winetricks) the second half of the
loading bar is D3DX turning textures into GPU formats in x87 floating-point code, which
Rosetta emulates slowly: 99 % of the load's main-thread samples land in one x87 loop inside
`d3dx9_27.dll` (`tools/eipsample.c`). Wine's own d3dx9_27 does the same work in ~12 s instead
of ~170 s, but in Wine 10.0 `SetRawValue` is a stub, and both games upload their skinning
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
