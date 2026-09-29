# Goblin sentry tower (`WildSentryTower`)

Model `WBTower`, mesh `DBTOWER`, own texture `WBToweH.tga` (from `WBTower.tga`); new faces are
mapped onto the faction's `WBFortress.tga` atlas (two sheets). `Tier.STANDARD`. EA's tower is
kept whole: the rough black stone shaft, the four horn-plate buttresses, the porch over the door
and its ramp, the riveted hood with its spiked eaves and forked tip. The mesh hangs on a bone
turned 180 degrees: the camera sees the mesh's -x and +y sides.

## What changed

A small cousin of the citadel's spires.

- **Hood**: a riveted iron band at z 98, four great crimson horns with bleached tips sweeping
  out of it, four small tusks under them; an iron spike from the tip to z 144.5 with a big skull
  driven onto it.
- **Shaft**: a skull on a bloodied spike, a crimson hide with a white hand nailed under the
  ledge, a gibbet cage with a skeleton on an iron arm under the hood.
- **Foot**: a skirt of black rock ([`../arrow_den/pad.py`](../arrow_den/pad.py)) and two skull
  piles.
- **Banners**: one ragged banner with a white eye over the porch (cap 1), in `WBHCTower`
  (EA's flag is dropped by the house step).

## Kept clear

- The door, ramp and porch: nothing new at x < -12, |y| < 10 below z 24.
- The lookout: `N_WINDOW`'s light streaks (r up to 37, z 69..88): nothing new beyond the hood
  in that band.

## Status

Installed. 1,289 -> 5,019 triangles, height 124.0
-> 144.8 (+16.7 %), footprint unchanged, 9/9 preview checks.

## Open

- `WBTower.tga` has no `materials` rects in the atlas (ROLLOUT framework item 6): its rusty
  riveted hood plates will recolour as crimson hide and the stone as rock until they are added.
- Full build: bake, paint, lifecycle (`WBTower_A`, `_D1`, `_D2`, `_D3`), `sagekit house`.
  `N_WINDOW` is a night mesh: night lights not designed yet (the style has no `NightLook`).
