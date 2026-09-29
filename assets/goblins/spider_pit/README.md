# Goblin spider pit (`WildSpiderPit`)

Model `WBSpidPit_SKN`, mesh `ROCK`, own texture `WBBStonH.tga` (from `WBBStone.tga`). Palette E.
EA's rock spire, its boulders, the crimson hole of the pit (`SPI PIT`), the glowing web cards
(`WEBS`, cut-outs) and the level-3 cocoons are kept whole. The idea: a brood-mother's lair,
clutched by the legs of a great dead spider.

## What changed

- **Legs**: five jointed legs of crimson chitin with bleached claws, rising from the spire and
  bending down over the rock to the ground, bone knuckles at the joints, bristles on the upper
  legs (the new silhouette; the webs hang between them).
- **Spire**: a skull on an iron spike on its tip.
- **Larder**: a timber gibbet on the -Y side, propped, two flayed carcasses on chains.
- **Trophies**: skull piles and gnawed bones round the rock's foot.
- **Banner**: one on a post on the -Y boulder (cap 1).

## Kept clear

- The pit's opening to +X (x > 8, |y| < 22), where the spiders come out; nothing past ROCK's
  x 25.4. The web cards are left out of the bake (`bake_hidden`) so they cast no baked shadow.

## Status

Shape preview only. 330 -> 3,611 triangles, height 75.5 -> 81.8 (+8.5 %), footprint unchanged,
9/9 preview checks.
