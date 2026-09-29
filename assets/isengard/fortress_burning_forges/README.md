# Isengard fortress burning forges (`IsengardFortressCitadel`)

Stub from `python3 -m sagekit new isengard`: nothing redesigned yet (`design()` returns no solids).

- Source model `IBFBForges`, target mesh `IBFBFORGESA` (957 triangles), sheet `IBFortress.tga` -> own `IBFortresL.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_statues`.
- Covers the Draw module `ModuleTag_DrawBurningForges`.
- EA's body measured: `python3 -m sagekit measure isengard/fortress_burning_forges` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
