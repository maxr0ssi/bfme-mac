"""Angmar builder: a Hill-men thrall's cart hauling for the Witch-king out of Carn Dum.

Frost-rimed dark timber and iron bands, iron-shod wheels, a load of blue-black quarried stone
dusted with snow, a block of ice chained down, a cold-fire lantern on a crook (a pale-blue flame
in an iron cage), the citadel's frozen-tip tines in small on the corners, icicles under the bed and
a player-colour pennant. EA's orc porter (body, skeleton, animations) is kept; his robe is re-dyed
in cold slate wool on a private sheet, and EA's bucket is a banded pail with a rime-white rim on
the same bone. All coordinates are the model's rest space; the cart and its load follow the CART
bone, each wheel its own bone. Palette A2 (assets/angmar/style.py). Ships as KUBuilder_SKN (AngmarPorter
only). python3 -m sagekit unit angmar/porter --render (docs/UNITS.md).
"""
import math
import random

from assets.angmar.style import PALETTE
from sagekit.formats.w3dpose import hlod
from sagekit.units import DEFAULT_VIEWS, Mesh, Unit, View
from sagekit.units.mesh import uv_for
from sagekit.units.paint import crop_rgb, magick, ramp_bytes, raw

from .kit import block, chain, disc_ring, hexa, horn, ice_block, icicle, shard, slab, tine

(IRON, IRON_DK, STEEL, PLANK, PLANK_DK, TIMBER, STONE, STONE_LT, SNOW, ICE, ICE_DK, FLAME, FLAME_HOT,
 RIME, CHAIN, LEATHER) = range(16)
FLAG = 16                    # player colour: the pennant (left half, EA's cart mask)

# The cart box (EA's: x -23.3..-10.9, y -4.4..5.1), its axle and wheels (EA's wheel geometry)
X0, X1, Y0, Y1 = -23.2, -11.0, -4.4, 5.1
FLOOR, TOP = 4.7, 8.4
AXLE_X, AXLE_Z = -16.907, 4.046
WHEELS = ((-5.94, "WHEEL_R01", -1), (6.58, "WHEEL_L01", 1))
SHAFTS = (-4.7, 5.3)         # EA's shafts, where the orc's hands grip them (z 9.1, to x 6.0)
BUCKET = (-15.51, .05, 5.96)  # EA's bucket bone: the pail rides here, lifted out to throw water
LANTERN = (-11.2, -1.4)      # the crook's post, on the front wall
PENNANT = (-22.65, 4.55)     # the pennant's pole, the rear left corner


class Piece(Mesh):
    """The unit Mesh, plus the pennant's tag in the atlas' left half where EA's cart mask (tiled
    64 px) is solid: a 12 x 29 block of every tile."""

    @staticmethod
    def uv_for(tag, u, v):
        if tag == FLAG:
            return ((52.9 + 10.2 * u) / 2048, 1 - (133.4 - 26.6 * v) / 1024)
        return uv_for(tag, u, v)


def cart(m, rng):
    # Warm plank floor on two iron-shod sills; the axle under it.
    for i in range(6):
        x = X0 + .1 + i * 2.02
        slab(m, (x, Y0 + .1, 4.1), (x + 1.92, Y1 - .1, FLOOR), PLANK_DK if i % 2 else PLANK)
    for y in (Y0 + .8, Y1 - .8):
        slab(m, (X0 - .2, y - .4, 3.4), (X1 + .2, y + .4, 4.15), IRON_DK)
    m.tube((AXLE_X, -5.6, AXLE_Z), (AXLE_X, 6.3, AXLE_Z), .38, IRON_DK, sides=8)
    # Side walls of three frost-grained boards, iron bands and corner plates, a crust of snow on top.
    for y0, y1, s in ((Y0, Y0 + .4, -1), (Y1 - .4, Y1, 1)):
        for k, (z0, z1) in enumerate(((FLOOR - .3, 5.95), (6.0, 7.2), (7.25, TOP))):
            slab(m, (X0, y0, z0), (X1, y1, z1), TIMBER if k % 2 else PLANK_DK)
        yb = y0 - .12 if s < 0 else y1
        for x in (X0 + .25, -17.1, X1 - .25):
            slab(m, (x - .3, yb - .04, FLOOR - .35), (x + .3, yb + .16, TOP + .05), IRON)
            for z in (5.4, 6.6, 7.8):
                slab(m, (x - .12, yb + (-.12 if s < 0 else .14), z - .12), (x + .12, yb + (-.02 if s < 0 else .24), z + .12), STEEL)
        snow(m, (X0, y0 - .05, TOP), (X1, y1 + .05, TOP), rng)
    for x0, x1, s in ((X0, X0 + .4, -1), (X1 - .4, X1, 1)):
        for k, (z0, z1) in enumerate(((FLOOR - .3, 5.95), (6.0, 7.2), (7.25, TOP))):
            slab(m, (x0, Y0 + .4, z0), (x1, Y1 - .4, z1), TIMBER if k % 2 else PLANK_DK)
        xb = x0 - .12 if s < 0 else x1
        slab(m, (xb, Y0 + .3, 6.25), (xb + .12, Y1 - .3, 6.95), IRON)
        snow(m, (x0 - .05, Y0 + .4, TOP), (x1 + .05, Y1 - .4, TOP), rng)
    # Icicles under the bed, along every edge, uneven.
    for x in [X0 + .4 + i * .62 for i in range(20)]:
        for y in (Y0 + .05, Y1 - .05):
            if rng.random() < .75 and abs(x - AXLE_X) > .9:
                icicle(m, (x + rng.uniform(-.15, .15), y, FLOOR - .3), rng.uniform(.5, 1.5), rng.uniform(.14, .22), ICE)
    for y in [Y0 + .5 + i * .62 for i in range(14)]:
        for x in (X0 + .05, X1 - .05):
            if rng.random() < .7:
                icicle(m, (x, y + rng.uniform(-.15, .15), FLOOR - .3), rng.uniform(.5, 1.3), rng.uniform(.14, .2), ICE)
    # The frozen-tip tines on the four corners, leaning out; the rear ones taller.
    for x, y, h in ((X0 + .2, Y0 + .2, 3.6), (X0 + .2, Y1 - .2, 3.6), (X1 - .2, Y0 + .2, 2.6), (X1 - .2, Y1 - .2, 2.6)):
        tine(m, (x, y, TOP - .7), ((1 if x > -17 else -1) * .7, 1 if y > 0 else -1), h, .34, IRON, ICE, SNOW)
    # The shafts keep EA's line and grip; frost-grained, iron-banded, leather where the hands hold.
    for y in SHAFTS:
        m.box((X0 - .3, y - .3, 8.8), (6.0, y + .3, 9.4), TIMBER)
        slab(m, (-1.9, y - .36, 8.74), (1.4, y + .36, 9.46), LEATHER)
        for x in (-9.5, -5.2, -2.3, 1.8, 5.6):
            slab(m, (x - .22, y - .38, 8.72), (x + .22, y + .38, 9.48), IRON_DK)
    m.box((5.0, -4.6, 8.75), (5.9, 5.2, 9.45), TIMBER)


def snow(m, lo, hi, rng):
    """A ragged crust of snow along a wall top (lo, hi: its footprint at height lo z)."""
    (x, y, z), (X, Y, _) = lo, hi
    n = max(1, round(max(X - x, Y - y) / 2.2))
    along_x = X - x >= Y - y
    for i in range(n):
        a, b = i / n, (i + 1) / n
        if along_x:
            p0, p1 = (x + (X - x) * a, y, z), (x + (X - x) * b, Y, z)
        else:
            p0, p1 = (x, y + (Y - y) * a, z), (X, y + (Y - y) * b, z)
        h = rng.uniform(.16, .32)
        lo4 = [(p0[0], p0[1], z), (p1[0], p0[1], z), (p1[0], p1[1], z), (p0[0], p1[1], z)]
        ins = .3 * (p1[0] - p0[0] if along_x else p1[1] - p0[1]) / 2
        hi4 = [(p0[0] + (ins if along_x else .05), p0[1] + (.05 if along_x else ins), z + h),
               (p1[0] - (ins if along_x else .05), p0[1] + (.05 if along_x else ins), z + h),
               (p1[0] - (ins if along_x else .05), p1[1] - (.05 if along_x else ins), z + h),
               (p0[0] + (ins if along_x else .05), p1[1] - (.05 if along_x else ins), z + h)]
        hexa(m, lo4 + hi4, SNOW)


def wheels(meshes):
    # Iron-shod wheels: a dark felloe, a pale frost-rimed iron tyre with hobnails, eight timber
    # spokes, an iron hub with a rime cap.
    for y, bone, s in WHEELS:
        m = meshes[bone]
        disc_ring(m, (AXLE_X, AXLE_Z), y - .42, y + .42, 3.25, 3.75, PLANK_DK, bone, 20)
        disc_ring(m, (AXLE_X, AXLE_Z), y - .5, y + .5, 3.75, 4.08, STEEL, bone, 20)
        for i in range(10):
            a = i * math.tau / 10
            p = (AXLE_X + 4.08 * math.cos(a), y, AXLE_Z + 4.08 * math.sin(a))
            slab(m, (p[0] - .2, y - .56, p[2] - .2), (p[0] + .2, y + .56, p[2] + .2), IRON_DK, bone)
        for i in range(8):
            a = i * math.tau / 8 + .2
            end = (AXLE_X + 3.4 * math.cos(a), y, AXLE_Z + 3.4 * math.sin(a))
            m.tube((AXLE_X, y, AXLE_Z), end, .26, TIMBER, bone, sides=5)
        m.tube((AXLE_X, y - .6, AXLE_Z), (AXLE_X, y + .6, AXLE_Z), .95, IRON, bone, sides=8)
        m.tube((AXLE_X, y + s * .6, AXLE_Z), (AXLE_X, y + s * 1.1, AXLE_Z), .7, RIME, bone, sides=8, r1=.35)


def lantern(m):
    # A crook on the front wall reaching forward over the shafts, a cold-fire lantern hanging from
    # it: an iron cage under an open crown, a pale-blue flame inside on a dish.
    x, y = LANTERN
    m.tube((x, y, FLOOR), (x, y, 15.6), .26, IRON_DK, sides=6)
    horn(m, [(x, y, 15.6), (x + .5, y, 16.4), (x + 1.4, y, 16.6), (x + 2.3, y, 16.2)], .22, .14, IRON_DK, sides=5)
    hang = (x + 2.3, y, 16.2)
    chain(m, [hang, (hang[0], hang[1], 15.0)], .5, .06, CHAIN)
    cx, cy, z0, z1, r = hang[0], hang[1], 11.2, 14.1, 1.15
    corners = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in (math.pi / 4 + k * math.pi / 2 for k in range(4))]
    for px, py in corners:
        m.tube((px, py, z0), (px, py, z1), .08, IRON, sides=4)
    for z in (z0, z1):
        for i in range(4):
            a, b = corners[i], corners[(i + 1) % 4]
            m.tube((a[0], a[1], z), (b[0], b[1], z), .1, IRON, sides=4)
    slab(m, (cx - r * .8, cy - r * .8, z0 - .25), (cx + r * .8, cy + r * .8, z0 + .05), IRON_DK)
    # an open crown over the cage, so the flame shows from the RTS camera: four bars to a ring
    ring = (cx, cy, z1 + .85)
    for px, py in corners:
        m.tube((px, py, z1), ring, .08, IRON, sides=4)
    m.tube(ring, (cx, cy, 15.05), .14, IRON, sides=4)
    # the flame: a tall pale-blue tongue, a white core, two short licks
    base = (cx, cy, z0 + .1)
    horn(m, [base, (cx + .1, cy - .06, z0 + 1.2), (cx - .05, cy + .05, z0 + 2.75)], .78, .02, FLAME, sides=6)
    horn(m, [(cx, cy, z0 + .15), (cx + .05, cy, z0 + 1.2), (cx, cy, z0 + 2.1)], .5, .02, FLAME_HOT, sides=5)
    for dx, dy, h in ((.28, .18, 1.0), (-.25, -.2, .8)):
        horn(m, [(cx + dx, cy + dy, z0 + .1), (cx + dx * 1.2, cy + dy * 1.2, z0 + h)], .2, .02, FLAME, sides=4)


def pennant(m):
    # A swallow-tailed pennant in the player's colour on an iron pole with a frozen point, flying
    # back off the rear left corner.
    x, y = PENNANT
    m.tube((x, y, FLOOR), (x, y, 19.2), .2, IRON_DK, sides=6)
    m.tube((x, y, 19.2), (x, y, 19.9), .32, ICE, sides=5, r1=.26)
    m.tube((x, y, 19.9), (x, y, 21.2), .26, SNOW, sides=5, r1=.02)
    m.tube((x, y, 18.7), (x - 3.7, y, 18.7), .12, IRON_DK, sides=5)
    top, bot = 18.6, 15.0
    # columns along the pennant's length (-x); its lower edge rises, then the swallow tail
    xs = [x - .2, x - 1.3, x - 2.4, x - 3.5]
    lows = [bot, bot + .2, bot + .5, bot + .4]
    P = lambda px, z, dy: (px, y + dy, z)  # noqa: E731
    for side, dy in ((1, .03), (-1, -.03)):
        def put(q, uv):
            m.face(q if side < 0 else q[::-1], FLAG, None, uv if side < 0 else uv[::-1])   # q winds to -y
        for (xa, za), (xb, zb) in zip(zip(xs, lows), zip(xs[1:], lows[1:])):
            ua, ub = (x - xa) / 3.7, (x - xb) / 3.7
            put([P(xa, za, dy), P(xa, top, dy), P(xb, top, dy), P(xb, zb, dy)], [(ua, .1), (ua, 1), (ub, 1), (ub, .1)])
        mid = (bot + .4 + top) / 2
        put([P(xs[-1], lows[-1], dy), P(xs[-1], mid, dy), P(xs[-1] - 1.6, bot - .2, dy)], [(.9, .1), (.9, .5), (1, .1)])
        put([P(xs[-1], mid, dy), P(xs[-1], top, dy), P(xs[-1] - 1.6, top + .3, dy)], [(.9, .5), (.9, 1), (1, 1)])


def load(m, rng):
    # Rear right: a sawn block of ice, chained down across the cart. Rear left: blue-black quarried
    # blocks stacked four high, snow on their tops. Front: a few low blocks clear of the pail.
    lo, hi = (-22.8, -4.0, FLOOR), (-18.4, -.3, 10.8)
    ice_block(m, lo, hi, rng, ICE, ICE_DK)
    for base, d, ln in (((-21.6, -2.9, 10.5), (-.3, -.25, 1), 3.8), ((-20.3, -1.5, 10.7), (.15, .3, 1), 3.0),
                        ((-19.4, -3.0, 10.2), (.45, -.3, 1), 2.2)):
        shard(m, base, d, ln, .5, ICE, sides=5, point=.45, tip=SNOW)
    for x in (-21.6, -19.6):
        chain(m, [(x, Y0 - .1, TOP + .1), (x, -4.15, 10.6), (x, -2.2, 11.15), (x, -.1, 10.7), (x, .3, FLOOR + 1.6)], 1.0, .1, CHAIN)
    layers = [((-21.6, 1.35), (2.4, 2.3, 1.7), .04), ((-21.6, 3.75), (2.4, 2.3, 1.7), -.03),
              ((-19.0, 1.4), (2.5, 2.4, 1.7), -.05), ((-19.0, 3.8), (2.4, 2.3, 1.7), .06),
              ((-21.3, 2.5), (2.6, 3.0, 1.6), .12), ((-18.9, 2.7), (2.2, 2.6, 1.6), -.1),
              ((-20.3, 2.2), (2.8, 2.5, 1.5), .3), ((-20.6, 3.3), (1.8, 1.7, 1.3), -.25)]
    heights = [FLOOR, FLOOR, FLOOR, FLOOR, FLOOR + 1.7, FLOOR + 1.7, FLOOR + 3.3, FLOOR + 4.8]
    for k, (((cx, cy), size, yaw), z) in enumerate(zip(layers, heights)):
        block(m, (cx, cy, z), size, yaw, STONE, SNOW if k >= 4 else None, rng, side=STONE_LT if k % 3 == 0 else None)
    # front: low blocks either side of the pail, out of its way (it lifts out up and to +y)
    for (cx, cy), size, yaw in (((-12.7, -2.3), (2.4, 2.4, 1.3), .1), ((-16.2, -3.1), (2.2, 1.9, 1.2), -.08),
                                ((-12.6, .6), (1.8, 2.0, 1.0), -.2)):
        block(m, (cx, cy, FLOOR), size, yaw, STONE, SNOW, rng, side=STONE_LT)
    shard(m, (-12.4, 3.4, FLOOR), (.1, -.2, 1), 1.6, .55, ICE, sides=4, point=.5, tip=SNOW)
    block(m, (-15.5, .15, FLOOR), (3.2, 3.0, .45), 0, STONE, SNOW, rng)        # the pail stands on this


def pail(m):
    # EA's bucket as a stave pail of warm boards, iron bands, a rime-white rim, cold dark water.
    x, y, z = BUCKET
    m.tube((x, y, z + .05), (x, y, z + 2.6), 1.35, PLANK, sides=8, r1=1.6)
    for h, r in ((.5, 1.43), (2.0, 1.6)):
        m.tube((x, y, z + h), (x, y, z + h + .25), r, IRON, sides=8)
    m.tube((x, y, z + 2.6), (x, y, z + 2.72), 1.62, RIME, sides=8)
    m.tube((x, y, z + 2.2), (x, y, z + 2.3), 1.48, ICE_DK, sides=8)
    pts = [(x + 1.62 * math.cos(a), y, z + 2.5 + 1.3 * math.sin(a)) for a in [k * math.pi / 6 for k in range(7)]]
    for p, q in zip(pts, pts[1:]):
        m.tube(p, q, .09, IRON, sides=4)


# Swatches from palette A2; grain from EA's own cart, load and orc sheets.
SWATCHES = [("iron", .42), ("iron", .22), ("trim", .5), ("planks", .4),
            ("planks", .24), ("timber", .42), ("stone", .40), ("stone", .56),
            ("ice", .93), ("ice", .62), ("ice", .38), ("fire", .55),
            ("fire", .97), ("trim", .85), ("iron", .62), ("planks", .18)]
GRAIN = [("muportcart", (14, 60, 244, 124)), ("muportcart", (2, 0, 250, 26)),
         ("guporter_build", (62, 22, 98, 58)), ("muorcporter", (2, 60, 70, 170))]
WHICH = [1, 1, 1, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 1, 1, 3]
GAIN = [.9, .9, .7, .9, .9, 1.0, .7, .7, .25, .45, .45, .2, .1, .4, .9, .9]
# The orc's robe on EA's 256 px sheet (x0, y0, x1, y1): re-dyed; the apron plate, belt and skin are EA's
ROBE = [(53, 0, 152, 100), (73, 122, 152, 210), (0, 178, 73, 210), (0, 0, 38, 55), (195, 0, 256, 42),
        (63, 210, 152, 256)]
WOOL = [(0, (.02, .025, .036)), (.4, (.09, .11, .145)), (.75, (.22, .26, .32)), (1, (.40, .45, .53))]
PREVIEW_RED = (.50, .07, .05)        # the previews' stand-in for the player's colour


class Porter(Unit):
    """EA's orc porter, which Isengard, Mordor, the Goblins and Angmar all draw: ours ships under a
    name of its own and only AngmarPorter's Draw is repointed to it (its child objects inherit it)."""
    model, skeleton = "WUPorter_SKN", "MUOrcPrtr_SKL"
    own_model = "KUBuilder_SKN"
    objects = {"AngmarPorter": ("data\\ini\\object\\evilfaction\\units\\angmar\\angmarporter.ini", "ModuleTag_01")}
    anims = ("idla", "idlb", "runa", "wlka", "fira", "diea", "dieb")
    expected = {"wuporter_skn": "0f3aa90adf5415d9242ba1c7cf33807ce3d6bd2774b73e6bd195ca31cae8e47f",
                "muorcprtr_skl": "7d4d2bd88941d3c41bef5f778a9fa47f0967f10067220a2a97aa404d149766df"}
    # Two private names on one atlas: only the cart's maps to the player-colour mask, so the
    # mask's tiles never tint the orc.
    textures = {"muorcporter.tga": "KUCraftsO.tga", "muportcart.tga": "KUCrafts.tga",
                "guporter_build.tga": "KUCrafts.tga", "guporter_cart.tga": "KUCrafts.tga"}
    house = {"KUCrafts.tga": "HC_KUCrafts.tga"}
    mask = ("HC_MUPortCart.tga", "HC_KUCrafts.tga")
    archive = "!!!!!!!!!!!!sagekit-angmar-builder.big"
    smooth = ("ORCPORTER",)
    views = {**{k: v for k, v in DEFAULT_VIEWS.items() if k != "work"},     # EA's orc porter never builds
             "fall": View("dieb", 10, fit=True),
             "load": View("idla", 0, target=(-17, .3, 9), distance=46, elevation=40, azimuth=-60)}
    labels = ("EA'S ORC PORTER (ANGMAR)", "ANGMAR THRALL - DESIGN PREVIEW")

    def mesh(self, w, sk, name, keep=False, skin=None):
        return Piece(w.meshes[name], sk, keep=keep, names=self.textures, bone=self.bone,
                     rigid_bone=hlod(w.data)[2].get(name.upper(), 0), skin=skin)

    def design(self, w, sk):
        names = ("CART", "CARTSUPPLIES", "WHEEL_L01", "WHEEL_R01", "BUCKET", "ORCPORTER")
        meshes = {n: self.mesh(w, sk, n, keep=n == "ORCPORTER") for n in names}
        rng = random.Random(1974)
        cart(meshes["CART"], rng)
        lantern(meshes["CART"])
        pennant(meshes["CART"])
        wheels(meshes)
        load(meshes["CARTSUPPLIES"], rng)
        pail(meshes["BUCKET"])
        return meshes

    def check(self, b, original, new, sk):
        assert new.meshes["ORCPORTER"].textures == ["KUCraftsO.tga"], new.meshes["ORCPORTER"].textures

    def paint(self, b):
        work = b.work
        orc = bytearray(raw(b.src / "muorcporter.dds", "rgb"))
        for x0, y0, x1, y1 in ROBE:
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    i = (yy * 256 + xx) * 3
                    lum = sum(orc[i:i + 3]) / 765
                    orc[i:i + 3] = ramp_bytes(WOOL, .08 + lum * 1.25)
        (work / "orc.ppm").write_bytes(b"P6\n256 256\n255\n" + orc)
        # The pennant's tile: EA's cart mask, its solid pixels in the preview red
        mask = raw(b.src / self.mask[0].lower())
        iron = ramp_bytes(PALETTE.ramps["iron"], .3)
        hc = bytearray()
        for yy in range(256):
            for xx in range(256):
                i = ((yy % 64) * 64 + xx % 64) * 4
                a, g = mask[i + 3] / 255, mask[i] / 255
                hc += bytes(round(c * (1 - a) + 255 * p * (.45 + .9 * g) * a) for c, p in zip(iron, PREVIEW_RED))
        (work / "hc.ppm").write_bytes(b"P6\n256 256\n255\n" + hc)
        grains = [crop_rgb(b.src / (s + ".dds"), box, work / ("grain_%d.rgb" % k)) for k, (s, box) in enumerate(GRAIN)]
        means = [sum(g) / len(g) / 255 for g in grains]          # grain about its own mean: hue and value are A2's
        rng, pixels = random.Random(73), bytearray()
        for y in range(1024):
            for x in range(1024):
                tag = (y // 256) * 4 + x // 256
                material, mid = SWATCHES[tag]
                u, v = x % 256, y % 256
                data = grains[WHICH[tag]]
                o = (v * 256 + u) * 3
                lum = sum(data[o:o + 3]) / 765
                edge = min(u, v, 255 - u, 255 - v) / 255
                value = (mid + (lum - means[WHICH[tag]]) * GAIN[tag] + rng.uniform(-.02, .02)
                         + (.08 if edge < .018 else -.05 if edge < .03 else 0))
                pixels += ramp_bytes(PALETTE.ramps[material], value)
        (work / "materials.ppm").write_bytes(b"P6\n1024 1024\n255\n" + pixels)
        atlas = work / "kucrafts.png"
        magick("-size", "1024x1024", "tile:" + str(work / "orc.ppm"), work / "hc.ppm", "-geometry", "+0+0",
               "-composite", work / "materials.ppm", "+append", atlas)
        return atlas
