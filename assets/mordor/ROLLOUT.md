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
