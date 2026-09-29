# Dwarven catapult tower fortress expansion (`DwarvenCatapultExpansion`)

Model `DBFCTower`, mesh `DBFCTOWER`, own texture `DBFortressC.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.STANDARD`. The untextured `P1` plane (the catapult's platform, at the
`P1` bone) is left out of bakes and renders (`bake_hidden`); it is not touched.

## What changed

- **Parapet:** the fortress walls' solid chevron parapet round the rim (both sides and the prow):
  a coping with a bronze band on angular corbels, then slabs with stepped-triangle tops (the
  fortress's `chevron_parapet`, lowered onto a shorter coping so the height stays in budget).
- **Rune frieze:** a gold rune band with bronze edges along both side walls, under EA's triangle
  frieze and above the carved panels.
- **Banners:** six (6.5 x 17), hung from under the parapet's corbels (z 31.3..49.1): one on each
  prow face, over the point of its carved niche and clear of the corner shield; two on each side
  wall, between the carved niches. Cloth in `DBHCFCTower`.

## Kept clear

- The catapult's platform (floor z 50.0, x -37.8..8.6, |y| 18.7): everything new sits on the
  outer 2.2 of the 3.8-thick rim or on the outer walls.
- The plain -X wall (x -41.5, against the fortress) keeps its rim as it is.

## Status

Installed with the Dwarven pack. 242 -> 1,194 triangles, height 53.00 -> 61.80 (+16.6 %), 92/92
checks. Construction, really damaged and rubble are rebuilt along EA's pieces; damaged draws the
body on its own `_D` sheet.

## Known limits

- The platform floor's gold disc picks up the style's grime layers (dark blotches from the RTS
  camera); that comes from the paint stack, not this recipe.
