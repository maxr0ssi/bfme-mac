# Men barracks (`GondorBarracks`, `ArnorBarracks`)

Draft for review, not installed. Renders: `build/assets/men/barracks/renders/compare_*.png`
(level 1). The level-up meshes are chained on this recipe: [`barracks_level2`](../barracks_level2/README.md)
(V1, the yard wall) and [`barracks_level3`](../barracks_level3/README.md) (V2, the belfry and turrets);
rebuild them after this one, in that order.

## What changed

EA's body is kept whole (keep, buttresses, painted corbel arcade, dome, gate porch, wings). Added,
in the citadel's kit:

- **Keep crown**: a machicolated gallery round the upper shaft (corbels from the weathering, a
  sable band of silver stars, parapet, square merlons), a pinnacle over each corner pier; steel
  eave band, ribs, lantern, gilt orb and spike on the dome (to z 88.5; inside V2 at level 3).
- **Keep faces**: EA's south window in a hooded voussoir surround, a White Tree roundel over it,
  White Tree roundel on the west face.
- **Gate porch**: pilasters, an eleven-stone archivolt with keystone, an entablature with seven
  gilt stars on sable, a slate-coped pediment with the White Tree, a winged-helm crest and
  corner pinnacles.
- **Wings**: square merlons with capstones on every parapet, surrounds round EA's windows.
- **Banners**: three house-colour banners (cap 3): two on the keep's south face, one on the
  north wing's yard face. The cloth shows after `sagekit house men`.
- **Paint**: the dome's slate stays charcoal (`paintkit.Slate`; the recolour turned it pale).

## Fit and status

- `BARRACKS` 1,452 -> 7,386 triangles; footprint EA's; height +18.7 % (dome spike, z 88.5).
- 134/134 checks. Construction, damaged, really damaged and rubble all rebuilt along EA's pieces.
- Own texture `gbbarracks_neH`; EA's damaged models draw `GBBarracks_NewD`, which no INI state
  swaps to: the recipe adds `gbbarracks_neHD` (`levels.with_damaged`), without which the
  lifecycle step left D1-D3 to EA.

## Shared modules here

- `motifs.py`: the production group's motifs (windows, courses, cornices, parapets,
  machicolations, roofs, domes, roundels, friezes, banners, masts, `closed`, `knob`).
- `levels.py`: the chained level-up recipe (`LevelMesh`, `chain`, `level_textures`,
  `with_damaged`; GBVet copies `GBV<letter><1|2>`).
- `paintkit.py`: `Slate`, EA slate on a building's own sheet painted charcoal.
