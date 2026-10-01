# Isengard tavern (`IsengardTavern`)

EA's Dunland hall `ibwildbld_skn` ("Clan Steading" on its button), mesh `BUILDING`, own texture
`ibwildbuildinH.tga`; house-colour model Mordor's `MBHCOrcpit` (own copy, automatic). Palette A;
new pieces from the Isengard kit and [`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py). EA's hall is
kept whole: the long steep roof, the crossed logs at the gables, the log buttresses, the door.

Player-built: slot 6 of `IsengardPorterCommandSet` (`Command_ConstructIsengardTavern`), so a
building like the others, not a captured map building.

## Pass 4: destacked (2026-09-30)

Max after Mordor: "our furnace towers on everything look a lil stupid" and "super low quality
that tower". The rollout's needle stacks and stamped blade pairs read as bolted-on clones. Each
building now gets its own work instead (new pieces in [`shapes_trades.py`](../shapes_trades.py)),
smaller and fewer, its fire in its own forges, grates, braziers and pits.

- **Out**: the great chimney, the pair and the chains to the crest.
- **In**: three crude orc hides pegged with iron on the -Y slope the camera sees (`roof_hide`,
  placed on EA's roof as probed: z 56 at y -4 to 38.6 at y -16), a cook-fire with a spit and a
  haunch at the -X end (`spit_fire`). The crest, the crossed blades and the Hand shield stay.
- **Fire** 1 -> 1: the chimney -> the cook-fire (hearth).

1,848 -> 2,875 triangles (pass 3: 4,656), height +17.0 % (the crest; pass 3: +19.4 %), footprint
unchanged, 9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg` (installed
pass 3 against pass 4 at the RTS view).

## Pass 3: up to the citadel

Pass 2 read modest beside the citadel. Pass 3 applies its recipe: the pair, needle stacks,
the Hand in pointed-arch slots, fire. Sheet: `_review/production_v3.jpg`.

- **The pair** (the citadel's): two matching blades out of the roof slopes either side of the
  ridge's middle in the RTS view, (-16.6, -19.3) and (10.6, 15.3), from z 28 (in the roof) to
  77.5, two fins a face, the White Hand in a pointed-arch slot on each one's outer face, chains
  from each to the crest's tall middle fin. Nothing new stands on the ground (the level-ups
  take the hall's sides and door).
- **Great chimney**: pass 2's two stacks on the -Y slope stood where the left blade stands; one
  great spire stack behind the crest on the view's axis, (-12.5, 5.4), to z 68 plus its crown.
- **Fire** (1: chimney (EA's torches FX01, FX02 stay)).

1,848 -> 4,656 triangles, height 72.0 -> 86.0 (+19.4 %), footprint unchanged, 9/9 preview checks.

## Pass 2: the hall of the White Hand

- **Crest** (the new silhouette): a dorsal crest of seven layered knife fins along the ridge,
  rising from 6 to 17.5 above it (to z 76), silver front edges, ember slits in the tall ones.
- **Horns**: a pair of iron blades crossing over each gable's apex.
- **Stacks**: two blade-spire stacks through the roof's -Y slope, a crown of blades round each
  glowing mouth (to z 77).
- **The Hand**: on a great shield hung on chains in the +X gable, over the door (from z 34).
- **Fire** (2 points): the stacks. EA's chimney smoke (`FXSmokeBone`: no such bone in the model,
  so it rises from the object's origin) and its torches (`FX01`, `FX02`) stay.

1,848 -> 3,020 triangles, height 72.0 -> 84.3 (+17.0 %), footprint unchanged, 9/9 preview
checks. Pass 1 is `_review/production_v1.jpg`.

## Kept clear

- The door and the units' way out: made at (14.9, -0.1), rallying to (100, -0.1).
- The level-ups: `V1` hide walls along both sides, `V2` banners, `V3` stakes flanking the door;
  the torch posts (`TORCHES`).

## Sheets

Its sheets (`ibwildbuilding.tga`, `_d`, `_snow`, `_nrm`) are TGA files, not DDS. Since
2026-09-29 the extract step reads a sheet's DDS, else its TGA, and keeps a DDS copy in `src/`;
the snow swap (`ibwildbuilding_snow.tga` -> `ibwildbuildinH_snow.tga`) is a variant like any
other. `sagekit sheets` still lists DDS sheets only, so the states that stay EA's (rubble, the
building site) keep EA's colours for now.

## Status

- [x] pipeline reads its TGA sheets
- [x] pass 3 built in colour and installed (2026-09-29)
- [x] pass 4 designed (shape preview, 2026-09-30)
- [ ] pass 4 reviewed by Max, built in colour, installed
