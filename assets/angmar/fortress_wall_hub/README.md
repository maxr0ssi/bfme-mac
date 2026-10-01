# Angmar fortress wall hub (`AngmarWallHubSmallExpansion`)

Model `KBHTow`, mesh `HUBTOWER` (identity bone), own texture `KBFortressM.tga`. Palette A2. EA's
expansion hub kept whole: the wall hub's tower (the same mesh in model space) and the stub of wall
to the citadel. The walls' shared pieces are in [`../shapes_walls.py`](../shapes_walls.py); EA's facts in [`building.py`](building.py).

## Pass 1

- The wall hub's dress (`shapes_walls.hub`): merlons on the parapet, icicles under its overhang,
  ice drifts on the diagonal faces, EA's three horns frozen from their tips down, the cold brazier
  in the roof's middle (`coldflame` at (0, 0, 69.2)).
- The stub carries the walls' run: Carn Dum merlons on both top edges (z 44.6), a corbel with
  icicles either side of EA's buttress.

436 -> 2,208 triangles, height 96.1 -> 97.0 (+0.9 %), footprint unchanged, 9/9 preview checks.
`ICEWALL` (0.5 outside the shaft and stub, to z 33) out of the bakes; own `KBFortressM_Ice`.

## Status

- [x] healthy body designed (pass 1, shape previews; review `build/assets/angmar/_review/walls_v1.jpg`)
- [ ] reviewed by Max, built in colour, installed
- [ ] checked in game
