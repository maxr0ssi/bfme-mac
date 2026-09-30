# Mordor: building rollout

**Status: 25 stubs; palette F2 "Fire, shadow and steel" (Max's pick, 2026-09-30); the citadel in
pass 7 (claws of spikes inside the crowns round green witch-fire), built in colour and waiting for
Max's review ([fortress/README.md](fortress/README.md)). Pass 6 is the one installed.**
Every recipe passes `sagekit validate`.
Templates: [`assets/isengard/ROLLOUT.md`](../isengard/ROLLOUT.md),
[`assets/goblins/ROLLOUT.md`](../goblins/ROLLOUT.md); the loop is in
[docs/FACTIONS-PLAN.md](../../docs/FACTIONS-PLAN.md).

## Where to look

Build output is under `build/assets/mordor/` (not in git).

- The palette on EA's citadel: `_palettes/palette_options.jpg` (EA and F2, `sagekit palettes
  mordor --only F2`); round one (A to D) in `_palettes/palette_options_v1.jpg`, round two
  (E, F, G, A) in `_palettes/palette_options_v2.jpg`, round three (F, F2, F3, F4) in
  `_palettes/palette_options_v3.jpg`.
  Rows: `board` (the whole citadel from above) and `tower` (the corner towers' crowns and pyres).
- The citadel's measurements: `fortress/work/measure.json`; EA's facts in
  [fortress/building.py](fortress/building.py).

## Palette: F2 Fire, shadow and steel (Max's pick, 2026-09-30)

Not Isengard (machined black stone, silver edges, ember) and not the Goblins (crimson, tarnished
silver, bone). [`style.py`](style.py) `PALETTES`; paint in [`paint.py`](paint.py), rects in
[`atlas.py`](atlas.py).

| Option | Reads as |
|---|---|
| A Ash and lava | grey basalt, ash-grey walks, dark rusted iron with hot orange edges, orange glow |
| B The Red Eye | black stone and iron, tarnished bronze and brass edges, deep red-orange glow |
| C Scorched bone | pale ash-white towers and walls, black iron spikes with red edges, red glow |
| D Gorgoroth rust | charcoal stone, rust-red spikes, ochre ground, sulphur-yellow glow |
| E Morgul | black stone, ash-grey walks, dark iron; green witch-light in windows, trims and pyres |
| F Fire and shadow | black basalt and ash, orange fire and edges, green witch-light in the windows |
| G Barad-dur | black iron-stone, ash ground, dull iron edges, fire in the windows and pyres |
| F2 Fire, shadow and steel | F with hard cold steel on the blades' bright faces, where EA had its pale steel |
| F3 Fire, steel and ghost-light | F2 with pale green-white windows (Minas Morgul), less lime |
| F4 Hot steel and ghost-light | F3 with steel only on each blade's bright core, orange heat on its flanks |

Round three: Max picked F ("nice contrast") and asked for a touch of the hard silver EA's sheet
has. EA's pale steel is on the blades: the spike rows, the blade finials and hooked blade, the
crest and the crown blades (atlas.py `blade` rects). F2 to F4 paint only the brightest metal
there with a `steel` ramp; the wall-foot spikes and every other edge keep F's orange.
Max picked F2 ("F2 is super cool!"); its window green is nudged a third of the way from F's lime
toward F3's ghost-green (`MORGUL_WINDOW`). The other options stay in `PALETTES` for the record.
Pass 7 of the citadel (Max: "drastically reduce the green"): F2's windows are a dim ember now
(`EMBER_WINDOW`); the green stays on one lancet pair per tower (tag `witch`) and in the crowns'
green witch-fire (the game's particles).

Round two (Max asked about the films' green). The green is Minas Morgul's: EA uses it only in the
Morgul sorcery upgrade (MBFSorcery's MorgulSorceryFX, a pale jade witch-light) and the
Witch-king's poison and blade particles (yellow-green). MBFortress has none, and no Mordor
structure INI sets a green light. Ours is a sickly yellow-green, not the Elves' teal. From E on
the windows and slots glow (the atlas's `slit` rects); on EA's citadel only the tower crowns'
windows show, so the green reads there, on the trims and (E) on the pyres.

Recolour only: EA's body shows no lava cracks (the citadel's body does not use the sheet's
lava vein), so on it the glow is the roof pyres only. Lava in the joints comes
with the design (ember and flame faces, fire points).

EA's citadel is painted from four parts of MBFortress: the spiked and fluted wall plate, the
towers' shafts and crowns, the inner walls, and the cratered rock of the walks. Those are stone
(the plate under the spike rows too), rock, and iron with trim on its lit edges (atlas.py).

## Production sheets (2026-09-30)

Every production sheet the recipes draw has its own paint areas ([`atlas_sheets.py`](atlas_sheets.py)
SHEETS, `MordorSheetRecolour` in [`paint.py`](paint.py)), after Isengard's and the Goblins'. Board:
`_review/sheets_v2.jpg` (EA's buildings recoloured, no design; v1 was too dark, Max: "some of these
feel like a step back"). F2's black is for stone and iron only; wood, bone, hide and cloth keep
EA's values; the orc pit's pool is a sickly green sludge (Max kept EA's green); the Harad pair stays sand, gold, war-paint
red and ivory. MBFortress's paint is bit-identical (the citadel's colour layers hashed on its bake
before and after). New geometry: tags `bone` (ivory), `warpaint` and `brass` (atlas.py).

## Units

25 stubs from `sagekit new mordor`. What to know:

- **Haradrim palace and mumakil pen** (`MordorHaradrimPalace`, `MordorMumakilPen`, in the build
  menu `MordorPorterCommandSet` slots 6 and 9) are Mordor's, but their INIs live in BFME1's
  `structures\evilmen\` folder, so the scaffolder missed them. `sagekit/scaffold.py` STRUCTURES
  now lists both files and `MordorStyle.ini_dir` covers them. Both are static bodies on their
  own sheets (MBHrdPlc, MBMumkPen), drawn by no other faction. `mumakil_pen_02` is the pen's
  door (MBMumkpenDSCL, animated): likely stays EA's, like Isengard's warg pit door.
- The rest of the build menu is covered: slaughter house, lumber mill, orc pit, troll cage,
  siege works, tavern, battle tower, fortress. `MordorPorterCommandSet_ForMirkwood` builds
  Isengard's battle tower instead of Mordor's.
- **Not design units**: the four `*_morgul_sorcery` stubs (target MBFLAVAMEFF, 124 triangles on
  the MinasMorgulFX sheets) are the sorcery upgrade's effect meshes; `troll_cage_02` (the cage
  door, on a tilted bone) and `troll_cage_module_tag_03` (the chains) are animated parts. They
  stay EA's; dropping the stubs is Max's call.
- No player walls: `wall_catapult` and `gate_watchers` are fortress expansions.

## Harad group: palace, pen, battle tower, barricade (pass 2, 2026-09-30)

These are shape previews only: nothing is built or installed. Review sheets: `_review/harad_v2.jpg`
(pass 2) and `_review/harad_v1.jpg` (pass 1). Each sheet opens with the citadel's rts view, then
shows EA and ours at rts and close at level 1, with fire points marked. `harad_v2.jpg` adds rts rows
with the palace's and the pen's level 2 and 3 pieces shown. The group's pieces are in
[`shapes_harad.py`](shapes_harad.py).

| Building | Key new mass | Triangles | Height | Fire |
|---|---|---|---|---|
| [haradrim_palace](haradrim_palace/README.md) | a crown of eight ivory tusks round a great fire bowl on a stepped plinth at the peak; grounded tusk claws either side of the -Y door; brass suns on war-paint plates; two sun-and-serpent banners (player's colour) | 1,106 -> 5,797 | +42.1 % | 3 furnace (peak with plume, 2 claws with smoke), EA's bonfire (hearth) |
| [mumakil_pen](mumakil_pen/README.md) | a great arch of crossed ivory tusks over the open end, a fire bowl at its crown, the sun under it, chains; tusk claws on the berms; howdahs with canopies on the decks; two banners; lava | 1,472 -> 7,757 | +23.2 % | 5 furnace (crown with plume), 4 smoke, 2 embers |
| [battle_tower](battle_tower/README.md) | an eight-spike claw rising from the roof's dish round a jagged fire bowl, the Eye, lava from the foot | 680 -> 2,565 | +10.8 % | furnace + smoke, 4 embers |
| [barricade](barricade/README.md) | lava along every front and a moat at the gate, barbed portcullis teeth, stakes, steel lip spikes, a spike claw in the keep, the Eye | 923 -> 5,117 | +8.6 % | 2 braziers, 5 embers, 2 smoke |

- Max approved the Harad twist ("cool like it go for it"): F2's black, ember and steel, with ivory
  tusks (`bone`), brass (`brass`), war-paint red (`warpaint`) and banners in the player's colour.
- The palace's and the pen's level 2 and 3 pieces (`V1`, `V2A`/`V2`, banners) are in `bake_hidden`.
- The door `mumakil_pen_02` stays EA's. Its swing, measured over every animation frame, is kept
  clear.

## Add-ons group: the citadel's upgrades and expansions (pass 2, 2026-09-30)

Shape previews only (not built, not installed). Review sheet: `_review/addons_v2.jpg` (pass 1: `addons_v1.jpg`; the citadel's
rts at the top, every add-on built at once on our citadel, then each one EA's and ours in place and
close, fire points marked). The upgrades sit on the citadel; the expansions were checked on all seven
of its pads (EA's base file `bases\fortress_mordor`). No face of any add-on crosses the citadel's new
faces. Shared pieces: [`shapes_addons.py`](shapes_addons.py) (the crowns' claw at any size; `fissure`,
forked cracks glowing from within in a dark lip, and `runnel`, since pass 1's cracks read as
painted flames; the Watchers' eyes, arch teeth).

| Building | Key new mass | Triangles | Height | Fire |
|---|---|---|---|---|
| [fortress_fire_arrows](fortress_fire_arrows/README.md) | six hooked spikes rising from inside EA's pod between its twelve, closing over embers; barbs on the legs | 376 -> 1,312 | +17.2 % | brazier |
| [fortress_magma_cauldrons](fortress_magma_cauldrons/README.md) | a larger furnace mouth at the cauldron tower's foot with forked cracks up the tower; lava brimming in all eight spouts, poured down seven walls in runnels | 780 -> 2,339 | 0 % | furnace, 3 embers |
| [fortress_gorgoroth_spire](fortress_gorgoroth_spire/README.md) | a claw of five spikes round a fire on each corner of the keep's roof; forked cracks up the shaft and the buttresses | 1,060 -> 5,916 | 0 % | 4 brazier |
| [fortress_lava_moat](fortress_lava_moat/README.md) | slag rafts and glowing bubbles on EA's lava; basalt teeth and impaling stakes on the outer bank between the pads | 630 -> 4,869 | +6.4 % | 2 smoke, 3 embers |
| [gate_watchers](gate_watchers/README.md) | the Watchers' six eyes in Morgul witch-light (the one green accent), barbed teeth in the arch, two clawed fire baskets | 1,271 -> 2,111 | 0 % | 2 brazier |
| [wall_catapult](wall_catapult/README.md) | the family's claw on the rim: 13 spikes leaning in, open over the catapult and clear of its arm's swing (EA's animation, by 3.4); fire baskets in its gaps; forked cracks up the drum | 962 -> 4,064 | 0 % | 2 brazier, 2 embers |
| [fortress_barricade](fortress_barricade/README.md) | the citadel's crown on its tower (eight spikes round a fire), the Eye in its windows, forked cracks, arch teeth | 1,199 -> 5,403 | +5.9 % | brazier |

The `*_morgul_sorcery` stubs stay EA's (effect meshes). EA's moat bank covers the citadel's own
lava at the -Y and +X wall feet once the moat is built (EA's moat, not ours).

## Production group: orc pit, slaughter house, lumber mill, siege works, troll cage, tavern (pass 2, 2026-09-30)

Shape previews only (not built, not installed). Review sheet: `_review/production_v2.jpg` (the
citadel's rts at the top, then EA and ours at rts and close, with the fire points marked); pass 1
is `_review/production_v1.jpg`. Pieces: [`shapes_production.py`](shapes_production.py) and
[`shapes_production_big.py`](shapes_production_big.py). Pass 2 after the review of pass 1: no bowl
perched on a roof (it read as an egg stuck on); fire comes out of grounded stacks, pits and rings;
one bold mass per building at rts. No green: orange fire, lava and steel only.

| Building | Key new mass | Triangles | Height | Fire |
|---|---|---|---|---|
| [orc_pit](orc_pit/README.md) | fourteen spikes rising from inside the crater's rim over the pit, a 48-degree gap where the orcs climb out; coal shelves round the pit's foot; lava seams; war drum, whip post, stakes | 257 -> 4,146 | +19.4 % | 4 forge, plume, 2 embers, smoke |
| [slaughter_house](slaughter_house/README.md) | a grounded basalt smoke stack with a clawed mouth; a great smoke-rack gantry of carcasses; butcher blocks, bone heaps, a lava runnel; a gibbet off the gable | 832 -> 5,221 | +11.5 % | chimney, plume, embers, 2 brazier |
| [lumber_mill](lumber_mill/README.md) | a big claw rising from inside the fire pit's ring round the charcoal fire (clear of EA's flame card); a tall saw gantry across the log; a log-pile ramp | 1,204 -> 4,964 | 0 % | furnace, plume, brazier, embers |
| [siege_works](siege_works/README.md) | a grounded basalt forge stack over the walls, its mouth clawed, furnace mouths feeding a lava runnel; a half-built siege tower on its scaffold; a crane over a catapult | 667 -> 6,485 | +9.8 % | furnace, 3 forge, plume, embers, smoke, 2 brazier |
| [troll_cage](troll_cage/README.md) | eleven heavy hooked iron claw bars over the pen, chained to a spiked boss, a fire pit under them; steel spikes over the door; lava at the pen's foot | 1,064 -> 3,971 | +7.1 % | forge, plume, embers, smoke, 2 brazier |
| [tavern](tavern/README.md) | a great grounded basalt chimney stack against the front wall, its mouth clawed; steel spikes along the ridge; a gibbet over the door, fire baskets, lava | 528 -> 2,920 | +16.2 % | chimney, plume, embers, smoke, 2 brazier |

The troll cage's door (`troll_cage_02`) and chains (`troll_cage_module_tag_03`) stay EA's and
clear. The lumber mill ships as Mordor's own copy (`MBLumMill2_SKN`). EA's orc pit and tavern
bodies carry loose vertices (8 and 2): `design()` drops them, as the Men forge does.

## Ownership (`sagekit owners mordor`)

- `MBLumMill_*`, `MBLumberMill*`, `MBHCLumberMill`: the Goblins and Isengard draw them too.
  Mordor's own copies: model `MBLumMill2_SKN`, sheet `MBLumberMilB.tga`, house `MBHCLumMill2`
  (Isengard's: `IBLumMill_SKN`, `MBLumberMilX.tga`, `IBHCLumberMill`; the Goblins':
  `WBLumMill_SKN`, `MBLumberMilH.tga`, `WBHCLumberMill`). No clash.
- `MBHCOrcpit`: Isengard's tavern draws it (its copy `IBHCOrcpit`). Mordor's copy is
  `MBHCOrcpit2`: the house prefix of Mordor is EA's own, so `Building.own_house_copy` adds a 2
  where the copy's name would be EA's.
- `mbtavern`: Isengard draws it too; pinned as `MBTaverH.tga`.
- `MBFurnace*`, `MBHCFurnace`, `mbsizetemplate`: Isengard's only, despite the name; `sagekit
  sheets mordor` skips them.

## Open

1. `house_template = 'MBHCSentry'` for the expansions: unchecked.
2. The citadel: Max's review of pass 7 (`_review/citadel_v7.jpg`), then install and an in-game look
   at the green witch-fire.
