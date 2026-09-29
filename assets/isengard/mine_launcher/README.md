# Isengard mine launcher (`IsengardMineLauncherExpansion`)

Model `IBFMLaunch`, mesh `IBFMLAUNCH`, own texture `IBFortresP.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. A fortress expansion. EA's launcher is kept whole: the spiked back tower with its
pointed doorway, the roof sloping to the loading star, the crew's platform, the three ramps. The
mines (`BOMB1`..`3`) and the crew (`IBFMLaunch_SKN`) are unit art and stay EA's.

## What changed (`launcher.py`)

- Pointed merlons along the front walls' cornice, knife fins up their corners.
- The White Hand in a pointed arch and ember slits on each side of the tower, knife fins up its
  corners.
- Iron jaws flanking each ramp's lip.
- On the crew's platform: a pyramid of orcfire mines, a brazier and a firebox (`fire_points`, 2:
  brazier, furnace).

## Kept clear

- The tower's doorway (+X face, z 48..58.5), the Uruk's spot (r 5 round (-16.3, 13.9)), the launch
  paths past `B_FX1`..`3`.

## Status

Designed, shape preview only (not built, not installed). 1,094 -> 2,386 triangles, height and
footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`IBFMLaunch_A`, `_D2`, `_D3`). No house model: no banner.
