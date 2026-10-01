# Angmar wall tower (`AngmarWallTowerSmall`)

Model `KBArrwWal`, mesh `ARROWTOWER` (identity bone), own texture `KBFortressG.tga`. Palette A2.
EA's arrow tower kept whole: the barrel on the wall line, the flared parapet, the pointed keep
with its three horns gathered into a crown to z 111.6. The walls' shared pieces are in [`../shapes_walls.py`](../shapes_walls.py); EA's facts in [`building.py`](building.py).

## Pass 1

- **Peak**: EA's three horns frozen from z 95 to their points (`freeze`): the citadel tines'
  frozen tips on the crown EA already gave the tower, no new spike.
- **Fire**: two sorcerers' cold braziers on the walk round the keep, between EA's arrow bones
  (`coldflame`).
- **Battlement and ice**: Carn Dum merlons round the parapet's top (none at EA's three hooks),
  icicles under the parapet's flare, ice drifts up the barrel's foot on the diagonals.

1,287 -> 2,735 triangles, height 111.7 -> 112.8 (+1.0 %), footprint unchanged, 9/9 preview
checks. EA's body carries six loose vertices: `design()` drops them (the Men forge's
`drop_loose`). Kept clear: the arrow bones (r 8.6, z 67), the wall's run through the tower. No
Ice Walls mesh; own `KBFortressG_Ice`.

## Status

- [x] healthy body designed (pass 1, shape previews; review `build/assets/angmar/_review/walls_v1.jpg`)
- [ ] reviewed by Max, built in colour, installed
- [ ] checked in game
