# Elven fortress wall hub (`ElvenCastleWallHubExpansion`)

Model `EBEFWHub` (the round tower the fortress raises at a corner of its own when the wall-hub
expansion is bought), redesigned mesh `EBWALLRMPRTN01`, `Tier.STANDARD`, painted from the faction
sheet `EBFortress.tga` onto its own textures `EBFortresX.tga` / `EBFortresX_NRM.tga` (DXT5: EA's
cut-out alpha kept; + `_D`, `_snow`, `_U` variants).

EA's `EBEFWHub` draws the castle wall hub's body a second time: `EBWALLRMPRTN01` (374 triangles) is
the free-standing hub's `EBWALLRMPRTN` ([`wall_hub`](../wall_hub/README.md)) vertex for vertex,
beside a short wall run of its own out of the west side into the fortress (`EBWALLRMPRTN`, 148
triangles, EA's and untouched) and EA's dome (`SPHERE01`, on a bone at 47.09), which stays. As the
Dwarves did with theirs, the recipe subclasses the wall hub and takes its design whole:

- **Crown:** the walls' crown round the rim (filigree band, silver coping, lancet merlons), at the
  segments' heights, so a fortress corner and the free-standing hubs read as one wall.
- **Windows:** silver arch frames with sea-green reveals round the six lancet windows, a leaf
  banner in the player's colour in each. The windows at 144 and 216 degrees flank the wall run
  (it meets the hub within 14 degrees of the -x axis) and keep theirs.
- **Lanterns:** crystal lanterns on the rim's corners (none at 180, over the run).

The cloth goes to our house-colour model `EBHCEFWHub` (Draw tag
`ModuleTag_Draw_HCFortressWallHub`, from the style's `house_template`). `is_body` is the
building's own again (the wall hub leaves this expansion out of its own Draw modules).

The construction state draws `EBWallRmprtN_A`, the free-standing hub's own model. The wall hub
ships it carrying the same design, so this recipe neither derives it (`drawn_models` leaves it
out) nor rebuilds it (`lifecycle` skip), and no two recipes ship the same file.

Footprint unchanged (x +-24.09, y +-22.83), height 53.05 -> 60.60 (+14.2 %, limit 20 %),
374 -> 6,146 triangles. `checks`: 73/73.

Night lights: EA's model has no night meshes and the INI names none (`NightWindowName`).

## Status (`python3 -m sagekit inventory elves/fortress_wall_hub`)

| Part | Healthy | Damaged (`_D1`) / snow / stonework | Really damaged (`_D2`), rubble (`_D3`) | Construction |
|---|---|---|---|---|
| body (`EBEFWHub`) | built, rendered, not installed | derived: our body on the variant sheets | lifecycle: `_D2` ours; `_D3` left to EA by the lifecycle checks (`work/lifecycle.json`) | `EBWallRmprtN_A`, the wall hub's |
