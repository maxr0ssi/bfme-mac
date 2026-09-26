# Elves fortress enchanted anvil (`ElvenCitadel`, `ModuleTag_DrawEnchantedAnvil`)

The smithy on the back of the ring: a work platform over the ring's cap (anvil, weapon rack, the
smith on the fortress's `POSITIONBONE`) and the forge chimney standing in the courtyard. Own texture
`EBFortresL.tga` (DXT5). EA's anvil (`EBFANVIL2`, painted from `EBForge.tga`) and the smith are untouched.

## What changed (body `EBFANVIL1`, healthy)

- **Chimney crown.** A moulded collar round the rim (open over the flue), six upright gilt leaf
  blades round it, and a starlight crystal rising from the flue (to z 114.65): the "enchanted" forge.
  At 4.2 each blade stays one piece (the kit builds a blade over the gilt tile's height, 4.3, in
  pieces, so a taller crown is free to design).
- **Banner poles.** Two gilt poles on the platform, at (-47, -5.5) and (-36, 11.5), clear of the
  anvil, the rack and the smith: a moulded foot, a leaf finial (z 96.4), a leaf banner (5.6 x 15,
  house colour) and a pennant (11) flying toward the platform's middle, inside the footprint.

## Numbers

- Footprint unchanged (x -50.26..-11.66, y -17.02..17.04); height 106.19 -> 114.65 (+8.0 %).
- Triangles 999 -> 2,445 (budget 5,000). Texel density median 11.1 px/unit.
- Checks: 90/90. House colour: 66 cloth faces -> `EBHCFortress`.
- Lifecycle: `EBFAnvil_A`, `_D2` and `_D3` carry the redesign.

## The alpha check

EA's own material draws `EBFANVIL1` with alpha test off (NormalMapped.fx, `AlphaTestEnable` 0), so
no hole of EA's sheet shows on it in the game, EA's or ours. The checks report the cut-out agreement
as information only for such a target (sagekit/blender/alpha.py): 49 of 60 points, the misses on
the edges of the leaf-emblem cut-out that EA paints the chimney top from. The recipe's emphasis on
that band, there only for the check, is gone.

## Night lights

No night meshes in EA's model; none declared.

## Status

| Part | Healthy | Construction | Damaged | Really damaged / rubble |
|---|---|---|---|---|
| smithy (`EBFAnvil`) | built, checks pass, **awaiting review** | ours (`_A`) | texture swap | ours (`_D2`, `_D3`) |
