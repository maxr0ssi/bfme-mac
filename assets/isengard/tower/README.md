# Isengard tower (`IsengardTowerExpansion`)

Model `IBFITower`, mesh `IBFITOWER` (identity bone), own texture `IBFortresQ.tga`; `IBFITOWERB`
stays EA's. Palette A. EA's tower is a small Orthanc already (square shaft tapering in bands,
pointed windows, a flared crown of flanges and horns to z 130.5): it stays whole and gets fire.

## Pass 1 (shape preview)

- **Fire**: four fire baskets on iron brackets out of the shaft's corners at z 87, under the
  crown, lighting it from below (`fire_points`, four 'brazier').
- **Embers**: EA's pointed windows glow: ember panels in the upper two window rows on every
  face, leaning back with the recess.
- **Banner**: one heavy banner on the field face (+X, away from the citadel) between the bands.
- **The wall stub** takes the walls' profile ([`shapes_walls.py`](../shapes_walls.py) `stub`):
  short knife fins, a buttress blade, ember slits, the silver lip and ridge, spikes, needles.

848 -> 2,108 triangles, height unchanged (130.5), footprint unchanged, 9/9 preview checks.

## Kept clear

- The crown and its horns (EA's); the stub's end at x -32.67 where it meets the citadel's wall.

## Status

- [x] healthy body designed (pass 1, shape preview)
- [ ] reviewed, built in colour, installed
