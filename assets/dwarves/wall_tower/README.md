# Dwarven wall tower (`DwarvenWallTowerSmall`)

Model `DBWallTwrN`, redesigned mesh `DBWALLTWRN`, `Tier.STANDARD`, painted from the faction atlas
`DBFortress1` onto its own textures `DBFortressV.tga` / `DBFortressV_NRM.tga` (+ `_D`, `_snow`, `_U`).
The model's second mesh `DBWALLN` (EA's wall piece through the tower, 128 triangles, not the wall
segment's model) is untouched and keeps EA's recoloured sheet.

`crown.py` holds the crown pieces the wall's towers and gates share (`step_pyramid` at any scale,
`ziggurat`, `chevron`, `band`); `wall_gate`, `wall_postern` and `wall_trebuchet` import it.

## What changed (body, healthy)

- **Crown:** the fortress's battered crown ring (dz -8.4) on the bronze shield panels, a stepped
  pyramid (0.7 scale, gilded point) on each corner post, a chevron merlon over the middle of
  each side. The archer notches under the ring and the arrow bones (`ARROW_01..08`, z 93.6) stay
  clear.
- **Roof:** a stepped roof over EA's stone pyramid: rune tier, bronze cornice, triangle-frieze
  tier, bronze cornice, stone tier, gilded point (the new top, z 124.4). Every tier stays outside
  the pyramid under it.
- **Shaft:** a rune belt at the walkway (z 49.4..53.4); a battered plinth with a string course on
  the two faces that look out of the wall (+-X); two Erebor-blue banners on each of those faces,
  either side of EA's carved window, hung free under the head's V-shaped corbel. The cloth is in
  the house-colour model `DBHCWallTwrN` (the player's colour).
- **Where the walls meet:** the wall runs along Y. The EA wall piece shows between the shaft
  (|y| 11.2) and the neighbouring segments (|y| 19). The wall segment's coping and chevron parapet
  run along it on both faces out to this mesh's footprint (|y| 18.03). The profile is imported
  from `wall_segment/building.py` (`COPING`, `COPING_X`, `chevron_parapet` at dz 0: coping top 57,
  chevrons to 63.6), so the two cannot drift apart. Only the last 1.0 before each neighbour is
  EA's piece without a parapet: the footprint check stops this mesh at 18.03.

Footprint unchanged, height 117.5 -> 124.4 (+5.9 %), 472 -> 1,670 triangles. `checks`: 51/51.

## Status

| Part | Healthy | Construction (`_A`) | Damaged (`_D1`) | Really damaged / collapse (`_D2`, `_D3`) | Snow / stonework |
|---|---|---|---|---|---|
| body (`DBWallTwrN`) | built, rendered, not installed | derived: our body | derived: our body, own `_D` sheet | old (EA's broken bodies) | own `_snow` / `_U` sheets |
