# Angmar sanctum (`AngmarFortressCitadel`)

Model `KBFSanctum`, mesh `KBFSANCTUM`, own texture `KBFortressP.tga` (from `KBFortressB.tga`). The
citadel's `UPGRADE_IVORY_TOWER` add-on (`ModuleTag_SanctumDraw`): EA's sorcerer's tower in the middle
of the well (to z 175.4), kept whole. New pieces come from the Angmar kit's ice. EA's facts are in
[`building.py`](building.py).

## What changed

- **An ice collar** (the bold mass): six blooms of ice crystals burst up between the fins over the
  skirt (the ledge at z 98, r 12.2), round the tower's waist under the crown, the big three to
  z ~118: level with the frozen tips of the citadel's four tines round it, so the tower reads as
  frozen by the same sorcery.
- **Fire** (`fire_points`, 3): `coldflame` in the craters of the three big blooms (z 101.9).
- Tried and cut in pass 1: blooms on the skirt's sloping roof (read as small tufts, pushed out of
  EA's footprint); a collar of shards at the foot (hidden by the curtain at RTS, only added to the
  cairn's crossing).

## Kept clear

- EA's eye bones (`EYEBONE` z 173.9, `EYEBONE01` z 147.7: AngSanctumCharge, the weapon) and the
  crown: nothing new above z 118.
- No new face crosses the citadel's new faces.
- **Open, not ours to fix**: EA's shaft stands where the citadel's cairn is (180 faces cross, the
  cairn's shards out through the shaft at z 4..57), and the citadel's `coldfire` (0, 0, 51.9) burns
  inside the shaft once the sanctum is built. See the rollout notes.

## Status

Pass 1, shape preview only (not built, not installed): 1,452 -> 2,262 triangles, height and
footprint unchanged, 9/9 preview checks. Review sheet: `build/assets/angmar/_review/addons_v1.jpg`.

- [x] healthy body designed (pass 1)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint, lifecycle (`KBFSanctum_A`, `_D1`..`_D3`).
- The cairn and the cold fire inside the shaft (citadel).
