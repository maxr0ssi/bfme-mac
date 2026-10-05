"""The fire budget's review sheets: each building's fire before and after, drawn over its renders
(docs/ART.md "Fire budget"; the renderer is sagekit/paint/fire_composite.py).

    python3 -m sagekit.fire_review --snapshot <out.json>
        the fire as it stands: every recipe's points, the kinds, each system's block and live count
    python3 -m sagekit.fire_review --before <snapshot.json> <faction/building> ...
        build/assets/_review_finish/fire_budget/<faction>_<building>.jpg: rows healthy and damaged,
        columns the in-game camera (a 1:1 crop) and the close-up, each before | after, with the live
        particles of our fire (and of EA's damage fire, the same in both) on every tile

Healthy tiles draw over the build's renders (renders/new_<view>.png); damaged ones over a render of
our body with its damaged sheet (the Blender render job, cached in the work folder), with EA's own
damage fire of the DAMAGED state at EA's bones (EA's systems, untinted: the faction's FX archive
only recolours them). The particles are an approximation of the game's sprites; check in game.
"""
import json
import os
import subprocess
import sys

from . import paths

OUT = os.path.join(paths.BUILD, "_review_finish", "fire_budget")
WORK = os.path.join(OUT, "work")
VIEWS = ("ingame", "close")
FONT = paths.FONT


def header_rows(lines):
    """A block's rows from its FXParticleSystem header to its End (our comment line dropped)."""
    i = next(i for i, x in enumerate(lines) if x.strip().lower().startswith(("fxparticlesystem", "particlesystem")))
    return list(lines[i:])


def snapshot(path=None):
    """The fire as the code stands: {kinds, systems: {name: rows}, live: {name: n}, buildings: {id: [[xyz], kind]}}."""
    from . import fire_systems, registry
    from .fire import KINDS, points
    from .fire_budget import rates
    from .fire_systems import LOADED, MEMBER, ea_block
    from .formats.ini import apply_ops
    from .game import Install
    g = Install()
    texts = {m: g.read(m).decode("latin-1") for m in LOADED if g.owner(m)}
    texts[MEMBER] = apply_ops(texts[MEMBER], [fire_systems.ops(g)])
    r = rates(g)
    out = {"kinds": {k: list(v) for k, v in KINDS.items()}, "systems": {}, "live": {}, "buildings": {}}
    for bid in registry.building_ids():
        pts = points(registry.load(bid))
        if not pts:
            continue
        out["buildings"][bid] = [[list(xyz), kind] for _, xyz, kind in pts]
        for s in {s for _, _, k in pts for s in KINDS[k]}:
            for m in (MEMBER,) + tuple(x for x in LOADED if x != MEMBER):
                try:
                    a, z = ea_block(texts[m], s)
                except ValueError:
                    continue
                out["systems"][s] = texts[m].splitlines()[a:z + 1]
                out["live"][s] = r.live(s)
                break
    if path:
        with open(path, "w") as fh:
            json.dump(out, fh, indent=0)
    return out


def ea_damage_fire(b, g):
    """[(model-space point, EA system)] every EA Draw of b's objects burns in its DAMAGED state."""
    from .drawcost import Ini, pick
    from .fire import plan
    out = []
    for member, obj in sorted({(d["file"], d["object"]) for d in plan(b, g)}):
        ini = Ini(g.read(member).decode("latin-1"))
        for draw in ini.draws.get(obj, []):
            out += _state_fire(g, ini, draw, pick(draw, {"DAMAGED"}))
    return out


def _state_fire(g, ini, draw, st):
    """[(model-space point, system)] of one EA Draw's state: its ParticleSysBone lines at its model's
    bones (a bone the model lacks: the origin)."""
    from .drawcost import particles_of, state_lines
    from .formats.w3d import W3DFile
    from .formats.w3dpose import Skeleton, point
    if st is None or not st.model or st.model.lower() == "none" or not g.owner(g.model_path(st.model)):
        return []
    data = g.read(g.model_path(st.model))
    skl = W3DFile(data).skeleton()
    sk = Skeleton(g.read(g.model_path(skl[:-4])) if skl else data)
    bones = {n.upper(): point(m, (0, 0, 0)) for n, m in zip(sk.names, sk.rest)}
    names, out = set(particles_of(ini.lines, draw, st)), []
    for s in [x for x in draw.states if x.kind == "model" and not x.flags and x is not st] + [st]:
        for line in state_lines(ini.lines, s):
            w = line.replace("=", " ").split()
            if len(w) >= 3 and w[0].lower() == "particlesysbone" and w[2] in names:
                out.append((tuple(bones.get(w[1].upper()[:15], (0.0, 0.0, 0.0))), w[2]))
    return out


def damaged_renders(b, ws, views):
    """{view: png} of our body with its damaged sheet (rendered once into the work folder)."""
    from .pipeline import Pipeline, Render
    d_variant = next((new for old, new in ws.variants.items() if old.lower().endswith("_d.tga")), None)
    if d_variant is None:
        return {}
    own = d_variant[:-6] + d_variant[-4:]                       # IBFortresH_D.tga -> IBFortresH.tga
    texmap = ws.texture_map()
    if d_variant.lower() not in texmap:
        return {}
    work = os.path.join(WORK, b.id.replace("/", "_"))
    os.makedirs(work, exist_ok=True)
    prefix = os.path.join(work, "damaged_")
    out = {v: prefix + v + ".png" for v in views}
    if all(os.path.exists(p) for p in out.values()):
        return out
    step = Render(Pipeline(b))
    refs = step.references(ws.shipped_model, recoloured=True)
    refs[own.lower()] = texmap[d_variant.lower()]
    step.blender("render", log_as="render_fire_budget_damaged", w3d=ws.shipped_model, prefix=prefix,
                 views=",".join(views), res="1600x1100", spp="48", frame=b.target, **refs)
    return out


def raw_rgb(png, dest):
    size = subprocess.check_output(["magick", "identify", "-format", "%w %h", png], text=True).split()
    subprocess.check_call(["magick", png, "-alpha", "off", "-depth", "8", "rgb:" + dest])
    return [int(x) for x in size]


def sheet_tiles(bid, before, after, g, cache):
    from . import registry
    from .fire_checks import views as all_views
    from .fx.preview import params
    from .workspace import Workspace
    b = registry.load(bid)
    ws = Workspace(b)
    views = all_views(b, ws, g)
    dmg_bg = damaged_renders(b, ws, VIEWS)
    ea_texts = [g.read(m).decode("latin-1") for m in ("data\\ini\\fxparticlesystem.ini", "data\\ini\\particlesystem.ini")]
    from .fire_systems import ea_block
    damage = ea_damage_fire(b, g)
    ea_params, ea_live = {}, 0.0
    from .drawcost import Rates
    rates = Rates(ea_texts)
    for _, s in damage:
        ea_live += rates.live(s)
        if s not in ea_params:
            for t in ea_texts:
                try:
                    a, z = ea_block(t, s)
                except ValueError:
                    continue
                ea_params[s] = params(t.splitlines()[a:z + 1], g, cache)
                break
    tiles, labels = [], []
    work = os.path.join(WORK, bid.replace("/", "_"))
    os.makedirs(work, exist_ok=True)
    for state in ("healthy", "damaged"):
        for v in VIEWS:
            bg_png = os.path.join(ws.path("renders"), "new_%s.png" % v) if state == "healthy" else dmg_bg.get(v)
            if not bg_png or not os.path.exists(bg_png):
                bg_png = os.path.join(ws.path("renders"), "new_%s.png" % v)
            bg = os.path.join(work, "%s_%s.rgb" % (state, v))
            size = raw_rgb(bg_png, bg)
            for side, snap in (("before", before), ("after", after)):
                pts = snap["buildings"].get(bid, [])
                ems = []
                for xyz, kind in pts:
                    ems.append(dict(pos=xyz, systems=[params(header_rows(snap["systems"][s]), g, cache)
                                                      for s in snap["kinds"][kind]]))
                if state == "damaged":
                    ems += [dict(pos=list(p), systems=[ea_params[s]]) for p, s in damage if s in ea_params]
                ours = sum(snap["live"][s] for _, k in pts for s in snap["kinds"][k])
                out = os.path.join(work, "%s_%s_%s.ppm" % (state, v, side))
                tiles.append(dict(bg=bg, size=size, view=list(views[v]), emitters=ems, seed=11, out=out))
                text = "%s, %s, %s: our fire %.0f live particles (%d points)" % (side, state, v, ours, len(pts))
                if state == "damaged":
                    text += " + EA's damage fire %.0f" % ea_live
                labels.append((out, text, size))
    return tiles, labels


def review(ids, before_path):
    from .game import Install
    g = Install()
    with open(before_path) as fh:
        before = json.load(fh)
    after = snapshot()
    os.makedirs(WORK, exist_ok=True)
    cache = {}
    for bid in ids:
        tiles, labels = sheet_tiles(bid, before, after, g, cache)
        job = os.path.join(WORK, bid.replace("/", "_") + "_job.json")
        with open(job, "w") as fh:
            json.dump(dict(tiles=tiles), fh)
        subprocess.check_call([paths.blender_python(), "-m", "sagekit.paint.fire_composite", job], cwd=paths.REPO)
        sheet(bid, labels, before, after)


def sheet(bid, labels, before, after):
    """Rows healthy, damaged; columns in-game crop before | after, close before | after (half size)."""
    pngs = []
    for out, text, (w, h) in labels:
        png = out[:-4] + ".png"
        crop = ["-gravity", "center", "-crop", "%dx%d+0+0" % (w // 2, h // 2), "+repage"] if "ingame" in out else \
            ["-resize", "%dx%d" % (w // 2, h // 2)]
        subprocess.check_call(["magick", out] + crop + ["-font", FONT, "-gravity", "NorthWest", "-fill", "#f2ead8",
                               "-undercolor", "#000a", "-pointsize", "17", "-annotate", "+8+8", " %s " % text, png])
        pngs.append(png)
    rows = []
    for i in range(0, len(pngs), 4):
        row = os.path.join(WORK, "%s_row%d.png" % (bid.replace("/", "_"), i // 4))
        subprocess.check_call(["magick"] + sum(([p, "-size", "6x10", "xc:#141414"] for p in pngs[i:i + 4]), [])[:-3]
                              + ["-background", "#141414", "-gravity", "center", "+append", row])
        rows.append(row)
    nb = sum(before["live"][s] for _, k in before["buildings"].get(bid, []) for s in before["kinds"][k])
    na = sum(after["live"][s] for _, k in after["buildings"].get(bid, []) for s in after["kinds"][k])
    head = os.path.join(WORK, "%s_head.png" % bid.replace("/", "_"))
    subprocess.check_call(["magick", "-size", "3218x46", "xc:#141414", "-font", FONT, "-fill", "#f0c870", "-pointsize", "24",
                           "-gravity", "West", "-annotate", "+10+0",
                           "%s: our fire %.0f -> %.0f live particles (budget 60). Columns: in-game camera (1:1 crop) "
                           "before, after; close-up before, after. Particles approximated (no wind); check in game."
                           % (bid, nb, na), head])
    dest = os.path.join(OUT, bid.replace("/", "_") + ".jpg")
    subprocess.check_call(["magick", head] + rows + ["-background", "#141414", "-gravity", "NorthWest", "-append",
                                                     "-quality", "88", dest])
    print("  " + os.path.relpath(dest, paths.REPO))


def main(argv):
    if "--snapshot" in argv:
        snapshot(argv[argv.index("--snapshot") + 1])
        return 0
    before = argv[argv.index("--before") + 1] if "--before" in argv else os.path.join(OUT, "before.json")
    ids = [a for a in argv if "/" in a and not a.endswith(".json")]
    review(ids, before)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
