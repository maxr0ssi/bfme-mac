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

The RotWK HUD has only these two skins, Good and Evil. A palantir per faction would need new APT
movies (the research put it at large to extra-large, with a high crash risk): not done.

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
5. Box-filtered to 2x and 1x and sharpened a little. The 1x carries EA's alpha byte for byte, the
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
- No INI, no upgrades, no asset.dat records (EA's names; TGAs need no record).
- The archive changes textures and APT geometry only. Everyone in a LAN game should still run the
  same files (MULTIPLAYER.md); it ships in the archive like every other pack.

## Not covered yet

- The spell book frame (`apt_spellstore_1`), the side command bar, menus: same method, not done.
- The release pack (`sagekit/pack.py`) does not carry the HUD archive.
