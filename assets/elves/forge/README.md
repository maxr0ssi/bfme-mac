# Elves forge (`EregionForge`)

EA's furnace tower, arched hearth, weapon rack, stone planter and mallorn remain whole.
The smith, equipment, foliage, upgrade crowns, bones, hearth fire and smoke are unchanged.

## Current design

- A silver-rimmed hexagonal collar and gilt leaf coronet crown the chimney; the flue stays open.
- Six silver-framed lancet windows dress the furnace shaft.
- The hearth keeps its arch under a silver barge board and gilt leaf finial.
- Three crystal lanterns stand on the planter; three hang from the mallorn at EA's lantern sites.
- Gilt leaf finials crown the weapon rack's upturned beam ends.
- Two player-colour leaf banners: one on the chimney, one beside the hearth.

The first pass's extra banners, rack pennants, chimney lanterns and added knotwork bands were
removed. EA's original carved and painted detail remains visible.

## Models, lifecycle and night

The skinned body `BOX01` uses `ebforgH` textures; cloth goes to `EBHCForge`. EA's forge atlas
paints retained faces and the fortress atlas paints additions. Mask hints retain bark and dark
steel, and turn the existing copper band into silver knotwork on enamel.

Construction carries the redesign. The previous `FORGE5` layout fallback was fixed by matching
the source's optional extra colour stream to the target's required streams, without dropping a
target requirement. `_D1`, `_D2` and `_D3` have no matched body pieces and remain EA's recoloured
models. These damage states are reported fallbacks, not custom lifecycle geometry.

At night the tree and planter lanterns, six shaft windows and hearth back wall glow. Free glow
cards occupy EA's tree-lantern locations. The chimney has no added night lanterns.

## Verification (2026-09-26)

Current body: 1,122 → 4,860 triangles; height and footprint unchanged. Checks: 130/130.
Day, lifecycle and night comparisons are in `build/assets/elves/forge/renders/`; `chimney`
looks behind the tree to show the crown. Awaiting player review; nothing installed.
