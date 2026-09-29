# Goblins (Misty Mountains): building rollout

**Status: palette E; all 14 buildings are built and installed (2026-09-28).** Every recipe passes
`sagekit validate` (136 of 512 MB) and its checks. Colour review sheets:
`build/assets/goblins/_review/fortress_colour.jpg`, `production_colour.jpg`. No Goblin night look
yet: EA's night pieces stay. Template: [`assets/men/ROLLOUT.md`](../men/ROLLOUT.md); the loop is in
[docs/FACTIONS-PLAN.md](../../docs/FACTIONS-PLAN.md).

## Where to look

Build output is under `build/assets/goblins/` (not in git; each player builds their own).

- Style board, EA's Goblin buildings as they are: `build/assets/goblins/_board/goblins_board.jpg`
  (level-3 row: the V1/V1A/V2 level-up meshes). Tiles: `build/assets/goblins/_board/out/ea_*.png`.
- Palette options on EA's citadel: `build/assets/goblins/_palettes/palette_options.jpg` (A-C) and
  `palette_options_2.jpg` (D, E). E is the palette in [`style.py`](style.py); A-D are retired.
- The citadel and throne: `build/assets/goblins/fortress/renders/citadel_review.jpg`,
  `build/assets/goblins/fortress_throne/renders/`; see [fortress](fortress/README.md) and
  [fortress_throne](fortress_throne/README.md).
- Each stub's docstring: EA's facts, target, lifecycle models and house colour. Measurements:
  `build/assets/goblins/<building>/work/measure.json`.
- The bar for every building: the Dwarven before/after renders and the Goblin citadel. Keep EA's
  detailed body and enrich it; never strip it.

## Design

1. **Palette: E, "Blood, iron and bone"**: crimson horn and hide, gritty silver iron, near-black
   rock and charcoal timber, bleached bone as accents. A-D stay in `style.py` for comparison until
   they are retired.
2. **Kit**: [`shapes.py`](shapes.py) (horns, spikes, tusks), [`shapes_bone.py`](shapes_bone.py)
   (skulls, spines, ribcages), [`shapes_crude.py`](shapes_crude.py) (plates, lashed poles,
   palisades, rag banners), built and used by the citadel and throne.
3. **Night look:** sickly torchlight, a `NightLook` of the Goblins' own coloured from the
   palette's `fire` ramp. Not built yet: the citadel and throne have no night lights.

## Units

14 recipes: the citadel and throne are designed, the other 12 are stubs. Scaffolder picks, checked by hand:

| Stub | EA model / target (tris) | Check |
|---|---|---|
| fortress | `WBFortress` / `WBFORTRESS` (2738) | ok; `EYES` (glowing eyes, WBEyes) stays EA's; drawn by WildFortress (building) and WildFortressCitadel |
| fortress_throne | `WBFGThrone` / `WBFGTHRONE` (854) | ok; the monument upgrade, although EA's Draw tag is Gondor's `ModuleTag_IvoryTowerDraw` |
| fortress_spines | `WBFRSpin` / `WBFRSPIN` (736) | ok; also drawn by WildFortressRazorSpines |
| arrow_den, burrows, giant_sentry, spider_holes | `WBFADen`, `WBFBurrow`, `WBFGSentry`, `WBSHole` | ok; single meshes, no house model (HOUSE_DRAW) |
| cave | `WBCave_SKN` / `WBCAVE` (505) | ok; `WBCAVE_STONE` (225, WBStone) and the level-ups V1/V1A are other meshes |
| fissure | `WBFissure` / `CYLINDER01` (230) | ok: the only body (a rock cone on WBStone); `PLANE01` is the fissure's floor |
| spider_pit | `WBSpidPit_SKN` / `ROCK` (330) | ok; `SPI PIT` (72) and the web cards (`WEBS`, cut-outs) stay EA's |
| treasure_trove | `WBTreaTrov_SKN` / `WBTREATROVT` (1585) | ok; `ROCK` (562, `WTreasureStone` with the Dwarves' `DBStoneA_NRM`) is second |
| mine_shaft | `WBPit_SKN` / `WBPITMETAL` (686) | ok; its buried rocks (z -14) are ignored when finding the ground; V1 (314) is the level-2 mesh |
| lumber_mill | `MBLumMill_SKN` / `LUMBERMILL` (1204) | ships as `WBLumMill_SKN`: Mordor's model, drawn by Isengard and Mordor too (ChildObjects of the civilian LumberMill); V2 (385) is the level-up |
| sentry_tower | `WBTower` / `DBTOWER` (1289) | ok; the mesh is named DBTOWER but is EA's Goblin tower on WBTower |

Not units: the drake (`WUFireDrk_SKN`), bat cloud and fire arrows (effects of fortress upgrades),
the citadel door leaves `WBFDoor` (24 triangles each, part of the citadel recipe).

Map castle pieces (not scaffolded, optional after the rollout): `WildCastleWall{Segment,Hub,Gate}`
draw `WBWallRamp2`, `WBWallRmprt`, `WBWallGate`: the Dwarven placeholders' geometry (82-166
triangles, same bounds) on the yellow "Wall" sheet `WBWall`, Goblin-only. The Dwarven
`oldwall_segment`, `oldwall_hub`, `oldwall_gate` recipes are the template.

## Ownership (`sagekit owners goblins`)

- `WBCave` (cave, fissure/spider pit/trove night meshes) is drawn by Isengard (`IBArmory`) and
  Mordor (`MBMumkPen`, the lumber mill): the cave pins `wbcavH.tga`; `sagekit sheets` skips it.
- `WBStone` (fissure body, cave rock) is drawn by the Elves' Ent and Mordor's trolls: pinned.
- `MBLumberMill`, `MBLumMill_*` and `MBHCLumberMill`: Isengard and Mordor draw them too; own model
  `WBLumMill_SKN`, own sheet `MBLumberMilH.tga`, own house copy (automatic).
- `DBStoneA_NRM` (treasure trove's rock) is the Dwarven bunker's normal map: leave that mesh EA's.
- `Evil_House_Color_Flag` (every WBHC* banner) is shared by all evil factions: the house step's
  own copies handle it.
- Everything else the stubs ship is Goblin-only. The old castle walls are Goblin-only too.

## Banners

Few. EA gives each Goblin house model one 330-triangle `HC_BANNER01` (z -22..53). Caps count player-colour cloth pieces per building, EA's included: citadel 3, cave 2,
throne 1, sentry tower 1, every other building 1, spines 0, expansions 0 or 1. Cloth is ragged
and hangs from poles and bone spars, never a neat heraldic field; it takes the player's colour.

## 1. Fortress and add-ons

Drawn by `WildFortressCitadel` with `WBHCFortress`. Add-ons have `parts = (<tag>,)`.

| Recipe | Upgrade | Constraints | Banners |
|---|---|---|---|
| fortress (installed) | - | HERO tier; x -65..71, y +-65, z 0..117; walls at +-43.4 (z 0..42), walk 55.7-60; EYES meshes stay; the door `WBFDoor` (+-leaves z 7.5..44) belongs to the citadel | 3 |
| fortress_throne (installed) | UPGRADE_FORTRESS_MONUMENT | z 0..173.5 (the tallest piece: watch `max_z_growth`); P1 (z 74.8) is where the fire drake perches: keep it clear; `WBFGThrone_A` has a user-flag construction state | 1 |
| fortress_spines ([designed](fortress_spines/README.md)) | FORTRESS_IMPROVEMENT_4 | a ring of spikes round the keep (r ~77, z 0..14); heads at z 12.9; miss the citadel's gate dressing (x > 44, \|y\| < 36) and spire columns | 0: skulls on six uprights, tusks, chevaux de frise, three impaled; 736 -> 4,714, +17 % (`max_z_growth = 0.35`) |

The citadel's crowns and gate are in `fortress/crown.py` and `fortress/gate.py`; the throne's
dragon and nest in `fortress_throne/dragon.py` and `nest.py`. Spines: designed (shape preview).

## 2. Expansions (fortress pads)

Each sits on a pad, has no house model (`HOUSE_DRAW`, the style's `house_template` WBHCTower) and
no night meshes. All on `WBFortress`.

| Recipe | Constraints | Banners | State |
|---|---|---|---|
| arrow_den | x -45.5..24.8, z 0..89; its eye card `EYES` stays | 1 | [designed](arrow_den/README.md): ribs gripping the stalk, fangs under the bowl, roof horns and skull spike, gibbet on the brace; 499 -> 4,804, +18.7 % |
| burrows | x -51.8..0, z 0..43.5; low mounds: keep the openings | 0 | [designed](burrows/README.md): a beast's ribcage over the roof, its neck and horned skull over the mouth, tusk jaws; 588 -> 4,543, +18.4 % |
| giant_sentry | P1 (z 30) is the mountain giant's stand: keep it clear | 1 | [designed](giant_sentry/README.md): a crown of horns and a skull totem on the rim, ribs gripping the column, skulls on the rim spikes, boulder heaps, thigh bone; 368 -> 6,079, +14.5 % |
| spider_holes | x -48.5..16.2, z 0..47; the holes are spawn openings | 0 | [designed](spider_holes/README.md): a dead spider's eight legs over the carapace, cocoons; 348 -> 4,139, +5.4 % |

**Shared (written):** [`arrow_den/pad.py`](arrow_den/pad.py): rocks and the rock skirt along a
footprint, great ribs (Bezier or path), ribs clasping a column, rib arches over a roof, riveted
bands round any convex outline. Groups 1, 2 and 4 are designed in shape previews (9/9 each); the
review sheet is `build/assets/goblins/_review/fortress.jpg`; nothing is built or installed.

## 3. Production and economy

`_SKN` models whose units animate (goblins, spiders, cocoons): keep their clearances. Each has
EA's house model; cave, fissure, spider pit, trove and lumber mill carry an `N_WINDOW`/`N_FIRE`
pair copied from the cave (80 + 16 triangles at z 0..47): check whether it sits on each body
before marking night lights. Level-ups: cave and trove V1 (243, WBPit2) and V1A (160, WBStone),
mine shaft V1 (314), V2 (skinned) and V2A (243), lumber mill V2 (385).

| Recipe | Sheet | Constraints | Banners | State |
|---|---|---|---|---|
| cave | own `wbcavH` | ground at -5.7 (the mouth dips); goblin sword-guard animates; WBHCCave | 2 | [designed](cave/README.md): gate of lashed timber and fangs, tusks, troll skull, summit totem; 505 -> 6,299, +13.6 % |
| fissure | own `WBStonH` | a rock cone round the fissure floor (`PLANE01`, WBFissure): keep the floor open | 1 | [designed](fissure/README.md), pass 2: jaw gate (two towers, bridge, bone teeth) over the mouth, tall totem, palisades, idol skull, crest horns; 230 -> 7,711, +14.8 % |
| spider_pit | `WBBStone` | spider webs are DXT5 cut-outs on EA's sheets; cocoons are skinned and level-3 only | 1 | [designed](spider_pit/README.md): five legs of a dead spider clutching the spire, larder gibbet; 330 -> 3,611, +8.5 % |
| treasure_trove | `WBTreaTrov` | gold and jewels (`COIN01`, `JEWELS` on WBTreaTrovGold) stay EA's; two goblins animate; z -9.4..51.8 | 1 | [designed](treasure_trove/README.md), pass 2: the dragon shackled - great horns with spiked collars, spiked head band, nails, heavy chains, strongboxes; 1,585 -> 4,948, +11.0 % |
| mine_shaft | `wbpit2` | a low rim (z 0..18) round a pit: the hole's centre and the goblin's climb out (to (5.5, -11)) stay clear, the archer's box too; N_GLOW torches | 1 | [designed](mine_shaft/README.md), pass 2 (redesign): a working mine - winch tower, boom, wheel and bucket, shoring, spoil heaps, cart; 686 -> 4,833, +100 % (`max_z_growth = 1.05`, Max's OK) |
| lumber_mill | own `MBLumberMilH` | own model `WBLumMill_SKN`; orcs animate; fire card FIRE01 stays EA's | 1 | [designed](lumber_mill/README.md), pass 2: palisades along the back and behind the shed, frame saw, log piles, crane, shed trophies; 1,204 -> 5,983, +4.8 % |

Designed means shape previews pass (9/9 each) and the review sheet is
`build/assets/goblins/_review/production.jpg` (the first pass: `production_v1.jpg`); nothing is built (bake, paint, lifecycle, night)
or installed. The level-up meshes (V1, V1A, V2, V2A) stay EA's and nothing new stands where they
appear; none is redesigned, so no `base` chain yet.

**Shared (written):** [`cave/motifs.py`](cave/motifs.py): posts, props, lashed trestles, gate
frames, stakes on uneven ground, ladders, bone spars, pole banners, torches and torch brackets,
hide frames, strongboxes, ring-stakes, a windlass, an ore cart, a spoked wheel, a bucket, plank
shoring, spoil heaps and a watchtower. The trove sets
`world_space = True` (its body hangs on a bone turned 243 degrees about z).

**Night meshes (checked):** the `N_WINDOW`/`N_FIRE` pair is two night-only torch posts (40
triangles each, z 0..34.6, on WBCave) with flame cards on top (z 28.8..47.2), standing beside each
building, not on it: cave and fissure at (62..72, 21) and (62..69, -34) (in front of the mouth,
past the body's x 56.8); spider pit (25, 40), (1, -49); trove (36, 31), (-38, -19); lumber mill
(-1, 47), (-8, -51). The mine shaft's are N_GLOW flame cards over EA's two poles and a lens-flare
plane (N_GLOW, z 19.4). See framework item 7.

## 4. Towers

| Recipe | Constraints | Banners | State |
|---|---|---|---|
| sentry_tower | z -0.3..123.8; N_WINDOW (EXLightStreaks) at z 69..88: the lookout; WBHCTower; the mesh is turned 180 degrees | 1 | [designed](sentry_tower/README.md): hood band, great horns, skull spike to z 144.5, gibbet, painted hide; 1,289 -> 5,019, +16.7 %; WBTower needs `materials` rects (item 6) |

## Framework items

Done:

1. **Ownership through ChildObjects.** `ownership.scan` credits a ChildObject or ObjectReskin
   with the Draw modules it inherits, so the lumber mill stub no longer changes Isengard's and
   Mordor's mills.
2. **Buried meshes.** `scaffold.bodies` ignores meshes wholly below the model's origin when it
   finds the ground (the mine shaft, Mordor's slaughter house).
3. **The Goblin kit**, tested in the citadel and throne builds.
4. **UV layout of EA's citadel body.** EA's own WBFORTRESS layout overlapped (0.73 %); the
   citadel sets `facet_islands = 8` and passes 90/90.
5. **Atlas regions of the production sheets** (2026-09-28, previews only, not yet in a build).
   `atlas.py` `SHEETS`: material rects in each production sheet's own pixels (wbcave, WBStone,
   WBBStone, wbpit2, WBTreaTrov, MBLumberMill at 256), a `rock` material that wins over the colour
   rules inside its rects, and optional per-sheet tones (wbpit2's iron: EA's bright rust made a
   darker silver). Max's picks: the mine collar silver iron, the mill's wood-chips timber.
6. **GoblinSheetRecolour** (`paint.py`): on a production building EA's faces (tag 0) take their
   sheet's rects and tones, new faces WBFortress's; on a flat sheet the sheet's own atlas
   (`GoblinStyle.sheet_atlas`, for `sagekit sheets goblins`). `GoblinStyle.recolour(building)`
   picks it only for a building whose sheet has a table; the citadel and throne keep
   `GoblinRecolour` itself. Checked: the flat WBFortress recolour is bit-identical, new faces on
   the citadel's bake are bit-identical, the citadel and throne previews pass. The rects were
   read by eye; confirm them on the first bakes of each building.

Open:

7. **Night look** (kept EA's for now: `GoblinStyle.night` stays None, the safe choice; with no
   NightLook every Goblin model keeps EA's night meshes untouched; the new pieces stand clear of
   EA's night-only torch posts, the lumber mill's hide frame moved for it). Later: `GoblinStyle.night =
   NightLook("WBNight.tga", ...)`, its ramp from the
   palette's `fire` ramp, e.g. `[(0, (0, 0, 0)), (0.2, (0.2, 0.01, 0.02)), (0.45, (0.62, 0.09,
   0.06)), (0.75, (0.95, 0.35, 0.18)), (1, (1.0, 0.75, 0.55))]` (sickly red torchlight, not the
   Dwarves' orange). Setting it turns every Goblin night mesh into our lights or a dark stand-in,
   so it lands together with each recipe's `night_lights`. The production buildings' night meshes
   are EA's two night-only torch posts beside each building (see Production above), not windows:
   either keep them (a framework option to leave a building's night meshes EA's under a NightLook,
   or a Light draped on a night-only post of our own, `docs/FACTIONS-PLAN.md` tool 3), or light
   our own fires. Candidate lights: the cave's mouth (a `door` in the gate frame's plane, x 48,
   |y| < 11, z 2..21) and its two torches; the fissure's crest fire bowl and the crack (on
   `PLANE01`, a `night_surfaces` mesh); the spider pit's hole (on `SPI PIT`); the trove's torch
   and the dragon's mouth (FX_MOUTH); the mine shaft's two new baskets under EA's N_GLOW01/02
   (at (-37.9, 5.9) and (53.6, -18.5), z 18.8..21) and the pit's mouth; the lumber mill's fire
   pit (20, 33). The citadel and throne have no night meshes.
8. **Upgrade names:** the scaffolder names an upgrade from its Draw tag; EA's tags can be
   borrowed from another faction (the throne's `IvoryTowerDraw`). Check upgrade stubs by hand
   until the scaffolder reads the model instead.

## Order

1. Groups 1-4 in parallel in draft mode: fortress spines + expansions; production A (cave,
   fissure, spider pit); production B (trove, mine shaft, lumber mill); towers.
2. Integration pass: `sagekit sheets` and `sagekit house goblins`, the poster, the lifecycle
   review; review before install.
