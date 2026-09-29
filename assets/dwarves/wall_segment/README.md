# Dwarven wall segment (`DwarvenWallSegmentSmall`)

Model `DBWallN`, mesh `DBWALLN`, own texture `DBFortressW.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.STANDARD`. The postern (`DwarvenWallPosternGateSmall`) draws `DBWallN`
too, so its wall takes this design. The profile constants in `building.py` are shared by
`wall_end`, `wall_hub`, `wall_tower` and the gates.

## What changed

Both faces get the same design (either may face the enemy).

- **Parapet**: a coping with a bronze drip band and chamfer (top z 57.0) and the fortress's
  `chevron_parapet` (four slabs per face, z 56.6..63.6).
- **Corbel table**: five angular corbels per face under EA's rune band (z 44.0..51.1).
- **Plinth**: battered, along the foot between the end buttresses (to z 6.3).
- **Banners**: four, one in each bay beside the relief niche; cloth in `DBHCWallN` (Draw tag
  `ModuleTag_Draw_HCWallN`, so it does not collide with the postern's own house model).

## Kept clear

- The ends (y +-19): segments tile and may be stretched, so only the coping and the chevron slabs
  reach them. Everything stays inside x +-8.3.

## Status

Installed with the Dwarven pack. 144 -> 720 triangles, height 53.03 -> 63.63 (+20.0 %), 94/94
checks. Construction is rebuilt; damaged and the placement cursor (`DBWallN_CUR`) derive the new
body; really damaged and collapse are rebuilt along EA's pieces.
