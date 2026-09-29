# Dwarven castle-wall gate (`DwarvenCastleWallGate`)

Model `DBWallGate`, mesh `GBWALLGATE`, own texture `DBWalG.tga` (no normal map), painted from the
faction atlas `DBFortress1.tga`. `Tier.STANDARD`. EA's sheet `DBWall.tga` is a placeholder; no face
samples it (see [oldwall_segment](../oldwall_segment/README.md)).

## What changed

EA's stand-in (no door, no bones but its own, the passage open to the sky): two gatehouse blocks
(|y| 53.4 .. 98.39, x +-33.13, chamfered to +-23.77 at the wall end, an upper storey overhanging
to +-37.21, roofs ramping down to the walkway) and a wall stub at each end (|y| 98.39 .. 136.89,
the castle-wall section with its walkway at 51.78). Rebuilt as an Erebor gatehouse after the new
wall gate:

- **Gatehouse:** the towers and a bridge over the passage (from z 45.96, the top of EA's
  opening) under one projecting head round the fronts and chamfers: three-step corbels, a rune
  band with Erebor-blue enamel (60 .. 66), a bronze drip band, the coping and chevron merlons.
- **Arch:** a stepped pointed arch on both faces (two rings with the triangle frieze and bronze
  reveals, then a frame), springing at 42.8 from the towers' inner faces; a rune lintel and a
  stepped relief in the tympanum.
- **Roof:** stepped pyramids with gilded points on the four outer corners, a stepped rune roof
  on each tower, the gate's stepped crown over the passage (gilded point 85.3), two banner poles.
- **Banners:** a long banner (8 x 28) down each tower face and the two poles; cloth in
  `DBHCWallGate` (Draw tag `ModuleTag_Draw_DBHCWallGate`).
- **Wall stubs:** the segment's section (`oldwall_segment/wall.py`) at walkway 51.78, so their
  ends meet the castle-wall segment's lines.

## Kept clear

- The passage: nothing new in |y| < 53.4 below z 42.8; the arch opening contains EA's (sloped
  soffit included).

## Status

Installed with the Dwarven pack. 210 -> 4,946 triangles, height 71.30 -> 85.35 (+19.7 %), 32/32
checks. The object has no other condition states and no `_A`/`_D*` models.
