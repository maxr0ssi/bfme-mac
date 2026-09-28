"""Selectable Elven craftsman review build. No installation: use the separate reviewed installer."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from assets.dwarves.porter.unit import Mesh as BaseMesh
from assets.elves.style import PALETTE
from sagekit import paths
from sagekit.formats import w3dmesh as WM, w3dpose as P
from sagekit.formats.textures import compiled_path, write_dds
from sagekit.formats.w3d import MESH, W3DFile, rename_textures
from sagekit.game import Install

FOLDER = Path(paths.BUILD)/"elves/porter"
ANIMS = ("idla", "idlb", "runa", "wlka", "fira", "diea", "dieb")
EXPECTED = {"euporter_skn": "aa03bb943f1c2de458b2adac765b71ef237fc0086bd22bb5cfae24c11fba869b",
            "guporter_skl": "cb8a6fa38469fd95ac1c791843a75c013fdec5684503b4711b0485a4eee5e9ec"}
NAMES = {"euworker.tga": "eucrafts.tga", "guporter_cart.tga": "eucrafts.tga",
         "guporter_build.tga": "eucrafts.tga"}
SWATCHES = [("wood",.65),("wood",.47),("trim",.64),("gold",.67),
            ("cloth",.55),("wood",.22),("stone",.65),("stone",.86),
            ("trim",.84),("tiles",.4),("gold",.83),("stone",.5),
            ("wood",.32),("crystal",.68),("stone",.74),("cloth",.3)]


class Mesh(BaseMesh):
    """Reuse the proven rig-bound primitives and affine atlas layout, with Elven texture names."""
    def chunk(self):
        m = self.original
        raw = WM.build_mesh(m.bytes, {0:WM.Source(m.bytes)}, m.name, m.container,
                            self.verts, self.tris, True, self.skeleton.rest)
        # The existing writer preserves chunk sizes. Pad the shorter C-string aliases
        # with NUL bytes rather than shrinking legacy texture-name chunks.
        return rename_textures(raw, [(None,k,v.ljust(len(k),"\0")) for k,v in NAMES.items()], m.name)


def prepare():
    src = FOLDER/"src"
    src.mkdir(parents=True,exist_ok=True)
    g, hashes = Install(), {}
    for n in tuple(EXPECTED)+tuple("guporter_"+a for a in ANIMS):
        member = g.model_path(n)
        data = g.read(member)
        digest = hashlib.sha256(data).hexdigest()
        if n in EXPECTED and digest != EXPECTED[n]:
            raise ValueError("Unsupported source model/rig: "+n)
        (src/(n+".w3d")).write_bytes(data)
        hashes[member] = digest
    w = W3DFile(str(src/"euporter_skn.w3d"))
    textures = {}
    for name in {t.lower() for m in w.meshes.values() for t in m.textures}:
        member = compiled_path(name,".dds")
        data = g.read(member)
        dest = src/(name[:-4]+".dds")
        dest.write_bytes(data)
        textures[name] = str(dest)
        hashes[member] = hashlib.sha256(data).hexdigest()
    member = compiled_path("HC_EUWorker.tga",".tga")
    data = g.read(member)
    (src/"hc_euworker.tga").write_bytes(data)
    hashes[member] = hashlib.sha256(data).hexdigest()
    (FOLDER/"textures.json").write_text(json.dumps(textures,indent=2))
    (FOLDER/"sources.json").write_text(json.dumps(hashes,indent=2))
    return w,P.Skeleton((src/"guporter_skl.w3d").read_bytes())


def colour(material,value):
    value = max(0,min(1,value))
    ramp = PALETTE.ramps[material]
    for (a,ca),(b,cb) in zip(ramp,ramp[1:]):
        if a <= value <= b:
            t = (value-a)/(b-a)
            return bytes(round(255*(x*(1-t)+y*t)) for x,y in zip(ca,cb))
    raise ValueError(value)


def magick(*args):
    subprocess.run(["magick",*map(str,args)],check=True)


def paint():
    src, work = FOLDER/"src",FOLDER/"work"
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
    write_dds(str(work/"eucrafts.png"),str(work/"eucrafts.dds"))
    # House masks use alpha to select coloured regions; transparent white is neutral.
    mask = subprocess.check_output(["magick",str(src/"hc_euworker.tga"),"-depth","8","rgba:-"])
    # ImageMagick's tile compositing clears RGB under alpha zero. Repeat raw rows so
    # the game's neutral transparent-white pixels remain byte-for-byte identical.
    (work/"mask.rgba").write_bytes(b"".join(mask[(y%256)*1024:(y%256+1)*1024]*4+
                                          bytes((255,255,255,0))*1024 for y in range(1024)))
    magick("-size","2048x1024","-depth","8","rgba:"+str(work/"mask.rgba"),work/"hc_eucrafts.tga")
    textures = json.loads((FOLDER/"textures.json").read_text())
    textures["eucrafts.tga"] = str(work/"eucrafts.dds")
    (work/"textures.json").write_text(json.dumps(textures,indent=2))


def check():
    src,work = FOLDER/"src",FOLDER/"work"
    old,new = [W3DFile(str(p/"euporter_skn.w3d")) for p in (src,work)]
    sk = P.Skeleton((src/"guporter_skl.w3d").read_bytes())
    assert [b for t,b in old.top() if t!=MESH] == [b for t,b in new.top() if t!=MESH]
    assert old.meshes.keys() == new.meshes.keys()
    for n in ("BUCKET","HAMMER"):
        assert old.meshes[n].bytes == new.meshes[n].bytes,n
    a,b = old.meshes["ELF"],new.meshes["ELF"]
    assert a.verts == b.verts[:len(a.verts)]
    assert P.influences(a.bytes) == P.influences(b.bytes)[:len(a.verts)]
    for n,m in new.meshes.items():
        assert all(math.isfinite(x) for v in m.verts+m.uv for x in v),n
        assert len(m.uv)==len(m.verts)==len(m.normals),n
        assert all(0<=i<len(m.verts) for t in m.tris for i in t),n
        if m.skinned:
            bones=P.influences(m.bytes)
            assert len(bones)==len(m.verts) and all(0<=b<len(sk.pivots) for b in bones),n
            if n in ("CART_MESH","CARTSUPPLIES"):
                assert set(bones)==set(P.influences(old.meshes[n].bytes)),n
        if n in ("ELF","CART_MESH","CARTSUPPLIES"):
            assert all(0<=v<=1 for uv in m.uv for v in uv),n
            assert all(t.lower()=="eucrafts.tga" for t in m.textures),n
    for n,digest in EXPECTED.items():
        assert hashlib.sha256((src/(n+".w3d")).read_bytes()).hexdigest()==digest
    for a in ANIMS:
        assert P.Animation((src/("guporter_"+a+".w3d")).read_bytes()).hierarchy.upper()==sk.name.upper()
    mask = subprocess.check_output(["magick",str(work/"hc_eucrafts.tga"),"-depth","8","rgba:-"])
    source_mask = subprocess.check_output(["magick",str(src/"hc_euworker.tga"),"-depth","8","rgba:-"])
    assert len(mask)==2048*1024*4 and len(source_mask)==256*256*4
    for y in range(1024):
        row=mask[y*8192:(y+1)*8192]
        assert row[:4096]==source_mask[(y%256)*1024:(y%256+1)*1024]*4
        assert row[4096:]==bytes((255,255,255,0))*1024
    report = {"source_triangles":sum(len(m.tris) for m in old.meshes.values()),
              "new_triangles":sum(len(m.tris) for m in new.meshes.values()),
              "source_vertices":sum(len(m.verts) for m in old.meshes.values()),
              "new_vertices":sum(len(m.verts) for m in new.meshes.values()),
              "model_sha256":hashlib.sha256(new.data).hexdigest()}
    (work/"checks.json").write_text(json.dumps(report,indent=2))
    print("PASS: original anatomy, rig, HLOD, tools; finite geometry, valid UVs and bone bindings.")
    return report


def previews(states):
    from sagekit.pipeline import blender_slot,game_running,Render
    if game_running():raise SystemExit("Close the game before rendering previews.")
    for state in states:
        for who in ("original","new"):
            with blender_slot(),(FOLDER/"work"/(who+"_"+state+".log")).open("w") as log:
                subprocess.run([paths.BLENDER,"-b","--python",str(Path(__file__).with_name("preview.py")),
                                "--",who,state],stdout=log,stderr=subprocess.STDOUT,check=True)
            print("Rendered",who,state,flush=True)
        images=[]
        for who,label in [("original","ORIGINAL ELVEN BUILDER"),("new","ELVEN MASTER CRAFTSMAN - REVIEW")]:
            image=FOLDER/"renders"/(who+"_"+state+".png")
            labelled=image.with_name("label_"+image.name)
            magick(image,"-gravity","NorthWest","-font",Render.FONT,"-pointsize","23","-fill","white",
                    "-undercolor","#17251dcc","-annotate","+20+20"," "+label+" ",labelled)
            images.append(labelled)
        magick(*images,"+append",FOLDER/"renders"/("compare_"+state+".png"))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check",action="store_true")
    p.add_argument("--render",nargs="*",choices=("portrait","rts","run","walk","water","death","fall","idle"))
    a=p.parse_args()
    if not a.check:
        from .design import design
        (FOLDER/"work").mkdir(parents=True,exist_ok=True)
        w,sk=prepare()
        meshes=design(w,sk)
        (FOLDER/"work/euporter_skn.w3d").write_bytes(WM.replace_meshes(w.data,{n:m.chunk() for n,m in meshes.items()}))
        paint()
    check()
    if a.render is not None:previews(a.render or ["portrait","rts","run","water","death","fall","idle"])


if __name__=="__main__":main()
