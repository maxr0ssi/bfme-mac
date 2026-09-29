# Elven battle tower (`ElvenBattleTower`)

Model `EBBbattleTwr`, mesh `EBBBATTLETWR`, own texture `EBBbattleTwH.tga` (from `EBBbattleTwr.tga`).
`Tier.STANDARD`. EA's measurements are in `building.py`.

## What changed

- **Spire**: EA's fish-scale cupola becomes the foot of a concave octagonal slate needle: swan-neck
  eaves, silver corner ribs, a gold collar, a gilt mast and leaf finial (z 155.1).
- **Foot**: a silver coping and a knotwork band between gilt beads round the three plain faces,
  stopping at the porch; crystal lanterns on gilt swan-neck brackets on the -y and -x faces.
- **Porch lanterns**: EA's `EBBBATTLETWRLE` draw an Elven copy of Gondor's night-window sheet.
- **Night**: five lights: three shaft lattice windows, the shaft face over the porch, the porch door.
- **Banners**: a long leaf pennant from the mast; cloth in `EBHCBbattleTwr`.

## Kept clear

- The head below z 103: EA's gables and horns, and the archer bones (3..14) in their windows.

## Status

Installed with the Elven pack. 2,631 -> 5,634 triangles, height 131.3 -> 155.1 (+18.2 %), 111/111
checks. Construction, really damaged and collapse are rebuilt along EA's pieces. Damaged and the
map-placed snow tower (`EBBbattleTwrS`, added through `drawn_models`) derive the new body.
