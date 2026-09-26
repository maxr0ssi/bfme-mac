"""House colour: the part of a faction's look that follows the player's colour.

BFME2 tints meshes named HC_* in a model drawn with OkToChangeModelColor (EA's small house-colour
banners: DBHCFortress, DBHCMine...). A building's geometry step takes its cloth faces (the
Building.house_tags regions) out of the body into work/house_cloth.json; this step adds every
building's cloth to the house-colour model it is shown with (several buildings may share one: the
fortress and its upgrades all feed DBHCFortress), splices the result into EA's file and records
what install must do: the model's cache record, and MultiPlayerOnly = No on its Draw modules (EA
shows house banners in multiplayer only; ours are part of the building), and no model in the states
whose lifecycle model cuts or moves the faces the banners hang on (sagekit/lifecycle.py).

A house model another faction draws too (Arnor draws NBHCElvnBarx and EBHCMalTree beside the Elven
barracks and mallorn) is never changed: Building.own_house_copy names an own copy ("copy_of"), which
ships EA's file renamed with our cloth, and only this faction's Draw modules show it (the own_model
pattern, sagekit/owncopy.py).

    build/assets/<faction>/_house/  src/ EA's models, work/ exports, out/ what ships, house.json
"""
import json
import os
import subprocess
import time

from . import paths
from .formats.w3d import W3DFile, fix, rename_model, splice_mesh
from .lifecycle import house_ops
from .game import Install
from .pipeline import blender_slot, game_running
from .registry import building_ids, load
from .workspace import Workspace

# EA's Dwarven_House_Color_Banner.tga (and its kind): the folded cloth inside the frame, in Blender
# UV space (u0, v0, u1, v1)
CLOTH_RECT = (0.48, 0.38, 0.90, 0.86)
# EA's own little house flag in each model: dropped, so only our banners carry the player's colour
# (the user's choice: the flag stood in front of our banners, e.g. in the barracks' yard)
KEEP_EA_FLAG = False
RUN_PY = os.path.join(paths.REPO, "sagekit", "blender", "house.py")


def root(faction):
    return os.path.join(paths.BUILD, faction, "_house")


def groups(faction):
    """{model (lower): {"model", "mesh", "draws", "cloth": [json paths]}} over the faction's buildings."""
    out = {}
    for bid in building_ids():
        if not bid.startswith(faction + "/"):
            continue
        ws = Workspace(load(bid))
        if not ws.house or not os.path.exists(ws.house_cloth) or not json.load(open(ws.house_cloth)):
            continue
        g = out.setdefault(ws.house["model"].lower(), dict(ws.house, draws=[], cloth=[]))
        g["cloth"].append(ws.house_cloth)
        g["draws"] += [d for d in ws.house["draws"] if d not in g["draws"]]
        g.setdefault("buildings", []).append(bid)
    return out


def build(faction, force=False, log=print):
    install, r = Install(), root(faction)
    for d in ("src", "work", "out"):
        os.makedirs(os.path.join(r, d), exist_ok=True)
    record = {"models": [], "ini": {}}
    for key, g in sorted(groups(faction).items()):
        member = install.model_path(g["model"])
        ea = g.get("template") or g.get("copy_of")         # a model of our own: EA's template, or EA's
        if ea:                                              # shared model (own copy), renamed; its flag
            orig = rename_model(install.read(install.model_path(ea)), ea, g["model"])      # replaced by our cloth
        else:
            orig = install.read(member)
        src = os.path.join(r, "src", key + ".w3d")
        with open(src, "wb") as fh:
            fh.write(orig)
        skl = W3DFile(orig).skeleton()          # a skinned house model (EBHCStable): its skeleton
        if skl:                                 # file goes next to it, where the importer looks
            with open(os.path.join(r, "src", skl), "wb") as fh:
                fh.write(install.read(install.model_path(skl[:-4])))
        export =os.path.join(r, "work", key + ".w3d")      # named like the original: the exporter
        while game_running() and not force:                 # names its containers after the file
            time.sleep(10)
        with blender_slot():
            p = subprocess.run([paths.BLENDER, "-b", "--python", RUN_PY, "--", src, export, g["mesh"],
                                ",".join(map(str, CLOTH_RECT)),
                                "keep" if KEEP_EA_FLAG and not g.get("template") else "fresh"] + g["cloth"],
                               capture_output=True, text=True)
        with open(os.path.join(r, "work", key + ".log"), "w") as fh:
            fh.write(p.stdout + p.stderr)
        if "HOUSE OK" not in p.stdout or "Traceback" in p.stdout + p.stderr:
            raise SystemExit("house colour: Blender failed for %s - see %s" % (g["model"], fh.name))
        fixed, _ = fix(orig, open(export, "rb").read())
        mesh = W3DFile(fixed).meshes[g["mesh"]]
        out = splice_mesh(orig, g["mesh"], mesh.bytes, W3DFile(orig).meshes[g["mesh"]].container)
        if W3DFile(out).object_names() != W3DFile(orig).object_names():
            raise SystemExit("house colour: %s changed its object names" % g["model"])
        dest = os.path.join(r, "out", *member.split("\\"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(out)
        record["models"].append(member)
        for ini, obj, tag in g["draws"]:
            if g.get("template"):
                ops = [("draw", obj, tag, g["model"])]
            else:                   # an own copy: shown in place of EA's by this faction's modules only
                ops = [("model", obj, tag, g["copy_of"], g["model"])] if g.get("copy_of") else []
                ops.append(("field", obj, tag, "MultiPlayerOnly", "No"))
            record["ini"].setdefault(ini, []).extend(ops)
        for bid in g["buildings"]:          # not over rubble or a building site (sagekit/lifecycle.py)
            for ini, ops in house_ops(Workspace(load(bid)), g["draws"]).items():
                record["ini"].setdefault(ini, []).extend(op for op in ops if op not in record["ini"][ini])
        log("  %-16s %4d -> %4d triangles (cloth from %d building%s)" % (
            g["model"], len(W3DFile(orig).meshes[g["mesh"]].tris), len(mesh.tris), len(g["cloth"]),
            "" if len(g["cloth"]) == 1 else "s"))
    with open(os.path.join(r, "house.json"), "w") as fh:
        json.dump(record, fh, indent=1)
    return record


def shipped(faction):
    """(record, out dir) of the last build, or (None, None)."""
    p = os.path.join(root(faction), "house.json")
    return (json.load(open(p)), os.path.join(root(faction), "out")) if os.path.exists(p) else (None, None)
