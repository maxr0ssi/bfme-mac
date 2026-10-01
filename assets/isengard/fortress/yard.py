"""The Isengard citadel's story pieces (Blender side), pass 3: up where the RTS camera sees them.

    -Y walk      a log stack (felled Fangorn), a slag cart, the side stack with a fire grate at its
                 foot and a molten runnel from it to a gantry lifting a crucible off a floor grate,
                 a pike rack, an anvil with glowing work, ingots, braziers, ember lanterns
    +Y walk      a rack of Uruk shields, a forge (hearth, anvil with glowing work, bellows,
                 crucible, ingots), a molten runnel from the side stack to it, a pipe to the
                 bellows house, a brazier, ember lanterns
    front walk   a fire grate, braziers, ember lanterns; the White Hand on a shield over the gate
    -Y wall face the dammed Isen: a flume out of the wall onto an overshot water wheel (z 19..37)
                 turning two gear wheels
    front tower  scaffolding up the +X -Y tower's outer face (z 0..60), a half-built siege
                 ladder leaning on it
    everywhere   silver collars and caps on EA's pinnacles, lanterns on brackets off the front towers;
                 flames out of every chimney, brazier, hearth, grate and crucible (shapes_fire.py)

Positions are polar (degrees, radius) about the citadel's centre. Kept clear: the gate opening
(x > 73, |y| < 11), the burning forges over the -X wall (x -70..-19, |y| < 29), the orcfire
cauldrons and the gatehouse's orcfire (x 60..75, |y| < 14, z 52..94), the wizard's tower (r < 22),
the footprint (|y| <= 74.16, x -74.16..84.76) and EA's ground (nothing below z -0.06).
"""
import math

from mathutils import Vector as V

WALK = 48.5
G = 0.7                                     # open ground: the kit sinks at most 0.7 (shapes_yard.GROUND)
STACK_R = 61.5                              # the side stacks at (0, +-61.5)
# EA's pinnacles: the curtain's corner spikes (head z 59.8) and the wedge towers' points (z 91.4)
CORNERS = [(26.8, 64.8), (0.1, 70.3), (-26.9, 64.8), (-64.8, 26.6), (-70.2, 0.1), (-64.7, -26.9), (-26.8, -64.7),
           (0.1, -70.2), (26.8, -64.7), (64.8, -26.7), (64.8, 26.6)]
POINTS = [(58.8, 59.1), (59.1, -59.4), (-58.9, -59.2)]


def polar(deg, r, z=0.0):
    a = math.radians(deg)
    return V((r * math.cos(a), r * math.sin(a), z))


def radial(deg):
    a = math.radians(deg)
    return V((math.cos(a), math.sin(a), 0))


def tangent(deg):
    a = math.radians(deg)
    return V((-math.sin(a), math.cos(a), 0))


def arc(deg0, deg1, r, z, steps=4):
    return [polar(deg0 + (deg1 - deg0) * i / steps, r, z) for i in range(steps + 1)]


def stacks(kit):
    """The chimneys on the side walks: lozenge stacks tapering to blade crowns."""
    out = []
    for sy in (1, -1):
        out += kit.needle_stack((0.0, sy * STACK_R), 90.0 * sy, 4.6, 3.0, 44.0, 102.0, collar=0.6)
    return out


def minus_y(kit):
    out = kit.log_stack(polar(246.5, 62.0, WALK), tangent(246.5), 8.0, 1.0, rows=2)
    out += kit.slag_cart(polar(257.0, 60.0, WALK), tangent(257.0), 1.1)
    out += kit.fire_grate(polar(270, STACK_R - 7.6, WALK), tangent(270), -radial(270), w=3.6, h=2.8, d=1.2)
    out += kit.floor_grate(polar(283.5, 60.5, WALK), tangent(283.5), 3.4, 3.4)
    out += kit.gantry(polar(283.5, 60.5, WALK), tangent(283.5), 8.5, 10.5, drop=2.0)
    out += kit.runnel([V((1.5, -60.4, WALK + 0.2))] + arc(275.5, 280.5, 60.5, WALK + 0.2, 2), 0.7)
    out += kit.pike_rack(polar(293.5, 66.4), -tangent(293.5), -radial(293.5), 0.0, WALK, 4.5, 7.5, d=0.6, pikes=4)
    anvil = polar(291.0, 59.5, WALK)
    out += kit.anvil(anvil, tangent(291.0), 1.1) + kit.glowing_work(anvil + V((0, 0, 3.1)), tangent(291.0), 1.1)
    out += kit.ingots(polar(295.5, 58.0, WALK), tangent(295.5), 3, 0.9)
    for deg in (251.0, 289.0):
        out += kit.brazier(polar(deg, 56.2, WALK), 1.5, 3.4)
    out += kit.post_lantern(polar(262.5, 55.2, WALK), 4.5)
    return out


PIPE = [V((-0.3, 63.8, 57.0)), V((-8.5, 63.8, 57.0)), V((-8.5, 63.8, 51.5)), V((-9.5, 60.0, 51.5))]   # stack -> bellows house


def plus_y(kit, pipe=PIPE):
    out = kit.shield_rack(polar(67.5, 65.8, WALK), -tangent(67.5), -radial(67.5), 5.6, 2, 4.4)
    c = polar(78.0, 61.0, WALK)
    out += kit.hearth(c, tangent(78.0), -radial(78.0), w=5.0, d=3.4, h=2.6, hood=4.2)
    anvil = c - radial(78.0) * 4.6 + tangent(78.0) * 1.5
    out += kit.anvil(anvil, tangent(78.0), 1.1) + kit.glowing_work(anvil + V((0, 0, 3.1)), tangent(78.0), 1.1)
    out += kit.crucible(c - radial(78.0) * 3.6 - tangent(78.0) * 3.2, 1.3, 2.2)
    out += kit.bellows(c + tangent(78.0) * 4.2 + radial(78.0) * 0.5, -tangent(78.0), 1.0)
    out += kit.ingots(c - radial(78.0) * 5.8 - tangent(78.0) * 1.2, tangent(78.0), 3, 0.9)
    out += kit.runnel([V((1.5, 60.4, WALK + 0.2))] + arc(84.5, 80.0, 60.5, WALK + 0.2, 1), 0.7)
    if pipe:
        out += kit.pipe(pipe, 0.5)
    out += kit.brazier(polar(86.0, 56.2, WALK), 1.5, 3.4)
    out += kit.post_lantern(polar(95.5, 55.2, WALK), 4.5)
    return out


def rails(kit):
    """Blade rails along the walks' inner edges by the forges."""
    out = []
    for deg in (73.0, 288.0):
        out += kit.blade_rail(polar(deg, 55.0, 0.0), tangent(deg), -4.0, 4.0, WALK, 5, 2.6)
    return out


def front(kit):
    """The front walks: a fire grate, braziers, lanterns; the White Hand on a shield over the gate."""
    out = kit.floor_grate(polar(-20.5, 60.0, WALK), tangent(-20.5), 3.0, 3.0)
    for deg in (-24.0, 19.5):
        out += kit.brazier(polar(deg, 56.2, WALK), 1.5, 3.4)
    for deg in (-16.5, 24.5):
        out += kit.post_lantern(polar(deg, 55.2, WALK), 4.5)
    out += kit.shield(V((77.0, 0.0, 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, 43.8, 8.5, d=0.2)
    for sgn in (-1, 1):                     # chains from the shield's rim to the gatehouse
        out += kit.chain(V((77.4, sgn * 3.2, 51.5)), V((77.4, sgn * 5.8, 55.0)), link=1.2)
    return out


def isen(kit):
    """The flume from a sluice in the -Y wall onto an overshot water wheel, two gears beside it."""
    deg = 281.25
    a, t, n = radial(deg) * 69.2, tangent(deg), radial(deg)
    out = kit.water_wheel(a + n * 2.6 + V((0, 0, 28.0)), -t, 8.6, w=2.2, spokes=6, paddles=10)
    P = lambda u, d, z: a + t * u + n * d + V((0, 0, z))          # noqa: E731
    top, low = P(15.5, 2.6, 44.5), P(2.0, 2.6, 38.2)
    out.append(kit.beam(top, low, 0.95, "timber"))
    out.append(kit.beam(top + V((0, 0, 0.75)), low + V((0, 0, 0.75)), 0.55, "water"))
    for f in (0.2, 0.75):
        p = top.lerp(low, f)
        out.append(kit.beam(p - n * 2.6 - V((0, 0, 1.6)), p - V((0, 0, 0.7)), 0.3, "iron"))
    out.append(kit.beam(P(16.2, 0.3, 43.5), P(16.2, 3.4, 43.5), 1.8, "iron"))          # the sluice box in the wall
    out.append(kit.beam(P(17.8, 1.6, 42.0), P(17.8, 1.6, 48.5), 0.25, "iron"))         # its gate's rack
    out += kit.gear(a, t, n, -13.9, 28.0, 4.6, 0.7, teeth=10, th=1.2)
    out += kit.gear(a, t, n, -16.8, 35.1, 3.0, 0.4, teeth=8, th=1.1)
    return out


def siege(kit):
    """Scaffolding up the +X -Y tower's outer face and a half-built siege ladder against it."""
    p0, p1 = V((52.5, -46.9, G)), V((58.5, -58.5, G))
    d = (p1 - p0).normalized()
    n = V((d.y * -1, d.x, 0))
    if n.dot(V((1.0, 0.3, 0))) < 0:
        n = -n
    out = kit.scaffold(p0 + n * 0.6 - d * 1.0, d, n, 12.5, 4.2, 58.0, levels=5)
    out += kit.siege_ladder(p0 + n * 9.0 + d * 5.5, d, n, 40.0, w=3.4, rungs=14, built=0.55, lean=0.2)
    return out


def trims(kit):
    """Silver on EA's pinnacles: a cap on every curtain corner spike, a collar on the towers'
    points; lanterns on brackets off the front towers."""
    out = []
    for x, y in CORNERS:
        c = V((x, y, 0))
        out.append(kit.beam(c + V((0, 0, 57.0)), c + V((0, 0, 60.4)), 0.6, "trim", 0.0))
    for x, y in POINTS:                     # a collar under each tower's point (a strip down the point
        c = V((x, y, 0))                    # floated clear of it: the points lean)
        out.append(kit.beam(c + V((0, 0, 87.6)), c + V((0, 0, 89.0)), 1.1, "trim"))
    for x, y, nx, ny in ((56.0, -52.7, 0.888, 0.46), (52.7, 56.0, 0.46, 0.888)):
        t = V((-ny, nx, 0))
        out += kit.bracket_lantern(V((x, y, 0)), t, V((nx, ny, 0)), 0.0, 66.0, reach=2.6, s=1.3)
    return out


def build(kit, stacks_on=True, pipe=PIPE):
    return (stacks(kit) if stacks_on else []) + minus_y(kit) + plus_y(kit, pipe) + front(kit) + isen(kit) + siege(kit) + trims(kit)
