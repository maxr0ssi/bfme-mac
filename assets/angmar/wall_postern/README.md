# Angmar wall postern (`AngmarWallPosternGateSmall`)

Model `KBPostGateN`, mesh `POSTERN GATE` (identity bone), own texture `KBFortressF.tga`. Palette A2.
EA's two gabled porches kept whole (each a pointed arch recess in a stone frame, standing out of
the wall's faces), with EA's ice-crystal sculptures on their blocks. The walls' shared pieces are in [`../shapes_walls.py`](../shapes_walls.py); EA's facts in [`building.py`](building.py).

## Pass 1

- The gate's language in little: a barbed iron portcullis raised in each porch's arch (five bars,
  barbed steel teeth to z 22.8, a riveted beam set into the frame).
- Rime along both slopes of each gable, icicles hanging along the eaves.
- No merlons (no walk), no fire, no banners; EA's crystal sculptures are the ice at its feet, and
  the segment it stands in carries the walk's dress.

422 -> 1,238 triangles, height 43.6 -> 44.0 (+0.7 %), footprint unchanged, 9/9 preview checks.
No Ice Walls mesh; own `KBFortressF_Ice`.

## Status

- [x] healthy body designed (pass 1, shape previews; review `build/assets/angmar/_review/walls_v1.jpg`)
- [ ] reviewed by Max, built in colour, installed
- [ ] checked in game
