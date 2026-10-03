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
- Other limits: 3 colours with a free picker, 8 class slots, 5 subclasses per class, 64 weapon-set
  flags (EA uses 40).

## Layout

| Path | What |
|---|---|
| `assets/cah/kit/` | the shared kit: `geom.py` (primitives, lod trimming), `ornament.py`, `paint.py` (sheet painter, masks), `models.py` (sources, model copies, checks), `ini.py` (fragments, composition, lint), `survey.py`, `render.py` |
| `assets/cah/<class>/` | a class: `design.py` (its spec), `build.py`, `paint.py` (tile tables), its part designs |
| `assets/cah/pack/design.py` | the one unit recipe: the archive name and every class's mask lines (shared house-colour INI) |
| `sagekit/units/cah.py` | stage, install and revert the whole pack |
| `sagekit/blender/cah_pose.py` | the renders' Blender side |

## Commands

```sh
python3 -m assets.cah.kit.survey --markdown        # EA's subclasses (the table below)
python3 -m assets.cah.<class>.build [--skip-paint] # sources, sheets, models, INI fragment, every check
python3 -m assets.cah.kit.render <class>           # build/assets/cah/<class>/renders/overview.png (one Blender)
python3 -m sagekit.units.cah --stage               # compose all classes, lint, pack, asset.dat round trip
python3 -m sagekit.units.cah --install [--dry-run] # one archive, records, shared house-colour INI
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

A part's design function draws into a `Gear` (`kit/geom.py`): `shell`, `sweep`, `tube`, `stud`, `slab`,
`loft`, `blade`, `ribbon`, all in the design model's rest space and each bound to an EA bone. Never
reorder or remove an entry once a build has shipped: append only.

## Naming (never collide)

| Thing | Rule | Example |
|---|---|---|
| Upgrades | `Upgrade_SKH_<STEM>_<CHH|CHSP|CHBOD|CHG|CHS|CHB><nn>` per subclass stem (table), `nn` from 01 | `Upgrade_SKH_ARFE_CHH01` |
| Weapon upgrades | `Upgrade_SKH_CHW<nn>`, `nn` = its own flag `WEAPONSET_CREATE_A_HERO_WS_<nn>` | `Upgrade_SKH_CHW52` |
| Weapon-set flags | Dwarf 43-45 (used). **Men + Wizards 46-51, Archers 52-57, Orc/Uruk/Corrupted Man/Olog-hai 58-64** | |
| Sub-objects (≤ 15 chars) | `SK<STEM>_<PART>`, globally unique | `SKARFE_HOODPK` |
| Model copies | EA's name with `CH` → `SK` | `SKHW_SM_M_SKN` |
| Sheets (≤ the template's texture name) | `SKCAH_<FAM>GEAR.tga`, `SKCAH_<FAM>FUN.tga`; masks `HC_` + sheet | `SKCAH_ARGEAR.tga` |
| INI module tags | made by the kit (`SKH_Show_<sub-object>`, `SKH_Remove_<upgrade>`, `SKH_Weapon_<upgrade>`) | |

The Dwarf keeps its first names (`Upgrade_SKH_DWARF_…`, `SKH_*` sub-objects). `<FAM>` is the
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
  ours) must each fail.
- **Pack (`--stage`):** no member another archive serves first; nothing filed twice; asset.dat
  staged and reverted on copies gives back today's records byte for byte.

## Not covered yet

- The **body** row: EA swaps the body texture there (`UpgradeTexture`); the kit adds sub-objects only.
- Per-entry names.
- New rows.

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
  - Shared upgrades use class stems: `Upgrade_SKH_SOS_…`, `_CMEN_…`, `_OLOG_…`.
