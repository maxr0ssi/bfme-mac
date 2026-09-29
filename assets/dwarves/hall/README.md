# Dwarven fortress hall expansion (`DwarvenHallExpansion`)

Model `DBFGBunk`, mesh `DBFGBUNK`, own texture `DBFortressG.tga` (from the faction atlas
`DBFortress1.tga`; the fortress owns `DBFortressH`). `Tier.STANDARD`.

## What changed

- **Crown:** the fortress's tower crown lowered onto the hall's head (top 85.1): a battered crown
  ring with a bronze step, stepped-pyramid corner blocks and a stepped gable in the middle of each
  side, so the hall reads as one of the fortress's towers from the RTS camera.
- **Roof:** a battered stepped ziggurat over the old carved pyramid: rune belt, bronze step, a
  tier with the gold triangle frieze, a plain tier and a squat gilded point (top 104.5).
- **Door:** a pointed stepped frame round the door recess: two rings with the triangle frieze and
  bronze reveals, then a frame slab with a flat lintel, all in the 0.8 units between the door slab
  and the head's front (the bounding box). The opening itself is untouched.
- **Flanks:** a rune panel between bronze bands, with a small stepped triangle over it, on each
  side of the tower above the stepped slabs; battered plinths at the foot of the side slabs,
  either side of the low cross buttress.
- **Banners**: four, as [`erebor_tower`](../erebor_tower/README.md)'s (z 42.5..61.4); cloth in
  `DBHCFGBunk`.

## Kept clear

- The low connecting wall on the -X side (x -55..-27, facing the fortress) and the footprint.
- The eight `ARROW_*` bones fire from the head's windows (z 80.3); the crown starts at 85.1.
- `ENTERBONE` at the door foot (-2, 0, 0); the medallion over the door and the flank rune panels.

## Status

Installed with the Dwarven pack. 379 -> 1,441 triangles, height 93.97 -> 104.55 (+11.2 %), 85/85
checks. Construction, really damaged and rubble are rebuilt along EA's pieces; damaged draws the
body on its own `_D` sheet.
