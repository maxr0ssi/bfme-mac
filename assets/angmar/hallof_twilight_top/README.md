# Angmar Hall of Twilight, level 1's piece (`TOP_1` of `KBTemple`)

Model `KBTemple`, mesh `TOP_1` (the shrine's roof and its crown of three horns, shown at level 1),
own texture `KBTemplT.tga` (from `KBTemple.tga`). Palette A2. Chained on
[`hallof_twilight`](../hallof_twilight) (`base`); build after it, before
[`hallof_twilight_v1`](../hallof_twilight_v1) and [`hallof_twilight_v2`](../hallof_twilight_v2).

## What changed

- **The crown's three horns frozen at the tips** from z 64 to their points (the walls group's
  `freeze`: an ice casing, a ragged frost line, rime at the point, three crystals growing out), as on
  every other Angmar building. EA's roof and horns stay whole inside. Shared with the other levels:
  [`../hallof_twilight/horns.py`](../hallof_twilight/horns.py).

## Kept clear

- `TOP_1`'s own extent is the tower top (y -28.7..7.4), well inside the Hall's footprint; the front
  horn's casing passes its y min by 1.6, so `footprint_margin = 3.0` (the game's collision comes
  from the INI's geometry, not the mesh).
- Shown per upgrade level: no cloth, no night lights, no fire.

## Status

- [x] designed, built (474 -> 888 triangles, height +3.0 %), checks pass
- [ ] renders reviewed (`build/assets/angmar/_review/hall_levels_v1.jpg`)
- [ ] checked in game
