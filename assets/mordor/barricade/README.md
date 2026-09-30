# Mordor barricade (`MordorBarricade`)

Model `MBBarcade`, mesh `MBBARCADE`, own texture `MBBarcadH.tga` (from `MBBarcade.tga`); new faces
map to the faction's master sheet. EA's L of blocks and the keep are kept whole. EA's facts are in
[`building.py`](building.py) and the design is in [`defences.py`](defences.py).

## Pass 1: barbed steel and lava

- **Lava**: open lava runs along the foot of every front (y -30.4 before the low block and the
  keep, y -34 before the +X block, x 42.6 before the wing), with a basalt kerb outside it and a
  moat across the gate (x 45.6). Glowing cracks run up the fronts. It has `embers` and two thin
  `smoke` columns.
- **Gate**: the raised portcullis' six barbed steel teeth fill the gate's arch (+X face).
- **Stakes**: six crooked barbed stakes stand in a row before the low block and the keep.
- **Spikes**: steel spikes lean out along every roof's outer lip.
- **Keep**: eight jagged spikes rise from inside the keep's parapet and lean in (tips z 85.5).
  Their tips stay 6 or more from the archer in the middle.
- **The Eye** is on the keep's front (z 46..61).
- **Fire baskets**: two, on the low block's and the wing's roofs (`brazier`).

923 -> 5,117 triangles. Height 78.8 -> 85.6 (+8.6 %). Footprint unchanged. 9/9 preview checks.
9 fire points. Review sheets: `build/assets/mordor/_review/harad_v1.jpg`, `harad_v2.jpg` (unchanged in pass 2).

## Kept clear

- The archers' bones `ARCHER_01`..`04`: nothing within 5 of them.
- The door in the low block's front (x -36..-26, to z 18) has no crack over it.

## Open

- No house-colour cloth. EA gives the barricade no house model, so the style's template stands in.

## Status

- [x] healthy body designed (shape preview, pass 1)
- [x] coordinator's review of `harad_v1.jpg`: keep
- [ ] Max's review, then build, colour, install
