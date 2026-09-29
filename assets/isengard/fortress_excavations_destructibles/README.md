# Isengard excavations: chute and ladders (`IsengardFortressCitadel`)

Model `IBFExcavB`, mesh `IBFEXCAVB`, own texture `IBFortresK.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The destructible pieces of the citadel's `FORTRESS_IMPROVEMENT_3` add-on
(`ModuleTag_DrawExcavationsDestructibles`). EA's pieces are kept whole: the chute on its trestles,
the two ladders, the leaning post.

## What changed (`spoil.py`)

- Glowing ore tumbling down the chute out of an iron skip at its head.
- A lantern on an iron arm out of the post.

## Kept clear

- The south shaft's mound and stakes, the A-frame's swing, the burning forges, the wizard's tower.

## Status

Designed, shape preview only (not built, not installed). 374 -> 500 triangles, height and
footprint unchanged, 9/9 preview checks. No fire.

## Open

- Full build: bake, paint, lifecycle (`IBFExcavB_A`, `_D3`).
