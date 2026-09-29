# Men barracks (`GondorBarracks`, `ArnorBarracks`)

Level-ups: [`barracks_level2`](../barracks_level2/README.md) (V1),
[`barracks_level3`](../barracks_level3/README.md) (V2), chained on this recipe.

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
- **Banners**: three (cap 3): two on the keep's south face, one on the north wing's yard face;
  cloth in `GBHCBarracks`.
- **Paint**: the dome's slate stays charcoal (`paint.Slate`; the recolour turned it pale).

## Status

Installed with the Men pack. `BARRACKS` 1,452 -> 7,386 triangles, footprint EA's, height
77.6 -> 92.1 (+18.7 %, the dome spike), 134/134 checks. Construction, damaged, really damaged and
rubble are rebuilt along EA's pieces.

- Own texture `gbbarracks_neH`; EA's damaged models draw `GBBarracks_NewD`, which no INI state
  swaps to: the recipe adds `gbbarracks_neHD` (`levels.with_damaged`), without which the
  lifecycle step left D1-D3 to EA.

## Shared modules

- [`../motifs.py`](../motifs.py): the production group's motifs (windows, courses, cornices,
  parapets, machicolations, roofs, domes, roundels, friezes, banners, masts, `closed`, `knob`).
- [`../levels.py`](../levels.py): the chained level-up recipe (`LevelMesh`, `chain`,
  `level_textures`, `with_damaged`; GBVet copies `GBV<letter><1|2>`).
- [`../paint.py`](../paint.py): `Slate`, EA slate on a building's own sheet painted charcoal.
