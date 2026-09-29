# Men keep (`GondorKeep`, the battle tower)

Model `GBBtlTwrs`, mesh `OBJ0`, own sheet `GBBtlTwH.tga` (+ `_NRM`, `_D`, `_snow`). `Tier.STANDARD`.
EA's tower stays whole (shaft, pilasters, lancets, painted statue niches, frieze, ribbed dome,
porch). The crown, `tower.py`, is shared with the [sentry tower](../sentry_tower/README.md).

## What changed

- **Crown**: corbels under the frieze, a black band of silver stars, square merlons, a pinnacle
  over each fold, six corbelled bartizans with slate spirelets on the pilasters.
- **Dome**: slate, as on the citadel (its sheet panel is hinted as tiles, `DOME_TILES`, so it does
  not recolour to white stone); six steel ribs, a lantern cupola, gilt orb and steel spike.
- **Shaft**: sills, colonnettes and pointed hoods with gilt knobs on the 12 lancets; string courses
  at 27.6, 59.8 and 80.9; plinth blocks at the pilasters' feet.
- **Porch**: a voussoir archivolt, a black tympanum with the White Tree, raking cornices, a
  winged-helm crest, buttress piers with pinnacles.
- **Banners**: two, flanking the porch; cloth in `GBHCBtlTwrS`. White Tree shields on the other
  four pilasters.

## Kept clear

- EA's statue niches (every fold, z 30..46.6) and `N_WINDOW` night panes (z 63.25..78.03).

## Status

Installed with the Men pack. 1,022 -> 8,177 triangles, height 115.7 -> 133.7 (+15.5 %), 86/86
checks. Construction, really damaged and rubble are rebuilt; damaged is derived.

## Known limits

- In the `_D` sheet variant the dome panels' edges are lighter than in the healthy model (EA's
  damaged sheet is carried over as a ratio).
