# Men statue (`GondorStatue`, `GondorHeroStatue`)

Model `GPHealstue`, redesigned mesh `GPHEALSTUE`, painted from the unit sheet `GUHeroStat.tga`
(own `GUHeroStaH.tga`). The model is a lone mesh, with no hierarchy. EA's guardsman and the White
Tree relief on the pedestal's front are untouched; the work is all on the pedestal.

## What changed

- **Piers**: four corner piers stand out from the die: moulded bases, a steel band, and capitals
  under the cornice's flare.
- **Relief**: a moulded frame with a steel keystone rings EA's panel.
- **Sides**: White Tree shields on the die's plain sides (`keep/tower.py` shield, closed behind).
- **Step**: a moulded step lifts the figure's plinth.
- **Cornice**: steel braziers with gilt flames on the front corners, pinnacles with steel orbs on
  the back corners.
- **Banners**: one, on the back face; cloth in `GPHCHealstue`.

## Status

Installed with the Men pack. 550 -> 2,192 triangles, footprint and height unchanged (top 65.1, the
figure), 70/70 checks. `facet_islands = 20` seams the unwrap at EA's island borders and at turns
over 20 degrees, so the cloak's folds do not overlap in our layout. Damaged is derived; really
damaged and rubble are rebuilt. Construction stays EA's: our faces' backs open to the sky 2.85 %
against the 2 % standard (`work/lifecycle.json`).
