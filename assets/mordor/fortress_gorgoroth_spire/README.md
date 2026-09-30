# Mordor fortress gorgoroth spire (`MordorFortressCitadel`)

Stub from `python3 -m sagekit new mordor`: nothing redesigned yet (`design()` returns no solids).

- Source model `MBFEWEye`, target mesh `MBFEWEYE` (1060 triangles), sheet `MBFortress.tga` -> own `MBFortresD.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_statues`.
- Covers the Draw module `ModuleTag_DrawGorgorothSpire`.
- EA's body measured: `python3 -m sagekit measure mordor/fortress_gorgoroth_spire` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
