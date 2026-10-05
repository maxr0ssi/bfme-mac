"""A building's fire drawn over its render (sagekit/fire_review.py's renderer; the fire budget's review).

Runs on Blender's Python (numpy): python -m sagekit.paint.fire_composite <job.json>. Each tile of the
job is a render (raw RGB), the camera that made it (a Building view: target, distance, elevation,
azimuth, lens, as sagekit/blender/render.py sets it) and emitters: a model-space point and the
particle systems burning there (sagekit/fx/preview.py `params`). Every system is simulated to its
steady state (sagekit/paint/particles.py, the same random draws for every tile) and each live
particle drawn as a camera-facing sprite at its perspective size, every particle back to front
(additive ones added, alpha ones blended over what is behind them). No depth test: a fire behind a wall shows through it. An approximation of
the game's sprites (no wind, no ColorScale); the in-game look is Max's check.
"""
import json
import math
import sys

import numpy as np

from .particles import keyed, load_texture, simulate


def camera(view, size):
    """(eye, forward, right, up, focal px) of a view (fire_checks.project's camera)."""
    t, dist, elev, azim, lens = view
    e, a = math.radians(elev), math.radians(azim)
    eye = np.array(t, float) + dist * np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    f = np.array(t, float) - eye
    f /= np.linalg.norm(f)
    rt = np.array([f[1], -f[0], 0.0])
    rt /= np.linalg.norm(rt)
    up = np.cross(rt, f)
    return eye, f, rt, up, lens / 36.0 * max(size)


def steady(s):
    """A frame by which the system has reached its steady state."""
    return int(max(s["lifetime"]) * 2 + max(s["burst_delay"]) * 2 + 30)


def sprites(canvas, cam, s, parts, tex, alpha_list):
    """Queue (depth, ...) every live particle's sprite for drawing back to front."""
    eye, f, rt, up, k = cam
    h, w, _ = canvas.shape
    if not parts["age"].size:
        return
    d = parts["pos"] - eye
    z = d @ f
    x = w / 2 + k * (d @ rt) / np.maximum(z, 1e-3)
    y = h / 2 - k * (d @ up) / np.maximum(z, 1e-3)
    col = keyed(s["colors"], parts["age"], [0, 0, 0]) / 255.0
    if s["alphas"]:
        lo = keyed([(a[0], a[1]) for a in s["alphas"]], parts["age"], [0])[:, 0]
        hi = keyed([(a[0], a[2]) for a in s["alphas"]], parts["age"], [0])[:, 0]
        alpha = lo + (hi - lo) * parts["akey"]
    else:
        alpha = np.ones(parts["age"].size)
    for i in range(parts["age"].size):
        if z[i] <= 1:
            continue
        r = parts["size"][i] / 2 * k / z[i]
        if r < 0.5:
            continue
        alpha_list.append((z[i], x[i], y[i], r, parts["angle"][i], col[i], alpha[i], tex, s["shader"]))


def paint(canvas, x, y, r, angle, col, alpha, tex, shader):
    h, w, _ = canvas.shape
    e = r * 1.415                                           # a rotated square reaches r * sqrt(2)
    x0, x1 = int(max(0, x - e)), int(min(w, x + e + 1))
    y0, y1 = int(max(0, y - e)), int(min(h, y + e + 1))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    u, v = (xx - x) / r, (yy - y) / r
    ca, sa = math.cos(angle), math.sin(angle)
    u, v = u * ca - v * sa, u * sa + v * ca
    inside = (np.abs(u) <= 1) & (np.abs(v) <= 1)
    th, tw = tex.shape[:2]
    texel = tex[np.clip(((v + 1) / 2 * (th - 1)).astype(int), 0, th - 1), np.clip(((u + 1) / 2 * (tw - 1)).astype(int), 0, tw - 1)]
    rgb = texel[..., :3] * col
    a = texel[..., 3] * inside
    dst = canvas[y0:y1, x0:x1]
    if shader == "ADDITIVE":
        dst += rgb * a[..., None]
    else:
        a = a * alpha
        if shader == "ALPHA_TEST":
            a = (a > 0.5).astype(float)
        dst[:] = dst * (1 - a[..., None]) + rgb * a[..., None]


def render(tile, textures):
    w, h = tile["size"]
    canvas = np.fromfile(tile["bg"], dtype=np.uint8).reshape(h, w, 3).astype(float) / 255.0
    cam = camera(tile["view"], (w, h))
    queued = []
    for n, em in enumerate(tile["emitters"]):
        for j, s in enumerate(em["systems"]):
            parts = simulate(s, tile.get("frame") or steady(s), tile["seed"] + 101 * n + j)
            parts["pos"] = parts["pos"] + np.array(em["pos"], float)
            key = (s["tex"] or {}).get("path", "") + "|%s" % s.get("cells")
            if key not in textures:
                textures[key] = load_texture(s)
            sprites(canvas, cam, s, parts, textures[key], queued)
    for item in sorted(queued, key=lambda q: -q[0]):
        paint(canvas, *item[1:])
    out = (np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)
    with open(tile["out"], "wb") as fh:
        fh.write(b"P6\n%d %d\n255\n" % (w, h))
        fh.write(out.tobytes())


def main():
    job = json.load(open(sys.argv[1]))
    textures = {}
    for tile in job["tiles"]:
        render(tile, textures)


if __name__ == "__main__":
    main()
