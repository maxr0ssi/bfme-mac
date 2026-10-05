"""Review sheet for parts on bones (assets/cah/kit/attach.py), per class: for each subclass, each
row (helmets, shoulders, shields, weapons) on the creation-screen model as the menu cycles it: EA's
part, each of ours, EA's again; then each of the subclass's in-game models (and the mounted one) at
the RTS camera with EA's kit, our serious kit and our fun kit.

The game draws a part model of ours at its bone (AttachToBoneInAnotherModule). For the render
each part mesh goes into a copy of EA's model as a rigid sub-object on that bone, which places it
exactly as the attachment does (same bone-space vertices, same bone); a part split over bones
shows all its pieces. Only the listed sub-objects are drawn, as after the game's
SubObjectsUpgrades. The copies are for this sheet only; nothing ships them.

    python3 -m assets.cah.kit.attach <class> --review        -> build/assets/_review_finish/cah_attach/<class>_sheet.jpg
    python3 -m assets.cah.kit.attach <class> --review-only   (the built parts, no rebuild)
    python3 -m assets.cah.kit.attach_review --paint [class ...]  -> .../cah_attach/paint_sheet.jpg: a few
        serious parts per class in three Paint colours (the Paint picker, mask B)
"""
import json
import struct
import subprocess
from pathlib import Path

from sagekit import paths
from sagekit.formats.w3d import HLOD, MESH, W3DFile, chunk_bytes, chunks

from . import attach
from .models import folder, parts_of, rename_mesh
from .render import SCRIPT, textures

OUT = Path(paths.BUILD) / "_review_finish" / "cah_attach"
GROUPS = [("CreateAHero_Helmet", "HELMET", ("HLMT", "HELM", "HAT")), ("CreateAHero_ShoulderPlates", "SHOULDERS", ("SLDR",)),
          ("CreateAHero_Shield", "SHIELD", ("SHLD", "SHIELD")),
          ("CreateAHero_Weapon", "WEAPON", ("AXE", "SWRD", "SWD", "BOW", "STFF", "HMR", "TROLLHAMMER", "SPR", "MACE", "CLUB", "HAMMER"))]
PER_ROW = 8


def composite(ea_bytes, ea_name, meshes):
    """EA's model plus [(mesh chunk, bone index)] as rigid sub-objects on those bones."""
    top = list(chunks(ea_bytes, 0, len(ea_bytes)))
    last = max(k for k, (t, _, _, _) in enumerate(top) if t == MESH)
    out = bytearray()
    for k, (t, o, s, _) in enumerate(top):
        if t == HLOD:
            body = bytearray()
            for t2, o2, s2, h2 in chunks(ea_bytes, o + 8, o + 8 + s):
                if not h2:
                    body += ea_bytes[o2:o2 + 8 + s2]
                    continue
                arr = bytearray()
                for t3, o3, s3, _ in chunks(ea_bytes, o2 + 8, o2 + 8 + s2):
                    c = bytearray(ea_bytes[o3:o3 + 8 + s3])
                    if t3 == 0x703:
                        struct.pack_into("<I", c, 8, struct.unpack_from("<I", c, 8)[0] + len(meshes))
                    arr += c
                for chunk, bone in meshes:
                    name = W3DFile(chunk).meshes
                    arr += chunk_bytes(0x704, struct.pack("<I32s", bone, ("%s.%s" % (ea_name, next(iter(name)))).encode()), False)
                body += chunk_bytes(t2, bytes(arr), True)
            out += chunk_bytes(HLOD, bytes(body), True)
        else:
            out += ea_bytes[o:o + 8 + s]
        if k == last:
            for chunk, _ in meshes:
                out += attach._set_container(chunk, ea_name)
    return bytes(out)


def review_models(spec, built, src, work):
    """{EA model: (review copy path, {part: [its mesh names in the copy]}, head bone)}."""
    out = {}
    for model in attach.ea_models(spec):
        sk = attach.skeleton(spec, spec.SKELETONS[model])
        meshes, names, head = [], {}, None
        for name, (ea_model, bone, data) in sorted(built.items()):
            if ea_model != model:
                continue
            if attach.bone_code(bone) == "HD":
                head = bone
            for part, m in W3DFile(data).meshes.items():
                k = len(names.setdefault(part, []))
                piece = part if not k else part[:13] + "~%d" % k     # a split part's other pieces
                names[part].append(piece)
                meshes.append((rename_mesh(m.bytes, piece) if k else m.bytes, sk.names.index(bone)))
        path = work / (model + "_review.w3d")
        path.write_bytes(composite((src / (model + ".w3d")).read_bytes(), model.upper(), meshes))
        out[model] = (path, names, head or next((b for b in sk.names if "HEAD" in b.upper()), "B_HEAD"))
    return out


def body(R, model):
    b = R["body"][model]
    return list(b) if isinstance(b, (list, tuple)) else [b]


def ea_kit(R, model):
    """EA's parts the class's render shows (its EA kit and heads), for picking EA's part of a row."""
    names = list(R.get("ea_heads", []))
    for k in R.get("kits", []):
        if len(k) == 3 and k[2]:
            names += k[1]
        elif len(k) >= 4 and k[3] and k[0][:7] == model[:7]:
            names += k[2]
    return names


def ea_part(R, model, have, group):
    """EA's part of `group` in `model`: one of the class's EA kit parts if the model has it, else the
    first of the model's meshes with the row's prefix."""
    pre = next(p for g, _, p in GROUPS if g == group)
    for n in ea_kit(R, model) + sorted(have):
        if n.upper() in have and n.upper().startswith(pre):
            return n.upper()
    return None


def job_maker(spec, built, work):
    """(job(name, model, show, label, colours=None, **kw) -> a render job, review models): the
    renders draw the review copies of EA's models with our parts on their bones."""
    R = spec.RENDER
    src = folder(spec)[1]
    rev = review_models(spec, built, src, work)
    tex, masks = textures(spec, [p for p, _, _ in rev.values()])

    def job(name, model, show, label, colours=None, **kw):
        skel = spec.SKELETONS[model]
        return dict(name=name, label=label, model=str(rev[model][0]), skeleton=str(src / (skel + ".w3d")),
                    anim=str(src / (R["anims"][skel] + ".w3d")), frame=0, show=body(R, model) + show, textures=tex,
                    masks=masks, colours=colours or R["colours"], out=str(work / (name + ".png")), samples=16,
                    size=kw.pop("size", (300, 330)), **kw)
    return job, rev


def focus_of(spec, rev, model, group):
    """The camera for a row's part on `model`: helmets at the head, capes from behind."""
    path, names, head = rev[model]
    sk = attach.skeleton(spec, spec.SKELETONS[model])
    k = sk.rest[sk.names.index(head)][11] / 14.8                  # the head's height against the CaH dwarf's
    focus = dict(focus="head", head_bone=head) if group == "CreateAHero_Helmet" else dict(focus="part", dist=16.0 * k)
    if group == "CreateAHero_ShoulderPlates":
        focus["azimuth"] = 150                                  # capes and cloaks hang at the back
    return focus


def jobs(spec, built, work):
    R = spec.RENDER
    job, rev = job_maker(spec, built, work)
    rows = []
    for sub in spec.SUBCLASSES:
        models = [m.lower() for m in sub["models"]]
        c = next((m for m in models if spec.KIND[m] == "c"), models[0])
        path, names, head = rev[c]
        have = set(W3DFile(str(path)).meshes)
        mine = [p for p in parts_of(spec, c) if p[0] in names]
        for group, title, _ in GROUPS:
            ours = [p[0] for p in mine if p[1] == group]
            if not ours:
                continue
            ea = ea_part(R, c, have, group)
            focus = focus_of(spec, rev, c, group)
            part = lambda shown: dict(part=shown) if focus["focus"] == "part" else {}
            row = []
            if ea:
                row.append(job("%s_%s_ea1" % (c, title), c, [ea], "EA %s" % ea, **focus, **part([ea])))
            for n, p in enumerate(ours):
                row.append(job("%s_%s_%d" % (c, title, n), c, names[p], "%d %s" % (n + 1, p), **focus, **part(names[p])))
            if ea:
                row.append(job("%s_%s_ea2" % (c, title), c, [ea], "EA again", **focus, **part([ea])))
            rows.append(("%s, %s (%s): EA's, ours in menu order, EA's again" % (sub["name"], title.lower(), c.upper()), row))
        game = []
        for m in models:
            path, names, _ = rev[m]
            have = set(W3DFile(str(path)).meshes)
            kit_ea = [n for n in (ea_part(R, m, have, g) for g, _, _ in GROUPS) if n]
            mine = [p for p in parts_of(spec, m) if p[0] in names]
            pick = lambda sheet: [n for g, _, _ in GROUPS for p in [next((q for q in mine if q[1] == g and q[5] == sheet), None)]
                                  if p for n in names[p[0]]]
            kw = dict(elevation=48, scale=1.8, size=(300, 300))
            if spec.KIND[m] == "c":
                kw = dict(size=(300, 330))
            for label, show in (("EA's", kit_ea), ("ours, serious", pick("serious")), ("ours, fun", pick("fun"))):
                game.append(job("%s_kit_%s" % (m, label.split()[-1].strip(",")), m, show, "%s %s" % (m[5:].upper(), label), **kw))
        rows.append(("%s: kits on each model (in game at the RTS camera, the creation screen, mounted)" % sub["name"], game))
    return rows


# the Paint picker's colours on the Paint sheet (Hair and Skin stay the class's own)
PAINTS = [("red", (150, 28, 22)), ("blue", (38, 66, 150)), ("green", (52, 120, 48))]


def paint_rows(spec, n=3):
    """One row per class: up to n serious parts (the helmet, shoulders and shield or weapon with
    the most Paint) on the creation-screen model, each in every PAINTS colour."""
    R = spec.RENDER
    built, _, report = attach.load(spec)
    work = attach.attach_dir(spec) / "review"
    work.mkdir(parents=True, exist_ok=True)
    job, rev = job_maker(spec, built, work)
    cov = report["attach"]["paint"]
    sub = spec.SUBCLASSES[0]
    models = [m.lower() for m in sub["models"]]
    c = next((m for m in models if spec.KIND[m] == "c"), models[0])
    names = rev[c][1]
    mine = [p for p in parts_of(spec, c) if p[0] in names and p[5] == "serious" and p[6] is None]
    picks = []
    for groups in (("CreateAHero_Helmet",), ("CreateAHero_ShoulderPlates",), ("CreateAHero_Shield", "CreateAHero_Weapon")):
        best = sorted((p for p in mine if p[1] in groups), key=lambda p: -cov[p[0].upper()][2])
        picks += best[:1]
    row = []
    for p in picks[:n]:
        focus = focus_of(spec, rev, c, p[1])
        part = dict(part=names[p[0]]) if focus["focus"] == "part" else {}
        for label, rgb in PAINTS:
            row.append(job("%s_paint_%s_%s" % (c, p[0].lower(), label), c, names[p[0]], "%s %s" % (p[0], label),
                           colours=[R["colours"][0], R["colours"][1], rgb], **focus, **part))
    return ("%s (%s): Paint picker red / blue / green" % (spec.NAME, c.upper()), row), work


def render(rows, work, sheet, per_row=PER_ROW):
    """Render the rows' jobs in one Blender run and lay them out under their titles into `sheet`."""
    from sagekit import paths as P
    from sagekit.pipeline import blender_slot
    todo = [j for _, r in rows for j in r]
    (work / "jobs.json").write_text(json.dumps(todo, indent=1))
    with blender_slot(), (work / "blender.log").open("w") as log:
        subprocess.run(["nice", "-n", "15", P.BLENDER, "-b", "--python-exit-code", "1", "--python", str(SCRIPT), "--",
                        str(work / "jobs.json")], stdout=log, stderr=subprocess.STDOUT, check=True)
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for k, (title, r) in enumerate(rows):
        head = work / ("t_%d.png" % k)
        subprocess.run(["magick", "-size", "%dx34" % (300 * min(per_row, len(r))), "xc:#171b21", "-font", P.FONT, "-pointsize", "18",
                        "-fill", "#e8e2d0", "-gravity", "West", "-annotate", "+10+0", title, str(head)], check=True)
        made.append(str(head))
        lab = []
        for j in r:
            p = work / ("l_" + j["name"] + ".png")
            subprocess.run(["magick", j["out"], "-resize", "%dx%d!" % tuple(j["size"]), "-gravity", "NorthWest", "-font", P.FONT,
                            "-pointsize", "15", "-fill", "white", "-undercolor", "#171b21cc", "-annotate", "+6+6", " %s " % j["label"],
                            str(p)], check=True)
            lab.append(str(p))
        for n in range(0, len(lab), per_row):
            row = work / ("row_%d_%d.png" % (k, n // per_row))
            subprocess.run(["magick", *lab[n:n + per_row], "-background", "#171b21", "-gravity", "North", "+append", str(row)], check=True)
            made.append(str(row))
    subprocess.run(["magick", *made, "-background", "#171b21", "-gravity", "West", "-append", "-quality", "88", str(sheet)], check=True)
    print(sheet)
    return sheet


def review(spec):
    built, _, _ = attach.load(spec)
    work = attach.attach_dir(spec) / "review"
    work.mkdir(parents=True, exist_ok=True)
    return render(jobs(spec, built, work), work, OUT / ("%s_sheet.jpg" % spec.NAME))


def paint_review(specs):
    """build/assets/_review_finish/cah_attach/paint_sheet.jpg: a few serious parts per class in
    three Paint colours (python3 -m assets.cah.kit.attach_review --paint)."""
    rows = [paint_rows(s) for s in specs]
    work = Path(paths.BUILD) / "cah" / "paint_review"
    work.mkdir(parents=True, exist_ok=True)
    return render([r for r, _ in rows], work, OUT / "paint_sheet.jpg", per_row=9)


if __name__ == "__main__":
    import importlib
    import sys
    if sys.argv[1:2] == ["--paint"]:
        names = sys.argv[2:] or [s.NAME for s in importlib.import_module("assets.cah.pack.design").classes()]
        paint_review([importlib.import_module("assets.cah.%s.design" % n) for n in names])
