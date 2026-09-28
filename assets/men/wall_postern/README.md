# Men wall postern (`MenWallPosternGateSmall`, `ArnorWallPosternGateSmall`)

Model `GBWallPGN`, mesh `GBFDOTOWA01` (the door arch, `ModuleTag_DoorDraw`, drawn over a wall
segment: the object's wall is men/wall_segment's `GBWallN`). Own texture `GBFortressD.tga`.

## Design (2026-09-27)

EA's two deep portals kept whole; each front given the citadel gate's language at the postern's
size: a nine-stone voussoir archivolt with a raised keystone, pilasters with plinths and moulded
capitals at the springing, a portcullis's steel teeth under the crown of the arch, a moulded
coping along the gabled top, pinnacles with steel orbs on the shoulders and the winged-helm crest
on the apex.

The portals' fronts are the footprint's edge (x +-14.17): `footprint_margin = 1.0` lets the
archivolt, pilasters and coping stand up to 0.95 proud (collision is the segment's, from the INI).
No banners. Height 34.59 -> 39.94 (+15.5 %); 136 -> 1,214 triangles; checks 51/51.

## Status

- [x] healthy body designed; renders in `build/assets/men/wall_postern/renders/`
- [ ] Max's review
