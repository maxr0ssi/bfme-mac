# Dwarven wall end (`DwarvenWallCliffCap`)

Model `DBWallNE`, mesh `DBWALLNE`, own texture `DBFortressN.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.STANDARD`. The mesh hangs under a rotated bone, so the recipe works in
world axes (`world_space = True`); all numbers here are world.

EA's cliff cap is two wall-segment bays end to end: bay A (y -19..19) meets the next segment at
y +19, bay B (y -57..-19) runs into the cliff and ends in a plain cut at y -57.

## What changed

- **Wall profile**: [`wall_segment`](../wall_segment/README.md)'s constants unchanged (coping,
  chevron parapet 56.6..63.6, corbels, plinth in each bay).
- **Cut end** (y -57): a stepped terminal block across the walkway over both parapets, with the
  triangle frieze and a gilded point at z 72.4.
- **Banners**: eight, beside each niche (four per face); cloth in `DBHCWallNE`.

## Kept clear

- The joint at y +19: only the coping and the chevron slabs reach it, at the segment's exact
  heights, so the parapet runs straight on into the neighbour.
- The cut at y -57: the coping and bay B's plinth end 0.1 short of it.

## Status

Installed with the Dwarven pack. 296 -> 1,480 triangles, height 106.00 -> 125.39 (+18.3 %),
79/79 checks. Construction and damaged derive the new body; really damaged and collapse are
rebuilt along EA's pieces.
