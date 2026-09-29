# Elven fortress enchanted anvil (`ElvenCitadel`, `ModuleTag_DrawEnchantedAnvil`)

Model `EBFAnvil`, mesh `EBFANVIL1`, own texture `EBFortresL.tga` (from `EBFortress.tga`).
`Tier.STANDARD`. The smithy on the back of the [fortress](../fortress/README.md)'s ring: a work
platform and the forge chimney. EA's body, anvil (`EBFANVIL2`) and smith are kept.

## What changed

- **Coping**: the citadel's ring coping continues round the platform's parapet (top z 59.0).
- **Ring lantern** on the parapet's front, the one the citadel leaves out on its face 180.
- **Chimney crown**: a silver collar, six gilt leaf blades and a starlight crystal rising from the
  flue (z 114.65).
- **Banners**: one, on a gilt pole at (-47, -5.5) facing the courtyard; cloth in `EBHCFAnvil`.

## Kept clear

- The anvil, the weapon rack (x -44..-32, y -16..-4) and the smith's `POSITIONBONE`.

## Status

Installed with the Elven pack. 999 -> 2,505 triangles, height 106.2 -> 114.7 (+8.0 %), 90/90 checks,
`footprint_margin = 0.8` (the coping and lantern pass the parapet by 0.78). Construction, really
damaged and rubble are rebuilt along EA's pieces; damaged is a texture swap.

## Known limits

- EA's `EBFAnvil_D2AN` flings `BONE_3` and `BONE_2` off-scene (frames 5, 32); kept as EA made it.
