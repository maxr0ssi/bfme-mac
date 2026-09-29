# Dwarven wall trebuchet bastion (`DwarvenWallCatapultSmall`)

Model `DBWallTrebN`, mesh `DBWALLTREBN`, own texture `DBFortressJ.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.STANDARD`. `P1` (the flat platform card under the floor) is untouched and
left out of the bakes. The trebuchet itself is a separate object that stands on the round platform.

## What changed

- **Rim:** chevron merlons (stepped-triangle tops, bronze step) sit on the rim's outer 2.4. There
  are two on each angled face and one on each wall face, clear of the join. Each prow tip has a
  stepped pyramid with a gilded point.
- **Wall joins:** the wall runs along Y and meets the wall faces (y +-22.5) at x +-8.3. Over each
  join there is a pier on the rim, within y 19.0..22.5 (the platform ends at 18.7). It has a
  hexagon-frieze block, a bronze cornice, a triangle-frieze tier and a stone point at z 63.4. It
  takes the wall segment's coping (to 57) and chevrons (to 63.6) instead of leaving them to end in
  the air over the rim (53.1).
- **Banners:** eight, a pair on each of the four angled faces either side of EA's relief panel, hung under the
  band; cloth in `DBHCWallTrebN`.
- EA's carved panels, the triangle-frieze band and the prow emblems are kept.

## Kept clear

- The platform (z 50.1): nothing enters it, so the trebuchet keeps its floor.

## Status

Installed with the Dwarven pack. 288 -> 1,324 triangles, height 53.00 -> 63.34 (+19.5 %), 86/86
checks. Construction and damaged derive the new body; really damaged and rubble are rebuilt along
EA's pieces.

## Known limits

- Not verified: the trebuchet's swing against the merlons (6 above the rim) and the piers (10.3),
  both on the rim's outer edge.
