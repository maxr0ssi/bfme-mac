# Men stoneworks (`GondorStoneMaker`, `ArnorStoneMaker`)

Draft for review, not installed. Renders: `build/assets/men/stone_maker/renders/compare_*.png`.

## What changed

EA's quarry tower is kept whole (battered base, open crane stage between four diagonal corner
fins, top storey, treadwheel annex, stone pile, guild flag). The crane turns a platform of
radius about 17.5 from z 75.8 and its arm sweeps the north-west from 78.5 (GBStoneMK_IDLA, all
310 frames), so nothing rises above the rim; the second pass (the lead: too close to EA) enriches
the shaft and base instead:

- **Fins as pilasters**: long-and-short quoins up the four corner fins' end faces from the
  stage's foot (38.4) to where they step in (57.6), and a moulded two-step cap there.
- **Arches**: a pointed archivolt of wedge stones with a keystone round each of the stage's four
  openings, colonnettes with capitals up the jambs.
- **Bands**: a machicolation at the base's top (corbels, a sable slab with gilt stars, z
  24.2..28.2) on the south, east and west faces; the star frieze at the stage's foot; corbels
  and a star band under the top storey's rim.
- **Base**: battered buttresses with weathered tops either side of each window, window
  pediments, sills on corbels, a battered plinth.
- **Yard**: a low wall with a moulded coping and square posts with pyramid caps along the
  stone yard's east edge (outside the hooks' and the stones' reach); merlons on the annex.
- **Banner**: one house-colour banner on the top storey's south face (cap 1).
- EA's planks and red guild flag keep their colours (`prodkit.props_layer`).

## Fit and status

- `GBSTONEMK` 1,298 -> 8,586 triangles; height EA's; 214/214 checks. The south buttresses'
  feet stand 0.72 past EA's fins (`footprint_margin` 0.8: the collision is the INI's).
- The tower is hollow and open at its stage, so every face of the new pieces is kept
  (`prodkit.closed`): the sky check sees buried backs from inside.
- Construction rebuilt along EA's pieces; the damaged, really damaged and rubble models have no
  body pieces of ours and stay EA's (recoloured by the faction sheets).
- Own texture `GBstoneMkH` (no normal map on EA's sheet).
