"""The Goblin burrows (WildBurrowsExpansion): EA's hide-draped mound kept whole - the hunched roof,
the drapes and wings, the dark mouth under its hood, the stepped stone pad, the two skull poles -
and made the carcass of some great beast the Goblins dug into, in blood, iron and bone: four
bleached pairs of ribs arch over the roof from a skirt of black rock (pad.py, the expansions' pad),
a spine of vertebrae along the ridge joins them and runs down as its neck to the beast's horned
skull over the mouth's hood, two pairs of iron-collared tusks rise either side of the steps like
its jaws, skull piles lie by the mouth and a carcass hangs from the hood. No banner (the cap for the burrows is 0).

EA's facts (WBFBURROW mesh coordinates, measured; work/measure.json): WBFBurrow, 588 triangles on
WBFortress.tga (own copy WBFortresB.tga); x -51.76..-0.13, |y| <= 20.64, z -0.12..43.48. The
body narrows from the front (|y| ~12 at x -30, the drapes' tips to |y| 19.6 at z 26-30) to the flat
back wall (x -51.8, |y| 5.6, to z 33); the roof rises from z 33 at the back to 43.5 at x -28 and
falls to the hood (x -14..-9, z 30-32). The mouth: the front wall x -17, |y| < 7.7, z 1.7..26.8,
the steps in front of it (x -17..0, z 0..1.7): units come out here, so nothing new stands in
x > -18, |y| < 9 below z 29. The skull poles stand at (-16, +-17.9) to z 40.7. Lifecycle:
WBFBurrow_A (construction), _D2, _D3. House colour: none of EA's; our own (HOUSE_DRAW), no cloth.
"""
from sagekit.building import Building

from ..style import GoblinStyle

# the ribs over the roof: (x, half-width of the feet, apex); the roof below: z 33.5, 36, 39, 42.5
ARCHES = [(-47.0, 10.5, 37.8), (-41.0, 12.8, 40.8), (-35.0, 14.6, 44.2), (-29.0, 15.8, 47.2)]
SKULL = (-10.6, 0.0, 35.3, 7.0)                         # the beast's skull over the hood: x, y, z, size
TUSKS = [(-6.5, 13.5), (-12.5, 15.5)]                   # the jaws' roots either side of the steps (x, |y|)
PILES = [(-3.5, -17.0, 3, 2.3, 1), (-3.0, 17.2, 3, 2.2, 4), (-47.0, -9.5, 2, 2.0, 6)]


class Burrows(Building):
    style = GoblinStyle()
    source = "WBFBurrow"
    target = "WBFBURROW"
    sheet = "WBFortress.tga"
    sheet_normal = "WBFortress_NRM.tga"
    own_textures = {"WBFortress.tga": "WBFortresB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the Goblin kit's unwrap overlaps a little: seams at EA's islands and 8-degree turns
    HOUSE_DRAW = "ModuleTag_Draw_HCBurrows"
    views = {
        "rts": ((-25.9, -0.0, 21.7), 174, 50, -38, 50),
        "close": ((-24.0, 0.0, 22.0), 140, 22, -38, 45),
        "ingame": ((-25.9, -0.0, 21.7), 396, 53, -62, 50),
    }

    def design(self, kit):
        from ..arrow_den import pad
        V, Z = kit.V, kit.Z
        box = (-51.76, -0.13, -20.64, 20.64)
        outline = [(-20.0, -17.0), (-30.0, -14.5), (-40.0, -11.0), (-50.5, -6.5), (-50.5, 6.5), (-40.0, 11.0),
                   (-30.0, 14.5), (-20.0, 17.0)]
        out = pad.skirt(kit, outline, (-32.0, 0.0), r=2.6, h=2.6, pitch=3.3, out=0.9, seed=7, box=box, closed=False)
        # the beast's ribcage over the roof, its spine along the ridge
        for i, (x, half, apex) in enumerate(ARCHES):
            out += pad.arch(kit, x, half, apex, r=1.1 + 0.05 * i, bulge=0.1)
            for e in (-1, 1):
                out += pad.rock(kit, (x, e * (half + 0.4)), 2.6, 2.8, seed=20 + i * 2 + e)
        for (x0, _, z0), (x1, _, z1) in zip(ARCHES, ARCHES[1:]):
            out += kit.spine(V((x0 + 1.4, 0, z0 + 0.3)), V((x1 - 1.4, 0, z1 + 0.3)), 0.75, n=3)
        x, _, z = ARCHES[-1]
        out += kit.spine(V((x + 1.4, 0, z + 0.2)), V((-15.5, 0, 38.8)), 0.8, n=5)       # the neck, to the skull
        # the skull over the hood, the tusks either side of the steps
        sx, sy, sz, s = SKULL
        out += kit.horned_skull(V((sx, sy, sz)), (1, 0, 0), s, horn=1.45, detail=2)
        for (tx, ty), length in zip(TUSKS, (24.0, 21.0)):
            for e in (-1, 1):
                base = V((tx, e * ty, 1.4))
                out += kit.tusk(base, V((0.05, e * 0.25, 1.0)), V((0.1, -e * 0.9, 0.35)), length, 1.5, n=6, k=6)
                out += pad.rock(kit, (tx, e * (ty + 0.6)), 2.2, 2.0, seed=40 + int(tx) + e)
        for px, py, count, size, seed in PILES:
            out += kit.skull_pile(V((px, py, 0.0)), 3.0, count, size, seed=seed, face=(1, -0.5, 0))
        out += kit.chain(V((-11.0, -11.8, 31.4)), V((-11.0, -11.8, 28.6)))
        out += kit.carcass(V((-11.0, -11.8, 28.4)), 7.0, 1.6, facing=(1, -0.4, 0))
        return out

    def decals(self):
        from ..paint import goblin_layers
        sx, sy, sz, s = SKULL
        anchors = [(sx + 1.0, sy, sz - 1.5, 3.0, 9.0), (-11.0, -11.8, 22.0, 1.8, 3.0)]
        anchors += [(px, py, 0.8, 2.6, 2.0) for px, py, *_ in PILES]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        return 1.3 if c.z > 28 else 1.0
