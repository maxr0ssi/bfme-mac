# Men siege workshop, level 3 (`V2` of `GBWorkshop`)

Draft for review, not installed. Chained on [`workshop_level2`](../workshop_level2/README.md);
this is the chain's last link, so its `gbworkshop.w3d` is the one that ships. Renders:
`build/assets/men/workshop_level3/renders/`.

## What changed

EA's V2 is a chamfered-square storey on each gate tower, two arched windows a face, a slate
dome and a thin stone spike. Now, like the citadel's towers:

- a sable band with five gilt stars round each storey's foot, on every face;
- voussoir surrounds with keystones and sills round EA's sixteen windows;
- a corbelled bartizan on each of the four chamfers (slit windows, steel-banded cornice, slate
  spirelet, steel spike);
- the dome: a steel eave band, ribs up its hips and middles, a lantern cupola where EA's spike
  stood (cleared: `clear`), a steel mast, gilt orb and spike.

## Fit and status

- `V2` 1,304 -> 7,904 triangles; height 45.5 -> 51.2 (+12.6 %); the bartizans stand 0.6 past
  the storey's faces (`footprint_margin` 0.8: the building's collision is the INI's); 93/93
  checks.
- Own texture `GBVW2`; slate hints as level 2.
- Lifecycle: construction and rubble carry V2; the really damaged model is left as level 2
  built it (the lifecycle step: V2 and the damaged body use different sheets).
