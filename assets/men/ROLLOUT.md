# Men of the West (Gondor): building rollout plan

**Status (2026-09-27 night): done and installed.** Max approved the citadel and asked to
"finish all of the men buildings"; six design agents built the 44 recipes by the groups below,
then the integration pass recoloured the sheets (wood, thatch, coals, cloth and slate keep EA's
colours), built the house-colour models (`house_template` GBHCBtlTwrM; add-on banners in models
of their own) and rebuilt everything: every build ALL PASS, 394.7 of 512 MB. Poster:
`build/assets/men/men_poster.jpg`. Installed with `sagekit install men`; Max's in-game check
pending. The plan below is kept as written, with the framework items marked done.
The Elven equivalent is [`assets/elves/ROLLOUT.md`](../elves/ROLLOUT.md); the loop and the
lessons are in [docs/FACTIONS-PLAN.md](../../docs/FACTIONS-PLAN.md).

## Where to look

- Style board, EA's Men buildings as they are (the "before"):
  [`build/assets/men/_board/men_board.jpg`](../../build/assets/men/_board/men_board.jpg); the level-3
  row shows the GBVet level-up meshes. Tiles: `build/assets/men/_board/out/ea_*.png`.
- Each stub's docstring: EA's facts, the target, lifecycle models, house colour, and the measured
  bands, walls, heads and openings (`build/assets/men/<building>/work/measure.json`).
- The bar for every brief: the Dwarven before/after renders
  (`build/assets/dwarves/{fortress,citadel,barracks,statue,wall_gate}/renders/compare_*.png`) and the
  approved citadel pilot. Keep EA's detailed body and enrich it; never strip it.

## Units

31 stubs are in the registry and pass `sagekit validate` (198 MB of the 256 MB budget, citadel
included): the 26 of the first pass and, since the framework pass of 2026-09-27, the five that
were held back (below). The optional chained wall stubs and the level-up meshes come on top.

Scaffolder picks checked by hand (the stubs say so in their docstrings). Since the framework pass
`sagekit new men` makes every one of these picks itself:

| Stub | Scaffolder | Fixed to | Why |
|---|---|---|---|
| `wall_tower` | `BOX01` | `GBFARTOWA` | BOX01 is the wall stub under the tower (the segment's shape); the tower is GBFARTOWA |
| `wall_hub` | source `GBWallUpgrdN`, `GBFORTRESS02` | source `GBWallRmprtN`, `OBJECT03` | GBWallRmprtN is the player-placed hub (MenWallHubSmall) and fell under the 100-triangle rule (94); GBFORTRESS02 is a wall stub |
| `wall_hub_upgradeable` | (none) | `GBWallUpgrdN` / `OBJECT03` | the wall plot that upgrades replace; its hub is the same mesh as wall_hub's |
| `fortress_wall_hub` | `BOX01` | `OBJECT03` | BOX01 is the wall stub towards the citadel |
| `workshop` | `GBWORKSHOP1` | kept | V1HIDE is the level-1 yard |
| `farm` | (missed) | `GBFarm_SKN` / `GBFARM` | its Draw lives in `structures\farminterface.ini`, outside the Men folder |
| `statue` | (missed) | `GPHealstue` / `GPHEALSTUE` | painted from the unit sheet `GUHeroStat`, which the building-sheet filter drops |
| `fortress_oil_guy` | `own_textures` keyed `gbfortress1.tga` | `GBFortress1.tga` -> `GBFortressP.tga` | the lower-case key missed the atlas, so its texture fell back to the citadel's `GBFortressH` |

## Framework items before fan-out

Fix these in one framework pass before the design agents start. The framework stays frozen
while they run. **Items 1, 2, 3 and 6 are done (2026-09-27); 5 is checked; 4 is Max's.** What
changed is under each item; the engine side is in [docs/ART.md](../../docs/ART.md).

1. **Build variations.** Every fortress expansion has two bodies in one Draw module
   (`BUILD_VARIATION_ONE` / `_TWO`: GBFARTOWA/B, GBFDOTOWA/B, GBFTRTOWA/B). `lifecycle.plan` takes
   every model the covered Draw shows, so the A recipe would rebuild B's models with A's design
   and ship them under EA's names. House draws of our own would also show for both variations.
   Needed: a recipe per variation whose covered models are its own family, and house draws
   conditioned on the variation flag.
   *Done.* A recipe owns only its variation's states (`Building.own_states`,
   `formats/ini.py variation_states`: states naming its `BUILD_VARIATION_*` flag, and flagless
   ones showing no other variation's model; the flag is read from the states showing `source`, or
   set with `variation = ...`). Derived models, `lifecycle.plan`, variants, own-model repoints,
   ownership and `inventory` follow it. A house model of our own is drawn `Model = None` by
   default and per variation flag except in its own variation (the A recipe's also by default, as
   EA's default shows A), and its hidden lifecycle states keep the flag
   (`[BUILD_VARIATION_TWO REALLYDAMAGED]`), so each outscores the other in the engine's pick.
2. **INIs outside `MenStyle.ini_dir`.** `GondorFarm` is a ChildObject of `FarmInterface`
   (`goodfaction\structures\farminterface.ini`), so `Building.objects()` finds no Draw module for
   the farm: no swaps, lifecycle or house step. Arnor's objects (`structures\arnor\`) draw the
   same models. They get our model files shipped under EA's names, but none of the INI work: own
   models (`own_model`), house draws of our own (`HOUSE_DRAW`), variant swaps and hidden banners.
   Decide whether Arnor matters (LAN is Men-only unless Max plays Arnor); if it does,
   `ini_dir` becomes a list.
   *Done: Arnor gets the redesign.* `Style.ini_dirs()` takes `ini_dir` (a folder, a file or a
   list) plus the structure folder of each group that counts as the faction's
   (`ownership.FOLLOWS`: `structures\arnor\` for the Men), so every Men recipe's INI work now
   reaches Arnor's objects too (house copies, swaps, repoints, hidden banners); Arnor already
   counted as Men for ownership (`FOLLOWS`, and `Arnor*` objects by name). A ChildObject brings
   the Draw modules it inherits from a parent defined elsewhere (`Install.object_draws`): the farm
   now finds FarmInterface's Draw in `farminterface.ini` (edits go there), its lifecycle
   (GBFarm_A, _D1-3, _WB), its snow variant and GBHCFarm in GondorFarm's own module.
3. **Ownership false positive.** `recipe_problems` reports every model shown beside the source by
   any object. For the sentry tower that includes `GondorBaseDefenceFoundation`'s Draw2, which
   shows `OBBFoundationX`: an empty model (no meshes) shared by five factions. The scaffolder then
   set `own_model = "GBBtlTwrM2"`, which would hide the redesign from that plot and from Arnor.
   GBBtlTwrM itself is Men-only, so the sentry tower should ship in place.
   *Done.* `recipe_problems` counts only the models the recipe ships (its covered Draws' own
   states, which also drops Blue Mountains' `bb_tower03` beside GBFARTOWA) and none without
   meshes (`ownership.empty_model`); `lifecycle.plan` skips empty models too. The sentry tower
   stub ships in place.
4. **Budget (done 2026-09-27).** RotWK runs with 4 GB, and `budget_mb` is 512 for every
   faction. Normal maps are now counted as the game holds them (a standard recipe is 8.0 MB, the
   citadel 32 MB). Men: 280 of 512 MB with all 32 recipes, so the 12 level-up meshes (about
   100 MB) fit too.
5. **Numenor stonework** (a citadel upgrade with no model) swaps `GBFortress1.tga` for
   `GBFortress1_U.tga` on every wall, expansion and add-on. `variants()` gives each recipe an own
   `_U`. The postern's wall draw swaps `GBWall.tga` for `GBFortress1_U.tga` under construction
   (a cross-sheet swap). Check the variant names in the first wall build.
   *Checked.* Every recipe on GBFortress1 gets `<own>_U` (`GBFortressN_U.tga`, ...). The GBWall
   recipes (wall_segment, whose GBWallN the postern draws too, and wall_end) get
   `GBWalHFortress1_U.tga` / `GBWalXFortress1_U.tga`: the name is fine (an INI swap, no length
   rule), but the paint step carries EA's stonework over as the ratio of GBFortress1_U to GBWall
   at the wall's UVs, two unrelated sheets. Left for the walls group's first build to judge
   (new faces already use the master's `_U` ratio).
6. **Scaffolder fixes** to carry back into `sagekit/scaffold*.py` (so `sagekit new men --write`
   stays right): the 100-triangle rule versus 94-triangle hubs, `healthy()` ignoring the second
   build variation, the case of `own_textures` keys, unit-sheet bodies (statues) and inherited
   Draw modules (ChildObject).
   *Done.* Wall pieces (and the fortress wall hub) take 50+ triangles and their tallest mesh
   (OBJECT03, GBFARTOWA, not the wall stubs); two objects of one role take the object's name
   (`wall_hub_upgradeable`); `healthy()` returns one body per build variation (`<name>_b`); a mesh
   the object's SubObjectsUpgrades both show and hide (the farm's V1/V2) is not the body; a
   STRUCTURE with no building-sheet mesh may use a unit sheet (the statue's GUHeroStat); a
   ChildObject brings its inherited Draws and its own house model; one spelling per sheet
   (`GBFortress1.tga`), and `Building.texture_names` matches `own_textures` keys in any case; an
   existing recipe keeps its own texture name (the Dwarven rerun used to run out of names).

### Held back until the framework pass (now stubs)

| Unit | EA model / target | Was blocked by | Notes |
|---|---|---|---|
| arrow_tower | `GBFARTOWA` / `GBFARTOWA` (218) | 1, ownership | Blue Mountains' `EreaborGarrisonableTowerExt` (counted as Dwarven) draws GBFARTOWA and GBFARTOWB: `own_model = "GBFARTOWA2"`. Validate fails until item 1 is fixed |
| arrow_tower_b | `GBFARTOWB` / `GBFARTOWB` (368) | 1, ownership | also needs its own model, e.g. `GBFARTOWB2` |
| garrison_tower_b | `GBFDOTOWB` / `GBFDOTOWB` (466) | 1 | Men-only |
| trebuchet_b | `GBFTRTOWB` / `GBFTRTOWB` (206) | 1 | Men-only |
| sentry_tower | `GBBtlTwrM` / `GBBTLTWRMINI01` (486) | 3 | drop `own_model` |

`sagekit new men --write` wrote and measured all five on 2026-09-27 (arrow_tower
`own_model = "GBFARTOWA2"`, arrow_tower_b `"GBFARTOWB2"`, sentry_tower in place); validate
passes. The A and B recipes of a pair may be built and designed independently now.

## Banners

Max: "some, not loads". The caps below count player-colour cloth pieces per building, including
EA's own house models where the redesign keeps them. Walls carry none except the gate. The
fortress add-ons take at most one each (the Elven rule).

## 1. Fortress add-ons and upgrades

These parts are drawn by `MenFortressCitadel`, which carries `GBHCFortress`. Each part is shown
under its upgrade flag, so every stub has `parts = (<its tag>,)`. They carry no night meshes (any
lanterns stay dark). Wait for the citadel pilot's pieces; its folder stays the pilot's.

| Stub | EA model / target | Upgrade | Constraints | Banners |
|---|---|---|---|---|
| fortress_oil | `GBFBOil` / `GBFBOIL` (154) | UPGRADE_BOILING_OIL | cauldrons ring the keep; the steam bones (STEAM_BONE02-09) keep EA's positions; built with animation `GBFBoil_ASKL` | 0 |
| fortress_oil_guy | `GBFBOil_SKN` / `GBFBOILPOT` (164) | UPGRADE_BOILING_OIL | the pot a skinned man-at-arms tips (animations IDLA/ATKA); the body is raised off the ground, so keep the pivot; no lifecycle models | 0 |
| fortress_ivory_tower | `GBFITower` / `GBFITOWER` (402) | UPGRADE_IVORY_TOWER | the tallest piece (z 11.6-177.9): watch `max_z_growth`; animation `GBFITower_ASKL`, and PACKING/UNPACKING states | 1 |
| fortress_house_of_healing | `GBFHeal` / `GBFHEAL` (552) | UPGRADE_HOUSE_OF_HEALING | its facade faces outwards; animation `GBFHeal_ASKL` | 1 |

The citadel door (`GBFDoor_DRC`, 16-triangle leaves) and `GBFFLAMING` inside GBFortress belong
to the pilot.

**Shared first:** `assets/men/fortress_ivory_tower/citadel_motifs.py`: the pilot's cornice,
corbel course, White Tree relief and finial as functions, so the add-ons match the citadel
without importing its recipe.

## 2. Expansions

These sit on the citadel's pads, are drawn by their own objects and have no house model of
their own (`HOUSE_DRAW`). They carry no night meshes. Numenor stonework applies (item 5).

| Stub | EA model / target | Constraints | Banners |
|---|---|---|---|
| garrison_tower | `GBFDOTOWA` / `GBFDOTOWA` (430) | variation A only (item 1); nine openings measured: keep the gate arch clear | 1 |
| trebuchet | `GBFTRTOWA` / `GBFTRTOWA` (108) | variation A (item 1); the open platform (P1 is its trebuchet bone): keep the top clear | 0 |
| fortress_wall_hub | `GBGFWHub` / `OBJECT03` (94) | the hub tower, the same mesh as wall_hub's: subclass `WallHub` as the Elves did. The mesh stands on a bone (z -80.7..17.4 in mesh coordinates). BOX01 is a wall stub (optional chain) | 0 |
| arrow_tower, arrow_tower_b, garrison_tower_b, trebuchet_b | `GBFARTOWA`, `GBFARTOWB`, `GBFDOTOWB`, `GBFTRTOWB` | the arrow towers ship own models (Blue Mountains draws them); each B shares its A's pad.py and dome.py | 1, 1, 1, 0 |

**Shared first:** `assets/men/wall_hub/dome.py`, created by the walls group before anyone fans
out. It holds the octagonal drum, ribbed dome and spire that EA repeats on the wall hub, the
upgradeable plot, the wall tower, the fortress wall hub, and both arrow and garrison towers. Also
`assets/men/garrison_tower/pad.py`: the pad base, arch and parapet shared by the A and B variations.

## 3. Walls and gate

These objects are in `campsandcastles.ini`. Every segment tiles the same slot (7.5 x 38, 49.5
high). Most pieces have no house model of their own (`HOUSE_DRAW`) and no night meshes. EA's
rubble `GBWall_Rubble` is drawn by four other factions: leave it EA's. The bibs `GBWallN_Bib` and
`GBWallRmprtNBib` are drawn by the Dwarves too; don't touch them.

| Stub | EA model / target | Constraints | Banners |
|---|---|---|---|
| wall_segment | `GBWallN` / `BOX01` (276) | also the postern's wall (MenWallPosternGateSmall draws GBWallN); the placement cursor `GBWallN_CUR` goes in `also_derived`, as for the Dwarves and Elves; sheet `GBWall` (the Elves draw it too; own texture pinned) | 0 |
| wall_end | `GBWallNE` / `GBWALLNE` (554) | cliff cap; z -46..49.5 (it reaches down the cliff); shares GBWallN_D3 | 0 |
| wall_hub | `GBWallRmprtN` / `OBJECT03` (94) | the player-placed hub; stands on a bone (mesh z -80.7..17.4); segments meet it from any side, so keep its faces in their planes | 0 |
| wall_hub_upgradeable | `GBWallUpgrdN` / `OBJECT03` (94) | subclass `WallHub`; GBFORTRESS01/02 are wall stubs (optional chains); replaced by the gate, postern, tower and trebuchet upgrades | 0 |
| wall_gate | `GBWallGateN` / `GBFDOTOWA` (580) | the gate leaves BOX06-09 are animated (`GBWallGateN_SKL`, OP/OPN): don't build into their swing (x -5..5, y -40..40, z 0..40) | 2 |
| wall_postern | `GBWallPGN` / `GBFDOTOWA01` (136) | a door arch drawn over the segment (`ModuleTag_DoorDraw`, `parts`); it loops `GBWallrampart` | 0 |
| wall_tower | `GBWallTwrN` / `GBFARTOWA` (238) | the tower mesh is named like the arrow tower's but is a different mesh (238 vs 218 triangles): design both from dome.py. BOX01 is the segment stub (optional chain reusing wall.py) | 1 |
| wall_trebuchet | `GBWallTrebN` / `GBFTRTOWA` (144) | an open platform (P1 is the trebuchet's bone) | 0 |

**Shared first:** `assets/men/wall_segment/wall.py` (coping, crenellation rhythm, string course
and battered foot, used by the segment, end, postern, stubs and gate), and
`assets/men/wall_hub/dome.py` (above). Test both in a real build before fanning out: kit bugs
cost the Elves the most time.

## 4. Production and economy

These are `_SKN` models whose units animate (keep their clearances). Each has EA's house model and
night windows. All of them except the market and stoneworks level up. The level-up meshes (V1 at
level 2, V2 at level 3) are painted from the shared **GBVet** sheet (Men-only), and V1HIDE/V2HIDE
are level-1 stand-ins. Leave the level-up meshes to the faction sheet recolour, or chain them
(`base = "men/<building>"`, like the Dwarven archery walls). Mind item 4.

| Stub | EA model / target | Level-up meshes | Constraints | Banners |
|---|---|---|---|---|
| barracks | `GBBarracks_SKN` / `BARRACKS` (1452) | V1 216, V2 1994 | OBJECT01 (300) is a second body on the sheet; SPEAR prop; GBHCBarracks | 3 |
| archer_range | `GBArcheryN_SKN` / `ARCHERY` (913) | V1 379, V2 797, ARCHERY_HIGH_ON 236 | the body hangs on a raised bone; animated pulley (skinned, own sheet `gbarcheryn_a`); targets on GUArcher; DXT5 cut-outs; GBHCArcheryN | 2 |
| stable | `GBStable_SKN` / `GBSTABLE` (2186) | V1 354, V2 806 (+V2FLAG) | horses animate in the stalls; the Elven stable is drawn from Gondor's GBStable sheets (own texture pinned); GBHCStable | 2 |
| forge | `GBBlkSmith_SKN` / `GBBLKSMITH` (483) | V1 298, V2 376 | smith animation, fire plane, weapon racks (PG02); GBHCBlkSmith | 1 |
| workshop | `GBWorkshop` / `GBWORKSHOP1` (732) | V1 604, V2 1304 | V1HIDE (236) is the level-1 yard on the body's sheet; GBHCWorkshop | 2 |
| farm | `GBFarm_SKN` / `GBFARM` (228) | V1 666 (walls), V2 341 (pillars), both on GBFarm | skinned crops and peasant; DXT5 cut-outs; GBHCFarm is drawn by GondorFarm's own module | 1 |
| market_place | `GBMarket_SKN` / `MARKET_STRUCTUR` (2834) | - | the densest body; vendor, woman and chicken animate; awnings are cut-outs (DXT5); GBHCMarket | 2 |
| stone_maker | `GBStoneMK_SKN` / `GBSTONEMK` (1298) | - | no normal map on its sheet; the crane, pulleys and hooks are separate animated meshes (`GBStoneMK_SKL` IDLA): don't cover their paths; GBHCstoneMk | 1 |

**Shared first:** `assets/men/barracks/motifs.py` (window surrounds, roof ridges and eaves,
cornice, banner mounts, White Tree roundel, sized from the measured bands) and
`assets/men/barracks/levels.py` (the chained level-up recipe pattern, if any level-up mesh is
redesigned).

## 5. Towers and specials

| Stub | EA model / target | Constraints | Banners |
|---|---|---|---|
| keep | `GondorKeep`: `GBBtlTwrs` / `OBJ0` (1022) | the battle tower; tall round tower with a dome (z 0.3-116); N_WINDOW night; GBHCBtlTwrS | 2 |
| sentry_tower | `GBBtlTwrM` / `GBBTLTWRMINI01` (486) | ships in place; also drawn on the base-defence plot (editor state); GBHCBtlTwrM | 1 |
| well | `GBWell` / `GBWELL` (752) | water meshes (SPOUT03, RBWELLWATER01 and a splash on Elven-shared sheets) stay EA's; heal effect; GBHCWell | 0 |
| statue | `GondorStatue`, `GondorHeroStatue`: `GPHealstue` / `GPHEALSTUE` (550) | a figure on a plinth painted from the unit sheet GUHeroStat (own texture pinned `GUHeroStaH`); plan pedestal work, not re-carving; GPHCHealstue | 1 |

**Shared first:** `assets/men/keep/tower.py` (round drum courses, ribbed dome and lantern, window
hoods), used by the keep and the sentry tower.

## Order

1. ~~Framework pass (items 1-6), then `sagekit new men --write` for the held-back stubs.~~ Done
   2026-09-27 (item 4, the budget, is Max's call).
2. After the pilot is approved: the walls group writes `wall.py` and `dome.py` and builds one
   segment and one hub to test the kit.
3. Four or five agents in parallel by the groups above, in draft mode, with the framework frozen.
4. Integration pass: `sagekit house men`, the poster, the lifecycle review; then Max reviews.
