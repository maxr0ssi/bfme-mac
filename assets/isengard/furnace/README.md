# Isengard furnace (`IsengardFurnace`)

Model `MBFurnace_SKN` (Mordor's name, drawn by Isengard only), mesh `FURNACE`, own texture
`MBFurnacH.tga`. Palette A; new pieces from the Isengard kit and the production group's
[`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py). `world_space`: the mesh hangs on a bone moved
(3.5, -0.2, 0.3), so design and fire points share world axes. EA's body is kept whole.

## Pass 3: up to the citadel

Pass 2 read modest beside the citadel. Pass 3 applies its recipe: the pair, needle stacks,
the Hand in pointed-arch slots, fire. Sheet: `_review/production_v3.jpg`.

- **The pair** (the citadel's): two matching lozenge blades out of the mound's top either
  side of the crater in the RTS view, mirrored about it (`shapes_industry_big.blade_pair`), to
  z 128.5: flared, spurred feet, one fin a face (three read as a cage at this size), silver
  edges, ember slits, needle tips, the White Hand in a pointed-arch slot on each one's outer
  face. The left one's foot is at z 86, above the level-up hut (`V2`, to z 84.6), which hugs the
  mound's -Y shoulder; nothing new stands on that side below it.
- **Great chimney**: pass 2's wide spire out of the crater (a box at the RTS view) is a needle
  stack now, between the blades like the citadel's great chimney (z 44 to 116, crown to 125).
- **Chains** from each blade to the chimney's throat.
- The crater's crown keeps three blades (the pair stands where the others were).
- **Fire** (9: chimney, furnace, hearth, 3 crucible, 3 brazier).

1,141 -> 6,073 triangles, height 113.2 -> 134.9 (+19.2 %), footprint unchanged, 9/9 preview checks.

## Pass 2: the smelter

Pass 1 (buttresses, crown, a stack behind the horns) read almost as EA's at the RTS view. Pass 2
gives the mound one great pointed mass:

- **Spire**: a blade-spire stack out of the crater between the horns, to z 128: a lozenge shaft
  from a flared foot, a set-back step, knife fins up its sharp edges, three rows of ember slits,
  an ember band with spikes, a crown of blades round its glowing mouth
  (`shapes_industry_big.spire_stack`; the kit's needle stack cannot take this size). Pass 1's
  stack behind the horns is gone: at the RTS view the two merged.
- **Buttresses**: four layered knife-edge fins of black stone on the mound's +Y flank, a fifth on
  its front under the level-up's deck; silver front edges, ember slits.
- **Crown**: seven iron blades round the crater's rim, leaning out.
- **Tap**: a steep iron hood over the chute's mouth, spikes on its ridge.
- **Gantry**: iron A-frames over the mould, a square crucible on its chain.
- **Yard**: a forge on the +Y side, a rack of tongs and blades, ingots, a slag heap and cart,
  three braziers, one banner on an iron frame facing the camera.
- **Fire** (9 points; EA's furnace has none): chimney at the spire's mouth, furnace at the tap,
  three crucibles (the mould, the gantry, the forge), hearth, three braziers.

1,141 -> 4,431 triangles, height 113.2 -> 131.1 (+15.8 %), footprint unchanged, 9/9 preview
checks. Pass 1 is `_review/production_v1.jpg`.

## Kept clear

- The level-up hut `V2` (the -Y half above z 34, and its ladder up the -X side).
- The melt, the mould, the pool and the ingots (`LIQUIDMETAL1`, `MOLD`, `POOLOMETAL`, `INGOTS`,
  EA's) and the yard in front where the porters work.
- EA's night torch posts (`N_WINDOW`).

## Status

- [x] healthy body designed (pass 3, shape preview)
- [ ] reviewed by Max, built in colour, installed
