# Dwarven hearth (`DwarvenHearth`)

Economy building. Source model `DBHearth`, target mesh `DWARFHEARTH` (660 triangles, one mesh),
painted from its own sheet `DBHearth.tga` (no normal map); new faces are mapped onto the faction
atlas. `Tier.STANDARD`.

## The original (measured, DWARFHEARTH coordinates)

- A star-pointed plate: square +-22.2 at z 0 with chamfered corners and diamond pads (top z 0.5)
  on the four axes, out to +-27.3.
- The fire ring: a square wall 3.1 wide (outer faces +-10.5, inner +-7.4, top z 7.8) round the
  fire bed (z 4.9), sloped panels on its outer faces, sloped buttresses at its corners, and small
  pointed tips (z 9.0) on the two free corners (+,+) and (-,-).
- A gantry running diagonally from pillar (-8, 8) to pillar (8, -8): 2.8-square pillars
  (z 7.7-21.7), capitals (z 24.1-25.5), and a gabled beam whose flat top is z 33.8 for |u| <= 5.1
  (u along (1,-1)/sqrt2), sloping down to the capitals.
- The house-colour banner (`DBHCHearth`) stands at x 12.4..23.9, y -23.8..-12.3: kept clear.

## What changed (body, healthy)

- **Gantry crown:** a rune-banded cornice capping the beam, a triangle-frieze step and a stepped
  gable point above it (the new roofline, z 39.4); stepped shoulder blocks down both slopes of the
  beam, and a stepped bronze-tipped finial over each capital.
- **Fire ring:** a bronze coping on each straight side, with a small stepped-triangle parapet
  (triangle frieze on its outer face) at the middle of each side; stepped pedestals with a bronze
  band round both pillar feet; stepped pyramids with bronze points over the old corner tips.
- **Plate:** a squat three-tier stepped pyramid with a bronze point on each diamond pad.
- The fire bed stays open to the camera; nothing reaches the banner's corner.

Footprint unchanged (new geometry inside +-22.9), height 34.4 -> 40.0 (+16.2 %, limit 20 %),
660 -> 1,332 triangles (about 2x). Every new face checked outward-facing offline.

## Status (`python3 -m sagekit inventory dwarves/hearth`)

**Blocked by a framework bug: not built, no renders, checks not run.** The `geometry` step fails
inside sagekit after `design()` succeeds (564-672 triangles added, bbox and Z growth fine):

```
File "sagekit/blender/layout.py", line 189, in own_layout
    me.uv_layers["UVMap.001"].data.foreach_set("uv", buf)
KeyError: 'bpy_prop_collection[key]: key "UVMap.001" not found'
```

`own_layout` (and `scene.export_w3d`, line 42) assume the importer always creates a second UV
layer `UVMap.001`; for DBHearth (one texture, no normal map) it does not. Both places need an
`if "UVMap.001" in me.uv_layers` guard. Rebuild with `python3 -m sagekit build dwarves/hearth`
once fixed, then review the renders.

| Part | Healthy | Construction | Damaged | Really damaged / rubble | Snow |
|---|---|---|---|---|---|
| body (`DBHearth`) | designed, not built (framework bug) | old | old | old | old |
| banner (`DBHCHearth`) | old | | | | |
