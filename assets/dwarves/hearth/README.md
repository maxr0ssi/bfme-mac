# Dwarven hearth (`DwarvenHearth`)

Model `DBHearth`, mesh `DWARFHEARTH`, own texture `DBHeartX.tga` (from `DBHearth.tga`, no normal
map); new faces sample the faction atlas. `Tier.STANDARD`. EA's measurements are in `building.py`.

## What changed

- **Gantry**: a rune-banded cornice on the beam, a triangle-frieze step and a stepped gable
  (the new top, z 40.0); stepped shoulders down both slopes; a bronze-tipped finial over each capital.
- **Fire ring**: a bronze coping on each side with a small stepped parapet at its middle; stepped
  pedestals round the pillar feet; stepped pyramids on the two free corners.
- **Plate**: a squat stepped pyramid on each diamond pad.
- **Banners**: two poles on the free corners (+,+) and (-,-); cloth in `DBHCHearth`.

## Kept clear

- The fire bed, open to the camera; EA's house banner at the (+X, -Y) corner.

## Status

Installed with the Dwarven pack. 660 -> 1,500 triangles, height 34.4 -> 40.0 (+16.2 %), footprint
unchanged, 74/74 checks. Construction and damaged derive the new body; really damaged and rubble
are rebuilt along EA's pieces. No night lights (EA's model has no night meshes).
