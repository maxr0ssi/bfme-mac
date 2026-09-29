# Dwarven wall gate (`DwarvenWallGateSmall`)

Model `DBWallGateN_SKN` (skinned: skeleton `DBWallGateN_SKL`, the door `DOOR` on its own bone),
mesh `DBWALLGATEN` (rigid, identity pivot), own texture `DBFortressQ.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.STANDARD`. The door, its bone, the hierarchy and the animations are EA's,
byte for byte.

## What changed

- **Gatehouse:** a bridge block between the towers over the door (x +-9.2, z 45.6..66). On both
  faces is a deep stepped pointed arch: two recessed rings with the triangle frieze and bronze
  reveals, then a frame out to the towers. Stone jamb blocks run back to the door groove.
- **Tympanum:** inside the arch, a rune lintel (Erebor-blue enamel, gold runes) over the door and
  a stepped relief over it (stone tier, triangle-frieze tier, bronze tier, stone point).
- **Top:** a hexagon cornice over the arch frame, three chevron merlons on each side, and the
  gate's crown in the middle (rune tier, bronze cornice, triangle tier, hexagon tier, gilded
  point, z 89). Two banner poles stand on the walkway either side of the crown.
- **Towers:** the same crown as the wall tower: a battered crown ring on the head rim, stepped
  pyramids on the corners, a chevron merlon on each side, and a stepped roof with a gilded point
  over EA's timber roof (z 113.4). A long banner hangs on each tower face that looks out of the
  wall (4 in all), under the head's flare and above the door relief.
- **Banners:** the four tower banners and the two poles; cloth in `DBHCWallGateN_S`.

## Kept clear

- The door (x +-4, y +-40, z 0..45) drops 42.7 into the ground to open and rises to close; it
  never moves up or sideways. Everything new is above z 45.6 over the door, or at |x| >= 4.4 beside it.
- With the gate open, units walk through |y| <= 20 (`OpenLeft`/`OpenRight` block 20..40); the new
  jambs are at |y| >= 33.
- Where the walls meet (y +-58.2): the towers are wider and taller than the wall's coping (57)
  and chevrons (63.6); nothing is added on those faces.

## Status

Installed with the Dwarven pack. 880 -> 3,642 triangles, height 98.25 -> 113.47 (+15.5 %), 98/98
checks. Construction and damaged derive the new body; really damaged and collapse are rebuilt
along EA's pieces. The door is EA's in every state.
