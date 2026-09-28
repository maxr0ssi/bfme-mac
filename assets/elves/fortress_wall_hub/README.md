# Elven fortress wall hub

Model `EBEFWHub`, redesigned mesh `EBWALLRMPRTN01`, `Tier.STANDARD`. Its own textures are
`EBFortresX.tga` / `EBFortresX_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

The fortress corner uses the free-standing hub's design: EA's body and lattice dome kept
whole, filigree band and mithril coping round the rim, gold ribs and leaf crown on the dome,
and crystal lanterns. No banners, window frames or rim merlons. EA's short connecting wall
run remains intact. The recipe inherits the hub's target-versus-separate-dome height bound.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

Damaged states derive or rebuild the body. Collapse `_D3` uses EA's rest pose before its pieces
move; it now passes the unchanged lifecycle gates. Construction uses `EBWallRmprtN_A`, built
and shipped by `wall_hub`; this recipe deliberately does not ship that file a second time.

Build outputs and before/after images are in `build/assets/elves/fortress_wall_hub/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.

## Superseded first-pass measurements

These figures describe the previous design, not the current output. Current reports live in
`build/assets/elves/fortress_wall_hub/work/` and are verified again for this finishing pass.

Footprint unchanged (x +-24.09, y +-22.83), height 53.05 -> 60.60 (+14.2 %, limit 20 %),
374 -> 6,146 triangles. `checks`: 73/73.
