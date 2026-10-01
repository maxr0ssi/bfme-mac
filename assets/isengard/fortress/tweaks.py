"""The citadel's tweak options (Blender side; shape previews, 2026-09-30). After pass 4 took the
needle stacks off every other building (Max: "super low quality that tower"), the citadel still had
three: the great chimney up EA's foundry tower's point between the pair (foundry.CHIMNEY) and the
two side stacks on the walks (yard.stacks). ISENGARD_CITADEL picks one; unset, the citadel is the
installed design (pass 7). The pair BL/BR, the Hands, the slits and B3 are the same in every option.

    A   de-stack: all three needle stacks go. Where each side stack stood, a smelting hearth on the
        walk (stone bed, iron hood, flue) feeds the walk's molten runnel; a crucible on the -Y walk;
        the +Y pipe to the bellows house runs from the hearth's flue. EA's foundry point gets the
        silver collar the other three points have. Fire 20: the 3 chimneys become 2 hearths and a
        crucible.
    B   one quality stack: the great chimney goes; the +Y side stack (the foundry's side, piped to
        the bellows house) is rebuilt as the furnace's smelter stack (shapes_trades.smelter_stack),
        square, faces along the walk, stepped stone courses into the walk, mouth at z 96 (under the
        pair's 120), without rivet heads (the budget; two stacks came to 15,253 triangles); the -Y
        one becomes A's hearth. Fire 20: the smelter's chimney, a hearth and the crucible.
    C   one family: A, and the three spiked wedge towers' outer top edges carry Orthanc's horns (the
        wall hubs' crown A horn, two an edge rising to EA's point) in place of the iron spikes, so
        citadel and walls read as one base. Fire 20, as A.
    D   C without the pair BL/BR and their great Hands (Max on v1: "get rid of the stupid tower",
        the tall pair). They carried no fire points (only ember slits), so fire stays 20; the
        grates at the wall's foot where they stood stay as glowing pits. B3 and its crane stay.
    D2  D with a horned crown on EA's foundry tower point (the triangle in the RTS view): a stone
        plinth clamped over the point, a faceted fire-pot on it, a ring of broad Orthanc horns
        round it rising to z 109 and two horns down each outer edge near the point, all outside
        the orcfire upgrade's fire-card box. Fire 21: D's and the fire-pot (brazier).

The switch and the options' fire points are in building.py (option(), CITADEL_FIRE).
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft

from . import walls, yard
from .yard import WALK, polar, radial, tangent

FOUNDRY_POINT = (-58.9, 59.2)               # EA's foundry tower point (the great chimney stood on it)
SIDES = (90.0, 270.0)                       # the side stacks' places, (0, +-61.5) on the walks
CRUCIBLE = (266.0, 63.4)                    # A, B, C: the crucible on the -Y walk (polar)
SMELTER = (5.0, 44.0, 96.0)                 # B: half-diagonal, foot (in the walk), mouth
HEARTH_PIPE = [V((0.0, 61.5, 57.0)), V((-8.5, 61.5, 57.0)), V((-8.5, 61.5, 51.5)), V((-9.5, 60.0, 51.5))]


def collar(kit):
    """The silver collar the other three tower points have (yard.trims), on the foundry's."""
    x, y = FOUNDRY_POINT
    c = V((x, y, 0))
    return [kit.beam(c + Z * 87.6, c + Z * 89.0, 1.1, "trim")]


def crucible(kit):
    deg, r = CRUCIBLE
    return kit.crucible(polar(deg, r, WALK), 1.4, 2.4)


def hearths(kit, sides=SIDES):
    """A: a smelting hearth where each side stack stood, its mouth to the courtyard."""
    out = []
    for deg in sides:
        out += kit.hearth(polar(deg, yard.STACK_R, WALK), tangent(deg), -radial(deg), w=6.0, d=4.4, h=2.8, hood=4.6)
    return out


def smelter(kit):
    """B: the furnace's smelter stack, smaller and without rivet heads, on the +Y walk where the
    side stack stood (its pipe to the bellows house kept); the -Y walk gets A's hearth."""
    from ..shapes_trades import smelter_stack
    r, z0, z1 = SMELTER
    return smelter_stack(kit, polar(90.0, yard.STACK_R, 0.0), r, z0, z1, rot=45.0, rivets=False) + hearths(kit, (270.0,))


def tower_horns(kit):
    """C: Orthanc's horns along the wedge towers' outer top edges in place of walls.tower_spikes
    (same edges, same reach), two an edge, rising toward EA's point: with the point, five horns a
    tower."""
    from ..shapes_addons import horn
    out = []
    for sx, sy in walls.SPIKED:
        for (x0, y0), (x1, y1) in walls.EDGES:
            p0, p1 = V((sx * x0, sy * y0, 0)), V((sx * x1, sy * y1, 0))
            t = (p1 - p0).normalized()
            n = V((t.y, -t.x, 0))
            if n.dot(p0.lerp(p1, 0.5) - V((sx * 38.8, sy * 38.8, 0))) < 0:
                n = -n
            for u, top in ((11.0, 92.4), (24.0, 93.4)):     # the one nearer the point taller
                out += horn(kit, p0 + t * u - n * 0.4, n, t, 85.2, top, 1.55, 1.6, lean=0.24, curl=0.08, flare=1.25,
                            steps=3)
    return out


CROWN = ((-56.6, 56.8), 4.4, 84.0, 91.5)      # D2: plinth centre (the point, nudged inward), radius, z0, top


def point_crown(kit):
    """D2: the wall hubs' crown A on EA's foundry tower point (head (-58.9, 59.1) z 90.2; the
    tower's roof z 85.7): a hexagonal stone plinth over the point with a silver ledge, a spiked
    faceted fire-pot on it, six broad horns round it leaning out (the two facing the camera
    tallest), and two horns down each outer edge toward the point. Clear of the orcfire fire-card
    box (x > -51.4 and y < 51.8 above z 80)."""
    from ..shapes_addons import cauldron, horn
    (cx, cy), r, z0, z1 = CROWN
    c = V((cx, cy, 0))
    ring = lambda rr, z: kit.ring(cx, cy, rr, z, 6, phase=0.0)                       # noqa: E731
    out = [loft([ring(r * 0.8, z0), ring(r, z1 - 1.2), ring(r + 0.5, z1 - 1.2), ring(r + 0.5, z1 - 0.6), ring(r * 0.92, z1)],
                ["stoneA", "stoneA", "trim", "stoneA"], cap0=("stoneA", False), cap1=("stoneA", True))]
    out += cauldron(kit, c + Z * z1, 2.9, 3.2, k=6, spikes=True, legs=False)
    kit.fire(c + Z * (z1 + 2.8), "brazier")
    for i in range(6):
        a = math.radians(45.0 + 60.0 * i)          # one horn straight out along the point's bisector (135)
        n = V((math.cos(a), math.sin(a), 0))
        out += horn(kit, c + n * (r - 0.6), n, V((-n.y, n.x, 0)), z1 - 1.0, 109.0 if i in (0, 3) else 104.0, 1.9, 2.1,
                    lean=0.2, curl=0.1, flare=1.3, steps=4)
    sx, sy = -1, 1
    for (x0, y0), (x1, y1) in walls.EDGES:            # down the two outer edges near the point
        p0, p1 = V((sx * x0, sy * y0, 0)), V((sx * x1, sy * y1, 0))
        t = (p1 - p0).normalized()
        nn = V((t.y, -t.x, 0))
        if nn.dot(p0.lerp(p1, 0.5) - V((sx * 38.8, sy * 38.8, 0))) < 0:
            nn = -nn
        for u, top in ((30.5, 93.0), (36.0, 95.0)):
            out += horn(kit, p0 + t * u - nn * 0.4, nn, t, 85.2, top, 1.4, 1.5, lean=0.24, curl=0.08, flare=1.25, steps=3)
    return out


def design(kit, opt):
    """The citadel with option opt ("A", "B", "C") applied."""
    from . import foundry
    if opt in ("D", "D2"):
        out = foundry.build(kit, chimney=False, pair=False) + crucible(kit)
        out += walls.build(kit, spikes=False) + tower_horns(kit) + yard.build(kit, stacks_on=False, pipe=HEARTH_PIPE)
        out += hearths(kit) + (point_crown(kit) if opt == "D2" else collar(kit))
        return out
    out = foundry.build(kit, chimney=False) + collar(kit) + crucible(kit)
    if opt == "B":
        out += walls.build(kit) + yard.build(kit, stacks_on=False) + smelter(kit)
    elif opt == "C":
        out += walls.build(kit, spikes=False) + tower_horns(kit) + yard.build(kit, stacks_on=False, pipe=HEARTH_PIPE)
        out += hearths(kit)
    else:
        out += walls.build(kit) + yard.build(kit, stacks_on=False, pipe=HEARTH_PIPE) + hearths(kit)
    return out
