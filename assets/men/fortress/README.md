# Men citadel (Gondor) - third pass

Staged for review, not installed. Review: `build/assets/men/fortress/review.html` and the sheet
`build/assets/men/fortress/renders/citadel_review.jpg`.

Max on the second pass: "men needs lots of work look at dwarves i want the extra small details
this is quite boring shaped in comparison". Its silhouette was EA's, its reliefs 0.7 deep and its
palette grey on grey. This pass keeps EA's body whole and changes the silhouette the Dwarven way,
with a kit of its own (`assets/men/shapes.py`, `MenShapes`) and paint of its own (`assets/men/paint.py`).

## What changed

- **Tower crowns** (`crown.py`): a machicolated gallery round each shaft top (two-step corbels,
  a slab 2 out, parapet, square merlons with capstones), its front a black band of painted silver
  seven-pointed stars (`StarBand`); four corbelled bartizans with slit windows and slate spirelets;
  pilasters up the chamfers from EA's corner buttresses into them.
- **Domes**: steel eave band, twelve steel ribs, a lantern cupola, a steel mast, gilt orb and
  spike to z 129 (EA 116.65, +10.6%).
- **Walls**: crenellated parapets on the side and back walls, a string course, pinnacles over
  EA's buttresses.
- **Gatehouse** (`gate.py`): pilasters, eleven voussoirs and a keystone, portcullis teeth, a
  black frieze with the seven gilt stars, a slate-roofed pediment with the White Tree, a
  winged-helm crest and corner pinnacles.
- **Heraldry**: four house-colour banners (White Tree, steel rods, gilt knobs) on the front
  towers, hung 1 out, under the flame hardware; steel-framed White Tree shields on the back towers.
  The cloth goes to an own copy, `GBHCFortress2` (`house_shared` returns True: Arnor draws
  `GBHCFortress` too).
- **Palette** (`style.py`): brighter limestone, charcoal slate, bright steel, sable enamel,
  muted old gold. No Elven ivory/mithril/gold.

## Fit and status

- `GBFORTRESS` 1,458 -> 14,853 triangles (budget 15,000); footprint unchanged; 109/109 checks.
- Own names kept: `GBFortress2`, `GBFortressH`; Arnor and neutral stay on EA's models.
- Clear of the doors' sweep (x 50.5..67, |y| < 15.45, z < 41), the oil outlets, the flame
  hardware and the banner pennants (z 105..112 at the poles). The front towers' galleries stop at
  x 44.3 on the face toward the healing house, whose corner block and spirelet stand there.
- The pediment stands in front of the healing house's lower arcade when that upgrade is built
  (`renders/compare_upgate.png`): a judgement call for Max.
- Construction, heavy damage and rubble built along EA's pieces; no night meshes (EA has none).
- Upgrade composites were rendered with a review script outside the pipeline (EA's upgrade
  models from `reference/`); particles and the oil crew are not simulated.

```sh
python3 -B -m sagekit build men/fortress --from geometry --to geometry
python3 -B -m sagekit house men
python3 -B -m sagekit build men/fortress --from bake
```
