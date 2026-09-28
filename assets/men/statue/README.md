# Men statue (`GondorStatue`, `GondorHeroStatue`)

Model `GPHealstue`, redesigned mesh `GPHEALSTUE`, painted from the unit sheet `GUHeroStat.tga`
(own `GUHeroStaH.tga`). The model is a lone mesh, with no hierarchy.

## What changed

EA's guardsman is untouched, and so is the White Tree relief on the pedestal's front. The work is
all on the pedestal:

- Four corner piers stand out from the die: moulded bases, a steel band, and capitals under the
  cornice's flare.
- A moulded frame with a steel keystone rings EA's relief panel.
- White Tree shields sit on the die's plain sides (`keep/tower.py` shield, closed behind).
- A moulded step lifts the figure's plinth.
- Steel braziers with gilt flames stand on the cornice's front corners, and pinnacles with steel
  orbs on its back corners.
- 1 house-colour banner on the back face (cap 1).

## Status

- [x] checks 70/70 ALL PASS. Footprint and height are unchanged (x -7.86..9.0, y -8.44..9.37, top
      65.2 = the figure). 550 -> 2192 triangles.
- [x] `facet_islands = 20`: unwrapped whole, the figure's cloak folds flipped over one another in
      our layout (0.24 % of texels twice). It is now seamed at EA's island borders and at turns
      over 20 degrees: 0 % overlap.
- [x] lifecycle: really damaged and rubble are rebuilt, and damaged is derived. Construction stays
      EA's (open backs 2.85 % against the 2 % standard; `work/lifecycle.json`).
- [ ] banner shows after `sagekit house men`; Max's review
