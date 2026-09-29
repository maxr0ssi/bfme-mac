# Isengard ballista (`IsengardBallistaExpansion`)

Model `IBFBalTow`, mesh `IBFBALTOW`, own texture `IBFortresX.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. A fortress expansion: the pad the ballista stands on. EA's pad is kept whole: the
pentagon with its prow, the finned foot, the two bands, the cornice and the flat top.

## What changed (`pad.py`)

- Pointed merlons along the cornice (three to an edge, silver on their heads).
- The White Hand in a pointed arch on each long side, ember arrow loops either side of it.
- A blade up the prow, knife fins on the upper walls' corners.
- Two braziers at the top's back corners (`fire_points`, 2, brazier).

## Kept clear

- The top: the ballista and its crew (P1, x -26.4..6, |y| < 15.5) have the whole platform.

## Status

Designed, shape preview only (not built, not installed). 234 -> 1,206 triangles, height 51.1 ->
58.2 (+13.9 %, the merlons), footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`IBFBalTow_A`, `_D2`, `_D3`). No house model: no banner.
