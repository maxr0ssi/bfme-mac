# Isengard siege works (`IsengardSiegeWorks`)

Model `IBSeigeWork`, mesh `IBSEIGEFRAME`, own texture `IBSeigeWorH.tga` (DXT5, EA's cut-out
alpha kept). The walls `IBSEIGEWALLS` (own sheet `IBSeigeWall`) stay EA's. Palette A; new pieces
from the Isengard kit and [`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py). `world_space`: the
frame hangs on a bone moved (20.3, -0.3, 0.7). EA's body is kept whole, the awning with the
painted Hand included.

## Pass 4: destacked (2026-09-30)

Max after Mordor: "our furnace towers on everything look a lil stupid" and "super low quality
that tower". The rollout's needle stacks and stamped blade pairs read as bolted-on clones. Each
building now gets its own work instead (new pieces in [`shapes_trades.py`](../shapes_trades.py)),
smaller and fewer, its fire in its own forges, grates, braziers and pits.

- **Out**: the two tridents at the mouth, their chain and Hand shield, the four needles out of
  the post heads.
- **In**: two low forge plinths flanking the mouth (a battered stone block, a silver coping with
  iron spikes, two fire grates in its front, the Hand in a pointed-arch slot between them). The
  half-built siege tower is the yard's one tall new mass; the ram, the forge and the ladder stay.
- **Fire** 8 -> 8: the grates and braziers as before (the grates moved with the plinths).

932 -> 4,026 triangles (pass 3: 7,602), height +0 % (pass 3: +18.3 %), footprint
unchanged, 9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg` (installed
pass 3 against pass 4 at the RTS view).

## Pass 3: up to the citadel

Pass 2 read modest beside the citadel. Pass 3 applies its recipe: the pair, needle stacks,
the Hand in pointed-arch slots, fire. Sheet: `_review/production_v3.jpg`.

- **The pair** (the citadel's): the two tridents at the mouth keep their horns and saddle; the
  middle of each is the citadel's broad lozenge blade (6.2 x 4.2, to z 72.5, two fins a face,
  silver edges, ember slits), the White Hand in a pointed-arch slot on its outer face between
  the fins, mirrored about the mouth's axis; two fire grates glow in each saddle's front.
- The Hand shield on the chain between them is greater (11 tall, its foot at z 33).
- **Siege tower** moved out from under the awning, where the RTS camera never saw it, to the
  -Y edge at (-14, -46.4): 7 wide, 54 tall, 78 % built, its pointed roof frame over the awning.
  The log stack shortened to (-34, -46.3).
- **Fire** (8: 4 furnace (the saddles' grates), 2 brazier, hearth, crucible).

932 -> 7,602 triangles, height 63.2 -> 74.7 (+18.3 %), footprint unchanged, 9/9 preview checks.

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

- [x] pass 3 built in colour and installed (2026-09-29)
- [x] pass 4 designed (shape preview, 2026-09-30)
- [ ] pass 4 reviewed by Max, built in colour, installed
