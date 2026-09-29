# Elven wall end (`ElvenWallCliffCap`)

Model `EBWallNE`, mesh `EBWALLN`, own texture `EBFortresE.tga` (from `EBFortress.tga`, EA's cut-out
alpha kept). `Tier.STANDARD`. The crown profile is [`wall.py`](../wall_segment/wall.py), shared by
every Elven wall piece.

EA's cliff cap and all its window detail stay whole, including the faces below ground.

## What changed

- **Crown**: the segments' filigree band, mithril coping and leaf crest, carried to the cut end.
- **Lantern-house** on the end pier: ivory, lattice lancets, silver frames, a swept slate roof with
  a gilt finial.
- **Banners**: none; no extra frames on EA's wall windows.

## Kept clear

- The joint: the next segment still meets the same section.

## Status

Installed with the Elven pack. 1,227 -> 4,950 triangles, height 102.40 -> 120.35 (+17.5 %),
footprint unchanged, 79/79 checks. Construction and damaged derive the new body; really damaged
and collapse are rebuilt along EA's pieces and animations.
