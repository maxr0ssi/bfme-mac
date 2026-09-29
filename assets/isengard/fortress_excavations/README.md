# Isengard excavations (`IsengardFortressCitadel`)

Model `IBFExcav`, mesh `IBFEXCAV`, own texture `IBFortresJ.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The citadel's `FORTRESS_IMPROVEMENT_3` add-on (`ModuleTag_DrawExcavations`): the
terraced pit that fills the courtyard. EA's body is kept whole: the terraces, the three spoil
mounds and their shafts, the winding tower; `IBFEXCAVAT2`..`AT5` (the A-frame, its bucket and rope,
animated) stay EA's.

## What changed (`pits.py`)

- **The pits of Isengard**: fire and smoke out of all three shafts (`fire_points`, 3, chimney).
- **The flue** (pass 3): the south shaft made the pit's furnace flue, the citadel's needle
  chimney out of its mound (flange on the rim at z 21, a glowing throat at z 50, its corners
  turned 45 degrees clear of the chute's skip), a ring of leaning iron stakes round it. It stops
  under EA's A-frame, whose pulley swings over the shaft no lower than z 58.8.
- **Terrace spikes**: iron spikes along the upper terrace (r 41.5) in four arcs, leaning in.
- **North-east floor**: a loaded ore cart, a slag heap with embers, a log stack; lanterns on posts.

## Kept clear

- The bucket and rope that rise out of the north shafts and swing across (`IBFExcavAN`, swept every
  second frame): the north shafts stay open, nothing new within r 9 of them above z 18; the whole
  sweep (A-frame included) passes no closer than 0.6 to any new solid.
- The A-frame's swing, the winding tower, the wizard's tower, the burning forges, the chute and
  ladders.
- The citadel: its wedge towers stand over EA's rim (their inner faces at r 44), so nothing new
  goes past r 43; no vertex inside the citadel's new solids either way.

## Status

Designed, shape preview only (not built, not installed). Pass 3: 875 -> 2,012 triangles, height
and footprint unchanged, 9/9 preview checks. Review sheet: `build/assets/isengard/_review/addons_v3.jpg` (pass 3; `addons.jpg` is pass 1).

## Open

- Full build: bake, paint, lifecycle (`IBFExcav_A`, `_D3`).
