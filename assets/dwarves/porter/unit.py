"""Build the selectable Dwarven craftsman for review: python3 -m assets.dwarves.porter.unit.

Writes only build/assets/dwarves/porter. --render also makes posed before/after previews;
--check verifies the built W3D against its source. There is deliberately no install command.
"""
import argparse
import hashlib
import json
import math
import random
import subprocess
from pathlib import Path

from assets.dwarves.style import PALETTE
from sagekit import paths
from sagekit.formats import w3dmesh as WM
from sagekit.formats import w3dpose as P
from sagekit.formats.textures import compiled_path, write_dds
from sagekit.formats.w3d import MESH, NORMALS, STAGE_TEXCOORDS, VERTICES, W3DFile, rename_textures
from sagekit.game import Install

FOLDER = Path(paths.BUILD) / "dwarves/porter"
ANIMS = ("idla", "runa", "wrka", "wrkb", "wrkc", "fira", "diea", "dieb")
EXPECTED = {"skn": "af7b8eeb0ab43b7447e3238208474fef4bc583aac005bae99b740858e212e62b",
            "skl": "5aa137518f7cb16365c7e845a8d28b94db290992648b5a9c9f6a80a3c0ba7948"}
NAMES = {"duporter.tga": "ducrafts.tga", "guporter_cart.tga": "ducrafts_cart.tga",
         "guporter_build.tga": "ducrafts_build.tga"}
# Each swatch comes from the established faction palette. Grain is painted into the texture;
# previews use the original game's material, without Blender-only metallic shading.
SWATCHES = [("wood", .34), ("wood", .47), ("iron", .55), ("bronze", .51),
            ("wood", .25), ("cloth", .48), ("stone", .63), ("stone", .88),
            ("wood", .77), ("rock", .22), ("bronze", .85), ("iron", .9),
            ("wood", .22), ("cloth", .35), ("stone", .42), ("inlay", .6)]


def uv_for(tag, u, v):
    return (.5 + ((tag % 4) + .05 + .9 * u) / 8, 1 - ((tag // 4) + .95 - .9 * v) / 4)


class Mesh:
    """This recipe's polygons, bound to the existing rig and serialized by sagekit's mesh writer."""

    def __init__(self, original, skeleton, keep=False):
        self.original, self.skeleton = original, skeleton
        self.verts, self.tris = [], []
        if keep:
            bones = P.influences(original.bytes)
            for i, bone in enumerate(bones):
                self.verts.append((0, [(i, 1)], P.IDENTITY, bone,
                                   {STAGE_TEXCOORDS: ((original.uv[i][0]+2)/8, (original.uv[i][1]+2)/4)}))
            self.tris = list(zip(original.tris, original.surface))

    def face(self, points, tag, bone, uvs=None):
        a, b, c = points[:3]
        e, f = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
        n = (e[1] * f[2] - e[2] * f[1], e[2] * f[0] - e[0] * f[2], e[0] * f[1] - e[1] * f[0])
        if sum(x * x for x in n) < 1e-12:
            raise ValueError("degenerate design face")
        bone = self.skeleton.index(bone)
        transform = P.invert(self.skeleton.rest[bone])
        off = len(self.verts)
        uv = uvs or [(0, 0), (1, 0), (1, 1), (0, 1)][:len(points)]
        for p, (u, v) in zip(points, uv):
            self.verts.append((0, [(0, 1)], transform, bone,
                               {VERTICES: p, NORMALS: n, STAGE_TEXCOORDS: uv_for(tag, u, v)}))
        self.tris += [((off, off + i, off + i + 1), self.original.surface[0]) for i in range(1, len(points) - 1)]

    def box(self, lo, hi, tag, bone="CART"):
        x, y, z = lo
        X, Y, Z = hi
        bevel = min(.09,min(X-x,Y-y,Z-z)/5)
        rings=[]
        for inset,zz in [(bevel,z),(0,z+bevel),(0,Z-bevel),(bevel,Z)]:
            a,b,c,d=x+inset,X-inset,y+inset,Y-inset
            k=bevel*.4 if inset else bevel
            rings.append([(a+k,c,zz),(b-k,c,zz),(b,c+k,zz),(b,d-k,zz),
                          (b-k,d,zz),(a+k,d,zz),(a,d-k,zz),(a,c+k,zz)])
        for lower,upper in zip(rings,rings[1:]):
            for i in range(8):
                j=(i+1)%8
                self.face([lower[i],lower[j],upper[j],upper[i]],tag,bone)
        for pts,zz,rev in [(rings[0],z,True),(rings[-1],Z,False)]:
            for i in range(8):
                j=(i+1)%8
                face=[((x+X)/2,(y+Y)/2,zz),pts[j if rev else i],pts[i if rev else j]]
                self.face(face,tag,bone,[((p[0]-x)/(X-x),(p[1]-y)/(Y-y)) for p in face])

    def tube(self, a, b, r, tag, bone="CART", sides=10, r1=None):
        d = [b[i] - a[i] for i in range(3)]
        length = math.sqrt(sum(x*x for x in d))
        d = [x / length for x in d]
        up = (0, 0, 1) if abs(d[2]) < .9 else (0, 1, 0)
        u = (d[1]*up[2]-d[2]*up[1], d[2]*up[0]-d[0]*up[2], d[0]*up[1]-d[1]*up[0])
        q = math.sqrt(sum(x*x for x in u)); u = [x/q for x in u]
        v = (d[1]*u[2]-d[2]*u[1], d[2]*u[0]-d[0]*u[2], d[0]*u[1]-d[1]*u[0])
        rings = [[tuple(c[j] + radius*(u[j]*math.cos(i*2*math.pi/sides) + v[j]*math.sin(i*2*math.pi/sides))
                        for j in range(3)) for i in range(sides)] for c,radius in [(a,r),(b,r if r1 is None else r1)]]
        for i in range(sides):
            k = (i+1) % sides
            self.face([rings[0][i],rings[0][k],rings[1][k],rings[1][i]],tag,bone)
            self.face([a,rings[0][k],rings[0][i]],tag,bone)
            self.face([b,rings[1][i],rings[1][k]],tag,bone)

    def chunk(self):
        m = self.original
        raw = WM.build_mesh(m.bytes, {0: WM.Source(m.bytes)}, m.name, m.container,
                            self.verts, self.tris, True, self.skeleton.rest)
        return rename_textures(raw, [(None,k,v) for k,v in NAMES.items()], m.name)


def prepare():
    src = FOLDER / "src"
    src.mkdir(parents=True, exist_ok=True)
    g = Install()
    hashes = {}
    for n in ("skn", "skl") + ANIMS:
        member = g.model_path("duporter_" + n)
        data = g.read(member)
        if n in EXPECTED and hashlib.sha256(data).hexdigest() != EXPECTED[n]:
            raise SystemExit("Unsupported builder %s: inspect the model/rig before using this recipe." % n)
        (src / ("duporter_" + n + ".w3d")).write_bytes(data)
        hashes[member] = hashlib.sha256(data).hexdigest()
    w = W3DFile(str(src / "duporter_skn.w3d"))
    textures = {}
    for name in sorted({t.lower() for m in w.meshes.values() for t in m.textures}):
        dest = src / (name[:-4] + ".dds")
        dest.write_bytes(g.read(compiled_path(name, ".dds")))
        textures[name] = str(dest)
    (FOLDER / "textures.json").write_text(json.dumps(textures, indent=2))
    (src/"dbfortress1.dds").write_bytes(g.read(compiled_path("DBFortress1.tga", ".dds")))
    (FOLDER / "sources.json").write_text(json.dumps(hashes, indent=2))
    return w, P.Skeleton((src / "duporter_skl.w3d").read_bytes())


def paint():
    work = FOLDER / "work"
    # Preserve the game's painted grain and carved metal. Crops are in the source's 256px grid.
    crops = [("guporter_cart",(25,25,230,47)),("guporter_cart",(28,180,57,250)),
             ("guporter_cart",(3,3,240,19)),("duporter",(2,34,92,51)),
             ("duporter",(168,175,246,197)),("duporter",(35,184,140,246)),
             ("dbfortress1",(36,199,202,254))]
    samples=[]
    for i,(source,(x,y,X,Y)) in enumerate(crops):
        dest=work/("grain_%d.rgb"%i)
        subprocess.run(["magick",str(FOLDER/"src"/(source+".dds")),"-resize","256x256!","-crop",
                        "%dx%d+%d+%d"%(X-x,Y-y,x,y),"+repage","-resize","256x256!","-depth","8","rgb:"+str(dest)],check=True)
        samples.append(dest.read_bytes())
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
            for (a, ca), (b, cb) in zip(ramp,ramp[1:]):
                if a <= value <= b:
                    t = (value-a)/(b-a)
                    rgb=[aa*(1-t)+bb*t for aa,bb in zip(ca,cb)]
                    if material=="wood":
                        gray=sum(rgb)/3
                        rgb=[c*.42+gray*.58 for c in rgb]
                    pixels.extend(round(255*c) for c in rgb)
                    break
    ppm = work / "materials.ppm"
    ppm.write_bytes(b"P6\n1024 1024\n255\n" + pixels)
    atlas = work / "craftsman.png"
    # EA's character UV islands tile outside 0..1. Repeat the original four times each way,
    # then transform UVs affinely; modulo per vertex would stretch triangles across the seams.
    subprocess.run(["magick", "-size", "1024x1024", "tile:"+str(FOLDER/"src/duporter.dds"),
                    "(",str(ppm),"-resize","1024x1024!",")","+append",str(atlas)],check=True)
    textures = json.loads((FOLDER / "textures.json").read_text())
    for name in NAMES.values():
        dest = work / (name[:-4] + ".dds")
        write_dds(str(atlas), str(dest))
        textures[name] = str(dest)
    (work / "textures.json").write_text(json.dumps(textures, indent=2))


def paint_mask():
    """Add player colour without rebuilding the reviewed model or diffuse atlases."""
    src, work = FOLDER/"src", FOLDER/"work"
    source = Install().read(compiled_path("hc_duporter.tga", ".tga"))
    (src/"hc_duporter.tga").write_bytes(source)
    mask = subprocess.check_output(["magick",str(src/"hc_duporter.tga"),"-depth","8","rgba:-"])
    assert len(mask) == 256*256*4
    # Repeat raw rows: compositing would clear the RGB of neutral transparent white.
    pixels = b"".join(mask[(y%256)*1024:(y%256+1)*1024]*4+
                      bytes((255,255,255,0))*1024 for y in range(1024))
    (work/"mask.rgba").write_bytes(pixels)
    subprocess.run(["magick","-size","2048x1024","-depth","8",
                    "rgba:"+str(work/"mask.rgba"),str(work/"hc_ducrafts.tga")],check=True)


def check_mask():
    source = FOLDER/"src/hc_duporter.tga"
    assert source.read_bytes() == Install().read(compiled_path("hc_duporter.tga", ".tga"))
    raw = lambda p: subprocess.check_output(["magick",str(p),"-depth","8","rgba:-"])
    mask, original = raw(FOLDER/"work/hc_ducrafts.tga"), raw(source)
    assert len(mask) == 2048*1024*4 and len(original) == 256*256*4
    for y in range(1024):
        row = mask[y*8192:(y+1)*8192]
        assert row[:4096] == original[(y%256)*1024:(y%256+1)*1024]*4
        assert row[4096:] == bytes((255,255,255,0))*1024


def check():
    check_mask()
    src, work = FOLDER / "src", FOLDER / "work"
    original, new = W3DFile(str(src/"duporter_skn.w3d")), W3DFile(str(work/"duporter_skn.w3d"))
    sk = P.Skeleton((src/"duporter_skl.w3d").read_bytes())
    assert original.skeleton() == new.skeleton()
    assert [b for t,b in original.top() if t != MESH] == [b for t,b in new.top() if t != MESH]
    assert new.meshes.keys() == original.meshes.keys()
    assert new.meshes["BUCKET"].bytes == original.meshes["BUCKET"].bytes
    assert new.meshes["HELM"].bytes == original.meshes["HELM"].bytes
    for name,m in new.meshes.items():
        assert len(m.uv) == len(m.verts) == len(m.normals), name
        assert all(0 <= i < len(m.verts) for t in m.tris for i in t), name
        assert all(math.isfinite(x) for v in m.verts for x in v), name
        assert all(math.isfinite(x) for uv in m.uv for x in uv), name
        if name not in ("HELM", "BUCKET"):
            assert all(0 <= x <= 1 for uv in m.uv for x in uv), name
        if m.skinned:
            assert len(P.influences(m.bytes)) == len(m.verts), name
            assert all(0 <= b < len(sk.pivots) for b in P.influences(m.bytes)), name
    # Keep the face, hands, boots and flexible body exactly on EA's rig; only their UVs move.
    old, body = original.meshes["DWARF"], new.meshes["DWARF"]
    assert body.verts[:len(old.verts)] == old.verts
    assert P.influences(body.bytes)[:len(old.verts)] == P.influences(old.bytes)
    for anim in ANIMS:
        a = P.Animation((src/("duporter_"+anim+".w3d")).read_bytes())
        assert a.hierarchy.upper() == sk.name.upper()
        assert a.frames > 0
    (work/"checks.txt").write_text("PASS: unchanged skeleton/HLOD/bucket/helmet; original body vertices and bone assignments; mesh, UV and bone indices; animation hierarchy headers.\nMotion decoding is checked separately by preview.py with OpenSAGE. Not an in-game approval.\n")
    print((work/"checks.txt").read_text())


def previews(states):
    from sagekit.pipeline import blender_slot, game_running
    if game_running():
        raise SystemExit("The game is running; close it before rendering builder previews.")
    for state in states:
        for who in ("original", "new"):
            with blender_slot(), (FOLDER/"work"/(who+"_"+state+".log")).open("w") as log:
                subprocess.run([paths.BLENDER,"-b","--python",str(Path(__file__).with_name("preview.py")),
                                "--",who,state], stdout=log,stderr=subprocess.STDOUT,check=True)
            print("Rendered",who,state,flush=True)
        images = []
        for who,title in [("original","CURRENT HD BUILDER"),("new","EREBOR MASTER BUILDER - DESIGN PREVIEW")]:
            path = FOLDER/"renders"/(who+"_"+state+".png")
            label = path.with_name("label_"+path.name)
            from sagekit.pipeline import Render
            subprocess.run(["magick",str(path),"-gravity","NorthWest","-font",Render.FONT,"-pointsize","23",
                            "-fill","white","-undercolor","#171b21cc","-annotate","+20+20"," "+title+" ",str(label)],check=True)
            images.append(str(label))
        subprocess.run(["magick",*images,"+append",str(FOLDER/"renders"/("compare_"+state+".png"))],check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    p.add_argument("--render", nargs="*", choices=("portrait","rts","run","work","water","death"))
    a = p.parse_args()
    if not a.check:
        from .design import design
        (FOLDER/"work").mkdir(parents=True,exist_ok=True)
        w, sk = prepare()
        meshes = design(w,sk)
        (FOLDER/"work/duporter_skn.w3d").write_bytes(WM.replace_meshes(w.data,{n:m.chunk() for n,m in meshes.items()}))
        paint()
        paint_mask()
    check()
    if a.render is not None:
        previews(a.render or ["portrait","rts","run","work","water","death"])


if __name__ == "__main__":
    main()
