"""Build 2x pages: extract EA's, upscale each rect, compose, write the DDS the way EA's is, check.

build/assets/_ui2x/
    src/<page>.dds, .png            EA's page as the game reads it, and decoded
    up/in/<page>__l_t_r_b.png       a rect padded and bled (sagekit/paint/ui2x.py prep)
    up/x4/<page>__l_t_r_b.png       Real-ESRGAN 4x of it (cached: delete to redo)
    pages/<page>/<mip>.png          our 2x page and its mips
    pages/<page>.dds                what ships: EA's format (an uncompressed page becomes DXT5),
                                    twice EA's size, one mip more than EA's
    report/<page>.json              per rect: colour and alpha error against EA's at 1x
"""
import json
import os
import shutil
import struct
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

from .. import paths
from ..icons import pages as ipages
from ..icons import pixels
from ..pipeline import REALESRGAN
from . import root

ERR_COLOUR = 0.06       # mean colour error (0..1) a rect may have against EA's, back at 1x (EA's DXT noise removed counts)
ERR_ALPHA = 0.04
SHARPEN_OWN = {"portrait": 0.35, "button": 0.25}     # half the grade's (sagekit/paint/icons.py) at 1x


def key(page, rect):
    return "%s__%d_%d_%d_%d" % ((page,) + tuple(rect))


def blender_py(stage, job):
    path = root("jobs", "%s-%d.json" % (stage, os.getpid() if stage == "prep" else hash(job["report"]) & 0xffff))
    with open(path, "w") as fh:
        json.dump(job, fh)
    res = subprocess.run([paths.blender_python(), "-m", "sagekit.paint.ui2x", stage, path], cwd=paths.REPO,
                         env=dict(os.environ, PYTHONPATH=paths.REPO), capture_output=True, text=True)
    if res.returncode:
        raise SystemExit("ui2x %s failed:\n%s" % (stage, res.stderr[-3000:]))


def upscale(inputs):
    """Real-ESRGAN 4x of every input not done yet, in one run."""
    todo = [p for p in inputs if not os.path.exists(p.replace(os.sep + "in" + os.sep, os.sep + "x4" + os.sep))]
    if not todo:
        return
    if not os.path.exists(REALESRGAN):
        raise SystemExit("Real-ESRGAN not found at %s (see assets/README.md)" % REALESRGAN)
    with tempfile.TemporaryDirectory(dir=root()) as tmp:
        src, dst = os.path.join(tmp, "in"), os.path.join(tmp, "out")
        os.makedirs(src)
        os.makedirs(dst)
        for p in todo:
            shutil.copyfile(p, os.path.join(src, os.path.basename(p)))
        subprocess.check_call([REALESRGAN, "-i", src, "-o", dst, "-n", "realesrgan-x4plus", "-f", "png",
                               "-m", os.path.join(os.path.dirname(REALESRGAN), "models")],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for p in todo:
            out = os.path.join(dst, os.path.basename(p))
            if not os.path.exists(out):
                raise SystemExit("Real-ESRGAN wrote nothing for %s" % p)
            shutil.move(out, p.replace(os.sep + "in" + os.sep, os.sep + "x4" + os.sep))
    print("Real-ESRGAN: %d rects upscaled" % len(todo))


def level_bytes(w, h):
    return max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * 16


def header(ea, w, h, mips):
    """EA's header with our size and mip count; an uncompressed page's becomes a DXT5 header."""
    i = ipages.info(ea)
    if i["fourcc"] in ("DXT3", "DXT5"):
        hd = bytearray(ea[:ipages.HEADER])
        struct.pack_into("<IIII", hd, 12, h, w, level_bytes(w, h), 0)
        struct.pack_into("<I", hd, 28, mips)
        return bytes(hd)
    hd = bytearray(ipages.HEADER)
    hd[0:4] = b"DDS "
    struct.pack_into("<7I", hd, 4, 124, 0xA1007, h, w, level_bytes(w, h), 0, mips)
    struct.pack_into("<2I4s", hd, 76, 32, 0x4, b"DXT5")
    struct.pack_into("<I", hd, 108, 0x401008)
    return bytes(hd)


def encode_level(png, tmp):
    out = os.path.join(tmp, os.path.basename(png) + ".dds")
    subprocess.check_call([pixels.MAGICK, png, "-define", "dds:compression=dxt5", "-define", "dds:mipmaps=0",
                           "-define", "dds:cluster-fit=true", "-define", "dds:weight-by-alpha=false", out])
    return open(out, "rb").read()[ipages.HEADER:]


def write_dds(ea_dds, level_dir, mips, out):
    ea = open(ea_dds, "rb").read()
    i = ipages.info(ea)
    w, h = 2 * i["width"], 2 * i["height"]
    body = []
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(mips):
            lw, lh = max(1, w >> k), max(1, h >> k)
            data = encode_level(os.path.join(level_dir, "%d.png" % k), tmp)
            if len(data) != level_bytes(lw, lh):
                raise SystemExit("%s mip %d: %d bytes for %dx%d" % (out, k, len(data), lw, lh))
            body.append(data)
    data = header(ea, w, h, mips) + b"".join(body)
    if i["fourcc"] == "DXT3":
        data = ipages.as_dxt3(data)
    with open(out, "wb") as fh:
        fh.write(data)
    return out


def check_dds(ea_dds, dds, top_png):
    """Problems with a 2x page: twice EA's size, one mip more, EA's format (DXT5 for an
    uncompressed one), the top level the intended pixels within DXT's error."""
    ea, ours = ipages.info(open(ea_dds, "rb").read()), ipages.info(open(dds, "rb").read())
    probs = []
    want = dict(width=2 * ea["width"], height=2 * ea["height"], mips=ea["mips"] + 1,
                fourcc=ea["fourcc"] if ea["fourcc"] in ("DXT3", "DXT5") else "DXT5")
    if ours != want:
        probs.append("header %s, want %s" % (ours, want))
    n = os.path.getsize(dds) - ipages.HEADER
    if n != sum(level_bytes(max(1, want["width"] >> k), max(1, want["height"] >> k)) for k in range(want["mips"])):
        probs.append("%d bytes of blocks for the header's chain" % n)
    _, _, mean = pixels.differ(pixels.read(top_png), pixels.read(dds), visible=True)
    if mean > 8:                                # DXT on busy 2x detail: EA's own pages err as much
        probs.append("the encoded page is off our pixels by %.1f on average" % mean)
    return probs


def build(spec, workers=6):
    """spec: {page: {mips, rects: [{rect, kind, own (4x crop or None)}]}} -> ({page: dds}, problems).
    EA's page is read from the pristine game."""
    from ..game import Install
    g = Install()
    jobs = []
    for page, s in sorted(spec.items()):
        ea_dds, ea_png = ipages.extract(g, page, root("src"))
        rects = sorted(s["rects"], key=lambda rc: bool(rc.get("own")))        # ours last: they win
        for rc in rects:
            k = key(page, rc["rect"])
            rc.update(input=root("up", "in", k + ".png"), x4=root("up", "x4", k + ".png"))
        jobs.append(dict(name=page, src=ea_png, ea_dds=ea_dds, mips=s["mips"], out=root("pages", page, "x"),
                         rects=rects))
    for pg in jobs:
        pg["out"] = os.path.dirname(pg["out"])
    need = [pg for pg in jobs if any(not rc.get("own") and not os.path.exists(rc["x4"]) for rc in pg["rects"])]
    if need:
        blender_py("prep", dict(pages=need))
    upscale([rc["input"] for pg in jobs for rc in pg["rects"] if not rc.get("own")])
    chunks = [jobs[k::workers] for k in range(workers)]
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda ch: ch and blender_py("finish", dict(pages=ch, sharpen_own=SHARPEN_OWN,
                                                                report=root("report", "%s.json" % ch[0]["name"]))),
                    chunks))
    report = {}
    for ch in chunks:
        if ch:
            report.update(json.load(open(root("report", "%s.json" % ch[0]["name"]))))
    out, probs = {}, []

    def one(pg):
        dds = write_dds(pg["ea_dds"], pg["out"], pg["mips"], root("pages", pg["name"] + ".dds"))
        p = check_dds(pg["ea_dds"], dds, os.path.join(pg["out"], "0.png"))
        for rect, err, aerr, own, _, _ in report[pg["name"]]:
            if not own and err > ERR_COLOUR:
                p.append("rect %s: off EA's picture by %.3f at 1x" % (rect, err))
            if aerr > ERR_ALPHA:
                p.append("rect %s: alpha off EA's by %.3f at 1x" % (rect, aerr))
        return pg["name"], dds, p

    with ThreadPoolExecutor(workers) as ex:
        for name, dds, p in ex.map(one, jobs):
            out[name] = dds
            probs += ["%s: %s" % (name, x) for x in p]
    with open(root("checks.txt"), "w") as fh:
        fh.write("\n".join(probs or ["ok: %d pages" % len(out)]) + "\n")
    return out, probs
