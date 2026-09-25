# Dwarven archery range (`DwarvenArcheryRange`)

Model `DBArchRnge_SKN` (a skinned model: separate skeleton `DBArchRnge_SKL`, animated archer and
smith). The redesigned mesh is `ARCHERYRANGE`, which holds the hall, the tower base, the gallery and
the four tower posts. It gets its own texture, `dbarchrngh.dds` / `dbarchrngh_nrm.tga`. Nothing else
changes: the archer, the props, `ARCHERYBASE`, the upgrade meshes `V1` / `V1A` / `V2` and the bones.

## What changed (body, healthy)

- **East door → portal:** a stepped pointed portal that stands out from the wall
  (`portal()` in `building.py`). It has three rings. The inner rings are set back and carry the
  triangle frieze on their fronts and bronze on their inner faces. Inside the arch is a rune
  panel, with a rune band across the front above it. The top is a stepped crown: bronze
  cornice, a tier with the triangle frieze, then a point. The door opening (y -4.6..9.3, height
  19.8) stays clear.
- **Hall roofline:** a stone ridge cap with the hexagon chain on both sides, topped by four large
  stepped-triangle chevrons.
- **South gable:** a relief of three stepped tiers (rune tier, bronze tier, stone tier) and a
  point, set under the crossed barge boards.
- **Tower top:** on each side between the posts, a corbelled cornice with the hexagon frieze
  and a bronze drip, then a solid chevron parapet outside EA's plank railing. The west side has
  a parapet only north of the ladder (y > 41).
- **Tower posts:** a bronze rune collar on each of the four posts at z 35–39.
- **Gallery:** chevron parapets on both long sides. The south one stops short of the ground
  ladder. Below them are a rune fascia and a bronze corbel table on corbels.
- **Hall base:** low battered plinths along the west and east walls. The east plinth runs around
  the portal.

Footprint unchanged. Height unchanged (+0 %; the posts' 72.0 stays the top). The mesh has 2,282
triangles, up from 861 (2.7x; the budget is 15,000). Every new face faces outward, and no new
face shows its back to the sky.

## Status

| Part | Healthy | Construction | Damaged / really damaged / rubble | Snow | LOD M/L |
|---|---|---|---|---|---|
| body (`DBArchRnge_SKN`) | geometry and paint done; **build blocked at `cache`** (framework) | old (`DBArchRnge_A`) | old (no derived models: D1/D2/D3 do not carry a rigid `ARCHERYRANGE`) | variant `dbarchrngH_snow.dds` painted | old |
| banner (`DBHCArchRnge`) | old | | | | |

What still blocks the full pipeline (all in `sagekit/`, reported, not worked around):

1. **`cache` fails.** The model is filed in RotWK's `asset.dat`, but its sheet `dbarchrnge.tga` is
   filed only in BFME2's: `CacheError: no asset record for dbarchrnge.tga to copy`. Also, neither
   cache has an object record for `DBARCHRNGE_SKN.ARCHERYRANGE`. `cache_ops` is overridden here to
   register the textures without switching a dependency. Because of that missing record, the
   check "ARCHERYRANGE depends on dbarchrngh.dds" cannot pass as written.
2. **`checks` and `render` cannot import the shipped model.** Its hierarchy is the separate
   `dbarchrnge_skl.w3d`, which is not next to `out/art/w3d/db/dbarchrnge_skn.w3d`.
3. **Some checks fail on EA's own meshes.** "parented to bone" expects `BONE`, but this model's
   meshes are skinned (`ARMATURE`) or object-parented. "UV layers inside [0,1]" fails on EA's
   archer/prop UVs. These fail for the untouched original meshes too.

For review, the checks were run from a scratch script on the shipped model copied next to its
skeleton, with the asset cache section skipped. Every geometry, texture, layout and byte-identity
check passes. The only failures are the 33 checks on EA's meshes described in item 3.

`bake_hidden` leaves the archer, the smith, their props, the ground plate and the night windows
out of the bakes, so they don't bake shadows onto the sheet. It hides them in the renders too.
