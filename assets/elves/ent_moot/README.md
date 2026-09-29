# Elven Ent moot (`ElvenEntMoot`)

Model `FBEntmoot`, mesh `FENTMOOT`, own texture `FBEntmooH.tga` (from `FBEntmoot.tga`, EA's cut-out
alpha kept, no normal map; variants `_snow`, `_D`, `_D2`). `Tier.STANDARD`. EA's measurements are
in `building.py`. It stays a clearing: no gold, lanterns or cloth.

## What changed

- **Standing stones**: eight rough slabs fill the gaps in EA's ring of eleven boulders, so the ring
  reads whole; the tallest pair (28-29) flanks the horn's root like a gate. Each swells, then draws
  in to a blunt sloping top, and leans a little toward the middle.
- **Fallen stones**: one or two at each stone's foot.
- **Paint**: the atlas's bark grain (never ashlar) in the natural rock ramp, warmed and darkened to
  match EA's boulders (`decals()`), with moss.
- **Banners**: none; EA's house-colour model here (`RBHCEntMoot`) is flowers.

## Kept clear

- The middle, where the Ents gather, and the four places the upgrades plant trees
  (`TreeLothlorien08EntMoot`): `design()` refuses a stone within 14 of a tree.

## Status

Installed with the Elven pack. 381 -> 1,205 triangles, height and footprint unchanged (the horn
stays the top), 75/75 checks. Construction and rubble are rebuilt along EA's pieces; damaged and
really damaged derive the new body.
