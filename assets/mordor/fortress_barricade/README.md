# Mordor fortress barricade (`MordorFortressBarricadeExpansion`)

Model `MBFBarric`, mesh `MBFBARRIC`, own texture `MBFortresX.tga` (from `MBFortress.tga`). A fortress expansion built on the citadel's pads: a wall with a walk for archers and a square tower, kept whole with EA's base plate `BIB`. (Not the player-built `barricade`, which is another building.) New pieces
come from the Mordor kit and the add-ons' shared pieces ([`../shapes_addons.py`](../shapes_addons.py)).
EA's facts are in [`building.py`](building.py).

## What changed (`tower.py`)

- **The citadel's crown on its tower**: inside the tower's open top (floor z 111.1) a claw of eight
  jagged, hooked spikes (the crowns' Horn: steel outer edge, teeth, a hook, lava seams on the tall
  four) leaning in round a heap of embers and a real fire, to z 128.
- **The Eye** in the pointed window on each of the tower's broad faces (z 76..94).
- Forked cracks glowing from within (pass 2; pass 1's read as painted flames) up the tower's
  broad faces and the wall's outer end from the top of the base plate (z 9.45); the barbed bottom of a raised portcullis in the wall's arch (both faces).
- **Fire** (`fire_points`, 1): `brazier` in the crown (-19.2, 0, 112.9).

## Kept clear

- The archers' walk (EA's P1, z 50) and bones ARROW_01..04; the base plate BIB.
- Checked on all seven pads: no face crosses the citadel's new faces.

## Status

Designed, shape preview only (not built, not installed). Pass 2: 1,199 -> 5,403 triangles, height 120.8 -> 128.0 (+5.9 %), footprint unchanged, 9/9 preview checks. Checked on our citadel
(pass 7) with every add-on built at once. Review sheet: `build/assets/mordor/_review/addons_v2.jpg` (pass 1: `addons_v1.jpg`).

- [x] healthy body designed (pass 2)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint, lifecycle (`MBFBarric_A`, `_D2`, `_D3`).
