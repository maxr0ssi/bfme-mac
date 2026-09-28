# Elven vigilant ent expansion

Model `EBFVEntHol`, redesigned mesh `EBFVENTBUD`, `Tier.STANDARD`. Its own textures are
`EBFortresN.tga` / `EBFortresN_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

EA's planter, soil bed, connecting arm and slab stay whole, and the ent's space stays clear.
An ivory balustrade with a silver rail circles the rim, with six leaf-capital lantern posts.
Mithril caps follow the arm and slab shoulders; gilt finials and a crystal beacon crown them.
The arm keeps the shared pointed arch frame. Two banners hang from the slab ends.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

Construction, really damaged and rubble models rebuild along EA's pieces and motion.
Damaged, snow and stonework variants retain our body.

Build outputs and before/after images are in `build/assets/elves/vigilant_ent/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.

## Superseded first-pass measurements

These figures describe the previous design, not the current output. Current reports live in
`build/assets/elves/vigilant_ent/work/` and are verified again for this finishing pass.

Footprint unchanged (x -43.91..19.28, y -21.18..21.18), height 53.0 -> 53.0 (+0 %),
260 -> 9,600 triangles (the balusters and columns are most of it). `checks`: 92/92.
