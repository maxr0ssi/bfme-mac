# Isengard wizard's tower: Orthanc (`IsengardFortressCitadel`)

Model `IBFWTower`, mesh `IBFWTOWER`, own texture `IBFortresN.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The citadel's `UPGRADE_FORTRESS_MONUMENT` add-on (`ModuleTag_DrawWizardsTower`),
standing in the courtyard of the [citadel](../fortress/README.md). EA's octagonal tower is kept
whole: its bands, windows, spurred plinth, the thin horn blades and spike of its crown.

## What changed (`orthanc.py`)

"Four mighty piers of many-sided stone welded into one, but near the summit they opened into
gaping horns":

- **Piers**: one on each diagonal face from the ground to z 138, nine-sided in plan (a flute cut
  into each cheek, a silver arris), flared at the foot, a waist over the plinth's batter, a
  set-back cornice at the plinth's top (z 40), tapering with EA's shaft.
- **Horns**: each pier opens at z 138 into a horn that leans out, closes behind into a knife edge
  and curls back to a point at z 200, framing EA's crown and the lightning's bone.
- **Windows**: ember-lit pointed windows up every pier's cheeks at three heights.
- **Door and Hand**: a pointed doorway framed in silver on the +X face (the gate's side), the
  White Hand in a pointed arch above it.
- **Balcony**: Saruman's balcony over the door at z 94, on pointed corbels, a spiked railing, a
  glowing window behind it.
- **Pass 3 (up to the citadel)**: the White Hand great in a pointed-arch slot high on the three
  axis faces the balcony leaves free (-Y, +Y, -X, z 101..117), and fire: a brazier on an iron
  bracket out of every pier's arris at z 78, between the windows and above the walls, and two
  on the balcony (`fire_points`, 6, brazier). Orthanc's identity (piers, horns, door, balcony) is
  unchanged.

## Kept clear

- The lightning: `FXBONE` at (0, 1.2, 184.1); nothing near the axis above z 165.
- Every other upgrade built at once: the excavations' chute (its rail at r 20.9..21.8, z 29..34)
  and the A-frame's standing timber (r 21.9, z 34..41) - the piers stand 3.2 out there - and the
  bucket and rope that rise out of the north shafts (swept over `IBFExcavAN`, clear).
- The citadel's new solids: no vertex inside them either way, none on its fire points.
- The pier braziers stand at z 78, 13 or more clear of the excavations' A-frame and bucket over
  `IBFExcavAN` (at z 46, the first try, the A-frame's head passed within 1 of the +X -Y one).
- As EA's own tower sinks into the excavations' floor, the piers' feet sink into the floor and the
  two north spoil mounds' flanks (z 13..18), and touch the burning forges' foot at z 0..9, where EA's
  tower already overlaps it.

## Status

Designed, shape preview only (not built, not installed). Pass 3: 1,572 -> 5,486 triangles,
height 175.7 -> 200 (+13.8 %), footprint unchanged (`footprint_margin = 1.0` for the door frame on
the battered face), 9/9 preview checks, 6 fire points. Review sheet: `build/assets/isengard/_review/addons_v3.jpg` (pass 3; `addons.jpg` is pass 1).

## Open

- Full build: bake, paint, lifecycle (`IBFWTower_A`, `_D1`..`_D3`) and renders with the citadel.
