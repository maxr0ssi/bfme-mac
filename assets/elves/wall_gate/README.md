# Elven wall gate (`ElvenCastleWallGate`)

Model `EBWallGateN_SKN`, mesh `EBWALLGATEN`, own texture `EBFortresD.tga` (from `EBFortress.tga`,
cut-out alpha kept). `Tier.STANDARD`. Crown from [`wall.py`](../wall_segment/wall.py). EA's gate
towers, warrior statues, torches and folding lattice doors stay whole.

## What changed

- **Bridge**: a slender bridge carries the wall crown and leaf crest over the passage; a pointed
  arch holds a crystal lantern above its middle.
- **Tower heads**: a filigree band and mithril coping, no merlons, crystal lanterns on the corners.
- **Banners**: two, on the towers' outward faces, same side; cloth in `EBHCWallGateN_S`.

## Kept clear

- The passage (|y| < 40.16) and the leaves' travel: nothing new below z 48.9.
- The towers' outer faces (|y| 58.68), where the segments meet.

## Status

Installed with the Elven pack. 128 -> 7,350 triangles, height 60.16 -> 71.39 (+18.7 %), 115/115
checks. Every damaged and collapse state derives the new body on EA's bones; EA's door animation
and fire effects stay.

## Known limits

- The Blender previews draw EA's torch effect cards as black rectangles, EA's side and ours alike.
