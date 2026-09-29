# Isengard: building rollout

**Status: 25 measured stubs; palette A with silver (Max's pick); the citadel's third shape pass
(2026-09-28).** Nothing is built or installed. Every recipe passes `sagekit validate`. Template:
[`assets/goblins/ROLLOUT.md`](../goblins/ROLLOUT.md); the loop is in
[docs/FACTIONS-PLAN.md](../../docs/FACTIONS-PLAN.md).

## Where to look

Build output is under `build/assets/isengard/` (not in git; each player builds their own).

- Style board, EA's Isengard buildings as they are: `_board/isengard_board.jpg`
  (`python3 -m sagekit board isengard`; last row: the level-up meshes shown).
- The palette on EA's citadel: `_palettes/palette_options.jpg` (`sagekit palettes isengard`), EA
  beside A; the three first options: `palette_options_v1.jpg`.
- The citadel: `_review/citadel.jpg` (pass 3; EA against ours at the rts, close and keep
  views), passes 1 and 2 in `citadel_v1.jpg`, `citadel_v2.jpg`; see [fortress](fortress/README.md).
- Each stub's docstring: EA's facts, target, lifecycle models and house colour. Measurements:
  `<building>/work/measure.json`.

## Design

1. **Palette: A, "Orthanc black and silver"** ([`style.py`](style.py)): near-black faceted stone,
   dark iron, ember orange, and silver-white on the polished edges (EA's brightest metal texels,
   the new "trim" faces) and the White Hand. B and C are retired. No crimson and no bone (the
   Goblins'); Mordor will want red and black steel, so Isengard's black is stone.
2. **Kit**: [`shapes.py`](shapes.py) (faceted stone, the four-horned crown, furnace stacks),
   [`shapes_works.py`](shapes_works.py) (riveted plate, hoops, chains, gears, pulleys, vents,
   slag, hooks, spike rows, pike racks, the White Hand, heavy banners on iron frames) and
   [`shapes_yard.py`](shapes_yard.py) (stumps, logs, a frame saw, hearths, anvils, bellows,
   crucibles, gantries, a water wheel and flume, scaffolding, siege ladders, Uruk shields and
   racks, pipework, fire grates).
3. **Paint**: [`paint.py`](paint.py) `IsengardRecolour` splits EA's sheet into stone (the smooth
   panels), rock, wood, the Hand's white, embers (by colour) and iron (the rest), rects in
   [`atlas.py`](atlas.py), read by eye; confirm on the citadel's first bake.

## Units

25 recipes. Scaffolder picks, checked by hand:

| Stub | EA model / target (tris) | Check |
|---|---|---|
| fortress | `IBFortress` / `IBFORTRESS` (3876) | ok; `IBFORTRESSB` (48) stays EA's; drawn by IsengardFortressCitadel and IsengardFortress |
| fortress_orcfire_munitions | `IBFOrcfire` / `IBFORCFIRE` (920) | ok; on the walls (z 52.7..93.7); fire cards `MBFDPF`, `MBFDPFG` stay EA's |
| fortress_excavations | `IBFExcav` / `IBFEXCAV` (875) | ok; `IBFEXCAVAT2`..`AT5` (28-314) are more of it: check whether they animate before designing |
| fortress_excavations_destructibles | `IBFExcavB` / `IBFEXCAVB` (374) | ok |
| fortress_burning_forges | `IBFBForges` / `IBFBFORGESA` (957) | ok, but it hangs on a bone (z -16..16 round its pivot): check where it stands on the citadel |
| fortress_burning_forges_destructibles | `IBFBForgB` / `IBFBFORGES` (971) | ok; folder renamed from EA's tag spelling (`...Descrutbiles`) |
| fortress_wizards_tower | `IBFWTower` / `IBFWTOWER` (1572) | ok; the courtyard's Orthanc (to z 175.7) |
| ballista, tower, mine_launcher | `IBFBalTow`, `IBFITower`, `IBFMLaunch` | ok; expansions, no house model (HOUSE_DRAW); the launcher's `BOMB1`-`3` are unit art |
| fortress_wall_hub | `IBFWHub` / `IBFBALTOW01` (476) | ok; z -25.5..37 (its foot is buried) |
| wall_segment, wall_hub, wall_end | `IBWallN`, `IBWallRmprtN`, `IBWallNE` | ok; the hub's mesh is also named `IBFBALTOW01`, the end's `IBWALLN` (other models) |
| wall_gate | `IBWallGateN_SKN` / `IBGATE` (200) | ok: the frame; the leaves `IBGATEDOOR01`/`02` (712 each) are bigger and animate |
| armory | `IBArmory_SKN` / `IBARMORY` (468) | **fixed**: the scaffolder took the treadwheel `IBARMORYWHEEL1` (525, a bone tilted 8 degrees, its rim to z -32.7); world_space dropped, views re-centred |
| battle_tower | `IBBtlTwr` / `TOWER` (541) | ok; `IBBtlTwrM` (its copy) is drawn by Mordor's base defence |
| siege_works | `IBSeigeWork` / `IBSEIGEFRAME` (932) | ok; `IBSEIGEWALLS` (228, own sheet `IBSeigeWall`) stays EA's; V2 is the level-up |
| uruk_pit | `IBUrukPit_SKN` / `IBURUKPIT_NEW` (1087) | ok; V2 (792) the level-up |
| warg_pit | `IBWARGPIT` / `IPWARGPIT` (3224) | ok (EA's mesh name); V2 the level-up |
| warg_pit_02 | `IBWARGPIT_DRC` (158) | **not a unit**: the warg pit's door (closed; `_DRO` open), its own Draw module. Fold into warg_pit or leave EA's; the stub can go |
| warg_sentry | `IBWargSent` / `IBWARGSENT` (3013) | ok |
| furnace | `MBFurnace_SKN` / `FURNACE` (1141) | ok; Mordor's name but drawn by Isengard only; `MOLD`, `INGOTS`, `SHOVEL`, `LIQUIDMETAL1` stay EA's; V2 the level-up |
| lumber_mill | `MBLumMill_SKN` / `LUMBERMILL` (1204) | ok; ships as own model `IBLumMill_SKN`, own sheet `MBLumberMilX.tga` (the Goblins' is `...MilH`); V2 the level-up |
| tavern | `ibwildbld_skn` / `BUILDING` (1848) | check: `IsengardTavern` may be a captured map building, not player-built; house model is Mordor's `MBHCOrcpit` (own copy) |

Not units: the crebain (`Crebain_SKN`), the forge worker (`IBFBForgesU_SKN`), the launcher's
crew, the siege works' wheels (`IBSeigeW_DRC`) and `IBWARGPIT_WLB` (no static body).

## Ownership (`sagekit owners isengard`)

- `WBCave` (the Goblin cave's sheet): Isengard draws it only on the night-only torch posts
  (`N_WINDOW`) of the armory, furnace, siege works, uruk pit, warg pit, warg sentry and lumber
  mill; Goblins and Mordor draw it too. `IsengardStyle.night` stays None, so those stay EA's and
  the sheet is never recoloured.
- `MBLumMill_*`, `MBLumberMill*`, `MBHCLumberMill`: Goblins and Mordor draw them too. Own model
  `IBLumMill_SKN`, own sheet `MBLumberMilX.tga`, own house copy (automatic).
- `MBFurnace*`, `MBHCFurnace`: Isengard's only, despite the name. No own copy needed.
- `MBHCOrcpit` (the tavern's house model): Mordor's orc pit draws it: own house copy (automatic).
- `IBCCenter*` and sheets `ibccenter01`, `ibccenter01_d`, `ibccenter02`: the Goblins' camp keep
  draws them; not an Isengard unit; `sagekit sheets` skips them.
- `IBBtlTwrM` / `ibbtltwrm`: Mordor's base defence foundation draws it; skipped by `sheets`.
- `ibfoundation`: the Men's INI swaps use it; skipped by `sheets`.
- `Evil_House_Color_Flag`: every evil faction's banners; the house step's own copies handle it.
- Everything else the stubs ship is Isengard's own (70 of 75 sheets).

## Banners

Few and heavy: iron frames (top bar on brackets, side rods, a weighted foot, a V-cut foot), the
White Hand raised on the cloth, cloth in the player's colour. The citadel has three.

## Open

1. The house template for the expansions (`IBHCBtlTwr` set, unchecked).
2. Night look: none yet (EA's night meshes stay).
3. Checked (2026-09-28): no vertex of the excavations, burning forges or wizard's tower upgrade
   lies inside the citadel's new solids; one glow card of the orcfire upgrade (MBFDPFG) dips
   1.4 into the foundry's tier 2 under its roof.
