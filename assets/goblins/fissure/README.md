# Goblin fissure (`GoblinFissure`)

Model `WBFissure`, mesh `CYLINDER01`, own texture `WBStonH.tga` (from `WBStone.tga`, which the
Elves' Ent and Mordor's trolls draw too). Palette E. EA's horseshoe of rock and the crack's floor
(`PLANE01`, WBFissure) are kept whole. The idea: a vent the Goblins worship and work.

## What changed

- **Idol**: a great horned troll skull nailed to the overhang at the crack's head, looking down it.
- **Crests**: a horn crown and a skull on an iron spike on the back peak (the new silhouette); a
  pair of bleached tusks on each arm's crest; iron spikes along both arms' ridges.
- **Gate** (the new silhouette): a jaw gate over the crack's mouth. A timber tower on each lip
  (braced posts, a plank deck with a stake parapet, a troll skull on its corner), a plank bridge
  with rope rails between their decks at z 20, high over the floor, bone teeth hanging from its
  front and a skull on a chain under its middle. A tall totem stands before the -Y tower.
- **Palisades**: tall sharpened logs running back from each tower along the arms' feet.
- **Climb**: a lashed ladder up the -Y arm to its crest, a fire bowl at the top.
- **Trophies**: skull piles by the towers.
- **Banner**: one on a tall post on the -Y crest, a horned skull on its point (cap 1).

## Kept clear

- The floor (`PLANE01`, x -36..64 in CYLINDER01 coordinates) and the steam over it: nothing
  stands on it. The gate's bridge crosses high over its mouth (z 19..21, teeth down to z 11).

## Status

Shape preview only (second pass, after Max's review of v1: too thin). 230 -> 7,711 triangles,
height 51.9 -> 59.6 (+14.8 %), footprint unchanged, 9/9 preview checks. Design coordinates are CYLINDER01's (model minus (1.6, 8.06)).
