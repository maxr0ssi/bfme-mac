# Men of the West builder (`GUPorter_SKN`)

Stub: `design.py` ships EA's builder unchanged. The design comes next, with the
[Dwarven builder](../../dwarves/porter/design.py) as the template; how a recipe works:
[docs/UNITS.md](../../../docs/UNITS.md).

```sh
python3 -m sagekit unit men/porter --render     # build/assets/men/porter/renders/compare_<state>.png
```

## What EA has

- **Objects:** `MenPorter` (`data\ini\object\goodfaction\units\men\porter.ini`, built by
  `MenFortressCommandSet` and the monument sets) and `ArnorPorter` (`...\units\arnor\arnorporter.ini`,
  `ArnorFortressCommandSet` and its Fornost / Amon Sul / monument variants), each with a `NoSelect`
  child. Both draw `GUPorter_SKN` on `GUPorter_SKL`, so one in-place redesign is both factions'
  builder (Arnor follows the Men, as for the buildings). Cinematic objects draw it too.
- **Model:** `GUPorter_SKN` (`W3D.big`, 1,144 triangles): `GUPORTERLUIGI` the man (skin, 554 tris,
  `GUPorter.tga`), `CART_MESH` (skin on `WHEEL_R01`, `WHEEL_L01`, `CART`; `GUPorter_Cart.tga`),
  `CARTSUPPLIES` (skin on `CART`; `GUPorter_Build.tga`), `BUCKET` (rigid on `BUCKET`). The hammer
  is part of the man's mesh. `guporter_sknm` / `_sknl` exist (lower detail levels); like the
  Dwarven and Elven builders only `_SKN` is redesigned.
- **Skeleton:** `GUPorter_SKL`, 24 pivots: `WHEEL_R01`, `WHEEL_L01`, `PELVIS`, legs, `SPINE_1/2`,
  arms to `HAND_R` / `HAND_L`, `HEAD`, `CART`, `B_HAMMER`, `BUCKET`. The Elven builder uses the
  same skeleton and animations.
- **Animations:** `guporter_idla idlb runa wlka wlkb wrka..wrke fira diea dieb`. The INI plays IDLA,
  IDLB, WLKA (wander), RUNNING, DIEA / DIEB, WRKA / WRKB while constructing (the man walks away from
  the cart and hammers), ATNA; `PorterFireWater` on `BUCKET` when unpacking.
- **Textures:** `GUPorter.tga` (256 px), `GUPorter_Cart.tga`, `GUPorter_Build.tga` (256 px, HD
  Edition). The cart and supply sheets are also drawn by the Dwarven, Elven and orc porters'
  buckets and loads: ship private names (free: `GUCrafts.tga`, `HC_GUCrafts.tga`), never EA's sheets.
- **Player colour:** `GUPorter.tga` -> `HC_GUPorter.tga`, `GUPorter_Cart.tga` ->
  `HC_GUPorter_Cart.tga` (both 256 px); the supplies have none.
- **asset.dat:** filed in BFME2's cache only (one model record, five object records); the unit's
  records go there (`Install.route_cache_ops`).
- Construction workers (`GondorWorker`, `ArnorWorker`: `GUWorker_SKN`) are not part of it.
