# Dwarven wall tower (`DwarvenWallTowerSmall`)

Model `DBWallTwrN`, mesh `DBWALLTWRN`, own texture `DBFortressV.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.STANDARD`. The model's second mesh `DBWALLN` (EA's wall piece through the
tower, 128 triangles, not the wall segment's model) is untouched and keeps EA's recoloured sheet.

`crown.py` holds the crown pieces the wall's towers and gates share (`step_pyramid` at any scale,
`ziggurat`, `chevron`, `band`); `wall_gate`, `wall_postern` and `wall_trebuchet` import it.

## What changed

- **Crown:** the fortress's battered crown ring (dz -8.4) on the bronze shield panels, a stepped
  pyramid (0.7 scale, gilded point) on each corner post, a chevron merlon over the middle of
  each side.
- **Roof:** a stepped roof over EA's stone pyramid: rune tier, bronze cornice, triangle-frieze
  tier, bronze cornice, stone tier, gilded point (the new top, z 124.4). Every tier stays outside
  the pyramid under it.
- **Shaft:** a rune belt at the walkway (z 49.4..53.4); a battered plinth with a string course on
  the two faces that look out of the wall (+-X).
- **Banners:** four, two on each outward face either side of EA's carved window, hung free under
  the head's V-shaped corbel; cloth in `DBHCWallTwrN`.
- **Where the walls meet:** the wall segment's coping and chevron parapet run along EA's wall piece
  on both faces out to this mesh's footprint (|y| 18.03), imported from `wall_segment/building.py`
  so the two cannot drift apart.

## Kept clear

- The archer notches under the ring and the arrow bones (`ARROW_01..08`, z 93.6).
- The footprint check stops this mesh at |y| 18.03, so the last 1.0 before each neighbour is EA's
  piece without a parapet.

## Status

Installed with the Dwarven pack. 472 -> 1,670 triangles, height 117.48 -> 124.40 (+5.9 %), 86/86
checks. Construction and damaged derive the new body; really damaged and collapse are rebuilt
along EA's pieces.
