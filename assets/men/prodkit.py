"""Shared by the production group (workshop, farm, market place, stone maker and the workshop's
and farm's level-up meshes): host-side fixes, paint layers and Blender-side pieces the kit
(shapes.py) and assets/men/motifs.py lack. Blender and numpy imports stay inside the
functions, so the recipes load anywhere.

    same_length_variants   state-variant names kept to EA's length (W3D renames in place)
    banner                 kit.banner on two closed stone consoles
    pointed_arc, pointed_voussoirs   a pointed arch of wedge stones round an opening
    VET_TILES, with_tiles  GBVet's slate triangle as the painter's `tiles` hint
    props_layer            EA's painted props keep their own colours under the stone recolour
"""


def same_length_variants(building, install, variants):
    """The framework's state variants with every name kept to EA's length: a derived body painted
    from a sheet named off the body's (GBWorkshop_D1 draws GBWorkshop1D.tga beside the body's
    GBWorkshop3.tga) gets an own name one letter longer (GBWorkshopH1D), and W3D patches names in
    place. Such a name loses letters from the own stem until it fits (GBWorkshpH1D)."""
    own = building.own_diffuse[:-4]
    out = {}
    for ea, mine in variants.items():
        extra = len(mine) - len(ea)
        if extra > 0:
            stem, tail = own, mine[len(own):]
            stem = stem[:-1 - extra] + stem[-1]            # drop letters before the own letter
            mine = stem + tail
        out[ea] = mine
    return out


def banner(kit, a, t, n, u, z_top, width, length, d=1.0):
    """kit.banner (its cloth goes to the house-colour model) on two stone consoles under the rod's
    ends: square blocks, their tops closed (motifs.banner_mount's widen upwards and leave their
    tops open under the rod, which the sky check sees)."""
    from .motifs import slab
    out = kit.banner(a, t, n, u, z_top, width, length, d)
    h = width / 2 + 1.4
    for e in (-1, 1):
        m = u + e * h
        out.append(slab(a, t, n, m - 0.5, m + 0.5, z_top - 1.6, z_top - 0.1, -0.25, d + 0.3,
                        ("stoneB", "stoneB", "top", "stoneB"), "stoneB"))
    return out


# GBVet (512): the slate-tiled roof triangle the level-up domes are painted from, in the 4x upscale's
# pixels (top-down rows, as the atlases' mask_hints): painted with the palette's slate, not as stone
VET_TILES = [(4 * 146, 4 * 64, 4 * 230, 4 * 152)]


def with_tiles(atlas, tiles):
    """The building's own-sheet Atlas with `tiles` rectangles as its slate mask hints (a plain
    Atlas for a building's own sheet has none, so the Recolour paints its slate as stone)."""
    atlas.mask_hints = dict(getattr(atlas, "mask_hints", {}) or {}, tiles=list(tiles))
    return atlas


def pointed_arc(half, spring, rise, e, f):
    """The point at fraction f (0 springing, 1 apex) up side e (-1, 1) of a pointed arch of half
    width `half` springing at `spring` with its apex `rise` above: two circular arcs centred on
    the springing line, each through the other side's springing point's mirror."""
    import math
    R = (half * half + rise * rise) / (2 * half)
    top = math.acos((R - half) / R)
    th = top * f
    return e * (half - R + R * math.cos(th)), spring + R * math.sin(th)


def pointed_voussoirs(a, t, n, u, half, spring, rise, width, d0, d1, count=4, key=True):
    """A pointed arch of wedge stones framing an opening (half, spring, rise: its inner edge),
    `width` deep in the face, standing d0..d1 out of it, `count` stones a side, alternate stones
    0.25 prouder, and a keystone at the apex. The opening itself stays clear."""
    from sagekit.blender.geometry import prism_uz
    out = []
    oh, orise = half + width, rise + width * 1.25
    for e in (-1, 1):
        for i in range(count):
            f0, f1 = i / count, (i + 1) / count
            if key and i == count - 1:
                f1 = 0.9
            p = [pointed_arc(half, spring, rise, e, f0), pointed_arc(oh, spring, orise, e, f0),
                 pointed_arc(oh, spring, orise, e, f1), pointed_arc(half, spring, rise, e, f1)]
            poly = [(u + x, z) for x, z in p]
            if e > 0:
                poly.reverse()
            out.append(prism_uz(a, t, n, poly, d0, d1 + (0.25 if i % 2 else 0.0),
                                ["stoneB", "stoneB", "stoneB", "stoneB"], "stoneA", None))
    if key:
        (x0, z0), (x1, z1) = pointed_arc(half, spring, rise, -1, 0.9), pointed_arc(half, spring, rise, 1, 0.9)
        zt = spring + orise + 0.6
        poly = [(u + x0, z0), (u + x1, z1), (u + 0.9, zt), (u - 0.9, zt)]
        out.append(prism_uz(a, t, n, poly, d0, d1 + 0.45, ["stoneB", "stoneB", "top", "stoneB"], "stoneA", None))
    return out


def props_layer(sat=(0.3, 0.45), gate=(0.35, 0.6), hue=None, strength=0.95, rects=()):
    """A paint layer that gives EA's painted props back their own colours - crates, barrels,
    fruit, awnings, straw, timber - where the style's stone recolour would turn them to white
    stone: texels of EA's own sheet more saturated than `sat` (and, if given, within `hue`,
    degrees), gathered over a few texels and gated (`gate`) so speckles in the stone stay stone,
    take EA's colour back (as the style's Lawn keeps the grass green). Per sheet: the market's
    props against its beige paving, the farm's thatch and timber against its grey stone. New
    faces are never touched. `rects`: [(u0, v0, u1, v1)] of EA's sheet (Blender UV, v up, taken
    modulo 1 as EA tiles them) whose texels on EA's faces keep EA's colour whatever their
    saturation (the farm's palisade stakes: grey-brown planks the colour rule misses). Host side
    (numpy), built on first use; the layer lives in men/paint.py, which the sheet recolour shares."""
    from .paint import keep_layers
    return keep_layers()["Props"](sat=sat, gate=gate, hue=hue, strength=strength, rects=rects)


def chimney_cap(x0, x1, y0, y1, z):
    """A coping and two chimney pots on a stack whose top is the rectangle x0..x1, y0..y1 at z
    (the farmhouse's, owned by EA's roof meshes)."""
    from .motifs import box
    from .shapes import turned
    out = [box(x0 - 0.38, x1 + 0.38, y0 - 0.38, y1 + 0.38, z - 0.75, z + 0.3, "course", cap0=("stoneB", True), cap1=("top", True)),
           box(x0 + 0.1, x1 - 0.1, y0 + 0.1, y1 - 0.1, z + 0.3, z + 0.7, "stoneB", cap0=("stoneB", True), cap1=("top", True))]
    yc = (y0 + y1) / 2
    for f in (0.28, 0.72):
        xc = x0 + (x1 - x0) * f
        out.append(turned(xc, yc, [(0.75, z + 0.65), (0.75, z + 1.1), (0.55, z + 1.3), (0.55, z + 2.6), (0.72, z + 2.8), (0.72, z + 3.1)],
                          ["course", "stoneB", "stoneA", "course", "course"], k=8, cap0=("stoneB", True), cap1=("iron", True)))
    return out
