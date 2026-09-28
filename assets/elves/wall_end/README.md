# Elven wall end

Model `EBWallNE`, redesigned mesh `EBWALLN`, `Tier.STANDARD`. Its own textures are
`EBFortresE.tga` / `EBFortresE_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

EA's cliff cap and all its window detail stay whole, including the below-ground faces.
The segments' filigree band, mithril coping and leaf crest continue to the cut end. A small
ivory lantern-house crowns the end pier, with lattice lancets, silver frames and a swept slate
roof with a gilt finial. No banners or extra frames on EA's wall windows. The next segment
still meets the same section.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

Construction and damaged states derive the body; really damaged and collapsing states rebuild
it along EA's pieces and animations.

Build outputs and before/after images are in `build/assets/elves/wall_end/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.

## Superseded first-pass measurements

These figures describe the previous design, not the current output. Current reports live in
`build/assets/elves/wall_end/work/` and are verified again for this finishing pass.

Footprint unchanged, height 102.4 -> 120.35 (+17.5 %, limit 20 %), 1,227 -> 7,178 triangles (96
cloth faces moved to `EBHCWallNE`). `checks`: 79/79 pass.