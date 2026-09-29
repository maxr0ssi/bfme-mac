# Men market place (`GondorMarketPlace`, `ArnorMarketPlace`)

Model `GBMarket_SKN`, mesh `MARKET_STRUCTUR`, own texture `GBMarketPlacH.tga` (from
`GBMarketPlace.tga`, DXT5, EA's cut-outs kept). EA's market kept whole (platform, paving, arcaded
walls, campanile and bell, stalls, crates, baskets, the three awnings).

## What changed

- **Campanile crown**, the citadel's: a machicolated gallery with a sable star front and square
  merlons, four corbelled bartizans with slate spirelets; steel ribs up the dome, a lantern
  cupola, mast, gilt orb and spike; star bands on the belfry, White Tree roundels on the shaft.
- **Arcade**: a star frieze under the coping, a capped pinnacle over each pier, a keystone at
  every arch head, a White Tree roundel in the south spandrel.
- **West wall**: a pediment over the great arch (sable tympanum with the White Tree both sides,
  raking cornices, pinnacles).
- **Props** (`prodkit.py`, `props_layer`): crates, barrels, fruit, stalls and awnings keep
  EA's colours.
- **Banners**: two, on the arcade's end piers; cloth in `GBHCMarket`.

## Kept clear

- The arcade, where the vendor, townswoman, chicken and basket animate; the awnings, posts, torch.

## Status

Installed with the Men pack. 2,834 -> 10,022 triangles, height 73.0 -> 85.7 (+17.5 %), 114/114
checks. Construction and rubble are rebuilt, damaged is derived. Really damaged stays EA's: its
per-vertex layout differs from the template's.
