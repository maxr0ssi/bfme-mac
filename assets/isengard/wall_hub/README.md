# Isengard wall hub (`IsengardCastleWallHub`)

Model `IBWallRmprtN`, mesh `IBFBALTOW01` (on a bone at z 25.47: model z = mesh z + 25.47), own
texture `IBFortresD.tga`. Palette A. EA's hexagonal shaft is kept whole (bands, leaning parapet,
knife fins round the foot) and crowned as Orthanc is ([`shapes_walls.py`](../shapes_walls.py)
`hub`, shared with [fortress_wall_hub](../fortress_wall_hub/README.md)).

## Pass 1 (shape preview)

- Six straight horns on the parapet's corners; a stepped hexagonal plinth on the roof with a
  lozenge needle (silver collar and edges) to model z 75; six radial ribs with silver tops from the
  plinth to the horns' feet (the roof no longer one flat slab).
- Three iron spikes leaning out of each parapet face; silver on the six corner arrises; a pair of
  pointed ember slits on every face between EA's bands.
- No fire and no banners: hubs repeat along every wall.

258 -> 1,390 triangles, height 62.6 -> 75.0 (+19.9 %), footprint unchanged, 9/9 preview checks.

## Kept clear

- Segments run into any face (its middle 16.6, to model z 59.2): nothing new stands out of a face
  there but the slits (0.2 proud); the spikes stand above the parapet (model 62.5).

## Status

- [x] healthy body designed (pass 1, shape preview)
- [ ] reviewed, built in colour, installed
