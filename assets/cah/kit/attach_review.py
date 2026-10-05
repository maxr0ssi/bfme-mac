"""Review sheet for parts on bones (assets/cah/kit/attach.py): the class's creation-screen head and
hand with EA's part, ours, then EA's again, and the in-game model at the RTS camera.

The game draws a part model of ours at its bone (AttachToBoneInAnotherModule). For the render
each part mesh goes into a copy of EA's model as a rigid sub-object on that bone, which places it
exactly as the attachment does (same bone-space vertices, same bone). Only the listed sub-objects
are drawn, as after the game's SubObjectsUpgrades. The copies are for this sheet only; nothing
ships them.

    python3 -m assets.cah.kit.attach <class> --review   -> build/assets/_review_finish/cah_attach/<class>_*.jpg
"""
import json
import struct
import subprocess
from pathlib import Path

from sagekit import paths
from sagekit.formats.w3d import HLOD, MESH, MESH_HEADER3, W3DFile, chunk_bytes, chunks, rename_model

from . import attach
from .models import folder
from .render import SCRIPT, textures

OUT = Path(paths.BUILD) / "_review_finish" / "cah_attach"


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


def review(spec):
    from sagekit.pipeline import blender_slot
    built, _, _ = attach.load(spec)
    _, src, _ = folder(spec)
    work = attach.attach_dir(spec) / "review"
    work.mkdir(parents=True, exist_ok=True)
    R = spec.RENDER
    comp = {}
    for model in (R["head_model"], R["game_model"]):
        meshes = []
        sk = attach.skeleton(spec, spec.SKELETONS[model])
        for name, (ea_model, bone, data) in built.items():
            if ea_model == model:
                for m in W3DFile(data).meshes.values():
                    meshes.append((m.bytes, sk.names.index(bone)))
        ea = (src / (model + ".w3d")).read_bytes()
        comp[model] = work / (model + "_review.w3d")
        comp[model].write_bytes(composite(ea, model.upper(), meshes))
    tex, masks = textures(spec, list(comp.values()))
    body = lambda m: list(R["body"][m]) if isinstance(R["body"][m], (list, tuple)) else [R["body"][m]]
    helm = next(p[0] for p in attach.parts(spec) if p[1] == "CreateAHero_Helmet")
    axe = next(p[0] for p in attach.parts(spec) if p[1] == "CreateAHero_Weapon")
    ea_helm, ea_axe = R["ea_heads"][-1], "AXE_03"
    hm, gm = R["head_model"], R["game_model"]

    def job(name, model, show, label, **kw):
        skel = spec.SKELETONS[model]
        return dict(name=name, label=label, model=str(comp[model]), skeleton=str(src / (skel + ".w3d")),
                    anim=str(src / (R["anims"][skel] + ".w3d")), frame=0, show=body(model) + show, textures=tex, masks=masks,
                    colours=R["colours"], out=str(work / (name + ".png")), samples=24, size=kw.pop("size", (340, 370)), **kw)
    head = dict(focus="head", head_bone=R.get("head_bone", "B_HEAD"))
    hand = dict(focus="part", dist=15.0)
    rows = [[job("h1", hm, [ea_helm, ea_axe], "1 EA helmet %s" % ea_helm, **head),
             job("h2", hm, [helm, ea_axe], "2 ours %s (EA's hidden)" % helm, **head),
             job("h3", hm, [ea_helm, ea_axe], "3 EA again (ours hidden)", **head)],
            [job("w1", hm, [ea_helm, ea_axe], "1 EA axe %s" % ea_axe, part=[ea_axe], **hand),
             job("w2", hm, [ea_helm, axe], "2 ours %s" % axe, part=[axe], **hand),
             job("w3", hm, [ea_helm, ea_axe], "3 EA again", part=[ea_axe], **hand)],
            [job("g1", gm, [ea_helm, ea_axe], "IN GAME: EA's", elevation=48, scale=3.0, size=(340, 340)),
             job("g2", gm, [helm, axe], "IN GAME: ours", elevation=48, scale=3.0, size=(340, 340)),
             job("g3", gm, [ea_helm, ea_axe], "IN GAME: EA's again", elevation=48, scale=3.0, size=(340, 340))]]
    todo = [j for r in rows for j in r]
    (work / "jobs.json").write_text(json.dumps(todo, indent=1))
    with blender_slot(), (work / "blender.log").open("w") as log:
        subprocess.run([paths.BLENDER, "-b", "--python-exit-code", "1", "--python", str(SCRIPT), "--", str(work / "jobs.json")],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for k, r in enumerate(rows):
        lab = []
        for j in r:
            p = work / ("l_" + j["name"] + ".png")
            subprocess.run(["magick", j["out"], "-gravity", "NorthWest", "-font", paths.FONT, "-pointsize", "16", "-fill", "white",
                            "-undercolor", "#171b21cc", "-annotate", "+8+8", " %s " % j["label"], str(p)], check=True)
            lab.append(str(p))
        row = OUT / ("%s_row%d.jpg" % (spec.NAME, k + 1))
        subprocess.run(["magick", *lab, "+append", "-quality", "90", str(row)], check=True)
        made.append(str(row))
    sheet = OUT / ("%s_sheet.jpg" % spec.NAME)
    subprocess.run(["magick", *made, "-background", "#171b21", "-gravity", "West", "-append", "-quality", "90", str(sheet)], check=True)
    print(sheet)
    return sheet
