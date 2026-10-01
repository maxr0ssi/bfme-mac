"""A Lórien craftsman: curved birch cart, silver fittings, gold leaves and real building supplies.

Retains the original elf's anatomy, face, hair and rig; all cart parts follow their original bones.
python3 -m sagekit unit elves/porter --render (docs/UNITS.md).
"""
import math

from assets.elves.style import PALETTE
from sagekit.units import Unit, View
from sagekit.units.paint import magick, ramp_bytes

BIRCH, WOOD, SILVER, GOLD, CLOTH, LEATHER, STONE, PAPER, BRIGHT, SLATE = range(10)


def curve(m,points,r,tag,bone="CART"):
    for a,b in zip(points,points[1:]):
        m.tube(a,b,r,tag,bone,sides=6)


def leaf(m,centre,width,height,tag=GOLD,bone="CART",side=False):
    x,y,z=centre
    # A closed, subtly folded leaf, with a raised central vein.
    outline=[(-width*.5,0),(-width*.37,height*.45),(0,height),
             (width*.37,height*.45),(width*.5,0),(0,-height*.12)]
    def point(u,v,depth):return (x+u,y+depth,z+v) if side else (x+depth,y+u,z+v)
    for sign in (-1,1):
        mid=point(0,height*.32,sign*.10)
        for i in range(len(outline)):
            a=point(*outline[i],0);b=point(*outline[(i+1)%len(outline)],0)
            m.face([mid,a,b] if sign>0 else [mid,b,a],tag,bone)


def cart(m):
    for y in (-3.3,-1.65,0,1.65,3.3):
        m.box((-5.6,y-.78,4.7),(5.7,y+.78,5.13),BIRCH)
    for y in (-3.3,3.3):
        m.box((-5.9,y-.24,3.9),(6.0,y+.24,4.75),WOOD)
    m.tube((.485,-6.8,4.046),(.485,7.4,4.046),.25,SILVER,sides=8)
    # Low curved rails and slender leaf ribs keep the load visible.
    for y in (-4.55,4.55):
        for x in (-5.5,-2.0,2.1,5.6):
            m.tube((x,y,5.05),(x,y,9.0),.19,SILVER,sides=6)
        top=[(-5.6,y,9.2),(-4.0,y,9.7),(-2.0,y,10.0),(0,y,10.1),
             (2.0,y,10.0),(4.1,y,9.7),(5.7,y,9.2)]
        curve(m,top,.26,BIRCH)
        curve(m,[(x,y,z+.22) for x,y,z in top],.07,GOLD)
        m.box((-5.55,y-.15,5.45),(5.6,y+.15,6.4),BIRCH)
        for x in (-3.8,0,3.8):
            curve(m,[(x-1.1,y,6.35),(x-.65,y,7.0),(x,y,8.35),
                     (x+.65,y,7.0),(x+1.1,y,6.35)],.10,SILVER)
            leaf(m,(x,y,8.3),.58,1.12,side=True)
    for x in (-5.5,5.6):
        for z in (5.65,7.0,8.7):
            m.tube((x,-4.55,z),(x,4.55,z),.21,BIRCH,sides=6)
        leaf(m,(x,0,7.1),1.05,1.9)
    # The original grasp points and rail heights are unchanged.
    for y in (-4.67,5.34):
        curve(m,[(5.5,y,6.0),(8.0,y,7.5),(12.0,y,8.9),(16.0,y,9.10),(23.30,y,9.10)],.27,BIRCH)
        m.tube((14.3,y,9.1),(18.1,y,9.1),.31,LEATHER,sides=8)
        for x in (13.8,18.6):
            m.tube((x-.12,y,9.1),(x+.12,y,9.1),.33,SILVER,sides=8)
    m.tube((22.9,-4.67,9.1),(22.9,5.34,9.1),.31,BIRCH,sides=8)
    # Ring locations come from the source wheel geometry, not the offset bone pivots.
    for y,bone in [(-5.94,"WHEEL_R01"),(6.58,"WHEEL_L01")]:
        for i in range(24):
            a,b=i*math.tau/24,(i+1)*math.tau/24
            for r0,r1,tag in [(3.75,4.30,BIRCH),(4.30,4.66,SILVER)]:
                for yy,flip in [(y-.35,False),(y+.35,True)]:
                    pts=[(.485+r0*math.cos(a),yy,4.046+r0*math.sin(a)),
                         (.485+r1*math.cos(a),yy,4.046+r1*math.sin(a)),
                         (.485+r1*math.cos(b),yy,4.046+r1*math.sin(b)),
                         (.485+r0*math.cos(b),yy,4.046+r0*math.sin(b))]
                    m.face(pts[::-1] if flip else pts,tag,bone)
                for r in (r0,r1):
                    pts=[(.485+r*math.cos(a),y-.35,4.046+r*math.sin(a)),
                         (.485+r*math.cos(a),y+.35,4.046+r*math.sin(a)),
                         (.485+r*math.cos(b),y+.35,4.046+r*math.sin(b)),
                         (.485+r*math.cos(b),y-.35,4.046+r*math.sin(b))]
                    m.face(pts[::-1] if r==r0 else pts,tag,bone)
        for i in range(10):
            a=i*math.tau/10
            points=[(.485+rr*math.cos(a+bend),y,4.046+rr*math.sin(a+bend))
                    for rr,bend in [(0,0),(1.5,.1),(2.8,.08),(3.92,0)]]
            curve(m,points,.18,BIRCH,bone)
        m.tube((.485,y-.60,4.046),(.485,y+.60,4.046),.6,SILVER,bone,sides=10)
        m.tube((.485,y-.67,4.046),(.485,y+.67,4.046),.29,GOLD,bone,sides=8)


def supplies(m):
    # Dressed ivory masonry and warm timber, below the original supply silhouette.
    for z,starts in [(5.2,(-4.8,-1.7,1.4)),(7.55,(-4.7,-1.6))]:
        for i,x in enumerate(starts):
            m.box((x,-3.35,z),(x+2.9,-.1,z+2.15),STONE if i%2 else 14)
    for x,height in [(-4.4,18.7),(-2.8,17.3),(-1.2,15.8)]:
        m.box((x-.49,1.6,5.2),(x+.49,2.7,height),BIRCH)
    for z in (11.5,11.82):
        m.box((-4.97,1.48,z),(-.62,2.82,z+.15),LEATHER)
    # A slender pre-carved arch, a visible piece of the architecture this builder makes.
    points=[(-5.0,3.65,6.0),(-4.8,3.65,11.0),(-3.8,3.65,14.0),
            (-2.4,3.65,16.0),(-.8,3.65,17.5)]
    curve(m,points,.34,BIRCH)
    curve(m,[(x+.28,y-.08,z) for x,y,z in points],.095,GOLD)
    m.box((1.2,.5,5.2),(5.35,3.7,8.0),WOOD)
    m.box((1.1,.4,8.0),(5.45,3.8,8.55),CLOTH)
    for x in (1.55,4.95):
        m.box((x-.12,.35,7.95),(x+.12,3.85,8.65),SILVER)
    leaf(m,(3.25,.29,7.3),.58,1.0,side=True)
    for y in (1.4,2.3):
        m.tube((1.7,y,8.98),(4.9,y,8.98),.32,PAPER,sides=10)
        m.tube((3.0,y,8.98),(3.28,y,8.98),.35,LEATHER,sides=8)
    # Small mallet and ruler are load props, never substitutes for the animated held tool.
    m.tube((.1,-2.2,10.1),(.1,.5,10.1),.14,BIRCH,sides=6)
    m.box((-.6,-2.65,9.75),(.8,-1.9,10.5),SILVER)
    m.box((1.6,-3.2,7.45),(4.8,-2.96,7.62),GOLD)


SWATCHES = [("wood",.65),("wood",.47),("trim",.64),("gold",.67),
            ("cloth",.55),("wood",.22),("stone",.65),("stone",.86),
            ("trim",.84),("tiles",.4),("gold",.83),("stone",.5),
            ("wood",.32),("crystal",.68),("stone",.74),("cloth",.3)]


def colour(material,value):
    return ramp_bytes(PALETTE.ramps[material],value)


class Porter(Unit):
    """EA's Elf on the shared Gondor porter rig and animations (GUPorter_SKL)."""
    model, skeleton = "EUPorter_SKN", "GUPorter_SKL"
    anims = ("idla", "idlb", "runa", "wlka", "fira", "diea", "dieb")
    expected = {"euporter_skn": "aa03bb943f1c2de458b2adac765b71ef237fc0086bd22bb5cfae24c11fba869b",
                "guporter_skl": "cb8a6fa38469fd95ac1c791843a75c013fdec5684503b4711b0485a4eee5e9ec"}
    textures = {"euworker.tga": "eucrafts.tga", "guporter_cart.tga": "eucrafts.tga",
                "guporter_build.tga": "eucrafts.tga"}
    house = {"EUCrafts.tga": "HC_EUCrafts.tga"}
    mask = ("HC_EUWorker.tga", "HC_EUCrafts.tga")
    archive = "!!!!!!!!!!!!sagekit-elf-builder.big"
    same_bones = ("CART_MESH", "CARTSUPPLIES")
    smooth = ("ELF",)
    # These legacy opaque meshes ignore texture alpha in game. Blender otherwise
    # premultiplies the stored diffuse colours, turning most of EUWorker black.
    opaque = True
    views = {"portrait": View("idla", 0, target=(8, 0, 11), distance=76, elevation=22, size=(1200, 1100)),
             **{k: View(a, f, target=(8, 0, 11), distance=84, size=(1100, 950))
                for k, (a, f) in {"rts": ("idla", 0), "run": ("runa", 8), "walk": ("wlka", 8),
                                  "water": ("fira", 38), "idle": ("idlb", 30)}.items()},
             "death": View("diea", 45, size=(1100, 950), fit=True),
             "fall": View("dieb", 10, size=(1100, 950), fit=True)}
    labels = ("ORIGINAL ELVEN BUILDER", "ELVEN MASTER CRAFTSMAN - REVIEW")
    label_colour = "#17251dcc"

    def design(self, w, sk):
        meshes={n:self.mesh(w,sk,n,keep=n=="ELF") for n in ("CART_MESH","CARTSUPPLIES","ELF")}
        cart(meshes["CART_MESH"])
        supplies(meshes["CARTSUPPLIES"])
        return meshes

    def check(self, b, original, new, sk):
        for n in ("BUCKET","HAMMER"):
            assert original.meshes[n].bytes == new.meshes[n].bytes,n

    def paint(self, b):
        src, work = b.src, b.work
        # Preserve the original skin/hair and painted clothing detail; change only cloth regions.
        magick(src/"euworker.dds","-alpha","off","-depth","8","rgb:"+str(work/"body.rgb"))
        body = bytearray((work/"body.rgb").read_bytes())
        for y in range(256):
            for x in range(256):
                i = (y*256+x)*3
                old = body[i:i+3]
                lum = sum(old)/765
                if x < 125 and y < 110:
                    body[i:i+3] = colour("stone", .18+lum*.88)
                elif x < 126 and y >= 115:
                    body[i:i+3] = colour("cloth", .18+lum*.85)
        (work/"body.ppm").write_bytes(b"P6\n256 256\n255\n"+body)
        # Sample painted wood grain instead of flat plastic colours; the existing palette supplies hue.
        magick(src/"guporter_cart.dds","-alpha","off","-crop","205x22+25+25","+repage",
               "-resize","256x256!","-depth","8","rgb:"+str(work/"grain.rgb"))
        grain = (work/"grain.rgb").read_bytes()
        pixels = bytearray()
        for y in range(1024):
            for x in range(1024):
                tag = (y//256)*4+x//256
                mat,mid = SWATCHES[tag]
                u,v = x%256,y%256
                i = (v*256+u)*3
                lum = sum(grain[i:i+3])/765
                edge = min(u,v,255-u,255-v)
                value = mid+(lum-.45)*(1.65 if mat=="wood" else .42)
                if mat in ("trim","gold"):
                    value += .10*math.sin(u*math.pi/128)
                value += .10 if edge<4 else -.06 if edge<8 else 0
                pixels.extend(colour(mat,value))
        (work/"materials.ppm").write_bytes(b"P6\n1024 1024\n255\n"+pixels)
        magick("-size","1024x1024","tile:"+str(work/"body.ppm"),work/"materials.ppm",
               "+append",work/"eucrafts.png")
        return work/"eucrafts.png"
