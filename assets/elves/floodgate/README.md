# Elven floodgate

Model `EBFFGate`, redesigned mesh `EBFFGATE1`, `Tier.STANDARD`. Its own textures are
`EBFortresF.tga` / `EBFortresF_NRM.tga` and state variants, painted from `EBFortress.tga`
with EA's cut-out alpha retained.

## Current design

EA's horses, gold swirls, pointed bays, water and ground ring stay whole. A mithril coping
and silver-railed ivory balustrade ring the basin; crystal lanterns stand on newels over the
buttress piers. The aqueduct receives matching coping and pointed silver arch frames.
Only two banners remain, on the front piers beside the flood. Moving leaves belong to
[`floodgate_doors`](../floodgate_doors/README.md).

`pad.py` supplies the expansions' shared arch and coping helpers. The facet-island unwrap
preserves the horse surfaces; the footprint margin accommodates the existing banner rods.

The shared palette is the approved citadel's soft ivory, strong mithril and mallorn gold, slate
roofs and EA's teal glass. No face of EA's healthy body is removed.

## Lifecycle and review

Damaged, snow and stonework variants carry our body. Really damaged and rubble models rebuild
along EA's pieces. Construction matches only EA’s exact healthy surface (`surface = 0.05`), preserving the nearby
paired internal caps as break faces. This fixes the former open-back fallback while keeping the
original gates and animation. No failing model is forced into the output.

Build outputs and before/after images are in `build/assets/elves/floodgate/`. The current
`work/lifecycle.json` identifies each rebuilt or derived model; `work/logs/checks.log` records
the checks. Review images are `renders/compare_*.png` and `renders/lifecycle/*.png`.
Healthy and lifecycle comparisons were rebuilt and visually checked in this finishing pass.
Nothing is installed; the player’s review remains the next step.

EA supplies no night meshes or `NightWindowName` here; the new crystals are day-lit.
