#!/usr/bin/env python3
"""Hero portraits and icons in EA's look, rendered from the heroes' game models.

EA's hero art is renders of the game models, graded: the portrait behind the power buttons
(HP*, 192 x 192 on a 256 page of its own, sepia on parchment under a vignette), the hero icon
(HI*, 64 x 64, the bust cut out) and its revive state (HI*_res, the bust in blue on a pale disc).
Each of ours is graded against the EA hero it stands next to (the Captain against King Dain,
Gamling against Boromir, whose kit he carries), at 4x, then box-filtered (assets/heroes/imaging.py).

    python3 -m assets.heroes.portraits [captain gamling]   -> build/assets/heroes/portraits/
"""
import json
import subprocess
import sys
from pathlib import Path

from sagekit import paths
from sagekit.formats.textures import compiled_path, sheet_member, write_dds
from sagekit.game import Install

from . import imaging
from . import render as R

OUT = Path(paths.BUILD) / "heroes" / "portraits"
# hero: (portrait, icon, its EA reference portrait/icon, how the model is shot)
HEROES = {
    "captain": dict(portrait="HPEreborCaptain", icon="HIEreborCaptain", page="SKHeroUI_E01.tga",
                    ref=("HPKingDain", "HIKingDain"), bone="B_HEAD", offset=[0.6, 0, 1.0], dist=(19.5, 12.0), az=(16, 20)),
    "gamling": dict(portrait="HPGamling", icon="HIGamling", page="SKHeroUI_G01.tga",
                    ref=("HPBorimir", "HIBorimir"), bone="BAT_HEAD", offset=[0.5, 0, 0.1], dist=(12.0, 9.0), az=(-30, -26)),
}
LIKE = {"page": "heroui_039.tga", "icon": "hikingdain.tga"}      # EA records to copy (a texture record holds no size)


def icon_texture(name):
    """Our icon's texture: SK + the image name (EA ships placeholder HIGamling textures of its own)."""
    return "SK%s.tga" % name


def model_source(hero):
    """(model file, skeleton, animation, textures, meshes shown) of the hero's game model."""
    if hero == "captain":
        from .captain.design import MODEL, SKELETON, folder
        d, src, work = folder()
        tex = json.loads((work / "textures.json").read_text())
        return (work / (MODEL.lower() + ".w3d"), src / (SKELETON.lower() + ".w3d"), src / "dudain_idlb.w3d", tex,
                ["COAT", "BODY", "HEAD", "SHIELD", "HELMET", "REDAXE"])
    from .gamling_model import GEAR, MODEL, SKELETON, folder
    d, src, work = folder()
    tex = json.loads((work / "textures.json").read_text())
    return (work / (MODEL.lower() + ".w3d"), src / (SKELETON.lower() + ".w3d"), src / "guboromir_idla.w3d", tex,
            ["RUGAMLING_MESH", GEAR])


def ea_reference(name, dest):
    """EA's mapped image `name` as a PNG of its rect."""
    from . import ea
    from sagekit.icons.pixels import crop, read, write
    body = ea.all_blocks("MappedImage")[name]
    import re
    tex = re.search(r"Texture\s*=\s*(\S+)", body).group(1)
    l, t, r, b = (int(re.search(r"%s:(\d+)" % k, body).group(1)) for k in ("Left", "Top", "Right", "Bottom"))
    g = Install()
    m = sheet_member(g, tex)
    raw = dest.with_suffix(".dds")
    raw.write_bytes(g.read(m))
    img = read(str(raw))
    w, h, data = crop(img, (l, t, r if r - l in (64, 192) else r + 1, b if b - t in (64, 192) else b + 1))
    write(str(dest), w, h, data)
    return dest


def build(heroes=None):
    heroes = heroes or list(HEROES)
    OUT.mkdir(parents=True, exist_ok=True)
    jobs, grade, made = [], [], {}
    for h in heroes:
        H = HEROES[h]
        model, skel, anim, tex, show = model_source(h)
        hp_ref = ea_reference(H["ref"][0], OUT / ("ea_%s.png" % H["ref"][0]))
        hi_ref = ea_reference(H["ref"][1], OUT / ("ea_%s.png" % H["ref"][1]))
        res_ref = ea_reference(H["ref"][1] + "_res", OUT / ("ea_%s_res.png" % H["ref"][1]))
        common = dict(focus="head", head_bone=H["bone"], head_offset=H["offset"], elevation=6, transparent=True, samples=48)
        jobs += [R.job("%s_hp" % h, "", model, skel, anim, show, tex, OUT, size=(768, 768), head_dist=H["dist"][0],
                       azimuth=H["az"][0], **common),
                 R.job("%s_hi" % h, "", model, skel, anim, show, tex, OUT, size=(256, 256), head_dist=H["dist"][1],
                       azimuth=H["az"][1], **common)]
        grade += [dict(op="portrait", render=str(OUT / ("%s_hp.png" % h)), ea=str(hp_ref), out=str(OUT / (H["portrait"] + ".png"))),
                  dict(op="icon", render=str(OUT / ("%s_hi.png" % h)), ea=str(hi_ref), out=str(OUT / (H["icon"] + ".png"))),
                  dict(op="revive", icon=str(OUT / (H["icon"] + ".png")), ea=str(res_ref), out=str(OUT / (H["icon"] + "_res.png")))]
        made[h] = H
    _render(jobs)
    report = imaging.run(grade, OUT)
    files = {}
    for h, H in made.items():
        page = OUT / (H["page"][:-4] + ".png")             # EA's layout: the portrait at the page's top left
        subprocess.run(["magick", "-size", "256x256", "xc:#00000000", str(OUT / (H["portrait"] + ".png")), "-geometry", "+0+0",
                        "-composite", str(page)], check=True)
        for png, tga in ((page, H["page"]), (OUT / (H["icon"] + ".png"), icon_texture(H["icon"])),
                         (OUT / (H["icon"] + "_res.png"), icon_texture(H["icon"] + "_res"))):
            dds = OUT / (tga[:-4].lower() + ".dds")
            write_dds(str(png), str(dds), alpha=True)
            files[compiled_path(tga, ".dds")] = dds
    (OUT / "report.json").write_text(json.dumps(dict(grade=report, files={k: str(v) for k, v in files.items()}), indent=1))
    return files


def _render(jobs):
    from sagekit.pipeline import blender_slot
    spec = OUT / "jobs.json"
    spec.write_text(json.dumps(jobs, indent=1))
    with blender_slot(), (OUT / "blender.log").open("w") as log:
        subprocess.run([paths.BLENDER, "-b", "--python-exit-code", "1", "--python", str(R.SCRIPT), "--", str(spec)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)


def mapped_images():
    """Our MappedImage blocks: {EA file key: text} (portraits go with EA's heroui.ini, icons with
    heroselecticons.ini, in EA's form)."""
    hp, hi = [], []
    for H in HEROES.values():
        hp.append("MappedImage %s\n  Texture = %s\n  TextureWidth = 256\n  TextureHeight = 256\n"
                  "  Coords = Left:0 Top:0 Right:192 Bottom:192\n  Status = NONE\nEnd\n" % (H["portrait"], H["page"]))
        for n in (H["icon"], H["icon"] + "_res"):
            hi.append("MappedImage %s\n\tTexture = %s\n\tTextureWidth = 64\n\tTextureHeight = 64\n"
                      "\tCoords = Left:0 Top:0 Right:63 Bottom:63\n\tStatus = NONE\nEnd\n" % (n, icon_texture(n)))
    return {"heroui": "\n".join(hp), "heroselecticons": "\n".join(hi)}


def textures():
    """(texture name, EA texture whose asset.dat record it copies) of every file we ship."""
    out = []
    for H in HEROES.values():
        out += [(H["page"].lower(), LIKE["page"]), (icon_texture(H["icon"]).lower(), LIKE["icon"]),
                (icon_texture(H["icon"] + "_res").lower(), LIKE["icon"])]
    return out


if __name__ == "__main__":
    for k, v in build(sys.argv[1:] or None).items():
        print(k, v)
