# Isengard ballista (`IsengardBallistaExpansion`)

Model `IBFBalTow`, mesh `IBFBALTOW`, own texture `IBFortresX.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. A fortress expansion: the pad the ballista stands on. EA's pad is kept whole: the
pentagon with its prow, the finned foot, the two bands, the cornice and the flat top.

## What changed (`pad.py`)

- **The pair** (pass 3, the citadel's blades): two lozenge blades against the long walls' back
  halves ((-27.2, +-16.1), 15 long, 7 wide), mirrored about the pad's axis, from the foot to
  needles at z 68.5, behind the ballista as the RTS camera sees it; a stockier profile than the
  citadel's (the needle over the last eighth) so they keep their mass above the low pad; layered
  fins, silver edges, ember slits, the White Hand in a pointed-arch slot on each one's outer face.
- A crown of pointed merlons (9.6 tall) along the cornice: two to an edge from the blades round
  the prow, three on the back edge between the blades.
- The White Hand in a pointed arch on each long side, ember arrow loops beside it; knife fins
  on the long walls and the prow faces, a blade up the prow, ember loops on the prow faces.
- Two braziers at the top's front corners (`fire_points`, 2, brazier).

## Kept clear

- The top: the ballista and its crew (P1, x -26.4..6, |y| < 15.5) have the whole platform; the
  blades stand at its back corners, outside it above the cornice.

## Status

Designed, shape preview only (not built, not installed). Pass 3: 234 -> 3,188 triangles, height
51.1 -> 68.6 (+34.3 %), footprint unchanged, 9/9 preview checks. `max_z_growth = 0.35`, as the citadel's: needs Max's OK like the citadel's had; at the default
0.20 the blades stop at z 61.
Review sheet: `build/assets/isengard/_review/addons_v3.jpg` (pass 3; `addons.jpg` is pass 1).

## Open

- Full build: bake, paint, lifecycle (`IBFBalTow_A`, `_D2`, `_D3`). No house model: no banner.
