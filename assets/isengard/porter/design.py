"""Isengard builder: an Uruk-hai labourer's cart hauling Fangorn timber to the forges of Orthanc.

EA's orc porter, skeleton and animations kept (robe dyed charcoal, apron dark leather); a black
timber cart bound in riveted iron with silver edges and faceted iron points, heavy
cleated wheels, a deck of Fangorn logs cut and chained, a two-man saw strapped on top, a crate of
fresh iron ingots, kite plaques and a banner bearing the White Hand on the player's colour.
Palette A, Orthanc black and silver (assets/isengard/style.py). The facts: README.md; the recipe
API: docs/UNITS.md. python3 -m sagekit unit isengard/porter --render
"""
import math
import random

from sagekit.units import DEFAULT_VIEWS, Unit, View

from .kit import HOUSE, annulus, arc, chain, endgrain, flat, plane, solid, spike, uvs, white_hand

(WOOD, BARK, IRON, SILVER, ENDGRAIN, LEATHER, MARK, STEEL,
 INGOT, CHAIN, BLACK, SOOT, _12, _13, _14, _15) = range(16)

# EA's cart in the model's rest space: the bed, the shafts the orc holds (EA's grip line), the axle.
BED = (-23.2, -11.0)                # x, rear and front wall
SIDE_R, SIDE_L = -4.35, 5.0         # y of the side walls (0.5 thick)
FLOOR, DECK, TOP = 5.6, 9.3, 10.0   # bed floor, load deck (over EA's bucket), wall top
SHAFT_R, SHAFT_L, SHAFT_Z = -4.67, 5.35, 9.1
AXLE = (-16.91, 4.05)               # x, z: the wheels' pivot
WHEEL_R, WHEEL_L = -5.94, 6.58
# Fangorn logs: (y, z, radius, rear x, front x)
LOGS = [(-2.55, 10.65, 1.35, -24.7, -14.2), (.33, 10.62, 1.32, -24.4, -14.3), (3.21, 10.65, 1.35, -24.9, -14.15),
        (-1.11, 12.93, 1.35, -24.3, -14.6), (1.77, 12.93, 1.35, -24.6, -14.4)]
POLE = (-23.05, 5.6)                # banner pole x, y


def box(m, lo, hi, tag):
    m.box(lo, hi, tag)


def walls(m):
    # Two iron sills on the axle, a plank floor, black boards banded in iron, a silver top edge.
    m.tube((AXLE[0], WHEEL_R + .2, AXLE[1]), (AXLE[0], WHEEL_L - .2, AXLE[1]), .38, IRON, sides=8)
    for y in (-3.0, 3.7):
        box(m, (BED[0] - .2, y - .35, 4.45), (BED[1] + .2, y + .35, 5.1), IRON)
    box(m, (BED[0], SIDE_R, 5.1), (BED[1], SIDE_L, FLOOR), SOOT)     # under the deck: one board
    for y in (SIDE_R, SIDE_L):
        for k, (z0, z1) in enumerate(((FLOOR, 7.0), (7.06, 8.5), (8.56, TOP - .3))):
            box(m, (BED[0], y - .25, z0), (BED[1], y + .25, z1), SOOT if k == 1 else WOOD)
        box(m, (BED[0] - .1, y - .32, TOP - .45), (BED[1] + .1, y + .32, TOP), IRON)
        box(m, (BED[0] - .1, y - .36, TOP - .02), (BED[1] + .1, y + .36, TOP + .14), SILVER)
        box(m, (BED[0] + .2, y - .32, 6.85), (BED[1] - .2, y + .32, 7.2), IRON)
        for x in (BED[0] + .2, AXLE[0], BED[1] - .2):
            box(m, (x - .3, y - .38, 4.6), (x + .3, y + .38, TOP + .45), IRON)
        box(m, (AXLE[0] - .38, y - .44, TOP + .45), (AXLE[0] + .38, y + .44, TOP + .65), SILVER)
    # Tailgate low (the logs ride over it); headboard full height.
    for z0, z1 in ((FLOOR, 7.2), (7.26, DECK - .05)):
        box(m, (BED[0] - .25, SIDE_R, z0), (BED[0] + .25, SIDE_L, z1), WOOD)
    box(m, (BED[0] - .32, SIDE_R, DECK - .4), (BED[0] + .32, SIDE_L, DECK), IRON)
    for z0, z1 in ((FLOOR, 7.0), (7.06, 8.5), (8.56, TOP - .3)):
        box(m, (BED[1] - .25, SIDE_R, z0), (BED[1] + .25, SIDE_L, z1), WOOD)
    box(m, (BED[1] - .32, SIDE_R, TOP - .45), (BED[1] + .32, SIDE_L, TOP), IRON)
    box(m, (BED[1] - .36, SIDE_R, TOP - .02), (BED[1] + .36, SIDE_L, TOP + .14), SILVER)
    # Faceted iron points on the corner posts, Orthanc's crown in small; the pole takes the last.
    for x, y in ((BED[0] + .2, SIDE_R), (BED[1] - .2, SIDE_R), (BED[1] - .2, SIDE_L)):
        box(m, (x - .42, y - .42, TOP + .45), (x + .42, y + .42, TOP + .7), SILVER)
        spike(m, (x, y, TOP + .7), (x, y, TOP + 2.4), .5, IRON)


def shafts(m):
    # EA's grip line: square beams bolted along the walls, iron-shod, silver-capped ends.
    for y in (SHAFT_R, SHAFT_L):
        box(m, (-15.0, y - .3, SHAFT_Z - .32), (5.96, y + .3, SHAFT_Z + .32), WOOD)
        for x in (-14.2, -11.8, -7.5, -2.0):
            box(m, (x - .3, y - .36, SHAFT_Z - .38), (x + .3, y + .36, SHAFT_Z + .38), IRON)
        box(m, (5.4, y - .38, SHAFT_Z - .4), (6.15, y + .38, SHAFT_Z + .4), IRON)
    box(m, (5.08, SHAFT_R - .3, SHAFT_Z - .32), (5.88, SHAFT_L + .3, SHAFT_Z + .32), WOOD)
    box(m, (5.02, -.6, SHAFT_Z - .38), (5.94, 1.3, SHAFT_Z + .38), IRON)


def heraldry(m):
    # A kite plaque on each wall: silver rim, the player's colour, the White Hand.
    kite = [(-1.3, 1.5), (1.3, 1.5), (1.18, -.25), (0, -1.95), (-1.18, -.25)]
    for y, s in ((SIDE_R - .4, -1), (SIDE_L + .4, 1)):
        at = plane((-21.25, y, 8.05), (0, s, 0))
        flat(m, at, kite, 1.1, .02, SILVER, (0, s, 0))
        flat(m, at, kite, .97, .06, HOUSE, (0, s, 0))
        white_hand(m, at, 1.25, .14, MARK, (0, s, 0), outline=BLACK)
    # The banner: a stout iron pole with a faceted point, a cross-arm, the cloth cut to a point.
    x, y = POLE
    box(m, (x - .26, y - .26, 4.7), (x + .26, y + .26, 20.6), IRON)
    for z in (7.0, TOP - .2):
        box(m, (x - .2, SIDE_L, z - .2), (x + .2, y + .2, z + .2), IRON)
    box(m, (x - .36, y - .36, 20.6), (x + .36, y + .36, 20.9), SILVER)
    spike(m, (x, y, 20.9), (x, y, 22.3), .5, IRON)
    box(m, (x, y - .17, 19.9), (-18.7, y + .17, 20.25), IRON)
    spike(m, (-18.7, y, 20.07), (-17.9, y, 20.07), .22, SILVER)
    cloth = [(-1.65, 2.2), (1.65, 2.2), (1.65, -1.6), (0, -2.9), (-1.65, -1.6)]
    for s in (-1, 1):
        at = plane((-20.6, y, 17.6), (0, s, 0))
        flat(m, at, cloth, 1, .05, HOUSE, (0, s, 0))
        white_hand(m, at, 1.35, .13, MARK, (0, s, 0), outline=BLACK)
        for b in (2.05, -1.45):
            flat(m, at, [(-1.7, b - .1), (1.7, b - .1), (1.7, b + .12), (-1.7, b + .12)], 1, .08, BLACK, (0, s, 0))


def wheel(m, y, bone):
    # Black felloe in an iron tyre with square cleats: heavy, angular, made in Isengard's forges.
    cx, cz = AXLE
    annulus(m, cx, cz, y, .36, 3.05, 3.62, WOOD, bone)
    annulus(m, cx, cz, y, .44, 3.6, 4.08, IRON, bone)
    for i in range(14):
        a, w = i * math.tau / 14, .13
        lo = [(cx + 4.0 * math.cos(a + k * w), cz + 4.0 * math.sin(a + k * w)) for k in (-1, 1)]
        hi = [(cx + 4.32 * math.cos(a + k * w * .7), cz + 4.32 * math.sin(a + k * w * .7)) for k in (-1, 1)]
        quad = [lo[0], lo[1], hi[1], hi[0]]
        solid(m, [(p, y - .4, q) for p, q in quad], [(p, y + .4, q) for p, q in quad], SILVER if i % 2 else IRON, bone)
    for i in range(6):
        a = i * math.tau / 6 + math.pi / 6
        m.tube((cx + .6 * math.cos(a), y, cz + .6 * math.sin(a)), (cx + 3.2 * math.cos(a), y, cz + 3.2 * math.sin(a)),
               .3, WOOD, bone, sides=6)
    m.tube((cx, y - .7, cz), (cx, y + .7, cz), .9, IRON, bone, sides=6)
    s = 1 if y > 0 else -1
    m.tube((cx, y + s * .6, cz), (cx, y + s * .95, cz), .5, SILVER, bone, sides=6)
    spike(m, (cx, y + s * .95, cz), (cx, y + s * 1.45, cz), .38, IRON, bone, sides=6, twist=0)


def load(m):
    rng = random.Random(7)
    # A plank deck over EA's bucket (it rides hidden in the bed, as under EA's stone pile).
    for i in range(5):
        y0 = SIDE_R + .25 + i * 1.77
        box(m, (BED[0] + .25, y0, DECK - .3), (-11.3, y0 + 1.72, DECK), WOOD if i % 2 else SOOT)
    # Fangorn logs, bark furrowed, the sawn ends pale with rings; a lopped branch stub.
    for y, z, r, x0, x1 in LOGS:
        m.tube((x0, y, z), (x1, y, z), r, BARK, sides=9)
        for x, s in ((x0, -1), (x1, 1)):
            endgrain(m, (x + s * .04, y, z), (s, 0, 0), r * .93, ENDGRAIN, 9)
    m.tube((-19.5, 1.77, 14.0), (-18.6, 2.6, 15.7), .42, BARK, sides=6, r1=.3)
    endgrain(m, (-18.6, 2.6, 15.7), (.9, .83, 1.7), .29, ENDGRAIN, 6)
    m.tube((-22.0, -2.55, 11.7), (-22.6, -3.6, 12.9), .36, BARK, sides=6, r1=.26)
    # The two-man saw on top, teeth out, handles across.
    blade = [(-23.4, 1.18), (-15.6, 1.18), (-15.6, 2.0), (-19.5, 2.4), (-23.4, 2.0)]
    solid(m, [(x, y, 14.3) for x, y in blade], [(x, y, 14.4) for x, y in blade], STEEL)
    for i in range(22):
        x = -23.3 + i * .35
        tri = [(x, 1.2), (x + .35, 1.2), (x + .175, .78)]
        solid(m, [(a, b, 14.32) for a, b in tri], [(a, b, 14.38) for a, b in tri], STEEL)
    for x in (-23.75, -15.25):
        m.tube((x, .9, 14.4), (x, 2.7, 14.4), .2, LEATHER, sides=6)
        box(m, (x - .35 if x < -20 else x - .1, 1.45, 14.25), (x + .1 if x < -20 else x + .35, 1.95, 14.45), IRON)
    # Two chains over the stack and the saw, made fast to rings on the walls.
    hull = (arc((-2.55, 10.65), 1.6, math.pi, math.pi * .72, 3) + arc((-1.11, 12.93), 1.6, math.pi * .8, math.pi * .5, 4)
            + [(1.77, 14.62)] + arc((1.77, 12.93), 1.65, math.pi * .45, math.pi * .2, 4)
            + arc((3.21, 10.65), 1.6, math.pi * .28, 0, 3))
    for x in (-21.6, -16.9):
        path = [(x, SIDE_R + .3, DECK + .1)] + [(x + rng.uniform(-.05, .05), y, z) for y, z in hull] + [(x, SIDE_L - .3, DECK + .1)]
        chain(m, path, CHAIN)
        for y in (SIDE_R + .3, SIDE_L - .3):
            box(m, (x - .35, y - .2, DECK - .1), (x + .35, y + .2, DECK + .3), SILVER)
    # A crate of fresh-cast iron ingots for the forges, at the front of the bed.
    x0, x1, y0, y1, z1 = -14.05, -11.3, SIDE_R + .3, SIDE_L - .3, 11.3
    for a, b in (((x0, y0), (x0 + .3, y1)), ((x1 - .3, y0), (x1, y1)), ((x0, y0), (x1, y0 + .3)), ((x0, y1 - .3), (x1, y1))):
        box(m, (a[0], a[1], DECK), (b[0], b[1], z1), SOOT)
    for x in (x0, x1):
        for y in (y0, y1):
            box(m, (x - .12, y - .12, DECK), (x + .12, y + .12, z1 + .1), IRON)
    box(m, (x0 - .05, y0 - .05, z1 - .3), (x1 + .05, y0 + .32, z1), IRON)
    box(m, (x0 - .05, y1 - .32, z1 - .3), (x1 + .05, y1 + .05, z1), IRON)

    def ingot(xa, xb, ya, yb, z, along_x):
        lo = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
        inset = (.18, .1) if along_x else (.1, .18)
        hi = [(xa + inset[0], ya + inset[1]), (xb - inset[0], ya + inset[1]), (xb - inset[0], yb - inset[1]), (xa + inset[0], yb - inset[1])]
        solid(m, [(a, b, z) for a, b in lo], [(a, b, z + .42) for a, b in hi], INGOT)
    for i in range(8):
        y = y0 + .4 + i * .98
        ingot(x0 + .45, x1 - .45, y, y + .82, 10.55, True)
    for x in (-13.5, -12.65, -11.8):
        ingot(x - .36, x + .36, -1.6 + rng.uniform(-.3, .3), 1.5 + rng.uniform(-.3, .3), 10.97, False)


class Porter(Unit):
    """EA's orc porter, which Isengard, Mordor, the Goblins and Angmar all draw: ours ships under a
    name of its own and only IsengardPorter's Draw is repointed to it (Angmar keeps EA's)."""
    model, skeleton = "WUPorter_SKN", "MUOrcPrtr_SKL"
    own_model = "IUBuilder_SKN"
    objects = {"IsengardPorter": ("data\\ini\\object\\evilfaction\\units\\isengard\\porter.ini", "ModuleTag_01")}
    anims = ("idla", "idlb", "runa", "wlka", "fira", "diea", "dieb")
    expected = {"wuporter_skn": "0f3aa90adf5415d9242ba1c7cf33807ce3d6bd2774b73e6bd195ca31cae8e47f",
                "muorcprtr_skl": "7d4d2bd88941d3c41bef5f778a9fa47f0967f10067220a2a97aa404d149766df"}
    # The orc draws IUPorter (no house colour, like EA's); the cart and load draw IUCrafts, whose
    # mask is EA's cart mask tiled (only the HOUSE cloth samples its alpha). One atlas, two names.
    textures = {"muorcporter.tga": "IUPorter.tga", "muportcart.tga": "IUCrafts.tga",
                "guporter_build.tga": "IUCrafts.tga"}
    house = {"IUCrafts.tga": "HC_IUCrafts.tga"}
    mask = ("HC_MUPortCart.tga", "HC_IUCrafts.tga")
    archive = "!!!!!!!!!!!!sagekit-isengard-builder.big"
    smooth = ("ORCPORTER",)
    views = {**{k: v for k, v in DEFAULT_VIEWS.items() if k != "work"},
             "fall": View("dieb", 40, fit=True)}
    labels = ("EA'S ORC PORTER (ISENGARD)", "ISENGARD URUK LABOURER - DESIGN PREVIEW")

    def design(self, w, sk):
        meshes = {n: self.mesh(w, sk, n, keep=n == "ORCPORTER")
                  for n in ("ORCPORTER", "CART", "CARTSUPPLIES", "WHEEL_R01", "WHEEL_L01")}
        for m in meshes.values():
            m.uv_for = uvs
        walls(meshes["CART"])
        shafts(meshes["CART"])
        heraldry(meshes["CART"])
        load(meshes["CARTSUPPLIES"])
        wheel(meshes["WHEEL_R01"], WHEEL_R, "WHEEL_R01")
        wheel(meshes["WHEEL_L01"], WHEEL_L, "WHEEL_L01")
        return meshes

    def check(self, b, original, new, sk):
        assert new.meshes["BUCKET"].bytes == original.meshes["BUCKET"].bytes, "BUCKET"

    def paint(self, b):
        from .paint import atlas
        return atlas(b)
