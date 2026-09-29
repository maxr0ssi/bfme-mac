# Isengard mine launcher (`IsengardMineLauncherExpansion`)

Model `IBFMLaunch`, mesh `IBFMLAUNCH`, own texture `IBFortresP.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. A fortress expansion. EA's launcher is kept whole: the spiked back tower with its
pointed doorway, the roof sloping to the loading star, the crew's platform, the three ramps. The
mines (`BOMB1`..`3`) and the crew (`IBFMLaunch_SKN`) are unit art and stay EA's.

## What changed (`launcher.py`)

- Pointed merlons along the front walls' cornice, knife fins up their corners.
- **The pair** (pass 3, the citadel's blades): two lozenge blades flanking EA's back tower
  ((-30.8, +-16.6), 15 long, 8 wide), mirrored about the launcher's axis, from the foot to needles
  at z 89 over the tower's spikes (74.7), leaning in: layered fins, silver edges, ember slits, a
  spur at each +X foot, the White Hand in a pointed-arch slot on each one's outer face (pass 1's
  Hands on the tower's sides sat behind them). Knife fins up the tower's front corners.
- Iron jaws flanking each ramp's lip.
- On the crew's platform: a pyramid of orcfire mines, a brazier and a firebox (`fire_points`, 2:
  brazier, furnace).

## Kept clear

- The tower's doorway (+X face, z 48..58.5), the Uruk's spot (r 5 round (-16.3, 13.9)), the launch
  paths past `B_FX1`..`3`. The +Y blade stands on the crew platform's back corner (x < -23.9 at
  its height); the mines moved to (-18.6, 21.4) beside it.

## Status

Designed, shape preview only (not built, not installed). Pass 3: 1,094 -> 4,110 triangles, height
74.8 -> 89.1 (+19.1 %), footprint unchanged, 9/9 preview checks. Review sheet: `build/assets/isengard/_review/addons_v3.jpg` (pass 3; `addons.jpg` is pass 1).

## Open

- Full build: bake, paint, lifecycle (`IBFMLaunch_A`, `_D2`, `_D3`). No house model: no banner.
