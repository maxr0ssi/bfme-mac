# Elven fortress (`ElvenCitadel`, `ElvenFortress`)

Model `EBFortress`, mesh `EBFORTRESS1`, own texture `EBFortresH.tga` (from `EBFortress.tga`, EA's
cut-out alpha kept; variants `_D`, `_snow`, `_U`, `_U_Snow`). `Tier.HERO` (4096 texture, 2048
normal map). Palette: [`style.py`](../style.py). The [eagle's nest](../fortress_eagles_nest/README.md),
[enchanted anvil](../fortress_enchanted_anvil/README.md), [mystic fountains](../fortress_mystic_fountains/README.md)
and [crystal moat](../fortress_crystal_moat/README.md) draw at the same origin.

EA's body kept whole; four banners.

## What changed

- **Silver coping** round the ring's cap: a mithril nose 0.55 proud, a top 3.3 wide.
- **Ring crown**: gilt leaf finials (6.4 tall) on EA's eight leaf gables and crystal lanterns on
  silver posts over the six plain ring faces, so the crown reads gable, lantern, gable.
- **Tree-houses**: a silver cap along each ridge's sag, a gilt leaf finial where the dormers meet it.
- **Flèche** ([`spire.py`](spire.py)) astride the gatehouse ridge at x 61.5: an octagonal drum, a
  silver-railed balcony (z 96), an open lantern round a starlight crystal and a slate needle with
  silver ribs and a gilt leaf, the new top.
- **Two lantern towers** at the gate (x 72.4, y ±20.6): plinth, leaf-capital column, open lantern
  stage round a crystal, slate needle.
- **Paint**: EA's tan gable frames, beams, leaf emblems and roof tracery become gold, the roofs
  slate, the window leading silver; EA's teal stays in the lattice glass. EA's other meshes
  (`EBFORTRESS2` gate arch, `EBFORTRESS3` lanterns, `EBFORTRESS4` foliage) keep EA's sheet, recoloured.
- **Banners**: four, one on each gate tower facing down the ramp and one on each side of the
  flèche's drum; cloth in `EBHCFortress`.

## Kept clear

- The 32 `ARROW_*` bones on the tree-house balconies, `FELLOWSHIPBONE` and the smith's `POSITIONBONE`.
- The ring's face toward 180 has no lantern: the enchanted anvil carries the crown there.

## Status

Installed with the Elven pack. 5,326 -> 14,818 triangles (budget 15,000), height 123.2 -> 139.6
(+13.3 %), footprint unchanged, 114/114 checks. Construction, really damaged and rubble are rebuilt
along EA's pieces; damaged is a texture swap (`EBFortresH_D`). The banners hide while the fortress
is built or broken.
