"""A skinned body's animation, played: EA's model and ours posed in EA's own animation (the idle the
Draw module plays) at three frames, at the building's RTS camera, side by side:
renders/anim/compare_<animation>.png (rows: frames; columns: EA | ours).

One Blender process (sagekit/blender/unit_pose.py, the units' poser: OpenSAGE's decoder, every
frame checked finite and moving) renders both sides with one camera and light. The render step
runs it for every recipe whose target is a skin (sagekit/skinbody.py); never the game.
"""
import json
import os
import subprocess

from . import paths
from .formats.w3d import W3DFile

SCRIPT = os.path.join(paths.REPO, "sagekit", "blender", "unit_pose.py")
SIZE = (1100, 760)


def animations(b, install):
    """[animation name] of the source model's skeleton that the Draw modules this building covers
    play (KBMill_IDLE), in the INI's order."""
    skl = (W3DFile(install.read(install.model_path(b.source))).skeleton() or "")[:-4].lower()
    out = []
    for draws in b.objects(install).values():
        for d in draws:
            for s in d.states if b.covers(d) else ():
                for a in s.animations:
                    k, _, name = a.partition(".")
                    if skl and k.lower() == skl and name and name not in out:
                        out.append(name)
    return out


def frames(n, count=3):
    return [int(i * n / count) for i in range(count)]


def render(step):
    """The render step's hook: nothing for a rigid target."""
    from . import skinbody
    from .formats import w3dpose as P
    from .nightlights import day_hidden
    b, ws, g = step.b, step.ws, step.p.install
    if not skinbody.skinned(ws):
        return []
    out_dir = ws.path("renders", "anim")
    os.makedirs(out_dir, exist_ok=True)
    skel = os.path.join(ws.src, W3DFile(ws.source_model).skeleton())
    views = {}
    for v in getattr(b, "anim_views", ("rts",)):      # the RTS camera, and any closer view the recipe adds
        target, dist, elev, azim, lens = b.views[v]
        views[v] = dict(target=list(target), distance=dist, elevation=elev, azimuth=azim, lens=lens, size=list(SIZE),
                        fit=False, fit_min=0, fit_scale=1)
    made = []
    for name in animations(b, g):
        anim = ws.path("src", name.lower() + ".w3d")
        with open(anim, "wb") as fh:
            fh.write(g.read(g.model_path(name)))
        n = P.Animation(open(anim, "rb").read()).frames
        jobs = []
        for who, model in (("orig", ws.reference_model), ("new", ws.shipped_model)):
            textures = ws.texture_map()                 # as the render step maps them
            textures.update(step.references(model, recoloured=who == "new"))
            hide = list(day_hidden(b, open(model, "rb").read()))
            for v, view in views.items():
                for f in frames(n):
                    jobs.append(dict(who=who, state="anim_%s_%s_%d" % (who, v, f), view=view, frame=f, model=model,
                                     reference=ws.reference_model, skeleton=skel, anim=anim, textures=textures,
                                     smooth=[], opaque=False, hide=hide, out=_cell(out_dir, who, name, v, f),
                                     motion=os.path.join(out_dir, "motion_%s.txt" % name.lower())))
        spec = os.path.join(out_dir, "jobs_%s.json" % name.lower())
        with open(spec, "w") as fh:
            json.dump(jobs, fh, indent=1)
        from .pipeline import blender_slot
        with blender_slot(), open(os.path.join(ws.logs, "anim_%s.log" % name.lower()), "w") as log:
            subprocess.run([paths.BLENDER, "-b", "--python-exit-code", "1", "--python", SCRIPT, "--", spec],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        for v in views:
            rows = []
            for f in frames(n):
                row = os.path.join(out_dir, "_row_%03d.png" % f)
                cells = []
                for who, text in (("orig", "EA's original"), ("new", "%s (%s)" % (b.id, b.style.palette.name))):
                    src = _cell(out_dir, who, name, v, f)
                    cell = src[:-4] + "_l.png"
                    step.tool(["magick", src, "-font", step.FONT, "-gravity", "NorthWest", "-fill", "#f2ead8",
                               "-undercolor", "#0008", "-pointsize", "26", "-annotate", "+16+12",
                               " %s - %s frame %d of %d (%s) " % (text, name, f, n, v), cell])
                    cells.append(cell)
                step.tool(["magick", cells[0], "-size", "10x%d" % SIZE[1], "xc:#141414", cells[1], "+append", row])
                rows.append(row)
                for c in cells:
                    os.remove(c)
            dest = os.path.join(out_dir, "compare_%s%s.png" % (name.lower(), "" if v == "rts" else "_" + v))
            step.tool(["magick"] + rows + ["-background", "#141414", "-splice", "0x10", "-append", dest])
            for r in rows:
                os.remove(r)
            made.append(dest)
            print("  " + os.path.relpath(dest, paths.REPO))
    return made


def _cell(out_dir, who, name, view, f):
    return os.path.join(out_dir, "%s_%s%s_f%03d.png" % (who, name.lower(), "" if view == "rts" else "_" + view, f))
