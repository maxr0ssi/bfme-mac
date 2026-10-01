# Angmar citadel (`AngmarFortressCitadel`, `AngmarFortress`)

Model `KBFortress`, mesh `KBFORTRESS`, own texture `KBFortresH.tga` (from `KBFortress.tga`).
`Tier.HERO`. Palette A2 "Carn Dum frost, warm timber" (Max's pick, 2026-10-01: A with D's wood,
cooled a touch; `ANGMAR_PALETTE` builds another, [`../style.py`](../style.py)). New pieces come from the Angmar kit
([`shapes.py`](../shapes.py), [`shapes_crown.py`](../shapes_crown.py),
[`shapes_ice.py`](../shapes_ice.py)) and the Mordor and Isengard kits' generic pieces. EA's body
is kept whole. EA's facts are in [`building.py`](building.py), [`crown.py`](crown.py) and
[`walls.py`](walls.py).

## Pass 4: four frozen tines

Max on pass 3 (citadel_palettes_v1): the eight tines with EA's horns read busy at RTS - "reduce a
few horns but keep some ... I think size is fine, just 4 more detailed ones?" and "I like ice cold
tips, like frozen style". A2 confirmed, its wood "just slightly too warm, just a little".

- **Four forged tines** ([`crown.py`](crown.py), [`../shapes_tine.py`](../shapes_tine.py)), the tall
  size kept (z 120), on the building's axes (the gate +X), EA's bastion windows looking out
  between them. Each is a quality piece: a ten-sided section with steel bevels and a raised spine
  down its outer face, seven barbs hooking up off both edges, two riveted iron bands above the
  walk, a rune groove of short strokes and diamonds glowing faint cold blue up the spine.
- **Frozen tips**: dark iron up most of the length; from z ~95 (a little different on each tine)
  the iron is cased in ice under a ragged frost line, white rime on the last stretch to the point,
  ice crystals (the wall-foot clusters' shards) growing up out of the casing and a few out of the
  iron just below it, icicles hanging off the barbs. EA's horns get no frost crust: the crown's
  four frozen points are the one bold accent, and frosting EA's eight horn tips too brought back
  the bristle Max called busy.
- **A2's wood a touch cooler**: the planks less orange, toward weathered brown, less of EA's orange
  grain kept ([`../style.py`](../style.py)).

## Pass 3: the Witch-king's crown (eight tines, superseded)

- **The crown** ([`crown.py`](crown.py)): out of the courtyard well rise eight broad iron tines
  on a ring (r 38), four tall to z 120 and four short to z 100. Each is a blade with a ridge down
  both faces, widest (19 across) just above the walk, with steel edges, barbs hooking up off both
  edges and rime on the point. They flare out a little, like a crown. They stand between the
  diagonals, so EA's bastion windows on the well side look out through the gaps. EA's four great
  spires curve in over them. No height growth: the tips stay under EA's spires (z 143.6).
- **Cold fire**: a cairn of black stone and ice shards fills the crown's heart, and the cold fire
  burns out of its crater at the walk's height (`coldfire`: our `SagekitColdFire`, EA's
  furnaceFire ice-blue to white, and `SagekitColdSmoke`, a modest blue-black plume). Four more
  cold flames burn round it (`coldflame`). EA's own blue fire on this citadel is a flame card
  (`EXFireTorchSeqBlue` on `MBFDPF`, shown with the Banners upgrade), not a particle system, so
  there was nothing of EA's to reuse.
- **Ice** ([`walls.py`](walls.py)): angular crystal clusters grow out of the wall feet: a great one
  against each bastion's point and smaller ones in the corners where the bastions meet the
  curtain. Small clusters sit on the parapet's top. Icicles hang under a rime crust along the
  curtain's lip. Cold glow wells out of fissures along the -Y and gate-side feet, with a black
  stone kerb and ice breaking out of it.
- **Story** ([`yard.py`](yard.py)): four sorcerers' braziers on the walk, each a claw of iron
  prongs out of black stone shards with a cold flame in it. Iron gibbets with cages hang off the
  -Y wall towers. Icicles hang off the gate's lintel like a frozen portcullis, their points above
  z 32. Two heavy banners hang from the curtain's lip between the wall towers, the cloth in the
  player's colour.

Kept clear: EA's night windows (`N_WINDOW`: the curtain's slits, the bastions' fronts and their
well faces), the Ice Walls shell (`ICEWALL`, 1.5..3 outside the curtain: the icicles hang outside
it and the clusters stand on the ground beyond it), the Ice Munitions horns and mist on the
bastions, the Banners upgrade's blue torch cards, the arrow bones, the gate and the doorway. The
renders leave the upgrade meshes out (`bake_hidden`).

13,440 triangles (EA 4,652; budget 15,000). Footprint and height unchanged.

Reviews: `build/assets/angmar/_review/citadel_v1..v3.jpg` (shape passes),
`citadel_palettes_v1.jpg` (pass 3: EA, then A2 and A, full builds), `citadel_v4.jpg` (EA, pass 3
and pass 4 in A2, and the crown close).

## Status

- [x] healthy body designed (pass 4, for Max's review)
- [x] palette picked: A2 (A with D's wood, cooled a touch)
- [ ] checked in game (the cold fire's size and colour are seen only in game)
