# Dwarven siege works (`DwarvenSiegeWorks`)

Model `DBForge`, mesh `DWARFBUILDING`, own texture `DBforgH.tga` (from `DBforge.tga`).
`Tier.STANDARD`. A forge hall with a great chimney behind a walled pit; the pit floor is the
two-leaf hatch (`DBForgeDr_SKN`, EA's) the engines rise through. The mesh hangs from bone
`DWARFBUILDING`, so the ground is at mesh z -49.1. `building.py` lists every measurement it uses.

## What changed

- **Chimney**: a battered crown ring with a hexagon frieze, stepped pyramids on the chamfers,
  stepped gables on the sides, corbels under the cap and a rune belt round the shaft.
- **Hall roofline**: a coping with chevron slabs and corbels along the hall front.
- **Pit**: chevron parapets on the outer edges of both walkways, rune friezes on their pit-side
  faces, a battered plinth under the +X wall; stepped hip caps bind the slab pairs at the back.
- **Exit**: two squat battered pylons flank the grille ramp.
- **Anvil**: EA's `ANVIL` (painted from the Elven forge's `EBForge.tga`) now samples `DBAnvil.tga`,
  the Dwarven recoloured copy (`shared_sheets` in [`style.py`](../style.py)).
- **Banners**: six (two on the chimney, two on the hall front, one on each exit pylon); cloth in
  `DBHCforge`.

## Kept clear

- The pit and the hatch leaves' swing (hinges at x -52.5 and -2.7, open to z -19.7), the exit ramp,
  the stairs, the anvil and the `SMOKE01` bone in the flue.

## Status

Installed with the Dwarven pack. 985 -> 3,225 triangles, height 81.50 -> 91.26 (+12.0 %),
138/138 checks, 2 night lights. Damaged derives the new body; construction, really damaged and
rubble are rebuilt along EA's pieces.
