# Men market place (`GondorMarketPlace`, `ArnorMarketPlace`)

Draft for review, not installed. Renders: `build/assets/men/market_place/renders/compare_*.png`.

## What changed

EA's market is kept whole (stepped platform, paving, arcaded walls, the campanile with its bell,
stalls, crates, baskets, the three cut-out awnings). Second pass (the lead: the first was too
close to EA) - the silhouette now changes:

- **Campanile crown**, the citadel's: a machicolated gallery at the shaft's top (two-step
  corbels, a slab with a sable front and gilt stars, a parapet of square merlons) and four
  corbelled bartizans with slit windows and slate spirelets on its corners; steel ribs up the
  dome, a lantern cupola, mast, gilt orb and spike; pinnacles on the cornice; a star band on
  each belfry face; White Tree roundels on the shaft (south, east).
- **Arcade**: a star frieze under the coping; over each pier a moulded cap and a pinnacle; a
  raised keystone at every arch head; a White Tree roundel in the spandrel of the south arches.
- **West wall**: over its great arch a pediment the wall's thickness deep (sable tympanum with
  the White Tree both sides, raking cornices, apex and end pinnacles), keystones on both faces.
- **Banners**: two house-colour banners on the arcade's end piers (cap 2).
- **Props colour** (`prodkit.props_layer`): crates, barrels, fruit, stalls and awnings keep EA's
  colours.

The vendor, the townswoman, the chicken and the basket animate inside the arcade; nothing new
stands there, and the awnings (DXT5 cut-outs), their posts and the torch keep their places.
Keystones start at the arch crowns: below them the arch's void shows their underside to the sky.

## Fit and status

- `MARKET_STRUCTUR` 2,834 -> 10,022 triangles; footprint EA's; height 73.0 -> 85.7 (+17.5 %, the
  campanile's spike); 114/114 checks.
- Lifecycle: construction and rubble rebuilt along EA's pieces, D1 derived; the really damaged
  model stays EA's (its per-vertex layout differs from the template's).
- Own texture `GBMarketPlacH` (DXT5, EA's cut-outs kept).
