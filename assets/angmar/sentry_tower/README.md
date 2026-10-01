# Angmar sentry tower (`AngmarSentryTower`)

Model `KBBtlTwr`, mesh `BASE`, own texture `KBBtlTwH.tga` (from `KBBtlTwr.tga`). Free-standing (built
by the porter). EA's hexagonal tower, its six corner blades and horns kept whole. EA's facts are in
[`building.py`](building.py).

## What changed

- **A frozen crown on the roof** (the bold mass): three forged iron tines (the citadel's tine at 36
  tall: spine, steel edges, barbs, a riveted band, a rune groove, frozen tips with crystals and
  icicles) rise from the flat roof (z 86) to z 122 on the short-blade corners, between EA's three
  tall horns, round a cairn of black stone and ice.
- **Fire** (`fire_points`, 1): `coldfire` in the cairn's crater (0, 0, 93.6).

## Kept clear

- The windows' arrow bones (z 45.2, 67.8), the night windows (`N_WINDOW`), the doorway and steps.

## Status

Pass 1, shape preview only (not built, not installed): 1,527 -> 3,681 triangles, height and
footprint unchanged, 9/9 preview checks. Review sheet: `build/assets/angmar/_review/addons_v1.jpg`.

- [x] healthy body designed (pass 1)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint (its own sheet KBBtlTwr; new faces on the master's regions), lifecycle
  (`KBBtlTwr_A`, `_D1`..`_D3`), house model `KBHCBtlTwr`.
