"""Build isolated Dwarven troop art for review. Stages a package; has no installation action."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from sagekit import paths
from sagekit.formats import w3dmesh as WM, w3dpose as P
from sagekit.formats.assetcache import AssetCache
from sagekit.formats.big import Archive, pack
from sagekit.formats.textures import compiled_path
from sagekit.formats.w3d import (W3DFile, chunks, chunk_bytes, rename_model, rename_textures,
                                MESH, HIERARCHY, HLOD, HLOD_HEADER)
from sagekit.game import Install
from sagekit.pipeline import game_running
from . import catalog, infantry, siege, paint

FOLDER=Path(paths.BUILD)/"dwarves/troops/redesign"
ARCHIVE="!!!!!!!!!!!!!sagekit-dwarf-troops.big"
PREFIX="dt"
PAINT_MODULE="assets.dwarves.troops.paint"


def configure(folder, archive, prefix, roster, designer, painter, paint_module):
    """Configure this process for another faction using the same private-art pipeline."""
    global FOLDER, ARCHIVE, PREFIX, catalog, infantry, siege, paint, PAINT_MODULE
    from types import SimpleNamespace
    FOLDER,ARCHIVE,PREFIX=folder,archive,prefix
    catalog,infantry,paint=roster,designer,painter
    siege=SimpleNamespace(SUPPORTED_MODELS=())
    PAINT_MODULE=paint_module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def alias(name):
    return PREFIX+sha(name.lower().encode())[:4]+".tga"


def private_model(data, old, new):
    """Own the model/container while keeping the original hierarchy used by animation files."""
    renamed=W3DFile(rename_model(data,old,new)); original=W3DFile(data)
    out=[]
    for (tag,raw),(oldtag,source) in zip(renamed.top(),original.top()):
        assert tag==oldtag
        if tag==HIERARCHY:raw=source
        if tag==HLOD:
            raw=bytearray(raw)
            a=next(c for c in chunks(raw,8,len(raw)) if c[0]==HLOD_HEADER)[1]
            b=next(c for c in chunks(source,8,len(source)) if c[0]==HLOD_HEADER)[1]
            raw[a+32:a+48]=source[b+32:b+48]
            raw=bytes(raw)
        out.append(raw)
    return b"".join(out)


def prepare():
    if game_running():raise SystemExit("Close the game before building art.")
    g=Install(pristine=False)
    catalog.validate(g)
    src,work,out=[FOLDER/n for n in ("src","work","out")]
    for d in (src,work,out):d.mkdir(parents=True,exist_ok=True)
    prior=json.loads((FOLDER/"build.json").read_text()) if (FOLDER/"build.json").exists() else {}
    hashes,owners={},{}

    def extract(member):
        data=g.read(member);digest=sha(data)
        if member in prior.get("source_hashes",{}):
            assert prior["source_hashes"][member]==digest,"Reviewed source changed: "+member
        hashes[member]=digest;owners[member]=g.owner(member).path
        dest=src.joinpath(*member.split("\\"));dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
        return str(dest)

    models={};textures={};texture_names=set();geometry={}
    lod_parent={m:b for b,variants in catalog.LOD_MODELS.items() for m in variants}
    names={n:PREFIX+sha(n.encode())[:8] for n in catalog.MODELS if n not in lod_parent}
    for n,base in lod_parent.items():names[n]=names[base]+n[len(base):]
    assert len(set(names.values()))==len(names)
    for name,new in names.items():
        assert not g.has_model(new),"Private model name occupied: "+new
        assert not any(c.has_model(new+".w3d") for c in g.asset_caches().values())
        source=extract(g.model_path(name));w=W3DFile(source)
        skeleton=extract(g.model_path(w.skeleton()[:-4])) if w.skeleton() else source
        sk=P.Skeleton(Path(skeleton).read_bytes())
        changed={}
        if name in infantry.supported_modelnames:
            changed=infantry.design(w,sk,name)
        elif name in siege.SUPPORTED_MODELS:
            changed=siege.design(w,sk,name)
        data=WM.replace_meshes(w.data,changed) if changed else w.data
        neww=W3DFile(data)
        assert neww.skeleton()==w.skeleton()
        assert neww.meshes.keys()==w.meshes.keys()
        for n,m in w.meshes.items():
            result=neww.meshes[n]
            assert result.verts[:len(m.verts)]==m.verts,(name,n,'positions')
            assert result.uv[:len(m.uv)]==m.uv,(name,n,'UVs')
            assert result.tris[:len(m.tris)]==m.tris,(name,n,'faces')
            old_bones=P.influences(m.bytes)
            if old_bones:assert P.influences(result.bytes)[:len(old_bones)]==old_bones
            else:assert P.influences(result.bytes) is None
        path=work/(name+".w3d");path.write_bytes(data)
        models[name]=dict(alias=new,source=source,work=str(path),skeleton=skeleton)
        geometry[name]=dict(old_vertices=sum(len(m.verts) for m in w.meshes.values()),
            new_vertices=sum(len(m.verts) for m in neww.meshes.values()),
            old_triangles=sum(len(m.tris) for m in w.meshes.values()),
            new_triangles=sum(len(m.tris) for m in neww.meshes.values()),
            old_bytes=len(w.data),new_bytes=len(data),geometry_enhanced=bool(changed),
            lod_parent=lod_parent.get(name))
        texture_names|={t.lower() for m in w.meshes.values() for t in m.textures}
    for e in catalog.ROSTER:
        for v in e["variants"]:texture_names.update(v.get("textures",{}).values())
    texture_names.update(getattr(catalog,"EXTRA_TEXTURES",()))
    source_textures={}
    for name in sorted(texture_names):
        member=next((compiled_path(name,ext) for ext in (".dds",".tga")
                     if g.owner(compiled_path(name,ext))),None)
        assert member,name
        source_textures[name]=extract(member)
        if paint.eligible(name):
            new=alias(name)
            assert len(new)<=len(name),(name,new)
            assert not any(g.owner(compiled_path(new,ext)) for ext in (".dds",".tga")),new
            textures[name]=dict(alias=new,source=source_textures[name],output=str(work/(new[:-4]+".dds")))
    assert len({t['alias'] for t in textures.values()})==len(textures)
    animations=catalog.animation_inventory(g)
    for name in animations["files"]:extract(g.model_path(name))
    for member in catalog.SOURCE_MEMBERS:extract(member)
    ini=Path(extract("data\\ini\\housecolor.ini")).read_bytes()
    house={};shared_house={}
    for block in re.findall(rb"(?ims)^HouseColor\s*\r?\n.*?^End[^\r\n]*",ini):
        base=re.search(rb"(?im)^\s*BaseTexture\s*=\s*(\S+)",block)
        mask=re.search(rb"(?im)^\s*HouseTexture\s*=\s*(\S+)",block)
        if base and mask and base[1].decode().lower() in textures:
            name=base[1].decode().lower();old=mask[1].decode().lower()
            member=next((compiled_path(old,ext) for ext in (".tga",".dds") if g.owner(compiled_path(old,ext))),None)
            if old in getattr(catalog,"SHARED_HOUSE_TEXTURES",set()):
                assert not member,("Shared mask now has a compiled source; review mapping",old)
                assert any(c.has_texture(old) for c in g.asset_caches().values()),old
                shared_house[name]=old
                continue
            assert member,old
            house[name]=dict(alias="hc_"+textures[name]["alias"],source=extract(member),template=old)
    result=dict(models=models,textures=textures,source_textures=source_textures,house=house,shared_house=shared_house,
                source_hashes=hashes,source_owners=owners,animations=animations,geometry=geometry)
    (FOLDER/"build.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def package(data):
    g=Install(pristine=False);files={};out=FOLDER/"out"
    for name,item in data["models"].items():
        w=W3DFile(item["work"]);changed={}
        for key,m in w.meshes.items():
            renames=[(None,t,data["textures"][t.lower()]["alias"].ljust(len(t),"\0"))
                     for t in m.textures if t.lower() in data["textures"]]
            changed[key]=rename_textures(m.bytes,renames,key)
        raw=private_model(WM.replace_meshes(w.data,changed),name,item["alias"])
        assert W3DFile(raw).skeleton()==w.skeleton()
        files[g.model_path(item["alias"])]=raw
        for n,m in W3DFile(raw).meshes.items():
            assert m.verts==w.meshes[n].verts and m.uv==w.meshes[n].uv
    for item in data["textures"].values():files[compiled_path(item["alias"],".dds")]=Path(item["output"]).read_bytes()
    for item in data["house"].values():
        files[compiled_path(item["alias"],Path(item["source"]).suffix)]=Path(item["source"]).read_bytes()
    replacements={n:v["alias"] for n,v in data["models"].items()}
    replacements.update({n:v["alias"] for n,v in data["textures"].items()})

    def line_swap(match):
        return re.sub(r"[\w.]+",lambda m:replacements.get(m[0].lower(),m[0]),match[0])

    for member in catalog.INI_MEMBERS:
        original=g.read(member).decode("latin1")
        # Restrict substitutions to visual model/texture directives; animation/gameplay stays exact.
        text=re.sub(r"(?im)^\s*(?:Model|Texture|RandomTexture|UpgradeTexture)\s*=\s*[^\r\n;]*",line_swap,original)
        if hasattr(catalog,"scoped_ini"):
            text=catalog.scoped_ini(member,original,replacements)
        files[member]=text.encode("latin1")
    ini=g.read("data\\ini\\housecolor.ini")
    for name,item in sorted(data["house"].items()):
        ini+=("\r\nHouseColor\r\n BaseTexture = "+data["textures"][name]["alias"]+
              "\r\n HouseTexture = "+item["alias"]+"\r\nEnd\r\n").encode()
    for name,mask in sorted(data.get("shared_house",{}).items()):
        ini+=("\r\nHouseColor\r\n BaseTexture = "+data["textures"][name]["alias"]+
              "\r\n HouseTexture = "+mask+"\r\nEnd\r\n").encode()
    files["data\\ini\\housecolor.ini"]=ini
    for member,raw in files.items():
        dest=out.joinpath(*member.split("\\"));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    stage=FOLDER/"staged";stage.mkdir(exist_ok=True)
    pack(sorted(files.items()),str(stage/ARCHIVE))
    archive=Archive(str(stage/ARCHIVE))
    assert set(archive.index())==set(files)
    assert all(archive.read(n)==v for n,v in files.items())
    caches={Path(d)/"asset.dat":AssetCache(str(Path(d)/"asset.dat")) for d in paths.GAMEDIRS.values()}
    for name,item in data["textures"].items():
        cache=next(c for c in caches.values() if c.has_texture(name));cache.add_texture(item["alias"],name)
    for item in data["house"].values():
        cache=next(c for c in caches.values() if c.has_texture(item["template"]));cache.add_texture(item["alias"],item["template"])
    for live,cache in caches.items():(stage/(live.parent.name+"-asset.dat")).write_bytes(cache.data)
    (FOLDER/"checks.json").write_text(json.dumps(dict(status="PASS",models=len(data["models"]),
        textures=len(data["textures"]),house_masks=len(data["house"]),archive_members=len(files),
        original_geometry_preserved=True,original_animations_shipped=False,installed=False),indent=2)+"\n")
    print("PASS: isolated models, original geometry/rig/UVs, private sheets/masks, archive read-back. Staged only.")


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--package-only",action="store_true");a=p.parse_args()
    if a.package_only:data=json.loads((FOLDER/"build.json").read_text())
    else:
        data=prepare()
        subprocess.run([paths.blender_python(),"-B","-m",PAINT_MODULE,str(FOLDER/"build.json")],check=True)
    package(data)


if __name__=="__main__":main()
