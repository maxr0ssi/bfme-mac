# Elven wall end (`ElvenWallCliffCap`)

Model `EBWallNE`, redesigned mesh `EBWALLN`, `Tier.STANDARD`, painted from `EBFortress.tga` onto its
own textures `EBFortresE.tga` / `EBFortresE_NRM.tga` (+ `_D`, `_snow`, `_U` variants), DXT5 (EA's
cut-out alpha kept).

EA's cliff cap is two wall segments end to end (four lancet bays per face) with the faces carried
on below the ground to z -51.2 for the falling ground at a cliff's foot; the far end is cut plain.
`EBWALLN` hangs under a bone turned 180 degrees about z, so the design works in mesh coordinates
(z is still up; `world_space` is not needed): y -19..57, the joint with a segment at y = -19, the
cut end at y = 57 (model space: the joint at +19, the cut at -57).

## What changed (body, healthy)

- **Crown:** the segments' crown the whole length (the shared profile,
  [wall_segment/README.md](../wall_segment/README.md)); at the joint it ends exactly as a segment's
  does, so the parapet line runs straight on; the merlons run from the joint into the turret.
- **Windows and banners:** the segments' arch frames and a leaf banner in each of the eight windows
  (cloth to our house-colour model `EBHCWallNE`, Draw tag `ModuleTag_Draw_HCWallEnd`).
- **Turret at the cut end:** a pale stone lantern-house on the crown over the end pier (x +-4.2,
  y 48.4..56.7, z 52.9..58.6) with a silver string course, a lancet window of EA's lattice glass in
  a silver arch frame on each open face, and a square swept slate roof with upturned eaves and a
  gilt leaf finial (eaves corners at x +-4.45, y 57.0: inside the footprint).
- Nothing below the ground changes.

Footprint unchanged, height 102.4 -> 120.35 (+17.5 %, limit 20 %), 1,227 -> 7,178 triangles (96
cloth faces moved to `EBHCWallNE`). `checks`: 79/79 pass.

## Status (`python3 -m sagekit inventory elves/wall_end`)

| Part | Healthy | Construction (`_A`) / damaged (`_D1`) / snow / stonework | Really damaged, collapsing (`_D2`, `_D3`) |
|---|---|---|---|
| body (`EBWallNE`) | done, rendered, not installed | derived: our body | rebuilt by the lifecycle step around our body |

## Night lights

TODO, as the segment: no night meshes or `NightWindowName` in EA's cliff cap; the turret's
windows are the place for starlight once it has one.
