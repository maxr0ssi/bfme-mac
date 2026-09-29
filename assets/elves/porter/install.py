"""Stage/install the reviewed Elven builder alone; --revert restores only its scoped snapshot."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from .unit import EXPECTED, FOLDER, check
from sagekit import paths
from sagekit.formats.assetcache import AssetCache
from sagekit.formats.big import Archive, pack
from sagekit.formats.textures import compiled_path
from sagekit.formats.w3d import W3DFile
from sagekit.game import Install
from sagekit.install import apply, cache_records, read, revert_faction
from sagekit.pipeline import game_running

ARCHIVE = "!!!!!!!!!!!!sagekit-elf-builder.big"
MODEL = "euporter_skn.w3d"
INI = "data\\ini\\housecolor.ini"
MAPPING = b"\r\nHouseColor\r\n\tBaseTexture = EUCrafts.tga\r\n\tHouseTexture = HC_EUCrafts.tga\r\nEnd\r\n"


def prepare():
    check()
    g=Install()
    active=Install(pristine=False)
    dest=Path(paths.GAMEDIRS["rotwk"])/ARCHIVE
    receipt=FOLDER/"_install/receipt.json"
    owned=False
    if dest.exists():
        if not receipt.exists():raise ValueError("Builder archive exists without a scoped receipt")
        entry=next((e for e in json.loads(receipt.read_text()) if e["path"]==str(dest)),None)
        if not entry or hashlib.sha256(dest.read_bytes()).hexdigest()!=entry["after"]:
            raise ValueError("Existing builder archive changed after installation")
        owned=True
    for name,digest in EXPECTED.items():
        member=g.model_path(name)
        if owned and name=="euporter_skn":
            if Path(active.owner(member).path)!=dest:raise ValueError("Another pack overrides the builder")
        elif hashlib.sha256(active.read(member)).hexdigest()!=digest:
            raise ValueError("Active builder model/rig changed: "+name)
    for member,digest in json.loads((FOLDER/"sources.json").read_text()).items():
        if owned and member==g.model_path("euporter_skn"):continue
        if hashlib.sha256(active.read(member)).hexdigest()!=digest:
            raise ValueError("Active source changed since the review build: "+member)
    for name in ("eucrafts.tga","hc_eucrafts.tga"):
        for ext in (".dds",".tga"):
            owner=active.owner(compiled_path(name,ext))
            if owner and (not owned or Path(owner.path)!=dest):
                raise ValueError("Private texture name is already occupied: "+name)
        if not owned:
            for directory in paths.GAMEDIRS.values():
                if AssetCache(str(Path(directory)/"asset.dat")).has_texture(name):
                    raise ValueError("Private texture is already registered: "+name)
    model="euporter_skn.w3d"
    original=W3DFile(str(FOLDER/"src"/model))
    new=W3DFile(str(FOLDER/"work"/model))
    live=Path(g.asset_cache(model))
    cache=AssetCache(str(live))
    changed={(model,(m.container+"."+m.name).lower()) for n,m in new.meshes.items()
             if original.meshes[n].textures != m.textures}
    assets={model,"eucrafts.tga","hc_eucrafts.tga"}
    untouched=cache_records(cache,assets,changed)
    cache.patch_model(str(FOLDER/"work"/model),model)
    cache.add_texture("hc_eucrafts.tga","hc_euworker.tga")
    for n,m in new.meshes.items():
        for old,texture in zip(original.meshes[n].textures,m.textures):
            if old.lower()!=texture.lower():
                cache.add_texture(texture,old,model,m.container+"."+m.name)
                assert texture.lower() in [x.lower() for x in cache.dependencies(model,m.container+"."+m.name)]
    assert not cache.stale_entries(str(FOLDER/"work"/model),model)
    assert cache_records(cache,assets,changed)==untouched
    # Preserve the active mappings, including any independently installed faction/unit art.
    member="data\\ini\\housecolor.ini"
    ini=active.read(member)
    blocks=re.findall(rb"(?ims)^HouseColor\s*\r?\n.*?^End[^\r\n]*",ini)
    matching=[b for b in blocks if re.search(rb"(?im)^\s*BaseTexture\s*=\s*eucrafts\.tga\s*$",b)]
    if matching:
        if not owned or len(matching)!=1 or not re.search(rb"(?im)^\s*HouseTexture\s*=\s*hc_eucrafts\.tga\s*$",matching[0]):
            raise ValueError("Conflicting existing Elven craftsman house-colour mapping")
    else:
        ini+=MAPPING
    # Earlier packs win. Do not report a successful install whose new mapping is shadowed.
    owner=Path(active.owner(member).path)
    folders=[Path(paths.GAMEDIRS[n]) for n in paths.SEARCH_ORDER[active.game]]
    if ((folders.index(owner.parent),owner.name.lower()) <
            (folders.index(dest.parent),dest.name.lower()) and active.read(member)!=ini):
        raise ValueError("An earlier pack owns housecolor.ini; compose its builder mappings first")
    files={g.model_path("euporter_skn"):new.data,
           compiled_path("eucrafts.tga",".dds"):(FOLDER/"work/eucrafts.dds").read_bytes(),
           compiled_path("hc_eucrafts.tga",".tga"):(FOLDER/"work/hc_eucrafts.tga").read_bytes(),
           member:ini}
    return files,{live:cache.data}


def release():
    """The builder for sagekit/pack.py, staged with --check: (archive, {game: [cache op]} as prepare()
    applies them, {INI: the lines added to EA's}, [folders of the EA files it was made from])."""
    g=Install()
    original,new=W3DFile(str(FOLDER/"src"/MODEL)),W3DFile(str(FOLDER/"work"/MODEL))
    ops=[("patch",MODEL),("texture","hc_eucrafts.tga","hc_euworker.tga",None,None)]
    ops+=[("texture",texture,old,MODEL,m.container+"."+m.name) for n,m in new.meshes.items()
          for old,texture in zip(original.meshes[n].textures,m.textures) if old.lower()!=texture.lower()]
    staged=Archive(str(FOLDER/"_install"/ARCHIVE))
    work={g.model_path("euporter_skn"):MODEL,compiled_path("eucrafts.tga",".dds"):"eucrafts.dds",
          compiled_path("hc_eucrafts.tga",".tga"):"hc_eucrafts.tga"}
    if any(staged.read(m)!=(FOLDER/"work"/f).read_bytes() for m,f in work.items()):
        raise SystemExit("The staged builder is not the reviewed build: stage it again (--check)")
    game=next(k for k,d in paths.GAMEDIRS.items() if Path(d)==Path(g.asset_cache(MODEL)).parent)
    return FOLDER/"_install"/ARCHIVE,{game:ops},{INI:MAPPING},[FOLDER/"src"]


def install(check_only=False):
    if game_running():raise SystemExit("Close the game before staging/installing.")
    dest=Path(paths.GAMEDIRS["rotwk"])/ARCHIVE
    expected={Path(d)/"asset.dat":read(Path(d)/"asset.dat") for d in paths.GAMEDIRS.values()}
    expected[dest]=read(dest)
    files,updates=prepare()
    stage=FOLDER/"_install"
    stage.mkdir(parents=True,exist_ok=True)
    archive=stage/ARCHIVE
    pack(sorted(files.items()),str(archive))
    updates[dest]=archive.read_bytes()
    for path,data in updates.items():
        if path.name=="asset.dat":(stage/(path.parent.name+"-asset.dat")).write_bytes(data)
    if check_only:
        print("Staged Elven builder and private player-colour mask. Unrelated cache records preserved. Nothing installed.")
        return
    if game_running():raise SystemExit("Game started during staging; nothing installed.")
    apply(updates,stage/"receipt.json",expected)
    print("Installed reviewed Elven builder only; scoped backups saved.")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group()
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--revert",action="store_true")
    a=p.parse_args()
    if a.revert:revert_faction("elves/porter")
    else:install(a.check)


if __name__=="__main__":main()
