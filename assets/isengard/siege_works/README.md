# Isengard siege works (`IsengardSiegeWorks`)

Model `IBSeigeWork`, mesh `IBSEIGEFRAME`, own texture `IBSeigeWorH.tga` (DXT5, EA's cut-out
alpha kept). The walls `IBSEIGEWALLS` (own sheet `IBSeigeWall`) stay EA's. Palette A; new pieces
from the Isengard kit and [`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py). `world_space`: the
frame hangs on a bone moved (20.3, -0.3, 0.7). EA's body is kept whole, the awning with the
painted Hand included.

## Pass 2: the war-yard

- **Tridents** (the new silhouette): either side of the mouth on +X, a lozenge blade tower to
  z 72.5 between two lesser horns leaning out on a stone saddle; ember slits, needle tips. An iron
  chain slung between them high over the mouth, a White Hand shield hung from it; a brazier at
  each one's inner foot.
- **Needles**: iron needles with knife fins out of the four middle and +X post heads (the -X
  heads carry EA's fire).
- **Engines** under the awning: a half-built siege tower (timber posts leaning in, braces, the
  lower levels skinned in riveted iron, a drawbridge, a pointed iron roof frame) and a ram (a great
  trunk with iron hoops and an iron wedge head, slung on chains from two iron A-frames).
- **Forge** under the awning's +Y side; knife fins clasp every post; a half-built ladder on the
  +Y side, felled trunks on the -Y side.
- **Fire** (4 points): the two braziers, the forge's hearth and crucible. EA's own fire on the
  -X posts' heads (`BN_FIRE05/06`) stays.

932 -> 6,692 triangles, height 63.2 -> 74.7 (+18.3 %), footprint unchanged, 9/9 preview
checks. Pass 1 is `_review/production_v1.jpg`.

## Kept clear

- The mouth: units are made at (66.7, 0) and leave for (130, 0) (x > 40, |y| < 22); the chain
  hangs at z 46.
- The level-up tower (`V2`, `V2A`: x -81..-37).
- EA's night torch posts (`N_WINDOW`).

## Status

- [x] healthy body designed (pass 2, shape preview)
- [ ] reviewed by Max, built in colour, installed
