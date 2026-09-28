# Men fortress Houses of Healing (`MenFortressCitadel`, UPGRADE_HOUSE_OF_HEALING)

Staged for review, not installed. Renders: `build/assets/men/fortress_house_of_healing/renders/`;
on the citadel, behind the gate pediment: `build/assets/men/_group_addons/compare_citadel_upgate.png`.

## What changed

EA's hall kept whole (arcade, stepped gable, six robed statues, knotwork, the White Tree shield,
the barrel vault), dressed from `fortress_ivory_tower/citadel_motifs.py`:

- a black frieze of silver stars under a new moulded cornice across the front. The citadel's
  pediment stands in front of the lower arcade, and its winged crest now shows against the frieze.
- a raised, mitred coping up every step of the gable; the seven gilt stars of Elendil over the niche;
  a stone acroterion and steel-and-gilt finial on the apex
- steel ribs over the slate vault, a crest of steel spikes along its ridge, a lantern flèche on the
  ridge (arcaded lantern, slate spire, gilt orb, spike)

## Fit and status

- `GBFHEAL` 552 -> 1,984 triangles (budget 6,000); height 59.7 -> 70.5 (+18.1 %).
- `footprint_margin = 1.0`: the cornice's nose reaches x 49.66 (EA 48.75), still behind the
  pediment (x 50.2) and inside the citadel's footprint. Nothing passes |y| 26.7 (the towers' faces).
- Checks 82/82 only with the two framework fixes described in the Ivory Tower's README (no
  hierarchy, empty container name). No banner, for the reason the Ivory Tower's README gives.
- Lifecycle: construction, D2 and D3 rebuilt along EA's pieces.
