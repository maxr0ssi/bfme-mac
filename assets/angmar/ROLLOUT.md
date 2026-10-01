# Angmar: building rollout

**Status: 20 measured stubs; palette A2 (Max's pick, 2026-10-01: A "Carn Dum frost" with D's
warm wood, cooled a touch); the citadel designed (pass 4, four frozen tines of the Witch-king's
crown) and built in A2; nothing installed.** Every recipe passes `sagekit validate`. Template:
[`assets/mordor/ROLLOUT.md`](../mordor/ROLLOUT.md); the loop is in
[docs/FACTIONS-PLAN.md](../../docs/FACTIONS-PLAN.md).

## Where to look

Build output is under `build/assets/angmar/` (not in git).

- The palette options on EA's citadel: `_palettes/palette_options.jpg` (round three: EA, A, A2 and
  D; round two, A to D, in `_palettes/palette_options_r2.jpg`; round one, too dark and too alike,
  in `_palettes/palette_options_r1.jpg`). Rows: `board` (the whole citadel)
  and `keep` (the four spires, the horns, the walk).
- The citadel's measurements: `fortress/work/measure.json`; EA's facts in
  [fortress/building.py](fortress/building.py).
- The citadel: shape passes `_review/citadel_v1..v3.jpg`, pass 3 in A2 and A
  `_review/citadel_palettes_v1.jpg`, pass 4 `_review/citadel_v4.jpg` (EA, pass 3 and pass 4 in A2). The design:
  [fortress/README.md](fortress/README.md). A build paints in A2 unless `ANGMAR_PALETTE` says
  otherwise ([`style.py`](style.py)).

## EA's Angmar

KBFortress (the citadel), KBFortressB (walls, towers, expansions, the sanctum) and KBFortressX (the
House of Lamentation, the spikes, the kennel): cool blue-grey stone blocks with iron-framed arrow
slits and rust runs, a slab plinth, dark timber with white frost in its grain (the citadel's horns
and spires), warm orange plank walks, scale shingles with an oily violet-green sheen. EA's fire is
already blue (the citadel's torch cards draw `EXFireTorchSeqBlue`). The Ice Walls upgrade swaps
every master sheet for an `_Ice` copy and shows `ICEWALL`; Ice Munitions shows ice horns
(`ICEMUNITIONS01..04`). Banners: the evil factions' shared `Evil_House_Color_Flag` on `KBHC*`
models (the citadel's `KBHCFortress` with the Banners upgrade), tinted in the player's colour.

## Palette options

Not the Elves (moonsilver, teal enamel on ivory), not Isengard (black, silver, ember), not Mordor
(black, ash, orange, Morgul green), not the Goblins (crimson, bone, iron). Every ramp keeps EA's
value contrast ([`style.py`](style.py) `_curve`: luminance k * x^gamma at EA's own luminance x), so
lights stay light, wood stays wood. Paint in [`paint.py`](paint.py), rects in
[`atlas.py`](atlas.py) and [`atlas_sheets.py`](atlas_sheets.py).

| Option | Reads as |
|---|---|
| A Carn Dum frost | blue-black slate stone, rime-white frost on every light and on the horns, blue slate shingles, icy cyan-blue slits |
| B Witch-king's pall | charcoal stone with dead bone-white lights, ashen bleached boards, violet shingles, cold violet-blue witch-light |
| C Iron and ice | rust-dark iron-brown stone and plates, strong rust, dark boards, frost-white crust on the lights, pale steel-blue edges |
| D Blue fire on grey stone | EA's own, colder: grey-blue stone, warm boards, the shingles' oily sheen kept, rust, EA's blue torch-fire in the slits |
| A2 Carn Dum frost, warm timber | **Max's pick (2026-10-01)**: A with D's warm planks and frost-grained timber ("A without question, but maybe A with the wood of D?") |

## Units

20 stubs from `sagekit new angmar` (the build menu is `AngmarPorterCommandSet`: mill, barracks,
den, Hall of Twilight, forge works, sentry tower, wall hub, fortress).

- **Sentry tower** (`AngmarSentryTower`, slot 8) is a ChildObject of
  `AngmarSentryTower_Independent` in the same file; the scaffolder resolved only parents defined
  elsewhere and drops `_Independent` as a variant, so the tower had no stub.
  `scaffold.local_children` fixes it (no other faction's plan changes).
- **Missing: forge works and mill.** `KBForge`'s body is `BASE`, 1,991 skinned triangles (the
  hill troll works it); `KBMill`'s is `BASE`, 580 skinned (V1 510 and V2 1,309 are static level-ups).
  The scaffolder and the geometry step take static bodies only, so both need a skinned-target path
  in the framework (or a design on the static level-up meshes) before they get recipes.
- **Not a building on its own:** `hallof_twilight_v1` is the Hall of Twilight's level-2 piece
  (V1, shown at level 2, hidden at 3); its level-3 piece V2 (1,753) has no stub.
  `fortress_house_of_healing` is the House of Lamentation upgrade (EA's tag
  `ModuleTag_HouseOfHealingDraw`).
- No effect mesh, door or chain got a stub: the doors (`KBHallDoors_CL`, `KBForgeDoor`,
  `KBFDoor_CLS`) were left out, and the ice meshes are inside `KBFortress` (see its docstring).
- `barracks` pins `KBHall_Normal.tga` -> `KBHalH_Normal.tga` (`Building.texture_names` now honours a
  pin for a normal map EA named off the `_NRM` pattern).

## Ownership (`sagekit owners angmar`)

- No stub's model or sheet is drawn by another faction: no own models needed.
- The citadel draws the Dwarven bib `DBFortress_Bib` (sheet `GBWall_Bib`, Dwarves, Men, Elves);
  the wall segment draws `GBWall_Rubble` (everyone's). Neither may be recoloured in place.
- `WUPorter_SKN`: Angmar keeps EA's orc porter; the Goblins, Isengard and Mordor ship their own
  copies (`WUBuilder_SKN`, `IUBuilder_SKN`, `MUBuilder_SKN`), so nothing of Angmar's changes.
- `DolGolGate` (Mordor's battle tower sheet) shows up only through Carn Dum's map catwalks
  (civilian), not an Angmar building.

## Open

1. ~~Max's pick of a palette~~: A2 (2026-10-01).
2. Production sheet tables (KBHall, KBDen, KBTemple, KBForge, KBMill, KBBtlTwr) in
   `atlas_sheets.py` before `sagekit sheets angmar` runs; tables for the `_Ice` sheets' ice crust.
3. The forge works and the mill (skinned bodies).
4. `house_template = 'KBHCBtlTwr'` for the walls and expansions: unchecked.
