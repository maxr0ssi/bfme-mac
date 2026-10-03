#!/usr/bin/env python3
"""A class's overview sheet: EA's parts beside ours at the same zoom (head shots on the creation-
screen model), the class's kits full length, and the in-game models at the RTS camera; the hero's
three colours previewed through the masks. One Blender process (the shared slot), lean samples.

    python3 -m assets.cah.kit.render <class> [--samples N]   -> build/assets/cah/<class>/renders/overview.png

The class's design.py gives RENDER = {"body": {model: body mesh or [meshes]}, "head_model": model, "game_model":
model, "ea_heads": [EA meshes], "kits": [(label, [meshes], ea?)], "colours": [(r, g, b)] * 3,
"anims": {skeleton: the idle animation it is posed in}}.
"""
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

from sagekit import paths
from sagekit.formats.textures import sheet_member
from sagekit.formats.w3d import W3DFile
from sagekit.game import Install

from .models import folder, parts_of

SCRIPT = Path(paths.REPO) / "sagekit" / "blender" / "cah_pose.py"


def textures(spec, models):
    """{texture: local file} for every sheet the shown models draw (EA's extracted, ours built)
    and {texture: mask} from EA's housecolor.ini and the class's masks."""
    d, src, work = folder(spec)
    tex_dir = src / "tex"
    tex_dir.mkdir(parents=True, exist_ok=True)
    g = Install()
    out, masks = {}, {}
    hc = {b.lower(): h for b, h in re.findall(r"BaseTexture\s*=\s*(\S+)\s*\n\s*HouseTexture\s*=\s*(\S+)",
                                               g.read("data\\ini\\housecolor.ini").decode("latin-1"))}
    names = {t.lower() for m in models for mesh in W3DFile(str(m)).meshes.values() for t in mesh.textures}
    for sheet in spec.SHEETS.values():
        out[sheet.lower()] = str(work / (sheet.lower()[:-4] + ".dds"))
        masks[sheet.lower()] = str(work / spec.MASKS[sheet].lower())
    for t in sorted(names - set(out)):
        member = sheet_member(g, t)
        if member:
            dst = tex_dir / member.split("\\")[-1]
            if not dst.exists():
                dst.write_bytes(g.read(member))
            out[t] = str(dst)
        if t in hc and sheet_member(g, hc[t]):
            m = sheet_member(g, hc[t])
            dst = tex_dir / m.split("\\")[-1]
            if not dst.exists():
                dst.write_bytes(g.read(m))
            masks[t] = str(dst)
    return out, masks


def _body(R, model):
    """The meshes always shown: R["body"][model], one mesh or a list (the wizards' body and head)."""
    b = R["body"][model]
    return list(b) if isinstance(b, (list, tuple)) else [b]


def jobs(spec, samples):
    R = spec.RENDER
    d, src, work = folder(spec)
    shipped = {ea.lower(): work / (ours.lower() + ".w3d") for ea, ours in spec.MODELS.items()}
    ea_path = lambda m: src / (m + ".w3d")
    tex, masks = textures(spec, list(shipped.values()) + [ea_path(m) for m in shipped])
    out_dir = d / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)

    def job(name, model, ea, idle, show, label, **kw):
        skel = spec.SKELETONS[model]
        return dict(name=name, label=label, model=str(ea_path(model) if ea else shipped[model]), skeleton=str(src / (skel + ".w3d")),
                    anim=str(src / (R["anims"][skel] + ".w3d")), frame=0, show=_body(R, model) + show, textures=tex,
                    masks=masks, colours=R["colours"], out=str(out_dir / (name + ".png")), samples=samples,
                    size=kw.pop("size", (420, 500)), **kw)
    head = dict(focus="head", size=(340, 370), head_bone=R.get("head_bone", "B_HEAD"))
    hm, gm = R["head_model"], R["game_model"]
    helmets = [p[0] for p in parts_of(spec, hm) if p[1] == "CreateAHero_Helmet"]
    rows = {"heads": [job("ea_" + h, hm, True, 0, [h], "EA " + h, **head) for h in R["ea_heads"]] +
                     [job("h_" + h, hm, False, 0, [h], h, **head) for h in helmets],
            "kits": [job("k%d" % i, hm, ea, 0, parts, label) for i, (label, parts, ea) in enumerate(R["kits"])],
            "game": [job("g%d" % i, gm, ea, 1, parts, "IN GAME: " + label, elevation=48, scale=3.0, size=(320, 320))
                     for i, (label, parts, ea) in enumerate(R["kits"])]}
    return rows, out_dir


def run(spec, samples=16):
    from sagekit.pipeline import blender_slot
    rows, out_dir = jobs(spec, samples)
    todo = [j for r in rows.values() for j in r]
    specfile = out_dir / "jobs.json"
    specfile.write_text(json.dumps(todo, indent=1))
    with blender_slot(), (out_dir / "blender.log").open("w") as log:
        subprocess.run([paths.BLENDER, "-b", "--python-exit-code", "1", "--python", str(SCRIPT), "--", str(specfile)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    made = []
    for k, r in rows.items():
        if not r:
            continue
        lab = []
        for j in r:
            p = out_dir / ("l_" + j["name"] + ".png")
            subprocess.run(["magick", j["out"], "-gravity", "NorthWest", "-font", paths.FONT, "-pointsize", "16", "-fill", "white",
                            "-undercolor", "#171b21cc", "-annotate", "+8+8", " %s " % j["label"], str(p)], check=True)
            lab.append(str(p))
        for n in range(0, len(lab), 8):          # same zoom everywhere: tiles at their size, 8 a row
            row = out_dir / ("row_%s_%d.png" % (k, n // 8))
            subprocess.run(["magick", *lab[n:n + 8], "+append", str(row)], check=True)
            made.append(str(row))
    subprocess.run(["magick", *made, "-background", "#171b21", "-gravity", "West", "-append", str(out_dir / "overview.png")],
                   check=True)
    print(out_dir / "overview.png")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    samples = int(sys.argv[sys.argv.index("--samples") + 1]) if "--samples" in sys.argv else 16
    run(importlib.import_module("assets.cah.%s.design" % args[0]), samples)
