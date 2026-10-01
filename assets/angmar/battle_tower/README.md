# Angmar battle tower (`AngmarBattleTowerExpansion`)

Model `KBArrowTower`, mesh `ARROWTOWER`, own texture `KBFortressH.tga` (from `KBFortressB.tga`). The
citadel's tower expansion, on any of its seven pads (EA's base file `bases\fortress_angmar`), its
wing toward the citadel. EA's tower, parapet bowl, lantern and horns kept whole. EA's facts are in
[`building.py`](building.py).

## What changed

- **A small frozen crown on the lantern** (the bold mass): three forged iron tines (the citadel's
  tine at 30 tall: spine, steel edges, barbs, a riveted band, a rune groove, frozen tips with
  crystals and icicles) rise from the lantern's roof (z 86) to z 116 in the gaps between EA's three
  horns, round a cairn of black stone and ice.
- **Fire** (`fire_points`, 1): `coldfire` in the cairn's crater (-3, 0, 92.2).
- Nothing on the wing: on the corner pads it runs into the bastion.

## Kept clear

- The archers' ring and ARROW01..04 (z 73), EA's horns and blades, the Ice Walls shell (`ICEWALL`).
- Checked on all seven pads: no new face crosses the citadel's new faces.
- **Open, not ours to fix**: on the S and N pads EA's tower crosses the citadel's two banners
  (fortress/yard.py, at -90 and 90 degrees) and, on S, the fissure kerb.

## Status

Pass 1, shape preview only (not built, not installed): 1,168 -> 3,334 triangles, height and
footprint unchanged, 9/9 preview checks. Review sheet: `build/assets/angmar/_review/addons_v1.jpg`.

- [x] healthy body designed (pass 1)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint, lifecycle (`KBArwTow_A`, `_D1`..`_D3`), its house model.
- The crown sits between EA's horns and is partly hidden by them at RTS: Max's call whether it wants
  to be taller.
