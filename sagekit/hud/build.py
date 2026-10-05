"""Build the HUD textures (docs/HUD.md): extract EA's, upscale, paint, write TGAs, double the geometry,
check everything.

build/assets/_hud/
    src/<key>.tga, <key>.png          EA's texture as the game loads it, and decoded
    up/<key>_x4.png, _a4.png, _a2.png Real-ESRGAN 4x colour; EA's alpha Lanczos 4x and 2x
    paint/<key>_4.png, _2.png, _1.png ours at 4x (review), 2x and 1x
    1x/art/textures/apt_*.tga         what --install --1x ships: EA's size, EA's alpha exactly
    2x/art/textures/apt_*.tga         what --install ships: twice the size ...
    2x/<movie>_geometry/*.ru          ... with every texture matrix sampling them doubled
    checks.txt, paint.txt             the checks and the ring measurements
"""
import json
import os
import subprocess

from .. import paths, texrecords
from ..icons import pixels
from ..pipeline import REALESRGAN
from . import root, spritecheck, table, tga
from .apt import Apt, geometry, images, matrices, retina

MAGICK = pixels.MAGICK


def specs():
    """[(movie, texture id, spec, key, member)] of the table."""
    frames, key, member = table()
    return [(mv, tid, spec, key(mv, tid), member(mv, tid)) for (mv, tid), spec in sorted(frames.items())]


def d(*parts):
    p = os.path.join(root(), *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def extract(apt):
    for mv, tid, spec, key, member in specs():
        data = apt.read(member)
        src = d("src", key + ".tga")
        if not os.path.exists(src) or open(src, "rb").read() != data:
            with open(src, "wb") as fh:
                fh.write(data)
            pixels.write(d("src", key + ".png"), *tga.decode(data))
            for f in ("_x4", "_a4", "_a2"):
                if os.path.exists(d("up", key + f + ".png")):
                    os.remove(d("up", key + f + ".png"))


def upscale():
    """Real-ESRGAN sees the colour only; the alpha is resized on its own (sagekit/alpha.py does the same)."""
    if not os.path.exists(REALESRGAN):
        raise SystemExit("Real-ESRGAN not found at %s (see assets/README.md)" % REALESRGAN)
    for mv, tid, spec, key, member in specs():
        png = d("src", key + ".png")
        x4, a4, a2 = (d("up", key + f + ".png") for f in ("_x4", "_a4", "_a2"))
        if not os.path.exists(x4):
            colour = d("up", key + "_rgb.png")
            subprocess.check_call([MAGICK, png, "-alpha", "off", colour])
            subprocess.check_call([REALESRGAN, "-i", colour, "-o", x4, "-n", "realesrgan-x4plus",
                                   "-m", os.path.join(os.path.dirname(REALESRGAN), "models")],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for out, pct in ((a4, 400), (a2, 200)):
            if not os.path.exists(out):
                subprocess.check_call([MAGICK, png, "-alpha", "extract", "-filter", "Lanczos", "-resize",
                                       "%d%%" % pct, "-depth", "8", out])


def paint():
    textures = []
    for mv, tid, spec, key, member in specs():
        t = dict(name=key, kind=spec["kind"], ea=d("src", key + ".png"), x4=d("up", key + "_x4.png"),
                 alpha4=d("up", key + "_a4.png"), alpha2=d("up", key + "_a2.png"),
                 out4=d("paint", key + "_4.png"), out2=d("paint", key + "_2.png"), out1=d("paint", key + "_1.png"))
        if spec["kind"] == "frame":
            t.update(side=spec["side"], rings=[dict(name=n, centre=c, radii=r) for n, c, r in spec["rings"]])
        else:
            t.update(parts=[[list(r), s] for r, s in spec["parts"]], sharpen=0.2)
        textures.append(t)
    job = d("paint", "job.json")
    with open(job, "w") as fh:
        json.dump(dict(textures=textures, report=d("paint.txt")), fh, indent=1)
    res = subprocess.run([paths.blender_python(), "-m", "sagekit.paint.hud", job], cwd=paths.REPO,
                         env=dict(os.environ, PYTHONPATH=paths.REPO), capture_output=True, text=True)
    if res.returncode:
        raise SystemExit("painting failed:\n" + res.stderr[-3000:])
    print(res.stdout.rstrip())


def write_textures(apt):
    import shutil
    for res in ("1x", "2x"):                        # nothing stale ships (files() walks these)
        shutil.rmtree(os.path.join(root(), res), ignore_errors=True)
    for mv, tid, spec, key, member in specs():
        ea = apt.read(member)
        for size, f in (("1x", "_1"), ("2x", "_2")):
            w, h, rgba = pixels.read(d("paint", key + f + ".png"))
            path = d(size, *member.split("\\"))
            with open(path, "wb") as fh:
                fh.write(tga.encode(ea, w, h, rgba))
    for mv in sorted({s[0] for s in specs()}):
        doubled, n = retina(apt, mv, {s[1] for s in specs() if s[0] == mv})
        for member, data in doubled.items():
            with open(d("2x", *member.split("\\")), "wb") as fh:
                fh.write(data)
        print("%s: %d texture styles in %d geometry files doubled" % (mv, n, len(doubled)))


def files(res):
    """{archive member: path} of what a `res` install ships ("1x" or "2x")."""
    base = os.path.join(root(), res)
    out = {}
    for dirpath, _, names in os.walk(base):
        for n in names:
            p = os.path.join(dirpath, n)
            out["\\".join(os.path.relpath(p, base).split(os.sep))] = p
    return out


def _alpha(rgba):
    return rgba[3::4]


def check(apt):
    """Problems, one line each: the textures keep EA's header layout and alpha; the 2x geometry
    doubles exactly the styles sampling our textures and keeps every texel inside the texture."""
    lines, bad = [], 0

    def say(ok, text):
        nonlocal bad
        bad += not ok
        lines.append(("ok   " if ok else "FAIL ") + text)

    for mv, tid, spec, key, member in specs():
        ea = apt.read(member)
        ew, eh, ergba = tga.decode(ea)
        one = open(d("1x", *member.split("\\")), "rb").read()
        two = open(d("2x", *member.split("\\")), "rb").read()
        w1, h1, rgba1 = tga.decode(one)
        w2, h2, rgba2 = tga.decode(two)
        same = one[:17] == ea[:17] and one[17] & 0xF0 == ea[17] & 0xF0 and len(one) == len(ea)
        say(same, "%s 1x: EA's header (but 8 alpha bits) and size (%dx%d)" % (key, w1, h1))
        say(_alpha(rgba1) == _alpha(ergba), "%s 1x: alpha is EA's, byte for byte" % key)
        say((w2, h2) == (2 * ew, 2 * eh) and tga.info(two)[2:4] == tga.info(ea)[2:4]
            and tga.info(two)[4] & 0xF0 == tga.info(ea)[4] & 0xF0 and tga.alpha_bits(two) == 8,
            "%s 2x: %dx%d, EA's format, 8 alpha bits" % (key, w2, h2))
        a2 = _alpha(rgba2)
        worst = total = n = 0
        for y in range(eh):
            for x in range(0, ew, 3):
                i = (2 * y * w2 + 2 * x)
                diff = abs((a2[i] + a2[i + 1] + a2[i + w2] + a2[i + w2 + 1]) / 4 - ergba[(y * ew + x) * 4 + 3])
                worst, total, n = max(worst, diff), total + diff, n + 1
        # Lanczos rings by a few steps at a hard cut-out edge; on average it is EA's alpha
        say(total / n <= 1.0 and worst <= 64, "%s 2x: alpha box-filtered to 1x is EA's (mean %.2f, at most %d of 255)" % (
            key, total / n, worst))
    for mv in sorted({s[0] for s in specs()}):
        ours = {s[1] for s in specs() if s[0] == mv}
        imgs = images(apt, mv)
        size = {}
        for tid in ours:
            w, h = tga.info(apt.read(table()[2](mv, tid)))[:2]
            size[tid] = (w, h)
        for member, data in geometry(apt, mv, own=True).items():
            path = d("2x", *member.split("\\"))
            new = open(path, "rb").read() if os.path.exists(path) else data
            old_m, new_m = matrices(data.decode("latin-1")), matrices(new.decode("latin-1"))
            for (img, a), (img2, b) in zip(old_m, new_m):
                want = tuple(2 * v for v in a) if imgs.get(img) in ours else a
                if img != img2 or any(abs(x - y) > 1e-4 * max(1, abs(x)) for x, y in zip(want, b)):
                    say(False, "%s %s: image %d's matrix %s, want %s" % (mv, member, img, b, want))
            if imgs and any(imgs.get(i) in ours for i, _ in old_m):
                texels = _texel_bounds(new.decode("latin-1"), imgs, ours)
                for tid, (lo_u, lo_v, hi_u, hi_v) in texels.items():
                    w, h = size[tid]
                    if lo_u < -1 or lo_v < -1 or hi_u > 2 * w + 1 or hi_v > 2 * h + 1:
                        say(False, "%s %s: samples texels (%.0f, %.0f)-(%.0f, %.0f) of a %dx%d texture" % (
                            mv, member, lo_u, lo_v, hi_u, hi_v, 2 * w, 2 * h))
        say(True, "%s: every texture matrix sampling %s checked" % (mv, sorted(ours)))
        pairs = {tid: (apt.read(table()[2](mv, tid)), open(d("2x", *table()[2](mv, tid).split("\\")), "rb").read())
                 for tid in ours}
        n = spritecheck.check(apt, mv, pairs, say)
        say(True, "%s: %d sprites' sampled alpha compared with EA's" % (mv, n))
    for res in ("1x", "2x"):
        say(*texrecords.check(list(files(res)), "the %s pack" % res))
    with open(d("checks.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return lines, bad


def _texel_bounds(text, imgs, ours):
    """{texture id: (min u, min v, max u, max v)} in texels over the triangles each style draws."""
    out, cur = {}, None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("s "):
            m = matrices(line)
            cur = (imgs.get(m[0][0]), m[0][1]) if m and imgs.get(m[0][0]) in ours else None
        elif line.startswith("t ") and cur:
            tid, (a, b, c, dd, tx, ty) = cur
            v = [float(x) for x in line[2:].split(":")]
            for x, y in zip(v[0::2], v[1::2]):
                u, w = a * x + c * y + tx, b * x + dd * y + ty
                lo_u, lo_v, hi_u, hi_v = out.get(tid, (u, w, u, w))
                out[tid] = (min(lo_u, u), min(lo_v, w), max(hi_u, u), max(hi_v, w))
    return out


def run():
    apt = Apt()
    extract(apt)
    upscale()
    paint()
    write_textures(apt)
    lines, bad = check(apt)
    print("\n".join(lines))
    return bad
