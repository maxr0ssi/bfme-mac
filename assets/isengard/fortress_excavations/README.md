# Isengard fortress excavations (`IsengardFortressCitadel`)

Stub from `python3 -m sagekit new isengard`: nothing redesigned yet (`design()` returns no solids).

- Source model `IBFExcav`, target mesh `IBFEXCAV` (875 triangles), sheet `IBFortress.tga` -> own `IBFortresJ.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_barrels`.
- Covers the Draw module `ModuleTag_DrawExcavations`.
- EA's body measured: `python3 -m sagekit measure isengard/fortress_excavations` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
