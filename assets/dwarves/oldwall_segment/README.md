# Dwarven castle-wall segment (`DwarvenCastleWallSegment`)

Model `DBWallRamp2`, mesh `GBWALLRAMP2`, own texture `DBWalS.tga` (no normal map), painted from the
faction atlas `DBFortress1.tga`. `Tier.STANDARD`. EA's sheet `DBWall.tga` is a placeholder that
reads "Dwarven Wall", so `wall.clear_target` removes EA's faces and every volume is rebuilt.
Players do not build the old castle walls; map makers placed them (Erebor, Withered Heath,
Fornost, Helm's Deep).

## What changed

- **Wall section** ([`wall.py`](wall.py), shared with `oldwall_gate`'s stubs): the new walls'
  profile at the old section's size: battered plinth, three-step corbels, the rune band, a bronze
  drip band, the coping (top z 57.0) and the chevron parapet (z 56.6..63.6).
- **Faces**: a dwarf-statue pilaster in the middle and a banner in each bay.
- **Ramps**: a Dwarven stair down each (18 treads, stepped newels with gilded points).
- **Banners**: four, cloth in `DBHCWallRamp2`.
- [`upgrade.py`](upgrade.py) builds `oldwall_postern`, `oldwall_tower` and `oldwall_trebuchet`
  on the same section.

## Kept clear

- EA's footprint (x +-28.1, y +-62.93), the ends and the walkway (z 51.91).

## Status

Installed with the Dwarven pack. 106 -> 1,432 triangles, height 111.52 -> 111.20 (-0.3 %), 32/32
checks. The object has no other condition states and no `_A`/`_D*` models.
