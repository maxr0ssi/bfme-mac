# Mordor wall catapult (`MordorWallCatapultExpansion`)

Model `MBFWCTow`, mesh `MBFWCTOW`, own texture `MBFortresG.tga` (from `MBFortress.tga`). A fortress expansion built on the citadel's pads (the MordorFortress castle starts with four): a wall and a round spiked drum carrying the catapult, kept whole. New pieces
come from the Mordor kit and the add-ons' shared pieces ([`../shapes_addons.py`](../shapes_addons.py)).
EA's facts are in [`building.py`](building.py).

## What changed (`drum.py`)

- **The family's claw on the rim** (pass 2): thirteen jagged spikes (the citadel crowns' Horn, a
  steel outer edge, a hook down, lava seams on the tall seven; no inner teeth) round the drum's
  outer half (-90..90 degrees), rising from the parapet (r 21.2, z 52.5) and leaning in, to z 67
  and 65. Open in the middle: the catapult and its swing keep the platform.
- Two clawed fire baskets in the claw's gaps (+-52.5 degrees).
- Forked cracks glowing from within up the drum's seven outward flute panels (0, +-15, +-30, +-90
  degrees, z 24.5..39.5), each laid on the panel's face (raycast on EA's mesh). Pass 1's seams read
  as painted flames.
- **Fire** (`fire_points`, 4): `brazier` in each basket, `embers` at the roots of the two front
  cracks.

## Kept clear

- The top (EA's P1: the drum's octagon within r 19.4 of its axis and the wall walk, z 48).
- **The catapult's swing**: EA spawns MordorFortressCatapult (model MBFWCatap) at (-16, 0, 48); it
  turns to its target. Its animation (MBFWCatap.MBFWCatap, frames 0..120) measured frame by frame:
  the frame sweeps r 18.5 round (-16, 0) up to z 90, the arm and stone out to r 41.4, never lower
  than z 57.9 between r 18 and 20 from that axis, 68.5 between 20 and 24, 62.2 beyond. Every new
  vertex above the platform clears that envelope by 3.4 at least (checked on the preview stage).
- Checked on all seven pads: no face crosses the citadel's new faces.

## Status

Designed, shape preview only (not built, not installed). Pass 2: 962 -> 4,064 triangles, height unchanged, footprint unchanged, 9/9 preview checks. Checked on our citadel
(pass 7) with every add-on built at once. Review sheet: `build/assets/mordor/_review/addons_v2.jpg` (pass 1: `addons_v1.jpg`).

- [x] healthy body designed (pass 2)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- The claw may rise no higher than z 67.5 on the rim: the arm passes over it.
- Full build: bake, paint, lifecycle (`MBFWCTow_A`, `_D2`, `_D3`).
