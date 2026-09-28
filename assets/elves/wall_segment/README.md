# Elven wall segment

Model `EBWallN`, redesigned mesh `EBWALLN`, `Tier.STANDARD`. Its own textures are
`EBFortresB.tga` / `EBFortresB_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

EA's slender wall stays whole: lattice windows, pointed hoods, gold leaf emblems and V cornice.
Only its crown changes: a filigree band between gilt beads, mithril coping and a light crest of
slender gold-edged leaf merlons. Both faces match. The shared profile lives in `wall.py` and
continues through the ends, hubs and gate. Ends still tile and the engine may stretch the wall.
No banners or extra window frames: repeated wall pieces leave EA's window detail visible.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

Construction, damaged and placement models derive the healthy body. The damaged and collapsing
pieces are rebuilt along EA's original animation. Shared `GBWall_Rubble` remains EA's.

Build outputs and before/after images are in `build/assets/elves/wall_segment/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.

## Superseded first-pass measurements

These figures describe the previous design, not the current output. Current reports live in
`build/assets/elves/wall_segment/work/` and are verified again for this finishing pass.

Footprint unchanged, height 51.2 -> 59.0 (+15.2 %, limit 20 %), 326 -> 3,142 triangles
(48 cloth faces moved to `EBHCWallN`). `checks`: 84/84 pass.