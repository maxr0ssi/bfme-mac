# Angmar Hall of Twilight (`AngmarHallofTwilight`)

Model `KBTemple`, mesh `BASE`, own texture `KBTemplH.tga` (from `KBTemple.tga`). Palette A2. New
pieces from the army kit ([`../shapes_army.py`](../shapes_army.py)). EA's body is kept whole. EA's
facts are in [`building.py`](building.py).

## Pass 2: the sorcerers' ring

The coordinator's review of pass 1: the altar was lost at RTS and the stones were thin.

- **Five broad menhirs** (13 across, 9.5 deep, 34 to 39 tall) stand round the dais's rim on the
  ground. Each leans a little out, its top cut on a slant and rimed, with one great rune glowing down
  its outer face and ice crystals at its foot.
- **The altar** stands on the dais before the shrine, front-right toward the RTS camera. It has a broad
  step of dressed stone, a black stone block with three columns of cold runes, and a rimed top slab
  with a crater of ice and black stone shards.
- **Cold fire** burns out of the crater (`coldfire`).
- **EA's tower horns are not frozen.** They belong to the level pieces, not to `BASE`: `TOP_1` (level
  1, points at z 78.7), `V1` (level 2, z 83.1) and `V2` (level 3, z 88.2). The horns stand at the
  same places but rise 4.4 higher at each level, so one casing on `BASE` would sit right on one level
  only and cut through the horn on the other two. Freezing them needs a recipe per level piece (only
  `hallof_twilight_v1` exists).

Pass 1 (superseded): five rune stones 6.4 across and 3.4 deep.

`BASE` shows at every level, so all of it stands clear of every level piece: `TOP_1` and `ROCKS_1`
(level 1), `V1` (level 2, its own stub [`../hallof_twilight_v1`](../hallof_twilight_v1), left EA's),
and `V2` and its rune glow (level 3). V1's and V2's great horns spring from the dais's sides, and
their clumps reach in at the front corners and the back. The menhirs' corners keep 1.8 to 3.9 clear
of them below z 44. The front ramp (the way out) stays clear. The renders and bakes show level 1
(`bake_hidden`: `V1`, `V2`, `RUNEGLOWV2`, `N_WINDOW`).

2,099 triangles (EA 784). Footprint and height unchanged. 1 fire point.

## Status

- [x] healthy body designed (pass 2, shape previews)
- [ ] built in colour, renders reviewed
- [ ] checked in game
