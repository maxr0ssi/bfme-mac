# Elven floodgate (`ElvenFloodgateExpansion`)

Model `EBFFGate`, mesh `EBFFGATE1`, own texture `EBFortresF.tga` (from `EBFortress.tga`, EA's cut-out
alpha kept). `Tier.STANDARD`. The moving leaves are [`floodgate_doors`](../floodgate_doors/README.md);
[`pad.py`](pad.py) holds the arch and coping helpers the expansions share.

EA's horses, gold swirls, pointed bays, water and ground ring stay whole.

## What changed

- **Basin**: a mithril coping and a silver-railed ivory balustrade ring it; crystal lanterns stand
  on newels over the buttress piers.
- **Aqueduct**: a matching coping and pointed silver arch frames.
- **Banners**: two, on the front piers beside the flood; cloth in `EBHCFFGate`.

## Status

Installed with the Elven pack. 1,645 -> 8,053 triangles, height unchanged (80.39), 113/113 checks.
`footprint_margin = 0.9` for EA's banner rods; `facet_islands` unwraps the horses without folds.
Damaged, snow and stonework variants carry the new body. Construction, really damaged and rubble
are rebuilt along EA's pieces; construction matches only EA's exact healthy surface
(`surface = 0.05`), so the paired internal caps stay break faces.
