"""The A100 offload (docs/OFFLOAD.md): a faction's full-quality builds on a machine without the
game (Google Colab), finished on the Mac.

    python3 -m sagekit offload pack <faction> [--only b1,b2] [--no-extract]    (Mac)
        extract each building from the game, then one zip: the code, the building list, the
        workspaces' inputs (src/, work/*.json), the faction's shared inputs (_house, _night,
        recoloured sheets, shared-sheet copies, the ownership index) and a game snapshot
        (sagekit/snapshot.py) -> build/offload/<faction>-<date>.zip
    python3 -m sagekit offload run [--builds N] [--only b1,b2]                   (Colab, unzipped)
        every building from geometry to render on the snapshot (a chained recipe from extract,
        after its base), N at once, Blender limited by SAGEKIT_BLENDER_SLOTS; a timing table
    python3 -m sagekit offload results [--with-bakes]                           (Colab)
        out/, work/ (bakes left out unless asked), renders/, src/ and cache/ of every building
        that built -> build/offload/<faction>-<date>-results.zip
    python3 -m sagekit offload unpack <results.zip> [--print-only]              (Mac)
        the results into build/, then `build <b> --from ship --to checks` for each on the real
        game (ship, shared, ini, cache from EA's files; checks verify)
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

from . import paths, registry, snapshot

OFFLOAD = os.path.join(paths.REPO, "build", "offload")
META = "_offload"                               # inside the zips: manifest, snapshot, results record
CODE = ["sagekit", "assets", os.path.join("tools", "bigtool.py")]
STORED = (".png", ".jpg", ".zip", ".blend")     # already compressed (or not worth it)
FINISH = ("ship", "checks")                     # the Mac's steps after unpack: on the real game
BLENDER_STEPS = ("geometry", "bake", "paint", "export", "night", "lifecycle", "checks", "render")


def _rel(p):
    return os.path.relpath(p, paths.REPO)


def _files(root, skip=lambda rel: False):
    """Every file under root (repo-relative), skipping caches and what `skip` says."""
    out = []
    for d, dirs, names in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x != "__pycache__")
        for n in sorted(names):
            p = os.path.join(d, n)
            if not n.endswith(".pyc") and n != ".DS_Store" and not skip(_rel(p)):
                out.append(p)
    return out


def _add(z, path, arc=None):
    arc = arc or _rel(path)
    z.write(path, arc, zipfile.ZIP_STORED if path.lower().endswith(STORED) else zipfile.ZIP_DEFLATED)


def order(ids):
    """Buildings with each chained recipe after its base (when the base is in the list)."""
    out, left = [], list(ids)
    while left:
        for bid in left:
            base = registry.load(bid).base
            if not base or base not in left:
                out.append(bid)
                left.remove(bid)
                break
    return out


def selected(faction, only=None):
    ids = [b for b in registry.building_ids() if b.startswith(faction + "/")]
    if only:
        want = [x.strip() for x in only.split(",") if x.strip()]
        bad = [w for w in want if "%s/%s" % (faction, w) not in ids]
        if bad:
            raise SystemExit("not %s buildings: %s" % (faction, ", ".join(bad)))
        ids = ["%s/%s" % (faction, w) for w in want]
    if not ids:
        raise SystemExit("no %s buildings under assets/" % faction)
    return order(ids)


# ------------------------------------------------------------------------------------ pack (Mac)
def pack(faction, only=None, extract=True):
    from .game import Install
    from .pipeline import Pipeline, StepFailed
    ids = selected(faction, only)
    bases = sorted({b for bid in ids for b in _chain(bid)[:-1] if b not in ids})
    if extract:
        for bid in ids:
            try:
                Pipeline(registry.load(bid)).run("extract", "extract")
            except StepFailed as e:
                raise SystemExit("extract %s failed (a chained recipe needs its base built here first):\n%s" % (bid, e))
    g = Install()
    from .ownership import load
    load(g)                                     # the ownership index current (packed; no rescan there)
    members = snapshot.collect(g, faction, [registry.load(b) for b in ids + bases])
    os.makedirs(OFFLOAD, exist_ok=True)
    out = os.path.join(OFFLOAD, "%s-%s.zip" % (faction, datetime.date.today().strftime("%Y%m%d")))
    fac = os.path.join(paths.BUILD, faction)
    sheets = {m for m in members if m.startswith("art\\compiledtextures\\")}
    manifest = {"faction": faction, "buildings": ids, "bases": bases, "created": time.strftime("%Y-%m-%d %H:%M"),
                "blender": _blender_version(), "w3d_addon": "OpenSAGE.BlenderPlugin v0.7.2"}
    with zipfile.ZipFile(out + ".tmp", "w", compresslevel=6) as z:
        for c in CODE:
            p = os.path.join(paths.REPO, c)
            for f in _files(p) if os.path.isdir(p) else [p]:
                _add(z, f)
        for bid in ids:                                 # inputs: EA's sources and extract's records
            ws = paths.work_dir(bid)
            for f in _files(os.path.join(ws, "src")) + sorted(
                    os.path.join(ws, "work", n) for n in os.listdir(os.path.join(ws, "work")) if n.endswith(".json")):
                _add(z, f)
        for bid in bases:                               # a base built here, not rebuilt there
            ws = paths.work_dir(bid)
            keep = re.compile(r"^(src|out|work/export)/|^work/[^/]+\.json$")
            for f in _files(ws, lambda rel, ws=ws: not keep.match(os.path.relpath(os.path.join(paths.REPO, rel), ws))):
                _add(z, f)
        for sub in ("_house", "_night", os.path.join("_sheets", "shared")):
            if os.path.isdir(os.path.join(fac, sub)):
                for f in _files(os.path.join(fac, sub)):
                    _add(z, f)
        recoloured = os.path.join(fac, "_sheets", "out")   # the faction's sheets the models draw (renders)
        for f in _files(recoloured) if os.path.isdir(recoloured) else []:
            if os.path.relpath(f, recoloured).replace(os.sep, "\\").lower() in sheets:
                _add(z, f)
        own = os.path.join(paths.BUILD, "_ownership.json")
        if os.path.exists(own):
            _add(z, own)
        with tempfile.TemporaryDirectory(dir=OFFLOAD) as tmp:
            game = os.path.join(tmp, "game")
            manifest["snapshot_bytes"] = snapshot.write(g, members, game)
            for f in _files(game):
                _add(z, f, "%s/game/%s" % (META, os.path.relpath(f, game).replace(os.sep, "/")))
        z.writestr("%s/manifest.json" % META, json.dumps(manifest, indent=1))
    os.replace(out + ".tmp", out)
    print("\n%s: %d buildings%s, %.1f MB" % (_rel(out), len(ids), " (+ bases %s as built here)" % ", ".join(bases)
                                              if bases else "", os.path.getsize(out) / 1e6))
    print("EA's files are inside (the snapshot, src/): keep it in your private Drive only.")
    return out


def _chain(bid):
    """bid and the bases it builds on, root first."""
    out = [bid]
    while registry.load(out[0]).base:
        out.insert(0, registry.load(out[0]).base)
    return out


def _blender_version():
    try:
        r = subprocess.run([paths.BLENDER, "--version"], capture_output=True, text=True, timeout=60)
        return r.stdout.splitlines()[0].strip()
    except (OSError, IndexError, subprocess.TimeoutExpired):
        return "unknown"


def manifest():
    p = os.path.join(paths.REPO, META, "manifest.json")
    if not os.path.exists(p):
        raise SystemExit("no %s: run this in an unpacked offload bundle" % _rel(p))
    return json.load(open(p))


# ------------------------------------------------------------------------------------ run (Colab)
STEP_RE = re.compile(r"^\[(\S+)\] (\w+)$")
TIME_RE = re.compile(r"^  \((\d+)s\)$")


def run(builds=4, only=None):
    """Every building of the bundle from geometry (extract for a chained recipe) to render."""
    m = manifest()
    ids = [b for b in m["buildings"] if not only or b.split("/")[1] in only.split(",")]
    env = dict(os.environ, PYTHONPATH=paths.REPO, PYTHONUNBUFFERED="1")
    env.setdefault(snapshot.ENV, os.path.join(paths.REPO, META, "game"))
    logs = os.path.join(OFFLOAD, "logs")
    os.makedirs(logs, exist_ok=True)
    print("%d buildings, %d at once, %s Blender slots, snapshot %s" % (
        len(ids), builds, env.get("SAGEKIT_BLENDER_SLOTS", "4"), _rel(env[snapshot.ENV])), flush=True)
    done, results = {}, {}

    def one(bid):
        base = registry.load(bid).base
        if base in done:
            done[base].result()                         # its base first (it holds no build slot meanwhile)
            if results[base]["status"] != "ok":
                results[bid] = {"status": "skipped (base %s failed)" % base, "steps": {}, "seconds": 0}
                return
        with slots:
            build(bid, base)

    def build(bid, base):
        first = "extract" if base else "geometry"
        log = os.path.join(logs, bid.replace("/", "_") + ".log")
        t = time.time()
        with open(log, "w") as fh:
            r = subprocess.run([sys.executable, "-m", "sagekit", "build", bid, "--from", first, "--to", "render", "--force"],
                               cwd=paths.REPO, env=env, stdout=fh, stderr=subprocess.STDOUT)
        results[bid] = {"status": "ok" if r.returncode == 0 else "FAILED", "seconds": round(time.time() - t),
                        "steps": _step_times(log), "log": _rel(log)}
        print("%-28s %-7s %5ds" % (bid, results[bid]["status"], results[bid]["seconds"]), flush=True)
    t0, slots = time.time(), threading.Semaphore(max(builds, 1))
    with ThreadPoolExecutor(len(ids)) as ex:            # a thread each; `slots` lets N build at once
        for bid in ids:
            done[bid] = ex.submit(one, bid)
        for f in done.values():
            f.result()
    table = timing_table(ids, results, time.time() - t0, builds, env.get("SAGEKIT_BLENDER_SLOTS", "4"))
    print("\n" + table)
    with open(os.path.join(OFFLOAD, "timings.md"), "w") as fh:
        fh.write(table + "\n")
    with open(os.path.join(OFFLOAD, "results.json"), "w") as fh:
        json.dump({"faction": m["faction"], "buildings": ids, "results": results}, fh, indent=1)
    return 0 if all(r["status"] == "ok" for r in results.values()) else 1


def _step_times(log):
    out, step = {}, None
    for line in open(log, errors="replace"):
        line = line.rstrip("\n")
        s, t = STEP_RE.match(line), TIME_RE.match(line)
        if s:
            step = s.group(2)
        elif t and step:
            out[step] = int(t.group(1))
    return out


def timing_table(ids, results, wall, builds, slots):
    cols = list(BLENDER_STEPS)
    head = "| building | status | total s | " + " | ".join(cols) + " | host |"
    rows = [head, "|" + "---|" * (len(cols) + 4)]
    for bid in ids:
        r = results.get(bid, {"status": "not run", "steps": {}, "seconds": 0})
        host = sum(v for k, v in r["steps"].items() if k not in cols)
        rows.append("| %s | %s | %d | %s | %d |" % (bid, r["status"], r["seconds"],
                                                     " | ".join(str(r["steps"].get(c, "")) for c in cols), host))
    rows.append("\nwall clock %.0f s for %d buildings (%d at once, %s Blender slots)" % (wall, len(ids), builds, slots))
    return "\n".join(rows)


def results_zip(with_bakes=False):
    """The built buildings' out/, work/, renders/, src/, cache/ and the run's logs, zipped."""
    rec = json.load(open(os.path.join(OFFLOAD, "results.json")))
    faction = rec["faction"]
    out = os.path.join(OFFLOAD, "%s-%s-results.zip" % (faction, datetime.date.today().strftime("%Y%m%d")))
    skip = re.compile(r"\.blend1$" + ("" if with_bakes else r"|/work/bake/"))
    with zipfile.ZipFile(out + ".tmp", "w", compresslevel=6) as z:
        for bid, r in rec["results"].items():
            if r["status"] == "ok":
                ws = paths.work_dir(bid)
                for sub in ("out", "work", "renders", "src", "cache"):
                    for f in _files(os.path.join(ws, sub), lambda rel: bool(skip.search(rel))):
                        _add(z, f)
        fac = os.path.join(paths.BUILD, faction)
        for sub in ("_night", os.path.join("_sheets", "shared")):   # made or redone here
            for f in _files(os.path.join(fac, sub)) if os.path.isdir(os.path.join(fac, sub)) else []:
                _add(z, f)
        for f in _files(OFFLOAD, lambda rel: rel.endswith(".zip") or rel.endswith(".tmp")):
            _add(z, f)
        z.writestr("%s/results.json" % META, json.dumps(dict(rec, bakes=with_bakes), indent=1))
    os.replace(out + ".tmp", out)
    print("%s: %.1f MB" % (_rel(out), os.path.getsize(out) / 1e6))
    return out


# ------------------------------------------------------------------------------------ unpack (Mac)
def unpack(path, print_only=False):
    with zipfile.ZipFile(path) as z:
        rec = json.loads(z.read("%s/results.json" % META))
        faction, ok = rec["faction"], [b for b, r in rec["results"].items() if r["status"] == "ok"]
        allowed = ("build/assets/%s/" % faction, "build/offload/")
        names = [n for n in z.namelist() if not n.startswith(META + "/")]
        bad = [n for n in names if not n.startswith(allowed) or ".." in n.split("/")]
        if bad:
            raise SystemExit("unexpected paths in %s: %s" % (path, bad[:5]))
        for bid in ok:                                  # its build replaces ours, as a local build would
            ws = paths.work_dir(bid)
            for sub in ("out", "work", "renders", "cache"):
                shutil.rmtree(os.path.join(ws, sub), ignore_errors=True)
        stem = os.path.splitext(os.path.basename(path))[0]
        for info in z.infolist():
            if info.filename.startswith(META + "/") or info.is_dir():
                continue
            name = info.filename
            if name.startswith("build/offload/"):         # the run's logs, kept per results zip
                name = "build/offload/%s/%s" % (stem, name[len("build/offload/"):])
            dest = os.path.join(paths.REPO, *name.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with z.open(info) as src, open(dest, "wb") as fh:
                shutil.copyfileobj(src, fh)
            ts = time.mktime(info.date_time + (0, 0, -1))
            os.utime(dest, (ts, ts))
    for bid, r in rec["results"].items():
        print("%-28s %s" % (bid, r["status"]))
    print("unpacked %d buildings into %s; logs and timings in build/offload/%s/" % (len(ok), _rel(paths.BUILD), stem))
    cmds = [[sys.executable, "-m", "sagekit", "build", bid, "--from", FINISH[0], "--to", FINISH[1]] for bid in ok]
    if print_only:
        print("\nthen, on the Mac (the game's files: ship, shared, ini, cache; checks verify):")
        print("\n".join("  python3 -m sagekit build %s --from %s --to %s" % (c[4], *FINISH) for c in cmds))
        return 0
    failed = []
    for c in cmds:
        print("\n$ python3 -m sagekit build %s --from %s --to %s" % (c[4], *FINISH), flush=True)
        if subprocess.run(c, cwd=paths.REPO).returncode:
            failed.append(c[4])
    print("\nfinished %d of %d%s" % (len(cmds) - len(failed), len(cmds), "; FAILED: " + ", ".join(failed) if failed else ""))
    return 1 if failed else 0


def main(a):
    if a.action in ("pack", "unpack") and not a.target:
        raise SystemExit("offload %s needs %s" % (a.action, "a faction" if a.action == "pack" else "the results zip"))
    if a.action == "pack":
        pack(a.target, a.only, extract=not a.no_extract)
    elif a.action == "run":
        return run(a.builds, a.only)
    elif a.action == "results":
        results_zip(a.with_bakes)
    elif a.action == "unpack":
        return unpack(a.target, a.print_only)
    return 0
