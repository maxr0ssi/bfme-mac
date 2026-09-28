# Elven wall gate

Model `EBWallGateN_SKN`, redesigned mesh `EBWALLGATEN`, `Tier.STANDARD`. Its own textures are
`EBFortresD.tga` / `EBFortresD_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

EA's gate towers, warrior statues, torches and folding lattice doors stay whole. A slender
bridge carries the wall crown and leaf crest over the passage; a pointed arch holds a crystal
lantern above its middle. Each tower head has a filigree band and mithril coping, without
merlons, and crystal lanterns on its corners. Two leaf banners hang on the towers' outward
faces on the same side. Nothing new enters the moving doors' travel or the passage.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

All damaged and collapsing variants derive the body on EA's existing bones. The original door
animation and fire effects remain in place.

Build outputs and before/after images are in `build/assets/elves/wall_gate/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.
The unchanged torch effect cards appear as black rectangles in both Blender previews;
these belong to EA’s additive fire effects, not the new tower geometry.

## Superseded first-pass measurements

These figures describe the previous design, not the current output. Current reports live in
`build/assets/elves/wall_gate/work/` and are verified again for this finishing pass.

Gameplay geometry kept: nothing new below z 48.9 over the passage (|y| < 40.16) or in the leaves'
travel; the towers' outer faces (|y| 58.68), where the segments meet, are left alone; the footprint
(x -10.26..10.24, y -59.65..59.68) is unchanged. Height 60.16 -> 71.39 (+18.7 %, limit 20 %),
128 -> 8,622 triangles (44 cloth faces moved to `EBHCWallGateN_S`). `checks`: 115/115 pass.