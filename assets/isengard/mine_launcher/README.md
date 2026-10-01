# Isengard mine launcher (`IsengardMineLauncherExpansion`)

Model `IBFMLaunch`, mesh `IBFMLAUNCH`, own texture `IBFortresP.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. A fortress expansion. EA's launcher is kept whole: the spiked back tower with its
pointed doorway, the roof sloping to the loading star, the crew's platform, the three ramps. The
mines (`BOMB1`..`3`) and the crew (`IBFMLaunch_SKN`) are unit art and stay EA's.

## What changed (`launcher.py`)

- Pointed merlons along the front walls' cornice, knife fins up their corners.
- **Pass 4** (2026-09-30, Max: "our furnace towers on everything look a lil stupid"): pass 3's
  blade pair flanking the tower (to z 89) went; EA's spiked tower is the silhouette again. The
  White Hand in a pointed-arch slot on each of the tower's sides (z 40.5..55.5, standing proud of
  its ribs at y +-6.8..8.8). Knife fins up the tower's front corners.
- Iron jaws flanking each ramp's lip.
- On the crew's platform: a pyramid of orcfire mines, a brazier and a firebox (`fire_points`, 2:
  brazier, furnace).

## Kept clear

- The tower's doorway (+X face, z 48..58.5), the Uruk's spot (r 5 round (-16.3, 13.9)), the launch
  paths past `B_FX1`..`3`. The mines stand at (-18.6, 21.4).

## Status

Pass 3 built and installed (2026-09-29). Pass 4 designed, shape preview only: 1,094 -> 2,298
triangles (pass 3: 4,110), height unchanged (pass 3: +19.1 %), footprint unchanged, fire 2 -> 2,
9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg`. Pass 3: `_review/addons_v3.jpg`.

## Open

- Full build: bake, paint, lifecycle (`IBFMLaunch_A`, `_D2`, `_D3`). No house model: no banner.
