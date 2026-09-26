# Dwarven wall gate (`DwarvenWallGateSmall`)

Model `DBWallGateN_SKN` (skinned: skeleton `DBWallGateN_SKL`, the door `DOOR` on its own bone),
redesigned mesh `DBWALLGATEN` (rigid, identity pivot), `Tier.STANDARD`, own textures
`DBFortressQ.tga` / `DBFortressQ_NRM.tga` (+ `_D`, `_snow`, `_U`). The door, its bone, the
hierarchy and the animations are EA's, byte for byte.

## The door and the passage

The door (x +-4, y +-40, z 0..45) opens by dropping 42.7 into the ground
(`DBWallGateN_OPN`/`_OP`) and closes by rising again (`_CLS`/`_CL`). It never moves up or sideways.
Everything new is above z 45.6 over the door, or at |x| >= 4.4 beside it. With the gate open,
units walk through |y| <= 20 (the `OpenLeft`/`OpenRight` geometry blocks 20..40): the new
jambs are at |y| >= 33.

## What changed (body, healthy)

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
  wall (4 in all), under the head's flare and above the door relief. The cloth is in
  `DBHCWallGateN_S` (the player's colour).
- **Where the walls meet:** the segments meet the towers' outer faces (y +-58.2). The towers are
  wider (x +-9.2 up to z 71, x +-11.8 at the foot) and taller than the wall's coping (57) and
  chevrons (63.6). Nothing is added on those faces.

Footprint unchanged, height 98.2 -> 113.4 (+15.5 %), 880 -> 3,642 triangles. `checks`: 51/51.

## Status

| Part | Healthy | Construction (`_A`) | Damaged (`_D1`) | Really damaged / collapse (`_D2`, `_D3`, `_D4`) | Snow / stonework |
|---|---|---|---|---|---|
| body (`DBWallGateN_SKN`) | built, rendered, not installed | derived: our body | derived: our body, own `_D` sheet | old (EA's broken bodies) | own `_snow` / `_U` sheets |
| door (`DOOR`) | EA's | EA's | EA's | EA's | EA's |
