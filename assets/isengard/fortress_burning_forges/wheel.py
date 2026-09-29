"""The burning forges' wheel (Blender side), in IBFBFORGESA mesh coordinates: the hub at the
origin, the disc in the x-z plane, its axis along y (see building.py)."""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import loft

from .. import shapes_addons as A

Y = V((0, 1, 0))
FACES = (-7.3, -1.7)                    # the disc's two faces (y; its rim lips stand to -8.0 and -1.1)
BLADES = [37.5 + 60 * k for k in range(6)]  # between EA's lobes (22.5 + 30k) and ribs
VENTS = [7.5 + 60 * k for k in range(6)]


def radial(deg):
    a = math.radians(deg)
    return V((math.cos(a), 0, math.sin(a)))


def tangent(deg):
    a = math.radians(deg)
    return V((-math.sin(a), 0, math.cos(a)))


def blade(kit, deg, face, out, r0=3.6, r1=10.0, h=0.65, w=0.9):
    """A low iron rib standing h off a face (y = face, `out` = -1 or +1 along y) along the radius,
    silver on its edge (the disc turns through the forge's slot: nothing may stand higher)."""
    d, t = radial(deg), tangent(deg)
    base = lambda r, hh: d * r + Y * (face + out * hh)                      # noqa: E731
    tri = [base(r0, -0.8), base(r1, -0.8), base(r1 - 0.8, h), base(r0 + 0.4, h)]
    out_ = [A.extrude(tri, -t * w / 2, t * w / 2, "iron", ("iron", True), ("iron", True))]
    out_.append(kit.beam(tri[3], tri[2], 0.13, "trim"))
    return out_


def boss(kit, face=-7.3, r=3.0, h=1.6, k=6):
    """A riveted iron boss round EA's axle end on the -y face: a hexagonal ring, a silver lip."""
    ring = lambda rr, y: [radial(360.0 * i / k) * rr + Y * y for i in range(k)]      # noqa: E731
    out = [loft([ring(r * 1.05, face + 0.3), ring(r, face - h * 0.6), ring(r * 0.8, face - h), ring(r * 0.55, face - h)],
                ["iron", "trim", "iron"], cap0=("iron", False), cap1=("iron", True))]
    for i in range(k):
        p = radial(360.0 * (i + 0.5) / k) * (r * 0.92) + Y * (face - h * 0.35)
        out.append(kit.beam(p, p - Y * 0.4, 0.28, "trim"))
    return out


def vent(kit, deg, face, out, r0=5.2, r1=9.0, w=1.1):
    """A pointed ember vent in a face along the radius, standing 0.2 off it."""
    d, t = radial(deg), tangent(deg)
    y0, y1 = face - out * 0.8, face + out * 0.2
    poly = [d * r0 - t * w / 2, d * (r1 - w) - t * w / 2, d * r1, d * (r1 - w) + t * w / 2, d * r0 + t * w / 2]
    return [A.extrude(poly, Y * y0, Y * y1, "ember", ("ember", False), ("ember", True))]


def build(kit):
    out = []
    for face, o in zip(FACES, (-1, 1)):
        for deg in BLADES:
            out += blade(kit, deg, face, o)
        for deg in VENTS:
            out += vent(kit, deg, face, o)
    out += boss(kit)
    return out
