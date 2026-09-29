# Dwarven wall hub (`DwarvenWallHubSmall`)

Model `DBWallRmprtN`, mesh `DBWALLRMPRTN`, own texture `DBFortressR.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.STANDARD`.

EA's hub is a squat hexagonal bastion (corners (+-25.49, 0), (+-12.39, +-22.5); walls to z 51.65,
a chamfer to a ring at 53.06, a slope to a platform at 56.6, a central hexagonal block to 63.2)
where wall segments meet from any side. It gets the fortress's tower crown, at the wall segments'
heights so the parapet line runs on through it. The profile is
[`wall_segment`](../wall_segment/README.md)'s; the coping path is the hexagon moved in by 1.5
(`INSET`), with the coping face on the wall plane.

## What changed

- **Parapet:** a coping round the rim, flush with the walls (a bronze band on the wall's top edge,
  coping face to 56.6, bronze chamfer, top at 57.0) and the fortress's `chevron_parapet` on all six
  sides: the segments' coping top and chevron heights exactly.
- **Corner blocks:** a stepped block on each of the six corners (three tiers on the corner's
  two faces, 0.25 behind the coping face, from 52.9 to 65.4) with a gilded point at 68.0.
- **Crown:** a stepped hexagonal crown on the central block: a battered gold rune belt, a bronze
  step, a tier with the triangle frieze, a plain tier and a gilded point at 75.4.
- **Banners:** four (7 x 22), one on each slanted face, hung under EA's painted rune band
  (z 44.06..51.65) so the band runs on unbroken; cloth in `DBHCWallRmprtN` (Draw tag
  `ModuleTag_Draw_HCWallHub`).

## Kept clear

- Nothing stands out of the hexagon's two faces on the footprint (y = +-22.5) or past its corners.

## Status

Installed with the Dwarven pack. 138 -> 1,316 triangles, height 63.16 -> 75.34 (+19.3 %), 79/79
checks. Construction and damaged derive the new body; really damaged and collapse are rebuilt
along EA's pieces.
