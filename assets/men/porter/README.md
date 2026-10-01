# Men of the West builder (`GUPorter_SKN`)

A Gondor stone-mason, for Gondor and Arnor alike (both draw `GUPorter_SKN`). EA's man, face, rig and
animations are kept; the cart, load and tools are new, bound to EA's bones:

- **Cart:** dark timber bed with low sides, iron straps and axle, open ten-spoke wheels with iron
  tyres, steel hubs and gilt bosses, steel-capped corner posts with small gilt orbs. The shafts and
  crossbar sit on EA's grip line.
- **Crest:** a sable gable on the front board with the White Tree and seven stars in a steel frame,
  facing the man and the RTS camera. It stays under his arms (he reaches into the cart in the work
  and water animations) and clear of the corner where EA's hammer rides.
- **Gonfalon:** a swallow-tailed cloth in **player colour** with the White Tree on both faces, on a
  tall pole at the back corner; a plumb line hangs from the pole.
- **Load:** dressed white ashlar in a stepped stack, a lintel and cornice, a carved capital, a rope
  coil, the mason's mallet, a chisel and a steel square. The middle stays open for EA's bucket (it
  rides there, and slides out to +y when the man dies).
- **Man:** a dark tool belt with a steel buckle, a pouch, and a chisel in a loop. EA's hammer keeps
  its vertices and bones but takes a steel head and an ash handle.

```sh
python3 -m sagekit unit men/porter --render     # build/assets/men/porter/renders/compare_<state>.png
python3 -m sagekit unit men/porter --check | --stage | --install | --revert
```

1,144 -> 7,784 triangles. One private atlas, `GUCrafts.tga` (2048 x 1024: EA's `GUPorter` sheet
tiled on the left, 16 Gondor-palette swatches on the right), and `HC_GUCrafts.tga`, EA's
`HC_GUPorter` mask tiled. The gonfalon samples a clean patch of EA's shirt in the unused top-left
tile, so the game tints it with the player colour the way it tints his shirt; there the diffuse is
painted navy, the Men's preview stand-in (`check` asserts the patch is fully inside EA's mask).
The bucket is EA's, byte for byte.

## Known limits

- Not checked in game: player colour on the gonfalon, wheel rotation.
- EA's cart side planks took player colour (`HC_GUPorter_Cart`); ours carry it on the gonfalon
  instead, and the man's shirt keeps EA's.
- EA's animations themselves press the bucket into the right side board at the end of `diea` and
  the man's hips and elbows into the shafts in `diea` / `dieb`, as on EA's cart.

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
