# Angmar wall end (`AngmarWallCliffCap`)

Model `Dwarf`, mesh `DWARF` (identity bone), own texture `KBFortressK.tga`. Palette A2. EA's cliff
cap kept whole: two segments' worth of curtain (y -57..19) 8.5 lower than a segment, its foot
carried down into the cliff, ribs and horn pairs at y 0 and -38. The walls' shared pieces are in [`../shapes_walls.py`](../shapes_walls.py); EA's facts in [`building.py`](building.py).

## Pass 1

The segment's dress along the whole run (`shapes_walls.run`): Carn Dum merlons on both top edges
(the joint at y 19 keeps a segment's beat), a corbel with icicles between the ribs, ice drifts up
the foot in the four bays. No peak, fire or banners.

1,099 -> 2,611 triangles, height and footprint unchanged, 9/9 preview checks. `ICEWALL` (to
z -43.9..33) out of the bakes; own `KBFortressK_Ice`.

## Status

- [x] healthy body designed (pass 1, shape previews; review `build/assets/angmar/_review/walls_v1.jpg`)
- [ ] reviewed by Max, built in colour, installed
- [ ] checked in game
