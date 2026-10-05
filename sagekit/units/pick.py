"""Click picking: the volume the game tests a unit's clicks against, and a box that covers what we draw.

What the engine does (game.dat of RotWK 2.01, read 2026-10-04; EA's released Generals WW3D source,
hlod.cpp and W3DScene.cpp, has the same code without BFME's pick flag):
  - RTS3DScene::castRay 0x471a5b: for each selectable render object, a ray/sphere test against
    Get_Bounding_Sphere (vt+0x104), then a RayCollisionTestClass with byte +0x42 set to 1
    (0x471c7f) and robj->Cast_Ray (vt+0xf0).
  - HLodClass::Cast_Ray 0x59c680: with +0x42 set, the first sub-object of the top LOD whose class is
    an oriented box (Class_ID 0x1b, OBBoxRenderObjClass) answers the ray alone (0x59c6e5, a tail
    call). With no oriented box, every sub-object is ray-tested: an axis-aligned box (W3D box
    attribute ALIGNED) stays aligned to the world axes at its unrotated offset, and a skin tests
    its stored vertices, which sit in their bones' spaces, not where the body is drawn.
  - HLodClass::Update_Obj_Space_Bounding_Volumes 0x59d280: the oriented box named
    "<model>.BOUNDINGBOX" (strchr '.', stricmp 0xbec7a8) becomes the HLOD's bounds (the sphere of
    the ray pre-test, and culling).
  - HLodClass(HLodDefClass): a sub-object whose name has no prototype is skipped without a word.
So a skinned unit is clicked on its BOUNDINGBOX: it must exist under the name the HLOD asks for,
be oriented (turn with the unit), and enclose the model as we draw it.

`cover(data, sk)` makes the model's BOUNDINGBOX oriented and grows it (never shrinks it) to enclose
every mesh in the rest pose, in the box's bone space; `check(data, ea, sk)` proves it, against EA's
box. Build and checks: sagekit/units/build.py. docs/UNITS.md, "Click picking".
"""
import struct

from ..formats import w3dpose as P
from ..formats.w3d import BOX, HLOD, HLOD_SUB_OBJECT, W3DFile, chunks

ORIENTED, ALIGNED = 0x1, 0x2            # W3D_BOX_ATTRIBUTE_*
TOLERANCE = 1e-3


def _cstr(b):
    return b.split(b"\0")[0].decode("latin-1")


def boxes(data):
    """{BOX NAME: (payload offset, attributes, centre, extent)} of the model's box chunks."""
    out = {}
    for t, o, s, _ in chunks(data, 0, len(data)):
        if t == BOX:
            p = o + 8
            out[_cstr(data[p + 8:p + 40]).upper()] = (p, struct.unpack_from("<I", data, p + 4)[0],
                                                      struct.unpack_from("<3f", data, p + 44),
                                                      struct.unpack_from("<3f", data, p + 56))
    return out


def sub_objects(data):
    """[(SUB-OBJECT NAME, bone)] of the HLOD's first (top) LOD array."""
    for t, o, s, _ in chunks(data, 0, len(data)):
        if t != HLOD:
            continue
        for t2, o2, s2, has_sub in chunks(data, o + 8, o + 8 + s):
            if has_sub:
                return [(_cstr(data[o3 + 12:o3 + 44]).upper(), struct.unpack_from("<I", data, o3 + 8)[0])
                        for t3, o3, _, _ in chunks(data, o2 + 8, o2 + 8 + s2) if t3 == HLOD_SUB_OBJECT]
    return []


def unresolved(data):
    """HLOD sub-objects no chunk of the file defines (the game skips them)."""
    have = {(n or "").upper() for n, _, _, _ in W3DFile(data).cache_entries()}
    return [n for n, _ in sub_objects(data) if n not in have]


def pick_box(data):
    """(name, bone, attributes, centre, extent) of the BOUNDINGBOX the HLOD names and the file
    defines, or None."""
    found = boxes(data)
    for name, bone in sub_objects(data):
        if name.split(".")[-1] == "BOUNDINGBOX" and name in found:
            _, attr, c, e = found[name]
            return name, bone, attr, c, e
    return None


def visible(data, sk, pose=None):
    """(lo, hi) of every mesh vertex as drawn in `pose` (rest by default), in object space."""
    w = W3DFile(data)
    bones = P.hlod(data)[2]
    pose = pose or sk.pose(None, 0)
    pts = [p for m in w.meshes.values() for p in P.mesh_points(m, bones, pose) if p is not None]
    return tuple(min(p[i] for p in pts) for i in range(3)), tuple(max(p[i] for p in pts) for i in range(3))


def _in_box_space(lo, hi, sk, bone):
    """An object-space AABB as an AABB in the rest space of `bone` (bone 0: unchanged)."""
    if bone == 0:
        return lo, hi
    inv = P.invert(sk.rest[bone])
    corners = [P.point(inv, (x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    return tuple(min(c[i] for c in corners) for i in range(3)), tuple(max(c[i] for c in corners) for i in range(3))


def bounds(c, e):
    return tuple(c[i] - e[i] for i in range(3)), tuple(c[i] + e[i] for i in range(3))


def cover(data, sk):
    """Model bytes with its BOUNDINGBOX oriented and grown to enclose the rest pose (sizes and every
    other byte unchanged); unchanged when the model has no BOUNDINGBOX the HLOD resolves."""
    box = pick_box(data)
    if box is None:
        return data
    name, bone, attr, c, e = box
    lo, hi = bounds(c, e)
    vlo, vhi = _in_box_space(*visible(data, sk), sk, bone)
    lo = tuple(min(lo[i], vlo[i]) for i in range(3))
    hi = tuple(max(hi[i], vhi[i]) for i in range(3))
    d = bytearray(data)
    p = boxes(data)[name][0]
    struct.pack_into("<I", d, p + 4, (attr & ~ALIGNED) | ORIENTED)
    struct.pack_into("<3f", d, p + 44, *[(lo[i] + hi[i]) / 2 for i in range(3)])
    struct.pack_into("<3f", d, p + 56, *[(hi[i] - lo[i]) / 2 + TOLERANCE / 4 for i in range(3)])
    return bytes(d)


def without_volume(t, chunk):
    """A top-level chunk as the build must keep it: a box with its attributes, centre and extent
    blanked (cover() sets those), every other chunk as it is."""
    if t != BOX:
        return chunk
    c = bytearray(chunk)
    c[12:16] = bytes(4)
    c[52:76] = bytes(24)
    return bytes(c)


def check(data, ea, sk):
    """The click volume of our model against EA's: every HLOD sub-object resolves; when EA's model
    has a BOUNDINGBOX, ours is there under the HLOD's name, oriented, holds EA's box and encloses
    the rest pose. Returns a report dict; raises AssertionError."""
    missing = unresolved(data)
    assert not missing, "HLOD sub-objects the file does not define (the game drops them): %s" % missing
    theirs = pick_box(ea)
    if theirs is None:
        return {"box": None}
    ours = pick_box(data)
    assert ours, "EA's model is clicked on %s; ours has no BOUNDINGBOX the HLOD resolves" % theirs[0]
    name, bone, attr, c, e = ours
    assert bone == theirs[1], "%s moved from bone %d to %d" % (name, theirs[1], bone)
    assert attr & ORIENTED and not attr & ALIGNED, \
        "%s is not oriented (attributes 0x%x): the game does not click it as the unit turns" % (name, attr)
    lo, hi = bounds(c, e)
    elo, ehi = bounds(theirs[3], theirs[4])
    assert all(lo[i] <= elo[i] + TOLERANCE and hi[i] >= ehi[i] - TOLERANCE for i in range(3)), \
        "%s is smaller than EA's: %s..%s inside %s..%s" % (name, lo, hi, elo, ehi)
    vlo, vhi = _in_box_space(*visible(data, sk), sk, bone)
    out = [i for i in range(3) if vlo[i] < lo[i] - TOLERANCE or vhi[i] > hi[i] + TOLERANCE]
    assert not out, "the model sticks out of %s on axis %s: drawn %s..%s, box %s..%s" % (
        name, "".join("xyz"[i] for i in out), _r(vlo), _r(vhi), _r(lo), _r(hi))
    return {"box": name, "ea": [_r(elo), _r(ehi)], "ours": [_r(lo), _r(hi)], "drawn": [_r(vlo), _r(vhi)]}


def _r(v):
    return [round(x, 2) for x in v]
