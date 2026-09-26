# Elves fortress mystic fountains (`ElvenCitadel`, `ModuleTag_DrawMysticFountains`)

Eight half-round basins hung on the ring's faces (toward +-45, +-67.5, +-112.5, +-157.5 degrees), a
swan in each pouring water. Own texture `EBFortresK.tga` (DXT5). EA's water meshes (`EBFMFOUNT2`,
`EBFMFOUNT3`) are untouched.

## What changed (body `EBFMFOUNT1`, healthy)

- **Gilt lips.** A gilt bead sweeping round each basin's lip from wall to wall (radius 6.4, inside
  the rim: the +-45 basins set the footprint's x 42.2).
- **Starlight lanterns.** A small crystal lantern standing on each end of every lip, by the wall.
- **Banners.** A leaf banner (5.8 x 6.4, house colour) over the swan on the six gable faces, between
  the swan's head (z 31.5) and EA's frieze; the faces toward +-45 already carry the fortress's ring
  banners, which end over their swans.

## Numbers

- Footprint unchanged. Height (from the model's foot, z 10.57): 20.93 -> 28.81 (+37.6 %),
  `max_z_growth = 0.40` as the Dwarven old castle hub: under the 20 % default the top would be z 35.7,
  with no room for cloth between the swans' heads and the top.
- Triangles 1,520 -> 4,136 (budget 5,000). Texel density median 23.8 px/unit.
- Checks: 97/97. House colour: 72 cloth faces -> `EBHCFortress`.
- Lifecycle: `EBFMFount_A`, `_D2` and `_D3` carry the redesign.

## Night lights

No night meshes in EA's model; none declared.

## Status

| Part | Healthy | Construction | Damaged | Really damaged / rubble |
|---|---|---|---|---|
| basins (`EBFMFount`) | built, checks pass, **awaiting review** | ours (`_A`) | texture swap | ours (`_D2`, `_D3`) |

The renders draw only the basins' own cloth from the shared `EBHCFortress` (the fortress's banners
no longer float round them).
