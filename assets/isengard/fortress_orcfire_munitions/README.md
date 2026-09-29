# Isengard orcfire munitions (`IsengardFortressCitadel`)

Model `IBFOrcfire`, mesh `IBFORCFIRE`, own texture `IBFortresG.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The citadel's `FORTRESS_IMPROVEMENT_1` add-on (`ModuleTag_DrawOrcfireMunitions`):
five fire-pots, on the four wedge towers' tops and over the gate. EA's pots are kept whole (the
eight-sided drums and their curved fins); its fire cards `MBFDPF`, `MBFDPFG` and the smoke on
`GLOWBONE01`..`05` stay.

## What changed (`pots.py`)

- Each pot: a riveted iron rim with a silver lip and eight iron spikes round its mouth, an ember
  band round the drum, four knife blades between EA's fins, and orcfire jars (small iron-bound
  pots) at its foot.
- **Fire** (`fire_points`, 5, brazier): one at every mouth, under EA's fire cards.

## Kept clear

- EA's fire cards over the mouths; the citadel's spikes along the tower tops' edges (9 away) and
  its collars on the points; no vertex inside the citadel's new solids either way.

## Status

Designed, shape preview only (not built, not installed). 920 -> 4,200 triangles, height and
footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`IBFOrcfire_A`, `_D1`..`_D3`); whether our fire over EA's
  cards is too much, in game.
