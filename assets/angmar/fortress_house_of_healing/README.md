# Angmar House of Lamentation (`AngmarFortressCitadel`)

Model `KBFHoLa`, mesh `KBFHOLA`, own texture `KBFortressN.tga` (from `KBFortressX.tga`). The citadel's
`UPGRADE_HOUSE_OF_HEALING` add-on (EA reused the tag `ModuleTag_HouseOfHealingDraw`): EA's house on
the curtain over the gate, a round drum (z 40..103.5) with a curved wing round both sides roofed at
z 78, kept whole. New pieces come from the add-ons' shared pieces
([`../shapes_addons.py`](../shapes_addons.py)). EA's facts are in [`building.py`](building.py).

## What changed

- **Frozen captives** (the bold mass): on the wing's roofs either side of the drum, four thralls
  frozen standing into pillars of ice crystals (15 and 17 tall), their heads and arms raised in
  lament breaking out of the crystal, shackles on their wrists.
- **The lament-fire**: a cairn of black stone and ice on the drum's top (r 4.6, to z 113.5), the
  cold fire burning out of its crater.
- **Fire** (`fire_points`, 1): `coldfire` in the cairn (55, 0, 113).

## Kept clear

- EA's night windows (`N_WINDOW`), its horns, its icicle drips, its mist (another Draw).
- No new face crosses the citadel's new faces; new faces keep x >= 47 above z 85.
- **Open, not ours to fix**: EA's drum crosses the citadel's +X tine (295 faces at x 40.7..44,
  z 90..120: the tine's frozen tip stands against the drum's back). It needs a change to the
  citadel (fortress/crown.py), see the rollout notes.

## Status

Pass 1, shape preview only (not built, not installed): 754 -> 1,992 triangles, height and footprint
unchanged, 9/9 preview checks. Review sheet: `build/assets/angmar/_review/addons_v1.jpg` (in place
on our citadel).

- [x] healthy body designed (pass 1)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint, lifecycle (`KBFHoLa_A`, `_D1`, `_D2`).
- The +X tine's crossing (citadel).
