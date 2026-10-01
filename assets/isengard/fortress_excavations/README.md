# Isengard excavations (`IsengardFortressCitadel`)

Model `IBFExcav`, mesh `IBFEXCAV`, own texture `IBFortresJ.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The citadel's `FORTRESS_IMPROVEMENT_3` add-on (`ModuleTag_DrawExcavations`): the
terraced pit that fills the courtyard. EA's body is kept whole: the terraces, the three spoil
mounds and their shafts, the winding tower; `IBFEXCAVAT2`..`AT5` (the A-frame, its bucket and rope,
animated) stay EA's.

## What changed (`pits.py`)

- **The pits of Isengard**: fire and smoke out of all three shafts (`fire_points`, 3, chimney).
- **The south shaft** (pass 4, 2026-09-30, Max: "our furnace towers on everything look a lil
  stupid"): pass 3's needle flue out of it (to z 50) went. A riveted iron kerb on its rim (z 23.6)
  round a glowing grate of bars across the mouth, fire and smoke out of the shaft itself (z 22), a
  ring of leaning iron stakes round it. Nothing new rises toward the A-frame's pulley any more.
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

Pass 3 built and installed (2026-09-29). Pass 4 designed, shape preview only: 875 -> 2,068
triangles (pass 3: 2,012), height and footprint unchanged, fire 3 -> 3, 9/9 preview checks.
Sheet: `build/assets/isengard/_review/destack_v1.jpg`. Pass 3: `_review/addons_v3.jpg`.

## Open

- Full build: bake, paint, lifecycle (`IBFExcav_A`, `_D3`).
