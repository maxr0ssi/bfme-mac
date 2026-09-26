"""The gatehouse flèche (Blender side): a slender spire set astride the ridge of EA's gatehouse roof,
the fortress's one new tower. EA's roof is a pointed section (|y|, z: (12.7, 64.1), (7.5, 73.1),
(1.6, 80.2), a ridge rail 1.4 wide at 82.2 (x 53.4) to 84.4 (x 74.4)); the flèche stands at x 61.5,
between the back arch of the roof (x 53.4) and its front (x 75.5), clear of the teal gate arch
(EBFORTRESS2, x <= 73.3) and the mallorn foliage (EBFORTRESS4, z <= 99, x <= 55.6).

    drum       an octagon (apothem 4.2) from inside the roof (z 76) to z 96: a pointed lattice
               window front and back over the ridge, a silver cornice
    balcony    a corbelled gallery at z 96 with a silver-railed balustrade round it
    lantern    eight slender colonnettes round a tall starlight crystal, under a silver cornice
    spire      a swept slate needle, silver ribs up its eight corners and a gilt leaf on the tip
    banners    two long leaf banners (house colour) on the drum's sides, over the roof's slopes
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import loft, prism_uz, sweep

from ..shapes import ring, turned

CX, CY = 61.5, 0.0
APO = 4.2                       # the drum's apothem
K = 8
Z_FOOT, Z_DRUM = 76.0, 96.0     # the drum: from inside EA's roof to the balcony
GALLERY = 5.7                   # the balcony's apothem
Z_LANTERN = 104.0               # top of the lantern stage
SPIRE_R, SPIRE_H = 5.2, 27.0    # the needle's eave radius and height
BANNER = (93.0, 4.6, 11.0, 0.9)  # z_top, width, length, d: the tip at 82, over the roof's slope (z 73 at |y| 5.1)


def poly(apo, z, k=K):
    """A k-gon ring with faces toward 0, 45, ... degrees (apothem apo)."""
    return ring(CX, CY, apo / math.cos(math.pi / k), z, k, phase=math.pi / k)


def face(apo, deg):
    a = math.radians(deg)
    n = V((math.cos(a), math.sin(a), 0))
    t = V((-math.sin(a), math.cos(a), 0))
    return V((CX, CY, 0)) + n * apo, t, n


def build(kit):
    out = [loft([poly(APO, Z_FOOT), poly(APO, Z_DRUM - 1.4)], ["stoneA"], cap0=("stoneB", False),
                cap1=("top", False))]
    for deg in (0, 180):                                            # lattice windows over the ridge
        a, t, n = face(APO, deg)
        out += _window(kit, a, t, n, 1.0, 85.0, 89.8, 92.8)
    out += _cornice(APO, Z_DRUM - 1.4, Z_DRUM, 0.6)
    # the balcony: a bell corbel out to the gallery, its floor, and a balustrade on the rim
    out.append(loft([poly(APO - 0.2, Z_DRUM - 1.2), poly(GALLERY - 0.3, Z_DRUM - 0.2), poly(GALLERY, Z_DRUM),
                     poly(GALLERY, Z_DRUM + 0.5)], ["stoneB", "coping", "trim"], cap0=("stoneB", False),
                    cap1=("top", True)))
    rim = [(p.x, p.y) for p in poly(GALLERY - 0.45, 0.0)]
    out += kit.balustrade(rim + rim[:1], Z_DRUM + 0.5, height=1.9, pitch=1.9, center=(CX, CY), r=0.2)
    # the lantern: a floor, eight colonnettes round a starlight crystal, a cornice
    out.append(loft([poly(APO - 0.4, Z_DRUM + 0.4), poly(APO - 0.4, Z_DRUM + 1.0)], ["trim"],
                    cap0=("stoneB", False), cap1=("top", True)))
    for i in range(K):
        ang = 2 * math.pi * i / K + math.pi / K
        px, py = CX + 3.3 * math.cos(ang), CY + 3.3 * math.sin(ang)
        out.append(turned(px, py, [(0.34, Z_DRUM + 0.9), (0.26, Z_LANTERN - 0.9), (0.4, Z_LANTERN - 0.5)],
                          ["trim", "trim"], 6, cap0=("top", False), cap1=("top", False)))
    out += kit.crystal_lantern(CX, CY, Z_DRUM + 1.0, h=Z_LANTERN - Z_DRUM - 1.4, r=2.0, finial=False)
    out.append(loft([poly(APO - 0.4, Z_LANTERN - 0.6), poly(APO + 0.3, Z_LANTERN - 0.1), poly(APO + 0.3, Z_LANTERN + 0.4),
                     poly(APO - 0.2, Z_LANTERN + 0.7)], ["trim", "trim", "top"], cap0=("stoneB", True),
                    cap1=("top", True)))
    # the needle: a swept slate spire with silver ribs on its corners and the gilt leaf on the tip
    z0 = Z_LANTERN + 0.6
    out += kit.swept_roof(CX, CY, SPIRE_R, z0, SPIRE_H, k=K, per_side=1, upturn=1.2, lip=0.4, sweep_pow=1.5,
                          finial=True, phase=0.0)
    out += _ribs(z0 + 0.4, SPIRE_R, SPIRE_H, 1.5, 1.2)
    for deg in (90, -90):                                           # the banners over the roof's slopes
        a, t, n = face(APO, deg)
        z_top, width, length, d = BANNER
        out += kit.leaf_banner(a, t, n, 0.0, z_top, width, length, d=d, free=True)[:3]
    return out


def _window(kit, a, t, n, half, z0, spring, apex):
    """A pointed lattice-glass window with the kit's silver arch frame."""
    outline = kit.arch_outline(half, spring, apex, 0.0, 4)
    pts = [(-half, z0), (half, z0)] + [(x, z) for x, z in outline[:-1]] + [(-x, z) for x, z in reversed(outline)]
    out = [prism_uz(a, t, n, pts, -0.3, 0.12, [None] * len(pts), "window", None)]
    # the frame stands on the drum's face (d0 > 0) and inside its width (1.74 either side): past the
    # face's edge, or sunk into it, the jambs' open backs let the sky see the reveals' backs
    return out + kit.arch(a, t, n, 0.0, half, z0, spring, apex, w=0.5, d0=0.02, d1=0.5, k=4, finial=False)


def _cornice(apo, z0, z1, out_):
    """A moulded silver cornice round the drum from z0 to z1."""
    path = [(p.x, p.y) for p in poly(apo, 0.0)]
    path.append(path[0])
    h = z1 - z0
    prof = [(-1.0, z0), (0.2, z0), (out_, z0 + 0.45 * h), (out_, z0 + 0.85 * h), (out_ * 0.8, z1), (-1.0, z1)]
    return sweep(path, prof, [None, "trim", "coping", "trim", "top", None], center=(CX, CY))[0]


def _ribs(z, r, h, pw, upturn, steps=6, size=0.3):
    """Silver ribs up the needle's corners, riding on the swept faces: each a square section lofted
    along r (1 - s)**pw from the eave (turned up by `upturn`, fading as the swept_roof's) to the tip."""
    out = []
    for i in range(K):
        ang = 2 * math.pi * i / K
        c, s_ = math.cos(ang), math.sin(ang)
        rings = []
        for j in range(steps + 1):
            s = j / steps * 0.94
            rr = r * (1 - s) ** pw + 0.12
            zz = z + h * s + upturn * max(0.0, 1 - 3 * s)
            p = V((CX + rr * c, CY + rr * s_, zz))
            rad, tan = V((c, s_, 0)), V((-s_, c, 0))
            rings.append([p - tan * size, p - tan * size + rad * size * 1.4, p + tan * size + rad * size * 1.4,
                          p + tan * size])
        out.append(loft(rings, ["trim"] * steps, cap0=("trim", False), cap1=("trim", True)))
    return out
