# Isengard wall hub (`IsengardCastleWallHub`)

Model `IBWallRmprtN`, mesh `IBFBALTOW01` (on a bone at z 25.47: model z = mesh z + 25.47), own
texture `IBFortresD.tga`. Palette A. EA's hexagonal shaft is kept whole (bands, leaning parapet,
knife fins round the foot) and given the citadel's blade cluster on its roof
([`shapes_walls.py`](../shapes_walls.py) `hub`, shared with
[fortress_wall_hub](../fortress_wall_hub/README.md)).

## Crown options (hubs_v1, 2026-09-30)

Max on destack_v1: the body is fine, the blades on top look off. Three crowns for both hubs
(`shapes_walls.hub(kit, crown)`; `HUB_CROWN` in [building.py](building.py) picks; Max picked **A**; `ISENGARD_HUB_CROWN=A` previews one): **A** Orthanc's horned top (24 short silver-edged black
horns, a fire-pot in the middle, fire: brazier), **B** five pointed merlons a face with the Hand on
shields and a fire grate, **C** a stepped faceted cap with Hand arches, corner fins and a fire
well. All stay under the segments' needles (model 69-74). Sheet: `_review/hubs_v1.jpg`.

## Pass 4 (shape preview, 2026-09-30): no stack

Max: "our furnace towers on everything look a lil stupid ... super low quality that tower". The
needle stack between the blades went; the walls keep their blade pairs (the citadel's family,
crenellation) and no stacks. 258 -> 2,830 triangles, height +31.1 % (the blades), footprint
unchanged, 9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg`.

## Pass 3 (shape preview): the citadel's cluster

Pass 1 was still EA's drum with a small crown of six horns ("Isengard is pointy").

- **The cluster**: a needle stack on the axis (lozenge section, iron fins up its edges, a spiked
  ember collar, a blade crown round an ember throat) to model 84, between two matching lozenge
  blades along x (sharp edges to the x corners, three layered fins a face, silver edges, ember slits, a
  collar, leaning out a little as Orthanc's horns) to model 82: one pointed mass nearly corner
  to corner on the roof.
- **Corners**: the walls' lozenge needles (the segments' crest needles) on the parapet's six
  corners to model 72.5; silver on the six corner arrises down the shaft.
- Iron spikes leaning out of each parapet face; a pair of pointed ember slits on every face.
- No fire and no banners: hubs repeat along every wall (the stack's throat glows, no fire point).
- Tried and dropped: blades clasping the corners from the upper band (mostly buried in the drum,
  their fins broke through its corners as loose plates); a ring of pointed merlons (a fence of
  sticks); six corner blades round a stack (small, busy, the collars read as white crosses).

258 -> 3,052 triangles, height 62.6 -> 84.2 (+34.6 %, `max_z_growth` 0.35 as the citadel's),
footprint unchanged, 9/9 preview checks. Sheet: `build/assets/isengard/_review/walls_v3.jpg`
(pass 1: `walls.jpg`).

## Kept clear

- Segments run into any face (its middle 16.6, to model z 59.2): nothing new stands out of a face
  there but the slits (0.2 proud); the cluster stands on the roof, the needles on the corners.

## Status

- [x] pass 3 built in colour and installed (2026-09-29)
- [x] pass 4 designed (shape preview, 2026-09-30)
- [ ] pass 4 reviewed by Max, built in colour, installed
