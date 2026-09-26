# Elves green pasture fence (`ElvenGreenPasture`)

The paddock of the green pasture: mesh `FENCE` of `EBStable_SKN`. It is painted from
`EBStable_Alpha.tga`, a cut-out alpha sheet with no normal map (own texture `EBStable_AlphH.tga`,
DXT5). The recipe is chained on `elves/green_pasture` (`base`), so it is built after that one and
redesigns its finished model. The mesh hangs on a bone tilted 90 degrees, so
`world_space = True`.

## What changed (healthy)

- **Gate** (the paddock's far end, facing the camera): EA's round-headed stone gate becomes
  pointed:
  - a hood of dressed moonstone fills the spandrels between EA's round extrados and a pointed
    outline;
  - a silver moulding with an enamel soffit runs over the hood.

  The gate's face is the fence's footprint edge, so `footprint_margin = 0.6` lets the moulding
  stand 0.45 proud.
- **Lantern**: a crystal lantern hangs on a gilt rod from the gate's crown, above the passage
  (clear below z 25.6).
- **Posts**: each of the four corner posts gets a gilt collar and a leaf finial.
- EA's carved branch rails and their cut-out alpha stay as they are.

## Night, cloth

The fence is drawn at every upgrade level, so it is `always_shown` (sagekit/building.py): a
chained recipe that may carry cloth and night lights like a body (the Dwarven archery tower's,
walls' and obelisks' chained meshes are shown per level and still may not). At night the crown
lantern glows: a pane on its crystal's camera side and a small free glow card (10 across) round it
(`Light.glow`). No cloth is designed on the fence.

## Numbers

- **Footprint:** unchanged, apart from the 0.45 moulding on the gate's face.
- **Height:** 35.46 -> 41.28 (+16.4 %).
- **Triangles:** `FENCE` 1,332 -> 2,364.
- **Checks:** 159/159.
