# Mordor gate watchers (`MordorGateWatchersExpansion`)

Model `GWatchers`, mesh `GWATCHERS`, own texture `MBFortresF.tga` (from `MBFortress.tga`). A fortress expansion built on the citadel's pads: a gate wall and the three-headed Watcher (the Silent Watchers of Cirith Ungol), kept whole with EA's base plate `BIB`. New pieces
come from the Mordor kit and the add-ons' shared pieces ([`../shapes_addons.py`](../shapes_addons.py)).
EA's facts are in [`building.py`](building.py).

## What changed (`watchers.py`)

- **The Watchers wake**: each of the three vulture heads' eyes an almond of Morgul witch-light
  (tag `witch`, six in all, on EA's eye sockets). The one green accent of the add-ons: the
  Watchers are Minas Morgul's sorcery.
- The barbed bottom of a raised portcullis in the gate's arch (both faces, six teeth).
- Two clawed fire baskets on the gate's wall top (z 32), orange fire.
- **Fire** (`fire_points`, 2): `brazier` in each basket.

## Kept clear

- Checked on every one of the citadel's seven pads (EA's base file): no face crosses the citadel's
  new faces; on the S pad the nearest citadel fire point is 15.4 away.

## Status

Designed, shape preview only (not built, not installed). Pass 1: 1,271 -> 2,111 triangles, height unchanged, footprint unchanged, 9/9 preview checks. Checked on our citadel
(pass 7) with every add-on built at once. Review sheet: `build/assets/mordor/_review/addons_v2.jpg` (unchanged in pass 2).

- [x] healthy body designed (pass 1)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint, lifecycle (`GWatchers_A`, `_D2`, `_D3`).
- Whether the green eyes read by day in game (they are small: 2.3 long).
