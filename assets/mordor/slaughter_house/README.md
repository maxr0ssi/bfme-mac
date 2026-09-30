# Mordor slaughter house (`MordorSlaughterHouse`)

Model `MBSltrHs_SKN`, mesh `MBSLTRHS`, own texture `MBSltrHH.tga` (from `MBSltrHs.tga`). New pieces come from the Mordor kit ([`shapes.py`](../shapes.py) and its mixins) and the production group's modules [`shapes_production.py`](../shapes_production.py) (the claw spike, shelves, pits, the saw, the catapult, claw bars) and [`shapes_production_big.py`](../shapes_production_big.py) (grounded clawed stacks, the siege tower, the smoke rack, the log ramp). EA's body is kept whole; EA's facts are in [`building.py`](building.py).

## Pass 2: the smoke-house

Pass 1 (`_review/production_v1.jpg`) put fire bowls on roofs; the coordinator's review: a bowl perched on a roof reads as a small egg stuck on (the citadel's pass 5 lesson), and the buildings were too subtle at rts. Pass 2 (`_review/production_v2.jpg`) grounds every fire and gives each building one bold mass.

- **Stack**: a jagged basalt smoke stack from the ground at the yard's front (25, -60): iron bands, ember slits, a lava seam, its mouth at z 56 opening into seven hooked spikes to z 73 round a `chimney` fire and a heavy `plume`.
- **Smoke rack**: a great gantry of charred timber from (24, -15) to (24, -46), to z 26, with a top bar and two lower bars of meat hooks and heavy dark carcasses: the bold new mass at rts.
- **Yard** (on the terrain at z 0; EA's yard slab lies under it at -3.4): butcher blocks with steel cleavers, two bone heaps round spikes, a lava runnel to the stack's foot (`embers`).
- **Hall**: a gibbet cage off the ridge's -Y horned end, steel spikes along the +X deck's edge, two fire baskets (`brazier`) on it. Pass 1's bowl on the ridge is gone.
- Kept clear: the hook wheel's sweep (animated, r 18 round (21, 6)), the level-up tower (V2), the rhino (x 3..14, y -72..-35), the ramp.

Fire: 5 points (1 chimney, 1 plume, 1 embers, 2 brazier), the game's own particle systems on the rig's bones (`fire_points`, from the design's log). No green: orange fire and lava only.

## Status

- [x] healthy body designed (pass 2, 2026-09-30), preview checks pass
- [ ] Max's review: `build/assets/mordor/_review/production_v2.jpg`
- [ ] colour build, lifecycle and night checks (after EA's sheet is recoloured)
