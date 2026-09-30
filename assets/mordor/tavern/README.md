# Mordor tavern (`MordorTavern`)

Model `MBTavern_SKN`, mesh `MAINHOUSE`, own texture `MBTaverH.tga` (from `MBTavern.tga`; Isengard draws `mbtavern` too, so ours is pinned). New pieces come from the Mordor kit ([`shapes.py`](../shapes.py) and its mixins) and the production group's modules [`shapes_production.py`](../shapes_production.py) (the claw spike, shelves, pits, the saw, the catapult, claw bars) and [`shapes_production_big.py`](../shapes_production_big.py) (grounded clawed stacks, the siege tower, the smoke rack, the log ramp). EA's body is kept whole; EA's facts are in [`building.py`](building.py).

## Pass 2: the black hearth

Pass 1 (`_review/production_v1.jpg`) put fire bowls on roofs; the coordinator's review: a bowl perched on a roof reads as a small egg stuck on (the citadel's pass 5 lesson), and the buildings were too subtle at rts. Pass 2 (`_review/production_v2.jpg`) grounds every fire and gives each building one bold mass.

- **Stack**: a great jagged chimney stack of black basalt from the ground against the hall's front wall (-24, -35), leaning in toward the roof, past the eaves: iron bands, ember slits, a lava seam; its mouth at z 74 opens into seven hooked spikes to z 84 round a `chimney` fire and a `plume`. Pass 1's stack on the ridge is gone.
- **Ridge**: steel spikes up out of the ridge in two runs, clear of the crow's nest (V1).
- **Front**: a gibbet cage off the front wing's gable over the door, fire baskets (`brazier`) either side of the door, an open lava channel along the front (`embers`, `smoke`), a bone heap at the corner.
- EA's body carries two loose vertices; `design()` drops them.

Fire: 6 points (1 chimney, 1 plume, 2 brazier, 1 embers, 1 smoke), the game's own particle systems on the rig's bones (`fire_points`, from the design's log). No green: orange fire and lava only.

## Status

- [x] healthy body designed (pass 2, 2026-09-30), preview checks pass
- [ ] Max's review: `build/assets/mordor/_review/production_v2.jpg`
- [ ] colour build, lifecycle and night checks (after EA's sheet is recoloured)
