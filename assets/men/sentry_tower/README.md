# Men sentry tower (`GondorSentryTower`)

Model `GBBtlTwrM`, redesigned mesh `GBBTLTWRMINI01`, `Tier.STANDARD`, own sheet `GBBtlTwrH.tga`.
Ships in place. Also drawn, as an editor state, on the base-defence plot. The crown and dress are
the keep's (`assets/men/keep/tower.py`) at the sentry's size.

## What changed

- A moulded lip under the frieze, a black band of silver stars, merlons with a pinnacle over each
  fold, and six bartizans on the pilasters.
- The dome is slate (hinted as tiles), with 12 steel ribs, a lantern, a gilt orb and a spike.
- String courses at 33.4 and 54.6 collar the pilasters. Plinth blocks stand at the pilasters'
  feet, and sills and pointed hoods frame the six windows on the folds (`WINDOW_N01`, kept clear).
- 1 house-colour banner (cap 1), on face 312 under the sills.
- No corbels under the frieze: EA painted a winged helm on every face at z 55.4..61.4, and it
  stays in view.

## Status

- [x] checks 57/57 (footprint inside, height 81.3 -> 96.0, +18.1 %; 486 -> 5462 triangles)
- [x] lifecycle: every state derived (our body spliced in whole)
- [x] Arnor's `GBBtlTwrM_D2` draws the crack decal `GBMTDecal.tga`. Our variant of it is named
      `GBMTDecaH.tga` (as long as EA's name, as W3D needs). The taxonomy's
      `GBBtlTwrHMTDecal.tga` broke the in-place rename. This is a framework gap (`variants()`
      override in the recipe).
- [ ] banner shows after `sagekit house men`; Max's review
