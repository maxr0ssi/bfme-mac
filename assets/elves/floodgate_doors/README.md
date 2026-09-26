# Elven floodgate doors (`ElvenFloodgateExpansion`, `ModuleTag_DrawDoors`)

Model `EBFFGate_DRCA` (the doors closed; `EBFFGate_DROA` opens them and carries the same leaves,
derived), redesigned mesh `EBFFGATE2`, `Tier.STANDARD`, painted from the faction sheet
`EBFortress.tga` onto its own textures `EBFortresG.tga` / `EBFortresG_NRM.tga` (DXT5: EA's cut-out
alpha kept; + `_D`, `_U` variants). The floodgate itself: [`floodgate`](../floodgate/README.md).

Five stone leaves round the floodgate's drum that close its niches and drop to let the flood out.
Each is a thin pointed slab carrying a raised lancet boss up its middle (a shallow V, its ridge
0.34 proud of its shoulders). The mesh hangs on a bone turned a quarter about z and 21.24 up, so
the recipe's numbers are in the mesh's own coordinates and the views in the model's.

## What changed (body, healthy)

Every boss is dressed as a jewelled door-post in the floodgate's vocabulary:

- **Gilt bead** up the ridge (0.6 to 23.4).
- **Three clasps** across the boss (at 3.4, 10.9 and 18.4, 2.2 high): knotwork (silver knots on
  sea-green enamel) between gilt edges, one prism on each facet of the V.
- **Gilt leaf** (6.3 x 2.8) on the boss's pointed top.

Nothing stands above EA's tip or more than 0.6 proud of EA's surface, so the leaves still close
into the niches and drop as EA's do (closed, they stay behind the drum's pier fronts).
`footprint_margin = 0.65`: the bosses' ridges are EA's bounding box, and the bead, clasps and
leaf stand up to 0.6 past it. No cloth (`house_tags = ()`): the leaves move, a house-colour model
would not; the floodgate's piers carry its banners.

Footprint as above, height 36.62 -> 36.62 (+0 %), 280 -> 1,400 triangles. `checks`: 58/58.

## Status (`python3 -m sagekit inventory elves/floodgate`, Draw module `ModuleTag_DrawDoors`)

| Part | Closed (`_DRCA`) | Opening (`_DROA`) / damaged / stonework | Construction (`_DRA`), rubble (`_DRD3`) |
|---|---|---|---|
| doors (`EBFFGate_DRCA`) | done, rendered, not installed | derived: our leaves, EA's animation | `_DRD3` ours (lifecycle); `_DRA` left to EA by the lifecycle checks (our faces' backs open to the sky as it rises) |
