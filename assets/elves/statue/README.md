# Elven statue (`ElvenStatue`, `elvenstatue.ini`)

Model `EBStatue` has two meshes on one bone:

- `OBJECT12`: the warrior (9,828 triangles, `ebstatue.tga`). It stays EA's, byte for byte.
- `EBSTATUE01`: the holder he stands on (112 triangles, `ebstatueholder.tga` + `_nrm`).

The holder is the redesigned mesh. `ebstatueholder` belongs to this building alone: no other
faction, map or civilian object draws it (`sagekit owners elves`). It gets its own texture,
`ebstatueholdeH.tga` (+ `_nrm`, `_d1`, `_d2`). New faces are mapped onto the faction atlas.
`Tier.STANDARD`.

## The original (measured, model coordinates)

- **Holder:** a regular octagon round (-0.25, -1.55), corners at -4 + 45k degrees, so the
  footprint box touches four corners near the axes. Its circumradius:
  - 11.7 up to z 2.34, sloping in to 10.6 at 3.51;
  - the lower die battered to 9.56 at 12.54, then a step to 9.2 at 13.19;
  - the upper die battered to 8.5 at 26.07, and a cap to 8.1 at 26.96.
- **Figure:** his feet sink into the cap down to z 26.41.

## What changed (body, healthy)

- **Slope:** a silver coping on the slope's top edge.
- **Lower die:** a knotwork band (silver knots on sea-green enamel) between gilt beads, under the
  step, and a gilt bead on the step itself.
- **Upper die:**
  - six faces hold tall lancet niches: gold leaf tracery on slate (the atlas's lancet panel) in a
    silver pointed frame (leaf-tip ogee 0.2) with a sea-green reveal, a gilt leaf at the tip and a
    sill;
  - the other two faces carry leaf banners, which go to `EBHCStatue` (house colour).
- **Cornice:** under the feet, a corbel, a sea-green frieze and a silver coping. Its top is 26.05,
  under the feet.
- **Lantern columns:** in the footprint's four corner squares, outside the octagon. Each has a
  moulded pedestal as high as EA's base slab, a slender fluted column with a gilt leaf capital,
  and a crystal lantern (gilt cup, cap and leaf finial).

Earlier pass measurements (retained for history; current build evidence is in `work/logs/checks.log`):

Footprint unchanged. Holder height 27.03 -> 31.39 (+16.1 %, limit 20 %; the figure stands to
90.4). Triangles 112 -> 4,492 (`tri_budget` 6,000). Texel density median 24.4 px/unit.
`checks`: 60/60.

## Status

The latest ivory, mithril and mallorn-gold pass is built and passes the offline checks;
review is still required before installation. Lifecycle fallbacks below remain intentional.

| Part | Healthy | Construction | Damaged / really damaged | Rubble | Snow | LOD M/L |
|---|---|---|---|---|---|---|
| body (`EBStatue`) | built, checks pass, **awaiting review** | EA's (`EBStatue_A`: the lifecycle gate left it to EA, see below) | derived (`EBStatue_D1`, `_D2`, on `ebstatueholdeH_d1` / `_d2`) | derived (`EBStatue_D3`) | EA swaps only the figure's sheet | old |
| banner (`EBHCStatue`) | our two banners' cloth added (shown after `sagekit house elves`) | | | | | |

## Notes

- **32-bit normal map.** EA's `ebstatueholder_nrm.tga` is a 32-bit TGA; sagekit keeps its depth
  (sagekit/paint/imageio.py).
- **Construction.** `EBStatue_A` stays EA's. Rest-pose matching is already selected; a bounded
  probe with tighter surface classification still failed the unchanged open-back gate, so no
  geometry is forced through. The current failure details are in `work/lifecycle.json`.
  Earlier-pass evidence, retained for history: the gate found 11 % of our area open to the sky
  at frame 35, EA's 0 %.
- **Night.** The model has no night meshes (`N_*`), so no lights are declared. The crystal
  lanterns glow only if a night mesh is added (a framework question).
