# Isengard battle tower (`IsengardBattleTower`)

Model `IBBtlTwr`, mesh `TOWER`, own texture `IBBtlTwH.tga` (from `IBBtlTwr.tga`); new faces map to
the faction's master sheet. `Tier.STANDARD`. EA's tower is kept whole: the battered, clawed plinth,
the square shaft with its X-braced panel, the archers' deck and the upswept roof.

## What changed (`tower.py`)

- Knife fins up the shaft's four corners, silver-edged.
- Two riveted iron bands round the shaft, over and under the panel.
- The White Hand in a pointed arch on the shaft's +X face.
- Ember arrow slits in the plinth's +X and -Y faces.
- Iron spikes along the roof's eaves.
- Two braziers on the archers' deck (`fire_points`, 2, brazier).

## Kept clear

- The archers' bones (`ARROWBONE01`..`12`), the garrison flags (`GARRISON01`/`02`, out to y +-20),
  the door at the foot.

## Status

Designed, shape preview only (not built, not installed). 541 -> 1,382 triangles, height and
footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`IBBtlTwr_A`, `_D1`, `_D2`). `IBBtlTwrM` (Mordor's copy)
  stays EA's.
