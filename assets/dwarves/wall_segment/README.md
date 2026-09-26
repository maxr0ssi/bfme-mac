# Dwarven wall segment (`DwarvenWallSegmentSmall`)

Model `DBWallN`, redesigned mesh `DBWALLN`, `Tier.STANDARD`, painted from the faction atlas
`DBFortress1` onto its own textures `DBFortressW.tga` / `DBFortressW_NRM.tga` (+ `_D`, `_snow`,
`_U` variants). `DBWallN` is also drawn by the postern gate object (`DwarvenWallPosternGateSmall`,
module `ModuleTag_DrawWall`), so the postern's wall takes this design too.

The fortress's walls on EA's segment. Walls tile and the engine may stretch a segment along its
length, so the ends (y = +-19) are kept as EA's: only runs that continue into the neighbour reach
them (the coping; the chevron slabs, which divide the length evenly), and everything stays inside
EA's footprint (x +-8.3, y +-19). Both faces get the same design (either may face the enemy).

## What changed (body, healthy)

- **Parapet:** on both faces over the rune band, a coping with a bronze drip band and bronze
  chamfer and the fortress's solid `chevron_parapet` (four stepped-triangle slabs per face).
- **Corbel table:** five angular corbels per face under the rune band's overhang, over the bays
  and the relief niche (the fortress's corbels, sized to the 2.0 overhang).
- **Plinth:** a battered plinth along the foot between the end buttresses, flush with their faces
  at the foot; it runs behind the niche and fills its foot.
- **Banners:** a narrow banner (2.6 x 13) in each bay beside the relief niche, hung under the
  corbels. The cloth leaves the body for our house-colour model `DBHCWallN` (the player's colour;
  the rod, piping and rune band stay gold in the body). Its Draw module gets its own tag,
  `ModuleTag_Draw_HCWallN`: see *Framework notes*.
- **Paint:** the faction style (honey granite ashlar, gold-inlaid runes on Erebor-blue enamel in
  EA's rune band, bronze trim).

Footprint unchanged, height 53.0 -> 63.6 (+20.0 %, limit 20 %), 144 -> 720 triangles.
`checks`: 40/40 pass.

## The wall profile (shared with the hub and part 2: gates, postern, towers)

| Line | Value (z) | Where |
|---|---|---|
| walkway | 53.0 | EA's segment top, flat for \|x\| <= 6; the hub's ring is at 53.06 |
| rune band | 44.0 .. 51.1 | EA's, face at \|x\| 8.0 (the hub's painted band: 44.06 .. 51.65) |
| corbel table | 40.6 .. 44.0 | under the band, wall face \|x\| 6.0 -> 7.9 |
| bronze drip band | 50.4 .. 51.9 | 0.3 proud of the band (\|x\| 8.3) |
| coping face | 52.0 .. 56.6 | \|x\| 8.2 (d 1.2 out of the path \|x\| 7.0) |
| coping top | 57.0 | the fortress's `PARAPET` top; bronze chamfer 56.6 .. 57.0 |
| chevron slabs | 56.6 .. 63.6 | `kit.chevron_parapet(..., dz=0)`: slab 56.6-59.4, steps 60.7 / 62.0, point 63.6 |
| plinth | 0 .. 6.3 | foot 2.3 out of the wall face, top 0.8 out at 5.8 |

The chevron parapet is the kit's at `dz = 0`, i.e. exactly the fortress walls' heights; 63.6 is
also exactly EA's height + 20 %, the check's limit for a 53-high model.

## Status (`python3 -m sagekit inventory dwarves/wall_segment`)

| Part | Healthy | Damaged (`DBWallN_D1`) / snow / stonework | Really damaged, collapsing (`_D2`, `_D3`) | Construction (`_A`), placement (`_CUR`) |
|---|---|---|---|---|
| body (`DBWallN`) | done, rendered, not installed | derived: our body on the variant sheets | old (EA's broken bodies, recoloured sheets) | old (EA's own meshes: 128 / 112 triangles) |

## Framework notes

- `Building.new_house_model` gives every house-colour model the same Draw tag
  (`ModuleTag_Draw_HCBanner`) and `formats/ini.add_draw` is idempotent by tag. The postern object
  draws both `DBWallN` and `DBWallPGN`, so the second of `DBHCWallN` / `DBHCWallPGN` to be added
  would be silently skipped there. Worked around here by `HOUSE_DRAW = "ModuleTag_Draw_HCWallN"`.
- Not built: **`DBWallNE`** (`DwarvenWallCliffCap`, the wall end that runs into a cliff). Its
  mesh sits under a bone rotated by the quaternion (-0.5, 0.5, 0.5, -0.5): mesh-local = (-y, z,
  -x) of the world. sagekit works in mesh-local space throughout (the footprint and height
  checks, the sky visibility checks, `face_weights`, and the object-space position / normal bakes
  every paint layer uses: ashlar courses, streaks, ground dirt, moss), so its walls would be
  painted as if lying on their side and its "height" check would limit the wall's thickness while
  the real height could not grow past 53 (no chevron parapet). Needs the pivot's rotation applied
  (or checks and bakes in bone space) before it can be done.
- Not built: `DBWallRmprt` / `DBWallRamp2` (`DwarvenCastleWallHub` / `DwarvenCastleWallSegment`,
  the older castle-wall objects on their own sheet `DBWall.tga`, meshes named `GBWALL*`). No
  command set or fortress reaches them: they only create each other (segment upgrade -> hub ->
  segments); the Dwarven fortress builds the `...Small` objects above.
