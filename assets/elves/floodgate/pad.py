"""The Elven fortress expansions' connecting arm: the short arcade every pad building (floodgate,
watchtower, vigilant ent) reaches back to the fortress with, one pointed arch through it.

EA drew the same arm into each body, shifted along x: flat faces either side (|y| 6.03 on the
floodgate, 4.58 on the watchtower, -3.44 / 2.44 on the vigilant ent), an opening 12.6-13.1 wide
with jambs to 24.38 and its point at 40.37, and a painted moulding round it (flush with the face)
whose outer edge springs at 24.7, half 10.4 wide, to a point at 45.7. The kit's arch frames that
moulding: silver fronts, sea-green enamel reveals, a gilt leaf over the point, the opening itself
untouched (units walk through it).

Blender side (mathutils): the recipes import this module anywhere, so mathutils is imported inside."""

SPRING, APEX, HALF = 24.7, 45.7, 10.4      # the outer edge of EA's painted moulding
FRAME_W, FRAME_D = 1.1, 0.8                # our frame: width, how far it stands proud of the face
OGEE = 0.25                                # a slight leaf tip


def face(y, side):
    """(anchor, t, n) of an arm face at y whose outward normal is +y (side 1) or -y (side -1):
    t x n = -z, so t runs -x on the +y face and +x on the -y face."""
    from mathutils import Vector as V
    return V((0.0, y, 0.0)), V((-side, 0.0, 0.0)), V((0.0, float(side), 0.0))


def arch(kit, cx, faces, finial=True):
    """The pointed frame round the arm's arch on each face: faces [(y, side)], cx the arch's axis."""
    out = []
    for y, side in faces:
        a, t, n = face(y, side)
        u = -side * cx                     # the axis's position along t
        out += kit.arch(a, t, n, u, HALF, 0.0, SPRING, APEX, w=FRAME_W, d0=0.0, d1=FRAME_D, ogee=OGEE,
                        finial=finial)
    return out


def coping_profile(z, d_out=0.9, d_in=-1.4):
    """The kit's coping_run moulding (a rounded nose d_out proud, the top at z) as a convex (d, z)
    profile with tags, drawn without the kit's point in the middle of the bottom edge: that point
    lies on the straight bottom, so the end caps' fans made a zero-area triangle there and left it a
    loose vertex (the checks' "zero-area faces / loose verts"). The whole bottom is one face here."""
    prof = [(d_in, z - 1.6), (d_out * 0.55, z - 1.6), (d_out, z - 1.1), (d_out, z - 0.45), (d_out * 0.7, z), (d_in, z)]
    return prof, ["trim", "trim", "coping", "trim", "top", "stoneB"]


def coping_sweep(path, z, d_out, d_in, center):
    from sagekit.blender.geometry import sweep
    prof, tags = coping_profile(z, d_out, d_in)
    return sweep(path, prof, tags, center=center)[0]


def coping(kit, x0, x1, faces, z):
    """A moulded coping along the arm's top edges from x0 to x1 (the top at z), nosed out over each
    face; its inner part sits on the arm's top."""
    out = []
    for y, side in faces:
        out += coping_sweep([(x0, y), (x1, y)], z, 0.9, -1.4, ((x0 + x1) / 2, y - side))
    return out


def band(kit, x0, x1, faces, z0, z1):
    """A knotwork band (silver knots on sea-green enamel between gilt beads) along each face."""
    out = []
    for y, side in faces:
        out += kit.filigree_band([(x0, y), (x1, y)], z0, z1, d=0.3, center=((x0 + x1) / 2, y - side))
    return out
