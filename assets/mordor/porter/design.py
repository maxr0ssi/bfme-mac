"""Mordor builder: a slave-driver's cart of black iron, a load of rough basalt, an ember brazier in
a claw of hooked spikes, chains, shackles and a whip.

EA's orc porter (body, skeleton, animations) is kept; the orc's robe is re-dyed in ash and soot on
a private sheet, and EA's wooden bucket is an iron pail on the same bone. All coordinates are the model's rest space; the cart and its load follow
the CART bone, each wheel its own bone. Ships as MUBuilder_SKN (MordorPorter only).
python3 -m sagekit unit mordor/porter --render (docs/UNITS.md).
"""
import math
import random

from assets.mordor.style import PALETTE
from sagekit.formats.w3dpose import hlod
from sagekit.units import DEFAULT_VIEWS, Mesh, Unit, View
from sagekit.units.mesh import uv_for
from sagekit.units.paint import crop_rgb, magick, ramp_bytes, raw

from .kit import blade, chain, disc_ring, hook, horn, outward, ring, rock, slab

(IRON, IRON_DK, STEEL, CHAR, BASALT, BASALT_LT, ASH, EMBER, FLAME, TRIM, LEATHER, CHAIN, RUST, HOT,
 BASALT_HI, TIMBER) = range(16)
BAND, FLAG = 16, 17          # player colour: the cart's iron bands, the banner (left half, EA's mask)

# The cart box (EA's: x -23.3..-10.9, y -4.4..5.1), its axle and wheels (EA's wheel geometry)
X0, X1, Y0, Y1 = -23.2, -11.0, -4.4, 5.1
CY = (Y0 + Y1) / 2
FLOOR, TOP = 4.7, 8.2
AXLE_X, AXLE_Z = -16.907, 4.046
WHEELS = ((-5.94, "WHEEL_R01", -1), (6.58, "WHEEL_L01", 1))
SHAFTS = (-4.7, 5.3)         # EA's shafts, where the orc's hands grip them (z 9.1, to x 6.0)
BRAZIER = (-12.55, -2.6)
BUCKET = (-15.51, .05, 5.96)       # EA's bucket bone: the pail rides here, lifted out to throw water


class Piece(Mesh):
    """The unit Mesh, plus two tags in the atlas' left half where EA's cart mask (tiled 64 px) is
    solid: a 7-pixel band (the iron straps) and a 12 x 29 block (the banner)."""

    @staticmethod
    def uv_for(tag, u, v):
        if tag == BAND:
            return ((6 + 240 * u) / 2048, 1 - (69.9 - 5.0 * v) / 1024)
        if tag == FLAG:
            return ((52.9 + 10.2 * u) / 2048, 1 - (133.4 - 26.6 * v) / 1024)
        return uv_for(tag, u, v)


def cart(m):
    # Charred plank floor on two black iron beams; the axle under it.
    for i in range(6):
        x = X0 + .1 + i * 2.02
        slab(m, (x, Y0 + .1, 4.1), (x + 1.92, Y1 - .1, FLOOR), CHAR if i % 2 else TIMBER)
    for y in (Y0 + .8, Y1 - .8):
        slab(m, (X0 - .2, y - .4, 3.4), (X1 + .2, y + .4, 4.15), IRON_DK)
    m.tube((AXLE_X, -5.6, AXLE_Z), (AXLE_X, 6.3, AXLE_Z), .38, IRON_DK, sides=8)
    # Black iron walls, a player-colour band round their top, rivets, and a row of jagged teeth.
    for y0, y1, s in ((Y0, Y0 + .38, -1), (Y1 - .38, Y1, 1)):
        m.box((X0, y0, FLOOR - .3), (X1, y1, TOP), IRON)
        yb = y0 - .1 if s < 0 else y1
        slab(m, (X0 + .25, yb, 6.95), (X1 - .25, yb + .1, 7.85), BAND)
        for x in (X0 + .7, -17.1, X1 - .7):                 # upright straps over the band
            slab(m, (x - .28, yb - .06, 5.0), (x + .28, yb + .16, TOP + .05), IRON_DK)
        y = (y0 + y1) / 2
        for i in range(9):
            x = X0 + .9 + i * 1.3
            h = 1.5 if i % 2 else 1.0
            blade(m, (x - .5, y, TOP - .1), (x + .5, y, TOP - .1), (x + .25, y + s * .25, TOP + h), .2, STEEL if i % 2 else IRON)
    for x0, x1, s in ((X0, X0 + .38, -1), (X1 - .38, X1, 1)):
        m.box((x0, Y0 + .3, FLOOR - .3), (x1, Y1 - .3, TOP), IRON)
        xb = x0 - .1 if s < 0 else x1
        slab(m, (xb, Y0 + .5, 6.95), (xb + .1, Y1 - .5, 7.85), BAND)
    # Ember-lit trim along the wall tops (the citadel's orange edges).
    for lo, hi in (((X0, Y0 - .04, TOP), (X1, Y0 + .42, TOP + .16)), ((X0, Y1 - .42, TOP), (X1, Y1 + .04, TOP + .16)),
                   ((X0 - .04, Y0, TOP), (X0 + .42, Y1, TOP + .16)), ((X1 - .42, Y0, TOP), (X1 + .04, Y1, TOP + .16))):
        slab(m, lo, hi, TRIM)
    # The claw: three hooked spikes off each corner, leaning out, steel points; the rear ones tall.
    for x, y, h in ((X0 + .25, Y0 + .25, 3.6), (X0 + .25, Y1 - .25, 3.0), (X1 - .25, Y0 + .25, 2.4), (X1 - .25, Y1 - .25, 2.6)):
        ox, oy = (1 if x > -17 else -1), (1 if y > CY else -1)
        hook(m, (x, y, TOP - .6), (ox * .25, oy * .25, 1), (ox, oy, 0), h, .36, IRON, tip=STEEL)
        hook(m, (x, y, TOP - .4), (ox * .9, oy * .2, 1), (ox, 0, 0), h * .62, .24, IRON, tip=STEEL, sides=4)
        hook(m, (x, y, TOP - .4), (ox * .2, oy * .9, 1), (0, oy, 0), h * .62, .24, IRON, tip=STEEL, sides=4)
    # The shafts keep EA's line and grip; leather where the hands hold, iron bands, hooked ends.
    for y in SHAFTS:
        m.box((X0 - .3, y - .3, 8.8), (6.0, y + .3, 9.4), TIMBER)
        slab(m, (-1.9, y - .36, 8.74), (1.4, y + .36, 9.46), LEATHER)
        for x in (-9.5, -5.2, -2.3, 1.8):
            slab(m, (x - .22, y - .38, 8.72), (x + .22, y + .38, 9.48), IRON_DK)
        hook(m, (5.95, y, 9.1), (1, 0, -.15), (0, 0, -1), 1.3, .22, IRON, tip=STEEL)
    m.box((5.0, -4.6, 8.75), (5.9, 5.2, 9.45), TIMBER)


def wheels(meshes):
    # Heavy iron-shod wheels: a black tyre with short blades, six flat spokes, a spiked hub.
    for y, bone, s in WHEELS:
        m = meshes[bone]
        disc_ring(m, (AXLE_X, AXLE_Z), y - .45, y + .45, 3.45, 3.75, CHAR, bone, 20)
        disc_ring(m, (AXLE_X, AXLE_Z), y - .5, y + .5, 3.75, 4.1, IRON, bone, 20)
        for i in range(10):
            a = i * math.tau / 10 + .1
            p = lambda r, da=0: (AXLE_X + r * math.cos(a + da), y, AXLE_Z + r * math.sin(a + da))  # noqa: E731
            blade(m, p(4.05, -.09), p(4.05, .09), p(4.38, .14), .5, STEEL if i % 2 else IRON, bone)
        for i in range(6):
            a = i * math.tau / 6
            end = (AXLE_X + 3.6 * math.cos(a), y, AXLE_Z + 3.6 * math.sin(a))
            m.tube((AXLE_X, y, AXLE_Z), end, .3, IRON_DK, bone, sides=4)
            hook_at = (AXLE_X + 2.3 * math.cos(a), y, AXLE_Z + 2.3 * math.sin(a))
            blade(m, hook_at, (AXLE_X + 2.9 * math.cos(a), y, AXLE_Z + 2.9 * math.sin(a)),
                  (AXLE_X + 2.2 * math.cos(a + .32), y, AXLE_Z + 2.2 * math.sin(a + .32)), .22, IRON, bone)
        m.tube((AXLE_X, y - .62, AXLE_Z), (AXLE_X, y + .62, AXLE_Z), 1.0, IRON, bone, sides=8)
        m.tube((AXLE_X, y + s * .55, AXLE_Z), (AXLE_X, y + s * .75, AXLE_Z), 1.12, TRIM, bone, sides=8)
        horn(m, [(AXLE_X, y + s * .7, AXLE_Z), (AXLE_X, y + s * 1.6, AXLE_Z), (AXLE_X, y + s * 2.4, AXLE_Z)],
             .55, .04, IRON_DK, bone, sides=6, tip=STEEL)


def brazier(m):
    # An iron fire basket on a post at the front corner: embers heaped in it, flames rising,
    # five hooked spikes clawing up round it (the citadel's crowns in small).
    x, y = BRAZIER
    m.tube((x, y, FLOOR), (x, y, 9.6), .32, IRON_DK, sides=6)
    rim, r = 10.9, 1.45
    sq = [(x + r * math.cos(a), y + r * math.sin(a)) for a in (0, math.pi / 2, math.pi, 1.5 * math.pi)]
    bottom = (x, y, 9.3)
    centre = (x, y, 10.3)
    for i in range(4):
        a, b = sq[i], sq[(i + 1) % 4]
        outward(m, (bottom, (a[0], a[1], rim), (b[0], b[1], rim)), centre, IRON)
        m.tube((a[0], a[1], rim), (b[0], b[1], rim), .16, TRIM, sides=4)
    coals = [(x, y, rim + .55)] + [(px, py, rim) for px, py in sq]
    for i in range(4):
        outward(m, (coals[0], coals[1 + i], coals[1 + (i + 1) % 4]), (x, y, rim - 1), EMBER)
    for dx, dy, h in ((0, 0, 4.2), (.6, .35, 2.8), (-.55, .4, 2.4), (.15, -.6, 3.0), (-.4, -.35, 2.0)):
        b = (x + dx, y + dy, rim + .1)
        horn(m, [b, (b[0] + .12, b[1] - .06, b[2] + h * .45), (b[0] - .06, b[1] + .05, b[2] + h)],
             .62 if h > 4 else .42, .03, EMBER, sides=5, tip=FLAME)
    for i in range(5):
        a = i * math.tau / 5 + .3
        base = (x + 1.3 * math.cos(a), y + 1.3 * math.sin(a), rim - .6)
        hook(m, base, (math.cos(a) * .35, math.sin(a) * .35, 1), (-math.cos(a), -math.sin(a), 0),
             4.2 if i % 2 else 3.4, .3, IRON, tip=STEEL)


def gear(m, rng):
    # Shackles on a short chain off each rear side, a coiled whip on the right shaft.
    for y, s in ((Y0 - .55, -1), (Y1 + .55, 1)):
        pts = chain(m, (X0 + .9, y, 8.6), (-18.0, y, 8.6), 2.2, .9, .1, CHAIN)
        low = pts[len(pts) // 2]
        for dx in (-.55, .55):
            ring(m, (low[0] + dx, y + s * .1, low[2] - .75), (1, 0, .2), .5, .13, CHAIN, segments=6)
    y = SHAFTS[1] + .55
    for i in range(3):
        r, dx = 1.3 - i * .12, i * .18
        pts = [(-7.4 + dx + r * math.cos(a), y + i * .13, 7.6 + r * math.sin(a)) for a in [k * math.tau / 8 for k in range(9)]]
        for p, q in zip(pts, pts[1:]):
            m.tube(p, q, .15, RUST, sides=4)
    m.tube((-7.4, y - .1, 9.05), (-6.7, y - .15, 5.9), .24, LEATHER, sides=6)
    m.tube((-6.7, y - .15, 5.9), (-6.65, y - .15, 5.5), .3, TRIM, sides=6)
    horn(m, [(-8.3, y + .3, 6.9), (-8.0, y + .35, 5.4), (-8.4, y + .35, 4.2)], .13, .03, RUST, sides=4)


def load(m, rng):
    # Rough basalt heaped high in the back, three hewn basalt columns leaning out of it, a flat
    # slab where EA's bucket rides, a few low lumps by the brazier.
    cx, cy = -19.9, .35
    for k, (ex, ey, n, sz) in enumerate(((3.6, 3.9, 11, 1.2), (2.6, 3.1, 8, 1.35), (1.7, 2.2, 5, 1.4),
                                          (.9, 1.2, 3, 1.3), (0, 0, 1, 1.2))):
        for i in range(n):
            a = i * math.tau / n + k * .7 + rng.uniform(-.2, .2)
            c = (cx + ex * .8 * math.cos(a), cy + ey * .8 * math.sin(a), FLOOR + 2.2 + k * 1.6 + rng.uniform(-.15, .2))
            size = (sz * rng.uniform(.85, 1.15), sz * rng.uniform(.85, 1.1), sz * rng.uniform(.7, .9))
            if math.dist(c[:2], BUCKET[:2]) < 1.9 + size[0] * .8 and c[2] + size[2] > BUCKET[2]:
                continue                                    # the pail's room, and its way out
            rock(m, c, size, rng, rng.choice((BASALT, BASALT, BASALT_LT, ASH)))
    for (x, y), top, lean in [((-21.4, -.9), (-22.7, -2.4, 17.2), .82), ((-20.2, 1.9), (-21.6, 3.6, 15.0), .74)]:
        m.tube((x, y, FLOOR), top, lean, BASALT, sides=6)
        m.tube(top, (top[0] - .05, top[1], top[2] + .04), lean - .04, BASALT_HI, sides=6)
    m.tube((-16.4, -3.6, 9.2), (-22.6, 3.2, 12.6), .66, BASALT, sides=6)
    rock(m, (-15.5, .15, 5.15), (1.9, 1.8, .55), rng, BASALT)
    # lumps round EA's bucket (it rides at x -15.5 and lifts out up and to +y in the water animation)
    for c, sz in (((-12.7, .6, 6.0), (.8, 1.0, .9)), ((-15.6, -2.9, 6.0), (1.1, .9, 1.0)),
                  ((-13.1, 3.5, 5.6), (1.0, .8, .75)), ((-15.0, 3.9, 5.4), (1.0, .6, .6))):
        rock(m, c, sz, rng, rng.choice((BASALT, ASH)))


def pail(m):
    # EA's wooden bucket as a black iron pail, banded, an ember-copper rim and a bail handle.
    x, y, z = BUCKET
    m.tube((x, y, z + .05), (x, y, z + 2.6), 1.35, IRON_DK, sides=8, r1=1.6)
    for h, r in ((.5, 1.43), (2.45, 1.64)):
        m.tube((x, y, z + h), (x, y, z + h + .22), r, IRON, sides=8)
    m.tube((x, y, z + 2.67), (x, y, z + 2.7), 1.5, CHAIN, sides=8)
    pts = [(x + 1.62 * math.cos(a), y, z + 2.5 + 1.3 * math.sin(a)) for a in [k * math.pi / 6 for k in range(7)]]
    for p, q in zip(pts, pts[1:]):
        m.tube(p, q, .09, IRON, sides=4)


def banner(m):
    # A ragged war banner in the player's colour on a spiked pole at the rear left corner.
    x, y = X0 + .55, Y1 - .55
    m.tube((x, y, FLOOR), (x, y, 18.6), .2, IRON_DK, sides=6)
    horn(m, [(x, y, 18.6), (x, y, 20.0)], .26, .03, STEEL, sides=5)
    m.tube((x, y, 18.0), (x + 3.0, y, 18.0), .14, IRON_DK, sides=5)
    blade(m, (x + 2.9, y, 17.8), (x + 2.9, y, 18.2), (x + 3.6, y, 18.15), .1, STEEL)
    top = 17.9
    xs = [x + .25, x + 1.0, x + 1.7, x + 2.4, x + 2.95]
    tails = [12.6, 13.6, 11.9, 13.2, 12.3]
    for (xa, za), (xb, zb) in zip(zip(xs, tails), zip(xs[1:], tails[1:])):
        ua, ub = (xa - xs[0]) / (xs[-1] - xs[0]), (xb - xs[0]) / (xs[-1] - xs[0])
        for side, dy in ((1, .03), (-1, -.03)):
            q = [(xa, y + dy, za), (xb, y + dy, zb), (xb, y + dy, top), (xa, y + dy, top)]
            uv = [(ua, .15), (ub, .15), (ub, 1), (ua, 1)]
            if side < 0:
                q, uv = q[::-1], uv[::-1]
            m.face(q, FLAG, None, uv)


# Swatches from palette F2; grain from EA's own cart, load and orc sheets.
SWATCHES = [("iron", .66), ("iron", .45), ("steel", .66), ("wood", .62),
            ("rock", .44), ("stone", .66), ("rock", .58), ("fire", .7),
            ("fire", .92), ("trim", .62), ("wood", .86), ("iron", .88),
            ("trim", .35), ("fire", .45), ("rock", .68), ("wood", .45)]
GRAIN = [("muportcart", (14, 60, 244, 124)), ("muportcart", (2, 0, 250, 26)),
         ("guporter_build", (62, 22, 98, 58)), ("muorcporter", (2, 60, 70, 170))]
WHICH = [1, 1, 3, 0, 2, 2, 2, 2, 3, 1, 0, 1, 1, 2, 2, 0]
# The orc's robe on EA's 256 px sheet (x0, y0, x1, y1): re-dyed; the apron plate, belt and skin are EA's
ROBE = [(53, 0, 152, 100), (73, 122, 152, 210), (0, 178, 73, 210), (0, 0, 38, 55), (195, 0, 256, 42),
        (63, 210, 152, 256)]
RAG = [(0, (.02, .018, .017)), (.4, (.10, .085, .075)), (.75, (.24, .21, .19)), (1, (.40, .36, .32))]
PREVIEW_RED = (.50, .07, .05)        # the previews' stand-in for the player's colour


class Porter(Unit):
    """EA's orc porter, which Isengard, Mordor, the Goblins and Angmar all draw: ours ships under a
    name of its own and only MordorPorter's Draw is repointed to it (Angmar keeps EA's)."""
    model, skeleton = "WUPorter_SKN", "MUOrcPrtr_SKL"
    own_model = "MUBuilder_SKN"
    objects = {"MordorPorter": ("data\\ini\\object\\evilfaction\\units\\mordor\\porter.ini", "ModuleTag_01")}
    anims = ("idla", "idlb", "runa", "wlka", "fira", "diea", "dieb")
    expected = {"wuporter_skn": "0f3aa90adf5415d9242ba1c7cf33807ce3d6bd2774b73e6bd195ca31cae8e47f",
                "muorcprtr_skl": "7d4d2bd88941d3c41bef5f778a9fa47f0967f10067220a2a97aa404d149766df"}
    # Two private names on one atlas: only the cart's maps to the player-colour mask, so the
    # mask's tiles never tint the orc.
    textures = {"muorcporter.tga": "MUCraftsO.tga", "muportcart.tga": "MUCrafts.tga",
                "guporter_build.tga": "MUCrafts.tga", "guporter_cart.tga": "MUCrafts.tga"}
    house = {"MUCrafts.tga": "HC_MUCrafts.tga"}
    mask = ("HC_MUPortCart.tga", "HC_MUCrafts.tga")
    archive = "!!!!!!!!!!!!sagekit-mordor-builder.big"
    smooth = ("ORCPORTER",)
    views = {**{k: v for k, v in DEFAULT_VIEWS.items() if k != "work"},     # EA's orc porter never builds
             "fall": View("dieb", 10, fit=True),
             "load": View("idla", 0, target=(-17, .3, 9), distance=46, elevation=40, azimuth=-60)}
    labels = ("EA'S ORC PORTER (MORDOR)", "MORDOR SLAVE-DRIVER - DESIGN PREVIEW")

    def mesh(self, w, sk, name, keep=False, skin=None):
        return Piece(w.meshes[name], sk, keep=keep, names=self.textures, bone=self.bone,
                     rigid_bone=hlod(w.data)[2].get(name.upper(), 0), skin=skin)

    def design(self, w, sk):
        names = ("CART", "CARTSUPPLIES", "WHEEL_L01", "WHEEL_R01", "BUCKET", "ORCPORTER")
        meshes = {n: self.mesh(w, sk, n, keep=n == "ORCPORTER") for n in names}
        rng = random.Random(1937)
        cart(meshes["CART"])
        brazier(meshes["CART"])
        gear(meshes["CART"], rng)
        banner(meshes["CART"])
        wheels(meshes)
        load(meshes["CARTSUPPLIES"], rng)
        pail(meshes["BUCKET"])
        return meshes

    def check(self, b, original, new, sk):
        assert new.meshes["ORCPORTER"].textures == ["MUCraftsO.tga"], new.meshes["ORCPORTER"].textures

    def paint(self, b):
        work = b.work
        orc = bytearray(raw(b.src / "muorcporter.dds", "rgb"))
        for x0, y0, x1, y1 in ROBE:
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    i = (yy * 256 + xx) * 3
                    lum = sum(orc[i:i + 3]) / 765
                    orc[i:i + 3] = ramp_bytes(RAG, .08 + lum * 1.25)
        (work / "orc.ppm").write_bytes(b"P6\n256 256\n255\n" + orc)
        # The banner's and bands' tile: EA's cart mask, its solid pixels in the preview red
        mask = raw(b.src / self.mask[0].lower())
        iron = ramp_bytes(PALETTE.ramps["iron"], .35)
        hc = bytearray()
        for yy in range(256):
            for xx in range(256):
                i = ((yy % 64) * 64 + xx % 64) * 4
                a, g = mask[i + 3] / 255, mask[i] / 255
                hc += bytes(round(c * (1 - a) + 255 * p * (.45 + .9 * g) * a) for c, p in zip(iron, PREVIEW_RED))
        (work / "hc.ppm").write_bytes(b"P6\n256 256\n255\n" + hc)
        grains = [crop_rgb(b.src / (s + ".dds"), box, work / ("grain_%d.rgb" % k)) for k, (s, box) in enumerate(GRAIN)]
        means = [sum(g) / len(g) / 255 for g in grains]          # grain about its own mean: hue and value are F2's
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
                gain = 1.3 if material in ("fire", "stone") else .9
                value = mid + (lum - means[WHICH[tag]]) * gain + rng.uniform(-.025, .025) + (.08 if edge < .018 else -.06 if edge < .03 else 0)
                pixels += ramp_bytes(PALETTE.ramps[material], value)
        (work / "materials.ppm").write_bytes(b"P6\n1024 1024\n255\n" + pixels)
        atlas = work / "mucrafts.png"
        magick("-size", "1024x1024", "tile:" + str(work / "orc.ppm"), work / "hc.ppm", "-geometry", "+0+0",
               "-composite", work / "materials.ppm", "+append", atlas)
        return atlas
