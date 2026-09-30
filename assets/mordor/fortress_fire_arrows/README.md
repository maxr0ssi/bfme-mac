# Mordor fortress fire arrows (`MordorFortressCitadel`)

Model `MBFFArrows`, mesh `MBFFARROWS`, own texture `MBFortresB.tga` (from `MBFortress.tga`). The citadel's `FORTRESS_IMPROVEMENT_1` add-on (`ModuleTag_DrawFireArrows`): EA's clawed fire-pod on eight legs over the gatehouse (x 32.6..51.6, z 60..89.8). EA's pod, legs and twelve rim spikes are kept whole; its flame cards `FLAMES` and `FIREGLOW` and the smoke at `GLOWBONE01` stay. New pieces
come from the Mordor kit and the add-ons' shared pieces ([`../shapes_addons.py`](../shapes_addons.py)).
EA's facts are in [`building.py`](building.py).

## What changed (`pod.py`)

- **The crown in small**: six jagged, hooked spikes (the citadel crowns' Horn, a steel outer edge,
  teeth hooking up, a hook down, a lava seam on the tall three) rise from inside the pod's rim
  (r 4.4, z 79) in the gaps between EA's twelve spikes and close over the fire: the tall three to
  z 95.0, the short three to z 90.5.
- A heap of embers on EA's bed, a real fire in it.
- A hooked barb off each of EA's eight legs, halfway up.
- **Fire** (`fire_points`, 1): `brazier` in the pod (42.1, 0, 82), under EA's flame cards.

## Kept clear

- EA's flame cards (`FLAMES`: crossed planes on the pod's axes; `FIREGLOW` at x 44.5): kept in game,
  left out of bakes and renders (`bake_hidden`).
- The citadel: the frontispiece and the Eye (x 57.3), the parapet spikes (|y| > 14.5), the flue and
  fire baskets: no face crosses the citadel's new faces; the nearest citadel fire point is 34.5 away.

## Status

Designed, shape preview only (not built, not installed). Pass 1: 376 -> 1,312 triangles, height 29.9 -> 35.0 (+17.2 %), footprint unchanged, 9/9 preview checks. Checked on our citadel
(pass 7) with every add-on built at once. Review sheet: `build/assets/mordor/_review/addons_v2.jpg` (unchanged in pass 2).

- [x] healthy body designed (pass 1)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint, lifecycle (`MBFFArrows_A`, `_D1`..`_D3`).
- Whether our fire under EA's orange flame cards is too much, in game.
