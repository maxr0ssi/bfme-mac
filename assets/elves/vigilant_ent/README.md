# Elven vigilant ent (`ElvenVigilantEntExpansion`)

Model `EBFVEntHol`, redesigned mesh `EBFVENTBUD`, `Tier.STANDARD`, painted from the faction sheet
`EBFortress.tga` onto its own textures `EBFortresN.tga` / `EBFortresN_NRM.tga` (DXT5: EA's cut-out
alpha kept; + `_D`, `_snow`, `_U` variants).

The ent's planted ring on the fortress's pad: a twelve-sided planter round an earth bed (centre
(-1.9, 0), rim 2.95 wide at z 5.76), the arm back to the fortress over the expansions' pointed
arch, and a gabled slab across the arm's end. The ent stands in the bed; nothing new enters it
(everything stands on the rim or on the arm), and the footprint and height are EA's.

## What changed (body, healthy)

- **Balustrade:** a moonstone balustrade round the rim (turned balusters every 1.7, silver rail),
  on every side but the arm's.
- **Lantern posts:** eight square newels on the rim's corners (the rail runs into them), each
  carrying a slender leaf-capital column and a Lórien crystal lantern in a gilt cup (top 19.5).
- **Arch:** the pointed silver frame round the arm's arch on both faces (sea-green enamel
  reveals, a gilt leaf over the point), the expansions' shared frame (`floodgate/pad.py`); the
  opening is untouched.
- **Banners:** three leaf banners in the player's colour: on the arm's end (4.2 x 21, facing the
  RTS camera) and on the slab's two faces (3.0 x 17). The cloth goes to our house-colour model
  `EBHCFVEntHol` (Draw tag `ModuleTag_Draw_HCVigilantEnt`, from the style's `house_template`).
- **Beacon:** a crystal lantern on the arm's end, over the ent.
- **Paint:** the faction style (moonstone, silver mouldings, gilt leaf, sea-green enamel).

Footprint unchanged (x -43.91..19.28, y -21.18..21.18), height 53.0 -> 53.0 (+0 %),
260 -> 9,600 triangles (the balusters and columns are most of it). `checks`: 92/92.

Night lights: EA's model has no night meshes and the INI names none (`NightWindowName`), so the
crystals stay unlit at night; lighting them would need night meshes EA's object does not have.

## Status (`python3 -m sagekit inventory elves/vigilant_ent`)

| Part | Healthy | Damaged / snow / stonework | Construction (`_A`), really damaged (`_D2`), rubble (`_D3`) |
|---|---|---|---|
| body (`EBFVEntHol`) | done, rendered, not installed | our body on the variant sheets | all three ours (lifecycle: our body split along EA's pieces), rendered in `renders/lifecycle/` |
