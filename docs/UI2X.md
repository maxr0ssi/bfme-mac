# Retina 2x for portraits, buttons, our icons and the tooltip frame

At 3024x1964 the command bar's MappedImages are magnified: a unit portrait 1.8x, a 64 px button
about 1.4x (measured on a match screenshot, `build/assets/_review_finish/hud_inventory/inventory.md`).
`sagekit/ui2x/` ships them at twice EA's pixels, with no INI change.

```sh
python3 -m sagekit ui2x --stage               # build, check, stage, duplicate scan, review sheets
python3 -m sagekit ui2x --sheet               # the review sheets only
python3 -m sagekit ui2x --install [--dry-run] # !!!!!!!!!!!!!!sagekit-ui2x.big + the icon archive at 2x
python3 -m sagekit ui2x --revert [--dry-run]  # removes it, the icon archive back at 1x
```

Review sheets: `build/assets/_review_finish/ui2x/` (`portraits.jpg`, `buttons.jpg`, `icons_*.jpg`,
`hardest.jpg`, `tooltip.jpg`): EA's 1x beside our 2x at the size a 3024x1964 screen draws them, and a 2x detail.

## Why a bigger page is enough

A MappedImage's UVs are its `Coords` over the size the INI declares (`TextureWidth/Height`), not
over the loaded page. RotWK's 2.02 patch ships `ResourceBarIcons` declared 256 x 32 on a 512 x 64
page, and it draws whole. So every page here is twice EA's size with the INI untouched: the same
UVs, four times the texels. A page doubles only when every image on it, from any INI, declares the
page's real size and lies inside it (`uaportrait`, declared 192 on a 256 page, stays EA's), and
only power-of-two pages (the 1424 x 356 Create-a-Hero strip stays EA's). The skipped pages and
why: `build/assets/_ui2x/skipped.txt`.

## What is covered

| Item | What | Where it ships |
|---|---|---|
| 1 | the pages our building icons sit on: our crops box-filtered from the icon run's 4x renders, EA's other images on those pages upscaled | `!!!!!!!!!!!!!!sagekit-icons.big`, rebuilt at 2x (docs/ICONS.md) |
| 2 | unit and hero portraits (`unitportraits.ini`, `heroui.ini`, `expansion1icons.ini`) | `!!!!!!!!!!!!!!sagekit-ui2x.big` |
| 3 | 64 px buttons: unit commands, hero abilities (on the `heroui` pages), the hero bar (`heroselecticons.ini`), the spell book | the same |
| 4 | the tooltip frame: PalantirExport's ten `helpBox*` images, repainted, at 2x | the same, with the help box's and notification box's geometry |

A page any faction's icon run draws on belongs to the icon archive and is never in the ui2x one;
the stage scans every staged and installed `*sagekit-*.big` and refuses a member two of them carry.

## How EA's paintings are upscaled (`sagekit/paint/ui2x.py`)

EA's portraits and buttons have no larger source. Per image (per MappedImage rect):

1. EA's pixels, padded by their own edge; the colour under invisible pixels refilled from the
   visible ones. On a round button the fringe is refilled too (EA's fringe pixels are dark, and the
   upscaler drew them as a stair-stepped dark rim); any other shape keeps its fringe colour (the
   hero bar's faces have a light edge).
2. Real-ESRGAN 4x (`downloads/realesrgan`, `realesrgan-x4plus`), box-filtered to 2x.
3. EA's grain put back: the high frequencies of a Lanczos 2x of EA's pixels (0.7). Real-ESRGAN alone
   airbrushes the brush work and the parchment; the anime models flatten it to a cartoon (both
   rejected on the pilot faces). Images under 100 px keep a fifth of the Lanczos: Real-ESRGAN alone
   made the hero bar's tiny faces stare. Where the result, box-filtered back to 1x, strays from EA's
   picture (mean colour error over 0.045: busy noisy art such as webs, ivy and bark, where
   Real-ESRGAN invents strands), half as much Real-ESRGAN, then none (Lanczos with EA's grain).
   `hardest.jpg` shows those.
4. The alpha: Lanczos 2x, which keeps an edge as soft as EA drew it (a portrait's vignette, the
   hero bar's silhouettes). A round button's mask (a hard edge that is a circle, fit through EA's
   0.5 crossings within 1.5 px everywhere) is steepened to a one-pixel edge and its rim drawn as
   an exact anti-aliased circle: EA's 1x discs are stair-stepped, and at 2x the steps showed.
5. Pasted on a Lanczos 2x of EA's page; the mips box-filtered and sharpened a little (a button drawn
   at 1.4x of EA's size samples the 2x page at 0.7x, partly from mip 1).
6. Checked: box-filtered back to 1x, every rect must be EA's picture (mean colour error under 0.06,
   alpha under 0.04; EA's DXT noise removed counts towards it), and the page EA's format at twice
   its size with one mip more.

The DDS keeps EA's header and format (DXT3 stays DXT3); EA's uncompressed pages become DXT5 at 2x
(an uncompressed 1024 x 1024 page would cost 5.6 MB).

## The tooltip frame (`sagekit/ui2x/tooltip.py`)

The help box (`ingamehelpbox`) and the notification box (`ingamenotificationbox`) have no textures
of their own: their APT import tables pull PalantirExport's `helpBox*` images (export ids 1-10,
textures `apt_palantirexport_1..10.tga`), and no other movie imports them. PalantirExport's own
geometry only samples the palantir frames (the HUD pack's), never these. So the ten textures ship
at 2x with the 20 styles in the two movies' `.ru` files that sample them doubled (the method of
docs/HUD.md, through the import table).

One set serves both sides (EA's is gold on both). The frame lines and ornaments take the Good
palantir's bronze and gold (`assets/hud/look.py` `regrade`); the glow is EA's, warmed toward the
ember. An iron frame for Evil would need the movie to know the side: not done.

## Cost and LAN

- Texture memory (DDS bytes; a page only loads when something on it is drawn):
  item 1 +33.3 MB (99 icon pages), items 2-3 +53.5 MB (401 pages; EA's are 19.2 MB), item 4
  +1.5 MB: +88 MB if every page were drawn at once. A match draws the pages of the factions in it,
  a fraction of that; the game runs with 4 GB of address space (docs/MEMORY-4GB.md). Measured
  2026-10-04 from the staged archives.
- No INI change, no upgrades, no asset.dat records: every page keeps EA's name and EA's record (a
  texture's record has no size or format; the DXT5 pages too). The stage and the install check that
  asset.dat files every texture both archives ship (`sagekit/texrecords.py`).
- Everyone in a LAN game should run the same files (MULTIPLAYER.md); nothing here changes game data.
- Not yet seen in game. If a 2x page draws wrong, `--revert` puts EA's sizes back.
