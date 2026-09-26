# Elves green pasture (`ElvenGreenPasture`)

Model `EBStable_SKN` is skinned, with a separate skeleton `EBStable_SKL`. The redesigned mesh is
`EBBSTABLES`: the stable with its two wings, the pavilion and its dome. It gets its own texture,
`EBStablH.tga` / `EBStablH_NRM.tga` (DXT5: EA's cut-out alpha is kept), plus the variants. This
is a two-sheet build: EA's `EBStable.tga` for the old faces, and the fortress atlas for the new
ones.

The mesh hangs on a bone tilted 90 degrees, so `world_space = True`: every number is in model
axes. The paddock fence (`FENCE`, the same model) is the chained recipe
`elves/green_pasture_fence`.

Nothing else changes: the trees (`V1`, `V1A`), the level-2 crown (`V2`), the horses, Arwen, the
feed trough, the fence and the bones.

## What changed (body, healthy)

- **Crossing tower** (the silhouette): EA's low blue lattice dome is a Moorish dome, which the
  Elven standard rules out. It now disappears inside a crossing tower:
  - a sixteen-sided drum on the ring cornice, with lancet windows (lattice glass, silver frames)
    round its camera side between a silver base ring and a coping;
  - a slate spire, slightly concave, over the drum. Its eave turns up at every other corner
    (swan-neck eaves) over a gilt lip and a birch soffit;
  - a gilt leaf finial on the tip.

  The drum and the spire clear the dome everywhere (the numbers are in `building.py`).
- **Pavilion portal**: EA's round-headed gateway becomes a pointed portal:
  - a silver frame with an enamel reveal and a slight leaf tip (ogee 0.25);
  - a silver lintel at the springing;
  - a tympanum of gilt leaf-lancet tracery.

  The passage keeps its full width and 26.5 of its height.
- **Stalls**: the four stall arches on the paddock side get pointed silver frames with enamel
  reveals.
- **Cloth**: tall leaf banners on the portal's two flanking piers, and one on each of the two piers
  between the stalls. They move to `EBHCStable` (`house_tags`) and take the player's colour.
- **Wing ridges**: a crest of six gilt leaf finials.

The west side (away from the camera) keeps EA's shapes. So does the level-2 crown in the tree.

## Night

- The four stalls glow as doors (panes with halos).
- The portal glows as a door, a pane on the back of the gateway's recess.
- The drum's lancet windows glow (panes without halos).
- EA's night lanterns hung from the wings' end horns, outside the footprint (y +-58..65), with glow
  cards. Our geometry cannot reach there, but the glow can: EA's two cards (24 across, flat) stay
  where they were as free-hanging glows (`Light.glow`, sagekit/nightlights.py).

## Numbers

- **Footprint:** unchanged.
- **Height:** 58.30 -> 69.62 (+19.4 %, limit +20 %).
- **Triangles:** `EBBSTABLES` 1,116 -> 4,470 (budget 15,000).
- **Checks:** 163/163.

## Notes

- The `stalls` view is blocked by the paddock gate; `roof` and `close` show the paddock side.

## Status

| Part | Healthy | Construction / damaged / rubble | Snow |
|---|---|---|---|
| body (`EBStable_SKN`) | built, **awaiting review** | lifecycle step (`work/lifecycle.json`); `_D1` derived | painted |
| cloth (`EBHCStable`) | 4 leaf banners | | |
