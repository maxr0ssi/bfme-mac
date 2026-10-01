"""Goblin scavenger: EA's orc porter hauling a crooked cart of plunder out of Goblin-town.

Charcoal timber lashed with hide, tarnished scrap plates, mismatched wheels (a solid plank disc and
a salvaged spoked wheel with a bone for a spoke), a heap of loot with a spider-silk cocoon, bones and
skulls, a horned skull on a stake with crimson rags, and a tattered rag standard in the player's
colour. EA's orc, skeleton and animations are kept; every piece follows EA's bones.
Palette E, "blood, iron and bone" (assets/goblins/style.py). The facts: README.md; the recipe API:
docs/UNITS.md. python3 -m sagekit unit goblins/porter --render
"""
import math
import random

from assets.goblins.style import PALETTE
from sagekit.units import DEFAULT_VIEWS, Unit
from sagekit.units.paint import crop_rgb, magick, raw

from .kit import HOUSE, add, beam, bone_shaft, disc, drape, horn, lathe, rag, ring, skull, uvs

(WOOD, TIMBER, IRON, STEEL, RAG, BLOOD, BONE, OLDBONE,
 THONG, SILK, ROCK, STONE, SOCKET, RUST, SACK, PAINT) = range(16)

# EA's cart, in the model's rest space: the bed between the wheels, the shafts the orc holds
# (his hands sit on them in every animation but the water throw), the wheels' centres and radius.
BED = (-22.8, -11.2)                # x, rear and front
SIDE_R, SIDE_L = -4.45, 5.1         # y of the side boards
FLOOR = 5.0
SHAFT_R, SHAFT_L, SHAFT_Z = -4.7, 5.35, 9.1
AXLE = (-16.91, 4.05)               # x, z
WHEEL_R, WHEEL_L, RADIUS = -5.94, 6.58, 4.62


def cart(m):
    rng = random.Random(11)
    # Uneven floor planks over two rough sills and the axle.
    for i, y in enumerate((-3.6, -1.85, -.1, 1.65, 3.4)):
        m.box((BED[0] + rng.uniform(-.3, .2), y - .8, 4.45), (BED[1] + rng.uniform(-.4, .3), y + .8, FLOOR), WOOD if i % 2 else TIMBER)
    for y in (-3.1, 3.8):
        beam(m, (BED[0] - .2, y, 4.15), (BED[1] + .4, y, 4.15), .6, .6, WOOD)
    m.tube((AXLE[0], WHEEL_R + .1, AXLE[1]), (AXLE[0], WHEEL_L - .1, AXLE[1]), .34, RUST, sides=8)
    # Side boards nailed on crooked, one plank short; posts poke above them at odd heights.
    for y, s in ((SIDE_R, -1), (SIDE_L, 1)):
        for k, (z0, z1, dz) in enumerate(((5.0, 6.35, 0), (6.4, 7.7, .25), (7.75, 8.75, -.3))):
            x0 = BED[0] + (1.6 if k == 2 and s < 0 else 0)
            beam(m, (x0, y, (z0 + z1) / 2 - dz / 2), (BED[1], y, (z0 + z1) / 2 + dz / 2), .42, z1 - z0, WOOD if k % 2 else TIMBER)
        for x, top in ((BED[0] + .3, 10.6), (-17.0, 9.6), (BED[1] - .3, 10.2)):
            beam(m, (x, y, 4.4), (x + rng.uniform(-.2, .2), y, top), .55, .55, WOOD)
        # Scrap plates, bent and nailed over the gaps; bright scratched edges.
        for x0, x1, z0, z1, tilt in ((-21.4, -18.6, 5.6, 7.8, .2), (-15.2, -12.4, 6.1, 8.6, -.25)):
            beam(m, (x0, y + s * .27, (z0 + z1) / 2 - tilt), (x1, y + s * .27, (z0 + z1) / 2 + tilt), .1, z1 - z0, IRON)
            for x in (x0 + .3, x1 - .3):
                m.box((x - .13, y + s * .3 - .1, z1 - .55), (x + .13, y + s * .3 + .1, z1 - .3), STEEL)
    # Tailboard and headboard: planks across, lashed at the corners.
    for x in (BED[0], BED[1]):
        for z0, z1 in ((5.0, 6.4), (6.45, 7.85)):
            beam(m, (x, SIDE_R, (z0 + z1) / 2), (x, SIDE_L, (z0 + z1) / 2), .42, z1 - z0, TIMBER)
    for x in (BED[0] + .3, BED[1] - .3):
        for y in (SIDE_R, SIDE_L):
            for z in (6.0, 8.1):
                m.tube((x - .4, y, z), (x + .4, y, z), .38, BLOOD, sides=6)
    # The shafts keep EA's grip line; kinked where they leave the bed, bound in hide at the hands.
    for y in (SHAFT_R, SHAFT_L):
        k = .2 if y > 0 else -.2
        m.tube((-23.6, y, SHAFT_Z), (-11.0, y, SHAFT_Z), .34, WOOD, sides=6)
        m.tube((-11.0, y, SHAFT_Z), (-6.0, y + k, SHAFT_Z + .2), .34, WOOD, sides=6)
        m.tube((-6.0, y + k, SHAFT_Z + .2), (6.0, y, SHAFT_Z), .32, WOOD, sides=6)
        m.tube((-1.4, y, SHAFT_Z), (4.4, y, SHAFT_Z), .41, RAG, sides=6)
        for x in (-11.0, -6.0):
            m.tube((x - .35, y, SHAFT_Z), (x + .35, y, SHAFT_Z), .45, THONG, sides=6)
    m.tube((5.5, SHAFT_R - .25, SHAFT_Z), (5.5, SHAFT_L + .25, SHAFT_Z), .3, WOOD, sides=6)
    # Tusks on the front corners, pointing forward and out.
    for y, s in ((SIDE_R, -1), (SIDE_L, 1)):
        horn(m, (BED[1] + .1, y, 8.9), (BED[1] + 2.6, y + s * .9, 11.6), (.3, s * .3, -.6), .42, BONE)
    # The skull on a stake at the rear right corner, crimson rags knotted under it.
    post = (BED[0] + .25, SIDE_R + .4)
    beam(m, (post[0], post[1], 4.4), (post[0] - .5, post[1] - .15, 21.0), .5, .5, WOOD)
    m.tube((post[0] - .35, post[1] - .1, 17.2), (post[0] - .45, post[1] - .12, 18.0), .45, THONG, sides=6)
    skull(m, (post[0] - .55, post[1] - .15, 20.6), 1.15, (1, -.35), BONE, SOCKET, horns=(BLOOD, 3.2))
    rag(m, (post[0] - .6, post[1] - .5, 18.0), (0, .9, 0), 4.2, RAG, sway=(-.6, -.6, 0), cut=(1, .65, .9))
    rag(m, (post[0] - .3, post[1] + .45, 17.6), (.9, 0, 0), 3.2, BLOOD, sway=(-.4, .5, 0), strips=2, cut=(.8, 1))
    # The rag standard at the front left corner, behind the orc: a crooked pole, a cross-stick
    # along the axle and the player's colour torn into tails (HOUSE: under EA's cart mask, kit.py).
    pole = (BED[1] - .35, SIDE_L - .4)
    top = (pole[0] - .4, pole[1] - .1, 20.6)
    beam(m, (pole[0], pole[1], 4.4), top, .45, .45, WOOD)
    bar = ((top[0] + .05, top[1] - 3.6, 19.8), (top[0] - .05, top[1] + 1.0, 19.6))
    beam(m, bar[0], bar[1], .3, .3, WOOD)
    m.tube(add(top, (0, 0, -1.1)), add(top, (0, 0, -.6)), .36, THONG, sides=6)
    rag(m, (top[0] + .2, top[1] - 3.5, 19.5), (0, 4.3, 0), 6.4, HOUSE, sway=(-1.1, 0, 0),
        strips=4, cut=(.8, 1, .66, .92), wave=.3)
    skull(m, (top[0], top[1], 20.45), .5, (1, -.3), OLDBONE, SOCKET)
    # A bone hung off the cross-stick on a thong, rattling as it rolls.
    for t, length in ((.03, 1.5),):
        p = tuple(a + (b - a) * t for a, b in zip(*bar))
        m.tube(p, (p[0], p[1], p[2] - length), .07, THONG, sides=4)
        bone_shaft(m, (p[0], p[1], p[2] - length), (p[0] + .3, p[1], p[2] - length - 1.5), .16, BONE)


def load(m):
    """The plunder, kept off the middle of the bed where EA's bucket (here a helmet) rides."""
    # A spider-silk cocoon (something still wrapped in it) leaning in the rear left corner.
    a, b = (-21.2, 2.6, 5.0), (-18.6, 3.0, 13.0)
    lathe(m, a, b, [(0, .7), (.08, 1.45), (.22, 1.85), (.36, 1.6), (.5, 1.9), (.66, 1.7), (.8, 1.25),
                    (.92, .8), (1, .35)], SILK, sides=10)
    for t, r in ((.15, 1.72), (.36, 1.66), (.58, 1.86), (.8, 1.3)):
        c = tuple(p + (q - p) * t for p, q in zip(a, b))
        m.tube(add(c, (-.04, 0, -.12)), add(c, (.04, 0, .12)), r, OLDBONE, sides=10)
    for end in ((-22.6, 4.9, 9.0), (-17.0, 4.9, 8.8), (-22.5, .5, 8.0)):
        m.tube((-19.9, 2.8, 10.6), end, .06, SILK, sides=4)
    # A crimson tarp thrown over the sacks in the rear right corner.
    drape(m, (-22.5, -4.15, 5.0), (-17.4, -.5), [((-21.0, -2.3), 1.7, 4.4), ((-18.6, -2.8), 1.4, 3.6)], RAG)
    # A dented round shield hung on the headboard, facing the orc, slashed with war paint.
    c, r = (-10.95, -1.9, 7.4), 2.0
    m.tube(c, (c[0] + .22, c[1], c[2] + .03), r, IRON, sides=12)
    m.tube((c[0] + .05, c[1], c[2]), (c[0] + .28, c[1], c[2] + .03), r + .1, RUST, sides=12, r1=r)
    m.tube((c[0] + .2, c[1], c[2] + .03), (c[0] + .7, c[1], c[2] + .08), .5, STEEL, sides=8, r1=.2)
    for dy in (-.75, .75):
        beam(m, (c[0] + .27, c[1] + dy - .5, c[2] + 1.4), (c[0] + .27, c[1] + dy + .5, c[2] - 1.4), .06, .32, PAINT)
    # The front of the heap: a loot chest, scrap plates, a broken spear and bones.
    m.box((-13.4, -3.9, 5.0), (-11.6, -1.4, 7.4), WOOD)
    m.box((-13.5, -4.0, 7.4), (-11.5, -1.3, 7.9), RUST)
    for x in (-13.0, -12.0):
        m.box((x - .12, -4.05, 5.0), (x + .12, -1.25, 7.95), IRON)
    beam(m, (-13.3, -1.6, 8.1), (-11.7, -3.6, 9.6), 1.6, .12, STEEL)                  # a breastplate's half
    beam(m, (-13.2, 2.0, 5.2), (-12.0, 3.4, 10.8), 1.5, .12, IRON, up=(1, 0, 0))        # a bent plate on end
    for p, q in (((-13.4, 2.4, 5.6), (-11.6, 4.4, 9.4)), ((-14.2, 4.3, 6.0), (-11.9, 2.6, 8.6))):
        bone_shaft(m, p, q, .22, BONE)
    m.tube((-21.8, -.9, 5.2), (-10.4, -2.4, 17.2), .14, WOOD, sides=5)                 # the broken spear
    beam(m, (-10.4, -2.4, 17.2), (-9.9, -2.47, 17.8), .45, .1, STEEL, up=(1, 0, 0))
    m.face([(-9.9, -2.55, 17.8), (-9.9, -2.35, 17.8), (-9.35, -2.5, 18.75)], STEEL)
    m.face([(-9.35, -2.5, 18.75), (-9.9, -2.35, 17.8), (-9.9, -2.55, 17.8)], STEEL)
    # Skulls on the heap.
    skull(m, (-12.6, 3.1, 7.6), .62, (1, .3), OLDBONE, SOCKET)
    skull(m, (-20.0, -2.6, 8.4), .58, (.4, -1), BONE, SOCKET)
    skull(m, (-12.9, -2.6, 8.0), .5, (1, -.6), BONE, SOCKET)


def bucket(m):
    """EA's bucket (the water throw) as a dented scavenged helm, carried brim up."""
    c = (-15.5, .15, 6.0)
    lathe(m, c, add(c, (0, 0, 2.7)), [(0, 1.15), (.25, 1.65), (.55, 1.75), (.85, 1.85), (1, 1.95)], RUST, sides=10)
    m.tube(add(c, (0, 0, 2.55)), add(c, (0, 0, 2.8)), 2.02, STEEL, sides=10)
    lathe(m, add(c, (0, 0, .2)), add(c, (0, 0, -.6)), [(0, 1.1), (.7, .7), (1, .25)], IRON, sides=8)
    for s in (-1, 1):
        horn(m, (c[0], c[1] + s * 1.6, 7.8), (c[0] + .3, c[1] + s * 3.0, 9.6), (0, s * .3, -.4), .3, BLOOD)


def plank_wheel(m, bone):
    """The right wheel: a solid disc of planks, cleated in iron, a little out of round."""
    rng = random.Random(5)
    c = (AXLE[0], WHEEL_R, AXLE[1])
    disc(m, c, RADIUS, .42, TIMBER, bone, n=18, jitter=[rng.uniform(-.07, .05) for _ in range(18)])
    for dz in (-1.7, 1.7):
        beam(m, (c[0] - 3.6, c[1] - .52, c[2] + dz), (c[0] + 3.6, c[1] - .52, c[2] + dz), .2, .7, IRON, bone)
        beam(m, (c[0] - 3.6, c[1] + .52, c[2] + dz), (c[0] + 3.6, c[1] + .52, c[2] + dz), .2, .7, IRON, bone)
    for i in range(6):
        a = i * math.tau / 6 + .3
        x, z = c[0] + 3.9 * math.cos(a), c[2] + 3.9 * math.sin(a)
        m.box((x - .17, c[1] - .55, z - .17), (x + .17, c[1] + .55, z + .17), STEEL, bone)
    m.tube((c[0], c[1] - .8, c[2]), (c[0], c[1] + .8, c[2]), .8, RUST, bone, sides=8)
    # Three claw slashes of white war paint on the outer face.
    for dx in (-1.1, 0, 1.1):
        beam(m, (c[0] + dx - 1.0, c[1] - .45, c[2] + 2.9), (c[0] + dx + .9, c[1] - .45, c[2] - 2.7), .04, .34, PAINT, bone)


def spoke_wheel(m, bone):
    """The left wheel: salvaged, iron-tyred, one spoke replaced by a bone."""
    c = (AXLE[0], WHEEL_L, AXLE[1])
    ring(m, c, 3.65, 4.12, .38, WOOD, bone)
    ring(m, c, 4.12, RADIUS, .32, IRON, bone)
    for i in range(6):
        a = i * math.tau / 6 + .25
        end = (c[0] + 3.8 * math.cos(a), c[1], c[2] + 3.8 * math.sin(a))
        if i == 4:
            bone_shaft(m, (c[0] + .9 * math.cos(a), c[1], c[2] + .9 * math.sin(a)),
                       (c[0] + 3.4 * math.cos(a), c[1], c[2] + 3.4 * math.sin(a)), .22, BONE, bone)
        else:
            m.tube(c, end, .27, WOOD, bone, sides=5)
    m.tube((c[0], c[1] - .75, c[2]), (c[0], c[1] + .75, c[2]), .85, RUST, bone, sides=8)
    m.tube((c[0], c[1] - .85, c[2]), (c[0], c[1] + .85, c[2]), .32, STEEL, bone, sides=6)


# The 16 swatches: (palette ramp, middle value, grain source, grain contrast). Grain is EA's own
# painted detail (CROPS) taken for its light and dark only; the hue is the Goblin palette's.
SWATCHES = [("wood", .8, 0, 1.3), ("stone", .72, 0, 1.0), ("iron", .42, 1, .9), ("iron", .7, 1, .8),
            ("hide", .55, 2, .8), ("hide", .3, 2, .7), ("bone", .7, 3, .5), ("bone", .38, 3, .6),
            ("hide", .17, 4, .5), ("bone", .58, 5, .35), ("rock", .55, 4, .6), ("stone", .6, 5, .7),
            ("rock", .06, 4, .1), ("iron", .2, 1, .8), ("stone", .42, 2, .7), ("bone", .5, 5, .3)]
CROPS = [("guporter_build", (112, 168, 250, 205)), ("muorcporter", (3, 55, 70, 175)),
         ("muorcporter", (80, 10, 150, 95)), ("muorcporter", (153, 10, 200, 150)),
         ("muorcporter", (2, 210, 62, 254)), ("guporter_build", (0, 0, 255, 140))]


def ramp(material, value):
    stops = PALETTE.ramps[material]
    value = max(0, min(1, value))
    for (a, ca), (c, cb) in zip(stops, stops[1:]):
        if a <= value <= c:
            t = (value - a) / (c - a)
            return [x * (1 - t) + y * t for x, y in zip(ca, cb)]
    return list(stops[-1][1])


class Porter(Unit):
    """EA's orc porter, which Isengard, Mordor, the Goblins and Angmar all draw: ours ships under a
    name of its own and only WildPorter's Draw is repointed to it (Angmar keeps EA's)."""
    model, skeleton = "WUPorter_SKN", "MUOrcPrtr_SKL"
    own_model = "WUBuilder_SKN"
    objects = {"WildPorter": ("data\\ini\\object\\evilfaction\\units\\wild\\wildporter.ini", "ModuleTag_01")}
    anims = ("idla", "idlb", "runa", "wlka", "fira", "diea", "dieb")
    expected = {"wuporter_skn": "0f3aa90adf5415d9242ba1c7cf33807ce3d6bd2774b73e6bd195ca31cae8e47f",
                "muorcprtr_skl": "7d4d2bd88941d3c41bef5f778a9fa47f0967f10067220a2a97aa404d149766df"}
    textures = {"MUPortCart.tga": "WUCrafts.tga", "GUPorter_Build.tga": "WUCrafts.tga",
                "GUPorter_Cart.tga": "WUCrafts.tga"}
    house = {"WUCrafts.tga": "HC_WUCrafts.tga"}
    mask = ("HC_MUPortCart.tga", "HC_WUCrafts.tga")
    archive = "!!!!!!!!!!!!sagekit-goblin-builder.big"
    smooth = ("ORCPORTER",)
    views = {k: v for k, v in DEFAULT_VIEWS.items() if k != "work"}     # EA's orc porter never builds
    labels = ("EA'S ORC PORTER", "GOBLIN SCAVENGER - DESIGN PREVIEW")
    label_colour = "#2a0a10cc"

    def design(self, w, sk):
        meshes = {n: self.mesh(w, sk, n) for n in ("CART", "CARTSUPPLIES", "BUCKET", "WHEEL_L01", "WHEEL_R01")}
        for m in meshes.values():
            m.uv_for = uvs                      # the swatches, and the HOUSE region (kit.py)
        cart(meshes["CART"])
        load(meshes["CARTSUPPLIES"])
        bucket(meshes["BUCKET"])
        spoke_wheel(meshes["WHEEL_L01"], None)
        plank_wheel(meshes["WHEEL_R01"], None)
        return meshes

    def check(self, b, original, new, sk):
        assert new.meshes["ORCPORTER"].bytes == original.meshes["ORCPORTER"].bytes, "the orc is EA's"

    def paint(self, b):
        samples = [crop_rgb(b.src / (source + ".dds"), box, b.work / ("grain_%d.rgb" % i))
                   for i, (source, box) in enumerate(CROPS)]
        rng, pixels = random.Random(29), bytearray()
        for y in range(1024):
            for x in range(1024):
                tag = (y // 256) * 4 + x // 256
                material, mid, src, contrast = SWATCHES[tag]
                u, v = x % 256, y % 256
                o = (v * 256 + u) * 3
                lum = sum(samples[src][o:o + 3]) / 765
                edge = min(u, v, 255 - u, 255 - v) / 255
                value = mid + (lum - .45) * contrast + rng.uniform(-.02, .02)
                if tag == SILK:                 # wound strands across the cocoon
                    value += .07 * math.sin(v * .9 + 3 * math.sin(u * .05)) - (.12 if (u + 2 * v) % 41 < 2 else 0)
                if tag in (WOOD, TIMBER):       # long grain along the plank (u)
                    value += .1 * math.sin(v * .45 + 2.5 * math.sin(u * .02 + v * .1))
                if material in ("iron",):
                    value += .14 if edge < .02 else 0
                else:
                    value += .06 if edge < .015 else -.05 if edge < .03 else 0
                pixels.extend(round(255 * q) for q in ramp(material, value))
        (b.work / "materials.ppm").write_bytes(b"P6\n1024 1024\n255\n" + pixels)
        # The left half: cloth under EA's tiled cart mask, light and neutral so the player's colour
        # shades it in game (the preview shows it pale), its weave from the mask's own grey.
        mask = raw(b.src / self.mask[0].lower())
        size = int(round((len(mask) // 4) ** .5))
        left = bytearray()
        for y in range(1024):
            for x in range(1024):
                o = ((y % size) * size + x % size) * 4
                grey = .52 + .38 * mask[o] / 255 if mask[o + 3] > 127 else .35
                left.extend((round(255 * grey * .93), round(255 * grey * .9), round(255 * grey * .88)))
        (b.work / "cloth.ppm").write_bytes(b"P6\n1024 1024\n255\n" + left)
        atlas = b.work / "wucrafts.png"
        magick(b.work / "cloth.ppm", b.work / "materials.ppm", "+append", atlas)
        return atlas
