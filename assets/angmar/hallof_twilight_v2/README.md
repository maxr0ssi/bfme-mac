# Angmar Hall of Twilight, level 3's piece (`V2` of `KBTemple`)

Model `KBTemple`, mesh `V2` (shown at level 3 with its rune glow), own texture `KBTemplY.tga` (from
`KBTemple.tga`). Palette A2. Chained on [`hallof_twilight_v1`](../hallof_twilight_v1) (`base`): the
chain's last link, so its build ships `KBTemple` and the derived `KBTemple_D1` for the whole chain
(`hallof_twilight` -> `_top` -> `_v1` -> `_v2`; rebuild in that order after changing any link).

## What changed

- **The crown's three horns** (9.43 higher than at level 1) frozen at the tips, as on `TOP_1`.
- **The three great horns** rising from the dais's sides to z 107.5 frozen over their upper 35 %
  (from z 70), four crystals each. EA's V2 stays whole inside. Shared with the other levels:
  [`../hallof_twilight/horns.py`](../hallof_twilight/horns.py).
- V2's three small horns from the dais (to z 46) stay EA's: the menhirs stand 3 or less from them up
  to z 39, so a casing there would touch them.

## Kept clear

- Shown per upgrade level: no cloth, no night lights, no fire.

## Status

- [x] designed, built (1,753 -> 2,581 triangles, height +0.9 %), checks pass
- [ ] renders reviewed (`build/assets/angmar/_review/hall_levels_v1.jpg`)
- [ ] checked in game
