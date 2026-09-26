# Dwarven statue (`DwarvenStatue`)

Model `DBStatue` is a bare-hierarchy model. The redesigned mesh is `STATUEHOLDER`, the block the
king stands on. It gets its own texture, `DBStatuH.tga`, plus the variants `DBStatuH_snow`,
`_d1` and `_d2`. This is a two-sheet build: EA's `dbstatue` sheet (which has no normal map) for
the old faces, and the fortress atlas for the new ones. The figure (`THORIN`,
`THORINKINGGEAR`, `RAVENBLADE`) and its `SHIELD` are untouched.

## What changed (body, healthy)

EA's octagonal base block fills the footprint up to z 9.7, and its flat faces are the footprint's
edges, so it cannot be wrapped. The new parts are:

- **Corner buttresses.** Each of the block's four chamfered corners is filled by a buttress:
  plinth, bronze step, a gold rune belt between bronze bands, and a corbel. This turns the
  octagon into a square with corner towers. EA's chamfer plaques are buried inside the
  buttresses.
- **Cornice and walk-top.** Over the block sits a hexagon-chain cornice with a bronze coping. A
  walk-top slopes in from it over EA's cornice to the upper die.
- **Corner piers.** Four piers stand on the buttresses, each with a rune belt and a bronze
  capital:
  - the front two carry gold brazier bowls with gilded flame points (to z 28.6);
  - the back two become bronze banner poles with gilded points (to z 30.8). Each flies an
    Erebor-blue banner beside the die's flank. The banners stay clear of the flank's gold hexagon
    niche and of the king's cloak.
- **Top cornice.** Under the king's feet, a cornice (bronze corbel, gold rune belt, bronze
  coping) runs round EA's square cap. Its front stops behind the die's face, where the shield
  hangs.
- **Banner cloth.** It moves to `DBHCStatue` (`house_tags`) and takes the player's colour.

The four gold hexagon emblems in the upper die's niches stay in view.

## Numbers

- **Footprint:** unchanged.
- **Height of `STATUEHOLDER`:** 23.6 -> 30.9 (+30.9 %). `max_z_growth` is 0.35 because the
  figure stands to z 57.3, so the holder does not set the model's height.
- **Triangles:** 254 -> 1526 (budget 4,000).
- **Texel density:** median 26.3 px/unit.
- **Checks:** 72/72.

## Status

| Part | Healthy | Construction | Damaged / really damaged | Rubble | Snow | LOD M/L |
|---|---|---|---|---|---|---|
| body (`DBStatue`) | built, checks pass, **awaiting review** | ours (`DBStatue_A` carries the new body) | ours (`DBStatue_D1`, `_D2`, in `DBStatuH_d1` / `_d2`) | old (`DBStatue_D3` is a skinned rubble mesh) | `DBStatuH_snow` painted | old |
| banner (`DBHCStatue`) | our 2 banners' cloth added | | | | | |

## Framework note (worked around here)

In `sagekit/blender/checks_suite.py`, the derived-model check builds its "want" list with
`own.get(t, ...)`, and that lookup is case-sensitive. The model names the sheet `dbstatue.tga`, so
with `sheet = "DBStatue.tga"` the `DBStatue_A` check wanted EA's `dbstatue.tga` even though the
file correctly carried ours. The recipe spells the sheet in lower case, as the model does, and
pins the own name (`own_textures = {"dbstatue.tga": "DBStatuH.tga"}`).

## Note for review

When the house step is installed, EA's own house banner in `DBHCStatue` shows in skirmish too.
The renders show it as a small blue flag at the king's side.
