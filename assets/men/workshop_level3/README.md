# Men siege workshop, level 3 (`V2` of `GBWorkshop`)

Chained on `men/workshop_level2` ([`levels.py`](../levels.py)); the chain's last link, so
its `gbworkshop.w3d` ships. Own texture `GBVW2`; slate hints as level 2.

## What changed

EA's V2 is a chamfered-square storey on each gate tower, two arched windows a face, a slate
dome and a thin stone spike. Now, like the citadel's towers:

- a sable band with five gilt stars round each storey's foot, on every face;
- voussoir surrounds with keystones and sills round EA's sixteen windows;
- a corbelled bartizan on each of the four chamfers (slit windows, steel-banded cornice, slate
  spirelet, steel spike);
- the dome: a steel eave band, ribs up its hips and middles, a lantern cupola where EA's spike
  stood (cleared: `clear`), a steel mast, gilt orb and spike.

## Kept clear

- The bartizans stand 0.6 past the storey's faces (`footprint_margin` 0.8: the building's
  collision is the INI's).

## Status

Installed with the Men pack. `V2` 1,304 -> 7,904 triangles, height 45.5 -> 51.2 (+12.6 %), 93/93
checks. Construction and rubble carry V2; damaged is derived. Really damaged (`GBWorkshop_D2`)
does not carry V2: V2 and the damaged body are painted from different sheets.
