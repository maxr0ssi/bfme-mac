# Elven floodgate doors

Model `EBFFGate_DRCA`, redesigned mesh `EBFFGATE2`, `Tier.STANDARD`. Its own textures are
`EBFortresG.tga` / `EBFortresG_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

EA's five pointed door leaves and their raised bosses stay whole. Each receives a mithril
ridge bead, one gilt clasp with silver edges, and a gilt leaf on its pointed top. The earlier
three teal knotwork clasps were removed to keep EA's detail readable. No cloth is attached to
moving leaves. Additions remain behind the floodgate's pier fronts when the doors close.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

Opening derives the same leaves with EA's motion; rubble rebuilds along EA's pieces.
Construction `_DRA` places the finished leaves lower than the closed healthy model. Its explicit
`match_offset` aligns the healthy reference before cutting; live healthy geometry and EA's
animation are untouched. The construction now matches exactly and passes the unchanged gates.

Build outputs and before/after images are in `build/assets/elves/floodgate_doors/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.

## Superseded first-pass measurements

These figures describe the previous design, not the current output. Current reports live in
`build/assets/elves/floodgate_doors/work/` and are verified again for this finishing pass.

Footprint as above, height 36.62 -> 36.62 (+0 %), 280 -> 1,400 triangles. `checks`: 58/58.
