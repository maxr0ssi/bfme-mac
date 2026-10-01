# Mordor builder (`WUPorter_SKN`, shipped as `MUBuilder_SKN`)

Stub: `design.py` ships EA's builder unchanged. The design comes next, with the
[Dwarven builder](../../dwarves/porter/design.py) as the template; how a recipe works:
[docs/UNITS.md](../../../docs/UNITS.md).

```sh
python3 -m sagekit unit mordor/porter --render     # build/assets/mordor/porter/renders/compare_<state>.png
```

## What EA has

- **Object:** `MordorPorter` (`data\ini\object\evilfaction\units\mordor\porter.ini`, built by `MordorFortressCommandSet`, `MordorCampKeepCommandSet` and the monument sets).
  Its INI has no DEATH_1 state (DIEA only).
- **Shared model:** Isengard, Mordor, the Goblins and Angmar all draw EA's orc porter
  `WUPorter_SKN`. So this recipe ships its copy under its own name, `MUBuilder_SKN` (`own_model`, free
  in every archive and cache), and repoints only `MordorPorter`'s Draw (`objects`); Angmar keeps EA's.
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
  Gondor's sheets, which other factions draw too. Ship private names (free: `MUCrafts.tga`,
  `HC_MUCrafts.tga`), never EA's sheets.
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
