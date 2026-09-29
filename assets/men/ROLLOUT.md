# Men of the West (Gondor): building rollout

**Status: installed.** 44 recipes (32 buildings and 12 level-up meshes), 394.7 of 512 MB.
Arnor's objects draw the same models and get the redesign too. The citadel is
[fortress](fortress/README.md). The Elven equivalent is [`assets/elves/ROLLOUT.md`](../elves/ROLLOUT.md);
the loop is in [docs/FACTIONS-PLAN.md](../../docs/FACTIONS-PLAN.md).

## Where to look

Build output is under `build/assets/men/` (not in git; each player builds their own).

- Poster: `build/assets/men/men_poster.jpg`.
- Style board, EA's Men buildings as they are: `build/assets/men/_board/men_board.jpg` (the
  level-3 row shows the GBVet level-up meshes). Tiles: `build/assets/men/_board/out/ea_*.png`.
- Each recipe's docstring: EA's facts, the target, lifecycle models, house colour, and the
  measured bands, walls, heads and openings (`build/assets/men/<building>/work/measure.json`).

## Integration

The faction sheet recolour keeps EA's colours on wood, thatch, coals, cloth and slate. House
colour uses `house_template = "GBHCBtlTwrM"`; add-on banners get house models of their own.

## Scaffolder picks fixed by hand

`sagekit new men` now makes each of these picks itself:

| Recipe | Scaffolder | Fixed to | Why |
|---|---|---|---|
| `wall_tower` | `BOX01` | `GBFARTOWA` | BOX01 is the wall stub under the tower (the segment's shape); the tower is GBFARTOWA |
| `wall_hub` | source `GBWallUpgrdN`, `GBFORTRESS02` | source `GBWallRmprtN`, `OBJECT03` | GBWallRmprtN is the player-placed hub (MenWallHubSmall) and fell under the 100-triangle rule (94); GBFORTRESS02 is a wall stub |
| `wall_hub_upgradeable` | (none) | `GBWallUpgrdN` / `OBJECT03` | the wall plot that upgrades replace; its hub is the same mesh as wall_hub's |
| `fortress_wall_hub` | `BOX01` | `OBJECT03` | BOX01 is the wall stub towards the citadel |
| `workshop` | `GBWORKSHOP1` | kept | V1HIDE is the level-1 yard |
| `farm` | (missed) | `GBFarm_SKN` / `GBFARM` | its Draw lives in `structures\farminterface.ini`, outside the Men folder |
| `statue` | (missed) | `GPHealstue` / `GPHEALSTUE` | painted from the unit sheet `GUHeroStat`, which the building-sheet filter drops |
| `fortress_oil_guy` | `own_textures` keyed `gbfortress1.tga` | `GBFortress1.tga` -> `GBFortressP.tga` | the lower-case key missed the atlas, so its texture fell back to the citadel's `GBFortressH` |

## Framework items

All done; the engine side is in [docs/ART.md](../../docs/ART.md).

1. **Build variations.** A recipe owns only its variation's states (`Building.own_states`,
   `formats/ini.py variation_states`), so each fortress expansion has an A and a B recipe
   (`arrow_tower` / `arrow_tower_b`, ...), and house draws follow the variation flag.
2. **INIs outside `MenStyle.ini_dir`.** `Style.ini_dirs()` adds the structure folders of groups
   that count as the faction (`ownership.FOLLOWS`: `structures\arnor\`), so Arnor gets every INI
   edit; a ChildObject brings the Draw modules it inherits (the farm finds FarmInterface's).
3. **Ownership false positive.** `recipe_problems` counts only the models a recipe ships, and
   none without meshes, so the sentry tower ships in place.
4. **Budget.** `budget_mb` is 512 for every faction (RotWK runs with 4 GB); normal maps count as
   the game holds them (a standard recipe 8.0 MB, the citadel 32 MB).
5. **Numenor stonework** swaps `GBFortress1.tga` for `GBFortress1_U.tga`: every recipe on
   GBFortress1 gets `<own>_U`; the GBWall recipes (wall_segment, wall_end) get
   `GBWalHFortress1_U.tga` / `GBWalXFortress1_U.tga`, painted from the ratio of two unrelated
   sheets at the wall's UVs.
6. **Scaffolder fixes** in `sagekit/scaffold*.py`: 50-triangle wall pieces, one body per build
   variation, case-blind `own_textures` keys, unit-sheet statues, inherited Draw modules.

## Level-up meshes

The six production buildings with level-ups (barracks, archer range, stable, forge, workshop,
farm) have two chained recipes each: `<building>_level2` (V1) on `men/<building>`, and
`<building>_level3` (V2) on `_level2` ([`levels.py`](levels.py)). Build them in
that order; rebuilding a link means rebuilding the links after it. A level mesh carries no cloth
and no night lights: the house and night models show at every level, so they would hang in the
air before the upgrade. Each link paints its own copy of GBVet (`GBV<letter><1|2>`).

## Banners

Few. The caps below count player-colour cloth pieces per building, EA's own house models
included. Walls carry none except the gate. The fortress add-ons take at most one each.

## 1. Fortress add-ons and upgrades

These parts are drawn by `MenFortressCitadel`, which carries `GBHCFortress`. Each part is shown
under its upgrade flag, so every recipe has `parts = (<its tag>,)`. They carry no night meshes (any
lanterns stay dark).

| Recipe | EA model / target | Upgrade | Constraints | Banners |
|---|---|---|---|---|
| fortress_oil | `GBFBOil` / `GBFBOIL` (154) | UPGRADE_BOILING_OIL | cauldrons ring the keep; the steam bones (STEAM_BONE02-09) keep EA's positions; built with animation `GBFBoil_ASKL` | 0 |
| fortress_oil_guy | `GBFBOil_SKN` / `GBFBOILPOT` (164) | UPGRADE_BOILING_OIL | the pot a skinned man-at-arms tips (animations IDLA/ATKA); the body is raised off the ground, so keep the pivot; no lifecycle models | 0 |
| fortress_ivory_tower | `GBFITower` / `GBFITOWER` (402) | UPGRADE_IVORY_TOWER | the tallest piece (z 11.6-177.9): watch `max_z_growth`; animation `GBFITower_ASKL`, and PACKING/UNPACKING states | 1 |
| fortress_house_of_healing | `GBFHeal` / `GBFHEAL` (552) | UPGRADE_HOUSE_OF_HEALING | its facade faces outwards; animation `GBFHeal_ASKL` | 1 |

The citadel door (`GBFDoor_DRC`, 16-triangle leaves) and `GBFFLAMING` inside GBFortress belong
to the citadel recipe.

**Shared:** `assets/men/fortress_ivory_tower/citadel_motifs.py`: the citadel's cornice,
corbel course, White Tree relief and finial as functions, so the add-ons match the citadel
without importing its recipe.

## 2. Expansions

These sit on the citadel's pads, are drawn by their own objects and have no house model of
their own (`HOUSE_DRAW`). They carry no night meshes. Numenor stonework applies (item 5).

| Recipe | EA model / target | Constraints | Banners |
|---|---|---|---|
| garrison_tower | `GBFDOTOWA` / `GBFDOTOWA` (430) | variation A (item 1); nine openings measured: keep the gate arch clear | 1 |
| trebuchet | `GBFTRTOWA` / `GBFTRTOWA` (108) | variation A (item 1); the open platform (P1 is its trebuchet bone): keep the top clear | 0 |
| fortress_wall_hub | `GBGFWHub` / `OBJECT03` (94) | the hub tower, the same mesh as wall_hub's: subclass `WallHub` as the Elves did. The mesh stands on a bone (z -80.7..17.4 in mesh coordinates). BOX01 is a wall stub (optional chain) | 0 |
| arrow_tower, arrow_tower_b, garrison_tower_b, trebuchet_b | `GBFARTOWA`, `GBFARTOWB`, `GBFDOTOWB`, `GBFTRTOWB` | the arrow towers ship own models (Blue Mountains draws them); each B shares its A's pad.py and dome.py | 1, 1, 1, 0 |

**Shared:** `assets/men/dome.py` holds the octagonal drum, ribbed dome and spire that EA repeats on the wall hub, the
upgradeable plot, the wall tower, the fortress wall hub, and both arrow and garrison towers. Also
`assets/men/garrison_tower/pad.py`: the pad base, arch and parapet shared by the A and B variations.

## 3. Walls and gate

These objects are in `campsandcastles.ini`. Every segment tiles the same slot (7.5 x 38, 49.5
high). Most pieces have no house model of their own (`HOUSE_DRAW`) and no night meshes. EA's
rubble `GBWall_Rubble` is drawn by four other factions: leave it EA's. The bibs `GBWallN_Bib` and
`GBWallRmprtNBib` are drawn by the Dwarves too; don't touch them.

| Recipe | EA model / target | Constraints | Banners |
|---|---|---|---|
| wall_segment | `GBWallN` / `BOX01` (276) | also the postern's wall (MenWallPosternGateSmall draws GBWallN); the placement cursor `GBWallN_CUR` goes in `also_derived`, as for the Dwarves and Elves; sheet `GBWall` (the Elves draw it too; own texture pinned) | 0 |
| wall_end | `GBWallNE` / `GBWALLNE` (554) | cliff cap; z -46..49.5 (it reaches down the cliff); shares GBWallN_D3 | 0 |
| wall_hub | `GBWallRmprtN` / `OBJECT03` (94) | the player-placed hub; stands on a bone (mesh z -80.7..17.4); segments meet it from any side, so keep its faces in their planes | 0 |
| wall_hub_upgradeable | `GBWallUpgrdN` / `OBJECT03` (94) | subclass `WallHub`; GBFORTRESS01/02 are wall stubs (optional chains); replaced by the gate, postern, tower and trebuchet upgrades | 0 |
| wall_gate | `GBWallGateN` / `GBFDOTOWA` (580) | the gate leaves BOX06-09 are animated (`GBWallGateN_SKL`, OP/OPN): don't build into their swing (x -5..5, y -40..40, z 0..40) | 2 |
| wall_postern | `GBWallPGN` / `GBFDOTOWA01` (136) | a door arch drawn over the segment (`ModuleTag_DoorDraw`, `parts`); it loops `GBWallrampart` | 0 |
| wall_tower | `GBWallTwrN` / `GBFARTOWA` (238) | the tower mesh is named like the arrow tower's but is a different mesh (238 vs 218 triangles): design both from dome.py. BOX01 is the segment stub (optional chain reusing wall.py) | 1 |
| wall_trebuchet | `GBWallTrebN` / `GBFTRTOWA` (144) | an open platform (P1 is the trebuchet's bone) | 0 |

**Shared:** `assets/men/wall_segment/wall.py` (coping, crenellation rhythm, string course
and battered foot, used by the segment, end, postern, stubs and gate), and
`assets/men/dome.py` (above).

## 4. Production and economy

These are `_SKN` models whose units animate (keep their clearances). Each has EA's house model and
night windows. All of them except the market and stoneworks level up. The level-up meshes (V1 at
level 2, V2 at level 3) are painted from the shared **GBVet** sheet (Men-only), and V1HIDE/V2HIDE
are level-1 stand-ins. The level-up meshes are chained recipes (above).

| Recipe | EA model / target | Level-up meshes | Constraints | Banners |
|---|---|---|---|---|
| barracks | `GBBarracks_SKN` / `BARRACKS` (1452) | V1 216, V2 1994 | OBJECT01 (300) is a second body on the sheet; SPEAR prop; GBHCBarracks | 3 |
| archer_range | `GBArcheryN_SKN` / `ARCHERY` (913) | V1 379, V2 797, ARCHERY_HIGH_ON 236 | the body hangs on a raised bone; animated pulley (skinned, own sheet `gbarcheryn_a`); targets on GUArcher; DXT5 cut-outs; GBHCArcheryN | 2 |
| stable | `GBStable_SKN` / `GBSTABLE` (2186) | V1 354, V2 806 (+V2FLAG) | horses animate in the stalls; the Elven stable is drawn from Gondor's GBStable sheets (own texture pinned); GBHCStable | 2 |
| forge | `GBBlkSmith_SKN` / `GBBLKSMITH` (483) | V1 298, V2 376 | smith animation, fire plane, weapon racks (PG02); GBHCBlkSmith | 1 |
| workshop | `GBWorkshop` / `GBWORKSHOP1` (732) | V1 604, V2 1304 | V1HIDE (236) is the level-1 yard on the body's sheet; GBHCWorkshop | 2 |
| farm | `GBFarm_SKN` / `GBFARM` (228) | V1 666 (walls), V2 341 (pillars), both on GBFarm | skinned crops and peasant; DXT5 cut-outs; GBHCFarm is drawn by GondorFarm's own module | 1 |
| market_place | `GBMarket_SKN` / `MARKET_STRUCTUR` (2834) | - | the densest body; vendor, woman and chicken animate; awnings are cut-outs (DXT5); GBHCMarket | 2 |
| stone_maker | `GBStoneMK_SKN` / `GBSTONEMK` (1298) | - | no normal map on its sheet; the crane, pulleys and hooks are separate animated meshes (`GBStoneMK_SKL` IDLA): don't cover their paths; GBHCstoneMk | 1 |

**Shared:** `assets/men/motifs.py` (window surrounds, roof ridges and eaves,
cornice, banner mounts, White Tree roundel, sized from the measured bands) and
`assets/men/levels.py` (the chained level-up recipes).

## 5. Towers and specials

| Recipe | EA model / target | Constraints | Banners |
|---|---|---|---|
| keep | `GondorKeep`: `GBBtlTwrs` / `OBJ0` (1022) | the battle tower; tall round tower with a dome (z 0.3-116); N_WINDOW night; GBHCBtlTwrS | 2 |
| sentry_tower | `GBBtlTwrM` / `GBBTLTWRMINI01` (486) | ships in place; also drawn on the base-defence plot (editor state); GBHCBtlTwrM | 1 |
| well | `GBWell` / `GBWELL` (752) | water meshes (SPOUT03, RBWELLWATER01 and a splash on Elven-shared sheets) stay EA's; heal effect; GBHCWell | 0 |
| statue | `GondorStatue`, `GondorHeroStatue`: `GPHealstue` / `GPHEALSTUE` (550) | a figure on a plinth painted from the unit sheet GUHeroStat (own texture pinned `GUHeroStaH`); pedestal work, the figure is not re-carved; GPHCHealstue | 1 |

**Shared:** `assets/men/keep/tower.py` (round drum courses, ribbed dome and lantern, window
hoods), used by the keep and the sentry tower.
