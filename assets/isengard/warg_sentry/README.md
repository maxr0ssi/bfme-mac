# Isengard warg sentry (`IsengardWargSentry`)

Model `IBWargSent`, mesh `IBWARGSENT`, own texture `IBWargSenH.tga` (from `IBWargSent.tga`); new
faces map to the faction's master sheet. `Tier.STANDARD`. EA's den is kept whole: the trodden disc,
the rocks, tusks and stakes round its rim, the great ribcage.

## What changed (`kennel.py`)

- An iron-banded palisade of sharpened stakes along the back rim.
- Warg posts: iron-capped stakes with a collar ring and a chain trailing into the den.
- Three clusters of iron-tipped stakes on the rim.
- The White Hand on an Uruk shield raised on a post.
- A fire pit under an iron grate and two tall braziers by the way out to the rally point
  (`fire_points`, 3: grate, brazier, brazier).

## Kept clear

- The middle (r < 38): the three wargs spawn at (10, 0) and roam there. New pieces stand on the
  rim where EA's collision boxes are.

## Status

Designed, shape preview only (not built, not installed). 3,013 -> 4,819 triangles, height and
footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`IBWargSent_A`, `_D1`..`_D3`). `N_WINDOW`, `N_FIRE` stay EA's.
