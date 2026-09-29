# Men farm, level 2 (`V1` of `GBFarm_SKN`)

Chained on `men/farm` ([`levels.py`](../levels.py)). Own texture `GBFarW` (GBFarm's copy;
the damaged state's `GBVetD` gets `GWVetD`, `prodkit.same_length_variants`).

## What changed

EA's V1 is a thick low stone wall round the yard, a timber palisade of sawtooth stakes along its
middle, tall posts at the corners and an arched gate in the west wall. Kept, and:

- **Gate**: a voussoir archivolt with a raised keystone on both faces; over it a stone pediment
  with the White Tree on a sable field (both faces), raking cornices, a pinnacle on the apex and
  one on each gate pier.
- **Piers**: dressed stone piers against the wall's outer faces (four on the long walls, two on
  the short ones), moulded caps, steel-ringed stone balls.
- **Props colour**: the palisade stakes and corner posts keep EA's timber colours
  (`prodkit.props_layer` with `rects`: EA's plank and post UV rectangles on GBFarm; a colour
  rule alone misses the grey-brown stakes and turns them white).

## Kept clear

- The piers stand 1.05 out of the wall's faces with their finials (`footprint_margin` 1.1: the
  wall's collision is the building's); every face kept (`prodkit.closed`).

## Status

Installed with the Men pack. `V1` 666 -> 2,814 triangles, height 29.7 -> 33.1 (+11.3 %),
120/120 checks. Construction and the world-builder model carry V1; damaged, really damaged and
rubble have no body pieces of ours and stay EA's.
