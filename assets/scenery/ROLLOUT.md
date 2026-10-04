# Map scenery: the audit and the rollout

EA's civilian buildings, ruins, set pieces and props: 1,938 objects in the civilian and obsolete
folders (townsfolk and animals left out), 1,078 of them placed by a map. Nobody builds them, so the
work is a recolour per sheet, in each culture's palette, with EA's geometry. How it works:
[docs/ART.md](../../docs/ART.md#map-scenery-civilian-buildings-and-set-pieces).

## The audit (2026-10-04)

`python3 -m sagekit scenery audit`, ranked by the multiplayer maps placing a culture's objects.
"Recoloured" counts the sheets this pack ships; the rest are normal maps, effect and unit sheets,
sheets a faction draws or one of our packs ships already, and sheets on no map.

| Rank | Culture | Palette | Objects (placed) | MP maps | Sheets | Recoloured |
|---|---|---|---|---|---|---|
| 1 | Common props and Dunland | Wilderland | 272 (186) | 222 | 142 | 54 |
| 2 | Gondor, Osgiliath, Ithilien (the pilot) | Men, StoneRecolour | 758 (267) | 165 | 114 | 12 |
| 3 | Rohan and Helm's Deep | Wilderland | 126 (87) | 92 | 96 | 35 |
| 4 | Dale and Lake-town | Wilderland | 61 (61) | 88 | 47 | 18 |
| 5 | The Shire, Bree, the villages | Wilderland | 29 (29) | 79 | 38 | 21 |
| 6 | Elven ruins and havens | Elves | 133 (119) | 69 | 52 | 13 |
| 7 | Mordor, Morgul, Dol Guldur, Harad, Rhun | Mordor | 130 (86) | 61 | 112 | 30 |
| 8 | Erebor, Blue Mountains, Iron Hills | Dwarves | 139 (102) | 50 | 63 | 26 |
| 9 | Arnor's ruins | Men | 73 (70) | 47 | 52 | 18 |
| 10 | Moria (Khazad-dum's halls) | Dwarves | 178 (40) | 36 | 98 | 39 |
| 11 | Angmar, Ettenmoors | Angmar | 33 (26) | 23 | 32 | 9 |
| 12 | Isengard | Isengard | 6 (5) | 3 | 6 | 0 |

275 sheets in all, at EA's sizes (memory as EA's). Gondor's own buildings mostly draw the Men's
sheets, which the Men pack recolours already (Amon Hen's ruins on 74 maps among them): this pack adds
Osgiliath's family (`osgilall` and its damaged JPGs and snow, the bridges, plots and ruins).

## Decisions

- **Osgiliath (pilot)**: Gondor's white stone through the Men's stone curve; the lilac and blue bricks
  are stone at any chroma, the brown earth on the ruins stays EA's (`OSGILIATH` in `cultures.py`).
  The Men's own sheet layers left blue specks and red blotches on it (their masks read the lilac
  cast as enamel and cloth), so the scenery has its own layer, `StoneRecolour`.
- **Rohan, Dunland**: Wilderland, not a faction's stone. Rohan's timber and thatch bleached white
  under Gondor's stone; the Dunlendings' hide huts went black under Isengard's.
- **Moria**: the Dwarves' palette. Khazad-dum's halls are dwarven stonework; the Goblins' near-black
  stone turned them, the bones and the buckets black.
- **Common props** (carts, barrels, sacks, fences in `civilianprop.ini`) are everyone's: Wilderland,
  whatever map they were made for.
- Skipped from the research: the castle and camp templates (on no shipped map), Barad-dur (0 maps),
  and every faction-folder object but Osgiliath's falling tower (`ALSO`), a map prop.

## State

Staged, not installed: `build/assets/scenery/_install/!!!!!!!!!!!sagekit-scenery.big` (275 sheets).
Review: `build/assets/_review_finish/scenery/<culture>.jpg` and `map_map_mp_south_ithilien.jpg`.

    python3 -m sagekit scenery sheets              # paint (only what changed)
    python3 -m sagekit install scenery --check     # stage
    python3 -m sagekit install scenery             # install
    python3 -m sagekit revert scenery              # take it out

Textures only: no INI, no models, no asset.dat change, no upgrades. Everyone in a LAN game should
have the same packs all the same (a sheet changes how a map looks, not the simulation).
