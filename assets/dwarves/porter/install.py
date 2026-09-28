"""Stage/install the reviewed builder and player colours; --revert restores its scoped backup."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from sagekit import paths
from sagekit.formats.assetcache import AssetCache
from sagekit.formats.big import Archive, pack
from sagekit.formats.textures import compiled_path
from sagekit.formats.w3d import W3DFile
from sagekit.game import Install
from sagekit.install import apply, cache_records, read, revert_faction
from sagekit.pipeline import game_running
from .unit import EXPECTED, FOLDER, NAMES, check, paint_mask

MODEL = "duporter_skn.w3d"
ARCHIVE = "!!!!!!!!!!!!sagekit-dwarf-builder.big"
STAGE = FOLDER/"_install"
LIVE = Path(paths.GAMEDIRS["rotwk"])
RECEIPT = STAGE/"receipt.json"
LEGACY = FOLDER/"install/receipt.json"
MASK = "hc_ducrafts.tga"
INI = "data\\ini\\housecolor.ini"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def owned_archive(dest):
    """Accept our scoped or legacy archive without resetting a subsequently edited cache."""
    if not dest.exists():
        if RECEIPT.exists() or LEGACY.exists():
            raise ValueError("Builder receipt exists but archive is missing")
        return False
    if RECEIPT.exists():
        entries = json.loads(RECEIPT.read_text())
        entry = next((e for e in entries if e["path"] == str(dest)),None)
        digest = entry["after"] if entry else None
    elif LEGACY.exists():
        digest = json.loads(LEGACY.read_text())["archive"]
    else:
        raise ValueError("Builder archive exists without a receipt")
    if sha(dest.read_bytes()) != digest:
        raise ValueError("Builder archive changed after installation")
    return True


def housecolour(ini, owned):
    blocks = re.findall(rb"(?ims)^HouseColor\s*\r?\n.*?^End[^\r\n]*",ini)
    for name in NAMES.values():
        pattern = rb"(?im)^\s*BaseTexture\s*=\s*"+re.escape(name.encode())+rb"\s*$"
        matching = [b for b in blocks if re.search(pattern,b)]
        if matching:
            if not owned or len(matching)!=1 or not re.search(
                    rb"(?im)^\s*HouseTexture\s*=\s*hc_ducrafts\.tga\s*$",matching[0]):
                raise ValueError("Conflicting builder player-colour mapping: "+name)
        else:
            ini += ("\r\nHouseColor\r\n\tBaseTexture = "+name+
                    "\r\n\tHouseTexture = "+MASK+"\r\nEnd\r\n").encode()
    return ini


def prepare():
    paint_mask()
    check()
    active = Install(pristine=False)
    owned = owned_archive(LIVE/ARCHIVE)
    model = FOLDER/"work"/MODEL
    files = {active.model_path("duporter_skn"):model.read_bytes()}
    files.update({compiled_path(n,".dds"):(FOLDER/"work"/(n[:-4]+".dds")).read_bytes()
                  for n in NAMES.values()})
    if owned:
        installed = Archive(str(LIVE/ARCHIVE))
        # The repair must not alter any reviewed geometry or diffuse pixel bytes.
        assert all(installed.read(n)==data for n,data in files.items()), "Reviewed builder art changed"
        assert Path(active.owner(active.model_path("duporter_skn")).path)==LIVE/ARCHIVE
    else:
        assert sha(active.read(active.model_path("duporter_skn")))==EXPECTED["skn"]
    assert sha(active.read(active.model_path("duporter_skl")))==EXPECTED["skl"]
    assert active.read(compiled_path("hc_duporter.tga",".tga"))==(FOLDER/"src/hc_duporter.tga").read_bytes()
    for name in (*NAMES.values(),MASK):
        for ext in (".dds",".tga"):
            owner = active.owner(compiled_path(name,ext))
            if owner and (not owned or Path(owner.path)!=LIVE/ARCHIVE):
                raise ValueError("Private texture already occupied: "+name)
        if not owned or name==MASK and compiled_path(MASK,".tga") not in Archive(str(LIVE/ARCHIVE)).index():
            for directory in paths.GAMEDIRS.values():
                assert not AssetCache(str(Path(directory)/"asset.dat")).has_texture(name), name
    original = W3DFile(str(FOLDER/"src"/MODEL))
    new = W3DFile(str(model))
    cache = AssetCache(str(LIVE/"asset.dat"))
    changed = {(MODEL,(m.container+"."+m.name).lower()) for n,m in new.meshes.items()
               if original.meshes[n].textures!=m.textures}
    assets = {MODEL,MASK,*NAMES.values()}
    untouched = cache_records(cache,assets,changed)
    cache.patch_model(str(model))
    cache.add_texture(MASK,"hc_duporter.tga")
    for n,m in new.meshes.items():
        for old,texture in zip(original.meshes[n].textures,m.textures):
            if old.lower()!=texture.lower():
                cache.add_texture(texture,old,MODEL,m.container+"."+m.name)
                assert texture.lower() in [d.lower() for d in cache.dependencies(MODEL,m.container+"."+m.name)]
    assert not cache.stale_entries(str(model))
    assert cache_records(cache,assets,changed)==untouched, "Unrelated cache records changed"
    files[compiled_path(MASK,".tga")] = (FOLDER/"work"/MASK).read_bytes()
    files[INI] = housecolour(active.read(INI),owned)
    owner = Path(active.owner(INI).path)
    if owner.parent==LIVE and owner.name.lower()<ARCHIVE.lower():
        raise ValueError("Higher-priority housecolor.ini pack would hide the builder mapping")
    return files,{LIVE/"asset.dat":cache.data}


def install(check_only=False):
    if game_running():raise SystemExit("Close the game before staging/installing.")
    expected = {Path(d)/"asset.dat":read(Path(d)/"asset.dat") for d in paths.GAMEDIRS.values()}
    expected[LIVE/ARCHIVE] = read(LIVE/ARCHIVE)
    files,updates = prepare()
    STAGE.mkdir(parents=True,exist_ok=True)
    archive = STAGE/ARCHIVE
    pack(sorted(files.items()),str(archive))
    assert all(Archive(str(archive)).read(n)==data for n,data in files.items())
    updates[LIVE/ARCHIVE] = archive.read_bytes()
    (STAGE/"asset.dat.new").write_bytes(updates[LIVE/"asset.dat"])
    if check_only:
        print("Staged builder player colours; reviewed model/diffuses and unrelated cache records preserved. Nothing installed.")
        return
    if game_running():raise SystemExit("Game started during staging; nothing installed.")
    apply(updates,RECEIPT,expected)
    assert Install(pristine=False).read(INI)==files[INI], "Installed house colours are shadowed"
    print("Installed Dwarven builder player colours; scoped backups saved.")


def revert():
    if RECEIPT.exists():
        return revert_faction("dwarves/porter")
    if game_running():raise SystemExit("Close the game before reverting.")
    if not LEGACY.exists():raise SystemExit("No builder receipt; nothing changed.")
    receipt = json.loads(LEGACY.read_text())
    owned_archive(LIVE/ARCHIVE)
    before = read(LIVE/"asset.dat")
    assert sha(before)==receipt["after"], "Cache changed since legacy installation; refusing to overwrite later art"
    backup = (LEGACY.parent/"asset.dat.bak").read_bytes()
    assert sha(backup)==receipt["before"], "Legacy backup changed"
    apply({LIVE/"asset.dat":backup,LIVE/ARCHIVE:None},STAGE/"legacy-revert.json",
          {LIVE/"asset.dat":before,LIVE/ARCHIVE:read(LIVE/ARCHIVE)})
    LEGACY.unlink()
    print("Legacy builder removed; guarded backup restored.")


def selfcheck():
    """Exercise composed INIs, both receipt formats and tamper rejection without live writes."""
    import tempfile
    from unittest.mock import patch
    base = b"HouseColor\r\n BaseTexture = eucrafts.tga\r\n HouseTexture = hc_eucrafts.tga\r\nEnd\r\n"
    result = housecolour(base,False)
    assert result.startswith(base) and housecolour(result,True)==result
    for wrong in (result, result.replace(b"hc_ducrafts.tga",b"wrong.tga")):
        try:
            housecolour(wrong,False if wrong==result else True)
        except ValueError:
            pass
        else:
            raise AssertionError("Conflicting mapping accepted")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dest, legacy, receipt = root/ARCHIVE,root/"legacy.json",root/"receipt.json"
        dest.write_bytes(b"reviewed archive")
        legacy.write_text(json.dumps({"archive":sha(dest.read_bytes())}))
        with patch(__name__+".LEGACY",legacy),patch(__name__+".RECEIPT",receipt):
            assert owned_archive(dest)
            receipt.write_text(json.dumps([{"path":str(dest),"after":sha(dest.read_bytes())}]))
            assert owned_archive(dest)
            dest.write_bytes(b"changed archive")
            try:
                owned_archive(dest)
            except ValueError:
                pass
            else:
                raise AssertionError("Modified archive accepted")
    print("PASS: preserve existing mappings; reject conflicting aliases and modified receipts' archives")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group()
    group.add_argument("--check",action="store_true")
    group.add_argument("--revert",action="store_true")
    group.add_argument("--selfcheck",action="store_true")
    args = p.parse_args()
    if args.selfcheck:selfcheck()
    elif args.revert:revert()
    else:install(args.check)


if __name__=="__main__":main()
