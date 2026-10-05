# Create-a-Hero: the cah pack

More choices in the Create-a-Hero (CaH) screen: serious and fun parts appended to the creation
screen's rows, for every class. The Dwarf (`assets/cah/dwarf`) is the first class and the template.

## How the screen lists choices

- `CahAppearance.apt` places exactly **7 rows**, one per `UISlot` 0-6: helmet, shoulders, body,
  gauntlets, weapon, shield, boots. A new row (a beard or cape row) would need APT and engine work, so a
  cape goes in the shoulder row.
- Each row is a Prev/Next cycler. It asks the game how many entries the subclass has
  (`MyHero::NumAppearance_N`), so the APT puts no cap on choices per row. EA's longest list is 9;
  the Dwarf's helmet row is now 20.
- `MyHero.dat` saves each row as an **index** into the subclass's list. Entries are therefore only
  ever **appended**. The lint fails if any of EA's lists stops being a prefix of ours.
  The engine sorts each row by the upgrades' `GroupOrder` as it parses it (comparator 0x61aa91,
  called from the bling adder 0x61e66f; a stable insertion sort for rows of 16 or fewer), so the
  index is a position in the *sorted* row. Ours sort after EA's because their `GroupOrder` starts
  past every EA row. EA's wizard helmet row is already reordered by this sort (`CorruptedMan_1_CHH08`, order 6, sorts before `WIZ_CHH07`).
- Other limits: 3 colours with a free picker, 8 class slots, 5 subclasses per class, 64 weapon-set
  flags (EA uses 40).
- **1152 upgrades in all.** The engine's upgrade mask is 1152 bits (exe 0x444db3); each Upgrade
  takes the next bit unchecked (0x66fcb7), and past bit 1151 `Object::removeUpgrade` (0x691438)
  overwrites its stack frame: EA's 1027 plus our first 161 crashed the game (2026-10-03). The lint
  counts EA's, every other archive of ours (they add none) and the pack's, prints the headroom and
  fails over 1152 (`sagekit/upgrades.py`, also in `python3 -m sagekit validate`).
- **Upgrades are shared by row and position.** An upgrade is only a name; each class shows its own
  sub-object for it. Every class's first appended helmet is `Upgrade_SKH_CHH01`, and so on (`CHSP`
  shoulders, `CHS` shields). Weapons stay one each, as each sets its own weapon-set flag. 21 + 22 =
  43 upgrades, headroom 82; a new class adds only weapons and entries past the longest row.

## Layout

| Path | What |
|---|---|
| `assets/cah/kit/` | the shared kit: `geom.py` (primitives, lod trimming), `ornament.py`, `paint.py` (sheet painter, masks), `models.py` (sources, part design per model, the old copies), `attach.py` (part models on bones, Draw modules), `attach_lint.py` (their checks), `attach_review.py` (review sheets), `ini.py` (fragments, composition, lint), `survey.py`, `render.py` |
| `assets/cah/<class>/` | a class: `design.py` (its spec), `build.py`, `paint.py` (tile tables), its part designs |
| `assets/cah/pack/design.py` | the one unit recipe: the archive name and every class's mask lines (shared house-colour INI) |
| `sagekit/units/cah.py` | stage, install and revert the whole pack |
| `sagekit/blender/cah_pose.py` | the renders' Blender side |

## Commands

```sh
python3 -m assets.cah.kit.survey --markdown        # EA's subclasses (the table below)
python3 -m assets.cah.<class>.build [--skip-paint] # sources and sheets (and the old copies, never shipped)
python3 -m assets.cah.kit.attach <class> [--review] # part models on bones, INI fragment, every check, review sheet
python3 -m assets.cah.kit.render <class>           # build/assets/cah/<class>/renders/overview.png (one Blender)
python3 -m sagekit.units.cah --stage               # compose all classes, lint, pack, asset.dat round trip
python3 -m sagekit.units.cah --install [--dry-run] # one archive, records, shared house-colour INI
python3 -m sagekit.units.cah --stage --classes dwarf   # only these classes (comma list), to test one at a time
python3 -m sagekit.units.cah --revert  [--dry-run]
```

Each class builds on its own into `build/assets/cah/<class>/`, including its INI composed alone onto
EA's and linted. The pack composes every class's `fragment.json` onto EA's files in class-name
order, lints the whole composition and packs **one** `!!!!!!!!!!!sagekit-cah.big`. Install and
revert stay one command each. Revert takes the records named by the installed archive, so it works
after classes are added.

## Adding a class

Copy `assets/cah/dwarf` and fill `design.py`:

| Name | Says |
|---|---|
| `NAME`, `CLASS_FILE` | the folder name; EA's `createaherosystem<CLASS_FILE>.inc` (several folders may share one class file, each adding to its own subclasses) |
| `SUBCLASSES` | `[{"index": n, "name", "models": [EA models]}]`; `index` is the `Upgrade_CreateAHero_SubClass_n` number |
| `MODELS` | `{EA model: our copy}`, `CH…` → `SK…` (e.g. `CHAR_FE_U_SKN` → `SKAR_FE_U_SKN`) |
| `SKELETONS`, `KIND` | `{model: skeleton}`; `{model: "u" / "c" / "m"}` (the budget column) |
| `DESIGN` | the model the parts are drawn in; models on its skeleton take them as drawn |
| `FIT_REFS`, `WEAPON_REF` | EA parts present with identical vertices in the design model and each other model (exact affine fit, else the build stops) |
| `EXPECTED`, `CHECK_ANIM` | SHA-256 of every EA source (models, skeletons, animations); `{skeleton: animation}` the drift check poses |
| `DESIGN_HAND`, `HAND` | the weapon bone in the design, and per skeleton |
| `TEMPLATE`, `TEMPLATE_TEX` | EA's skinned part whose material ours copy, and its texture (or `TEMPLATE = {model: (mesh, texture)}`); our sheet names replace it in place and must not be longer |
| `SHEETS`, `MASKS` | `{"serious"/"fun": sheet}`, `{sheet: mask}` |
| `SEAT` | `{group: function}` applied before placing (the Dwarf seats helmets on the head) |
| `BONES` | `{group: bones its parts may ride}` |
| `WEAPON_LIKE`, `WEAPON_NOTE` | EA's weapon-set flag each new weapon copies (one flag, or `{sub-object: flag}`); every EA WeaponSet on that flag is copied, so a bow keeps its ranged and melee sets. `WEAPON_LINES` (the Dwarf) gives the lines directly |
| `ALSO_SHOW` | `{sub-object: [EA sub-objects]}` shown with it (a bow shows `WestronSword` for melee) |
| `BUDGET`, `budget()` | vertex caps per group and kind |
| `PARTS` | `(sub-object, group, design(gear), name, description, "serious"/"fun", tile remap, upgrade[, [subclass indices]])`, in **append order** |
| `RENDER` | the overview's bodies, head model, EA helmets, kits, colours, idle animations |
| `ATTACH`, `ATTACH_STEM` | the parts that ride bones (every part) and the part-model name stem, at most 4 characters (`kit/attach.py`) |

A part's design function draws into a `Gear` (`kit/geom.py`): `shell`, `sweep`, `tube`, `stud`, `slab`,
`loft`, `blade`, `ribbon`, all in the design model's rest space and each bound to an EA bone. Never
reorder or remove an entry once a build has shipped: append only.

## Naming (never collide)

| Thing | Rule | Example |
|---|---|---|
| Upgrades | `Upgrade_SKH_<CHH|CHSP|CHS><nn>`, shared: our `nn`-th entry of that row in every class (`kit/ini.py` `row_upgrade`) | `Upgrade_SKH_CHH01` |
| Weapon upgrades | `Upgrade_SKH_CHW<nn>`, `nn` = its own flag `WEAPONSET_CREATE_A_HERO_WS_<nn>` | `Upgrade_SKH_CHW52` |
| Weapon-set flags | Dwarf 43-45 (used). **Men + Wizards 46-51, Archers 52-57, Orc/Uruk/Corrupted Man/Olog-hai 58-64** | |
| Sub-objects (≤ 15 chars) | `SK<STEM>_<PART>`, globally unique | `SKARFE_HOODPK` |
| Part models (≤ 15 chars) | `ATTACH_STEM` + EA model's two middle fields + `_` + bone code (`HD` head, `HR`/`HL` hands, `UL`/`UR` upper arms, `FL` forearm, `S1`/`S2` spine, `RB` ribs, `PV` pelvis; else the bone's name) | `SKDWTMU_HD` |
| Attach Draw modules | `SKH_Att_<ATTACH_STEM>_<bone>` | `SKH_Att_SKDW_B_HAND_R` |
| Sheets (≤ the template's texture name) | `SKCAH_<FAM>GEAR.tga`, `SKCAH_<FAM>FUN.tga`; masks `HC_` + sheet | `SKCAH_ARGEAR.tga` |
| INI module tags | made by the kit (`SKH_Show_<sub-object>`, `SKH_Remove_<upgrade>`, `SKH_Weapon_<upgrade>`) | |

The Dwarf keeps its first sub-object names (`SKH_*`); its upgrades moved to the shared names. `<FAM>` is the
model family (`HW`, `AR`, `WZ`, `SS`, `CM`, `TL`). If two groups share a family, agree on one
sheet pair or use the subclass stem. The lint refuses duplicate upgrades, module tags, sub-objects
shown by two upgrades, models or textures shipped twice, and more than 64 weapon-set flags.

## Budgets

The build trims each part (`lod` 1.0 down to 0.35: fewer sides, fewer sweep samples, rivets
dropped, thin plates as one two-sided face) until it fits its cap in that model. In game (_U):
helmets 650, shoulders 700, shields 600, weapons 540, cloaks 900. Creation screen (_C): 950 / 1100 /
900 / 700 / 1350. EA's own: dwarf helmets 401 / 921, shoulders 290 / 576, axes 468-532. Mounted (_M)
models take the _U caps. A part over its cap stops the pack (`--stage`).

## Serious and fun; fixed and tinted colours

The 3 hero colours act through a mask per sheet (`kit/paint.py`, like EA's `HC_CHDW_TM.tga`).
Alpha marks what takes a colour; G is EA's tunic channel, R its second cloth, B its studs.

- **Serious** parts tint their cloth and enamel tiles. The Dwarf's blue enamel and cloak follow
  colour G, its leather wraps R, its gems B. Metal stays metal.
- **Fun** parts are mostly **fixed** colours on purpose: a pink cape stays pink. Their tiles have
  tint `None`, or `special()` returns a fixed rgb. A few still tint: the jester and party hats.
- **Colour variants** of a serious part (gold-plated, hot pink) reuse its design with a tile
  `remap` onto fixed-colour tiles.
- All parts must read at the RTS camera.

## Checks (all automatic)

- **Sources:** EA's sources must match their SHA-256.
- **Models:** every EA chunk in our copies is byte for byte EA's, skin weights included. New meshes
  are skinned, single-bone, on their group's bones and draw only our sheets. Through an EA
  animation every vertex stays finite and keeps its distance to its bone. Budgets.
- **INI:** EA's data lint-clean, then ours; every list an extension of EA's; every label in EA's
  `lotr.str` (the menu shows EA's row label: 141 of EA's 275 part names are missing too, and a
  `lotr.str` of ours would replace a non-English player's strings); every entry clears its row's
  group and shows a sub-object our models carry; each weapon's set exists. Broken copies (inserted
  entry, missing label, no group clear, part missing from a model, missing weapon set, models not
  ours, over 1152 upgrades) must each fail.
- **Pack (`--stage`):** no member another archive serves first; nothing filed twice; asset.dat
  staged and reverted on copies gives back today's records byte for byte.

## Not covered yet

- The **body** row: EA swaps the body texture there (`UpgradeTexture`); the kit adds sub-objects only.
- Per-entry names.
- New rows.

## Known issue / redesign (2026-10-04)

Max tested the full pack (archive sha256 `89e08134…`, the staged build) after the crash fix:
"customisation now doesn't really work? It seems you put permanent stuff on them. You shouldn't
have edited the base stuff." A part stays on after he picks another option, in every row. The pack
is reverted. Nothing below is installed.

### What the pack replaces today

- **Art: nothing under EA's names.** 34 model copies `art\w3d\sk\sk*_skn.w3d`, 18 sheets and 18
  masks, all ours. The new asset.dat records are ours. EA's records are untouched.
- **INI: 11 members under EA's names**, each EA's 2.02 file with our text appended:
  `createaheroupgrades.inc`, `createaherosystemappearancebling.inc`, `createaherosystemweapons.inc`,
  `createaherosystem{menofthewest,archer,wizard,dwarf,servantsofsauron,corruptedman,ologhai}.inc`
  (rows appended), and `object\createahero\createahero{weaponupgrades,removeupgradeupgrades,models}.inc`.
- **The real "edit of the base stuff" is `createaheromodels.inc`.** It points every
  `Model = CH…_SKN` line (34 states, every subclass, game/creation/mounted) at our `SK…` copy. Every
  Create-a-Hero hero then draws our copy, including saved heroes and heroes that pick only EA parts.
  The copy keeps EA's chunks byte for byte and adds 12-24 meshes (EA's largest skin has 45
  sub-objects; ours go up to 61).

### What the engine does with the rows (exe, checked against our data)

- `RemoveUpgradeUpgrade` (0x8bc1b3): it removes every upgrade on the object whose `GroupName` is in
  `UpgradeGroupsToRemove`, except the module's own `TriggeredBy` upgrades. `GroupOrder` plays no
  part. Our `SKH_Remove_*` modules are the same as EA's, one per upgrade.
- `GroupOrder` only sorts the rows (see above). With +2 for helmets and +3 for shields, EA's sorted
  order is unchanged in all 16 subclasses (checked with the composed files).
- `Object::removeUpgrade` (0x691438) resets each upgrade module the bit triggered (0x8d2901). For a
  `SubObjectsUpgrade` with `HideSubObjectsOnRemove`, that hides its `ShowSubObjects` (0x8b928e). The
  hide goes to every Draw module of the drawable (0x672823). `W3DModelDraw` keeps it by name in
  an unbounded vector (0x4c3b25) and applies it with `Get_Sub_Object_By_Name` (0x4ba74f).
- The applier (0x80ace3) gives each row's upgrade at its saved index (0x619b87). It removes nothing
  itself: the old part goes only through the new upgrade's `RemoveUpgradeUpgrade`.
- Default visibility: no CaH mesh, EA's or ours, has the W3D hidden flag (all `0x20000` skin), and no
  INI line hides them. `SubObjectsUpgrade` has no hide-on-create: its drawable-bound hook (0x8b8e86)
  only re-shows an executed upgrade.
- **What hides EA's parts is Lua, by name.** `data\scripts\scriptevents.xml` binds the CaH object's
  `AILuaEventsList = CreateAHeroFunctions` events `OnCreated` (`OnCreateAHeroFunctions`) and
  `OnGenericEvent` to `CreateAHeroHideEverything` in `data\scripts\scripts.lua` (2.02,
  `__patch202.big`). That function calls `ObjectHideSubObjectPermanently(self, "<name>", true)` for 153
  of EA's names (`HLMT_06`, `SLDR_06`, `AXE_01`, `SHIELD_01` …). None of ours is in the list.

Walking the switches through these rules (dwarf helmet: EA `DWARF_CHH01` → ours `SKH_CHH01` → EA
`DWARF_CHH03` → ours `SKH_CHH01` → ours `SKH_CHH02`; shoulders `SKH_CHSP01` ↔ `DWARF_CHSP02`; shield
`SKH_CHS01` ↔ `CAPG_CHS01`; weapon `SKH_CHW43` ↔ `CHW01`): every step removes the old row upgrade
and hides its part, for EA's parts and ours alike. Sharing row upgrades across classes adds up to 10
show/hide modules per upgrade, all by name, and one remove module. That changes nothing on a dwarf.
**So the INI data does not explain the stuck parts. The Lua list does.** Every hero drew our copy,
and the copy's 12-24 parts of ours started visible because the Lua list does not name them. A part
shown and then removed hides correctly, but every other part of ours stays on from spawn: the
"permanent stuff" in every row.

Defects found on the way:
- `SKH_FUN_PINKCAPE` (dwarf) was 16 characters. W3D mesh names hold 15 plus a terminator, so the
  name ran into the container field and the part could never be found by name. It is now
  `SKH_FUN_PINKCAP`. `kit/ini.py` lints every shown name (≤15, with a broken copy that must fail),
  and `kit/models.py` and `kit/attach.py` refuse longer mesh and model names.
- Editing `scripts.lua` to list our names would also work, but it replaces an EA file for everyone.
  Not done.

### Redesign: leave EA's heroes alone

Goal: no `createaheromodels.inc`, no copies of EA's skins. An EA-only hero draws byte for byte
what EA's game draws.

**A (recommended): part models attached to bones.** Each part is rigid already: every vertex rides
one bone (`kit/models.py`). A pauldron pair spans `BAT_UARML`+`BAT_UARMR`, so split each part per
bone. That loses nothing. For each subclass and bone, build one small model under our name (e.g.
`SKDW_TMU_HEAD`) that holds all of that subclass's pieces for that bone as separate meshes, each
with the W3D hidden flag (0x1000) set, so it starts hidden at load whatever the runtime does.
Add a Draw module per (subclass skeleton, bone) to `CreateAHero`. It has
`DefaultModelConditionState Model = None`, a `ModelConditionState = CREATE_A_HERO_nn` for that
subclass's _U/_C/_M states, `AttachToBoneInAnotherModule = <bone>` and `OkToChangeModelColor = Yes`.
This is EA's own pattern: `HeroOfTheWestShield` in `createaherodrawmodules.inc`, and EA's commented-out CaH weapons.
Only that subclass then instantiates them, about 5-9 per hero.
The upgrades, rows, `SubObjectsUpgrade` and `RemoveUpgradeUpgrade` stay as they are; the show and
hide reach the attached modules through the same broadcast (0x672823). Ship no `createaheromodels.inc`
and no asset.dat records for EA models; only records for the new part models.
- EA-named INI cannot be avoided. The rows live in EA's class files, and outside a map.ini there is
  no add-only override. The rule becomes: EA's lines byte for byte, ours appended only (already
  linted). That leaves 10 members, down from 11.
- Upgrades unchanged (43, headroom 82). LAN: INI and new archive members.
- Risk, low to medium. If something misbehaves, only our parts can; EA's options and saved EA-only
  heroes keep EA's own models. Open points for the pilot:
  - un-hiding a W3D-hidden mesh through `ShowSubObjects` (EA never does it: 0 of the hidden meshes
    in a third of EA's models are named in a `ShowSubObjects`);
  - bone names per skeleton (`B_HEAD`/`BAT_HEAD`/`TROLL HEAD`/`BIP HEAD`);
  - attachments on the mounted models.
- Effort: about 2 days for the kit (split per bone and emit part models in `kit/models.py`, Draw
  modules in `kit/ini.py`, records in `sagekit/units/cah.py`, lint for name length and hidden
  flags). Then about a day to rebuild every class and the review renders.

**B: our copy under a new name, only for heroes that pick a part of ours.** A `ModelConditionUpgrade`
on every upgrade of ours sets a spare flag, and the states with that flag draw the `SK` copy. This
needs a free model-condition flag; EA clears all of `CREATE_A_HERO_00-65` on every subclass switch.
It swaps the model mid-game and still depends on the runtime hide inside the copy. Medium-high risk.

**C: a copy under EA's name with EA's parts byte for byte and ours hidden.** This overrides EA's art
for every hero, which is exactly what Max rejected. Not proposed.

### The pilot (built and staged 2026-10-04, not installed)

The Dwarf's Erebor helm (`SKH_HLMT_ER`, `Upgrade_SKH_CHH01`) and Erebor war axe (`SKH_AXE_ER`,
`Upgrade_SKH_CHW43`): `ATTACH` in `assets/cah/dwarf/design.py`, built by `assets/cah/kit/attach.py`.

- 8 part models of ours, one per EA model and bone: `SKDW{TM,SG}{U,C}_HEAD` and `…_HANDR`. Each
  model has a root pivot plus one pivot per part, rigid meshes and an HLOD, like EA's `CUWestronSword`.
  Every part mesh has the W3D hidden flag. Each EA model gets its own fit, because the creation-screen
  Taskmaster and Sage differ slightly.
- 8 Draw modules appended to `createaherodrawmodules.inc` (`SKH_Att_<model>`). Each has
  `Model = None`, our model only in that EA model's own `CREATE_A_HERO_20/21/22/23` state, and
  `AttachToBoneInAnotherModule = B_HEAD / B_HAND_R / B_HANDR`.
- Shipped: 8 models, `SKCAH_DWGEAR` and its mask, and 7 INI files under EA's names, each EA's text
  byte for byte with ours after it (the class file: our entry at the end of each row).
  `createaheromodels.inc`, EA's skins and EA's asset.dat records are not shipped or touched.
  Records for our models list their own sub-objects (`add_model(..., own=True)`, EA's layout).
- Upgrades: 2 (EA 1027 + 2 = 1029, headroom 123).
- Checks (`kit/attach.py` `lint`, each with a broken copy that must fail): createaheromodels.inc is
  EA's; EA's text comes first in every shipped INI; every part is hidden and rigid; every model has its
  Draw module on a bone its skeleton has; names ≤15. Parts stay at their bone through EA's animation.
- Review: `build/assets/_review_finish/cah_attach/dwarf_sheet.jpg` (EA helmet, ours, EA again; the
  same for the axe; in game). The render puts each part on its bone exactly as the attachment does.

```sh
python3 -m assets.cah.kit.attach dwarf [--review]   # part models, INI fragment, checks, review sheet
python3 -m sagekit.units.cah --stage --classes dwarf
python3 -m sagekit.units.cah --install --classes dwarf
python3 -m sagekit.units.cah --revert
```

A class not converted yet (still on copies) is refused by `--stage`/`--install`.

**Max's result (2026-10-05, the installed pilot):** "works !": the helm and axe show only when picked, one
part at a time. But they do **not** follow the three Create-a-Hero colour pickers (see "Hero colours" below).

**What Max tests:** a dwarf (Taskmaster, then Sage) in the creation screen. Check:
1. No new part shows until it is picked.
2. Helmet row: EA helmet → Erebor helm → EA helmet: one helmet at a time.
3. The same in the weapon row with the Erebor axe.
4. A saved hero that uses only EA parts looks as before.
5. In a skirmish, the picked helm and axe stay on the dwarf and the house colour tints them.

If (1) fails, the engine ignores the W3D hidden flag. If (2) fails because a part never shows, it
ignores the show on a hidden-flag mesh. Either would need our Lua names, so ask Max first.

### Every class on bones (staged 2026-10-05, not installed)

Every class is now built by `kit/attach.py`, every part the old pack had (the silly ones too, same
designs, same sheets): `ATTACH = [every part]` and an `ATTACH_STEM` in each `design.py`. Nothing
ships copies of EA's skins any more; `MODELS` and `kit/models.py`'s copies only feed the old overview
renders.

| Class | Stem | Parts | Part models | Draw modules | Parts split by bone | Rows (ours) |
|---|---|---|---|---|---|---|
| archer_el | SKAE | 22 | 13 | 10 | 1 | helmet 11, shoulders 5, shield 3, weapon 3 |
| archer_fe | SKAF | 22 | 13 | 10 | 1 | helmet 11, shoulders 5, shield 3, weapon 3 |
| corruptedman | SKCM | 12 | 20 | 5 | 3 | helmet 6, shoulders 4, weapon 2 |
| dwarf | SKDW | 24 | 24 | 7 | 2 | helmet 13, shoulders 5, shield 3, weapon 3 |
| men_cg | SKCG | 18 | 18 | 10 | 2 | helmet 10, shoulders 4, shield 2, weapon 2 |
| men_sm | SKSM | 16 | 18 | 13 | 2 | helmet 8, shoulders 4, shield 2, weapon 2 |
| ologhai | SKTL | 16 | 42 | 21 | 3 | helmet 6, shoulders 5, shield 2, weapon 3 |
| servantsofsauron | SKSS | 17 | 24 | 10 | 4 | helmet 7, shoulders 5, shield 3, weapon 2 |
| wizard | SKWZ | 14 | 18 | 4 | 0 | helmet 8, shoulders 4, weapon 2 |

161 parts, 190 part models, 90 Draw modules. Upgrades: EA 1027 + ours 43 = 1070 of 1152, headroom
82 (shared row upgrades, as before). Staged archive: 239 members, 83 MB (190 models 45 MB, 18 sheets
25 MB, 18 masks 13 MB, 13 INI); a model loads only when its subclass's state draws it.

What changed in the kit:

- **Split by bone.** A pauldron pair, a cloak over the spine and both arms, the troll war-plates:
  `rigid_pieces` trims the part to its budget as a whole, then splits its triangles by the bone
  their vertices ride (a triangle across bones stops the build). Every piece keeps the part's
  sub-object name, so the part's one `SubObjectsUpgrade` shows all its pieces (the show and hide go
  to every Draw module and act by name in each). Nothing moves: each vertex rode one bone already.
- **One Draw module per (class, bone)**, not per model. It lists **every** `CREATE_A_HERO` state of
  the class's EA models in `createaheromodels.inc` (the mounted `MOUNTED CREATE_A_HERO_00/02`, the
  archers' and Corrupted Men's `… INVISIBLE_STEALTH`, the troll's two states), each with our model
  for that EA model and bone, or `Model = None`. With only its own state, a module made for the
  in-game Captain would also match `MOUNTED CREATE_A_HERO_00` and put the unmounted fit on the rider.
- **Bone names with a space** (`TROLL HEAD`, `BIP L UPPERARM`) are written quoted:
  `AttachToBoneInAnotherModule` is read by EA's quoted-string reader (game.dat 0x4b65ba → 0x42e757:
  a value opening with `"` takes the following tokens up to the closing quote, joined by one space).
- **Short model names** (the naming table) so troll bones fit in 15 characters.
- Per-skeleton bones come from each class's own placement (the Dwarf's `B_HAND_R`/`B_HANDR`, the
  Shieldmaiden's `BONE05/09/13/14` and `SPEARBONE` on the mount, the archers' `BOWBONE`, the trolls'
  `TROLL…`/`BIP …`/`BAT_…` rigs, `WEAPON`, `WEAPONCOB`, `FIREPOINT01`); each EA model keeps its own fit.
- **Checks** (`kit/attach_lint.py`, each with a broken copy that must fail): createaheromodels.inc
  is EA's; EA's text first in every shipped INI; every part mesh hidden, rigid, name ≤15; every part
  model on a bone its skeleton has, drawn by its class's module for that bone in a state of its own
  EA model; no module draws a model in another EA model's state; no module misses one of the class's
  states; every part in some model. Through EA's check animation every vertex keeps its distance to
  its bone. `--stage` reruns the class checks on the whole composition.

Review sheets (per subclass and row: EA's part, ours in menu order, EA's again on the creation-screen
model; then EA's kit, our serious kit and our fun kit on each of the subclass's models, the mounted
ones too), `build/assets/_review_finish/cah_attach/<class>_sheet.jpg` for `archer_el`, `archer_fe`,
`corruptedman`, `dwarf`, `men_cg`, `men_sm`, `ologhai`, `servantsofsauron`, `wizard`.

```sh
python3 -m assets.cah.kit.attach <class> [--review | --review-only]
python3 -m sagekit.units.cah --stage                # every class; the pilot must be --revert-ed before --install
```

### Hero colours (2026-10-05, open)

Max: the pilot's helm and axe do not change with the three colour pickers; earlier "select colors no
longer work on heros". What the exe does (read from game.dat; nothing run):

- The pickers are `CahAppearance::HairColor / SkinColor / PaintColor`. Each handler (e.g. 0x9c3c76)
  stores the colour in the hero record (`MyHero` +0x2c/+0x30/+0x34; setters 0x809745… set dirty bit 8)
  and calls the applier (`MyHero` vtable +0x10, 0x80ace3).
- The applier, on bit 8, builds a three-colour struct (0x80959a) and calls the drawable (0x6727b0),
  which calls **every** Draw module's slot 0x7c (`W3DModelDraw` 0x4b877d): if the module has a render
  object, it passes the colours to it (render object slot 0x1f8). The HLOD forwards to every
  sub-object (0x59b1a0); the mesh (0x54bde0) looks up its texture's `HouseColor` mask (housecolor.ini)
  and builds or rebuilds the coloured mask texture on the CPU (0x531c77: output = mask R × colour 1 +
  G × colour 2 + B × colour 3, alpha kept; the mask must be A8R8G8B8 or A4R4G4B4, anything else is
  skipped).
- The colours are **not stored** in the Draw module (the module's own colour, +0x28, is the player
  colour from `OkToChangeModelColor`; the "store in every module" broadcast 0x6727ea has no caller).
  So only render objects alive at the broadcast get the hero's colours; one created later shows the
  player colour (R channel only) until the next colour change.
- A CaH object's modules with `OkToChangeModelColor = Yes` mark their colour "rebuildable" (0x4b4a30,
  bit 30, from the object's KindOf), so later changes rebuild the coloured texture in place.

Our attached modules meet every condition found: they are in the broadcast (the show and hide reach
them the same way), have `OkToChangeModelColor = Yes`, copy EA's part material, and ship the mask as
an A8R8G8B8 DDS (texbake; d3dx9 loads EA's TGA masks as the same format). **So the cause is not
found in the static path, and no fix is made.** Two candidates, one test session separates them:

1. Pick an EA helmet on the Dwarf and move the pickers. If EA's helmet does not change either, the
   regression is global: try the same with `WINED3D_STASH_MANAGED=0` (Wine patch 0022 keeps managed
   textures out of the process; the rebuild locks and rewrites an uploaded texture), then with the cah
   pack reverted.
2. If EA's changes and ours do not, it is the attached modules: note whether ours change after a
   picker is moved *after* the part was picked (render object alive at the broadcast) or never.

**Offline checks, 2026-10-05 (no game run).** Both suspects of candidate 1 are cleared offline.

- *The texture sequence (game.dat).* The coloured texture is the mask texture itself. The mesh
  (0x54c2a1) names it `#<mask>#<colour key>` and creates a loader if no texture has that name
  (0x5326f8 → 0x531c0b). For a rebuildable colour the key is a fixed `-1,0,0,0`, so every CaH mesh
  with that mask shares one texture. Loading (0x53101b) has two paths, both MANAGED with usage 0:
  - a 24/32-bit TGA: `D3DXCreateTexture`, level 0 `LockRect(NULL, NOSYSLOCK)` and copy,
    `D3DXFilterTexture(BOX)` (skipped when the texture has one level);
  - anything else: `D3DXCreateTextureFromFileInMemoryEx`.

  Right after loading, 0x532847 → 0x531c77 copies level 0 to the heap (`GetSurfaceLevel(0)`,
  `LockRect(NULL, D3DLOCK_NOSYSLOCK)` from 0x516030, then unlock). This only happens for a rebuildable
  colour, and nothing is coloured yet. On each picker change, 0x5321ba (only if that copy exists) →
  0x531c77:
  1. the same lock;
  2. the copy, coloured, written into level 0;
  3. `UnlockRect`;
  4. `D3DXFilterTexture(tex, NULL, 0, D3DX_DEFAULT)` (0x532198) rebuilds the other levels.

  There is no UpdateTexture, AddDirtyRect, READONLY or DISCARD.
- *Wine 0022.* `scripts/cahrecolor.sh` (`tools/cahrecolor.c`) replays exactly that sequence: 16
  masks, both load paths, the first colour before or after the first draw, EvictManagedResources
  between colours, the copy taken only after a draw, and a one-level mask. After each of 3 colour
  changes it draws levels 0–2 and reads them back, and reads level 0 with a lock. On engines/w10
  (0022 installed) every check is ok with `WINED3D_STASH_MANAGED=1` (384 stashes and 384 restores in
  the trace) and with `=0`. A texture whose copy was taken is pinned in 32-bit memory after its first
  restore, so 0022 never stashes it again. **0022 is not the cause** as far as this sequence goes;
  the game's own run with `=0` remains the final word.
- *Our data.* No archive of ours ships a file with an EA `HC_CH*` name. EA's 65 CaH masks come only
  from EA's `Textures2.big`, as 32-bit TGAs. The HD Edition overrides `hc_mumnttroll.tga`, still a
  32-bit TGA. All our HC_ masks are A8R8G8B8 DDS with full mips, none DXT. sagekit-units.big's
  housecolor.ini is EA's live one (`__patch202.big`) with 38 blocks appended: no EA line is changed,
  and it has the same BOM and CRLF and ends in `End`. Our parts' 17 `SKCAH_*` entries name masks
  that are not shipped. The colour-picker UI files are EA's. **The packs do not touch EA's CaH
  colouring.**

So candidate 2 (our attached modules), or a cause outside this path, is what the test session in
step 1 has to settle.

**Offline checks 2, 2026-10-05 (no game run).** Every candidate left above is now traced in game.dat
or measured in the installed files. None breaks a colour. What the pickers reach is the answer.

- *Which picker drives which channel.* The handlers 0x9c3c22 / 0x9c3c4c / 0x9c3c76 are registered
  with `OnHairColor` / `OnSkinColor` / `OnPaintColor` (0x9c43dd / 0x9c439c / 0x9c435b). They set
  `MyHero` +0x2c / +0x30 / +0x34, which the colouring multiplies by mask **R / G / B**. So
  **Hair → R, Skin → G, Paint → B.**
- *EA's own parts take no hero colour.* The Dwarf's housecolor.ini lines cover only its body sheets
  (`CHDW_TM*`, `CHDW_SG*`, `CH_Dwarf_03`). Across every EA CaH skin, the meshes whose texture has a
  line are: helmets 6 of 198, shoulders 0 of 153, shields 0 of 35, swords, hammers and bows 0. The
  pickers colour EA's bodies (cloth, skin, hair), not their armour.
- *Our parts take a little, on Hair and Skin.* `python3 -m sagekit.housecheck --tint <archive>`
  measures the share of each part's surface where the mask's alpha and a channel are set (image row
  = (1 − V)·height; this V convention lands the Erebor helm on its intended tiles: gold, bronze dome,
  cheek, crest, rune band).
  - The pilot: Erebor helm 5.3 % (rune band, G = **Skin**), plus 0.3 % gems (B) on the creation-screen
    fit. Erebor axe 8.5 % (leather wraps, R = **Hair**). **Paint** changes neither.
  - The staged pack: 98 of 161 parts take no colour. 43 parts have 10 % or more, and 22 have 25 % or
    more. By channel, Hair reaches 29 parts, Skin 37 and Paint 7. That follows `kit/paint.py`'s
    rule (G cloth and enamel, R leather, B gems; metal stays metal).
- *The mask lookup* (housecolor.ini parser 0x828365 → 0x536643). Each `BaseTexture` is resolved through
  the asset manager (0xa32ee0, the textures asset.dat files at startup) to an id. The mask name is
  stored under that id (map 0xdd83f4).
  - A name that asset.dat does not file gets id **-1**, so its line never matches a mesh. A texture
    created later gets an id of its own (0x532875).
  - The mesh path (0x54bde0 → 0x54c49e: legacy material, one pass, no per-polygon stage-1 array) looks
    up its stage-0 texture's id (0x535e86), names `#<mask>#<key>` (`%d&%d&%d&%d`, 0xbe8998) and
    loads the mask by file name, `.dds` before `.tga` (0x530d29). The format is the file's own
    (`D3DXCreateTextureFromFileInMemoryEx`, format 0, 0x53117e). A 24/32-bit TGA loads as
    X8R8G8B8/A8R8G8B8 (0x5310ad).
  - Our part meshes have the same shader, one pass and one stage as EA's body meshes (the chunks
    compared), so they take the same path.
  - `SKCAH_DWGEAR.tga` and `HC_SKCAH_DWGEAR.tga` are filed in RotWK's asset.dat. The mask is an
    A8R8G8B8 DDS with 10 levels.
- *Rebuild and timing.* Create-a-Hero module colours are "rebuildable" (bit 30, from 0x4b4a30) only
  while `[0xde3d84]+0x18c` is set; the picker broadcast's colour (0x80959a) never is.
  - A mesh first coloured with a rebuildable colour gets flag +0x320 (0x54c68d). Every later broadcast
    then rebuilds the shared `#mask#-1&0&0&0` texture in place (0x532563 → vtable +0x3c = 0x5321ba →
    0x531c77).
  - A mesh without the flag makes a new `#mask#3&c1&c2&c3` texture at each broadcast, coloured at
    load.
  - Either way, a mesh in a render object that exists at the broadcast follows the pickers. The HLOD
    forwards to every sub-object, hidden ones included (0x59b1a0).
  - The applier gives the row upgrades (bit 4) and the subclass (bits 1|2) before it broadcasts
    (bit 8), and the broadcast (0x6727b0 → slot 0x7c, 0x4b877d) needs only a render object. Our modules
    have one from the subclass state on.
- *asset.dat.* No texture record changed in either cache against `.orig` (0 changed, 0 removed).
  No CaH or `HC_` record is left over from the reverted pack. A texture record has no format or size
  (name, timestamp, one `TEX` entry). RotWK's run order is unchanged (the same 53 joins as EA's);
  BFME2's is sorted. 26 BFME2 records name `_fx` models no archive ships any more; these are
  harmless, and not CaH.
- *Our archives.* The house-colour line set is EA's 2.02 lines plus 38 of ours.
  - Of ours, 17 name cah sheets the pilot does not ship. They are inert: they all land on id -1.
  - The mask providers for EA's lines are identical with and without our archives (53 EA lines have
    no mask in EA's files either).
  - Every hero texture in sagekit-heroes.big has its line, a filed record and an A8R8G8B8 mask.
  - Our only other CaH-adjacent member is `playertemplate.ini`, which adds three heroes to the
    buildable lists.
- *Lint.* `sagekit validate` now runs `sagekit/housecheck.py`. Every housecolor line of ours whose
  texture is shipped must have its `BaseTexture` filed in asset.dat and a mask the colouring handles.
  No archive of ours may serve a mask that it cannot colour. Its self-check has an unfiled base, a
  DXT mask, a 24-bit TGA mask and a missing mask, and each must fail.

**For Max to decide:** our armour can take more colour, and on the Paint picker. Today the Erebor
helm and axe change only a thin band or grip, and only with Skin or Hair, which is EA's rule. The
options are more tinted area, Paint (B) for armour enamel, or leaving armour fixed like EA's. Any of
these is an art change to `kit/paint.py` and the masks: rebuild, review, then install. If an EA body
(cloth, skin, hair) does not change with a picker either, that is the one in-game observation that
would still point at the engine path, and none of the above explains it.

## EA's subclasses

From `python3 -m assets.cah.kit.survey --markdown` (2.02). Lists are the current lengths per row,
in this order: helmet, shoulders, body, gauntlets, weapon, shield, boots. The kit stem is the `<STEM>`
of the naming rules.

| Class file / # | Subclass | _U / _C / _M models (skeleton) | Body sheet / mask | Lists (Hlm Sh Bd Gn Wp Sd Bt) | Weapon sets | Kit stem |
|---|---|---|---|---|---|---|
| menofthewest / 0 | Captain Of Gondor | U CHHW_CG_U_SKN (CHHW_CG_U_SKL)<br>C CHHW_CG_C_SKN (CHHW_CG_C_SKL)<br>M CHHW_MW_M_SKN (CHHW_MW_M_SKL) | CHHW_CG_05.tga / HC_CHHW_CG_05.tga | 6 5 4 6 5 5 6 | WS_03 WS_04 WS_05 WS_06 WS_27 | HWCG |
| menofthewest / 1 | Shield Maiden | U CHHW_SM_U_SKN (CHHW_SM_U_SKL)<br>C CHHW_SM_C_SKN (CHHW_SM_C_SKL)<br>M CHHW_SM_M_SKN (CHHW_SM_M_SKL) | CHHW_SM.tga / HC_CHHW_SM.tga | 5 6 5 6 6 5 6 | WS_03 WS_04 WS_05 WS_06 WS_27 WS_28 | HWSM |
| archer / 0 | Elven Archer | U CHAR_EL_U_SKN (CHAR_AR_U_SKL)<br>C CHAR_EL_C_SKN (CHAR_AR_C_SKL) | CHAR_EL_00.tga / HC_CHAR_EL_00.tga | 4 5 4 5 5 1 4 | WS_02 WS_08 WS_37 WS_38 WS_39 | AREL |
| archer / 1 | Female Elven Archer | U CHAR_FE_U_SKN (CHAR_FE_U_SKL)<br>C CHAR_FE_C_SKN (CHAR_FE_C_SKL) | CHAR_FE.tga / HC_CHAR_FE.tga | 4 7 3 7 5 1 7 | WS_02 WS_08 WS_37 WS_38 WS_39 | ARFE |
| wizard / 0 | Wanderer | U CHWZ_YW_U_SKN (CHWZ_YW_U_SKL)<br>C CHWZ_YW_C_SKN (CHWZ_YW_C_SKL) | CHWZ_WD.tga / HC_CHWZ_WD.tga | 9 3 3 1 6 1 1 | WS_07 WS_09 WS_10 WS_11 WS_40 WS_41 | WZYW |
| wizard / 1 | Avatar | U CHWZ_AV_U_SKN (CHWZ_YW_U_SKL)<br>C CHWZ_AV_C_SKN (CHWZ_YW_C_SKL) | CHWZ_WD.tga / HC_CHWZ_WD.tga | 9 3 3 1 6 1 1 | WS_07 WS_09 WS_10 WS_11 WS_40 WS_41 | WZAV |
| wizard / 2 | Hermit | U CHWZ_HR_U_SKN (CHWZ_YW_U_SKL)<br>C CHWZ_HR_C_SKN (CHWZ_YW_C_SKL) | CHWZ_WD.tga / HC_CHWZ_WD.tga | 9 3 3 1 6 1 1 | WS_07 WS_09 WS_10 WS_11 WS_40 WS_41 | WZHR |
| dwarf / 0 | Taskmaster | U CHDW_TM_U_SKN (CHDW_DW_U_SKL)<br>C CHDW_TM_C_SKN (CHDW_DW_C_SKL) | CHDW_TM.tga / HC_CHDW_TM.tga | 7 7 5 5 4 2 5 (before the pack) | WS_01 WS_31 WS_32 WS_36 | DWTM |
| dwarf / 1 | Sage | U CHDW_SG_U_SKN (CHDW_DW_U_SKL)<br>C CHDW_SG_C_SKN (CHDW_DW_C_SKL) | CHDW_SG.tga / HC_CHDW_SG.tga | 7 7 5 5 4 2 5 (before the pack) | WS_01 WS_31 WS_32 WS_36 | DWSG |
| servantsofsauron / 2 | Orc Raider | U CHSS_OR_U_SKN (CHSS_GB_U_SKL)<br>C CHSS_OR_C_SKN (CHSS_GB_C_SKL) | CHSS_OR.tga / HC_CHSS_OR.tga | 6 6 3 6 6 1 7 | WS_19 WS_20 WS_23 WS_24 WS_28 WS_32 | SSOR |
| servantsofsauron / 3 | Uruk (with armour pieces) | U CHSS_UK_U_SKN (CHSS_UK_U_SKL)<br>C CHSS_UK_C_SKN (CHSS_UK_C_SKL) | CHSS_UK_FA.tga / HC_CHSS_UK_FA.tga | 7 5 4 5 4 3 4 | WS_18 WS_19 WS_20 WS_24 | SSUK |
| corruptedman / 0 | Corrupted Man 1 (Easterling) | U CHCM_CM_U_SKN (CHCM_CM_U_SKL)<br>C CHCM_CM_C_SKN (CHCM_CM_C_SKL) | CHCM_CM_04.tga / HC_CHCM_CM_04.tga | 7 4 7 4 7 1 4 | WS_21 WS_22 WS_23 WS_24 WS_25 WS_26 WS_35 | CMCM |
| corruptedman / 1 | Corrupted Man 2 (Haradrim) | U CHCM_FN_U_SKN (CHCM_CM_U_SKL)<br>C CHCM_FN_C_SKN (CHCM_CM_C_SKL) | CHCM_CM_04.tga / HC_CHCM_CM_04.tga | 7 4 7 4 7 1 4 | WS_21 WS_22 WS_23 WS_24 WS_25 WS_26 WS_35 | CMFN |
| ologhai / 0 | Troll | U CHSS_TL_U_SKN (CHSS_TL_U_SKL)<br>C CHSS_TL_C_SKN (CHSS_TL_C_SKL) | MUMntTroll_CHERO_high.tga / HC_MUMntTroll_CHERO.tga | 5 7 3 7 6 1 2 | WS_12 WS_13 WS_14 WS_15 WS_29 WS_30 | SSTL |
| ologhai / 1 | Snow Troll | U CHTL_ST_U_SKN (CHTL_ST_U_SKL)<br>C CHTL_ST_C_SKN (CHTL_ST_C_SKL) | CHTL_ST_06.TGA / HC_CHTL_ST_06.TGA | 6 2 8 6 3 1 2 | WS_33 WS_34 WS_42 | TLST |
| ologhai / 2 | Hill Troll | U CHTL_HT_U_SKN (CHTL_HT_U_SKL)<br>C CHTL_HT_C_SKN (CHTL_HT_C_SKL) | CHTL_HT_05.tga / HC_CHTL_HT_05.tga | 6 2 8 6 3 1 2 | WS_33 WS_34 WS_42 | TLHT |

### Notes for the class groups

- **Men of the West:**
  - Each subclass has a mounted model. The Captain's is `CHHW_MW_M_SKN` on its own skeleton, so it
    needs `FIT_REFS` parts it shares with the _U model.
  - Template candidates: `BOOT_05` (`CHHW_CG_OF3D_BOOT_05.tga`, `CHHW_SM_OF3D_BOOT_05.tga`).
- **Wizards:** three subclasses share skeleton `CHWZ_YW_U_SKL` / `CHWZ_YW_C_SKL` (parts sit
  identically), each with its own body. Template: `HLMT_08` (`CHWZ_WZ_OF3D_HLMT_08.tga`).
- **Archers:**
  - Elves and the female archer have different skeletons (`CHAR_AR_*`, `CHAR_FE_*`) and no parts in
    common to fit. Use one folder per subclass (`assets/cah/archer_el`, `assets/cah/archer_fe`), both
    with `CLASS_FILE = "archer"`; the pack composes both onto `createaherosystemarcher.inc` by
    subclass index. The same applies to any subclass that cannot share a design model.
  - Bows have two weapon sets (ranged on `WEAPONSET_TOGGLE_1`, melee); `WEAPON_LIKE` copies both.
  - Bows also show `WestronSword` for melee (`ALSO_SHOW`).
  - Templates: `HLMT_03` (`CHAR_EL_OF3D_HLMT_03.tga`), `HLMT_05` (`CHAR_FE_OF3D_HLMT_03.tga`).
- **Evil:**
  - Servants of Sauron's subclass 0 (a troll) is commented out in EA's file. The class has the Orc
    Raider (2) and Uruk (3).
  - The Olog-hai troll uses `CHSS_TL_*`.
  - Snow and Hill trolls are `CHTL_*` with 38-45 meshes each.
  - Templates: `BOOT_06` (Orc), `SLDR_04` (Uruk), `HLMT_08` (Corrupted Man), `HLMT_02` (trolls,
    `MUMntTroll_CHERO_high.tga`).
  - The 7 subclasses span 6 skeletons, so `assets/cah/evil/` has no `design.py`: it measures each
    model from EA's own parts and fits every part to it, drawn in the model's own rest space
    (`OWN_SPACE` in `kit/models.py`).
  - Their parts take the shared row upgrades like every class.
