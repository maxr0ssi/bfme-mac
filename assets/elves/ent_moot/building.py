"""The Ent moot (ElvenEntMoot, elvenentmoot.ini): EA's grass-floored clearing ringed by boulders
under the great leaning horn of rock stays a clearing; the ring is made whole. Standing stones -
rough, weathered, leaning a little, each with a few fallen stones at its foot - stand round the
floor between EA's boulders, and a tall pair either side of the horn's root, a gate to it, and leave the four
places the moot's upgrades plant trees (TreeLothlorien08EntMoot at (-30, 65), (30, 65), (-61.16,
-17.11), (70.65, -29.12)) and the middle, where the Ents gather, open. Nothing is built: no gold,
no lanterns, no cloth. (The moot's house-colour model RBHCEntMoot is flowers; there is no cloth.)

EA's FENTMOOT (mesh = model coordinates, one bone) is the floor, an octagon of radius ~90 at z 0.6
(x -91.3..89.3, y -96.3..97.8: the footprint), its boulders (tops 15-20 at (-56.8, 42.5),
(53.7, 38.2), (73.4, -58.5), (-37.6, -83.3), (-75.8, -38.0), (2.2, -81.0)) and the horn, which
rises from the rim at +y and leans in over the floor to its tip at (0.9, 28.7, 52.4).

The rock stays natural: EA's sheet has its rock half hinted as rock (sheet_atlas), so the boulders
and the horn take the palette's natural stone ramp and not the ivory masonry the colour rules made of
them; decals() darkens it a little and warms it with the palette's earth accent. The new stones are
cut from the atlas's bark (rough, never masonry: no ashlar joints) and painted the same way, with
moss from the style's layers. Height unchanged (the horn stays the highest point).
"""
import math

from sagekit.building import Building

from ..style import ElvenStyle

GROUND = 0.6
# the standing stones, in the gaps of EA's ring of boulders: (angle deg, radius, height, width, lean)
# round the floor's centre; the last two flank the horn's root
STONES = [(-50, 86, 22.0, 8.0, 0.04), (-74, 84, 19.0, 7.2, -0.05), (-101, 84, 24.0, 8.4, 0.05), (-130, 82, 20.0, 7.6, -0.04),
          (160, 74, 21.0, 7.8, 0.05), (17, 70, 23.0, 8.2, -0.05), (75, 85, 28.0, 9.0, -0.03), (105, 85, 29.0, 9.0, 0.03)]
# FBEntmoot.tga's rock half on its 2048 upscale (x, y down): the grey rock and the rooty earth,
# the flower card (x 268..330, y 0..60 original) left out
ROCK_HINTS = [(1320, 0, 2048, 240), (1048, 240, 2048, 2048)]
EARTH_VALUE = 0.86          # the rock's value against the ramp's (a pale silver-grey on its own)
TREES = [(-30.0, 65.0), (30.0, 65.0), (-61.16, -17.11), (70.65, -29.12)]


def hash01(*k):
    """A repeatable pseudo-random number in [0, 1) from integers."""
    h = 2166136261
    for v in k:
        h = ((h ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
    h ^= h >> 13
    h = (h * 1274126177) & 0xffffffff
    return (h & 0xffffff) / float(0x1000000)


def menhir(cx, cy, h, w, lean, facing, seed, k=7):
    """A rough standing stone: a thick slab-like irregular k-gon (depth 0.7 of its width, each corner
    jittered), swelling a little and then drawn in towards a blunt, sloping top (a plane tilted
    across its face), leaning towards `facing` (radians) by `lean` per unit of height. Buried a
    unit below the ground."""
    from mathutils import Vector as V
    from sagekit.blender.geometry import loft
    ca, sa = math.cos(facing), math.sin(facing)
    jit = [0.8 + 0.35 * hash01(seed, i) for i in range(k)]
    tilt = 0.18 * (hash01(seed, 77) - 0.5) * h / w            # the top's slope across the face
    levels = [(-1.0, 1.0), (GROUND, 1.0), (GROUND + 0.4 * h, 1.04), (GROUND + 0.75 * h, 0.9), (GROUND + 0.9 * h, 0.68),
              (GROUND + h, 0.5)]
    rings = []
    for li, (z, f) in enumerate(levels):
        off = lean * max(0.0, z - GROUND)
        ring = []
        for i in range(k):
            a = 2 * math.pi * (i + 0.3 * hash01(seed, i, 7)) / k
            r = 0.5 * w * f * (jit[i] + 0.1 * (hash01(seed, i, li) - 0.5))
            u, v = r * math.cos(a), 0.7 * r * math.sin(a)           # u across the stone, v through it
            zz = z + (tilt * u if li == len(levels) - 1 else 0.0)
            ring.append(V((cx + ca * off - sa * u + ca * v, cy + sa * off + ca * u + sa * v, zz)))
        rings.append(ring)
    return loft(rings, [None, "bark", "bark", "bark", "bark"], cap0=("bark", False), cap1=("bark", True))


def fallen(cx, cy, r, h, seed, k=6):
    """A low rounded stone at a standing stone's foot."""
    from mathutils import Vector as V
    from sagekit.blender.geometry import loft
    rings = []
    for li, (z, f) in enumerate(((-0.6, 0.9), (GROUND, 1.0), (GROUND + 0.55 * h, 0.85), (GROUND + h, 0.4))):
        rings.append([V((cx + r * f * (0.8 + 0.4 * hash01(seed, i, li)) * math.cos(2 * math.pi * i / k + seed),
                         cy + r * f * (0.8 + 0.4 * hash01(seed, i, li + 5)) * math.sin(2 * math.pi * i / k + seed), z))
                      for i in range(k)])
    return loft(rings, [None, "bark", "bark"], cap0=("bark", False), cap1=("bark", True))


class EntMoot(Building):
    style = ElvenStyle()
    source = "FBEntmoot"
    target = "FENTMOOT"
    sheet = "FBEntmoot.tga"
    sheet_normal = None
    facet_islands = True                # the horn's smooth shell unwraps onto itself (sagekit/blender/layout.py)
    own_textures = {"FBEntmoot.tga": "FBEntmooH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-1.2, 1.1, 14.0), 430, 50, -38, 50),
        "close": ((-1.2, 1.1, 12.0), 250, 24, -30, 45),
        "ingame": ((-1.2, 1.1, 24.8), 1352, 53, -62, 50),
    }

    @property
    def sheet_atlas(self):
        """EA's sheet with its rock half hinted as rock: the boulders and the horn (every raised face
        samples the right half, the grey rock above and the rooty earth below; the flower card at
        its top left is left out) take the palette's natural stone grey (the "rock" ramp) instead
        of the ivory masonry the colour rules make of them, and no gold flecks."""
        a = super().sheet_atlas
        a.mask_hints = {"rock": ROCK_HINTS}
        return a

    def decals(self):
        """Every rock texel - EA's boulders and horn (the rock hints) and the new stones (the atlas's
        bark, hinted rock on the faction sheet) - in the palette's natural stone grey, darkened a
        little and warmed by the palette's own earth ("dirt" accent): weathered field stone, not
        the ramp's pale silver-grey. The new stones' dark bark grain is lifted to EA's boulders'."""
        import numpy as np

        from sagekit.paint.fields import ramp
        from sagekit.paint.layers import Layer

        class EarthyRock(Layer):
            def apply(self, col, cv, pal):
                m = np.clip(np.maximum(cv.rock, cv.tag_is("bark")), 0, 1)[..., None]
                L = np.clip(cv.lum + 0.15 * cv.tag_is("bark"), 0, 1)
                dirt = np.array(pal["dirt"], np.float32)
                tint = EARTH_VALUE * dirt / dirt.mean()
                return col * (1 - m) + ramp(L, pal["rock"]) * tint * m
        return [EarthyRock()]

    def design(self, kit):
        out = []
        for i, (ang, r, h, w, lean) in enumerate(STONES):
            a = math.radians(ang)
            cx, cy = r * math.cos(a), r * math.sin(a)
            if min(math.hypot(cx - x, cy - y) for x, y in TREES) < 14.0:
                raise ValueError("ent_moot: stone at %d degrees stands where a tree is planted" % ang)
            # each stone turns its broad face to the middle and leans out or in a little
            out.append(menhir(cx, cy, h, w, lean, a, 17 + i))
            for j in range(1 + i % 2):
                b = a + (0.07 if j == 0 else -0.08) * (1 if i % 3 else -1)
                rr = r + (3.0 if j == 0 else -4.5)
                out.append(fallen(rr * math.cos(b), rr * math.sin(b), 2.2 + 1.2 * hash01(i, j), 2.0 + 1.6 * hash01(i, j, 3),
                                  31 + 7 * i + j))
        return out
