# Mordor mumakil pen (`MordorMumakilPen`)

Model `MBMumkpen`, mesh `MUMAKILPEN`, own texture `MBMumkPeH.tga` (from `MBMumkPen.tga`); new faces
map to the faction's master sheet. EA's pit, decks, rails and berms are kept whole. The door
(`mumakil_pen_02`) stays EA's. EA's facts are in [`building.py`](building.py), the design in
[`pen.py`](pen.py), the group's pieces in [`../shapes_harad.py`](../shapes_harad.py).

## Pass 2: the tusk arch

The pen uses the same Harad twist as the palace (approved by Max): Mordor's black, fire and steel,
with ivory tusks, brass, war-paint red and sun-and-serpent banners.

- **Arch** (the new mass, over the open +X end at x 45.8):
  - A stepped basalt plinth with a fire bowl stands on each side (`furnace`, `smoke`).
  - From each plinth two big ivory tusks rise over the mumakil's way (z 58 over |y| 20) and cross
    at the crown (z 72) like sabres.
  - A basalt saddle on the crossing carries a fire bowl (`furnace` and a heavy dark `plume`, to
    z 83).
  - The Harad sun on a war-paint plate hangs under the crown, facing out.
  - Chains with hooks hang from the tusks.
- **Claws**: one on each berm between the rail's posts, a stepped plinth with a fire bowl and six
  ivory tusks round it.
- **Howdahs**: a spiked howdah frame on each deck (x -21), 15 by 5.4, with charred timber walls,
  brass rails, a pointed canopy in the player's colour, and steel spikes jutting out over the berm.
- **Banners**: two banners in the player's colour hang from the -Y rail, each with the sun and
  serpent in brass.
- **Lava**: open lava runs along the foot of the -Y berm.

1,472 -> 7,757 triangles. Height 69.6 -> 85.8 (+23.2 %, `max_z_growth` 0.25). Footprint unchanged.
9/9 preview checks. 12 fire points. Review sheet: `build/assets/mordor/_review/harad_v2.jpg`.

## Kept clear

- **The door's swing**, measured over every frame of its animations (2026-09-30):
  - `MBMumkpenDOP` (opening): x -43.2..35.6, |y| < 23.8, z 44.3..80.2.
  - `MBMumkpen_DROCD` (damaged): x -43.2..36.9, |y| < 23.8, z 35.1..80.2.
  - At its widest the far end rises by 29, about 24 degrees.
  - Nothing of ours is in x -44..37.5, |y| < 24.5, z 35..81. The arch stands beyond x 43.
- The mumakil's way (|y| < 20) and EA's deck beams' ends past it (|y| 19..24, z 44..48).
- `V1`, `V2` and `BANNERS` appear only from levels 2 and 3. `bake_hidden` leaves them out of bakes
  and renders, and the sheet has an rts row with them shown. Also kept clear: the house banner's
  pole (29.8, 22.3) and the night meshes.

## Status

- [x] healthy body designed (shape preview, pass 2)
- [ ] Max's review of `harad_v2.jpg`, then build, colour, install
