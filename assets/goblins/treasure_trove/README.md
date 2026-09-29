# Goblin treasure trove (`WildTreasureTrove`)

Model `WBTreaTrov_SKN`, mesh `WBTREATROVT`, own texture `WBTreaTroH.tga` (from `WBTreaTrov.tga`).
Palette E. EA's carved dragon (head, curled body, claw over the hoard), its rock bed (`ROCK`,
with the Dwarves' `DBStoneA_NRM`: left EA's) and the gold and jewels are kept whole. The idea:
the Goblins' prize, a dead dragon shackled on its hoard.

## What changed

- **Horns**: two great crimson horns (40 long) with bleached tips rising from the back of the
  head and sweeping back, spiked riveted iron collars at their roots (the new silhouette).
- **Band**: a spiked iron strap over the head between the horns and the nails.
- **Nails**: two iron spikes driven down through the skull, a goblin skull on each.
- **Chains**: the jaw chained at both corners to big iron ring-stakes, heavy links.
- **Plunder**: three iron-bound strongboxes along the +X front, a torch on a post among them.
- **Trophies**: skull piles by the jaws.
- **Banner**: one on a post at the -Y front by the head (cap 1).

## Kept clear

- The hoard (x 3..41, y -42..-3) and the two goblins who work it; the level-up tower and rock on
  the -X+Y side (V1, V1A).

## Status

Shape preview only (second pass). 1,585 -> 4,948 triangles, height 61.2 -> 68.0 (+11.0 %), footprint unchanged,
9/9 preview checks. `world_space = True`: the body hangs on a bone turned about z, so the design
works in model axes.
