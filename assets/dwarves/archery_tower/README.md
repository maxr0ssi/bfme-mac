# Dwarven archery range, level 3 tower (`V2` of `DBArchRnge_SKN`)

The storey EA shows at `Upgrade_StructureLevel3` (`ModuleTag_ShowPillars`: `V1 V1A V2`), redesigned
on the archery range's finished model: `base = "dwarves/archery_range"`. The building takes
`build/assets/dwarves/archery_range/out/.../dbarchrnge_skn.w3d` as its source, redesigns `V2`,
and ships the whole model in place of the range's. Rebuild this after the archery range, and
`dwarves/archery_walls` (based on this one) after this.

Own texture: `DBArchRngT.tga` (`dbarchrngt.dds`, `dbarchrngt_nrm.tga`, snow `dbarchrngT_snow`).
It is a two-sheet build like the range: EA's `dbarchrnge.tga` for the old faces, the fortress atlas
for the new ones. Tier STANDARD.

## What changed

EA's V2 was a timber storey on four tall legs, with gothic windows, a shingle pyramid spire and
horned eaves. The redesign matches the stone range below it and the fortress towers.

- **Piers:** each timber leg rises out of the range's post bastion (z 61.4) inside a stone pier.
  The pier has a bronze foot, a rune belt at the open loggia (z 70–72.6) and a second rune belt
  at the arrow slits (z 97–100). The piers run up into the crown.
- **Storey course:** under the storey, spanning the piers over the loggia. It has a stepped
  soffit, a bronze fillet, the hexagon frieze and a bronze coping. It starts at z 76.2, above the
  range's crown finials (at most 71.8) and the bow prop.
- **Storey walls:** stone over EA's timber walls. There is a pointed arrow slit at each pair of
  arrow bones: `ARROW_01..12`, the `WeaponLaunchBone` of the level-3 arrows, at z 96–100 on the
  east, north and south faces. Each slit has a bronze reveal and a proud stepped frame (sill,
  jambs, pointed hood). EA's dark window shows through each slit. An Erebor-blue banner hangs
  between the slits on each of those three faces. The west face has the ladder and stays plain.
- **Crown:** a corbelled cornice (bronze band, hexagon frieze) carries the crown ring. The ring
  overhangs east and west, where EA's eave horns reach x 12 and 50.2 inside it. It has a gold
  rune belt on blue enamel and a sloped bronze coping.
- **On the crown:** a fortress step pyramid on each corner. Mid-side is the range's own crown
  gable at this scale: bronze band, triangle-frieze tier, stone point, gilded finial.
- **Spire:** six stone tiers step in with EA's pyramid (base z 110.37, apex 136.68); each tier's
  foot is 0.45 outside it, so the shingles are inside the stone. Two tiers carry the triangle
  and hexagon friezes. On top are a bronze collar and a gilded point to z 146.5.

## What stays usable

- The arrow bones: the slits frame them, and nothing new stands in front of them.
- V2's ladder (y 40.6–49.7, from the gallery deck to z 95): the course's west face is at x 17.9,
  where the ladder meets the wall. The NW pier does not grow toward the ladder.
- The loggia on the tower top: the props and the range's crown gables stay clear.
- The bones and the hierarchy.

Footprint = V2's (x 6.61–50.25, y 26.02–54.85). Height +8.9 % (limit 20 %). V2 goes from 576 to
about 2,200 triangles (budget 15,000).

## House colour

`house_tags = ()`: the banners' cloth stays in V2, in the palette's blue. The house-colour model
(`DBHCArchRnge`) is drawn at every level. Cloth moved into it would hang in the air at levels 1
and 2, when V2 is hidden.

## Status

| Part | Healthy | Snow | Other states |
|---|---|---|---|
| `V2` (level 3) | built, checks pass, **awaiting review** | variant `DBArchRngT_snow` painted | EA's (damaged models carry no V2) |

The renders show the whole model at level 3. The range's own body (`ARCHERYRANGE`) renders grey
in them: the render step looks up the model's other textures in the game's archives and in the
recoloured sheets, and the range's own `dbarchrngH` is in neither. In game it is textured.
