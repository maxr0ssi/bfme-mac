# Men stoneworks (`GondorStoneMaker`, `ArnorStoneMaker`)

Model `GBStoneMK_SKN`, mesh `GBSTONEMK`, own texture `GBstoneMkH.tga` (from `GBstoneMk1.tga`, no
normal map). EA's quarry tower kept whole (battered base, open crane stage between four corner
fins, top storey, treadwheel annex, stone pile, guild flag); the new work is on shaft and base.

## What changed

- **Fins as pilasters**: long-and-short quoins up the fins' end faces (z 38.4..57.6), a two-step cap.
- **Arches**: a pointed archivolt with a keystone round each stage opening, colonnettes up the jambs.
- **Bands**: a machicolation with a sable star slab at the base's top (z 24.2..28.2, south, east,
  west); the star frieze at the stage's foot; corbels and a star band under the top storey.
- **Base**: battered buttresses beside each window, window pediments, sills on corbels, a plinth.
- **Yard**: a low coped wall with capped posts on the east edge; merlons on the annex. EA's planks
  and red guild flag keep their colours.
- **Banners**: one, on the top storey's south face; cloth in `GBHCstoneMk`.

## Kept clear

- The crane's sweep (`GBStoneMK_IDLA`, 310 frames): radius about 17.5 from z 75.8, the arm from
  78.5 to the north-west. Nothing rises above the rim; the yard wall is outside the hooks' reach.

## Status

Installed with the Men pack. 1,298 -> 8,586 triangles, height unchanged, 214/214 checks,
`footprint_margin = 0.8` (the south buttresses' feet stand 0.72 past EA's fins). The stage is open,
so every face of the new pieces is kept (`prodkit.closed`). Construction is rebuilt; damaged,
really damaged and rubble have no body pieces of ours and stay EA's (recoloured).
