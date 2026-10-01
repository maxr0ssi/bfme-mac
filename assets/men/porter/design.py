"""Gondor stone-mason: dressed white stone on a dark timber cart, a mason's mallet and plumb line,
and the White Tree on a sable headboard and on a gonfalon in player colour.

EA's man, rig and animations are kept (MenPorter and ArnorPorter both draw GUPorter_SKN); every new
piece follows one of EA's bones. Coordinates are the model's rest space: the man faces +x between
the shafts, the cart's centre line is y = 0.335. python3 -m sagekit unit men/porter --render
(docs/UNITS.md).
"""
import math
import random

from assets.men.style import PALETTE
from sagekit.units import Unit, View
from sagekit.units.mesh import uv_for
from sagekit.units.paint import crop_rgb, magick, ramp_colour, raw

WOOD, TIMBER, IRON, STEEL, GOLD, SABLE, STONE, STONE2, WHITE, ROPE, LEATHER, BRIGHT, STONE3, \
    DARK, SLATE, GILT = range(16)
HC = 99                         # player-colour cloth: EA's shirt, which HC_GUPorter tints
Y0 = .335                       # EA's cart centre line (wheels at -5.94 and 6.58, shafts -4.67, 5.34)
WHEEL_X, WHEEL_Z = .485, 4.046  # EA's wheel centre (the wheel pivots sit off the wheels)

# The cloth samples a clean patch of EA's shirt in the atlas' unused top-left tile: there EA's
# mask (tiled by the framework) tints it with the player colour, as it tints the man's shirt.
HC_BOX = (12, 58, 34, 100)      # x0, y0, x1, y1 in the 256-pixel sheet
SHIRT = (0, 0, 100, 108)        # EA's player-colour shirt in the sheet (HC_GUPorter's alpha)


def hc_uv(tag, u, v):
    if tag != HC:
        return uv_for(tag, u, v)
    x0, y0, x1, y1 = HC_BOX
    return ((x0 + (x1 - x0) * u) / 2048, 1 - (y0 + (y1 - y0) * (1 - v)) / 1024)


def piece(m):
    m.uv_for = hc_uv
    return m


def ring(m, centre, axis, r0, r1, half, tag, bone, n=24):
    """A flat annulus of thickness 2*half about `axis` ("y" or "z"): wheel rims, tyres, coils."""
    cx, cy, cz = centre
    for i in range(n):
        a, b = i * math.tau / n, (i + 1) * math.tau / n
        def p(r, t, h):
            return (cx + r * math.cos(t), cy + h, cz + r * math.sin(t)) if axis == "y" else \
                   (cx + r * math.cos(t), cy + r * math.sin(t), cz + h)
        for h, flip in [(-half, axis == "y"), (half, axis != "y")]:
            q = [p(r0, a, h), p(r1, a, h), p(r1, b, h), p(r0, b, h)]
            m.face(q if flip else q[::-1], tag, bone)
        for r, out in [(r0, False), (r1, True)]:
            q = [p(r, a, -half), p(r, b, -half), p(r, b, half), p(r, a, half)]
            m.face(q if out == (axis == "z") else q[::-1], tag, bone)


def white_tree(m, at, s, bone="CART", stars=True):
    """The White Tree of Gondor and its stars, raised off a panel: at(u, v) is the panel point."""
    def t(a, b, r, tag=WHITE):
        m.tube(at(*a), at(*b), r * s, tag, bone, sides=5)
    t((0, -1.9 * s), (0, 1.0 * s), .2)
    for k in (-1, 1):
        t((0, -1.9 * s), (k * .75 * s, -2.25 * s), .14)
        t((0, -.6 * s), (k * 1.2 * s, .25 * s), .13)
        t((k * 1.2 * s, .25 * s), (k * 1.45 * s, .95 * s), .1)
        t((0, .05 * s), (k * .85 * s, 1.0 * s), .12)
        t((0, .6 * s), (k * .45 * s, 1.55 * s), .1)
    t((0, 1.0 * s), (0, 1.75 * s), .12)
    if stars:
        for i in range(-3, 4) if stars is True else stars:
            a = math.radians(90 - i * 26)
            u, v = 2.15 * s * math.cos(a), .55 * s + 1.9 * s * math.sin(a)
            m.tube(at(u, v, -.02), at(u, v, .16), .2 * s, WHITE, bone, sides=4)


def cart(m):
    # Plank floor across the bed, a dark chassis and an iron axle.
    for i in range(5):
        y = -3.87 + i * 1.682
        m.box((-5.9, y + .04, 4.5), (5.9, y + 1.64, 4.86), TIMBER if i % 2 else WOOD)
    for y in (-2.6, 3.27):
        m.box((-6.2, y - .35, 3.85), (6.2, y + .35, 4.7), DARK)
    m.tube((WHEEL_X, -6.7, WHEEL_Z), (WHEEL_X, 7.34, WHEEL_Z), .34, IRON, sides=8)
    # Low side boards so the white load reads; steel straps; the shafts ride along their tops.
    for y0, y1 in [(-4.32, -3.87), (4.54, 4.99)]:
        for z0, z1 in [(4.9, 6.78), (6.84, 8.62)]:
            m.box((-5.9, y0, z0), (5.9, y1, z1), WOOD)
        out = y0 - .06 if y0 < 0 else y1 + .06
        for x in (-3.6, 0, 3.6):
            m.box((x - .22, min(out, y0 + .1), 5.1), (x + .22, max(out, y1 - .1), 8.7), IRON)
    # Shafts and crossbar on EA's grip line (z 9.1, y -4.67 / 5.34); leather grips, steel ferrules.
    for y in (-4.67, 5.34):
        m.box((-6.7, y - .33, 8.77), (23.3, y + .33, 9.43), TIMBER)
        m.box((14.0, y - .35, 8.75), (18.4, y + .35, 9.45), LEATHER)
        for x in (6.9, 12.2, 22.1):
            m.box((x - .2, y - .4, 8.68), (x + .2, y + .4, 9.52), STEEL)
    m.box((22.45, -4.67, 8.77), (23.3, 5.34, 9.43), TIMBER)
    # Corner posts with steel caps and small gilt orbs, like the citadel's domes. The front post
    # on the camera side stays low: EA's hammer leans in that corner whenever the cart is pulled.
    for x in (-6.13, 6.13):
        for y in (-4.1, 4.77):
            top = {(-6.13, -4.1): 22.0, (6.13, -4.1): 7.55}.get((x, y), 9.9)
            m.box((x - .33, y - .33, 4.4), (x + .33, y + .33, top), TIMBER if top > 10 else WOOD)
            if top < 22:
                m.box((x - .4, y - .4, top - .4), (x + .4, y + .4, top), STEEL)
            if top == 9.9:
                m.tube((x, y, 9.9), (x, y, 10.15), .2, STEEL, sides=6)
                m.tube((x, y, 10.15), (x, y, 10.75), .34, GOLD, sides=8, r1=.08)
    # Tailboard and a low front board.
    m.box((-6.35, -3.87, 4.9), (-5.9, 4.54, 8.62), WOOD)
    m.box((-6.42, -3.9, 8.5), (-5.83, 4.57, 8.78), STEEL)
    m.box((5.9, -3.87, 4.9), (6.35, 4.54, 7.45), WOOD)
    m.box((5.83, -3.9, 7.25), (6.42, 4.57, 7.5), STEEL)
    # Crest: a sable gable in a steel frame with the White Tree and seven stars, like the citadel
    # gate's pediment, facing the man and the RTS camera. It stays under his arms when he reaches
    # into the cart (z < 10.4) and clear of the hammer's corner (y > -2.2).
    x0, x1, ya, yb, z0, z1, za = 5.9, 6.35, Y0 - 2.25, Y0 + 2.25, 5.1, 9.2, 10.3
    m.box((x0, ya, z0), (x1, yb, z1), SABLE)
    for x, flip in [(x0, True), (x1, False)]:
        tri = [(x, ya, z1), (x, yb, z1), (x, Y0, za)]
        m.face(tri[::-1] if flip else tri, SABLE)
    for y in (ya, yb):
        q = [(x0, y, z1), (x1, y, z1), (x1, Y0, za), (x0, Y0, za)]
        m.face(q if y == ya else q[::-1], SABLE)
        m.tube((6.42, y, z1), (6.42, Y0, za), .15, STEEL, sides=6)
        m.tube((6.42, y, z0), (6.42, y, z1), .15, STEEL, sides=6)
    m.tube((6.42, ya, z0 + .1), (6.42, yb, z0 + .1), .15, STEEL, sides=6)
    m.tube((x1, Y0, za - .1), (x1, Y0, za + .25), .22, GOLD, sides=8, r1=.05)
    white_tree(m, lambda u, v, d=0: (6.42 + d, Y0 + u, 7.4 + v), .72)
    # The plumb line hangs from an arm on the gonfalon post, on the camera side.
    m.tube((-6.13, -4.1, 13.2), (-6.13, -5.45, 13.2), .1, STEEL, sides=5)
    m.tube((-6.13, -5.4, 13.2), (-6.13, -5.4, 10.4), .05, ROPE, sides=4)
    m.tube((-6.13, -5.4, 10.4), (-6.13, -5.4, 9.5), .32, GOLD, sides=8, r1=.03)
    # The gonfalon: player-colour cloth with the White Tree, on a crossbar from the back post.
    m.tube((-6.13, -4.1, 22.0), (-6.13, -4.1, 22.3), .22, STEEL, sides=6)
    m.tube((-6.13, -4.1, 22.3), (-6.13, -4.1, 23.2), .36, GOLD, sides=8, r1=.05)
    m.tube((-6.13, -4.4, 21.4), (-6.13, -.1, 21.4), .11, STEEL, sides=6)
    m.tube((-6.13, -.1, 21.4), (-6.13, .15, 21.4), .2, GOLD, sides=6)
    flag_x, top, bot, y_a, y_b = -6.13, 21.3, 16.4, -3.95, -.35
    m.box((flag_x - .07, y_a, bot), (flag_x + .07, y_b, top), HC)
    mid = (y_a + y_b) / 2
    for side in (-1, 1):
        for ya_, yb_ in [(y_a, mid), (mid, y_b)]:
            tip = (ya_ + yb_) / 2
            tri = [(flag_x + side * .07, ya_, bot), (flag_x + side * .07, yb_, bot),
                   (flag_x + side * .07, tip, bot - 1.3)]
            m.face(tri if side < 0 else tri[::-1], HC, uvs=[(0, 1), (1, 1), (.5, 0)])
    for side in (-1, 1):
        white_tree(m, lambda u, v, d=0, s=side: (flag_x + s * (.08 + d), mid - s * u, 18.75 + v), .7,
                   stars=(-1, 0, 1))
    # Open-spoke wheels on EA's wheel bones: dark felloes, steel tyres, steel hubs, gilt bosses.
    for y, bone in [(-5.94, "WHEEL_R01"), (6.58, "WHEEL_L01")]:
        ring(m, (WHEEL_X, y, WHEEL_Z), "y", 3.6, 4.2, .4, WOOD, bone)
        ring(m, (WHEEL_X, y, WHEEL_Z), "y", 4.2, 4.66, .45, IRON, bone)
        for i in range(10):
            a = i * math.tau / 10
            m.tube((WHEEL_X, y, WHEEL_Z),
                   (WHEEL_X + 3.75 * math.cos(a), y, WHEEL_Z + 3.75 * math.sin(a)), .22, TIMBER, bone, sides=6)
        m.tube((WHEEL_X, y - .62, WHEEL_Z), (WHEEL_X, y + .62, WHEEL_Z), .72, STEEL, bone, sides=12)
        s = -1 if y < 0 else 1
        m.tube((WHEEL_X, y + s * .6, WHEEL_Z), (WHEEL_X, y + s * .82, WHEEL_Z), .34, GOLD, bone, sides=8)


def supplies(m):
    # Dressed white ashlar around a well in the middle, where EA's bucket rides (x -3.3..2.6).
    m.box((-5.75, -3.75, 4.88), (-3.5, .25, 7.25), STONE)
    m.box((-5.75, .45, 4.88), (-3.5, 4.4, 7.25), STONE3)
    m.box((-5.6, -3.5, 7.3), (-3.55, 2.2, 9.3), STONE2)
    m.box((-5.45, -3.1, 9.35), (-3.7, -.2, 11.2), STONE)
    m.box((-5.3, -2.75, 11.25), (-3.85, -.75, 12.7), WHITE)
    m.box((2.85, -3.75, 4.88), (5.75, -.2, 7.25), STONE2)
    m.box((2.85, .0, 4.88), (5.75, 4.4, 7.25), STONE)
    # A long lintel stone and a cut cornice along the sides of the well.
    m.box((-3.35, -3.75, 4.88), (2.65, -2.05, 6.95), STONE3)
    m.box((-3.2, -3.6, 6.95), (2.5, -2.2, 7.35), WHITE)
    # A carved capital ready for a column: round echinus under a square abacus.
    cx, cy = 4.25, 2.3
    m.tube((cx, cy, 7.25), (cx, cy, 7.95), .95, STONE2, sides=12)
    m.tube((cx, cy, 7.95), (cx, cy, 8.1), 1.07, STONE3, sides=12)
    m.tube((cx, cy, 8.1), (cx, cy, 8.85), 1.0, STONE, sides=12, r1=1.45)
    m.box((cx - 1.5, cy - 1.5, 8.85), (cx + 1.5, cy + 1.5, 9.45), WHITE)
    # A coil of rope on the front blocks.
    for z in (7.25, 7.72):
        ring(m, (3.85, -1.95, z + .24), "z", .6, 1.15, .23, ROPE, "CART", n=14)
    # The mason's mallet on the back stack and a chisel on the cornice. The well's +y side stays
    # open: EA's bucket slides there when the man dies.
    m.tube((-4.6, -.1, 9.5), (-4.6, 1.6, 9.5), .17, TIMBER, sides=6)
    m.tube((-5.4, 1.95, 9.75), (-3.8, 1.95, 9.75), .55, TIMBER, sides=10)
    for x in (-5.3, -3.9):
        m.tube((x - .08, 1.95, 9.75), (x + .08, 1.95, 9.75), .59, STEEL, sides=10)
    m.tube((-2.9, -2.9, 7.55), (-2.0, -2.9, 7.55), .2, WOOD, sides=6)
    m.tube((-2.0, -2.9, 7.55), (-1.05, -2.9, 7.55), .1, BRIGHT, sides=5)
    m.box((-1.1, -3.12, 7.48), (-.75, -2.68, 7.62), BRIGHT)
    # A steel square leaning on the back stack.
    m.box((-3.5, -3.2, 7.3), (-3.3, -2.9, 10.2), BRIGHT)
    m.box((-3.5, -3.2, 9.9), (-1.9, -2.9, 10.2), BRIGHT)


# The man's waist in rest space (x, y) at z 9.2, front to back: his belt runs just outside it.
WAIST = [(17.87, 0), (17.42, -1.54), (15.58, -2.82), (13.82, -1.24), (13.48, 0),
         (13.82, 1.24), (15.58, 2.82), (17.42, 1.54)]


def belt(m, z0, z1, gap, tag, bone):
    cx, cy = 15.7, 0
    ring = [(cx + (x - cx) * (1 + gap / math.hypot(x - cx, y - cy)), cy + y * (1 + gap / math.hypot(x - cx, y - cy)))
            for x, y in WAIST]
    for i in range(len(ring)):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % len(ring)]
        (px, py), (qx, qy) = WAIST[i], WAIST[(i + 1) % len(WAIST)]
        m.face([(ax, ay, z0), (ax, ay, z1), (bx, by, z1), (bx, by, z0)], tag, bone)
        m.face([(px, py, z1), (qx, qy, z1), (bx, by, z1), (ax, ay, z1)], tag, bone)
        m.face([(px, py, z0), (ax, ay, z0), (bx, by, z0), (qx, qy, z0)], tag, bone)


def outfit(m, original, sk):
    # A mason's tool belt: leather band, steel buckle, a pouch on the left hip and a chisel in a
    # loop on the right, all on the pelvis, clear of the thighs' swing.
    belt(m, 8.95, 9.45, .14, DARK, "PELVIS")
    m.box((17.98, -.38, 8.9), (18.12, .38, 9.5), STEEL, "PELVIS")
    m.box((15.0, 2.98, 7.9), (16.7, 3.5, 9.3), LEATHER, "PELVIS")
    m.box((14.92, 2.95, 8.85), (16.78, 3.56, 9.35), DARK, "PELVIS")
    m.box((15.45, -3.12, 8.6), (15.95, -2.94, 9.6), DARK, "PELVIS")
    m.tube((15.7, -3.2, 7.4), (15.7, -3.2, 9.0), .09, BRIGHT, "PELVIS", sides=5)
    m.tube((15.7, -3.2, 9.0), (15.7, -3.2, 10.0), .17, TIMBER, "PELVIS", sides=6)
    # EA's hammer, its vertices and bones untouched, takes a steel head and an ash handle.
    from sagekit.formats import w3dpose as P
    from sagekit.formats.w3d import STAGE_TEXCOORDS
    bones = P.influences(original.bytes)
    hammer = sk.index("B_HAMMER")
    for i, (v, b) in enumerate(zip(original.verts, bones)):
        if b == hammer:
            u, w = original.uv[i]
            tag = STEEL if P.point(sk.rest[b], v)[0] > 18.3 else TIMBER
            entry = m.verts[i]
            m.verts[i] = entry[:4] + ({**entry[4], STAGE_TEXCOORDS: uv_for(tag, u % 1, w % 1)},)


# (palette ramp, middle value, grain source): Gondor's white stone, steel and sable, dark timber.
SWATCHES = [("wood", .34, 0), ("wood", .5, 0), ("iron", .7, 2), ("trim", .72, 2),
            ("gold", .74, 2), ("enamel", .5, 1), ("stone", .84, 1), ("stone", .76, 1),
            ("stone", .93, 1), ("wood", .76, 0), ("wood", .66, 3), ("trim", .9, 2),
            ("stone", .68, 1), ("wood", .2, 0), ("tiles", .55, 1), ("gold", .9, 2)]
# Painted grain from EA's own sheets (crops in the 256-pixel grid): planks, stone, steel, cloth.
CROPS = [("guporter_cart", (30, 30, 225, 60)), ("guporter_build", (100, 30, 160, 62)),
         ("guporter_cart", (2, 2, 250, 20)), ("guporter", (5, 125, 95, 250))]


class Porter(Unit):
    """Gondor's porter, drawn by MenPorter and ArnorPorter alike: redesigned in place."""
    model, skeleton = "GUPorter_SKN", "GUPorter_SKL"
    anims = ("idla", "idlb", "runa", "wlka", "wrka", "wrkb", "fira", "diea", "dieb")
    expected = {"guporter_skn": "5055def66f8974b886111cf7be4287d0b19537ea38f1f482030524021bbf5710",
                "guporter_skl": "cb8a6fa38469fd95ac1c791843a75c013fdec5684503b4711b0485a4eee5e9ec"}
    textures = {"GUPorter.tga": "GUCrafts.tga", "GUPorter_Cart.tga": "GUCrafts.tga",
                "GUPorter_Build.tga": "GUCrafts.tga"}
    house = {"GUCrafts.tga": "HC_GUCrafts.tga"}
    mask = ("HC_GUPorter.tga", "HC_GUCrafts.tga")
    archive = "!!!!!!!!!!!!sagekit-men-builder.big"
    same_bones = ("CART_MESH", "CARTSUPPLIES")
    smooth = ("GUPORTERLUIGI",)
    views = {"portrait": View("idla", 0, target=(8, 0, 11), distance=80, elevation=22, size=(1200, 1100)),
             **{k: View(a, f, target=(8, 0, 11), distance=88, size=(1100, 950))
                for k, (a, f) in {"rts": ("idla", 0), "run": ("runa", 8), "walk": ("wlka", 8),
                                  "water": ("fira", 38)}.items()},
             "work": View("wrkb", 23, fit=True, size=(1100, 950)),
             "death": View("diea", 45, size=(1100, 950), fit=True),
             "fall": View("dieb", 10, size=(1100, 950), fit=True)}
    labels = ("EA'S MEN OF THE WEST BUILDER", "GONDOR STONE-MASON - REVIEW")

    def design(self, w, sk):
        meshes = {n: piece(self.mesh(w, sk, n, keep=n == "GUPORTERLUIGI"))
                  for n in ("CART_MESH", "CARTSUPPLIES", "GUPORTERLUIGI")}
        cart(meshes["CART_MESH"])
        supplies(meshes["CARTSUPPLIES"])
        outfit(meshes["GUPORTERLUIGI"], w.meshes["GUPORTERLUIGI"], sk)
        return meshes

    def check(self, b, original, new, sk):
        assert new.meshes["BUCKET"].bytes == original.meshes["BUCKET"].bytes, "BUCKET"
        # The cloth samples EA's mask where it is fully player colour.
        mask = raw(b.src / self.mask[0].lower())
        x0, y0, x1, y1 = HC_BOX
        assert all(mask[(y * 256 + x) * 4 + 3] == 255 for y in range(y0, y1) for x in range(x0, x1)), \
            "the cloth patch leaves EA's player-colour mask"

    def paint(self, b):
        samples = []
        for i, (source, box) in enumerate(CROPS):
            data = crop_rgb(b.src / (source + ".dds"), box, b.work / ("grain_%d.rgb" % i))
            samples.append((data, sum(data) / len(data) / 255))
        rng, pixels = random.Random(41), bytearray()
        for y in range(1024):
            for x in range(1024):
                tag = (y // 256) * 4 + x // 256
                material, mid, src = SWATCHES[tag]
                u, v = x % 256, y % 256
                data, mean = samples[src]
                lum = sum(data[(v * 256 + u) * 3:(v * 256 + u) * 3 + 3]) / 765
                edge = min(u, v, 255 - u, 255 - v)
                value = mid + (lum - mean) * (.9 if material == "wood" else .8 if material == "stone" else .45) + rng.uniform(-.02, .02)
                value += .08 if edge < 5 else -.05 if edge < 9 else 0
                pixels.extend(round(255 * c) for c in ramp(material, value))
        ppm = b.work / "materials.ppm"
        ppm.write_bytes(b"P6\n1024 1024\n255\n" + pixels)
        # Left half: EA's sheet 4 x 4 (the man samples one tile). In the unused top-left tile the
        # shirt the mask tints is painted navy, the Men's preview stand-in for the player colour.
        sheet = bytearray(raw(b.src / "guporter.dds", "rgb"))
        mask = raw(b.src / self.mask[0].lower())
        x0, y0, x1, y1 = SHIRT
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                i = yy * 256 + xx
                a = mask[i * 4 + 3] / 255
                if a:
                    lum = sum(sheet[i * 3:i * 3 + 3]) / 765
                    navy = ramp("cloth", .35 + lum * .45)
                    sheet[i * 3:i * 3 + 3] = bytes(round(255 * (c * a + o / 255 * (1 - a)))
                                                   for c, o in zip(navy, sheet[i * 3:i * 3 + 3]))
        corner = b.work / "corner.ppm"
        corner.write_bytes(b"P6\n256 256\n255\n" + bytes(sheet))
        atlas = b.work / "gucrafts.png"
        magick("-size", "1024x1024", "tile:" + str(b.src / "guporter.dds"), corner,
               "-geometry", "+0+0", "-composite", ppm, "+append", atlas)
        return atlas



def ramp(material, value):
    return ramp_colour(PALETTE.ramps[material], value)
