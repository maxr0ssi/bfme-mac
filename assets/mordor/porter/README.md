# Mordor builder (`WUPorter_SKN`, shipped as `MUBuilder_SKN`)

A slave-driver's cart on EA's orc porter: black iron walls with jagged steel teeth and ember-lit
edges, hooked spikes clawing up from every corner, a heap of rough basalt with hewn columns, an
ember brazier in a claw of hooked spikes (the citadel's crowns in small), shackles on chains, a
coiled whip on the shaft, iron-shod wheels with spiked hubs, and a ragged war banner. EA's wooden
bucket is an iron pail on the same bone. The orc keeps EA's body, face, skeleton and animations;
only his robe is re-dyed in ash and soot. Palette F2 (`assets/mordor/style.py`), no green.

```sh
python3 -m sagekit unit mordor/porter --render     # build/assets/mordor/porter/renders/compare_<state>.png
python3 -m sagekit unit mordor/porter --check | --stage
python3 -m sagekit unit mordor/porter --install | --revert
```

`design.py` is the recipe ([docs/UNITS.md](../../../docs/UNITS.md)), `kit.py` its shapes (rough
lumps, hooked spikes, teeth, chain links, rings). The views are EA's (no work pose, see below)
plus `fall` (DIEB) and `load`, a close look at the cart.

## What changed

- **Meshes:** `CART`, `CARTSUPPLIES`, `BUCKET` and both wheels are rebuilt on their own bones
  (all still rigid, as EA's); `ORCPORTER` keeps EA's vertices, bones and triangles (only its UVs
  move into the atlas). The shafts and crossbar keep EA's line, so the hands still grip them.
  720 -> 7,202 triangles.
- **Textures:** one atlas under two private names: `MUCraftsO.tga` (the orc) and `MUCrafts.tga`
  (cart, load, wheels, pail). Left half: EA's orc sheet, robe re-dyed, tiled 4 x 4; right half: 16
  F2 swatches with grain from EA's own sheets.
- **Player colour:** only `MUCrafts.tga` maps to `HC_MUCrafts.tga` (EA's `HC_MUPortCart.tga`
  tiled by the framework), so the orc never takes the cart mask. EA's mask is solid on a 7-pixel
  band and a 12 x 29 block of every 64-pixel tile; the iron bands round the walls and the banner
  are UV-mapped onto those (`Piece.uv_for`, tags `BAND` and `FLAG`, in the atlas' top-left tile).
  The previews paint that tile a stand-in red.

## Checks

The shared unit checks, plus: the orc draws only `MUCraftsO.tga`. Measured offline in every
animation (body vertices inside the new pieces): no more clipping than EA's own cart. The pail sits
on a basalt slab and the load keeps clear of its path out in the water animation (FIRA). As with
EA's, the bucket bone does not follow the cart in the deaths, so the pail meets the tipped load there.

## What EA has

- **Object:** `MordorPorter` (`data\ini\object\evilfaction\units\mordor\porter.ini`), built by
  `MordorFortressCommandSet`, `MordorCampKeepCommandSet` and the monument sets; no DEATH_1 state.
- **Shared model:** Isengard, Mordor, the Goblins and Angmar all draw `WUPorter_SKN`; this recipe
  ships its copy as `MUBuilder_SKN` and repoints only `MordorPorter`'s Draw. Angmar keeps EA's.
- **Model:** `ORCPORTER` (skin, 258 tris, `MUOrcPorter.tga`), `CART` (112), `WHEEL_L01`,
  `WHEEL_R01` (32 each, `MUPortCart.tga`), `CARTSUPPLIES` (`GUPorter_Build.tga`), `BUCKET`
  (`GUPorter_Cart.tga`). Skeleton `MUOrcPrtr_SKL`, 20 pivots, no hammer bone. Animations
  `idla idlb runa wlka fira diea dieb`; no work animation (the orc porter never shows a
  construction pose).
- **asset.dat:** RotWK files `WUPorter_SKN` twelve times, BFME2 once; the copy is filed as a copy
  of EA's record, the private sheets in BFME2's cache.
- Construction workers (`MUOrcLabor_SKN`) and `MUOrcPrtr_SKN` (the cinematic copy) are not part of it.

## Status

Design preview, not installed. Not checked in game: player colour, wheel spin.
