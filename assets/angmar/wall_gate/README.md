# Angmar wall gate (`AngmarWallGateSmall`)

Model `KBAngwGN_OP`, mesh `TOWERS` (identity bone), own texture `KBFortressE.tga`. Palette A2. EA's
two pylons kept whole (their great horns curving in over the gateway, EA's spike and emblem) and
the door slab between them untouched. The walls' shared pieces are in [`../shapes_walls.py`](../shapes_walls.py); EA's facts in [`building.py`](building.py).

## Passes 2-3 (the coordinator's reviews: the pass-1 grille hung between the horn tips
like a sign over the opening)

- **A gatehouse lintel**: a heavy stone beam from pylon to pylon just over the door's top
  (z 76.4..86), its rimed top rising to a low point in the middle (pass 3), the walls' merlons
  along its flat runs, icicles under them.
- **The barbed iron portcullis in the opening** (`grille`): one in each mouth of the gateway
  (|x| 6.6, outside the door's slot), raised into the lintel: eleven thick bars, rimed crossbars,
  steel teeth with barbs hanging to z ~59 (units pass under).
- **The Witch-king's sigil on the keystone** (`keystone`, pass 3: the pass-2 box on the lintel read
  blocky): a pointed keystone set into the lintel's middle, 0.4 proud of its faces, its point at
  z 93.4; the sigil inset on both faces at half the pass-2 size (iron kite plate, steel rim, the
  faceless helm with its cold eye-slit, the crown's seven steel tines).
- **Fire**: a cold brazier on each pylon top between the horn and EA's spike (`coldflame`).
- **Frost**: a corbel with icicles under each pylon top, ice drifts on the plinth ledges. No
  merlons (no walk), no new peak, no banners.

1,036 -> 4,288 triangles, height and footprint unchanged, 9/9 preview checks. Review:
`build/assets/angmar/_review/walls_v3.jpg`.

## Kept clear

- The door (`BONE_DOOR 01`) is a slab x -5.5..5.1, |y| < 40.1, z 0..75.8 that sinks into the ground
  to open (`KBAngwGN_OPAN`) and rises to close: nothing new enters its slot (|x| < 5.5) below
  z 76.2 (the lintel's underside at 76.4; the portcullises hang outside the slot).
- The end faces (|y| 68.4) where the segments meet. No Ice Walls mesh; own `KBFortressE_Ice`.

## Status

- [x] healthy body designed (pass 3, shape previews; review `build/assets/angmar/_review/walls_v3.jpg`)
- [ ] reviewed by Max, built in colour, installed
- [ ] checked in game
