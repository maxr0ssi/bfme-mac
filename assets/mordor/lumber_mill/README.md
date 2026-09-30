# Mordor lumber mill (`MordorLumberMill`)

Model `MBLumMill_SKN` shipped as our own `MBLumMill2_SKN`, mesh `LUMBERMILL`, own texture `MBLumberMilB.tga` (from `MBLumberMill.tga`); house copy `MBHCLumMill2`. The Goblins and Isengard draw EA's mill too; their copies are theirs. New pieces come from the Mordor kit ([`shapes.py`](../shapes.py) and its mixins) and the production group's modules [`shapes_production.py`](../shapes_production.py) (the claw spike, shelves, pits, the saw, the catapult, claw bars) and [`shapes_production_big.py`](../shapes_production_big.py) (grounded clawed stacks, the siege tower, the smoke rack, the log ramp). EA's body is kept whole; EA's facts are in [`building.py`](building.py).

## Pass 2: the charcoal pit

Pass 1 (`_review/production_v1.jpg`) put fire bowls on roofs; the coordinator's review: a bowl perched on a roof reads as a small egg stuck on (the citadel's pass 5 lesson), and the buildings were too subtle at rts. Pass 2 (`_review/production_v2.jpg`) grounds every fire and gives each building one bold mass.

- **Claw**: six big spikes rise from inside the fire pit's stone ring (r 12 round (20, 32.7)) and close over its coals, tall ones to z 42, short ones to z 33; they stand between the four crossed planes of EA's flame card (FIRE01), which stays.
- **Fire**: `furnace` over the coals among the spikes and a heavy `plume` over it: the orcs burn the felled wood to charcoal for the forges.
- **Saw**: a tall gantry of charred A-frames (to z 40, 25 across) over the great log's middle, a steel blade with hooked teeth hung on chains, bitten into the log.
- **Log ramp**: five courses of felled trunks at (38, -38), three skids leaning up onto the pile, iron stakes and chains.
- **Shed**: steel spikes leaning out along the front beam. **Yard**: a charcoal heap, a fire basket (`brazier`), a whip post by the stumps, a lava pool (`embers`).
- `facet_islands = 8` and `lifecycle = {"MBLumMill_A": {"fill": True}}`, as the Goblins' and Isengard's mills (EA's unwrap overlaps; its build model is a remodel).

Fire: 4 points (1 furnace, 1 plume, 1 brazier, 1 embers), the game's own particle systems on the rig's bones (`fire_points`, from the design's log). No green: orange fire and lava only.

## Status

- [x] healthy body designed (pass 2, 2026-09-30), preview checks pass
- [ ] Max's review: `build/assets/mordor/_review/production_v2.jpg`
- [ ] colour build, lifecycle and night checks (after EA's sheet is recoloured)
