# Angmar den (`AngmarDen`)

Model `KBDen`, mesh `BASE`, own texture `KBDeH.tga` (from `KBDen.tga`). Palette A2. New pieces from
the army kit ([`../shapes_army.py`](../shapes_army.py)). EA's body is kept whole. EA's facts are in
[`building.py`](building.py).

## Pass 2: the den's mouth

The coordinator's review of pass 1: the skull read small on the rock.

- **The skull is now the den's mouth.** The cave the wargs come out of, on the rock's +X side, becomes
  the mouth of a great frozen warg skull, 53.5 long.
- Its cranium rises out of the rock over the cave, with a rimed crest and ice crystals on the crown,
  flaring cheekbones, and brow ridges over dark sockets with frost crystals in them. The snout reaches
  out over the yard with long ice fangs and a dark nose.
- The lower jaw drops to the ground, its two halves apart so the wargs walk out between them.
- **Cold fire** glows low in its throat (`coldflame`), so the flames rise clear of the bone.
- A cluster of ice and black stone shards stands outside the pen wall.

Pass 1 (superseded): a 42-long skull on the rock's face over the pen.

Kept clear: the warg (`BROWNWOLF01`) and the dummy in the pen, the orc's platform and its level-2
roof (`V1`, and its spikes on the +X side), the level-3 watch tower (`V2`), and EA's cave glow and
mist. The renders and bakes show level 1 (`bake_hidden`: `V1`, `V2`). The `skull` and `cave` views
look at the mouth. `facet_islands = 8`: the first build's unwrap overlapped (0.02 %).

3,678 triangles (EA 2,256). Footprint and height unchanged. 1 fire point.

## Status

- [x] healthy body designed (pass 2, shape previews)
- [ ] built in colour, renders reviewed
- [ ] checked in game
