# Elven floodgate doors (`ElvenFloodgateExpansion`, `ModuleTag_DrawDoors`)

Model `EBFFGate_DRCA`, mesh `EBFFGATE2`, own texture `EBFortresG.tga` (from `EBFortress.tga`, EA's
cut-out alpha kept). `Tier.STANDARD`. The leaves of the [floodgate](../floodgate/README.md).

EA's five pointed door leaves and their raised bosses stay whole.

## What changed

- **Leaves**: each gets a mithril ridge bead, one gilt clasp with silver edges and a gilt leaf on
  its pointed top.
- **Banners**: none on moving leaves.

## Kept clear

- The floodgate's pier fronts: the additions stay behind them when the doors close.

## Status

Installed with the Elven pack. 280 -> 940 triangles, height unchanged (36.62), 74/74 checks,
`footprint_margin = 0.65`. Opening derives the new leaves with EA's motion; construction and
rubble are rebuilt along EA's pieces. Construction (`EBFFGate_DRA`) holds the leaves lower than the
closed model, so its `match_offset` aligns the healthy reference before cutting; EA's animation
is untouched.
