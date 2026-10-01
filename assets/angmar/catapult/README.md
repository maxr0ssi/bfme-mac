# Angmar catapult works (`AngmarCatapultExpansion`)

Model `KBTrollSlingTo`, mesh `KBTROLLSLINGTOW`, own texture `KBFortressL.tga` (from `KBFortressB.tga`,
DXT5, EA's cut-out alpha kept). Palette A2. New pieces from the army kit
([`../shapes_army.py`](../shapes_army.py)). EA's body is kept whole. EA's facts are in
[`building.py`](building.py).

## Pass 2: the frozen works

The coordinator's review: keep pass 1, and add a pile of ice boulders that reads at RTS.

- **Two frozen timber hoardings** run round the tower's top on the faces the RTS camera sees, between
  EA's blades. Each is a plank gallery on raking struts, with loopholes and a shingled lean-to up to
  the parapet. Rime lines the eaves and icicles hang under them.
- **A frozen timber gantry** stands at the foot on the camera's diagonal: A-frame trestles under a
  heavy rimed beam, two ice boulders hanging from it in iron slings over a heaped crib of big ice
  boulders.
- **The freezing pit** is on the other diagonal: a second pile of ice boulders and beside it a kerb
  of black stone round a grate of cold fire (`coldflame`). It is part of the works, not a torch.
- **More ice ammunition** sits in a crib on the platform, 16 from the troll.

Pass 1 tried a tall two-post hoist, then raking shear-legs. Both read as thin towers at RTS, so the
bold piece moved to the hoardings.

Kept clear: the platform's middle where the troll stands (`AngmarTrollSlingFortress` at (4.4, -0.5,
48.2)), the wall stub (-X) and the Ice Walls skirt (`ICEWALL`).

4,002 triangles (EA 397). Footprint and height unchanged. 1 fire point.

## Status

- [x] healthy body designed (pass 2, shape previews)
- [ ] built in colour, renders reviewed
- [ ] checked in game
