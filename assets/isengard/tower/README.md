# Isengard tower (`IsengardTowerExpansion`)

Model `IBFITower`, mesh `IBFITOWER` (identity bone), own texture `IBFortresQ.tga`; `IBFITOWERB`
stays EA's. Palette A. EA's tower is a small Orthanc already (square shaft tapering in bands,
pointed windows, a flared crown of flanges and horns to z 130.5): it stays whole and takes the
citadel's recipe.

## Pass 3 (shape preview)

Pass 1 gave it fire, glowing windows and a banner, but at the RTS view it read as EA's.

- **Four blades** on the shaft's diagonals from the plinth to needles at z 121: lozenges with
  their sharp edges out along EA's chamfered corners, clasping the shaft to z ~60 and standing
  free above it, just outside the crown's flared corners; a deep fin a face, silver edges, ember
  slits, a collar. The White Hand in a pointed-arch slot on the field (+X) face of the two field
  blades.
- **A needle stack out of the crown**, between EA's four inner horns, from the crown's floor
  (z 113) to its throat at z 162 and its blade crown to z 166: lozenge section, fins up its
  edges, an ember collar. Its throat is the tower's chimney fire.
- **Fire** (`fire_points`, five): the stack's chimney and four braziers on the crown's floor
  between the horns, the crown lit from within. Pass 1's bracket braziers on the shaft's corners
  gave way to the blades.
- **Embers**: EA's pointed windows glow (ember panels in the upper two window rows, leaning back
  with the recess); ember slits in the blades.
- **Banner**: one heavy banner on the field face (+X) between the bands.
- **The wall stub** takes the walls' profile ([`shapes_walls.py`](../shapes_walls.py) `stub`):
  short knife fins, a buttress blade, ember slits, the silver lip and ridge, spikes, needles.
- Tried and dropped: the blades with three layered fins a face and three rows of slits (a bundle
  of silver ladders at the RTS view).

848 -> 4,752 triangles, height 130.5 -> 166.3 (+27.4 %, `max_z_growth` 0.35 as the citadel's),
footprint unchanged, 9/9 preview checks. Views: `top` (the crown) and `field` (from +X, low).
Sheet: `build/assets/isengard/_review/walls_v3.jpg`.

## Kept clear

- EA's crown and its horns; the blades pass outside the crown's corners (0.5 clear at z 105).
- The stub's end at x -32.67 where it meets the citadel's wall; the stub's lip spikes stop at
  x -13, short of the -X blades.

## Status

- [x] healthy body designed (pass 3, shape preview)
- [ ] reviewed, built in colour, installed
