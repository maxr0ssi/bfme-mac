# Isengard fortress wizards tower (`IsengardFortressCitadel`)

Stub from `python3 -m sagekit new isengard`: nothing redesigned yet (`design()` returns no solids).

- Source model `IBFWTower`, target mesh `IBFWTOWER` (1572 triangles), sheet `IBFortress.tga` -> own `IBFortresN.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_monument`.
- Covers the Draw module `ModuleTag_DrawWizardsTower`.
- EA's body measured: `python3 -m sagekit measure isengard/fortress_wizards_tower` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
