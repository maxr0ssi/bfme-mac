# Elves fortress eagle's nest (`ElvenCitadel`, `ModuleTag_EaglesNestDraw`)

The pillar in the courtyard's middle that carries the Great Eagle's perch. Own texture
`EBFortresJ.tga` (DXT5). EA's eagle itself (`EBFE`, `ModuleTag_DrawEagle`) is not part of this recipe.

## Design (2026-09-26, the citadel's standard)

Reworked to the approved citadel's recipe (`assets/elves/fortress/README.md`): EA's pillar kept
whole (no face removed), a handful of additions in the citadel's silver and gold, and no cloth.
The pillar stands among the mallorn trees, so its head (over the canopy at z 99 and the tree-houses
at 122.9) is where the work shows.

## What changed (body `EBFENEST1`, healthy)

- **Arch frames.** A silver frame (leaf-tip ogee 0.25, slate reveal) round each of EA's four head
  recesses (12 x 18.5).
- **Sill band and cornice.** A silver sill band round the head's foot under the arches (z
  102.1..103.65) and a moulded silver cornice under the perch (z 122.3..124.25).
- **Crystal lanterns.** The citadel's ring lantern, smaller, on each of the cornice's corners: a
  short silver post, a starlight crystal in a gilt cup, a gilt leaf on the tip (z 134.7, under the
  eagle, which sits from z 137.2; the perch's roots and beams run along the axes, clear of them).
- **Necking.** A silver astragal round the shaft where it flares into the head (z 94.8..96.8) and a
  ring of eight gilt leaves hanging from it down the shaft's faces (6.6 on the axis faces, 4.2 on
  the diagonals): the leaf capital the plain shaft never had.
- **Shaft foot** (mostly behind the citadel's ring): a knotwork band (silver on sea-green, gilt
  beads) where EA's pointed wedges meet (z 52.5..54.6), silver collars on the foot's two steps.
- **Removed from the first pass:** the four shaft banners (7 x 30, one per face) and the enamel
  fillets. **Banners: 0**, so the citadel's shared `EBHCFortress` keeps its own four.

## Numbers

- Footprint unchanged (|x|, |y| 14.43); height unchanged (141.01: EA's perch stays the top).
- Triangles 718 -> 3,984 (budget 5,000).
- Checks: 86/86. House colour: no cloth.
- EA's material draws `EBFENEST1` with alpha test off, so its sheet's cut-outs never show; the alpha
  agreement is information only (sagekit/blender/alpha.py).
- Lifecycle: `EBFENest_A`, `_D2` and `_D3` carry the redesign. Added ornaments retain their
  normally buried backs and caps, keeping them closed when the collapse turns them over.
  The earlier open ornaments failed the rubble sky check; trying smaller split thresholds did
  not fix it. Closing the actual solids did, with the validation limits unchanged.

## The eagle's colour

`assets/elves/atlas.py` declares a `keep` region (wing, talons, head and body rects) so the sheet
recolour (`sagekit sheets`) leaves EA's eagle (painted on `EBFortress.tga`, drawn by `EBFE`) as EA
painted it; the stone between the feathers still recolours.

## Night lights

No night meshes in EA's model; none declared. The crystals are day-lit only.

## Status

| Part | Healthy | Construction | Damaged | Really damaged | Rubble |
|---|---|---|---|---|---|
| pillar (`EBFENest`) | built, checks pass, **awaiting review** | ours (`_A`) | texture swap | ours (`_D2`) | ours (`_D3`) |

Renders: `build/assets/elves/fortress_eagles_nest/renders/compare_{rts,close,ingame}.png`.
