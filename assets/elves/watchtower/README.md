# Elven watchtower

Model `EBFWTower`, redesigned mesh `EBFWTOWER`, `Tier.STANDARD`. Its own textures are
`EBFortresP.tga` / `EBFortresP_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

EA's tower, knotwork, dormers, roof and horns stay whole. A needle spire continues the pyramid,
with mithril ribs and gilt leaf tips on the horns. Mithril coping and crystal lanterns crown
the cornice; silver frames dress the flank doors and connecting arch. Two banners hang down
the shaft's flanks. The arrow bones and their firing space remain clear.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

Construction, really damaged and rubble models rebuild along EA's pieces and motion.
Damaged, snow and stonework variants retain our body.

Build outputs and before/after images are in `build/assets/elves/watchtower/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.

## Superseded first-pass measurements

These figures describe the previous design, not the current output. Current reports live in
`build/assets/elves/watchtower/work/` and are verified again for this finishing pass.

Footprint unchanged (x -42.54..12.73, y -18.42..18.44), height 151.88 -> 175.49 (+15.5 %, limit
20 %), 476 -> 3,350 triangles. `checks`: 92/92.
