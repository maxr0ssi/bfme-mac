# Men archer range (`GondorArcherRange`, `ArnorArcherRange`)

Draft for review, not installed. Renders: `build/assets/men/archer_range/renders/compare_*.png`
(level 1). The level-up meshes are chained on this recipe: [`archer_range_level2`](../archer_range_level2/README.md)
(V1, the thickened yard walls and the obelisks) and [`archer_range_level3`](../archer_range_level3/README.md)
(V2, the arcades, the turret and the statue); rebuild them after this one, in that order.

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
- **Banners**: two house-colour banners, on the tower's south and east faces (cap 2).
- **Paint**: the dome's and the hall roof's slate charcoal, the painted targets keep their red
  (`barracks/paintkit.py`: `Slate`, `Keep`).

## Fit and status

- `footprint_margin = 1.3`: the yard walls' and the tower's faces are the footprint's edge.
- Own texture `gbarcheryn_H`; the damaged models' sheet `GBArcheryN_LD` gets `gbarcheryn_HD`
  (`levels.with_damaged`) so the lifecycle step rebuilds them.
- `ARCHERY` 912 -> 6,956 triangles; height +2.2 %; 269/269 checks; construction, damaged, really
  damaged and rubble rebuilt along EA's pieces. Awaiting review.
