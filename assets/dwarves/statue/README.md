# Dwarven statue (`DwarvenStatue`)

Model `DBStatue`, mesh `STATUEHOLDER` (the block the king stands on), own texture `DBStatuH.tga`
(from `dbstatue.tga`, no normal map). `Tier.STANDARD`. The figure (`THORIN`, `THORINKINGGEAR`,
`RAVENBLADE`) and its `SHIELD` are EA's.

## What changed

- **Corner buttresses**: fill EA's four chamfered corners (plinth, bronze step, gold rune belt,
  corbel), so the octagon reads as a square with corner towers.
- **Cornice and walk-top**: a hexagon-chain cornice with bronze coping over the block, sloping in
  to the upper die.
- **Corner piers**: the front two carry gold brazier bowls (to z 28.6), the back two are banner
  poles (to z 30.8).
- **Top cornice**: bronze corbel, gold rune belt and coping round EA's cap under the king's feet.
- **Banners**: two, on the back piers; cloth in `DBHCStatue`.

## Kept clear

- The shield on the die's front face; the gold hexagon emblems in the die's niches; the king's cloak.

## Status

Installed with the Dwarven pack. 254 -> 1,526 triangles, height 23.61 -> 30.90 (+30.9 %,
`max_z_growth = 0.35`: the figure, to z 57.3, sets the model's height), 96/96 checks.
Construction, damaged and really damaged derive the new body; rubble is rebuilt along EA's pieces.

## Known limits

- EA's own house flag in `DBHCStatue` now shows in skirmish too, as a small flag at the king's side.
