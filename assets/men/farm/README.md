# Men farm (`GondorFarm`, `ArnorFarm`)

Draft for review, not installed. Renders: `build/assets/men/farm/renders/compare_*.png` (level 1:
V1 and V2 hidden). The level-up meshes are chained on this recipe:
[`farm_level2`](../farm_level2/README.md) (V1, the yard wall) and
[`farm_level3`](../farm_level3/README.md) (V2, the upper storey); rebuild them after this one.
The body's Draw is FarmInterface's (`farminterface.ini`, ROLLOUT item 2).

## What changed

EA's cottage is kept whole (porch hood, flower boxes, windows, the thatched awning, the shed).
Second pass (the lead: more Gondor character):

- **Quoins** up the four corners, **kneelers** (moulded blocks, weathered tops) on the gable
  walls' corners under the eaves, a battered plinth.
- **Porch** before the west door: two columns, an architrave on side beams, a slated pediment
  with the White Tree on sable, raking cornices, a gilt knob (EA's hood stays behind it).
- **Windows**: pediments on consoles over the west and east windows; label mouldings with drops
  over the south and north windows (above EA's frames).
- **South gable**: the White Tree in a steel ring and the house-colour banner (cap 1).
- **Dovecote**: squat and round by the field: plinth, drum, a landing ledge under a band of
  flight holes, a steel-banded cornice, a slate cone, a little open lantern, gilt orb and spike.
- **Props colour** (`prodkit.props_layer`): EA's thatch, door and timber keep their colours (by
  colour and, for the planks, by EA's UV rectangles).

The crops, the peasant and his hoe keep their field. The chimney belongs to EA's roof meshes
(V2HIDE, V2): a cap on it from this mesh floated in the air during construction (it followed the
wall pieces up), so level 1 keeps EA's stack; level 3's cap is on V2 (`farm_level3`).

## Fit and status

- `GBFARM` 228 -> 3,674 triangles; footprint EA's; height +2.8 % (the porch and dovecote stay low); all
  checks pass. Construction and the world-builder model rebuilt along EA's pieces;
  the damaged, really damaged and rubble models have no body pieces of ours and stay EA's.
- EA's walls are single planes, so every face of the new pieces is kept (`prodkit.closed`).
- Own texture `GBFarH` (DXT5, EA's cut-outs kept).
- The thatch of EA's own roof (V2HIDE, not redesigned) follows `sagekit sheets`: if the faction
  recolour whitens it, the same props rule belongs in the style (reported).
