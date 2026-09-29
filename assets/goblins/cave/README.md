# Goblin cave (`GoblinCave`)

Model `WBCave_SKN`, mesh `WBCAVE`, own texture `wbcavH.tga` (from `wbcave.tga`, which Isengard
and Mordor draw too). Palette E. EA's body is kept whole: the black rock (`WBCAVE_STONE`, EA's
WBStone mesh), the five crimson claws over the mouth, the horn spikes, the crooked stalks, the
rubble. The idea: the gate of Goblin-town, a hole in the mountain that spits out warriors.

## What changed

- **Gate**: a lashed timber frame in the mouth under the claws' tips, bone fangs hanging from its
  lintel, a goblin skull on each post's point, a torch on an iron arm off each post.
- **Tusks**: two great iron-collared tusks rising either side of the mouth and arching in over it.
- **Trophy**: a horned troll skull nailed to the middle claw over the mouth.
- **Summit**: a totem on the rock behind the claws (horned skull, bone crossbar with skulls,
  ribcage) in a ring of black horns: the new silhouette. A skull on an iron spike either side.
- **Flanks**: sharpened stakes along both front flanks, an impaled skeleton and a hide drying
  frame on the -Y side, skull piles by the rubble.
- **Banners**: two ragged house-colour banners on tall posts either side of the mouth (cap 2);
  EA's flag in `WBHCCave` is dropped.

[`motifs.py`](motifs.py) holds the pieces the production group shares (posts, props, gates,
stakes, ladders, bone spars, pole banners, torches, hide frames, chests, ring stakes, windlass,
ore cart).

## Kept clear

- The mouth under z 23 inside |y| < 12 (the sword-guard's walk); the gate's fangs end above z 19.5.
- The level-up meshes on the -X side: V1 (the tower, x -54..-8, y -3..37, z 35..92, its archers'
  bones at z 53) and its rock V1A.

## Status

Installed. 505 -> 6,299 triangles, height 59.3 -> 67.3
(+13.6 %), footprint unchanged, 9/9 preview checks. No custom night lights yet; EA's stay.
