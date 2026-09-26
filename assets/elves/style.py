"""The Elven look, Lórien and Rivendell: soft ivory stone, strong mithril silver and strong mallorn
gold (Max's pick, 2026-09-26, after the stark moonsilver round: "strong silver and gold elements
with a soft white"). Both metals must read at a glance from the RTS camera, on a stone quiet
enough to carry them:

    stone    soft warm ivory, mids about (0.86, 0.84, 0.80), shading to a gentle warm grey; never
             stark white, never muddy
    silver   bright mithril, a clean cool white-silver with dark burnished lows: trims, frames,
             ridges, copings, the knotwork and every new "trim" face; a darker groove on the stone
             beside it (Groove) makes it read as metal set in stone
    gold     warm, strong mallorn gold: EA's gold and tan (the gable frames, the leaf emblems and
             the lattice roofs' tracery, the Recolour's "gold" and "bronze" masks), and every new
             "gilt" face (finials, tracery, leaf ornament, crowns)
    roofs    a mid-value blue-grey slate, so both metals pop against it
    teal     only where EA has it: the lattice glass, its teal frames and the knotwork ground, a
             muted sea-glass; new enamel faces (arch reveals) are a deep slate groove instead
    wood     pale honeyed birch; bark and boards silver-grey
    cloth    the player's colour: the only strongly saturated thing on a building
    night    the teal-silver starlight

Same structure as the Dwarven style (one palette, one atlas, one kit, one paint stack), with a
Foliage layer so ivy and grass stay green (the Recolour would turn them to stone), a Scales layer
that skins new roofs in continuous fish-scale slate and the Groove beside the metals."""
import functools

from sagekit.nightlights import NightLook
from sagekit.style import Palette, Style

from .atlas import ElvenAtlas

# mithril: a cool blue silver, darker than the ivory in its mids and white in its highlights, so it
# reads as polished metal and not as more white stone (a pale silver on ivory read as stone). EA's knotwork strokes ("inlay"), the kit's "trim"
MITHRIL = [(0, (.07, .09, .13)), (.25, (.24, .29, .37)), (.45, (.44, .50, .60)), (.6, (.60, .67, .77)),
           (.75, (.78, .84, .92)), (.88, (.92, .95, 1.0)), (1, (1, 1, 1))]
# mallorn gold: warm and strong (about (0.86, 0.66, 0.26) at the mid), brown-amber in the lows, pale
# gold in the highlights. EA's gold and tan, the metal rims, the kit's "gilt"
GOLD = [(0, (.14, .08, .02)), (.25, (.40, .25, .06)), (.45, (.66, .46, .13)), (.6, (.82, .62, .22)),
        (.75, (.93, .77, .34)), (.88, (.99, .89, .53)), (1, (1, .97, .78))]
# sea-glass verdigris: EA's own teal only (the knotwork ground, the teal frames); muted
VERDIGRIS = [(0, (.05, .08, .09)), (.2, (.12, .21, .22)), (.38, (.22, .38, .38)), (.5, (.30, .50, .49)),
             (.62, (.38, .60, .58)), (.8, (.55, .74, .72)), (1, (.78, .89, .87))]
# deep slate: the reveals and soffits of new arches ("enamel"): a shadowed groove round the silver
SLATE = [(0, (.06, .07, .09)), (.3, (.17, .20, .24)), (.55, (.30, .34, .39)), (.8, (.45, .50, .56)),
         (1, (.62, .67, .72))]

PALETTE = Palette(
    "Ivory, mithril and mallorn gold",
    ramps={
        # soft ivory: about (0.86, 0.84, 0.80) where EA's walls land, shading to a warm grey
        "stone": [(0, (.12, .11, .10)), (.18, (.33, .31, .28)), (.32, (.53, .50, .46)), (.45, (.71, .68, .63)),
                  (.58, (.82, .80, .75)), (.7, (.87, .85, .81)), (.85, (.92, .90, .86)), (1, (.96, .95, .91))],
        "bronze": GOLD,
        "gold": GOLD,
        "inlay": MITHRIL,
        "trim": MITHRIL,
        # pale honeyed birch: about (0.78, 0.72, 0.60)
        "wood": [(0, (.14, .11, .08)), (.2, (.40, .34, .26)), (.4, (.60, .53, .42)), (.6, (.78, .72, .60)),
                 (.8, (.88, .84, .74)), (1, (.95, .93, .86))],
        "ground": VERDIGRIS,
        "enamel": SLATE,
        # body cloth where no house-colour model takes it (in game it is the player's colour)
        "cloth": [(0, (.03, .07, .06)), (.35, (.06, .20, .16)), (.6, (.12, .34, .27)), (.85, (.27, .52, .42)),
                  (1, (.55, .75, .62))],
        # the lattice window's glass (the grille hint): verdigris in the darks, blue-white in the light
        "iron": [(0, (.08, .15, .17)), (.15, (.20, .35, .37)), (.35, (.40, .58, .60)), (.6, (.63, .78, .82)),
                 (1, (.88, .95, .97))],
        # mallorn bark, earth and boards: silver-grey (a warm grey-brown at these values read as mud)
        "rock": [(0, (.10, .10, .11)), (.15, (.30, .30, .31)), (.3, (.50, .50, .50)), (.5, (.68, .68, .67)),
                 (.75, (.83, .83, .81)), (1, (.94, .94, .92))],
        # roofs: mid-value blue-grey slate where EA's dark slate (luminance 0.2..0.45) and the Scales land
        "tiles": [(0, (.08, .09, .11)), (.12, (.18, .20, .24)), (.3, (.33, .37, .42)), (.42, (.40, .44, .49)),
                  (.65, (.53, .57, .62)), (1, (.72, .75, .79))],
        # crystal lanterns and finials: blue-white glass, about (0.72, 0.86, 0.92)
        "crystal": [(0, (.14, .22, .28)), (.35, (.46, .62, .70)), (.6, (.72, .86, .92)), (.8, (.86, .94, .97)),
                    (1, (.97, 1, 1))],
        # foliage (ivy, grass, moss on the sheets): Lórien green going gold in the light
        "leaf": [(0, (.04, .07, .03)), (.35, (.16, .26, .10)), (.65, (.38, .48, .20)), (.9, (.70, .70, .34)),
                 (1, (.88, .84, .52))],
    },
    # shading stays gentle and warm-grey; the groove beside the metals (Groove) a cool grey
    accents={"occl": (0.30, 0.29, 0.28), "edge": (1.0, 0.99, 0.96), "grime": (0.32, 0.31, 0.29),
             "moss": (0.36, 0.44, 0.28), "dirt": (0.46, 0.43, 0.38), "groove": (0.36, 0.38, 0.42), "glow": None},
    tints={"stone_alt": (1.0, 0.99, 0.97), "stone_alt2": (0.99, 0.99, 1.0)},
)

# the stone's contrast: EA's grey-beige walls (luminance 0.3..0.75) land round the ramp's ivory mids
RECOLOUR = dict(stone_pivot=0.42, stone_gain=0.95, stone_mid=0.6)
# painted tags: (ramp, gain, lift) over EA's sheet luminance at the region the tag samples
# (atlas.py; measured on the 1024 original, p10 / p50 / p90). Each lands where its ramp names the
# colour, with the sheet's grain as a gentle spread round it
TAGRAMPS = {"trim": ("trim", 1.4, -0.6),            # plain light 0.69/0.88/1.0 -> 0.37/0.63/0.80: mithril
            "gilt": ("gold", 1.3, -0.45),           # plain light 0.69/0.88/1.0 -> 0.45/0.69/0.85: strong gold
            "enamel": ("enamel", 0.6, 0.12),        # plain mid 0.31/0.49/0.74 -> 0.31/0.41/0.56: slate groove
            "crystal": ("crystal", 0.6, 0.3),       # crystal 0.22/0.50/0.70 -> 0.43/0.60/0.72: blue-white
            "cloth": ("cloth", 0.85, 0.22)}         # body cloth (house colour in game)

# EA's motifs repainted (Repaint; atlas.py rects): (gain, lift, strength) over the sheet's luminance.
# The cream beams (value 0.65..1, saturation 0.1..0.3; EA's boards are darker and more saturated) land
# in the gold ramp's 0.5..0.8, the slate (0.1..0.4) in the tiles' mids
GILDED = (1.0, -0.12, 1.0)
ROOF_SLATE = (0.9, 0.06, 1.0)
ROOF_SCALES = (0.75, -0.06, 1.0)                    # EA's pale scales (0.45..0.85) to 0.28..0.58
LEADING = (1.1, -0.05, 0.9)

# starlight at night: silver-blue with a teal breath, softer than the Dwarven forge light. Ramp 0 is
# black (the night meshes are additive)
STARLIGHT = NightLook("EBStarlight.tga", ramp=[(0, (0, 0, 0)), (.3, (.08, .16, .26)), (.6, (.34, .54, .74)),
                                                (.85, (.66, .85, .96)), (1, (.90, .98, 1))],
                      gain={"halo": 0.8})


@functools.lru_cache(maxsize=None)
def elven_layers():
    """(Foliage, Scales, Groove, Repaint): the Elven paint layers, built on first use. sagekit.paint needs numpy (on
    Blender's Python); this module must import anywhere (validate, the registry, the host)."""
    import numpy as np

    from sagekit.paint.fields import hash01, hsv, ramp, smooth
    from sagekit.paint.imageio import to_srgb
    from sagekit.paint.layers import Layer

    class Foliage(Layer):
        """Green texels of the original sheet (ivy, grass, moss) painted with the leaf ramp by their own
        luminance, over whatever the Recolour made of them. Works on building canvases (the baked
        atlas colour) and on flat sheets (SheetCanvas.rgb)."""

        def __init__(self, strength=0.9, hue=(62.0, 150.0), sat=(0.16, 0.30)):
            self.strength, self.hue, self.sat = strength, hue, sat

        @staticmethod
        def source(cv):
            rgb = getattr(cv, "rgb", None)
            if rgb is not None:
                return rgb
            return cv.memo("foliage_rgb", lambda: to_srgb(cv.load("atlas")).astype(np.float32))

        def apply(self, col, cv, pal):
            H, S, V = hsv(self.source(cv))
            (h0, h1), (s0, s1) = self.hue, self.sat
            m = smooth(H, h0, h0 + 12) * (1 - smooth(H, h1 - 12, h1)) * smooth(S, s0, s1) * smooth(V, 0.06, 0.16)
            m = (m * self.strength * (1 - getattr(cv, "painted", 0.0)))[..., None]
            return col * (1 - m) + ramp(np.clip(cv.lum * 1.1, 0, 1), pal["leaf"]) * m

    class Scales(Layer):
        """Fish-scale slates in world space on new roof faces: rows follow z (each offset half a scale),
        scales run along the face's horizontal; per-scale tone, a shadowed rounded rim, the tiles ramp;
        the rims cut into the normal map. The atlas's slate region is tiled per face (a random window
        each), which on a roof of many small faces reads as a patchwork: this makes it one roof."""

        def __init__(self, tag="roof", width=1.6, height=1.15, tone=0.16, keep=0.3, depth=0.12):
            self.tag, self.W, self.H, self.tone, self.keep, self.depth = tag, width, height, tone, keep, depth

        def cells(self, cv):
            def compute():
                p, n = cv.flat(cv.pos), cv.flat(cv.nrm)
                t = np.stack([-n[:, 1], n[:, 0], np.zeros(len(n), np.float32)], -1)
                t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-6)
                row = np.floor(p[:, 2] / self.H)
                fz = p[:, 2] / self.H - row
                q = (p * t).sum(1) / self.W + 0.5 * (row % 2)
                col = np.floor(q)
                d = np.hypot((q - col - 0.5) * self.W, (fz - 1.0) * self.H) / (0.55 * self.W)
                rim = smooth(d, 0.8, 0.97) * (1 - smooth(d, 1.0, 1.12))
                v = 0.5 + self.tone * (hash01(row, col, 5) - 0.5) + 0.14 * (1 - fz) - 0.3 * rim
                return [x.reshape(cv.R, cv.R).astype(np.float32) for x in (v, rim)]
            return cv.memo(("scales", id(self)), compute)

        def apply(self, col, cv, pal):
            f = cv.tag_is(self.tag).astype(np.float32)[..., None]
            v, _ = self.cells(cv)
            L = np.clip((1 - self.keep) * v + self.keep * cv.lum, 0, 1)
            return col * (1 - f) + ramp(L, pal["tiles"]) * f

        def height(self, cv, ds):
            return ds(-self.depth * self.cells(cv)[1] * cv.tag_is(self.tag))

    class Groove(Layer):
        """A thin grey groove on the stone beside new metal (the `tags`' faces): silver on ivory stone
        has nearly the stone's value and reads as more stone; a shadowed joint round it makes it metal
        set in stone. World space, as the faces lie on the mesh (their UV islands are apart): the silver
        texels are binned in cells of half the width, and every stone texel takes its distance to the
        nearest cell's mean point among the 27 round its own; dark at the joint, gone at `width`."""

        def __init__(self, tags=("trim", "gilt"), width=0.6, strength=0.75, depth=0.08):
            self.tags, self.width, self.strength, self.depth = tags, width, strength, depth

        def mask(self, cv):
            def compute():
                out = np.zeros(cv.covm.shape, np.float32)
                src = cv.tag_is(*self.tags) & (cv.covm > 0.5)
                cand = (cv.covm > 0.5) & ~src & (cv.w_stone > 0.05)
                if not src.any() or not cand.any():
                    return out
                q = np.floor(cv.pos / (self.width / 2)).astype(np.int64)
                B = 1 << 20

                def key(c):
                    return ((c[..., 0] + B) << 42) | ((c[..., 1] + B) << 21) | (c[..., 2] + B)
                cells, inv = np.unique(key(q[src]), return_inverse=True)
                ps = cv.pos[src]
                n = np.bincount(inv, minlength=len(cells)).astype(np.float32)
                mean = np.stack([np.bincount(inv, ps[:, i], len(cells)) for i in range(3)], -1) / n[:, None]
                qc, pc = q[cand], cv.pos[cand]
                d = np.full(len(pc), 9.0, np.float32)
                for off in np.stack(np.meshgrid(*[(-1, 0, 1)] * 3, indexing="ij"), -1).reshape(-1, 3):
                    k = key(qc + off)
                    i = np.clip(np.searchsorted(cells, k), 0, len(cells) - 1)
                    d = np.where(cells[i] == k, np.minimum(d, np.linalg.norm(pc - mean[i], axis=1)), d)
                out[cand] = 1 - smooth(d, 0.3 * self.width, self.width)
                return out * cv.w_stone
            return cv.memo(("groove", id(self)), compute)

        def apply(self, col, cv, pal):
            g = (self.strength * self.mask(cv))[..., None]
            return col * (1 - g) + np.array(pal["groove"], np.float32) * g

        def height(self, cv, ds):
            return ds(-self.depth * self.mask(cv))

    class Repaint(Layer):
        """EA's own motifs on the faction sheet repainted as a material by their colour: texels of EA's
        faces (tag "old") whose sheet position lies in `rects` (original px, atlas.py) and whose
        original colour passes `gate`, painted with `ramp_name` by luminance. Only for a building
        painted from the faction sheet itself (its rects mean nothing on another sheet).
            warm    tan and cream (EA's gable frames, beams and tracery: gold)
            dark    slate and dark glass that is not warm (the lattice roofs' slate: tiles)
            light   pale grey strokes (the lattice windows' leading: silver)
            all     every texel (the tree-houses' scale roofs: a darker slate)"""

        def __init__(self, rects, ramp_name, gate, gain=1.0, lift=0.0, strength=1.0):
            self.rects, self.ramp_name, self.gate = rects, ramp_name, gate
            self.gain, self.lift, self.strength = gain, lift, strength

        def mask(self, cv):
            def compute():
                auv = cv.load("auv")
                x, y = auv[..., 0] * cv.atlas.size, (1 - auv[..., 1]) * cv.atlas.size
                inside = np.zeros(x.shape, bool)
                for x0, y0, x1, y1 in self.rects:
                    inside |= (x >= x0) & (x < x1) & (y >= y0) & (y < y1)
                H, S, V = hsv(Foliage.source(cv))
                warm = smooth(S, 0.06, 0.12) * (1 - smooth(S, 0.36, 0.46)) * smooth(H, 14, 20) * \
                    (1 - smooth(H, 56, 64)) * smooth(V, 0.48, 0.62)
                gate = {"warm": warm, "dark": (1 - smooth(V, 0.36, 0.5)) * (1 - warm),
                        "light": smooth(V, 0.45, 0.6) * (1 - smooth(S, 0.2, 0.3)),
                        "all": np.ones_like(V)}[self.gate]
                return (gate * inside * cv.tag_is("old") * cv.covm).astype(np.float32)
            return cv.memo(("repaint", self.gate, tuple(self.rects)), compute)

        def apply(self, col, cv, pal):
            m = (self.strength * self.mask(cv))[..., None]
            L = np.clip(cv.lum * self.gain + self.lift, 0, 1)
            return col * (1 - m) + ramp(L, pal[self.ramp_name]) * m

    return Foliage, Scales, Groove, Repaint


class ElvenStyle(Style):
    faction = "elves"
    name = "Lórien and Rivendell: ivory, mithril and mallorn gold"
    palette = PALETTE
    atlas = ElvenAtlas()
    ini_dir = "data\\ini\\object\\goodfaction\\structures\\elven"
    # art\compiledtextures\eb mixes Elven sheets with Erebor's (the Dwarven barracks and citadel draw
    # EBBarracks; the Erebor map pieces EB_*) and a few civilian props (bridge, shipwreck, port):
    # none of those are Elven buildings, so the sheet pass leaves them (by name prefix)
    sheet_dir = "art\\compiledtextures\\eb"
    not_elven = ("eb_", "ebbarracks", "ebbridge", "ebeam", "ebshipwreck", "ebsiege")
    master_variants = {"damaged": "EBFortress_D.tga", "snow": "EBFortress_Snow.tga", "stonework": "EBFortress_U.tga"}
    budget_mb = 256
    # cloth faces (Building.house_tags, "cloth" by default) leave the body for the house-colour model;
    # walls and expansions, which EA gave none, get a copy of EA's Elven house flag (HC_BANNER)
    house_template = "EBHCBbattleTwr"
    # EA's day meshes painted from another faction's sheet get the faction's own recoloured copy
    # (sagekit/sharedsheets.py): the battle tower's porch lanterns (EBBbattleTwr.EBBBATTLETWRLE) draw
    # Gondor's gbnightwindows by day, which the night-lights standard allows no shipped mesh
    shared_sheets = {"GBNightWindows.tga": "EBLanternPanes.tga"}
    night = STARLIGHT

    def sheets(self, install):
        return [m for m in super().sheets(install) if not m.split("\\")[-1].lower().startswith(self.not_elven)]

    def sheet_size(self, name):
        if name.lower().startswith("gbnightwindows"):
            return 512                  # a 128 sheet: its 4x upscale (the recolour never enlarges past it)
        return 2048 if name.lower().startswith("ebfortress") else 1024

    def sheet_layers(self):
        from sagekit.paint import layers as L
        Foliage = elven_layers()[0]
        return [L.Recolour(**RECOLOUR), Foliage(), L.MetalRims(min_plate=0.45), L.Inlay()]

    def shapes(self):
        from .shapes import ElvenShapes
        return ElvenShapes()

    def layers(self, building):
        from sagekit.paint import layers as L
        Foliage, Scales, Groove, Repaint = elven_layers()
        a = self.atlas
        own = [] if building.two_sheets else [                     # EA's motifs on the faction sheet
            Repaint(a.gilded, "gold", "warm", *GILDED),            # tan frames and tracery: gold
            Repaint(a.roof_slate, "tiles", "dark", *ROOF_SLATE),   # the lattice roofs' slate
            Repaint(a.roof_scales, "tiles", "all", *ROOF_SCALES),  # the tree-houses' scale roofs
            Repaint(a.leading, "trim", "light", *LEADING)]         # the lattice windows' leading: silver
        return [
            L.Recolour(**RECOLOUR),                                # ivory stone, gold metal, silver knotwork
            *[L.TagRamp(tag, r, gain=g, lift=k) for tag, (r, g, k) in TAGRAMPS.items()],
            *own,
            Scales(),                                              # new roofs: one continuous slate skin
            Foliage(),
            L.MetalRims(lift=0.2),
            L.BuildingDecals(building),
            L.WoodGrain(depth=0.22),
            # fine-jointed dressed stone: longer, lower blocks, quieter tints, thin shallow joints
            L.Ashlar(course=4.4, length=(9.0, 6.0), slab=(7.0, 10.0), tint_amount=0.6, tone=0.12, blotch=0.12,
                     fine=0.06, lit=0.08, mortar_dark=0.34, mortar_tint=0.12, groove=0.15),
            Groove(),                                              # the joint beside the metals
            L.Occlusion(),
            L.EdgeWear(base=0.22, metal=0.34),
            L.Streaks(),
            L.GroundDirt(),
            L.Moss(),
            L.Inlay(strength=0.8),
        ]
