# HUD icons: EA's portraits and buttons of our buildings

The command bar shows each building twice: its portrait when selected and its button in the build
menu. Both are MappedImages: a rect on a 256 x 256 DXT3/DXT5 page (`buildingradialbuttons_NNN`).
A portrait is 192 x 192, a sepia painting of the whole building on its ground under a round
vignette; a button 64 x 64 (59 on the Dwarven wall page), a close-up against the sky in a circle.
`sagekit/icons/` repaints them from our buildings in EA's look and leaves every other pixel EA's.

```sh
python3 -m sagekit icons dwarves --map        # the faction's building images: in its table, kept, not covered
python3 -m sagekit icons dwarves --render     # every shot in one Blender, then grade, pages, checks, sheet
python3 -m sagekit icons dwarves              # grade, pages, checks and sheet from the renders there
python3 -m sagekit icons dwarves --stage | --install | --revert [--dry-run]
```

Tables: Dwarves, Elves, Men (Arnor shows Gondor's icons), Goblins, Isengard, Mordor, Angmar (RotWK's
512 x 512 `expansion1icons` pages) and neutral (the Inn). Review sheets:
`build/assets/<faction>/_review/icons_v1.jpg`.

## The table

`assets/<faction>/icons.py` names each image and how to shoot it (`sagekit/icons/__init__.py`
has the fields): `Portrait(building, azim, elev, fill, at, focus, frame, extra)` and
`Button(...)`. The camera looks from (azim, elev) at the `focus` part of the framed meshes' box
and stands where that fills `fill` of the frame; lens shift puts its centre at `at`. `extra` draws
neighbours (the wall segments either side of a hub, as EA's wall portraits show them). `KEEP`
lists building art that stays EA's, with the reason (the catapult buttons are the catapult unit).
Each shot renders our model as it ships and EA's through the same camera, so a table's framing is
checked against EA's own icon (`_icons/crops/<image>_ea.png`). `--map` proposes images from the
objects each recipe draws (SelectPortrait, CommandButton `Object`); an upgrade button names the
object it turns into, which is not always the one the player builds (the Dwarven wall buttons name
the map's castle walls), so the table decides.

## The steps

| Step | Where | What |
|---|---|---|
| render | `icons/render.py`, `blender/icon.py` | at 4x the page's pixels (2x pages later need no new renders): the colour renders' materials and house colour, EA's dirt terrain fading out round the building (no hard horizon: the ground melts into the parchment as on EA's), transparent sky; a portrait is framed by its silhouette (what stands 5% of its height above the ground, so bibs, decals and rubble leave the frame to the ground); a tower (standing 1.4 times its width, framed whole) stands as EA's do: its body 84% of the frame tall, its foot 92% down, a thin spire above the body free to run into the burnt edge; a table's `frame` or `focus` part keeps its own fill |
| grade | `paint/icons.py` (Blender's Python) | portrait: a faint parchment sky, a burnt edge, luminance matched rank for rank to EA's portrait and coloured by EA's sepia at that luminance, 30% of our own colour kept; button: a blue sky with EA's clouds (or a stone wash), luminance and colour moved part way to EA's button; box-filtered to 1x, sharpened a little, EA's alpha exactly |
| pages | `icons/pages.py`, `icons/cli.py` | EA's page with our crops pasted; EA's format, size and 9 mips; every block no rect of ours touches is EA's bytes; ImageMagick writes no DXT3, so a DXT3 page keeps its colour blocks and stores the DXT5 alpha as DXT3's 4 bits |
| checks | `icons/pages.py` | format, size and mips EA's; pixels outside our rects EA's (exactly away from shared blocks); our rects the intended pixels within DXT error; alpha EA's within the 4-bit step |
| sheet | `icons/sheet.py` | `build/assets/<faction>/_review/icons_v1.jpg`: EA against ours at 1x and 2x, every page before and after |
| archive | `icons/install.py` | `!!!!!!!!!!!!!!sagekit-icons.big`, one for every faction (pages serve several), rebuilt from every installed faction's crops on each install and revert; no asset.dat records (EA's names and sizes) |
| release | `icons/install.py` `release()`, `packbuild.py` | each faction's pack carries `!!!!!!!!!!!!!!sagekit-icons-<faction>.big`, its own pages as deltas against EA's; refused while a page holds two factions' icons (none does today) |

An uncompressed page (`expansion1icons_021`, the Elven `buildingradialbuttons_150`) keeps EA's
top level byte for byte outside our rects; ImageMagick reads and writes such pages as BGRA whatever
their masks say, so `pixels.raw_dds` decodes them by their masks and the writer swaps to EA's RGBA.
On RotWK's pages the 64-pixel icons sit one pixel apart off the 4-pixel grid: a neighbour's edge
column shares DXT blocks with ours and moves by DXT's error (the check allows up to 96).

## Not covered yet

- Builders keep EA's face icons. A bust render through `sagekit/units/render.py` is easy, but EA's
  unit portrait (`UPDwarven_Porter`, 191 x 191) and button (`BDFortress_Porter`) are paintings of the
  face, which our redesign keeps; a render of the game mesh would be a visual downgrade. The
  portrait page also holds `UPAngmar_Porter`.
- 2x pages: the renders are 4x; the MappedImage UVs are Coords over the INI's declared size in EA's
  Generals source, unproven for BFME2, so the pages ship at EA's 256.
- The release pack (`sagekit/pack.py`) does not carry the icon archive yet.
