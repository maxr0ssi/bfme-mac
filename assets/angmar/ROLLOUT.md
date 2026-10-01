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
- `sagekit sheets angmar` recolours 96 sheets: no other faction draws any of them. Left out:
  `KBFoundation` and the four `KBMain*` (Men's Fornost draws them) and EA's placeholders `dummy`,
  `low`, `med` (style `sheet_skip`). `KBFortressX_D1` is `KBFortressB`'s damaged sheet (B's layout;
  the walls' damaged models draw it), so it paints from B's table. `KBFortress_Bib*` (no model draws
  them; the citadel shows the Dwarven bib) paint as ground, not through the citadel's atlas.
- `DolGolGate` (Mordor's battle tower sheet) shows up only through Carn Dum's map catwalks
  (civilian), not an Angmar building.

## Walls (shape previews, 2026-10-01; the gate in pass 3)

wall_segment, wall_hub, wall_gate, wall_end, wall_postern, wall_tower, wall_trebuchet and
fortress_wall_hub, designed from one set of pieces ([`shapes_walls.py`](shapes_walls.py)) so they
tile as one frozen wall. Review: `_review/walls_v3.jpg` (v1 and v2 have the earlier gates): the
citadel for reference, the line hub - segment - gate - segment - hub, then each piece EA | ours at
rts and close, fire marked.

- **One battlement**: Carn Dum merlons (stone teeth rising to an off-centre point, left and right
  in turn, the slopes rimed) at one pitch on every walk and parapet; a run of segments keeps the
  beat through its joints. The gate's pylons and the postern carry none (no walk).
- **Icicles under the walk**: a corbelled string course with a rime crust and icicles on the
  segments, the wall end and the trebuchet; icicles under EA's own parapet overhangs on the hubs
  and the tower.
- **Ice at the feet**: crystal drifts leaning up the faces, inside EA's footprints (a segment has
  1.9 beyond its face), a black stone shard among them.
- **Peaks**: no new spikes. The hubs and the tower already wear a crown of three EA horns; their
  points are frozen as the citadel's tines' (`freeze`: ice casing, ragged frost line, rime,
  crystals). The segments' horn pairs and the gate's great horns stay plain.
- **Fire**: cold braziers (`coldflame`) on the hubs' roofs (1), the gate's pylons (2), the
  tower's walk (2) and the trebuchet's platform (2).
- **The gate** (pass 2, the coordinator's review: the pass-1 grille hung like a sign over the
  opening; pass 3: the keystone set in, the lintel crenellated): a stone lintel from pylon to pylon
  just over the door, its rimed top peaked in the middle and carrying the walls' merlons, a barbed
  iron portcullis in each mouth of the gateway raised into it (thick bars, rimed crossbars, steel
  teeth to z ~59), a pointed keystone set into the lintel with the Witch-king's sigil inset (kite
  plate, faceless helm with a cold eye-slit, the crown's seven steel tines); the door's slot (it
  sinks into the ground to open) kept clear. The postern has the portcullis in little in each
  porch. Review `_review/walls_v3.jpg`.
- **Ice Walls**: every `ICEWALL` shell kept, out of the bakes; each piece's `KBFortressB_Ice`
  swap gets its own copy (`KBFortress?_Ice`) by the existing variant path; the crystals' feet pass
  through the shells as EA's ribs and plinths do.
- Triangles (EA -> ours): segment 380 -> 1,160, hub 352 -> 1,818, gate 1,036 -> 4,288, end
  1,099 -> 2,611, postern 422 -> 1,238, tower 1,287 -> 2,735, trebuchet 503 -> 1,977, fortress
  hub 436 -> 2,208. Heights +0..1 %, footprints unchanged, 9/9 preview checks each.

## Add-ons group: the citadel's upgrades and the two towers (pass 1, shape previews, 2026-10-01)

fortress_house_of_healing (the House of Lamentation), fortress_sanctum, fortress_spikes,
battle_tower and sentry_tower. Shared pieces: [`shapes_addons.py`](shapes_addons.py) (the forged
tine at any size with a scaled frozen tip, the cairn round a cold fire, the frozen captive, frozen
spikes read from EA's mesh at design time). Review: `_review/addons_v1.jpg` (the citadel for
reference, all of them on our citadel, then each EA's | ours in place at rts and close, fire marked;
the upgrades in the citadel's coordinates, the battle tower on EA's pads from `bases\fortress_angmar`).
One bold mass each, no new spires:

| Building | Key new mass | Triangles | Height | Fire |
|---|---|---|---|---|
| [fortress_house_of_healing](fortress_house_of_healing/README.md) | four thralls frozen into ice pillars on the wing roofs, arms raised in lament; a cairn on the drum | 754 -> 1,992 | 0 % | coldfire |
| [fortress_sanctum](fortress_sanctum/README.md) | a collar of six ice blooms round its waist, level with the tines' frozen tips | 1,452 -> 2,262 | 0 % | 3 coldflame |
| [fortress_spikes](fortress_spikes/README.md) | every tall spike (21) frozen from half its height, the casing following its own section | 1,326 -> 3,657 | +2.6 % | none |
| [battle_tower](battle_tower/README.md) | three small frozen tines on the lantern's roof between EA's horns, round a cairn | 1,168 -> 3,334 | 0 % | coldfire |
| [sentry_tower](sentry_tower/README.md) | three frozen tines on the flat roof between EA's horns, round a cairn | 1,527 -> 3,681 | 0 % | coldfire |

No new face of the group crosses the citadel's new faces (checked with every add-on in place and the
battle tower on all seven pads). EA's own bodies do cross the citadel's pass-4 pieces, which only
the citadel can fix (fortress/ is not the group's to change):

- the House's drum and the +X tine's frozen tip (295 faces, x 40.7..44, z 90..120);
- the sanctum's shaft and the cairn (180 faces), and the citadel's `coldfire` (0, 0, 51.9) burns
  inside the shaft once the sanctum stands: a sub-object hidden on `UPGRADE_IVORY_TOWER` (as EA's
  `SubObjectsUpgrade`) or a fire Draw state for it would need the framework;
- the spikes' clumps and the wall-foot ice clusters and fissures (1,009 of EA's faces);
- a battle tower on the S or N pad and the two banners (and on S the fissure kerb).

## Army group: barracks, den, kennel, Hall of Twilight, catapult works (pass 2, shape previews, 2026-10-01)

Shared pieces: [`shapes_army.py`](shapes_army.py): the thrall-master's gantry with frozen cages, the
cold fire pit, the warg skull, the warg-tusk arch, menhirs with great runes and the altar, the
hoardings, the gantry and the ice boulders. EA's roof spikes are frozen with the walls group's
`freeze` ([`shapes_walls.py`](shapes_walls.py)). Bone is `trim` (the palette's pale slate-to-rime
ramp), so it reads apart from the ice. Review: `_review/army_v2.jpg` (pass 1: `army_v1.jpg`): the
citadel for reference, then each building EA's | ours at rts and close, fire marked. One mass each
that reads at RTS, each its own story, no new spires:

| Building | Key new mass | Triangles | Height | Fire |
|---|---|---|---|---|
| [barracks](barracks/README.md) | the thrall-master's gantry across the front, as tall as the eaves, two great cages of frozen captives; EA's six roof spikes frozen | 918 -> 3,356 | 0 % | 2 coldflame (braziers at its feet) |
| [den](den/README.md) | the cave becomes the mouth of a great frozen warg skull, jaw on the ground, fangs of ice | 2,256 -> 3,678 | 0 % | coldflame (its throat) |
| [kennel](kennel/README.md) | two warg tusks crossing over the gate, iron-banded, ice teeth | 645 -> 1,387 | 0 % | none |
| [hallof_twilight](hallof_twilight/README.md) | a ring of five broad menhirs, a great rune glowing on each; the altar's crater | 784 -> 2,099 | 0 % | coldfire (the crater) |
| [catapult](catapult/README.md) | frozen timber hoardings round the top; a gantry over a heap of ice boulders; the freezing pit | 397 -> 4,002 | 0 % | coldflame (the pit) |

- The level pieces stay EA's and clear: the renders and bakes show level 1 (`bake_hidden`
  `V1`/`V2`). The Hall's design stands on `BASE`, clear of `TOP_1`, `V1` and `V2` at every level, so
  `hallof_twilight_v1` stays EA's.
- **Not done: the Hall's tower horns.** They belong to the level pieces (`TOP_1`, `V1`, `V2`), at
  the same places but 4.4 higher at each level. Freezing them needs a recipe per level piece; one
  casing on `BASE` would cut through the horn on two of the three levels.
- The kennel and the catapult stand on the citadel's pads (local -X toward the citadel). Our faces
  are on their outer halves, 125 or more from the citadel's centre, clear of its new faces (the
  bastion clusters reach r 107).
- `facet_islands = 8` on the den and the kennel: their first builds' unwraps overlapped.

## Open

1. ~~Max's pick of a palette~~: A2 (2026-10-01).
2. ~~Production sheet tables~~ (2026-10-01): KBHall, KBDen, KBTemple, KBForge, KBMill, KBBtlTwr,
   every bib, the `_Ice` crusts and the snow sheets have tables in `atlas_sheets.py`; EA vs A2 on
   EA's buildings in `_review/sheets_v1.jpg`. Rust stays warm and the ground is a cold earth on
   them (the citadel's KBFortress paint is unchanged, bit for bit).
3. The forge works and the mill (skinned bodies).
4. `house_template = 'KBHCBtlTwr'` for the walls and expansions: unchecked.
