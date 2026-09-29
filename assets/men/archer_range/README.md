# Men archer range (`GondorArcherRange`, `ArnorArcherRange`)

Level-ups: [`archer_range_level2`](../archer_range_level2/README.md) (V1),
[`archer_range_level3`](../archer_range_level3/README.md) (V2), chained on this recipe.

## What changed

EA's body is kept whole (buttressed tower, dome, hall, terrace, yard walls, target arcade and
its animated pulley). Added, in the citadel's kit:

- **Tower**: two machicolated galleries (corbels, a sable band of silver stars, merlons) round
  the lower shaft (z 64..73) and the upper (z 87..96), a corbelled bartizan with slit windows and
  a slate spirelet on each chamfer of the upper one; steel ribs and a lantern on the dome, kept
  under z 107.5 (level 3 stands the archer's statue there, its plinth half 3.1).
- **Hall**: a steel ridge with cresting and gilt knobs, a fascia on brackets, a frieze of gilt
  stars and a White Tree roundel on its front; a roundel on the terrace's back wall.
- **Yard walls**: upright piers and White Tree roundels on their outer faces (level 2 wraps them).
- **Banners**: two, on the tower's south and east faces (cap 2); cloth in `GBHCArcheryN`.
- **Paint**: the dome's and the hall roof's slate charcoal, the painted targets keep their red
  (`paint.py`: `Slate`, `Keep`).

## Status

Installed with the Men pack. `ARCHERY` 912 -> 6,956 triangles, height 105.3 -> 107.7 (+2.2 %),
269/269 checks. Construction, damaged, really damaged and rubble are rebuilt along EA's pieces.

- `footprint_margin = 1.3`: the yard walls' and the tower's faces are the footprint's edge.
- Own texture `gbarcheryn_H`; the damaged models' sheet `GBArcheryN_LD` gets `gbarcheryn_HD`
  (`levels.with_damaged`) so the lifecycle step rebuilds them.
