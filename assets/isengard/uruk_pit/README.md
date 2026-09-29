# Isengard uruk pit (`IsengardUrukPit`)

Model `IBUrukPit_SKN`, mesh `IBURUKPIT_NEW`, own texture `iburukpiH.tga`. Palette A; new pieces
from the Isengard kit and [`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py). EA's mound is kept whole:
both lobes, the pit's octagonal mouth, the ramp, ladders and decks, the cave mouth.

## Pass 2: the breeding pits

- **Birthing-frame** (the new silhouette): six knife ribs of iron rise from a riveted band on the
  pit's rim (z 44), stand up to a ring at z 56 and bend in to meet in a needle at z 70; meat hooks
  hang round the ring, a great hook on a chain down into the pit. It replaces pass 1's hoist.
- **Stacks**: two lozenge needle stacks either side of the pit, to z 66.
- **Fins**: a fan of three layered stone fins on the +X lobe's flank, over the cave mouth.
- **Furnace mouths**: two barred fireboxes glowing in the main lobe's -Y face.
- **Yard**: a birthing pit (iron kerb, glowing mud, blade posts, chains), two Uruk harnesses on
  stands and a blade rack on the +Y yard; a banner on an iron frame at the -X foot; two braziers.
- **Fire** (8 points): grate in the pit, chimney in each stack, furnace in each firebox, embers in
  the birthing pit, two braziers.

1,087 -> 4,561 triangles, height 65.4 -> 77.5 (+18.5 %), footprint unchanged, 9/9 preview
checks. Pass 1 is `_review/production_v1.jpg`.

## Kept clear

- The Uruk-hai and the hook that animate in the pit (`HOOK`, `PM_ORC`, `UILURTZ02`, z 0..17).
- The units' way out: made at (46, -10), rallying to (41, -70) through the cave mouth.
- The level-up (`V2`: the tower and banner at the back, two banner poles flanking the cave mouth).
- EA's night torch posts (`N_WINDOW`).

## Status

- [x] healthy body designed (pass 2, shape preview)
- [ ] reviewed by Max, built in colour, installed
