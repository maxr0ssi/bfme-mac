# Isengard fortress excavations destructibles (`IsengardFortressCitadel`)

Stub from `python3 -m sagekit new isengard`: nothing redesigned yet (`design()` returns no solids).

- Source model `IBFExcavB`, target mesh `IBFEXCAVB` (374 triangles), sheet `IBFortress.tga` -> own `IBFortresK.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_barrels`.
- Covers the Draw module `ModuleTag_DrawExcavationsDestructibles`.
- EA's body measured: `python3 -m sagekit measure isengard/fortress_excavations_destructibles` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
