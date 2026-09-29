# Dwarven archery range, level 3 tower (`V2` of `DBArchRnge_SKN`)

Model `DBArchRnge_SKN`, mesh `V2` (shown at `Upgrade_StructureLevel3`), own texture `DBArchRngT.tga`
(from `dbarchrnge.tga`). `Tier.STANDARD`. Chained on `dwarves/archery_range`; rebuild after it, and
rebuild `archery_walls` after this.

## What changed

EA's V2 is a timber storey on four legs under a shingle spire; it now matches the stone range below.

- **Piers**: each leg rises out of the range's post bastion inside a stone pier with two rune belts.
- **Storey course**: a stepped soffit, hexagon frieze and bronze coping from z 76.2, above the
  range's crown finials.
- **Storey walls**: stone over EA's timber, a pointed arrow slit with a stepped frame at each
  pair of arrow bones on the east, north and south faces.
- **Crown**: a corbelled cornice under a rune-belted ring, step pyramids on the corners, the
  range's crown gable mid-side.
- **Spire**: six stone tiers over EA's pyramid, a bronze collar and a gilded point (z 146.5).
- **Banners**: three, between the slits; the cloth stays in `V2` in the palette's blue
  (`house_tags = ()`), since the house model is drawn at every level.

## Kept clear

- The arrow bones `ARROW_01..12`: nothing new in front of them.
- V2's ladder (y 40.6-49.7) on the plain west face; the NW pier does not grow toward it.

## Status

Installed with the Dwarven pack. 576 -> 2,249 triangles, height 110.10 -> 119.92 (+8.9 %),
266/266 checks. Damaged derives the new body; construction, really damaged and rubble are rebuilt
along EA's pieces.
