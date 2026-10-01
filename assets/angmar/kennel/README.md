# Angmar kennel (`AngmarKennelExpansion`)

Model `KBFKennel`, mesh `KBFKENNEL`, own texture `KBFortressR.tga` (from `KBFortressX.tga`). Palette
A2. New pieces from the army kit ([`../shapes_army.py`](../shapes_army.py)). EA's body is kept whole,
less its four loose vertices. EA's facts are in [`building.py`](building.py).

## Pass 1: the warg-tusk arch

- **Two great warg tusks** rise from rimed black stone footings either side of the gate, the wolves'
  way out. They curve in and cross over EA's wolf pelt, one a little in front of the other.
- An iron band is riveted where the tusks cross, and teeth of ice line their inner edges.
- No fire: the kennel has no forge, pit or brazier of its own.

`facet_islands = 8`: the first build's unwrap overlapped (0.32 %).

Kept clear: the portcullis and the way out to the rally point (+X), the pelt, the front claws and the
Ice Walls shell (`ICEWALL`). The `gate` view looks at the arch.

1,387 triangles (EA 645). Footprint and height unchanged.

## Status

- [x] healthy body designed (pass 1, shape previews)
- [ ] built in colour, renders reviewed
- [ ] checked in game
