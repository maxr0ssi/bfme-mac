# Elves fortress (`ElvenCitadel`, `ElvenFortress`)

The faction's hero building (`Tier.HERO`: 4096 texture, 2048 normal map), own textures
`EBFortresH.tga` / `EBFortresH_NRM.tga` (DXT5: EA's cut-out alpha kept) and the variants
`EBFortresH_D`, `_snow`, `_U`, `_U_Snow`. Its upgrades (`fortress_eagles_nest`,
`fortress_enchanted_anvil`, `fortress_mystic_fountains`) and the crystal moat draw at the same
origin; build this one first. It is the example the other 22 Elven buildings follow.

## How we got here (2026-09-26)

1. **First pass** (commit 180bb7a): EA's body in a pale moonstone palette, eleven banners, gable
   finials, two lantern towers. Max: "all u did was change the colors."
2. **Rebuild pilot**: EA's body deleted and rebuilt as a white spired castle with 24 banners.
   Max: "Too many flags, and u removed details on the citadel… the point is to add the details
   lol some not loads."
3. **Palette**: after the stark white "Moonsilver" round, Max asked for "strong silver and gold
   elements with a soft white".

This round is the middle, the Dwarven fortress's level of change: EA's body kept whole, a handful
of real additions, four banners, and the new palette doing its share.

## What changed (body `EBFORTRESS1`, healthy)

EA's detailed body stays: the ring's arcade frieze, filigree lattice windows and carved leaf
gables, the four mallorn trees and their tree-houses, the gatehouse under its traceried roof, the
gate arch and the ramp (footprint, the 32 `ARROW_*` bones on the tree-house balconies,
`FELLOWSHIPBONE` and the smith's `POSITIONBONE` unchanged). No face of EA's is removed. New:

- **Silver coping** round the ring's cap (`COPING`, swept from the wing's wall on the face toward
  22.5 degrees round the back to the face toward -22.5): a mithril nose 0.55 proud and a top 3.3
  wide, its underside buried in EA's chamfer.
- **Gilt leaf finials** (6.4 tall) on the tips of EA's eight leaf gables.
- **Crystal lanterns** on slender silver posts over the six plain ring faces (the anvil's face,
  180, has none): a starlight crystal in a gilt cup with a gilt leaf tip, level with the gables'
  finials, so the ring's crown reads gable, lantern, gable, lantern.
- **Silver ridges on the tree-houses**: a cap following each ridge's sag between EA's horns, and
  a gilt leaf finial where the dormers' ridges meet it.
- **The gatehouse flèche** (`spire.py`) astride the gatehouse roof's ridge at x 61.5: an octagonal
  drum with a pointed lattice window front and back and a silver cornice, a corbelled **balcony**
  with a silver-railed balustrade (z 96), an open lantern of eight silver colonnettes round a tall
  starlight crystal, and a swept slate needle with silver ribs up its corners and a gilt leaf on
  the tip, the fortress's new top. A silver cap runs along the rest of the gatehouse ridge.
- **Two lantern towers at the gate** (x 72.4, y ±20.6, from the first pass): a moulded plinth, a
  leaf-capital column, an open lantern stage round a crystal and a swept slate needle.
- **Banners: four**, long leaf banners in the player's colour: one on the front of each gate
  tower, facing down the ramp, and one on each side of the flèche's drum, over the roof's slopes.

The paint (the Elven style, `assets/elves/style.py`) does the rest: soft ivory stone, EA's tan
gable frames, swooping beams, leaf emblems and roof tracery repainted strong mallorn gold, the
tree-house and gatehouse roofs a mid slate, the lattice windows' leading silver, EA's teal kept in
its lattice glass and frames.

## Palette ("Ivory, mithril and mallorn gold")

| Material | Where | Values (sRGB) |
|---|---|---|
| stone | EA's walls, new stone | ivory, mids (0.82, 0.80, 0.75) .. (0.87, 0.85, 0.81), shading to warm grey (0.53, 0.50, 0.46) |
| silver (`trim`, `inlay`) | copings, ridges, posts, ribs, knotwork, window leading | cool mithril, mid (0.60, 0.67, 0.77), highlights (0.92, 0.95, 1.0), lows (0.24, 0.29, 0.37) |
| gold (`gilt`, `gold`, `bronze`) | finials, cups, capitals, EA's tan frames and tracery | mallorn gold, mid (0.82, 0.62, 0.22), highlights (0.99, 0.89, 0.53), lows (0.40, 0.25, 0.06) |
| roofs (`tiles`) | EA's slate, new roofs (Scales) | mid slate (0.33, 0.37, 0.42) .. (0.53, 0.57, 0.62) |
| teal (`ground`, `iron`) | EA's lattice glass, teal frames, knotwork ground only | muted sea-glass (0.30, 0.50, 0.49) |
| groove | stone beside new metal (Groove) | (0.36, 0.38, 0.42) |
| cloth | banners | the player's colour, the only saturated thing |

EA's motifs are repainted by `Repaint` layers keyed on the sheet position (`atlas.py` `gilded`,
`roof_slate`, `roof_scales`, `leading`) and the original colour; they run only for buildings
painted from the faction sheet `EBFortress.tga`.

## Numbers

- Footprint unchanged (x -54.2..93.47, |y| 54.2); top 122.89 -> 139.26 (the flèche's gilt leaf;
  height +13.3 %, limit 20 %).
- Triangles 5,326 -> 14,818 (budget 15,000): 9,492 new, of which 4,342 gilt (leaf finials, capital
  leaves, lantern cups: the leaf blades are the costly part), 2,772 silver. Texel density median
  7.8 px/unit.
- House colour: 48 cloth faces (4 banners) -> `EBHCFortress`, shared with the upgrades.
- Checks: 114/114.

## Layout

`facet_islands = 20`: EA's mallorn trunks and roots, unwrapped whole, fold over themselves in the
new layout, so EA's faces are also cut at EA's own UV island borders and where they turn more than
20 degrees (sagekit/blender/layout.py). The fortress's upgrades set the same.

## Night lights

EA's fortress has no night meshes (no `N_WINDOW` and no `NightWindowName` in the INI), so there is
nothing to relight; the recipe declares no lights. The crystals are day-lit only.

## Status

| Part | Healthy | Construction | Damaged | Really damaged / rubble | Snow / stonework |
|---|---|---|---|---|---|
| body (`EBFortress`) | built, checks pass, **awaiting review** | ours (`EBFortress_A`) | texture swap (`EBFortresH_D`) | ours (`_D2`, `_D3`) | painted |
| banner (`EBHCFortress`) | our cloth, shared with the upgrades | hidden | | hidden | |

Lifecycle (`work/lifecycle.json`): all three states carry our body along EA's pieces, none fell
back to EA's. `_D3` notes the lifecycle step's usual warning for its piece `A1` (its bone's
visibility is animated, our faces ride a skin). The banners are hidden while the fortress is built
or broken.

The renders draw only this building's own cloth from the shared `EBHCFortress` (the upgrades'
banners are drawn with the upgrades; sagekit/blender/render.py `only_own`). EA's other meshes
(`EBFORTRESS2` teal gate arch and railings, `EBFORTRESS3` lanterns, `EBFORTRESS4` foliage) keep
EA's sheet and follow the faction's sheet recolour (`sagekit sheets elves`), which has no Repaint.

Review sheet: `build/assets/elves/fortress/renders/citadel_review.jpg` (EA, the first pass, ours at
the RTS, close and gate cameras).
