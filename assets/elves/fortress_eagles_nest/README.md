# Elves fortress eagle's nest (`ElvenCitadel`, `ModuleTag_EaglesNestDraw`)

The pillar in the courtyard's middle that carries the Great Eagle's perch. Own texture
`EBFortresJ.tga` (DXT5). EA's eagle itself (`EBFE`, `ModuleTag_DrawEagle`) is not part of this recipe.

## What changed (body `EBFENEST1`, healthy)

- **Shaft banners.** A leaf banner (7 x 30, house colour) on each of the shaft's four faces, hung
  from under the head (rod z 101.9) and ending at z 71.9; the rods sit in the head's plan, the cloth
  clear of the tapering shaft.
- **Head.** A silver-and-enamel pointed arch frame (leaf-tip ogee 0.25) round each of EA's four
  recesses (12 x 18.5), and a moulded cornice under the perch (z 122.3..124.25) with a starlight
  crystal lantern on each corner (to z ~134, under the eagle, which sits from z 137.2).
- **Shaft foot.** A knotwork band (silver on sea-green enamel, gilt beads) round the octagonal shaft
  where EA's pointed wedges meet (z 52.5..54.6); silver collars with an enamel fillet on the foot's
  two steps (z 13.67, 24.02).

## Numbers

- Footprint unchanged (|x|, |y| 14.43); height unchanged (141.01: EA's perch stays the top).
- Triangles 718 -> 2,910 (budget 5,000). Texel density median 12.0 px/unit.
- Checks: 70/70. House colour: 48 cloth faces -> `EBHCFortress`.
- EA's material draws `EBFENEST1` with alpha test off, so its sheet's cut-outs never show; the alpha
  agreement is information only (sagekit/blender/alpha.py), and the perch's extra texel emphasis
  that served that check is gone.
- Lifecycle: `EBFENest_A` and `_D2` carry the redesign; `_D3` (rubble) is left to EA by the
  lifecycle step (its sky check: our faces' backs open to the sky).

## The eagle's colour

The flat sheet recolour (`sagekit sheets`) took EA's eagle (painted on `EBFortress.tga`, drawn by
`EBFE`) for metal and turned it bright gold. `assets/elves/atlas.py` now declares a `keep` region
(wing, talons, head and body rects) and `sagekit/paint/sheets.py` leaves the non-stone texels there
as EA painted them; the stone between the feathers still recolours. Tested on a scratch copy of the
sheet only (nothing written to `build/assets/elves/_sheets`, nothing installed).

## Night lights

No night meshes in EA's model; none declared.

## Status

| Part | Healthy | Construction | Damaged | Really damaged | Rubble |
|---|---|---|---|---|---|
| pillar (`EBFENest`) | built, checks pass, **awaiting review** | ours (`_A`) | texture swap | ours (`_D2`) | EA's (lifecycle below standard) |
