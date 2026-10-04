"""Player-colour cloth for unit recipes (the construction workers, docs/UNITS.md).

The game tints a unit's sheet with the player colour where EA's house mask says so. The framework
tiles EA's mask under the atlas' left half, where EA's sheet repeats 4 x 4, so a new piece takes
the player colour when its UVs sample a patch of EA's sheet that the mask covers fully: `HC` is
that piece tag. A recipe picks the patch (`patch_uv(box)`, in the sheet's own pixel grid) in a
tile EA's body does not sample, and `check_patch` proves the mask covers it.

`drape` makes thin two-faced cloth (capes, sashes, hoods) from rows of points, each row on its
own bone, so the cloth stretches and bends with the body (`face_bones`).
"""
from ..formats import w3dpose as P
from ..formats.w3d import NORMALS, STAGE_TEXCOORDS, VERTICES
from .mesh import uv_for
from .paint import raw

HC = 99                         # the player-colour piece tag


def patch_uv(box, sheet=256, tile=(0, 0)):
    """uv_for with HC mapped onto `box` (x0, y0, x1, y1 in EA's `sheet`-pixel grid) inside tile
    (column, row) of the left half (4 x 4 tiles of 256 atlas pixels)."""
    x0, y0, x1, y1 = (c * 256 / sheet for c in box)
    tx, ty = tile[0] * 256, tile[1] * 256

    def uv(tag, u, v):
        if tag != HC:
            return uv_for(tag, u, v)
        return ((tx + x0 + (x1 - x0) * u) / 2048, 1 - (ty + y0 + (y1 - y0) * (1 - v)) / 1024)
    return uv


def check_patch(mask_file, box):
    """Assert EA's mask is fully player colour over `box` (its own pixel grid)."""
    mask = raw(mask_file)
    size = int(round((len(mask) // 4) ** .5))
    x0, y0, x1, y1 = box
    assert all(mask[(y * size + x) * 4 + 3] == 255 for y in range(y0, y1) for x in range(x0, x1)), \
        "the player-colour patch leaves EA's mask"


def face_bones(m, points, bones, tag, uvs):
    """Mesh.face with a bone per point (a skin only): a face spanning two bones stretches between
    them as the body bends, instead of tearing apart like rigid pieces on each bone."""
    a, b, c = points[:3]
    e, f = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
    n = (e[1] * f[2] - e[2] * f[1], e[2] * f[0] - e[0] * f[2], e[0] * f[1] - e[1] * f[0])
    off = len(m.verts)
    for p, bone, (u, v) in zip(points, bones, uvs):
        k = m._bone(bone)
        m.verts.append((0, [(0, 1)], P.invert(m.skeleton.rest[k]), k,
                        {VERTICES: p, NORMALS: n, STAGE_TEXCOORDS: m.uv_for(tag, u, v)}))
    m.tris += [((off, off + i, off + i + 1), m.original.surface[0]) for i in range(1, len(points) - 1)]


def drape(m, rows, tag=HC, depth=.14, axis=0):
    """Cloth of two faces `depth` apart along `axis` (0 x, 1 y, 2 z): rows [(bone, [point per
    column])] in order. Each row follows its own bone; on a skin the band between two rows on
    different bones stretches with the body (a rigid mesh takes its one bone). The tag's tile (or
    patch) is laid once across the whole cloth, so its weave runs on without seams."""
    n, cols = len(rows) - 1, len(rows[0][1]) - 1
    for r, ((upper, top), (lower, low)) in enumerate(zip(rows, rows[1:])):
        bones = [upper, upper, lower, lower] if m.skinned else [lower] * 4
        for i in range(cols):
            quad = [top[i], top[i + 1], low[i + 1], low[i]]
            uv = [(i / cols, 1 - r / n), ((i + 1) / cols, 1 - r / n), ((i + 1) / cols, 1 - (r + 1) / n),
                  (i / cols, 1 - (r + 1) / n)]
            inner = [tuple(c + (depth if k == axis else 0) for k, c in enumerate(p)) for p in quad]
            face_bones(m, quad, bones, tag, uv)
            face_bones(m, inner[::-1], bones[::-1], tag, uv[::-1])
