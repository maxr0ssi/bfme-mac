# Angmar builder (`WUPorter_SKN`, shipped as `KUBuilder_SKN`)

A Hill-men thrall's cart hauling for the Witch-king: frost-grained timber walls with iron straps
and a crust of snow, warm plank floor, icicles hanging under the bed, iron-shod wheels with
rime-white tyres and hobnails, blue-black quarried blocks stacked with snow on their tops, a sawn
block of ice chained down with crystals growing out of it, a cold-fire lantern hanging from a crook
over the shafts (a pale-blue flame in an iron cage), the citadel's frozen-tip tines in small on the
four corners, and a swallow-tailed pennant in the player's colour on a pole with an ice point.
EA's bucket is a banded stave pail with a rime rim. The orc keeps EA's body, face, skeleton and
animations; only his robe is re-dyed in cold slate wool. Palette A2 "Carn Dum frost, warm timber"
([style.py](../style.py)).

```sh
python3 -m sagekit unit angmar/porter --render     # build/assets/angmar/porter/renders/compare_<state>.png
python3 -m sagekit unit angmar/porter --check | --stage
python3 -m sagekit unit angmar/porter --install | --revert
```

`design.py` is the recipe ([docs/UNITS.md](../../../docs/UNITS.md)), `kit.py` its shapes (snow-capped
blocks, ice shards and icicles, the sawn ice block, the frozen tine, chains, wheel rings). The
views are EA's (no work pose) plus `fall` (DIEB) and `load`, a close look at the cart.

## What changed

- **Meshes:** `CART`, `CARTSUPPLIES`, `BUCKET` and both wheels are rebuilt on their own bones
  (all still rigid, as EA's); `ORCPORTER` keeps EA's vertices, bones and triangles (only its UVs
  move into the atlas). The shafts keep EA's line, so the hands still grip them. 720 -> 6,782
  triangles.
- **Textures:** one atlas under two private names: `KUCraftsO.tga` (the orc) and `KUCrafts.tga`
  (cart, load, wheels, pail). Left half: EA's orc sheet, robe re-dyed, tiled 4 x 4; right half: 16
  A2 swatches with grain from EA's own sheets. Both names, `HC_KUCrafts.tga`, `KUBuilder_SKN` and
  the archive are free in every archive and both asset.dat files (checked 2026-10-01).
- **Player colour:** only `KUCrafts.tga` maps to `HC_KUCrafts.tga` (EA's `HC_MUPortCart.tga` tiled
  by the framework), so the orc never takes the cart mask. The pennant (tag `FLAG`) is UV-mapped
  onto the solid 12 x 29 block of EA's 64-pixel mask in the atlas' top-left tile, as Mordor's
  banner; nothing else maps there. The previews paint that block a stand-in red.

## Checks

The shared unit checks, plus: the orc draws only `KUCraftsO.tga`. Looked at in every view (rts,
run, walk, water, both deaths, portrait, load): the wheels sit on the ground, no piece seen
through the orc, the load keeps clear of the pail's way out in the water animation (FIRA). As with
EA's, the bucket bone does not follow the cart in DIEB, so the pail rests on the tipped load there.

## What EA has

- **Object:** `AngmarPorter` (`data\ini\object\evilfaction\units\angmar\angmarporter.ini`), built by
  `AngmarFortressCommandSet`, `AngmarCitadelCarnDumCommandSet` and the monument sets; its child
  objects `AngmarPorterNoSelect` and `AngmarProterDarkEye` inherit its Draw. No DEATH_1 state
  (DIEA for every death).
- **Shared model:** Isengard, Mordor, the Goblins and Angmar all draw `WUPorter_SKN`; the other
  three ship their own copies (`IUBuilder_SKN`, `MUBuilder_SKN`, `WUBuilder_SKN`). This recipe ships
  `KUBuilder_SKN` and repoints only `AngmarPorter`'s Draw (`ModuleTag_01`).
- **Model:** `ORCPORTER` (skin, 258 tris, `MUOrcPorter.tga`), `CART` (112), `WHEEL_L01`,
  `WHEEL_R01` (32 each, `MUPortCart.tga`), `CARTSUPPLIES` (`GUPorter_Build.tga`), `BUCKET`
  (`GUPorter_Cart.tga`). Skeleton `MUOrcPrtr_SKL`, 20 pivots, no hammer bone. Animations
  `idla idlb runa wlka fira diea dieb`; no work animation.
- **asset.dat:** RotWK files `WUPorter_SKN` twelve times, BFME2 once; the copy is filed as a copy
  of EA's record, the private sheets in BFME2's cache.
- Construction workers and `MUOrcPrtr_SKN` (the cinematic copy) are not part of it.

## Status

Design preview, not installed. Not checked in game: player colour, wheel spin.
