# Men wall postern (`MenWallPosternGateSmall`, `ArnorWallPosternGateSmall`)

Model `GBWallPGN`, mesh `GBFDOTOWA01` (the door arch, `ModuleTag_DoorDraw`, drawn over a wall
segment: the object's wall is [`wall_segment`](../wall_segment/README.md)'s `GBWallN`). Own
texture `GBFortressD.tga` (from `GBFortress1.tga`). EA's two deep portals kept whole.

## What changed

- **Each front**, in the citadel gate's language at the postern's size: a nine-stone voussoir
  archivolt with a raised keystone, pilasters with plinths and moulded capitals at the springing,
  a portcullis's steel teeth under the crown of the arch.
- **Top**: a moulded coping along the gable, pinnacles with steel orbs on the shoulders, the
  winged-helm crest on the apex.
- **Banners**: none.

## Kept clear

- The portals' fronts are the footprint's edge (x +-14.17): `footprint_margin = 1.0` lets the
  archivolt, pilasters and coping stand up to 0.95 proud (collision is the segment's, from the INI).

## Status

Installed with the Men pack. 136 -> 1,214 triangles, height 34.6 -> 39.9 (+15.5 %), 51/51 checks.
Damaged, really damaged and the collapse are derived from the new body.
