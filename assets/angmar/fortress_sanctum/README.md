# Angmar fortress sanctum (`AngmarFortressCitadel`)

Stub from `python3 -m sagekit new angmar`: nothing redesigned yet (`design()` returns no solids).

- Source model `KBFSanctum`, target mesh `KBFSANCTUM` (1452 triangles), sheet `KBFortressB.tga` -> own `KBFortressP.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_monument`.
- Covers the Draw module `ModuleTag_SanctumDraw`.
- EA's body measured: `python3 -m sagekit measure angmar/fortress_sanctum` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
