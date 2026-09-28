# Men siege workshop, level 2 (`V1` of `GBWorkshop`)

Draft for review, not installed. Chained on [`workshop`](../workshop/README.md) (`base`), followed
by [`workshop_level3`](../workshop_level3/README.md); the pattern is
[`barracks/levels.py`](../barracks/levels.py). Renders: `build/assets/men/workshop_level2/renders/`.

## What changed

- **Walls**: a crenellated parapet (square merlons, capstones) along the walk's outer edge, on the
  straight runs and the diagonal returns. EA's lip on the yard edge stays (a coping there met EA's
  lip in coplanar faces the sky check rejected).
- **Bastions**: merlons round the rim and a watch turret on each: a drum with slit windows, a
  steel-banded cornice, a slate cone, a steel spike and a gilt knob.
- **Tower blocks**: merlons round their tops and a pinnacle on each outer corner.
- **Caps**: steel ribs up EA's slate caps (eight hips, four middles); the body's mast and orb
  stand through each apex, its crenellated parapet rings it.
- **Slate**: GBVet's slate triangle is given to the painter as `tiles`
  (`prodkit.VET_TILES`), so the caps stay charcoal slate instead of turning to stone.

## Fit and status

- `V1` 604 -> 3,792 triangles; footprint EA's; height unchanged; 108/108 checks.
- Own texture `GBVW1` (levels.py letter W). No cloth, no lights (a level mesh).
- Lifecycle: construction, really damaged and rubble carry V1; D1 derived.
