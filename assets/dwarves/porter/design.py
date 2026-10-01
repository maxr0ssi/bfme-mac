"""Erebor master builder: a working dwarf, oak tool cart and dressed-stone load.

All coordinates are the original model's rest space. Every new part follows an existing bone;
the living anatomy stays on its original rig. Only the selectable DUPorter_SKN is replaced.
python3 -m sagekit unit dwarves/porter --render (docs/UNITS.md).
"""
import math
import random

from assets.dwarves.style import PALETTE
from sagekit.units import Unit, View
from sagekit.units.paint import crop_rgb, magick

WOOD, OAK, IRON, BRONZE, LEATHER, BLUE, STONE, PAPER, ROPE, HAIR, GOLD, STEEL = range(12)


def chevron(m, x, y, z, width, height, bone, side=False):
    """The stepped Erebor mark on a bronze-backed blue panel."""
    for s in (-1,1):
        a,b = (x,y+s*width,z),(x,y,z+height)
        if side:
            a,b = (x+s*width,y,z),(x,y,z+height)
        m.tube(a,b,.09,GOLD,bone,sides=6)


def cart(m):
    # A plank floor and open-topped chest, with a dark iron chassis and corner straps.
    for y in [-3.6,-1.8,0,1.8,3.6]:
        m.box((-5.8,y-.85,4.65),(5.8,y+.85,5.25),OAK)
    for y in (-3.3,3.3):
        m.box((-6.3,y-.35,3.8),(7.3,y+.35,4.65),IRON)
    m.tube((.49,-7.2,4.046),(.49,7.8,4.046),.36,IRON)
    for y in (-4.8,4.8):
        for z in (5.55,7.0,8.45):
            m.box((-6,y-.25,z),(6,y+.25,z+1.32),WOOD)
        for x in (-5.8,0,5.8):
            m.box((x-.25,y-.34,5.2),(x+.25,y+.34,10.2),IRON)
            for z in (5.8,9.6):
                m.tube((x,y-.44,z),(x,y+.44,z),.15,BRONZE,sides=8)
        m.box((-6.2,y-.4,9.75),(6.2,y+.4,10.25),BRONZE)
        # The faction badge is readable above the wheel from the overhead camera.
        s = 1 if y>0 else -1
        m.box((2.7,y-.48,7.0),(5.35,y+.48,9.6),BRONZE)
        m.box((2.9,y-.5,7.2),(5.15,y+.5,9.4),BLUE)
        chevron(m,4.03,y+s*.54,8.3,.78,.65,"CART",side=True)
        chevron(m,4.03,y+s*.54,7.7,.78,.65,"CART",side=True)
    for x in (-6,6):
        for z in (5.55,7,8.45):
            m.box((x-.22,-4.7,z),(x+.22,4.7,z+1.3),WOOD)
        m.box((x-.4,-5.1,9.75),(x+.4,5.1,10.25),BRONZE)
    # Shafts and crossbar keep the original grip positions; leather protects the handholds.
    for y in (-5.35,5.35):
        m.box((5.6,y-.33,7.3),(23.15,y+.33,7.96),OAK)
        m.box((16.9,y-.38,7.25),(20.7,y+.38,8.01),LEATHER)
        for x in (6.7,12.4):
            m.box((x-.2,y-.4,7.2),(x+.2,y+.4,8.08),IRON)
    m.box((22.65,-5.7,7.3),(23.3,5.7,7.96),OAK)
    # Solid, actually round rims and open spokes, each assigned to the correct wheel bone.
    for y,bone in [(-6.7,"WHEEL_R01"),(7.34,"WHEEL_L01")]:
        for i in range(24):
            a,b = i*2*math.pi/24,(i+1)*2*math.pi/24
            for r0,r1,tag in [(3.55,4.1,OAK),(4.1,4.65,IRON)]:
                for yy,flip in [(y-.4,False),(y+.4,True)]:
                    p=[(.49+r0*math.cos(a),yy,4.046+r0*math.sin(a)),
                       (.49+r1*math.cos(a),yy,4.046+r1*math.sin(a)),
                       (.49+r1*math.cos(b),yy,4.046+r1*math.sin(b)),
                       (.49+r0*math.cos(b),yy,4.046+r0*math.sin(b))]
                    m.face(p[::-1] if flip else p,tag,bone)
                for r in (r0,r1):
                    p=[(.49+r*math.cos(a),y-.4,4.046+r*math.sin(a)),
                       (.49+r*math.cos(a),y+.4,4.046+r*math.sin(a)),
                       (.49+r*math.cos(b),y+.4,4.046+r*math.sin(b)),
                       (.49+r*math.cos(b),y-.4,4.046+r*math.sin(b))]
                    m.face(p[::-1] if r==r0 else p,tag,bone)
        for i in range(8):
            a = i*math.pi/4
            m.tube((.49,y,4.046),(.49+3.75*math.cos(a),y,4.046+3.75*math.sin(a)),.27,OAK,bone,sides=6)
        m.tube((.49,y-.75,4.046),(.49,y+.75,4.046),.73,BRONZE,bone,sides=12)
        m.tube((.49,y-.82,4.046),(.49,y+.82,4.046),.3,IRON,bone,sides=8)


def supplies(m):
    # Individual dressed blocks replace the old single stepped block of stone texture.
    for z,row in [(5.4,range(3)),(7.6,range(2)),(9.8,range(2))]:
        for i in row:
            x=-4.8+3.0*i
            m.box((x,-3.8,z),(x+2.8,.1,z+2.05),STONE if i%2 else 14)
    # Long timber projects above the load without exceeding the old supply silhouette.
    for x,y,z in [(-4.4,2.3,18.7),(-2.3,2.3,17.0),(-.2,2.3,15.4)]:
        m.box((x-.62,y-.62,5.3),(x+.62,y+.62,z),OAK)
        for zz in (11.7,12.05):
            m.box((x-.7,y-.7,zz),(x+.7,y+.7,zz+.19),ROPE)
    # A blue-lidded joiner's chest, brass bands, clasp, and a rolled plan.
    m.box((2.0,.7,5.4),(5.65,4.1,8.5),WOOD)
    m.box((1.85,.55,8.5),(5.8,4.25,9.2),BLUE)
    for x in (2.35,5.0):
        m.box((x-.14,.5,8.45),(x+.14,4.3,9.3),BRONZE)
    m.box((3.5,.43,7.8),(4.1,.65,9),BRONZE)
    m.tube((2.1,1.55,9.55),(5.4,1.55,9.55),.32,PAPER)
    m.tube((3.6,1.55,9.55),(3.85,1.55,9.55),.35,LEATHER)


def outfit(m):
    # Leather bib and split apron. Each lower panel follows its own thigh; the waist follows the
    # lower spine. Gaps between plates are intentional articulation, never a rigid skirt.
    m.box((20.78,-1.9,10.2),(21.02,1.9,11.7),LEATHER,"B_SPINE2_01")
    m.box((20.85,-2.7,8.85),(21.5,2.7,9.5),LEATHER,"B_SPINE1_01")
    for s,bone in [(-1,"BAT_THIGHR_01"),(1,"BAT_THIGHL_01")]:
        lo,hi=sorted((s*.16,s*2.65))
        m.box((21.13,lo,6.0),(21.45,hi,8.7),LEATHER,bone)
        m.box((21.46,lo+.08,6.15),(21.5,hi-.08,6.3),BRONZE,bone)
    m.box((21.5,-.65,8.92),(21.67,.65,9.52),BRONZE,"B_SPINE1_01")
    m.box((21.68,-.43,9.04),(21.7,.43,9.39),BLUE,"B_SPINE1_01")
    # Small leather shoulder guards and bronze edge: the bare moving arms remain visible.
    for s,b in [(-1,"B_UARMR_01"),(1,"B_UARML_01")]:
        m.tube((18.65,s*3.25,12.0),(18.65,s*4.0,11.2),1.22,LEATHER,b,sides=10,r1=1.15)
        m.tube((18.65,s*3.94,11.26),(18.65,s*4.07,11.13),1.19,BRONZE,b,sides=10)
    # Beard bindings follow the beard bones, not the torso: hammering won't pull them off.
    for y in (-.82,.82):
        m.tube((21.75,y,10.15),(21.5,y,11.1),.33,BRONZE,"BONE02_01",sides=8)
        m.tube((21.7,y,10.45),(21.63,y,10.72),.35,BLUE,"BONE02_01",sides=8)


def tools(m):
    b="B_HANDR_01"
    # Original grasp and hammer direction preserved; a forged rectangular head with bright faces.
    m.tube((18.9,-6.35,7.1),(22.5,-7.35,5.65),.22,OAK,b,sides=8)
    m.box((21.6,-8.4,4.65),(23.25,-6.1,6.55),IRON,b)
    for y in (-8.45,-6.1):
        m.box((21.55,y,4.6),(23.3,y+.16,6.6),STEEL,b)
    m.box((21.5,-7.5,4.58),(23.35,-7.0,6.62),BRONZE,b)


# Each swatch comes from the established faction palette. Grain is painted into the texture;
# previews use the original game's material, without Blender-only metallic shading.
SWATCHES = [("wood", .34), ("wood", .47), ("iron", .55), ("bronze", .51),
            ("wood", .25), ("cloth", .48), ("stone", .63), ("stone", .88),
            ("wood", .77), ("rock", .22), ("bronze", .85), ("iron", .9),
            ("wood", .22), ("cloth", .35), ("stone", .42), ("inlay", .6)]
# Preserve the game's painted grain and carved metal. Crops are in the source's 256px grid.
CROPS = [("guporter_cart",(25,25,230,47)),("guporter_cart",(28,180,57,250)),
         ("guporter_cart",(3,3,240,19)),("duporter",(2,34,92,51)),
         ("duporter",(168,175,246,197)),("duporter",(35,184,140,246)),
         ("dbfortress1",(36,199,202,254))]


class Porter(Unit):
    model, skeleton = "DUPorter_SKN", "DUPorter_SKL"
    anims = ("idla", "runa", "wrka", "wrkb", "wrkc", "fira", "diea", "dieb")
    expected = {"duporter_skn": "af7b8eeb0ab43b7447e3238208474fef4bc583aac005bae99b740858e212e62b",
                "duporter_skl": "5aa137518f7cb16365c7e845a8d28b94db290992648b5a9c9f6a80a3c0ba7948"}
    textures = {"duporter.tga": "ducrafts.tga", "guporter_cart.tga": "ducrafts_cart.tga",
                "guporter_build.tga": "ducrafts_build.tga"}
    house = {"ducrafts.tga": "hc_ducrafts.tga", "ducrafts_cart.tga": "hc_ducrafts.tga",
             "ducrafts_build.tga": "hc_ducrafts.tga"}
    mask = ("hc_duporter.tga", "hc_ducrafts.tga")
    sources = ("DBFortress1.tga",)
    archive = "!!!!!!!!!!!!sagekit-dwarf-builder.big"
    smooth = ("DWARF", "HELM", "POUCHES")
    views = {"portrait": View("idla", 0, distance=66, elevation=22, size=(1200, 1050)),
             "rts": View("idla", 0), "run": View("runa", 8),
             "work": View("wrkb", 23, target=(14, 0, 8), distance=105),
             "water": View("fira", 38), "death": View("diea", 45, target=(8, 0, 5), distance=80)}
    labels = ("CURRENT HD BUILDER", "EREBOR MASTER BUILDER - DESIGN PREVIEW")

    def design(self, w, sk):
        result={n:self.mesh(w,sk,n,keep=n in ("DWARF","POUCHES"))
                for n in ("CART_MESH","CARTSUPPLIES","HAMMER","DWARF","POUCHES")}
        cart(result["CART_MESH"])
        supplies(result["CARTSUPPLIES"])
        outfit(result["DWARF"])
        tools(result["HAMMER"])
        return result

    def check(self, b, original, new, sk):
        for n in ("BUCKET", "HELM"):
            assert new.meshes[n].bytes == original.meshes[n].bytes, n

    def paint(self, b):
        samples=[crop_rgb(b.src/(source+".dds"),box,b.work/("grain_%d.rgb"%i))
                 for i,(source,box) in enumerate(CROPS)]
        which=[0,1,6,3,4,5,6,6,1,4,3,6,4,5,6,3]
        rng, pixels = random.Random(73), bytearray()
        for y in range(1024):
            for x in range(1024):
                tag = (y//256)*4 + x//256
                material, mid = SWATCHES[tag]
                ramp = PALETTE.ramps[material]
                u,v=x%256,y%256
                data=samples[which[tag]]; offset=(v*256+u)*3
                lum=sum(data[offset:offset+3])/765
                edge=min(u,v,255-u,255-v)/255
                value = max(0, min(1, mid + (lum-.45)*.9 + rng.uniform(-.025,.025)
                                   + (.12 if edge<.018 else -.09 if edge<.03 else 0)))
                for (a, ca), (c, cb) in zip(ramp,ramp[1:]):
                    if a <= value <= c:
                        t = (value-a)/(c-a)
                        rgb=[aa*(1-t)+bb*t for aa,bb in zip(ca,cb)]
                        if material=="wood":
                            gray=sum(rgb)/3
                            rgb=[q*.42+gray*.58 for q in rgb]
                        pixels.extend(round(255*q) for q in rgb)
                        break
        ppm = b.work / "materials.ppm"
        ppm.write_bytes(b"P6\n1024 1024\n255\n" + pixels)
        atlas = b.work / "craftsman.png"
        # EA's character UV islands tile outside 0..1. Repeat the original four times each way,
        # then transform UVs affinely; modulo per vertex would stretch triangles across the seams.
        magick("-size", "1024x1024", "tile:"+str(b.src/"duporter.dds"),
               "(",ppm,"-resize","1024x1024!",")","+append",atlas)
        return atlas
