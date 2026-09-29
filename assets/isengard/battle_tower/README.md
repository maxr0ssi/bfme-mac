# Isengard battle tower (`IsengardBattleTower`)

Model `IBBtlTwr`, mesh `TOWER`, own texture `IBBtlTwH.tga` (from `IBBtlTwr.tga`); new faces map to
the faction's master sheet. `Tier.STANDARD`. EA's tower is kept whole: the battered, clawed plinth,
the square shaft with its X-braced panel, the archers' deck and the upswept roof.

## What changed (`tower.py`)

- **The pair** (pass 3, the citadel's blades): two lozenge blades welded to the shaft's +-Y faces
  from the plinth's foot ((16.3, +-10.6), 16 long, 7 wide), mirrored about the tower's axis,
  through the roof's eaves to needles at z 150 either side of EA's spike (126): layered fins,
  silver edges, ember slits, spurs at their -X feet, the White Hand in a pointed-arch slot on each
  one's outer +X face. They replace pass 1's corner fins.
- Two riveted iron bands round the shaft, over and under the panel.
- The White Hand in a pointed arch on the shaft's +X face.
- Ember arrow slits in the plinth's +X and -Y faces.
- Iron spikes along the roof's eaves.
- Two braziers on the archers' deck, two on brackets out of the plinth's +X face
  (`fire_points`, 4, brazier).

## Kept clear

- The archers' bones (`ARROWBONE01`..`12`), the garrison flags (`GARRISON01`/`02`, x 8..9, out to
  y +-20, z 83..103: the blades stand at x > 9.3 there), the door at the foot.

## Status

Designed, shape preview only (not built, not installed). Pass 3: 541 -> 3,412 triangles, height
124.6 -> 148.5 (+19.2 %), footprint unchanged, 9/9 preview checks. Review sheet: `build/assets/isengard/_review/addons_v3.jpg` (pass 3; `addons.jpg` is pass 1).

## Open

- Full build: bake, paint, lifecycle (`IBBtlTwr_A`, `_D1`, `_D2`). `IBBtlTwrM` (Mordor's copy)
  stays EA's.
