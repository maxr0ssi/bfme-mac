# Angmar barracks (`AngmarBarracks`)

Model `KBHall`, mesh `BASE`, own texture `KBHalH.tga` (from `KBHall.tga`, DXT5, EA's cut-out alpha kept).
Palette A2. New pieces from the army kit ([`../shapes_army.py`](../shapes_army.py)). EA's body is kept
whole. EA's facts are in [`building.py`](building.py).

## Pass 2: the thrall-master's gantry

The coordinator's review of pass 1: the gallows on the +X side barely changed the hall at RTS.

- **The gantry** stands across the front, over the way out, as tall as the eaves. At each end is a
  rimed stone plinth and an A-frame of two heavy iron-banded timber legs, with a cross-tie and a knee
  brace. Over them runs one heavy beam, iron-strapped, rimed along its top and hung with icicles.
- **Two great iron cages** hang on chains from iron arms out of the beam's front. Each holds a
  captive frozen inside a column of ice crystals.
- **Cold-fire braziers** (`coldflame`) stand on stone plinths before the A-frames' feet: claws of iron
  prongs out of black stone shards.
- **EA's six roof spikes** are frozen from about 60 % of their height to the point (`freeze`, from
  [`../shapes_walls.py`](../shapes_walls.py), on paths measured from the spikes' own sections).

Pass 1 (superseded): the gallows hung along the +X side with two cages and a fire pit under them.

Kept clear: the porch, the door, the level-2 horns (`V1`: the front pair, the corners) and the
level-3 tower (`V2`). Units pass under the beam and the cages on the way out to the rally point (-Y).
The renders and bakes show level 1 (`bake_hidden`: `V1`, `V2`, `N_WINDOW`).

3,356 triangles (EA 918). Footprint and height unchanged. 2 fire points.

## Status

- [x] healthy body designed (pass 2, shape previews)
- [ ] built in colour, renders reviewed
- [ ] checked in game
