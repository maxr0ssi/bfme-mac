# Men sentry tower (`GondorSentryTower`)

Model `GBBtlTwrM`, redesigned mesh `GBBTLTWRMINI01`, `Tier.STANDARD`, own sheet `GBBtlTwrH.tga`.
Ships in place. Also drawn, as an editor state, on the base-defence plot. The crown and dress are
the [keep](../keep/README.md)'s (`assets/men/keep/tower.py`) at the sentry's size.

## What changed

- A moulded lip under the frieze, a black band of silver stars, merlons with a pinnacle over each
  fold, and six bartizans on the pilasters.
- The dome is slate (hinted as tiles), with 12 steel ribs, a lantern, a gilt orb and a spike.
- String courses at 33.4 and 54.6 collar the pilasters. Plinth blocks stand at the pilasters'
  feet, and sills and pointed hoods frame the six windows on the folds.
- **Banners**: one, on face 312 under the sills; cloth in `GBHCBtlTwrM`.

## Kept clear

- EA's winged helm, painted on every face at z 55.4..61.4: no corbels under the frieze.
- The night windows (`WINDOW_N01`).

## Status

Installed with the Men pack. 486 -> 4,838 triangles, height 81.3 -> 96.0 (+18.1 %), 57/57 checks.
Every lifecycle state is derived (our body spliced in whole). Arnor's `GBBtlTwrM_D2` draws the crack
decal `GBMTDecal.tga`; ours is `GBMTDecaH.tga`, as long as EA's name (`variants()` in `building.py`).
