# Isengard furnace (`IsengardFurnace`)

Model `MBFurnace_SKN` (Mordor's name, drawn by Isengard only), mesh `FURNACE`, own texture
`MBFurnacH.tga`. Palette A; new pieces from the Isengard kit and the production group's
[`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py). `world_space`: the mesh hangs on a bone moved
(3.5, -0.2, 0.3), so design and fire points share world axes. EA's body is kept whole.

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

- [x] healthy body designed (pass 2, shape preview)
- [ ] reviewed by Max, built in colour, installed
