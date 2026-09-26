# Elven watchtower (`ElvenWatchtowerExpansion`)

Model `EBFWTower`, redesigned mesh `EBFWTOWER`, `Tier.STANDARD`, painted from the faction sheet
`EBFortress.tga` onto its own textures `EBFortresP.tga` / `EBFortresP_NRM.tga` (DXT5: EA's cut-out
alpha kept; + `_D`, `_snow`, `_U` variants).

The tallest of the fortress's pad buildings: a square base with a pointed door recess on each
flank and a knotwork cornice, a tapering shaft, and a lantern head of four dormers under a gabled
scale roof whose ridges sweep up into horns round a steep pyramid (151.88). The eight `ARROW_*`
bones fire from the dormers at z 121.76: nothing new is near them. The arm back to the fortress
crosses the expansions' arch. EA's head, roof, horns and knotwork stay as they are.

## What changed (body, healthy)

- **Spire:** the pyramid runs on into a needle spire: a four-sided concave sweep in fish-scale
  slate from where the pyramid is 4 out (z 146), its eaves turned up at the corners like EA's
  horns (swan-neck eaves), a gilt lip and a gilt leaf finial (top 175.5).
- **Banners:** a leaf banner in the player's colour down each face of the shaft (3.6 x 24), hung
  from a gilt rod just under each dormer's ledge (104.75), clear of the tapering shaft. The cloth
  goes to our house-colour model `EBHCFWTower` (Draw tag `ModuleTag_Draw_HCWatchtower`, from the
  style's `house_template`).
- **Lanterns:** a Lórien crystal lantern on a small plinth at each corner of the cornice (top
  about 63).
- **Doors:** pointed silver frames with sea-green reveals round the two flank door recesses (the
  recesses untouched).
- **Arch:** the expansions' pointed silver frame round the arm's arch on both faces
  ([`floodgate/pad.py`](../floodgate/pad.py)).
- **Paint:** the faction style (moonstone, silver mouldings, gilt leaf, sea-green enamel, slate).

The spire's soffit disc lies inside EA's pyramid, out of sight, and is buried.

Footprint unchanged (x -42.54..12.73, y -18.42..18.44), height 151.88 -> 175.49 (+15.5 %, limit
20 %), 476 -> 3,350 triangles. `checks`: 92/92.

Night lights: EA's model has no night meshes and the INI names none (`NightWindowName`); the
dormers stay dark. Lighting them would need night meshes EA's object does not have.

## Status (`python3 -m sagekit inventory elves/watchtower`)

| Part | Healthy | Damaged / snow / stonework | Construction (`_A`), really damaged (`_D2`), rubble (`_D3`) |
|---|---|---|---|
| body (`EBFWTower`) | done, rendered, not installed | our body on the variant sheets | all three ours (lifecycle), rendered in `renders/lifecycle/` |
