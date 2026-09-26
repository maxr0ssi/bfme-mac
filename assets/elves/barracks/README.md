# Elves barracks (`ElvenBarracks`)

Model `NBElvnBarx_SKN` is skinned, with a separate skeleton `NBElvnBarx_SKL`. Arnor's Elven
barracks draws the same model family, so this recipe ships an own copy, `EBElvnBarx_SKN`
(`own_model`). Only the Elven Draw modules are repointed to it; Arnor keeps EA's model.

The redesigned mesh is `NBELVNBARXA`: the hall, its porches and the walled yard. It gets its own
texture, `nbelvnbarH.tga` / `nbelvnbarH_NRM.tga`, plus the variants `nbelvnbarH_D` and
`nbelvnbarH_Snow`. This is a two-sheet build: EA's `nbelvnbarx.tga` for the old faces, and the
fortress atlas for the new ones.

Nothing else changes: the great mallorn (`V1`, `V1A`), the level-3 crown (`V2`), the weapon racks
and warriors, and the bones.

## What changed (body, healthy)

- **Hall front** (the yard side, facing the camera):
  - a blind arcade of six lancet windows. Each has EA's lattice glass on a slab, a pointed silver
    frame with an enamel reveal, and a silver sill;
  - five slender columns with gilt leaf capitals between the windows, carrying the eave;
  - a knotwork band (silver knots on sea-green enamel between gilt beads) along the plinth;
  - a leaf banner on each corner pier.

  The front is flat work (at most 0.8 proud) where EA's racks lean on the wall.
- **Ridge**: a crest of nine gilt leaf finials, alternating tall and short. It stays clear of the
  level-3 crown (`V2`, y >= 12.3).
- **Porches**:
  - a crystal lantern on each of the four porch pedestals, under the porch arch;
  - a tall crystal lantern on a gilt rod from each gable's swan-neck horn, where EA hangs its night
    lantern.
- **Yard**:
  - a balustrade (turned balusters under a silver rail) along the tops of the front, west and east
    walls;
  - a leaf pennant flying from each of the two obelisks.
- **Paint**: the faction style, automatic. EA's timber reads as pale silvered wood, and the
  knotwork panels as enamel.

## Player colour

The cloth (two banners, two pennants) goes to the house-colour model and takes the player's colour.
EA's `NBHCElvnBarx` is also drawn by Arnor's Elven barracks, so the house step ships an own copy,
`EBHCElvnBarx` (EA's file renamed, our cloth in place of EA's flag), shown by the Elven barracks'
Draw module only (`Building.own_house_copy`); Arnor keeps EA's flag.

## Night

Starlight panes on:

- the two horn lanterns (where EA's warm night lanterns hung);
- the two east porch lanterns;
- five of the six front windows. The sixth is behind a bow of EA's rack, whose pane would face the
  bow.

The panes have no halos: a halo would drape over the sills, and a lantern's crystal has no surface
round it for one. Instead each horn lantern hangs in a free glow card like EA's (24 across, flat,
`Light.glow`), where EA's glow cards (`N_GLOW`) were. EA's night-only lanterns (`N_WINDOW`) are
replaced by our lanterns' panes (sagekit/nightlights.py).

## Numbers

- **Footprint:** unchanged.
- **Height:** unchanged (the crest's tips stay under the gable horns, z 58.6).
- **Triangles:** `NBELVNBARXA` 2,211 -> 9,879 (budget 15,000). Most of it is gilt leaves and the
  balustrade.
- **Checks:** 168/168.

## Status

| Part | Healthy | Construction / damaged / rubble | Snow |
|---|---|---|---|
| body (`EBElvnBarx_SKN`) | built, **awaiting review** | lifecycle step (see `work/lifecycle.json`); `_D1` derived with `nbelvnbarH_D` | `nbelvnbarH_Snow` painted |
| cloth (`EBHCElvnBarx`, own copy) | 2 banners, 2 pennants | | |

## Notes

- EA's `nbelvnbarx_nrm.tga` is a 32-bit TGA; sagekit keeps its depth (sagekit/paint/imageio.py).
- `motifs.py` holds the motifs the production buildings share: lancet window, barge board,
  coronet, hanging lantern and crystal night light.
