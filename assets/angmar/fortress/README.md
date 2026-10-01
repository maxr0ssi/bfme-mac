# Angmar citadel (`AngmarFortressCitadel`, `AngmarFortress`)

Model `KBFortress`, mesh `KBFORTRESS`, own texture `KBFortresH.tga` (from `KBFortress.tga`).
`Tier.HERO`. Palette A2 "Carn Dum frost, warm timber" (Max's pick, 2026-10-01: A with D's wood,
cooled a touch; `ANGMAR_PALETTE` builds another, [`../style.py`](../style.py)). New pieces come from the Angmar kit
([`shapes.py`](../shapes.py), [`shapes_crown.py`](../shapes_crown.py),
[`shapes_ice.py`](../shapes_ice.py)) and the Mordor and Isengard kits' generic pieces. EA's body
is kept whole. EA's facts are in [`building.py`](building.py), [`crown.py`](crown.py) and
[`walls.py`](walls.py).

## Pass 5: clear of the upgrades

Max on pass 4: "pass 4 is great". The add-ons group found EA's own upgrade models crossing it, so
pass 5 moves our pieces out of their way and keeps the look. Measured on EA's models in the
citadel's coordinates, every model each upgrade draws (healthy, the build-up rising out of the
ground, damaged, rubble), the battle tower on all seven pads of `bases\fortress_angmar`:

- **The House of Lamentation** (over the gate): its drum's back stands at r 39.2 on the gate's
  axis (z 90..104, and the build-up raises it through every height below), where pass 4's +X tine
  had its frozen point (r 41..44). The crown's ring is drawn in by 7 (the tines rise at r 31 and
  flare to their points at r 35); the tines themselves are unchanged. The +X tine clears the drum
  by 1.7.
- **The sanctum** (rises in the middle of the well, r <= 20.3 to z 175): pass 4's cairn stood
  where its shaft goes and the cold fire would have burned inside it. The middle is now left open:
  the tines rise from a ring cairn of black stone and ice (r 23..40), a heap round each tine's
  root and a taller cairn on each diagonal with a crater in its top, the cold fire burning in each
  crater (r 29, z 51.5, the height of pass 4's fire). Built, the sanctum stands in the middle of
  the crown, 5.6 clear of the ring.
- **The Spikes** (26 clumps at r 80..108) and **a battle tower on each pad** (a corner pad's tower
  stands over the bastion's point): pass 4's great clusters at the bastions' points stood inside
  the corner towers, its corner clusters and fissures among the clumps. The two great clusters now
  stand on the clear ground each side of the gate's ramp (r 106, to z 30), a smaller one beside
  the SE one; seven small clusters sit in the gaps between the clumps; the fissures run beside the
  ramp from the wall foot out toward the great clusters (pass 4's along the -Y foot is gone: a
  tower on the S pad and the clumps fill it).
- **The banners** hung at -90 and 90, where a tower on the S or N pad runs its wing into the
  curtain. They hang now between the -Y face's wall tower and the SE bastion (-63.5, facing the RTS
  camera) and opposite it (115.5), clear of the night windows; the icicle rows there gave way.

The sanctum and the cairn: hiding the cairn and its fire while the sanctum stands was the other
way. EA does hide and show sub-objects by upgrade on this building (`SubObjectsUpgrade`:
`ShowSubObjects = IceWall` on the Ice Walls, `HideSubObjects` of every improvement on
`Upgrade_StructureLevel1`), and draws particles only in an upgrade's state (`ModuleTag_DrawHoLFX`,
`FORTRESS_IMPROVEMENT_8`). But our pieces are part of EA's body mesh (and of every damaged model cut
from it), so the cairn would need a mesh of its own in each lifecycle model, and our fire Draw
would need every one of EA's states doubled with `UPGRADE_IVORY_TOWER`: framework work and a
fragile pairing of states. Clearing the ground keeps one model that works with and without the
sanctum.

Clash check (`build/assets/angmar/_review/citadel_v5.jpg`, counted in the citadel's new faces): none
crosses any
model of the House, the sanctum, the Spikes or the battle tower on any pad (pass 4: 191, 112 and
232 rubble, 496 and 575 rubble, and the towers 16..107 on S, N, NE, SE), the build-ups included;
no fire point inside any of them.

13,584 triangles (EA 4,652; budget 15,000). Footprint and height unchanged. 8 fire points, 10
particle systems (pass 4: 9 and 10).

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

Pass 4: 13,440 triangles. Footprint and height unchanged.

Reviews: `build/assets/angmar/_review/citadel_v1..v3.jpg` (shape passes), `citadel_v5.jpg` (pass 4
and pass 5 with each upgrade in place, and the plans),
`citadel_palettes_v1.jpg` (pass 3: EA, then A2 and A, full builds), `citadel_v4.jpg` (EA, pass 3
and pass 4 in A2, and the crown close).

## Status

- [x] healthy body designed (pass 4, Max: "pass 4 is great")
- [x] pass 5: clear of the House, the sanctum, the Spikes and the battle towers (for Max's review)
- [x] palette picked: A2 (A with D's wood, cooled a touch)
- [ ] checked in game (the cold fire's size and colour are seen only in game)
