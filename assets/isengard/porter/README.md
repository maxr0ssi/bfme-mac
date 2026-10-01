# Isengard builder (`WUPorter_SKN`, shipped as `IUBuilder_SKN`)

An Uruk-hai labourer hauling Fangorn timber to the forges: EA's orc, skeleton and animations kept
(robe dyed charcoal, apron dark leather), on a black timber cart bound in riveted iron with silver
edges and faceted iron points at the corners. Heavy wheels with iron tyres and square cleats. On a
plank deck: five Fangorn logs, sawn ends pale with rings, chained down; a two-man saw strapped on
top; a crate of fresh iron ingots at the front. A kite plaque on each side and a pointed banner on
an iron pole carry the White Hand on the player's colour. Palette A
([style.py](../style.py)); the [Dwarven builder](../../dwarves/porter/design.py) is the template;
how a recipe works: [docs/UNITS.md](../../../docs/UNITS.md).

```sh
python3 -m sagekit unit isengard/porter --render     # build/assets/isengard/porter/renders/compare_<state>.png
python3 -m sagekit unit isengard/porter --stage      # the archive into _install/, nothing installed
python3 -m sagekit unit isengard/porter --install | --revert
```

`design.py` is the recipe (pieces and bones), `kit.py` the mesh helpers (oriented polygons, prisms,
wheels, chains, the White Hand), `paint.py` the atlas.

## What changed

- **Meshes:** `CART` (walls, shafts on EA's grip line, plaques, banner), `CARTSUPPLIES` (deck, logs,
  chains, saw, ingot crate) and the two wheels are rebuilt on their own EA bones; `ORCPORTER` keeps
  EA's vertices, bones and triangles (only its UVs move into the atlas); `BUCKET` is EA's byte for
  byte and rides hidden under the deck, as it did under EA's stone pile. 720 -> 8,504 triangles.
- **Textures:** one 2048 x 1024 atlas shipped under two private names: `IUPorter.tga` (the orc, no
  player colour, like EA's) and `IUCrafts.tga` (the cart, the load and the wheels).
- **Player colour:** `IUCrafts.tga` -> `HC_IUCrafts.tga`, EA's `HC_MUPortCart.tga` tiled every 64 px
  over the left half. In each tile, x 52..63 and y 42..63 plus the next tile's top band (y 0..6) is
  full alpha; the plaques' and banner's cloth (`kit.HOUSE`) map inside that patch in tile 0, which
  the orc never samples, over a light woven grey. Every other face samples the neutral swatches.
  The White Hands have a dark rim, so they read on any player colour. The renders show the grey.
- The wheels' cleats reach 0.25 below the ground plane (EA's tyres: 0.64), the tyres sit on it.

## What EA has

- **Object:** `IsengardPorter` (`data\ini\object\evilfaction\units\isengard\porter.ini`, built by `IsengardFortressCommandSet`, `IsengardCampKeepCommandSet` and the monument sets).
  Its INI plays DIEB for DEATH_1 and names a `BackingUp` animation no file has.
- **Shared model:** Isengard, Mordor, the Goblins and Angmar all draw EA's orc porter
  `WUPorter_SKN`. So this recipe ships its copy under its own name, `IUBuilder_SKN` (`own_model`, free
  in every archive and cache), and repoints only `IsengardPorter`'s Draw (`objects`); Angmar keeps EA's.
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
  Gondor's sheets, which other factions draw too. Ship private names (free: `IUCrafts.tga`, `IUPorter.tga`,
  `HC_IUCrafts.tga`), never EA's sheets.
- **Player colour:** only the cart: `MUPortCart.tga` -> `HC_MUPortCart.tga` (64 px). The orc's
  sheet has no mask. (`housecolor.ini` also maps `WUPorterCart.tga`, which no model draws.) The
  shared `house_mask` tiles a mask over the atlas' left half like EA's sheet; with the cart's
  128 px sheet and 64 px mask, plan where the cart's region and its mask go in the atlas.
- **asset.dat:** RotWK's cache files `WUPorter_SKN` twelve times (duplicates, the HLOD object
  only), BFME2's once with seven object records. The copy is filed in RotWK's cache as a copy of
  EA's record (`add_model`); the private sheets are registered in BFME2's, where `MUPortCart.tga`
  is (`Install.route_cache_ops`).
- Construction workers (`MordorWorker`, `WildLaborer`: `MUOrcLabor_SKN` on `MUGblnSlv_SKL`) are
  not part of it.

## Status

Design preview (`build/assets/isengard/porter/review_v1.jpg`), not installed. `--check` and
`--stage` pass.

## Known limits

- Not checked in game: wheel rotation, the house-colour patch, effects.
- The apron's texture is mirrored across the chest, so the orc carries no painted emblem.
