# Goblin citadel (`WildFortressCitadel`, `WildFortress`)

Model `WBFortress`, mesh `WBFORTRESS`, own texture `WBFortresH.tga` (from `WBFortress.tga`).
`Tier.HERO`. Palette E, "Blood, iron and bone" ([`style.py`](../style.py)); new pieces come from
the Goblin kit ([`shapes.py`](../shapes.py), `GoblinShapes`). EA's body is kept whole (towers,
hoods, glowing eyes, curtain walls, the dragon's head, the ramp).

## What changed

- **Spires** (`crown.py`): a riveted iron hoop round each hood, four great black horns with
  bleached tips at z 84, four small tusks under them, an iron spike from each hood's tip to z 137
  with a big scowling skull on it (the new silhouette), a skull trophy on a blood-tipped spike out
  of each column's outer corner. Front spires: an iron gibbet cage with a skeleton inside; back
  spires: a flayed hide on a hook.
- **Walls** (`building.py`): a leaning palisade of sharpened stakes along the side and back
  walks, a goblin skull on one stake per wall; a totem over each wall's middle buttress (horned
  troll skull, bone crossbar, ribcage); crimson hides daubed with white war paint.
- **Gate** (`gate.py`): two great iron-collared tusks arching in over the dragon's head, a hide
  on each; bone fangs along the tongue; skull piles and an impaled skeleton by each tusk; fire
  bowls on the front walk.
- **Skulls**: `GoblinShapes.skull`: a domed cranium set back behind a face of separate bones, so
  the eye sockets and nose are real holes; the big ones add temples and a hinged jaw, goblin
  skulls tusks, troll skulls horns. Three sizes (about 100 / 160 / 220 triangles).
- **Gore**: the `Gore` paint layer ([`paint.py`](../paint.py)): stains and drips from the skulls,
  trophies, bodies, piles and tusk tips (`gore_anchors`), thin drips under crimson ledges.
- **Banners**: three ragged banners on bone spars (two beside the gate, one on the -Y wall), each
  with a white painted mark; cloth in `WBHCFortress` (EA's flag dropped).

## Kept clear

- The doors' swing: x 44.5..57.1, |y| <= 13.7, z 7.5..44.4, and in to x 34.9 when damaged.
- The ramp; the glowing eyes (nothing between r 12.9 and the hood below z 70); the courtyard
  (throne, drake perch); the razor spines ring outside r 70.

## Status

Installed with the Goblin pack. 2,738 -> 14,380 triangles (budget 15,000), height 116.9 -> 137.0
(+17.2 %), footprint unchanged, 90/90 checks. Every lifecycle state carries the redesign:
construction, really damaged and rubble are rebuilt along EA's pieces. EA's own UV overlap
(0.73 %) is gone with `facet_islands = 8`. No night lights (EA's citadel has no night meshes).

## Known limits

- The razor spines ([`fortress_spines`](../fortress_spines/README.md), a stub) and the door
  leaves `WBFDoor` are still EA's art.
