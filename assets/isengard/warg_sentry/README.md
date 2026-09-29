# Isengard warg sentry (`IsengardWargSentry`)

Model `IBWargSent`, mesh `IBWARGSENT`, own texture `IBWargSenH.tga` (from `IBWargSent.tga`); new
faces map to the faction's master sheet. `Tier.STANDARD`. EA's den is kept whole: the trodden disc,
the rocks, tusks and stakes round its rim, the great ribcage.

## What changed (`kennel.py`)

- **The pair** (pass 3, the citadel's blades): two blade pylons on the den's back rim at r 49,
  mirrored about its back axis (141 degrees, away from the way out to the rally point), broad
  faces to the RTS camera, to needles at z 44: layered fins, spurs, silver edges, ember slits,
  the White Hand in a pointed-arch slot on each; chains from each to the Hand standard's head on
  the axis between them, a tall brazier at each one's foot.

- An iron-banded palisade of sharpened stakes along the back rim.
- Warg posts: iron-capped stakes with a collar ring and a chain trailing into the den.
- Three clusters of iron-tipped stakes on the rim.
- The White Hand on an Uruk shield raised on a post, on the back axis between the blades.
- A fire pit under an iron grate and two tall braziers by the way out to the rally point
  (`fire_points`, 5: grate and four braziers).

## Kept clear

- The middle (r < 38): the three wargs spawn at (10, 0) and roam there. New pieces stand on the
  rim where EA's collision boxes are.

## Status

Designed, shape preview only (not built, not installed). Pass 3: 3,013 -> 6,841 triangles, height
33.1 -> 44.3 (+34.1 %), footprint unchanged, 9/9 preview checks. `max_z_growth = 0.35`, as the citadel's: needs Max's OK like the citadel's had; at the default
0.20 the blades stop at z 39.
Review sheet: `build/assets/isengard/_review/addons_v3.jpg` (pass 3; `addons.jpg` is pass 1).

## Open

- Full build: bake, paint, lifecycle (`IBWargSent_A`, `_D1`..`_D3`). `N_WINDOW`, `N_FIRE` stay EA's.
