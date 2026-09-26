# Dwarven archery range (`DwarvenArcheryRange`)

Model `DBArchRnge_SKN` (a skinned model: separate skeleton `DBArchRnge_SKL`, animated archer and
smith). The redesigned mesh is `ARCHERYRANGE`, which holds the hall, the tower base, the gallery and
the four tower posts. It gets its own texture, `dbarchrngh.dds` / `dbarchrngh_nrm.tga` (two-sheet
build: EA's sheet for the old faces, the fortress atlas for the new ones). Nothing else changes:
the archer, the props, `ARCHERYBASE`, the upgrade meshes `V1` / `V1A` / `V2` and the bones.

## Second pass (why): the first version "felt a bit bland"

In the first pass the timber hall still dominated and read as EA's wooden shed. The added stone
was thin trim, not mass. There was little gold, and the tower top was modest. The second pass
rebuilds the hall as Dwarven masonry and gives the tower a crown like the fortress's.

## What changed (body, healthy)

- **Stepped stone roof:** EA's shingle roof is now inside one stepped stone solid. At the bottom
  is an eave course with a gold rune band that runs all round the hall. Above it, five tiers step
  in with EA's roof planes, so each inner corner sits on the old roof. On top is a ridge block
  with the hexagon chain, crowned by four chevrons with gilded tips. The treads are rings, so no
  face is hidden under the tier above; this keeps texel density at the fortress's level.
- **South gable:** the ends of the tiers form a crow-stepped stone gable (rune, triangle and
  hexagon bands). It is flush with the footprint, and two corner turrets stand at its feet. Each
  turret is battered, with a rune belt, a bronze cap and a gilded point.
- **Hall walls:** a battered stone plinth with a bronze string course runs under the windows.
  Stone pilasters with bronze capitals stand between the windows. Under the eave is a corbelled
  cornice with the hexagon frieze.
- **East gatehouse:** the stepped pointed portal keeps its rune tympanum, now with a rune lintel
  band. Two battered pylons flank it, each with a rune belt, a bronze cap and a gilded point. Over
  it is a stepped crown: bronze cornice, rune tier, triangle tier, stone tier, then a gable with
  the triangle frieze and a gilded finial. The crown rises out of the roof. The door opening
  stays clear.
- **Tower crown:** the corbelled hexagon cornice is kept. Above it is a battered crown ring with
  a gold rune belt and bronze coping. On the east, north and south sides is a stepped gable
  (bronze band, triangle frieze tier, stone point, gilded finial), with stepped merlons where
  there is room. The west ring stops north of the ladder and ends in a pier with a gilded point.
- **Tower posts:** each timber post rises out of a stone bastion at the tower head (stone shaft,
  rune belt, bronze coping, battered top) and stands on a battered stone plinth. The bronze rune
  collars at z 35–39 are kept.
- **Gallery:** as in the first pass (chevron parapets, now with gilded tips; rune fascia; corbel
  table on corbels).

## What stays usable

- **Archer and smith:** from the idle animations, the archer stands on the gallery deck at x ≈ -21,
  y 40–49 and the smith at x -7 to -2. The archer shoots south over the yard, crossing the south
  gallery edge at z ≈ 34 west of x -15.5. The south parapet starts at x -16.2 and its chevrons
  stay under that line. Nothing new stands on the deck.
- **Ladders:** `ARCHERYRANGE`'s ladder is on the tower's west face, y 31–40. The SW post's
  bastion does not grow toward it (+y 0, -x 0.5). `V2`'s ladder is at y 40.6–49.7; the west crown
  carries no gable, and the NW bastion stays 0.8 away.
- **Props and upgrades:** the bow prop (x ≤ 44.5) stays inside the east crown ring (d ≥ 1.7). At
  level 3, `V2`'s storey starts at z 80, above the crown's finials (≤ 71.8).

Footprint unchanged. Height unchanged (+0 %; the posts' 72.0 stays the top). The mesh has 3,649
triangles, up from 861 (budget 15,000). Median texel density is 5.9 px/unit, the same as the
fortress. No back face is visible from the sky. Checks: 208/208 pass.

Cameras (`views`) frame the whole building including `V2`; the "before" shots use the same
cameras.

## Status

| Part | Healthy | Construction | Damaged / really damaged / rubble | Snow | LOD M/L |
|---|---|---|---|---|---|
| body (`DBArchRnge_SKN`) | second pass built, checks pass, **awaiting review** | old (`DBArchRnge_A`) | damaged: derived `DBArchRnge_D1` (EA's `ARCHERY`, the same body on a bone turned 180°) on our `dbarchrngH_D` sheet, **awaiting review**; D2/D3 old | variant `dbarchrngH_snow.dds` painted | old |
| banner (`DBHCArchRnge`) | old | | | | |

`bake_hidden` leaves the archer, the smith, their props, the ground plate and the night windows
out of the bakes, so they don't bake shadows onto the sheet. It hides them in the renders too.
`V1` / `V1A` / `V2` (level 2–3 upgrades) are still in the bakes and renders, as in the first pass.

## Framework note (worked around here)

`sagekit/blender/layout.py` `add_solids()` has two limits:

- It fan-triangulates every polygon from its first vertex, so a non-convex face (for example a
  non-convex sweep profile used as an end cap) comes out wrong.
- It keeps a vertex map per polygon. A polygon with three collinear points (for example a chamfered
  `box_rings` ring on a side that does not grow) leaves a loose vertex.

In this recipe, non-convex profiles are never capped, and clamped post rings are square.
