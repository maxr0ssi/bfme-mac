# Isengard: building rollout

**Status: 25 measured stubs; palette A with silver (Max's pick); the citadel's sixth pass built in colour
with fire and small details (2026-09-29).** Nothing is installed. Every recipe passes `sagekit validate`. Template:
[`assets/goblins/ROLLOUT.md`](../goblins/ROLLOUT.md); the loop is in
[docs/FACTIONS-PLAN.md](../../docs/FACTIONS-PLAN.md).

## Where to look

Build output is under `build/assets/isengard/` (not in git; each player builds their own).

- Style board, EA's Isengard buildings as they are: `_board/isengard_board.jpg`
  (`python3 -m sagekit board isengard`; last row: the level-up meshes shown).
- The palette on EA's citadel: `_palettes/palette_options.jpg` (`sagekit palettes isengard`), EA
  beside A; the three first options: `palette_options_v1.jpg`.
- The citadel: `_review/citadel.jpg` (pass 6; passes 4-6 side by side at the RTS view, then EA
  against ours at the rts, close and keep views), earlier sheets `citadel_v1.jpg` .. `citadel_v5.jpg`; see [fortress](fortress/README.md).
- Each stub's docstring: EA's facts, target, lifecycle models and house colour. Measurements:
  `<building>/work/measure.json`.

## Design

1. **Palette: A, "Orthanc black and silver"** ([`style.py`](style.py)): near-black faceted stone,
   dark iron, ember orange, and silver-white on the polished edges (EA's brightest metal texels,
   the new "trim" faces) and the White Hand. B and C are retired. No crimson and no bone (the
   Goblins'); Mordor will want red and black steel, so Isengard's black is stone.
2. **Kit**: [`shapes.py`](shapes.py) (EA's points: knife-edge fins, 35-degree gables, obelisk
   stacks; faceted stone, the four-horned crown and round stacks of the first passes),
   [`shapes_spire.py`](shapes_spire.py) (lozenge blade towers and needle chimneys),
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
| fortress_excavations | `IBFExcav` / `IBFEXCAV` (875) | ok; `IBFEXCAVAT2`..`AT5` (28-314) **animate** (`IBFExcavAN`: AT2 the skinned A-frame and rope, AT5 the bucket rising out of the north shafts): stay EA's, their sweep kept clear |
| fortress_excavations_destructibles | `IBFExcavB` / `IBFEXCAVB` (374) | ok |
| fortress_burning_forges | `IBFBForges` / `IBFBFORGESA` (957) | ok: the forge's wheel, on a bone at (-42.1, 4.5, 66.2), turning about y (`IBFBForges_AN`) through the forge tower's slot |
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
| warg_pit_02 | `IBWARGPIT_DRC` (158) | **not a unit**: the warg pit's door (closed; `_DRO` open), its own Draw module. **Stays EA's** (2026-09-29): five models, two animated; the warg pit frames it. Not to be built; dropping the stub is Max's call |
| warg_sentry | `IBWargSent` / `IBWARGSENT` (3013) | ok |
| furnace | `MBFurnace_SKN` / `FURNACE` (1141) | ok; Mordor's name but drawn by Isengard only; `MOLD`, `INGOTS`, `SHOVEL`, `LIQUIDMETAL1` stay EA's; V2 the level-up |
| lumber_mill | `MBLumMill_SKN` / `LUMBERMILL` (1204) | ok; ships as own model `IBLumMill_SKN`, own sheet `MBLumberMilX.tga` (the Goblins' is `...MilH`); V2 the level-up |
| tavern | `ibwildbld_skn` / `BUILDING` (1848) | **checked**: player-built (slot 6 of `IsengardPorterCommandSet`, the Dunland hall); house model is Mordor's `MBHCOrcpit` (own copy); its sheets are TGA, not DDS (read since 2026-09-29, Open 4) |

Not units: the crebain (`Crebain_SKN`), the forge worker (`IBFBForgesU_SKN`), the launcher's
crew, the siege works' wheels (`IBSeigeW_DRC`) and `IBWARGPIT_WLB` (no static body).

### Walls (shape previews, 2026-09-29)

One wall profile in [`shapes_walls.py`](shapes_walls.py) on every wall piece, so segments, hubs,
the gate and the ends join without a seam. Fire only on the gate and the tower. Sheet:
`_review/walls.jpg`.

| Building | Idea | Tris EA -> ours | Height | Fire |
|---|---|---|---|---|
| wall_segment | knife fins, buttress blades, ember slits, silver lip and ridge, lip spikes, needles out of EA's pyramids (fork, needle, NEEDLE, needle, fork) | 376 -> 1,218 | +11.4 % | none |
| wall_hub | Orthanc crown: six horns, stepped plinth and needle, radial ribs, spikes, silver arrises, slits | 258 -> 1,390 | +19.9 % | none |
| fortress_wall_hub | the hub's crown; the walls' profile on the stub | 476 -> 2,314 | +19.9 % | none |
| wall_gate | two tridents (a blade tower between each pylon's horns), bracket braziers, slits, spikes, one banner a face | 200 -> 2,492 | +17.1 % | 4 brazier |
| wall_end | two segments' profile, a blade tower at the cut end | 822 -> 3,296 | +19.7 % | none |
| tower | bracket braziers under the crown, glowing windows, a banner, the profile on its stub | 848 -> 2,108 | 0 % | 4 brazier |

### Production (shape previews, pass 2, 2026-09-29)

The forge-and-industry heart: fire belongs here most. Pass 1 (`_review/production_v1.jpg`) was
too modest: at the RTS view most buildings read as EA's. Pass 2 gives each one or two big pointed
masses. The group's small pieces (fins, forges, birthing pits, banner frames, armour stands,
racks) are in [`shapes_industry.py`](shapes_industry.py), the big masses (spire stacks, tridents,
pyramid kilns, a birthing-frame, a crane, a siege tower, a ram, a dorsal crest, a log crib) in
[`shapes_industry_big.py`](shapes_industry_big.py). No round drums: kilns and crucibles are
square and turned to a corner. Sheet: `_review/production.jpg` (EA's against ours, rts and close).

| Building | Idea | Tris EA -> ours | Height | Fire |
|---|---|---|---|---|
| furnace | the smelter: a blade-spire stack out of the crater between the horns to z 128, layered stone buttresses on the mound, an iron crown round the crater, a hooded tap, a crucible gantry over the mould, a forge, racks | 1,141 -> 4,431 | +15.8 % | 9: chimney, furnace, 3 crucible, hearth, 3 brazier |
| armory | the Uruk armoury: the shed an iron hall (a steep pointed roof, stone gables, the Hand great in the +X gable, corner fins), a stack through its roof, a forge, three Uruk harnesses, racks | 468 -> 3,481 | +17.0 % | 6: chimney, hearth, crucible, 3 brazier |
| lumber_mill | Fangorn's end: a pair of steep square kilns with the banner between, a lozenge crane over a crib of felled Fangorn, a blade crest on the shed, a frame saw | 1,204 -> 3,836 | +18.8 % | 5: 2 chimney, hearth (EA's fire pit), 2 brazier |
| siege_works | the war-yard: trident towers flanking the mouth with a chain and the Hand between, needles out of the post heads, a half-built siege tower and a ram under the awning, a forge | 932 -> 6,692 | +18.3 % | 4: 2 brazier, hearth, crucible |
| uruk_pit | the breeding pits: an iron birthing-frame over the pit (six knife ribs to a needle, hooks), a needle stack either side, fins on the +X lobe, furnace mouths, a birthing pit, harness | 1,087 -> 4,561 | +18.5 % | 8: grate, 2 chimney, 2 furnace, embers, 2 brazier |
| warg_pit | the kennels: a gatehouse over the run (two blade gate towers, a pointed lintel with the Hand), blade pylons in the ring's corners, iron bands, hooks | 3,224 -> 5,586 | +19.7 % | 2 brazier |
| tavern | the hall of the White Hand: a dorsal crest of seven knife fins along the ridge, crossed blades over the gables, two spire stacks through the roof, the Hand over the door | 1,848 -> 3,020 | +17.0 % | 2 chimney |
| warg_pit_02 | the door: stays EA's; the stub stays as the record of that | - | - | - |

### Add-ons and expansions (shape previews, 2026-09-29)

The citadel's upgrades, checked on our citadel with every upgrade built at once (no vertex inside
the citadel's new solids either way, none on its fire points, the wheel's and the bucket's sweeps
clear), and the expansions. Shared pieces (Orthanc's piers and horns, pointed merlons, arch slots
with the Hand, fire-pots) are in [`shapes_addons.py`](shapes_addons.py). Sheet:
`_review/addons.jpg` (EA's against ours, rts and close views; the add-ons on the citadel).

| Building | Idea | Tris EA -> ours | Height | Fire |
|---|---|---|---|---|
| fortress_wizards_tower | Orthanc: four many-sided piers on the diagonals opening into horns, ember windows, a door and the Hand, Saruman's balcony | 1,572 -> 4,631 | +13.8 % | none |
| fortress_burning_forges | the wheel: ribs, ember vents and a boss, all inside the forge's slot | 957 -> 1,513 | 0 % | none (it turns) |
| fortress_burning_forges_destructibles | the forge: a beacon on the frame's roof, the stack's blade crown, hearth, anvil and bellows, a molten chute, fins and vents | 969 -> 1,943 | 0 % | 5: chimney, brazier, hearth, embers, crucible |
| fortress_excavations | the pits of Isengard: fire and smoke out of the shafts, a grate and stakes on the south one, terrace spikes, an ore cart | 875 -> 1,860 | 0 % | 3 chimney |
| fortress_excavations_destructibles | glowing ore down the chute out of an iron skip, a lantern | 374 -> 500 | 0 % | none |
| fortress_orcfire_munitions | war-engine fire-pots: iron rims, silver lips, spikes, blades, ember bands, orcfire jars | 920 -> 4,200 | 0 % | 5 brazier |
| ballista | pointed merlons round the top, the Hand each side, arrow loops, fins, a prow blade | 234 -> 1,206 | +13.9 % | 2 brazier |
| battle_tower | corner fins, riveted bands, the Hand, arrow slits, eaves spikes | 541 -> 1,382 | 0 % | 2 brazier |
| warg_sentry | the kennel: a palisade, warg posts and chains, stakes, a Hand standard; the middle clear for the wargs | 3,013 -> 4,819 | 0 % | 3: grate, 2 brazier |
| mine_launcher | merlons and fins on the front, the Hand and slits on the tower, ramp jaws, orcfire mines | 1,094 -> 2,386 | 0 % | 2: brazier, furnace |

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
2. Night look: none yet (EA's night meshes stay). Real flicker for the citadel's fires needs
   bones of our own and `ParticleSysBone` lines in the INI step: a framework item.
3. Checked (2026-09-29): no vertex of the excavations, burning forges, wizard's tower or
   orcfire upgrade lies inside the citadel's new solids.
4. TGA-only sheets (the tavern's `ibwildbuilding` family): fixed 2026-09-29, the extract step
   reads a sheet's DDS, else its TGA, and the tavern's snow swap is a variant (docs/ART.md).
   `sagekit sheets` still lists DDS sheets only: the tavern's states that stay EA's (rubble, the
   building site) keep EA's colours until it lists TGA-only sheets too.
