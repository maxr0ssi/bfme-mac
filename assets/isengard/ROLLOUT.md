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
   [`atlas.py`](atlas.py), read by eye; confirm on the citadel's first bake. Nine buildings paint
   EA's faces from sheets of their own (armory, battle tower, furnace, lumber mill, siege works,
   tavern, uruk pit, warg pit and its door, warg sentry): `atlas.py` `SHEETS` gives each its own
   rects (iron, mark for the Hand banners and bone, stone, rock, wood for timber, hide and fur;
   the first rect a texel falls in wins; the damaged and snow states share the layout), and
   `IsengardSheetRecolour` reads them on EA's faces, IBFortress's on new faces, and on the flat
   sheets `sagekit sheets` recolours (`IsengardStyle.sheet_atlas`). Fire is found by colour only
   outside every rect, so the lumber mill's rust no longer glows; the furnace's melt still does.
   Checked 2026-09-29: the flat IBFortress recolour and the citadel's recolour on its bake are
   bit-identical to before; new faces on a table's building are unchanged. Before this, those
   nine sheets' wood, hide, bone and banners came out iron or silver (IBFortress's rects read
   through the wrong layout). The rects were read by eye: confirm on each first bake.

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

### Walls (shape previews, pass 3, 2026-09-29)

One wall profile in [`shapes_walls.py`](shapes_walls.py) on every wall piece, so segments, hubs,
the gate and the ends join without a seam. Fire only on the gate and the tower. Pass 3 brings the
hubs and the tower up to the citadel: pass 1's hubs were still EA's drums with a small crown of
horns and the tower barely changed. The hubs get the citadel's cluster (a needle stack between
two lozenge blades) on the roof, the tower four corner blades and a needle stack out of its
crown; both may grow 35 %, as the citadel. Sheet: `_review/walls_v3.jpg` (pass 1: `walls.jpg`).

| Building | Idea | Tris EA -> ours | Height | Fire |
|---|---|---|---|---|
| wall_segment | knife fins, buttress blades, ember slits, silver lip and ridge, lip spikes, needles out of EA's pyramids (fork, needle, NEEDLE, needle, fork); unchanged in pass 3 (it repeats) | 376 -> 1,218 | +11.4 % | none |
| wall_hub | the citadel's cluster on the roof: a needle stack (ember collar and throat) between two lozenge blades to model 84, the walls' needles on the six corners, spikes, silver arrises, slits | 258 -> 3,052 | +34.6 % | none |
| fortress_wall_hub | the hub's blade cluster; the walls' profile on the stub | 476 -> 3,976 | +34.6 % | none |
| wall_gate | two tridents (a blade tower between each pylon's horns), bracket braziers, slits, spikes, one banner and one Hand in an arch slot a face | 200 -> 2,814 | +17.1 % | 4 brazier |
| wall_end | two segments' profile, a blade tower at the cut end | 822 -> 3,296 | +19.7 % | none |
| tower | four lozenge blades on the shaft's corners to z 121 (the Hand on the field pair), a needle stack out of the crown to z 166, braziers in the crown, glowing windows, a banner, the profile on its stub | 848 -> 4,752 | +27.4 % | chimney, 4 brazier |

### Production (shape previews, pass 3, 2026-09-29)

The forge-and-industry heart: fire belongs here most. Pass 1 (`_review/production_v1.jpg`) was
too modest; pass 2 (`_review/production.jpg`) gave each one or two big pointed masses but still
read modest beside the citadel. Pass 3 applies the citadel's recipe to each: its pair (two
matching lozenge blades, the White Hand in a pointed-arch slot on each one's outer face) either
side of the building's central element in the RTS view, needle stacks, ember slits, fire. The
group's small pieces (fins, forges, birthing pits, banner frames, armour stands, racks) are in
[`shapes_industry.py`](shapes_industry.py), the big masses (spire stacks, tridents, pyramid kilns,
the pair, the birthing spire, a crane, a siege tower, a ram, a dorsal crest, a log crib) in
[`shapes_industry_big.py`](shapes_industry_big.py). No round drums: kilns and crucibles are
square and turned to a corner. Every building stays inside +20 % height, so the pairs on the low
ones (armory, lumber mill, warg pit, at z 48-56) are shorter than the citadel's. Sheet:
`_review/production_v3.jpg` (the citadel's rts on top, then EA's against ours, rts and close).

| Building | Idea | Tris EA -> ours | Height | Fire |
|---|---|---|---|---|
| furnace | the smelter crowned: the pair out of the mound's top either side of the crater (to z 128.5, the left foot above the level-up hut), Hands, chains to the great chimney (a needle stack out of the crater); buttresses, a hooded tap, a crucible gantry over the mould, a forge, racks | 1,141 -> 6,073 | +19.2 % | 9: chimney, furnace, 3 crucible, hearth, 3 brazier |
| armory | the Uruk armoury: the pair either side of the iron hall's +X gable (to z 54.4, the limit), Hands, the gable's great Hand between; the hall (ridge z 44, a crest), a stack through its roof, a forge, three Uruk harnesses, racks | 468 -> 5,183 | +19.4 % | 6: chimney, hearth, crucible, 3 brazier |
| lumber_mill | Fangorn's end: the pair, two great spire stacks out of low square kilns either side of the banner; a lozenge crane over a crib of felled Fangorn, a blade crest on the shed, a frame saw | 1,204 -> 4,784 | +18.8 % | 5: 2 chimney, hearth (EA's fire pit), 2 brazier |
| siege_works | the war-yard: the pair, two tridents flanking the mouth, each's middle the citadel's broad blade with a Hand slot, fire grates in their saddles, a chain and a great Hand shield between; the half-built siege tower outside the -Y edge over the awning, needles out of the post heads, a ram, a forge | 932 -> 7,602 | +18.3 % | 8: 4 furnace, 2 brazier, hearth, crucible |
| uruk_pit | the breeding pits: the pair either side of the pit (to z 77.5), Hands; a pointed birthing spire over the pit (four knife ribs on a square, four iron bars, hooks), chimneys behind, fins on the +X lobe, furnace mouths, a birthing pit, harness | 1,087 -> 6,099 | +19.2 % | 8: grate, 2 chimney, 2 furnace, embers, 2 brazier |
| warg_pit | the kennels: the pair either side of the pit (one on the palisade's front, one outside its back, to z 55.5), Hands, a needle chimney behind the pit on the axis; the gatehouse over the run (two blade gate towers, a pointed lintel with the Hand), iron bands, hooks | 3,224 -> 7,114 | +19.7 % | 3: chimney, 2 brazier |
| tavern | the hall of the White Hand: the pair out of the roof slopes either side of the dorsal crest (z 28 to 77.5), Hands, chains to the crest's tall fin; one great chimney behind the crest, crossed blades over the gables, the Hand over the door | 1,848 -> 4,656 | +19.4 % | 1: chimney (EA's torches stay) |
| warg_pit_02 | the door: stays EA's; the stub stays as the record of that | - | - | - |

### Add-ons and expansions (shape previews, pass 3, 2026-09-29)

The citadel's upgrades, checked on our citadel with every upgrade built at once (no vertex inside
the citadel's new solids either way, none on its fire points, the wheel's real sweep and the
excavations' A-frame and bucket sweep (`IBFExcavAN`) clear), and the expansions. Pass 1
(`_review/addons.jpg`) kept most expansions at EA's height; pass 3 brings each up to the citadel:
the expansions get the citadel's pair of lozenge blades, mirrored about their own axis, flanking
EA's central element. Shared pieces (Orthanc's piers and horns, pointed merlons, arch slots with
the Hand, fire-pots, the blade helpers `blade_pair`, `blade_hand`, `foot_spurs`) are in
[`shapes_addons.py`](shapes_addons.py). Sheet: `_review/addons_v3.jpg` (the citadel's approved rts
render on top, then EA's against ours, rts and close; the add-ons on the citadel).

| Building | Idea | Tris EA -> ours | Height | Fire |
|---|---|---|---|---|
| fortress_wizards_tower | Orthanc (identity kept): four many-sided piers opening into horns, ember windows, a door and the Hand, Saruman's balcony; the Hand great high on three faces, braziers on the piers | 1,572 -> 5,486 | +13.8 % | 6 brazier |
| fortress_burning_forges | the wheel: ribs, ember vents and a boss, all inside the forge's slot (unchanged: it turns) | 957 -> 1,513 | 0 % | none (it turns) |
| fortress_burning_forges_destructibles | the forge: EA's round stack carried on as the citadel's needle chimney to z 138, a beacon on the frame's roof, hearth, anvil and bellows, a molten chute, fins and vents | 969 -> 2,149 | +19.6 % | 5: chimney, brazier, hearth, embers, crucible |
| fortress_excavations | the pits of Isengard: the south shaft a needle flue (under the A-frame's swing), fire out of the north shafts, terrace spikes, an ore cart | 875 -> 2,012 | 0 % | 3 chimney |
| fortress_excavations_destructibles | glowing ore down the chute out of an iron skip, a fire basket, a lantern | 374 -> 574 | 0 % | 2: embers, brazier |
| fortress_orcfire_munitions | war-engine fire-pots: claws of knife blades, iron rims, silver lips, spikes, ember bands, orcfire jars | 920 -> 4,200 | +1.9 % | 5 brazier |
| ballista | the pair against the long walls behind the ballista to z 68.5, a crown of pointed merlons, Hands, fins, loops, a prow blade | 234 -> 3,188 | +34.3 % (0.35: Max's OK pending) | 2 brazier |
| battle_tower | the pair welded to the shaft, through the roof to needles either side of EA's spike, Hands, bands, slits, eaves spikes | 541 -> 3,412 | +19.2 % | 4 brazier |
| warg_sentry | the pair as pylons on the back rim, chained to the Hand standard between them; palisade, warg posts, stakes; the middle clear for the wargs | 3,013 -> 6,841 | +34.1 % (0.35: Max's OK pending) | 5: grate, 4 brazier |
| mine_launcher | the pair flanking EA's spiked tower to needles over it, Hands on them, merlons and fins on the front, ramp jaws, orcfire mines | 1,094 -> 4,110 | +19.1 % | 2: brazier, furnace |

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
   `sagekit sheets` lists TGA-only sheets too (2026-09-29): `ibwildbuilding`, `_d`, `_snow` and
   `_bib` are recoloured and ship as TGA at EA's path, size and depth, so the tavern's EA meshes
   (V1 hide walls, V3 stakes, the torch posts) and its rubble and building site take the palette.
   `ibclansteading.tga` (the tavern's button) and the unused `_bib_snow` stay EA's. The sheet's
   pelt (the hide walls) paints as dark hide, a rock rect toned to 0.4 (atlas.py SHEETS), not
   the wood ramp's tan.
