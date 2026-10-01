# Isengard warg sentry (`IsengardWargSentry`)

Model `IBWargSent`, mesh `IBWARGSENT`, own texture `IBWargSenH.tga` (from `IBWargSent.tga`); new
faces map to the faction's master sheet. `Tier.STANDARD`. EA's den is kept whole: the trodden disc,
the rocks, tusks and stakes round its rim, the great ribcage.

## What changed (`kennel.py`)

- **Pass 4** (2026-09-30, Max: "our furnace towers on everything look a lil stupid"): pass 3's
  blade pair on the back rim went. Where each stood, at the palisade's ends: a heap of gnawed bones
  (`shapes_trades.bone_heap`, grey, not bleached), a chain stake with spiked collars lying in the
  dirt (`tether`), and the tall brazier at its foot as before.

- An iron-banded palisade of sharpened stakes along the back rim.
- Warg posts: iron-capped stakes with a collar ring and a chain trailing into the den.
- Three clusters of iron-tipped stakes on the rim.
- The White Hand on an Uruk shield raised on a post, on the back axis.
- A fire pit under an iron grate and two tall braziers by the way out to the rally point
  (`fire_points`, 5: grate and four braziers).

## Kept clear

- The middle (r < 38): the three wargs spawn at (10, 0) and roam there. New pieces stand on the
  rim where EA's collision boxes are.

## Status

Pass 3 built and installed (2026-09-29). Pass 4 designed, shape preview only: 3,013 -> 6,921
triangles (pass 3: 6,841), height unchanged (pass 3: +34.1 %; `max_z_growth` back to the default),
footprint unchanged, fire 5 -> 5, 9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg`.
Pass 3: `_review/addons_v3.jpg`.

## Open

- Full build: bake, paint, lifecycle (`IBWargSent_A`, `_D1`..`_D3`). `N_WINDOW`, `N_FIRE` stay EA's.
