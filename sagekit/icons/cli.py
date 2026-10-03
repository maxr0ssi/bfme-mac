"""python3 -m sagekit icons <faction> [options] (docs/ICONS.md)

    --map                 the faction's building images: in its table, kept EA's, or not covered
    --render [--only A,B] [--samples N] [--who new,ea]   the shots (one Blender), then everything below
    (no option)           grade the renders, compose the pages, check them, the review sheet
    --stage | --install | --revert [--dry-run]   the shared !!!!!!!!!!!!!!sagekit-icons.big
                          (`icons all --stage`: every faction with an icon run)
"""
import argparse
import json
import os
import subprocess

from .. import paths, registry
from ..game import Install
from . import pages, pixels, root, table
from .mapped import candidates, images, on_page

CLOUDS = {"parchment": "art\\compiledtextures\\cm\\cm1_cloud.dds", "sky": "art\\compiledtextures\\ts\\tscloudmed.dds"}


def manifest(faction, g):
    """{image: {page, rect, kind, building, sky}} of the faction's table."""
    icons, _ = table(faction)
    imgs = images(g)
    out = {}
    for name, shot in sorted(icons.items()):
        img = imgs.get(name.lower())
        if img is None:
            raise SystemExit("%s: no MappedImage %s" % (faction, name))
        dds, _ = pages.extract(g, img.page, os.path.join(root(faction), "src"))
        page = pages.info(open(dds, "rb").read())
        if img.size != (page["width"], page["height"]) or img.rect[2] > page["width"] or img.rect[3] > page["height"]:
            raise SystemExit("%s: %s is %s on a page the INI says is %s; the page is %dx%d" % (
                faction, name, img.rect, img.size, page["width"], page["height"]))
        out[name] = dict(page=img.page, rect=list(img.rect), kind=shot.kind, building=shot.building, sky=shot.sky)
    return out


def show_map(faction):
    g = Install()
    icons, keep = table(faction)
    ids = [b for b in registry.building_ids() if b.startswith(faction + "/")]
    cand = candidates(g, [registry.load(b) for b in ids])
    imgs = images(g)
    for name, who in sorted(cand.items()):
        img = imgs.get(name)
        if img is None or not img.page.startswith(("buildingradialbuttons", "expansion1icons")):
            continue
        mine = next((k for k in icons if k.lower() == name), None)
        kept = next((k for k in keep if k.lower() == name), None)
        state = "table: %s" % icons[mine].building if mine else "kept: %s" % keep[kept] if kept else "NOT COVERED"
        print("%-30s %-28s %-34s %s" % (img.name, img.page, ", ".join(sorted(b.split("/")[1] for b in who)), state))
    for k in sorted(set(icons) - {imgs[n].name for n in cand if n in imgs}):
        print("%-30s %-28s %-34s table: %s (by hand)" % (k, imgs[k.lower()].page, "-", icons[k].building))


def grade(faction, g, man):
    r = root(faction)
    src = os.path.join(r, "src")
    os.makedirs(os.path.join(r, "crops"), exist_ok=True)
    clouds = {}
    for k, member in CLOUDS.items():
        clouds[k] = os.path.join(src, k + ".png")
        if not os.path.exists(clouds[k]):
            with open(clouds[k][:-4] + ".dds", "wb") as fh:
                fh.write(g.read(member))
            subprocess.check_call([pixels.MAGICK, clouds[k][:-4] + ".dds[0]", clouds[k]])
    icons, _ = table(faction)
    job = dict(clouds=clouds, icons=[])
    for name, m in man.items():
        _, png = pages.extract(g, m["page"], src)
        ea = os.path.join(src, "ea_%s.png" % name)
        pixels.write(ea, *pixels.crop(pixels.read(png), m["rect"]))
        renders = []
        for who in ("new", "ea"):
            p = os.path.join(r, "render", "%s_%s.png" % (name, who))
            if os.path.exists(p):
                renders.append([p, os.path.join(r, "crops", "%s_%s@4x.png" % (name, who)),
                                os.path.join(r, "crops", "%s_%s.png" % (name, who))])
        if not renders:
            raise SystemExit("%s: not rendered: python3 -m sagekit icons %s --render --only %s" % (name, faction, name))
        job["icons"].append(dict(name=name, kind=m["kind"], sky=m["sky"], ea=ea, renders=renders,
                                 grade=icons[name].grade))
    path = os.path.join(r, "grade.json")
    with open(path, "w") as fh:
        json.dump(job, fh, indent=1)
    res = subprocess.run([paths.blender_python(), "-m", "sagekit.paint.icons", path], cwd=paths.REPO,
                         env=dict(os.environ, PYTHONPATH=paths.REPO), capture_output=True, text=True)
    if res.returncode:
        raise SystemExit("grading failed:\n" + res.stderr[-3000:])


def compose(g, page, crops, dest):
    """EA's page with crops [(rect, png)] in place: (png, dds) under dest/, and its problems."""
    src = os.path.join(dest, "..", "src")
    ea_dds, ea_png = pages.extract(g, page, src)
    img = pixels.read(ea_png)
    for rect, png in crops:
        img = pixels.paste(img, rect, pixels.read(png))
    os.makedirs(dest, exist_ok=True)
    png, dds = os.path.join(dest, page + ".png"), os.path.join(dest, page + ".dds")
    pixels.write(png, *img)
    rects = [tuple(r) for r, _ in crops]
    pages.write(ea_dds, png, rects, dds)
    return png, dds, pages.check(ea_dds, dds, png, rects)


def build_pages(faction, g, man):
    r = root(faction)
    by_page = {}
    for name, m in man.items():
        by_page.setdefault(m["page"], []).append((m["rect"], os.path.join(r, "crops", "%s_new.png" % name)))
    report, bad = [], 0
    for page, crops in sorted(by_page.items()):
        _, _, probs = compose(g, page, crops, os.path.join(r, "pages"))
        kept = [i.name for i in on_page(g, page) if i.name not in man]
        report.append("%s %s: %d of ours, EA's kept: %s" % ("FAIL" if probs else "ok  ", page, len(crops),
                                                         ", ".join(kept) or "-"))
        report += ["     " + p for p in probs]
        bad += bool(probs)
    with open(os.path.join(r, "checks.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))
    return bad


def main(argv):
    ap = argparse.ArgumentParser(prog="python3 -m sagekit icons", description=__doc__.split("\n")[0])
    ap.add_argument("faction")
    ap.add_argument("--map", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--samples", type=int)
    ap.add_argument("--who", default="new,ea")
    for x in ("stage", "install", "revert"):
        ap.add_argument("--" + x, action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.map:
        return show_map(a.faction)
    if a.stage or a.install or a.revert:
        from . import install
        return install.main(a.faction, "stage" if a.stage else "install" if a.install else "revert", a.dry_run)
    if a.render:
        from .render import run
        run(a.faction, set(a.only.split(",")) if a.only else None, tuple(a.who.split(",")), a.samples)
    g = Install()
    man = manifest(a.faction, g)
    with open(os.path.join(root(a.faction), "icons.json"), "w") as fh:
        json.dump(man, fh, indent=1)
    grade(a.faction, g, man)
    bad = build_pages(a.faction, g, man)
    from .sheet import review
    print("review sheet:", review(a.faction, g, man))
    return 1 if bad else 0
