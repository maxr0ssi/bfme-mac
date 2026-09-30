# Mordor orc pit (`MordorOrcPit`)

Model `MBOrcpit_SKN`, mesh `ORCPIT`, own texture `MBBStonH.tga` (from `MBBStone.tga`); house copy `MBHCOrcpit2`. New pieces come from the Mordor kit ([`shapes.py`](../shapes.py) and its mixins) and the production group's modules [`shapes_production.py`](../shapes_production.py) (the claw spike, shelves, pits, the saw, the catapult, claw bars) and [`shapes_production_big.py`](../shapes_production_big.py) (grounded clawed stacks, the siege tower, the smoke rack, the log ramp). EA's body is kept whole; EA's facts are in [`building.py`](building.py).

## Pass 2: the jaws of the pit

Pass 1 (`_review/production_v1.jpg`) put fire bowls on roofs; the coordinator's review: a bowl perched on a roof reads as a small egg stuck on (the citadel's pass 5 lesson), and the buildings were too subtle at rts. Pass 2 (`_review/production_v2.jpg`) grounds every fire and gives each building one bold mass.

- **Claw**: fourteen of the citadel's spikes, every 24 degrees, rise from inside the crater's inner wall (r 25 round the pit's axis (-5, 7)) and lean in over the pit: tall ones to z 39.2 (steel outer edge, teeth, a hook, a lava seam), short ones to z 34.5. A 48-degree gap round 298 degrees is the orcs' way out toward their rally point (10, -75). Two chains with meat hooks hang between the tall spikes at the back.
- **Pit of forges**: seven basalt shelves heaped with glowing coals ring the pit's foot on the inner wall (z 15.6..16.2, over EA's mud floor at 13..15); four `forge` fires on them and one heavy `plume` over the pit.
- **Lava**: glowing seams down the front slopes (250, 315, 20 degrees) into an open lava channel at the mound's foot and a lava pool; `embers` and a thin `smoke`.
- **Yard**: a war drum and a whip post at the front corner, three impaling stakes by the way out, an ash heap and a bone heap.
- The height limit (+20 %) holds the tips to z 39.4. EA's body carries eight loose vertices; `design()` drops them (the Men forge's `drop_loose`).

Fire: 8 points (4 forge, 1 plume, 2 embers, 1 smoke), the game's own particle systems on the rig's bones (`fire_points`, from the design's log). No green: orange fire and lava only.

## Status

- [x] healthy body designed (pass 2, 2026-09-30), preview checks pass
- [ ] Max's review: `build/assets/mordor/_review/production_v2.jpg`
- [ ] colour build, lifecycle and night checks (after EA's sheet is recoloured)
