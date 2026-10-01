# Angmar wall segment (`AngmarWallSegmentSmall`, `AngmarWallPosternGateSmall`)

Model `KBWallN`, mesh `KBWALL01` (identity bone), own texture `KBFortressD.tga`. Palette A2. EA's
body kept whole (the faces, the walk's channels, the middle rib with its curved horn pair). The walls' shared pieces are in [`../shapes_walls.py`](../shapes_walls.py); EA's facts in [`building.py`](building.py).

## Pass 1

- **Battlement**: six Carn Dum merlons a face (stone teeth rising to an off-centre point, left and
  right in turn, the slopes rimed), at the walls' common pitch (5.4), a half pitch in from each end,
  none over EA's rib.
- **Icicles under the walk**: a corbelled string course just under the top on both faces, a rime
  crust along its front and icicles under it.
- **Ice at the feet**: a drift of crystals up the foot in each bay, leaning along the face, a black
  stone shard among them.
- No peak, fire or banners: segments repeat many times (the hubs, tower and gate carry those).

380 -> 1,160 triangles, height unchanged (81.9), footprint unchanged, 9/9 preview checks.

## Kept clear

- The ends (y +-19) and EA's footprint (x -10.47..10.34): neighbours, hubs and the gate meet it, a
  stretched segment still joins.
- The Ice Walls shell (`ICEWALL`, |x| 8.85 to z 33): the crystals stand between it and the
  footprint, their feet through it as EA's rib is; out of the bakes (`bake_hidden`). The Ice Walls
  sheet gets our own copy (`KBFortressD_Ice`).

## Status

- [x] healthy body designed (pass 1, shape previews; review `build/assets/angmar/_review/walls_v1.jpg`)
- [ ] reviewed by Max, built in colour, installed
- [ ] checked in game
