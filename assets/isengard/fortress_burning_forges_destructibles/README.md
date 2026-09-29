# Isengard fortress burning forges destructibles (`IsengardFortressCitadel`)

Stub from `python3 -m sagekit new isengard`: nothing redesigned yet (`design()` returns no solids).

- Source model `IBFBForgB`, target mesh `IBFBFORGES` (971 triangles), sheet `IBFortress.tga` -> own `IBFortresM.tga`, DXT5 (EA's cut-out alpha kept).
- Role fortress_upgrade; nearest Dwarven recipe `fortress_statues`.
- Covers the Draw module `ModuleTag_DrawBurningForgesDescrutbiles`.
- EA's body measured: `python3 -m sagekit measure isengard/fortress_burning_forges_destructibles` -> `work/measure.json`.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
