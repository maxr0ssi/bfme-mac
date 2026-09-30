# Mordor fortress fire arrows (`MordorFortressCitadel`)

Stub from `python3 -m sagekit new mordor`: nothing redesigned yet (`design()` returns no solids).

- Source model `MBFFArrows`, target mesh `MBFFARROWS` (376 triangles), sheet `MBFortress.tga` -> own `MBFortresB.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_barrels`.
- Covers the Draw module `ModuleTag_DrawFireArrows`.
- EA's body measured: `python3 -m sagekit measure mordor/fortress_fire_arrows` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
