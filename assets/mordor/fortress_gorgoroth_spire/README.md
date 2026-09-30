# Mordor fortress Gorgoroth spire (`MordorFortressCitadel`)

Model `MBFEWEye`, mesh `MBFEWEYE`, own texture `MBFortresD.tga` (from `MBFortress.tga`). The citadel's `UPGRADE_FORTRESS_MONUMENT` add-on (`ModuleTag_DrawGorgorothSpire`): EA's tower of the Eye in the courtyard's middle, kept whole (the keep, its skirt of wedges, the round shaft, the crown and the horned Eye). New pieces
come from the Mordor kit and the add-ons' shared pieces ([`../shapes_addons.py`](../shapes_addons.py)).
EA's facts are in [`building.py`](building.py).

## What changed (`spire.py`)

- **Four claws round fire**: on each corner of the keep's roof (z 75.2), where EA's skirt of
  wedges meets it, a claw of five jagged, hooked spikes (the crowns' Horn, a steel outer edge, lava
  seams on the tall two) rises round a heap of embers and a real fire, to z 92: four fires round
  the foot of the shaft, as the citadel's four crowns burn.
- **Forked cracks glowing from within** (pass 2; pass 1's seams read as painted flames) up the
  round shaft on its diagonals (z 84..100) and up the keep's four buttresses (z 40..66, over the
  courtyard's walls).
- Tried and cut in pass 1: a claw inside EA's crown round the Eye's stem. EA's crescent fills the
  crown; the spikes read as sticks poking into the Eye.
- **Fire** (`fire_points`, 4): `brazier` in each corner claw (+-13.6, +-13.6, 77.2).

## Kept clear

- The Eye and its crown (z 131..175) and EA's bone EYEBONE (0, 0, 160.8), where GorSpireCharge
  plays while the spire powers up.
- The citadel keeps |x| < 19.15, |y| < 23.3 clear for the spire; no face crosses the citadel's new
  faces; the nearest citadel fire point is 24.4 away.

## Status

Designed, shape preview only (not built, not installed). Pass 2: 1,060 -> 5,916 triangles, height unchanged, footprint unchanged, 9/9 preview checks. Checked on our citadel
(pass 7) with every add-on built at once. Review sheet: `build/assets/mordor/_review/addons_v2.jpg` (pass 1: `addons_v1.jpg`).

- [x] healthy body designed (pass 2)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint, lifecycle (`MBFEWEye_A`, `_D2`, `_D3`).
- Whether the spire wants more at the RTS view (the Eye is EA's and stays; Max's call).
