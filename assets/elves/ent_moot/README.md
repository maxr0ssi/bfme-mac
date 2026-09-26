# Ent moot (`ElvenEntMoot`, `elvenentmoot.ini`)

Model `FBEntmoot`, one mesh `FENTMOOT` (381 triangles), painted from `FBEntmoot.tga` (DXT5 with
cut-out alpha, kept; no normal map). Our texture is `FBEntmooH.tga` (+ `_snow`, `_D`, `_D2`); new
faces are mapped onto the faction atlas. `Tier.STANDARD`.

## The original (measured, mesh = model coordinates)

- **Floor:** a grass octagon about 180 across at z -1.4. Its box, x -91.3..89.3, y -96.3..97.8, is
  the footprint.
- **Boulders:** eleven round the rim at radius 65-93, tops 8-20.
- **Horn:** a great horn of rock rises from the rim at +y and leans in over the floor to its tip at
  (0.9, 28.7, 52.4).
- **Trees:** the moot's upgrades plant trees at (-30, 65), (30, 65), (-61.16, -17.11) and
  (70.65, -29.12) (`ObjectCreationUpgrade`, `TreeLothlorien08EntMoot`); these stay clear.
- **House colour:** `RBHCEntMoot` is flowers, so there is no cloth.

## What changed (body, healthy)

It stays a clearing: nothing is built, with no gold, lanterns or cloth.

- **Standing stones:** eight rough standing stones fill the gaps in EA's ring of boulders, so the
  ring reads whole. The tallest pair (28-29) flanks the horn's root like a gate. Each stone is a
  thick irregular slab that swells, then draws in to a blunt, sloping top; it leans a little and
  turns its broad face to the middle.
- **Fallen stones:** one or two lie at each stone's foot.
- **Paint:** the stones take the atlas's bark grain, which is never masonry (no ashlar joints). It is
  painted in the stone ramp, lifted to the grey of EA's recoloured boulders (`decals()`), with moss
  from the style's layers.
- **Open ground:** the middle, where the Ents gather, and the four tree places stay open. `design()`
  refuses a stone within 14 of a tree.

Footprint and height unchanged (the horn stays the highest point). Triangles 381 -> 1,205.
Texel density median 2.5 px/unit: the floor is most of the area. `checks`: 75/75.

`facet_islands = True`: every original face is its own UV island. Blender's unwrap of the horn's
smooth shell folded onto itself (3 % overlap). This is a new opt-in `Building` attribute (see the
report's framework notes).

## Status

| Part | Healthy | Construction | Damaged / really damaged | Rubble | Snow | LOD |
|---|---|---|---|---|---|---|
| body (`FBEntmoot`) | built, checks pass, **awaiting review** | built (`FBEntmoot_A`, lifecycle) | derived (`FBEntmoot_D1`, `_D2`) | built (`FBEntmoot_D3`, lifecycle) | `FBEntmooH_snow` painted | none |

## Notes for review

- **Rock colour.** The faction's recolour turns EA's warm brown boulders and horn moonstone-grey,
  with yellow lichen flecks where the masks read gold. The new stones match that grey. Keeping the
  moot earthy would need the style's rock handling for this sheet (a decision for Max).
- **Night.** The model has no night meshes; nothing is lit.
