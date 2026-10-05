# The palantir HUD: EA's frame in our metal, sharp on Retina

The bottom-left palantir (the minimap ring, the portrait ring, the resource bar and the round
buttons) is an APT movie. Its art is a handful of 32-bit TGAs; `sagekit/hud/` repaints them in our
metal and ships each at EA's size and at twice EA's size, with the movies' geometry adjusted so the
game draws the 2x textures at the same place and size. The layout, the glass and the buttons'
emblems stay EA's.

```sh
python3 -m sagekit hud                        # extract, upscale, paint, write 1x + 2x, double the geometry, check, sheets
python3 -m sagekit hud --sheet                # the review sheets only
python3 -m sagekit hud --stage                # build/assets/_hud/_install/2x/!!!!!!!!!!!!!!sagekit-hud.big
python3 -m sagekit hud --install              # into RotWK/ (2x)
python3 -m sagekit hud --install --1x         # EA's sizes, no geometry: the fallback if 2x draws wrong
python3 -m sagekit hud --revert               # takes the archive out; the game draws EA's palantir
```

Review sheets: `build/assets/_review_finish/hud/hud_frames.jpg` (each frame, EA's page beside ours,
and a 4x detail), `hud_atlases.jpg` (the glass/button sheet and the portrait-ring sheet),
`hud_mockup.jpg` (the HUD at 3024x1964 and at 1512x982 over an in-game screenshot, EA's and ours).
The mock-ups need `build/assets/_hud/backdrop.png`, the bottom-left 900x620 of a 3024x1964 match
(kept out of git: it is EA's art); without it the sheets skip them.

## What is covered

`assets/hud/frames.py` lists the textures, `assets/hud/look.py` the two metals.

| Texture | What | Treatment |
|---|---|---|
| `apt_palantirexport_17`, `_20` | Good frame, with and without the portrait ring | rings redrawn, the rest recoloured: burnished bronze and gold |
| `apt_palantirexport_11`, `_14` | Evil frame, the same two | rings redrawn, the rest recoloured: blackened iron and steel |
| `apt_palantir_1` | minimap glass, glows, the round buttons and their sockets (both sides) | upscaled only (recoloured, the sockets' rims came out duller than EA's) |
| `apt_libingameimagesmain_1` | the portrait's chain of button rings, brackets, medallion bezels (both sides) | upscaled; the metal of the listed parts recoloured bronze, emblems and glows left alone |

EA's RotWK HUD has only these two skins, Good and Evil. One frame per faction is an APT edit on top of
this pack: see "One palantir per faction" below. (An earlier note here said it would need new APT
movies at a high crash risk; the edit below needs none.)

## How a frame is painted (`sagekit/paint/hud.py`, `hudrings.py`)

1. EA's texture is upscaled 4x: Real-ESRGAN on the colour (`downloads/realesrgan`, as the building
   sheets), Lanczos on the alpha.
2. Its metal is recoloured from its luminance by the side's `ornament` ramp, so the scroll joint, the
   resource bar, the knots and the Evil spikes stay EA's drawing in our metal.
3. Each ring is measured on EA's alpha (`hudrings.measure`): per degree, where the opaque metal
   starts and ends; the centre is refined until the inner edge has no first harmonic. EA's rings
   are hand-painted (an ellipse fit misses by 1-2 px), so the redraw follows the measured edges.
   A degree is redrawn whole when the band there is its usual width, beads only when something
   grows out of the broad band (Evil's thorns), and left to EA where something sits on the ring.
4. EA's cross-section is the same on every ring of all four frames: lip, bead, groove, second bead,
   groove, broad band. Each element is drawn again as a height field and lit as metal from the top
   left. Good: a polished gold bead, a gold rope, the broad band aged bronze engraved with a
   lozenge-and-pellet border. Evil: a chamfered steel bar, a notched blade edge, the broad band
   riveted iron plates with barbed chevrons and dark seams.
5. Evil only: a faint forge-ember (13%, Max's pick) wherever the metal is darker than its
   surroundings: grooves, plate seams, between the rivets, the cuts of EA's spikes (`ember`).
6. Box-filtered to 2x and 1x and sharpened a little. The 1x carries EA's alpha byte for byte, the
   2x EA's alpha resized (Lanczos).

## Retina 2x: why it works, and the one edit it needs

The icons (docs/ICONS.md) are MappedImages: an INI rect over a declared page size, so a page twice
the size could in principle ship without any other change. APT textures have no declared size;
what the game does, read from RotWK's `game.dat` (2.01):

- **The .dat.** `0x4AAB96` reads `<movie>.dat`: a line `img->tex` puts image `img` on texture
  `apt_<movie>_<tex>.tga`; any other line is parsed as `%d` only (`img=x y w h` names texture
  `apt_<movie>_<img>.tga`; the rect is never read).
- **The geometry.** `0x4AAE88` reads each `<movie>_geometry\<n>.ru`; a textured style
  `s tc:r:g:b:a:img:a:b:c:d:tx:ty` keeps the six floats (`0x4AB08D`). They map the shape's
  coordinates to the texture's pixels.
- **The normalisation.** `0x4A963C`, once per style, called by the shape's draw (`0x4A9CC3`):
  divides `a, c, tx` by the texture's width and `b, d, ty` by its height, both read from the loaded texture (`0x5322A8`, `0x5322D2`). It is the
  only reader of those sizes.
- **The path.** `0x477E73`: a texture whose name starts `apt_` is loaded from `Art/Textures/` as a
  TGA, not from `Art/CompiledTextures/`; created with one mip level.

So a texture twice the size alone would draw its top-left quarter. Doubled together with every
matrix that samples it, the game divides twice the pixels by twice the size: the same UVs, the
same shape on screen, twice the texels. `sagekit/hud/apt.py` doubles exactly the styles whose image
lives on one of our textures (117 files: 61 of Palantir, including the two the 2.02 patch
overrides, 52 of libInGameImagesMain, 4 of PalantirExport) and keeps every other byte. The checks
compare every matrix of every movie with EA's (doubled for ours, untouched for the rest) and keep
every sampled texel inside the texture. Not yet seen in game: if the 2x draws wrong, `--install
--1x` ships the repaint at EA's sizes with no geometry.

The archive sorts before `apt/*.big` and `__patch202.big` (the game mounts the apt/ folder with the
rest, first provider wins; the 2.02 patch overrides `palantir.apt` and two `.ru` files the same way).
The doubled `.ru` files start from the patch's versions.

## How big the HUD is on screen

Matched on a 3024x1964 screenshot, the double frame is drawn at 2.24x horizontally and 2.57x
vertically (the 2.02 patch squeezes the HUD 0.87 on a 16:10 screen). EA's 1x is magnified 2.2-2.6x
there, which is why it looks soft; our 2x is magnified 1.1-1.3x. At 1512x982 (Retina off) the 2x is
shrunk 1.8x with bilinear filtering and no mips; the mock-up shows it holds up.

## Cost and LAN

- Texture memory: 2x is about 22 MB against EA's 5.5 MB (+16.5 MB; the two atlases are 2048x1024).
- No INI, no upgrades, no asset.dat records: EA's names keep EA's records (a texture's record is its
  name and a timestamp, no size or format). The check suite and the install check that asset.dat
  files every texture the archive ships.
- The archive changes textures and APT geometry only. Everyone in a LAN game should still run the
  same files (MULTIPLAYER.md); it ships in the archive like every other pack.

## One palantir per faction

```sh
python3 -m sagekit hud --factions              # paint 7 frames (double + single), build the APT edit, check, trace, sheets
python3 -m sagekit hud --factions --sheet      # the review sheets only
python3 -m sagekit hud --factions --stage      # build/assets/_hud/_install/factions/!!!!!!!!!!!!!!sagekit-hud.big
python3 -m sagekit hud --factions --install    # replaces the installed HUD archive (the 2x pack plus the frames)
python3 -m sagekit hud --factions --revert     # back to the Good/Evil 2x pack (plain --revert: no archive)
```

**The mechanism** (game.dat 2.01). The game picks the palantir state from PlayerTemplate `Evil`
(`0x6d3e51`) and sends `SetPalantirFrameState("_good" | "_goodSingle" | "_evil" | "_evilSingle" |
"_hide")` (`0x8002dc`, names from the table at `0xc4e44c`); it also sends `SetPlayerFaction(<Side>)`
with PlayerTemplate `Side` (`0x80058e`), which EA's script uses only for the resource bar's faction
icon (it builds `"_" + faction` and drops it). `sagekit/hud/factionapt.py` edits the data:

- PalantirExport gets, per look and kind (double: minimap and portrait; single: minimap alone), an
  image, a shape and a sprite copied from EA's Good or Evil ones, exported as
  `PalantirFrame_<Look><Kind>`, with the images in the `.dat` and the shapes' `.ru` (matrix doubled).
- Palantir imports them; the frame clip (character 105) gets two frames per side, `_<Side>` and
  `_<Side>Single`, placing them with EA's transform for that side and kind; an action appended to the
  root's first frame wraps EA's two functions: each stores its argument, calls EA's original, then
  `sgApply()` turns the clip to `_<Side>[Single]` when the side is ours and the state a shown one.
- Append-only: nothing of EA's moves; 12 header words are repointed at grown copies of the
  character, import, export and frame arrays. The bytecode uses only opcodes EA's palantir uses.

| Side (PlayerTemplate) | Frame | | Side | Frame |
|---|---|---|---|---|
| Dwarves | `dwarves` | | Isengard | `isengard` |
| Elves | `elves` | | Mordor | `mordor` |
| Men, Arnor | `men` | | Wild | `goblins` |
| anything else (Observer, ...) | the Good/Evil pack's | | Angmar | `angmar` |

The looks are `assets/hud/factions/<faction>.py` (painted by `sagekit/paint/palantir/`, numpy on
Blender's Python), drawn over EA's frame: same layout and alpha, rings and resource bar redrawn in the
faction's cross-section, the scroll joint and spikes recoloured. The round buttons' rims (on
`apt_palantir_1` and `apt_libingameimagesmain_1`) are one sheet for every side in EA's movie (no
side labels on the button clips), so they stay the pack's for every faction.

**Cut from the citadel** (2026-10-04, Max: "re-look at all the citadels and redesign them that way").
Each frame is built from its faction's citadel: `assets/hud/factions/swatches.py` names crops of the
sheets the citadel is painted with (the faction atlas as our painter recoloured it; the Men's own
`GBFortressH`), `sagekit/hud/swatch.py` cuts them into `build/assets/_hud/factions/swatch/<faction>/`
(again when the sheet or the list changes), and `sagekit/paint/palantir/tex.py` lays them along the
rings: a swatch's colour becomes the albedo, its luminance a relief, so it is lit with the rest.
Friezes repeat a whole number of times round a ring, stone mirrors in pairs, so no seam at 0 degrees.

| Faction | The citadel | The frame |
|---|---|---|
| Dwarves | honey granite, gold coping, blue rune and triangle friezes, gold chevron shields | rune frieze round the glass, granite ashlar with chevron shields, gold beads; triangle frieze on the bar; a tower shield as medallion |
| Elves | ivory ashlar, teal lancet windows, slate scale roofs edged in mallorn gold | ivory ashlar pierced by teal lancets in gold, slate scales outside, gold beads; the arcade frieze on the bar; a lancet window medallion |
| Men | white ashlar, corbelled battlements, sable band of stars, White Tree banners | star band round the glass, white ashlar with White Tree cartouches, the corbel table outside; a blue White Tree banner medallion |
| Isengard | black fluted walls, silver-edged lancet panels, spikes | fluted black wall with silver lancet panels, silver spikes outside; the White Hand |
| Mordor | black fluted towers, fire-rimmed crown windows, green witch-fire, lava, blade crowns | lava channel, fluted iron with crown windows (two in three green), crown of blades; the Eye |
| Goblins | blood-red horn streaked white, black iron bands, bone tusks, skulls | bone tusks round the glass, red horn plates with iron straps and skulls; EA's spikes red and bone |
| Angmar | timber walk, blue-black stone, steel scale roofs, black horn tines with frost | timber walk round the glass, stone, scale coping, horn tines across it; the crown of tines medallion |

**Bold at the focal points** (Max, 2026-10-04: "be bolder"). The citadel materials stay the calm
base. Each look's signature is strong only near the joint between the rings, the bar's end caps and
the top (`assets/hud/factions/fx.py` `focus`): Mordor's lava seams, flames and embers with a fleck of
green; Angmar's ice crystals, frost and icicles; the Elves' polished gold and silver with filigree and
glints; the Dwarves' glowing blue runes and gems; the Men's glowing White Tree and star glints;
Isengard's furnace glow and a bold White Hand; the Goblins' ribs, skulls and blood. Painted bloom,
shine and glints are in the texture. **Past the silhouette** (`protrude`): blades, icicles, horns,
bones, a crest or a spire grow EA's alpha outward. They stay inside the frame's quad (its `.ru`
shape is the whole 512x256 page), and `frame.safe()` keeps them outside both glasses and 6 screen px
clear of the buttons and the resource numbers. The frame is not a click target, so the protrusions
are only visual.

Review: `build/assets/_review_finish/hud_citadel/all.jpg` (per faction: the citadel, the new frame
over the in-game crop at 3024x1964, the previous version, three 2x close-ups). The frames before are kept as
mock-ups in `build/assets/_hud/factions/sheet/prev/`. Same APT edit, same texture names and sizes:
`--factions --stage`, then `--factions --install` (revert: `--factions --revert`).

**Checks without the game** (`sagekit/hud/factioncheck.py`, `build/assets/_hud/factions/checks.txt`):
EA's bytes kept but the header words; every action of the movie decodes to its End (`aptfile.py`'s
reader decodes all 152 of EA's); our opcodes, flags, constants and branches are EA's kinds; every
import resolves to an export, every label to EA's transform, every image to a shipped texture at
twice EA's size with the 2x pack's matrix; then a small interpreter runs our bytecode with EA's
originals as stubs, replays the game's calls per side (side first, state first, re-shown) and follows
the label to the texture (`trace.txt`); and asset.dat files every texture the archive ships once the
installer's records are written. No external APT tool was available to cross-check the file.

**asset.dat.** The game draws a texture only when asset.dat files it; without a record it draws the
missing-texture magenta. The first install (2026-10-04) shipped the 14 frames under new names with no
record, and in game the whole frame quad drew magenta over the minimap and portrait, while the 2x
sockets and buttons (EA's names, EA's records, twice EA's size) drew. `--factions --install` now files
each new frame in RotWK's asset.dat as a copy of `apt_palantirexport_1.tga`'s record
(`sagekit/texrecords.py`), records the records in `installed.json`, and checks the live caches file
every texture afterwards; `--factions --revert` and `--revert` take exactly those records out, every
other record byte for byte, refusing records another install changed since.

**Risk.** A malformed APT file would fail when the palantir loads at match start. If a match does not
load, `--factions --revert` (or plain `--revert`) and it is gone. Cost: 14 more frame textures at
2x, 2 MB per double and 1 MB per single (21 MB). No INI, no upgrades; 14 asset.dat texture records.

Review sheets: `build/assets/_review_finish/hud_faction/hud_factions.jpg` (the fallback and each
faction over the in-game crop at 3024x1964, and details), `hud_factions_single.jpg`, `trace.txt`.

## Not covered yet

- The spell book frame (`apt_spellstore_1`), the side command bar, menus: same method, not done.
- The release pack (`sagekit/pack.py`) does not carry the HUD archive.
