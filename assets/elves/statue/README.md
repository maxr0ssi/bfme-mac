# Elven statue (`ElvenStatue`)

Model `EBStatue`, mesh `EBSTATUE01` (the holder), own texture `ebstatueholdeH.tga` (from
`ebstatueholder.tga`; EA's 32-bit normal map keeps its depth). `Tier.STANDARD`. The warrior
(`OBJECT12`) stays EA's, byte for byte. EA's measurements are in `building.py`.

## What changed

- **Slope**: a silver coping on its top edge.
- **Lower die**: a knotwork band (silver on sea-green) between gilt beads, a gilt bead on the step.
- **Upper die**: tall lancet niches on six faces: gold leaf tracery on slate in a silver pointed
  frame, a gilt leaf at the tip.
- **Cornice**: a corbel, a sea-green frieze and a silver coping, top z 26.05, under the feet (26.41).
- **Lantern columns** in the footprint's four corners: fluted, gilt leaf capital, crystal lantern.
- **Banners**: two, on the upper die's other two faces; cloth in `EBHCStatue`.

## Status

Installed with the Elven pack. 112 -> 5,506 triangles, holder height 27.03 -> 31.39 (+16.1 %; the
figure stands to 90.4), 60/60 checks. Damaged, really damaged and rubble derive the new holder.

## Known limits

- Construction stays EA's: our holder shows open backs while it rises
  (`build/assets/elves/statue/work/lifecycle.json`).
