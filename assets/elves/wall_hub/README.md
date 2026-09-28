# Elven wall hub

Model `EBWallRmprtN`, redesigned mesh `EBWALLRMPRTN`, `Tier.STANDARD`. Its own textures are
`EBFortresC.tga` / `EBFortresC_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

EA's round tower, lancet windows, ivy and separate lattice dome stay whole. The walls' filigree
band and mithril coping circle the rim without merlons. Gold ribs follow the existing dome to
a gilt collar, leaf coronet and finial. Crystal lanterns stand on silver posts around the rim.
No banners or added window frames.

`max_z_growth = 0.40` accounts for EA's dome being a separate mesh: the measured target ends at
53.05 while EA's existing dome reaches 67.6. The crown grows from that dome, not from an absent
roof. This inherited bound is unchanged in this finishing pass.

The fortress wall hub reuses `crown`, `dome` and `lanterns`. `is_body` excludes that expansion,
whose other models are owned by its own recipe.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

The game draws `EBWallRmprtN_A` healthy; it is derived from the static source to avoid importing
construction's underground first pose. Damaged models derive or rebuild the body. Collapse
`_D3` matches EA's rest pose: animation frame zero already displaces its pieces and was causing
open cuts. The unchanged lifecycle gates now accept the rebuilt collapse.

Build outputs and before/after images are in `build/assets/elves/wall_hub/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.

## Superseded first-pass measurements

These figures describe the previous design, not the current output. Current reports live in
`build/assets/elves/wall_hub/work/` and are verified again for this finishing pass.

Nothing passes the footprint (x +-24.09, y +-22.83): the crown's widest point, the gilt beads at
the 90-degree corner, is at y 22.79. Height 53.05 -> 60.6 (+14.2 %, limit 20 %), 374 -> 6,194
triangles (72 cloth faces moved to `EBHCWallRmprtN`). `checks`: 71/71 pass.