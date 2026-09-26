# Elven wall hub (`ElvenCastleWallHub`)

Model `EBWallRmprtN` (the game draws it healthy as `EBWallRmprtN_A`), redesigned mesh
`EBWALLRMPRTN`, `Tier.STANDARD`, painted from `EBFortress.tga` onto its own textures
`EBFortresC.tga` / `EBFortresC_NRM.tga` (+ `_D`, `_snow`, `_U` variants), DXT5 (EA's cut-out
alpha kept).

EA's hub is a round tower (a 20-gon of corner radius 22.5..22.59) where wall segments meet from any
side: six lancet windows between piers, a V cornice, a sloped rim to a walk at 51.45 and EA's
lattice dome (`SPHERE01`, its own mesh, r 20.65, z 51.06..67.6). It gets the walls' crown at the
segments' heights, so the parapet line runs on through the hub, and the segments' windows.

## What changed (body, healthy)

- **Crown** (the shared profile, [wall_segment/README.md](../wall_segment/README.md)): the core,
  the filigree band, the silver coping and two lancet merlons per 20-gon side round the rim (face
  line: a 20-gon of corner radius 22.3; the coping reaches in over the dome's foot, which rises out
  of its top).
- **Windows:** a silver arch frame with sea-green reveals round each of the six lancet windows
  (planar frames on the window's bent face: 0.95 proud at the jambs, flush at the apex; no finial,
  EA's hood sits there).
- **Banners:** a leaf banner in the player's colour hung in each window recess (6), cloth to our
  house-colour model `EBHCWallRmprtN`, Draw tag `ModuleTag_Draw_HCWallHub`.
- **Lanterns:** five crystal lanterns on the coping at the dome's foot.
- **Dome:** EA's, untouched (a separate mesh). Its top (67.6) is above this model's height limit
  (53.05 x 1.2 = 63.66), so it cannot be covered or replaced here; see *Open decision*.

Nothing passes the footprint (x +-24.09, y +-22.83): the crown's widest point, the gilt beads at
the 90-degree corner, is at y 22.79. Height 53.05 -> 60.6 (+14.2 %, limit 20 %), 374 -> 6,194
triangles (72 cloth faces moved to `EBHCWallRmprtN`). `checks`: 71/71 pass.

## Reuse

The pieces are static methods of `WallHub` (`crown`, `windows`, `lanterns`), for
`elves/fortress_wall_hub` (EA's `EBEFWHub` carries the same body as `EBWALLRMPRTN01`).

## Source and objects

- `source = "EBWallRmprtN"`: the healthy state draws `EBWallRmprtN_A`, the construction model at
  rest, but its file carries the construction animation and Blender imports its first frame (the
  body 70 units below the ground: empty renders, bakes in the wrong place). `EBWallRmprtN` is the
  same body, static; `_A` takes ours through derive.
- `is_body` leaves out `ElvenCastleWallHubExpansion`: that object also shows `EBWallRmprtN_A`
  while it is built, so without this the hub would ship the expansion's `EBEFWHub` models,
  lifecycle and house draw, which are `elves/fortress_wall_hub`'s.

## Status (`python3 -m sagekit inventory elves/wall_hub`)

| Part | Healthy | Construction (`_A`) / damaged (`_D1`) / snow / stonework | Really damaged (`_D2`) | Collapsing (`_D3`) |
|---|---|---|---|---|
| body (`EBWallRmprtN`) | done, rendered, not installed | derived: our body | rebuilt around our body | lifecycle step's call (see the report) |

## Open decision

EA's dome is a round lattice dome (not onion or Moorish), outside the redesigned mesh. Keeping it
is the default. The alternatives need Max: raise `max_z_growth` for this hub so a swept slate roof
can close over it (about 30 %), or leave it and add gilt leaf ribs on it within the 63.66 limit.

## Night lights

TODO, as the segment: no night meshes or `NightWindowName` in EA's hub. The lanterns are ready
for it.
