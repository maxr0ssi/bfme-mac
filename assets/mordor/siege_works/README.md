# Mordor siege works (`MordorSiegeWorks`)

Model `MBSeigeWork`, mesh `SEIGEWORK2`, own texture `MBSeigeWorkH.tga` (from `MBSeigeWork2.tga`, cut-out alpha). New pieces come from the Mordor kit ([`shapes.py`](../shapes.py) and its mixins) and the production group's modules [`shapes_production.py`](../shapes_production.py) (the claw spike, shelves, pits, the saw, the catapult, claw bars) and [`shapes_production_big.py`](../shapes_production_big.py) (grounded clawed stacks, the siege tower, the smoke rack, the log ramp). EA's body is kept whole; EA's facts are in [`building.py`](building.py).

## Pass 2: the war-forge

Pass 1 (`_review/production_v1.jpg`) put fire bowls on roofs; the coordinator's review: a bowl perched on a roof reads as a small egg stuck on (the citadel's pass 5 lesson), and the buildings were too subtle at rts. Pass 2 (`_review/production_v2.jpg`) grounds every fire and gives each building one bold mass.

- **Forge**: a great jagged basalt stack from the ground in the yard's back corner (-44, 24), eight-sided, iron bands, ember slits, a lava seam; its mouth at z 46 opens into seven hooked spikes to z 61 over the walls round a `furnace` fire and a heavy `plume`; three barred furnace mouths at its foot (`forge`).
- **Siege tower**: half-built at (8, 14), facing the mouth: raking timber posts to z 56, iron plates up the front and sides, a raised drawbridge with barbed teeth, the top storey bare frame, a scaffold by it. Placed off the forge's line of sight from the RTS camera so the two masses read apart.
- **Lava**: an open runnel from the forge's mouths across the yard (`embers`, `smoke`).
- **Crane and catapult**: a braced timber crane against the +Y wall swings a boulder over a catapult (-28, 2) (hooked iron claw for a cup, spiked counterweight).
- **Mouth**: fire baskets (`brazier`) and impaling stakes either side of the open +X side, inside EA's footprint.

Fire: 9 points (1 furnace, 1 plume, 3 forge, 1 embers, 1 smoke, 2 brazier), the game's own particle systems on the rig's bones (`fire_points`, from the design's log). No green: orange fire and lava only.

## Status

- [x] healthy body designed (pass 2, 2026-09-30), preview checks pass
- [ ] Max's review: `build/assets/mordor/_review/production_v2.jpg`
- [ ] colour build, lifecycle and night checks (after EA's sheet is recoloured)
