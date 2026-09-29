"""The excavations' destructible pieces (Blender side), IBFEXCAVB mesh coordinates (identity bone;
the citadel's frame). EA's pieces (probed 2026-09-29): a timber chute from its head by the south
shaft (-8, -30, z 33) down to (-31.5, -1.5, z 25.8), 3.8 wide; two ladders leaning at y -57..-40
to z 66; a leaning post at y 25..30 whose head is at (-8.1, 28.6, 54.7).

Glowing ore tumbling down the chute out of an iron skip at its head, a lantern on an iron arm out
of the post. Kept clear: the shaft mound (-0.2, -31.8; rim r 6.6),
the A-frame's swing (x -9..42, y -34..9) and the burning forges (x < -22, |y| < 22)."""
from mathutils import Vector as V

from sagekit.blender.geometry import Z, box

HEAD, FOOT = V((-8.0, -29.9, 33.0)), V((-31.5, -1.5, 25.8))


def chute(kit):
    out = []
    for f, s in ((0.2, 1.3), (0.42, 1.0), (0.63, 1.2), (0.85, 0.9)):
        out.append(kit.facet_lump(HEAD.lerp(FOOT, f) + Z * (s * 0.55 + 0.1), s, "ember"))
    d = (FOOT - HEAD).normalized()
    c = HEAD - d * 1.2 + Z * 0.2                        # an iron skip tipping into the chute's head
    out.append(box(c.x - 1.6, c.x + 1.6, c.y - 1.6, c.y + 1.6, c.z, c.z + 2.4, "iron", ("iron", True), ("ember", True)))
    out.append(kit.beam(c + V((-1.7, -1.7, 2.5)), c + V((1.7, -1.7, 2.5)), 0.22, "trim"))
    out.append(kit.beam(c + V((-1.7, 1.7, 2.5)), c + V((1.7, 1.7, 2.5)), 0.22, "trim"))
    return out


def lanterns(kit):
    p = V((-8.3, 28.9, 50.0))                         # an iron arm out of the post, a lantern on it
    out = [kit.beam(p - V((0.6, 0, 0)), p + V((3.0, 0, 0.4)), 0.2, "iron")]
    out += kit.lantern(p + V((3.0, 0, 0.3)), 1.4, chain=1.0)
    return out


def build(kit):
    return chute(kit) + lanterns(kit)
