# Goblin razor spines (`WildFortressCitadel`, `WildFortressRazorSpines`)

Model `WBFRSpin`, mesh `WBFRSPIN`, own texture `WBFortresD.tga` (from `WBFortress.tga`).
`Tier.STANDARD`. The citadel's `FORTRESS_IMPROVEMENT_4` add-on (`ModuleTag_DrawSpines`), drawn
round the [citadel](../fortress/README.md)'s foot. EA's ring is kept whole: the banded ring, the
flat spikes fanning out on the ground, the 38 leaning uprights.

## What changed

- **Skulls** driven onto six of the tall uprights (at +-73, +-107 and +-164 degrees), blood below.
- **Tusks**: twelve bleached tusks in iron collars rising out of the ring's top between the
  uprights, leaning out.
- **Chevaux de frise**: eight logs laid along the ring with pairs of sharpened stakes crossed
  through them, some tips bloodied, a thong round each log.
- **Impaled**: a skeleton lashed to a stake at each side and at the back (to z 16.2).
- **Gore**: the `Gore` paint layer under the skulls and the impaled.
- **Banners**: none (cap 0; the citadel carries three).

## Kept clear

- The gate: nothing new at x > 44, |y| < 36 (the ramp, the doors' swing, the citadel's gate
  tusks, skull piles, impaled skeletons and banners).
- The four spire columns at (+-44.2, +-44.2): nothing within 6 of them.

## Status

Designed, shape preview only (not built, not installed). 736 -> 4,714 triangles, height 13.8 ->
16.2 (+17 %; `max_z_growth = 0.35` for the impaled, far below the citadel's walls at z 42),
footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`WBFRSpin_A`, `_D2`, `_D3`) and renders with the citadel.
