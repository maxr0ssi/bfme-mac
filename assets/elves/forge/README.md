# Elves forge (`EregionForge`)

Model `EBForge_SKN` is skinned, with a separate skeleton `EBForge_SKL`. The redesigned mesh is
`BOX01`: the furnace tower, the arched hearth, the planter and the weapon rack, and also the
mallorn's trunk and branches. It gets its own texture, `ebforgH.tga` / `ebforgH_NRM.tga` (DXT5:
EA's cut-out alpha is kept), plus the snow variant `ebforgH_Snow`. This is a two-sheet build: EA's
`ebforge.tga` for the old faces, and the fortress atlas `EBFortress.tga` for the new ones.

`ebforge.tga` is also drawn by the Dwarven siege works' anvil. The Dwarves ship their own copy
(`DBAnvil.tga`, `shared_sheets`), so this recipe owns the sheet and pins its own name `ebforgH`.

Nothing else changes: the leaves (`LEAVES`), the upgrade crowns (`V2`, `V2A`, `V2B`), the smith
and his gear, the lance and shield, and the bones. That includes `FXFIRE` in the hearth and
`FXSMOKE` under the flue.

## What changed (body, healthy)

- **Chimney** (seen over the canopy from the RTS camera):
  - a coronet round the open flue: six gilt leaf blades facing out, with six smaller blades
    leaning out between them;
  - six small crystal lanterns on the rim;
  - a leaf banner on each of its two camera-side faces, under the band;
  - a knotwork band (silver knots on sea-green enamel, gilt beads) under the cap.

  The flue stays open, so the smoke still rises clear.
- **Furnace shaft**: a lancet window on each of its six faces (EA's lattice glass on a slab, a
  pointed silver frame with an enamel reveal, a small gilt leaf, a silver sill), and a knotwork
  band under the flare.
- **Hearth**:
  - a silver barge board with an enamel soffit along its pointed gable, with a leaf finial on the
    apex;
  - knotwork bands along both side walls;
  - two leaf banners on the camera-side wall.

  Nothing new stands in front of the hearth below z 17, where the smith works.
- **Planter**: three crystal lanterns on its front rim.
- **Mallorn**: three crystal lanterns on gilt rods, hung where EA hangs its night lanterns.
- **Weapon rack**: a gilt pole with a leaf finial over each post, each flying a leaf pennant.
- **Paint**: the faction style. `sheet_atlas` adds mask hints for EA's sheet, so that:
  - the mallorn's bark stays bark (the rock ramp: silver-grey mallorn bark), not stone;
  - the anvil's rusty plate becomes dark steel, not stone flecked with gold;
  - the copper knotwork band becomes silver knots on enamel.
- **Cloth**: the banners and pennants move to `EBHCForge` (`house_tags`) and take the player's
  colour.

## Night

Starlight replaces EA's warm lanterns. These glow:

- our three tree lanterns, where EA's night lanterns hung, each in a free glow card like EA's (24
  across, flat, `Light.glow`) where EA's glow cards were;
- the planter's and the chimney's crystals;
- the back wall of the hearth passage;
- the six shaft windows.

EA's own night lanterns are night-only meshes (`N_WINDOW`) hanging in the tree. The night step
replaces them with ours (sagekit/nightlights.py).

## Numbers

- **Footprint:** unchanged.
- **Height:** unchanged (the coronet stays under the tree's top).
- **Triangles:** `BOX01` 1,122 -> 6,844 (budget 15,000).
- **Checks:** 114/114.

## Status

| Part | Healthy | Construction | Damaged / really damaged / rubble | Snow |
|---|---|---|---|---|
| body (`EBForge_SKN`) | built, checks pass, **awaiting review** | EA's (the lifecycle step leaves `EBForge_A` to EA: its FORGE5 mesh's vertex layout differs) | EA's (`D1`-`D3` share no body pieces with ours) | `ebforgH_Snow` painted |
| cloth (`EBHCForge`) | 4 banners, 2 pennants | | | |

## Notes

- EA's `ebforge_nrm.tga` is a 32-bit TGA; sagekit keeps its depth (sagekit/paint/imageio.py).
- The `chimney` view looks from behind (azimuth 160), because the tree hides the chimney from the
  front.
