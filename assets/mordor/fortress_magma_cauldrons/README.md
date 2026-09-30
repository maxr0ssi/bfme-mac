# Mordor fortress magma cauldrons (`MordorFortressCitadel`)

Model `MBFMCauld`, mesh `MBFMCAULD`, own texture `MBFortresC.tga` (from `MBFortress.tga`). The citadel's `FORTRESS_IMPROVEMENT_3` add-on (`ModuleTag_DrawMagmaCauldrons`): the cauldron tower on the -X inner face, its two horns, the pan on the -X walk and eight spouts on the outer faces. EA's pieces are kept whole. The tipping cauldron and its orc are a skinned model of their own (`MBFMCauld_SKN`, `ModuleTag_DrawMagmaCauldronsGuy`, animated): not ours to change, and kept clear. New pieces
come from the Mordor kit and the add-ons' shared pieces ([`../shapes_addons.py`](../shapes_addons.py)).
EA's facts are in [`building.py`](building.py).

## What changed (`magma.py`)

- **The furnace** (pass 2: larger): a pointed mouth of glowing coals at the cauldron tower's foot
  in the courtyard (x -26.47, |y| < 5.8, z 1..17.4), an iron frame, a hooked barb clawing up each
  side, a steel spike over it; two forked cracks glowing from within run up the tower's courtyard
  face from it (z 18..42; pass 1's read as painted flames).
- **The spouts**: each of EA's eight spout mouths brims with lava (a flame sill in its recess);
  from seven of them lava pours down the battered wall in a narrow kinked runnel of even width
  (z 25 to 12..19.5; pass 1's tapered drips read as flame cones). The +X face's +Y spout
  stands over the citadel's scaffold and keeps only its sill.
- **Fire** (`fire_points`, 4): `furnace` in the mouth; `embers` at the three spouts the RTS camera
  sees (+X face -Y, -Y face both).

## Kept clear

- EA's footprint is +-52.74 while the citadel's faces stand at 52.8 on the ground: the runnels stand
  0.13 proud of the battered faces and stop where they would pass the footprint (z 12).
- The citadel's own cracks on the -Y and +X faces (fortress/walls.py): each drip over one stops
  above it (z 15..19.5); the scaffold (x 53.2..57.4, y 17..30); the courtyard's lava channel (broken
  at |y| < 10.5 at x -26.4); the Gorgoroth spire (x > -19.15). No face crosses the citadel's new
  faces; the nearest citadel fire point is 13.9 away.
- The cauldron's swing (`MBFMCauld_SKN`, CAULDRON at x -42.3..-29.8, y -22.8..15.9, z 69.6..91.3
  at rest) and the pan: nothing of ours above the tower's foot.

## Status

Designed, shape preview only (not built, not installed). Pass 2: 780 -> 2,339 triangles, height unchanged, footprint unchanged, 9/9 preview checks. Checked on our citadel
(pass 7) with every add-on built at once. Review sheet: `build/assets/mordor/_review/addons_v2.jpg` (pass 1: `addons_v1.jpg`).

- [x] healthy body designed (pass 2)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint, lifecycle (`MBFMCauld_A`, `_D2`, `_D3`).
- The walls under the drips are the citadel's: the add-on's own model shows the runnels' backs (soot) only where no wall stands, which never happens in game.
