# Goblin builder (`WUPorter_SKN`, shipped as `WUBuilder_SKN`)

A scavenger hauling plunder out of Goblin-town: a crooked charcoal-timber cart lashed with hide,
scrap plates, mismatched wheels (a solid plank disc slashed with white war paint, a salvaged spoked
wheel with a bone for a spoke), a crimson tarp over the sacks, a spider-silk cocoon, bones, skulls,
a shield on the headboard, a broken spear, bone tusks on the front corners, a horned skull on a
stake with crimson rags, and a tattered rag standard in the player's colour. EA's bucket is a
dented horned helm. Palette E, "blood, iron and bone" ([style.py](../style.py)). The orc, skeleton
and animations are EA's; the orc mesh is EA's byte for byte.

```sh
python3 -m sagekit unit goblins/porter --render     # build/assets/goblins/porter/renders/compare_<state>.png
python3 -m sagekit unit goblins/porter --check | --stage | --install | --revert
```

`design.py` is the recipe (pieces, bones, atlas paint); `kit.py` its shapes (crooked beams, lathed
bundles, skulls, rags, drapes, wheels) and the house-colour region. How a recipe works:
[docs/UNITS.md](../../../docs/UNITS.md).

## Our model

- **Rebuilt:** `CART` (the cart, shafts, stake and standard), `CARTSUPPLIES` (the load), `BUCKET`
  (the helm), `WHEEL_L01`, `WHEEL_R01`; each stays rigid on EA's bone, so the wheels spin and fall
  off in the deaths as EA's do. `ORCPORTER` is EA's (checked). 720 -> about 6,500 triangles.
- **Atlas:** one private sheet, `WUCrafts.tga` (2048 x 1024), for `MUPortCart.tga`,
  `GUPorter_Build.tga` and `GUPorter_Cart.tga`; the orc keeps `MUOrcPorter.tga`. The right half is 16
  palette swatches with EA's painted grain; the left half is neutral cloth under the mask.
- **Player colour:** `HC_WUCrafts.tga` is EA's 64 px `HC_MUPortCart.tga` tiled across the left half
  (the framework's mask, unchanged). In every 64 px tile, x 51..63 and y 35..63 (running into the
  next tile's top band) is solid house colour; the standard's rags (tag `HOUSE`) map into the inner
  part of one such tile (`kit.HOUSE_BOX`, alpha 255 with a 1 px margin). Nothing else maps there,
  so only the banner takes the player's colour. The preview draws it neutral grey.

## Status

Design preview; not installed. Not checked in game: player colour, wheel spin.

## What EA has

- **Object:** `WildPorter` (`data\ini\object\evilfaction\units\wild\wildporter.ini`, built by `WildFortressCommandSet` and its Evil Lorien / Rivendell / monument variants).
  Its INI plays DIEB for DEATH_1.
- **Shared model:** Isengard, Mordor, the Goblins and Angmar all draw EA's orc porter
  `WUPorter_SKN`. So this recipe ships its copy under its own name, `WUBuilder_SKN` (`own_model`, free
  in every archive and cache), and repoints only `WildPorter`'s Draw (`objects`); Angmar keeps EA's.
- **Model:** `WUPorter_SKN` (`W3D.big`, 720 triangles): `ORCPORTER` the orc (skin, 258 tris,
  `MUOrcPorter.tga`); `CART` (112 tris), `WHEEL_L01`, `WHEEL_R01` (32 each), all
  `MUPortCart.tga`; `CARTSUPPLIES` (`GUPorter_Build.tga`); `BUCKET` (`GUPorter_Cart.tga`).
  Everything but the orc is **rigid**: one HLOD bone per mesh (`CART` and `CARTSUPPLIES` on
  `CART`, the wheels on `WHEEL_L01` / `WHEEL_R01`, `BUCKET` on `BUCKET`). Pieces added to a
  rigid mesh follow its bone; `skin=True` makes it a skin whose pieces may follow any bone.
  `MUOrcPrtr_SKN` (the cinematic `CINE_MordorPorter`) is a separate copy of the same model.
- **Skeleton:** `MUOrcPrtr_SKL`, 20 pivots: `BAT_PELVIS`, legs to `B_TOEL` / `B_TOER`,
  `BAT_SPINE2`, arms to `B_HANDL` / `B_HANDR`, `BAT_HEAD`, `WHEEL_R01`, `WHEEL_L01`, `CART`,
  `BUCKET`. No hammer bone.
- **Animations:** `muorcprtr_idla idlb runa wlka fira diea dieb`. No work animation: the orc
  porter never shows a construction pose (no ACTIVELY_CONSTRUCTING state), so there is no work view.
- **Textures:** `MUOrcPorter.tga` (256 px), `MUPortCart.tga` (128 px); the bucket and load draw
  Gondor's sheets, which other factions draw too.
- **Player colour:** only the cart: `MUPortCart.tga` -> `HC_MUPortCart.tga` (64 px). The orc's
  sheet has no mask. (`housecolor.ini` also maps `WUPorterCart.tga`, which no model draws.)
- **asset.dat:** RotWK's cache files `WUPorter_SKN` twelve times (duplicates, the HLOD object
  only), BFME2's once with seven object records. The copy is filed in RotWK's cache as a copy of
  EA's record (`add_model`); the private sheets are registered in BFME2's, where `MUPortCart.tga`
  is (`Install.route_cache_ops`).
- Construction workers (`MordorWorker`, `WildLaborer`: `MUOrcLabor_SKN` on `MUGblnSlv_SKL`) are
  not part of it.
