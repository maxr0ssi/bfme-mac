# Mordor troll cage (`MordorTrollCage`)

Model `MBTrollPit_SKN`, mesh `MBTROLLPIT`, own texture `MBTrollPiH.tga` (from `MBTrollPit.tga`). `world_space`: the body's bone is moved (-18.5, -2.1, 0.2). New pieces come from the Mordor kit ([`shapes.py`](../shapes.py) and its mixins) and the production group's modules [`shapes_production.py`](../shapes_production.py) (the claw spike, shelves, pits, the saw, the catapult, claw bars) and [`shapes_production_big.py`](../shapes_production_big.py) (grounded clawed stacks, the siege tower, the smoke rack, the log ramp). EA's body is kept whole; EA's facts are in [`building.py`](building.py).

## Pass 2: the iron claw

Pass 1 (`_review/production_v1.jpg`) put fire bowls on roofs; the coordinator's review: a bowl perched on a roof reads as a small egg stuck on (the citadel's pass 5 lesson), and the buildings were too subtle at rts. Pass 2 (`_review/production_v2.jpg`) grounds every fire and gives each building one bold mass.

- **Claw**: eleven heavy hooked iron bars rise from inside the palisade (r 27 round the pen's middle (-27, -2)), up its inner face and in over the troll to steel points at z 54..59, two barbs each, chained to a spiked iron boss hanging at z 52 (the troll stands to z 37).
- **Fire**: a fire pit in the pen's west end (-43, -2), clear of the troll, burns under the claw (`forge`, `plume`). Pass 1's roof bowl is gone: one claw is enough.
- **Roof**: steel spikes along the roof's -Y edge over the great door.
- **Lava**: an open lava channel round the pen's south-west foot (`embers`, `smoke`); fire baskets (`brazier`) either side of the door.
- Kept clear: the door (troll_cage_02, x 16..51, animated) and the trolls' way out to (34, -45); the troll's chains (troll_cage_module_tag_03); the level 3 banners (V2).

Fire: 6 points (1 forge, 1 plume, 1 embers, 1 smoke, 2 brazier), the game's own particle systems on the rig's bones (`fire_points`, from the design's log). No green: orange fire and lava only.

## Status

- [x] healthy body designed (pass 2, 2026-09-30), preview checks pass
- [ ] Max's review: `build/assets/mordor/_review/production_v2.jpg`
- [ ] colour build, lifecycle and night checks (after EA's sheet is recoloured)
