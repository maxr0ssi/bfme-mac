# Angmar Hall of Twilight, level 2's piece (`V1` of `KBTemple`)

Model `KBTemple`, mesh `V1` (shown at level 2, hidden at 3), own texture `KBTemplX.tga` (from
`KBTemple.tga`). Palette A2. Chained on [`hallof_twilight_top`](../hallof_twilight_top) (`base`);
build after it, before [`hallof_twilight_v2`](../hallof_twilight_v2).

## What changed

- **The crown's three horns** (4.32 higher than at level 1) frozen at the tips, as on `TOP_1`.
- **The three great horns** rising from the dais's sides to z 86 frozen over their upper 40 % (from
  z 52), four crystals each. EA's V1 stays whole inside. Shared with the other levels:
  [`../hallof_twilight/horns.py`](../hallof_twilight/horns.py).

## Decision (2026-10-01)

First left EA's (the Hall's own design stands on `BASE`, clear of `V1`). Max wanted the Hall's horns
frozen like every other Angmar building's, so each level piece is redesigned: `TOP_1`, `V1`, `V2`.

## Kept clear

- The menhirs (on `BASE`) stand under z 39; the great horns' casings start over z 42.8 (the ragged
  frost line).
- Shown per upgrade level: no cloth, no night lights, no fire.

## Status

- [x] designed, built (1,499 -> 2,327 triangles, height +1.0 %), checks pass
- [ ] renders reviewed (`build/assets/angmar/_review/hall_levels_v1.jpg`)
- [ ] checked in game
