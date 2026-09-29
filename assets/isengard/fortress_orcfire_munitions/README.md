# Isengard fortress orcfire munitions (`IsengardFortressCitadel`)

Stub from `python3 -m sagekit new isengard`: nothing redesigned yet (`design()` returns no solids).

- Source model `IBFOrcfire`, target mesh `IBFORCFIRE` (920 triangles), sheet `IBFortress.tga` -> own `IBFortresG.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_barrels`.
- Covers the Draw module `ModuleTag_DrawOrcfireMunitions`.
- EA's body measured: `python3 -m sagekit measure isengard/fortress_orcfire_munitions` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
