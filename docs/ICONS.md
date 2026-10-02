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
| render | `icons/render.py`, `blender/icon.py` | at 4x the page's pixels (2x pages later need no new renders): the colour renders' materials and house colour, EA's dirt terrain, transparent sky |
| grade | `paint/icons.py` (Blender's Python) | portrait: a faint parchment sky, a burnt edge, luminance matched rank for rank to EA's portrait and coloured by EA's sepia at that luminance, 30% of our own colour kept; button: a blue sky with EA's clouds (or a stone wash), luminance and colour moved part way to EA's button; box-filtered to 1x, sharpened a little, EA's alpha exactly |
| pages | `icons/pages.py`, `icons/cli.py` | EA's page with our crops pasted; EA's format, size and 9 mips; every block no rect of ours touches is EA's bytes; ImageMagick writes no DXT3, so a DXT3 page keeps its colour blocks and stores the DXT5 alpha as DXT3's 4 bits |
| checks | `icons/pages.py` | format, size and mips EA's; pixels outside our rects EA's (exactly away from shared blocks); our rects the intended pixels within DXT error; alpha EA's within the 4-bit step |
| sheet | `icons/sheet.py` | `build/assets/<faction>/_review/icons_v1.jpg`: EA against ours at 1x and 2x, every page before and after |
| archive | `icons/install.py` | `!!!!!!!!!!!!!!sagekit-icons.big`, one for every faction (pages serve several), rebuilt from every installed faction's crops on each install and revert; no asset.dat records (EA's names and sizes) |

## Not covered yet

- Builders keep EA's face icons. A builder button would need a posed bust render of the unit
  recipe (`sagekit/units/render.py` poses it) against EA's portrait backdrop, on the unit pages
  (`unitportraits`, 256 x 256 per unit), graded like a button.
- 2x pages: the renders are 4x; the MappedImage UVs are Coords over the INI's declared size in EA's
  Generals source, unproven for BFME2, so the pages ship at EA's 256.
- The release pack (`sagekit/pack.py`) does not carry the icon archive yet.
