"""The Angmar shape vocabulary (Blender side): Carn Dum, the Witch-king's frozen hold. Where Mordor
is volcanic (basalt split by lava, hooked horns) and Isengard machined (lozenge blades, silver
edges), Angmar is frost on black iron: jagged iron spikes notched like the Witch-king's crown,
angular ice-crystal shards growing out of the stone (never round), icicles under every ledge, rime
crusts, cold blue-white fire. Every piece returns closed solids (sagekit.blender.geometry.Solid)
tagged with AngmarAtlas regions only (assets/angmar/atlas.py).

Placement as in the other kits:
    points      base / centre points and directions in 3D (spikes, shards, chains)
    a, t, n     a wall face: anchor a, along t, out along n; u along the face, z up, d out
                (sagekit.blender.geometry.prism_uz)

Tags: stoneA/stoneB (the dark dressed stone), slab, rock (raw stone), timber, planks, roof, iron,
steel (the cold lit edges of iron spikes), chain, soot, trim, slit, ice (the ice shards: pale blue
crystal), rime (frost crusts, white), flame and ember (cold fire's glow), cloth. The generic pieces
borrowed from the Mordor and Isengard kits name "wood", "mark", "water" and "witch": `retag` maps
them onto Angmar's (TAGS), so a recipe's design() ends with `return kit.retag(solids)`.

Ice (shapes_ice.py, IceKit)
    shard, ice_cluster, icicles, rime_crust
The crown (shapes_crown.py, CrownKit)
    CrownSpike, crown_spike, witch_crown, cold_brazier, frozen_captive
Borrowed (assets/mordor): HornKit (Horn, horn, witch_slit), StoryKit (cage, gibbet, portcullis),
LavaKit (face_crack); (assets/isengard) WorksKit (chain, hook, rivets, plate, spike_row, banner),
YardKit (scaffold, lantern), FireKit (fire, flames).
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

from assets.isengard.shapes import arc, beam, ring, side_of, tube, unit
from assets.isengard.shapes_fire import FireKit
from assets.isengard.shapes_works import WorksKit
from assets.isengard.shapes_yard import YardKit
from assets.mordor.shapes import MordorShapes
from assets.mordor.shapes_horn import HornKit
from assets.mordor.shapes_lava import LavaKit
from assets.mordor.shapes_story import StoryKit

from .shapes_crown import CrownKit
from .shapes_ice import IceKit
from .shapes_tine import TineKit

# the borrowed pieces' tag names -> Angmar's
TAGS = {"wood": "timber", "mark": "flame", "water": "ice", "witch": "slit"}


class AngmarShapes(IceKit, CrownKit, TineKit, HornKit, LavaKit, StoryKit, WorksKit, YardKit, FireKit):
    """The Angmar kit. Stable API: add pieces, keep these signatures (every Angmar recipe uses them)."""

    Z = Z
    V = V
    tube = staticmethod(tube)
    arc = staticmethod(arc)
    unit = staticmethod(unit)
    side_of = staticmethod(side_of)
    ring = staticmethod(ring)
    beam = staticmethod(beam)
    loft = staticmethod(loft)
    prism_uz = staticmethod(prism_uz)
    barb = MordorShapes.barb
    hung_chain = MordorShapes.hung_chain

    @staticmethod
    def retag(solids):
        """The borrowed pieces' tags ("wood", "mark", "water", "witch") onto Angmar's (TAGS), in place."""
        for s in solids:
            polys = []
            for pts, tag, keep in s.polys:
                base, _, rest = tag.partition("|")
                if base in TAGS:
                    tag = TAGS[base] + ("|" + rest if rest else "")
                polys.append((pts, tag, keep))
            s.polys = polys
        return solids

    @staticmethod
    def polar(c, r, deg, z):
        """The point r out from c at `deg` round it, at height z."""
        a = math.radians(deg)
        return V((c[0] + r * math.cos(a), c[1] + r * math.sin(a), z))
