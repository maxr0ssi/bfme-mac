# Men siege workshop (`GondorWorkshop`, `ArnorWorkshop`)

Draft for review, not installed. Renders: `build/assets/men/workshop/renders/compare_*.png`
(level 1: V1 and V2 hidden). The level-up meshes are chained on this recipe:
[`workshop_level2`](../workshop_level2/README.md) (V1) and
[`workshop_level3`](../workshop_level3/README.md) (V2); rebuild them after this one.

## What changed

EA's gatehouse is kept whole (the square towers, grilled windows, corbelled upper storeys with
their arcaded friezes, the moulded arch, the crenellated bridge). Added, in the citadel's kit:

- **Crowns**: a crenellated parapet round each tower top, a pinnacle with a steel orb on every
  corner, a steel mast with a gilt orb in the middle. At level 2 EA's slate caps (V1) rise inside
  the parapets and the mast is their finial; at level 3 the domed storeys (V2) close over them.
- **Gate**: a nine-stone voussoir archivolt with a raised keystone round EA's arch, front and yard.
- **Crests** over the bridge's middle merlons, front and yard: an entablature with a sable frieze
  and three gilt stars, a pediment with the White Tree on sable, raking cornices, a winged-helm
  crest and end pinnacles.
- **Towers**: pediments on consoles over the front and outer windows, paired corbels under the
  upper storeys' overhang at every corner, a battered plinth.
- **Banners**: two house-colour banners on the yard faces of the upper storeys (cap 2).

## Fit and status

- `GBWORKSHOP1` 732 -> 5,276 triangles; footprint EA's; height 53.1 -> 63.6 (+19.7 %, the mast's
  spike); 108/108 checks. Construction, really damaged and rubble rebuilt along EA's pieces; D1
  derived.
- Own texture `GBWorkshopH`; the damaged body's sheet `GBWorkshop1D` gets `GBWorkshoH1D`
  (`prodkit.same_length_variants`: the framework's `GBWorkshopH1D` is a letter too long for
  W3D's in-place rename).
- Banner cloth shows after `sagekit house men` (integration pass).
- `prodkit.py` holds the production group's helpers (same-length variants, a banner on closed
  consoles, pointed arches, slate hints for GBVet, `closed` for EA's single-plane walls).
