# Dwarven wall hub (`DwarvenWallHubSmall`)

Model `DBWallRmprtN`, redesigned mesh `DBWALLRMPRTN`, `Tier.STANDARD`, painted from the faction
atlas `DBFortress1` onto its own textures `DBFortressR.tga` / `DBFortressR_NRM.tga` (+ `_D`,
`_snow`, `_U` variants).

EA's hub is a squat hexagonal bastion (corners (+-25.49, 0), (+-12.39, +-22.5); walls to z 51.65,
a chamfer to a ring at 53.06, a slope to a platform at 56.6, a central hexagonal block to 63.2)
where wall segments meet from any side. It gets the fortress's tower crown, at the wall segments'
heights so the parapet line runs on through it.

## What changed (body, healthy)

- **Parapet:** a coping round the rim, flush with the walls (a bronze band on the wall's top edge,
  coping face to 56.6, bronze chamfer, top at 57.0) and the fortress's `chevron_parapet` on all six
  sides: the segments' coping top and chevron heights exactly.
- **Corner blocks:** a stepped block on each of the six corners (three tiers on the corner's
  two faces, 0.25 behind the coping face, from 52.9 to 65.4) with a gilded point at 68.0.
- **Crown:** a stepped hexagonal crown on the central block: a battered gold rune belt, a bronze
  step, a tier with the triangle frieze, a plain tier and a gilded point at 75.4.
- **Banners:** an Erebor-blue banner (7 x 22) on each of the four slanted faces, hung under EA's
  painted rune band (z 44.06..51.65) so the band runs on unbroken. The cloth goes to our
  house-colour model `DBHCWallRmprtN` (the player's colour), Draw tag `ModuleTag_Draw_HCWallHub`.
- **Paint:** the faction style.

Nothing stands out of the hexagon's two faces on the footprint (y = +-22.5) or past its corners;
the banners hang on the slanted faces, whose middles lie well inside it. Footprint unchanged,
height 63.2 -> 75.4 (+19.3 %, limit 20 %), 138 -> 1,316 triangles. `checks`: 44/44 pass.

Profile shared with the segments and part 2 (gates, postern, towers): see
[wall_segment/README.md](../wall_segment/README.md#the-wall-profile-shared-with-the-hub-and-part-2-gates-postern-towers).
Hub-specific: coping path = the hexagon moved in by 1.5 (`INSET`), coping face on the wall plane.

## Status (`python3 -m sagekit inventory dwarves/wall_hub`)

| Part | Healthy | Construction (`_A`) / damaged (`_D1`) / snow / stonework | Really damaged, collapsing (`_D2`, `_D3`) |
|---|---|---|---|
| body (`DBWallRmprtN`) | done, rendered, not installed | derived: our body on the variant sheets | old (EA's broken bodies, recoloured sheets) |
