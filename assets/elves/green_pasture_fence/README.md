# Elven green pasture fence (`ElvenGreenPasture`)

Mesh `FENCE` of `EBStable_SKN`, own texture `EBStable_AlphH.tga` (from `EBStable_Alpha.tga`, EA's
cut-out alpha kept, no normal map). `Tier.STANDARD`. Chained on
[`green_pasture`](../green_pasture/README.md); rebuild after it. Model axes (`world_space`), as the stable.

EA's carved branch rails and open filigree gateway stay whole.

## What changed

- **Gate**: a gilt leaf finial on its crown and a small crystal lantern on a gilt rod under it.
- **Corner posts**: gilt collars and leaf finials.
- **Night**: two lights, the lantern's crystal pane and a small free glow card; `always_shown` lets
  them glow at every upgrade level.
- **Banners**: none.

## Kept clear

- The gate's passage; the crown finial's blade stands proud of the gate's face (`footprint_margin = 0.6`).

## Status

Installed with the Elven pack. 1,332 -> 2,210 triangles, height 35.46 -> 39.66 (+11.9 %), 159/159
checks. Construction, really damaged and rubble rebuild the stable and fence together along EA's
pieces; damaged derives both.
