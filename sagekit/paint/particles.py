"""Still frames of a particle system, EA's and ours side by side (sagekit/fx/preview.py's renderer).

Runs on Blender's Python (numpy): python -m sagekit.paint.particles <job.json>. The job lists panels;
each panel is one or more systems (a master and its slaves, as sagekit/fx/preview.py `params` reads
them from the INI) drawn at a few ages into one strip of tiles, written as a binary PPM.

An approximation of the game's sprites, not its renderer: emission (volume, velocity, burst count
and delay, initial delay, system lifetime), per-frame physics (velocity damping, gravity, drift),
size, size rate and damping, rotation, the Color and Alpha keyframes, additive or alpha blending,
ground-aligned sprites; the first cell of a flip-book (GpuDraw). Wind, turbulence, per-particle
attached systems, volume particles, ColorScale and model particles (RenderObjectDraw: a disc in their
colour) are left out. EA's and our copy are drawn from the same random draws, so only colour differs.
"""
import json
import math
import sys

import numpy as np

ELEV = math.radians(35.0)               # the camera's elevation: about the game's RTS view
BG = np.array([0.20, 0.19, 0.16])        # terrain-like ground behind glows (additive)
LIGHT = np.array([0.46, 0.44, 0.38])     # a sunlit ground behind smoke (alpha), so dark plumes show


def rng_range(rng, pair, n):
    lo, hi = sorted(pair)
    return rng.uniform(lo, hi, n) if hi != lo else np.full(n, float(lo))


def keyed(keys, age, default):
    """Linear keyframes [(frame, *values)] at ages (n,); before the first key its value."""
    if not keys:
        return np.tile(np.array(default, float), (len(age), 1))
    keys = sorted(keys, key=lambda k: k[0])
    frames = np.array([k[0] for k in keys], float)
    vals = np.array([k[1:] for k in keys], float)
    out = np.empty((len(age), vals.shape[1]))
    for c in range(vals.shape[1]):
        out[:, c] = np.interp(age, frames, vals[:, c])
    return out


def emit(s, rng, n):
    """(positions, velocities) of n new particles."""
    vol, vel = s["vol"], s["vel"]
    t = vol.get("type", "point")
    if t == "line":
        a, b = np.array(vol.get("start", [0, 0, 0]), float), np.array(vol.get("end", [0, 0, 0]), float)
        pos = a + (b - a) * rng.uniform(0, 1, (n, 1))
    elif t == "box":
        h = np.array(vol.get("half", [0, 0, 0]), float)
        pos = rng.uniform(-1, 1, (n, 3)) * h
    elif t == "sphere":
        d = rng.normal(size=(n, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
        r = vol.get("radius", 0.0) * (np.ones((n, 1)) if vol.get("hollow") else rng.uniform(0, 1, (n, 1)) ** (1 / 3))
        pos = d * r
    elif t == "cylinder":
        ang = rng.uniform(0, 2 * math.pi, n)
        r = vol.get("radius", 0.0) * (np.ones(n) if vol.get("hollow") else np.sqrt(rng.uniform(0, 1, n)))
        pos = np.stack([np.cos(ang) * r, np.sin(ang) * r, rng.uniform(0, 1, n) * vol.get("length", 0.0)], 1)
    else:
        pos = np.zeros((n, 3))
    pos = pos + np.array(vol.get("offset", [0, 0, 0]), float)
    k = vel.get("type", "ortho")
    if k == "ortho":
        v = np.stack([rng_range(rng, vel.get(a, [0, 0]), n) for a in "xyz"], 1)
    elif k in ("spherical", "hemispherical"):
        d = rng.normal(size=(n, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
        if k == "hemispherical":
            d[:, 2] = np.abs(d[:, 2])
        v = d * rng_range(rng, vel.get("speed", [0, 0]), n)[:, None]
    elif k == "cylindrical":
        ang = rng.uniform(0, 2 * math.pi, n)
        rad = rng_range(rng, vel.get("radial", [0, 0]), n)
        v = np.stack([np.cos(ang) * rad, np.sin(ang) * rad, rng_range(rng, vel.get("normal", [0, 0]), n)], 1)
    elif k == "outward":
        d = pos - np.array(vol.get("offset", [0, 0, 0]), float)
        norm = np.linalg.norm(d, axis=1, keepdims=True)
        rnd = rng.normal(size=(n, 3))
        d = np.where(norm > 1e-6, d / np.maximum(norm, 1e-6), rnd / (np.linalg.norm(rnd, axis=1, keepdims=True) + 1e-9))
        v = d * rng_range(rng, vel.get("speed", [0, 0]), n)[:, None]
        v[:, 2] += rng_range(rng, vel.get("other", [0, 0]), n)
    else:
        v = np.zeros((n, 3))
    return pos, v


def simulate(s, until, seed):
    """Particles alive at frame `until`: dict of arrays (pos, size, angle, age, life, alpha keys)."""
    rng = np.random.default_rng(seed)
    parts = dict(pos=np.zeros((0, 3)), vel=np.zeros((0, 3)), size=np.zeros(0), rate=np.zeros(0), damp=np.zeros(0),
                 vdamp=np.zeros(0), angle=np.zeros(0), spin=np.zeros(0), age=np.zeros(0), life=np.zeros(0),
                 akey=np.zeros(0))
    start = rng_range(rng, s["initial_delay"], 1)[0]
    next_burst = start
    syslife = s["system_lifetime"]
    for f in range(int(until) + 1):
        if parts["age"].size:
            p = parts
            p["vel"] *= p["vdamp"][:, None]
            p["vel"][:, 2] -= s["gravity"]
            p["pos"] += p["vel"] + np.array(s["drift"], float)
            p["size"] = np.maximum(p["size"] + p["rate"], 0)
            p["rate"] *= p["damp"]
            p["angle"] += p["spin"]
            p["age"] += 1
            keep = p["age"] < p["life"]
            for k in p:
                p[k] = p[k][keep]
        if f >= next_burst and (syslife <= 0 or f - start < syslife):
            n = int(round(rng_range(rng, s["burst_count"], 1)[0]))
            if n > 0:
                pos, vel = emit(s, rng, n)
                new = dict(pos=pos, vel=vel, size=rng_range(rng, s["size"], n),
                           rate=rng_range(rng, s["size_rate"], n), damp=rng_range(rng, s["size_damp"], n),
                           vdamp=rng_range(rng, s["vel_damp"], n), angle=rng_range(rng, s["angle_z"], n),
                           spin=rng_range(rng, s["ang_rate_z"], n), age=np.zeros(n),
                           life=np.maximum(rng_range(rng, s["lifetime"], n), 1), akey=rng.uniform(0, 1, n))
                new["size"] += rng_range(rng, s["start_size_rate"], n)
                for k in parts:
                    parts[k] = np.concatenate([parts[k], new[k]])
            delay = rng_range(rng, s["burst_delay"], 1)[0]
            next_burst = f + max(1, int(round(delay))) if delay > 0 else f + 1
    return parts


def project(pos, scale, w, h, cy):
    x = pos[:, 0] * scale + w / 2
    y = cy - (pos[:, 2] * math.cos(ELEV) + pos[:, 1] * math.sin(ELEV)) * scale
    return x, y


def load_texture(s):
    t = s.get("tex")
    if not t:
        yy, xx = np.mgrid[-1:1:64j, -1:1:64j]
        a = np.clip(1 - np.hypot(xx, yy), 0, 1)
        return np.dstack([a, a, a, np.ones_like(a)])
    raw = np.fromfile(t["path"], dtype=np.uint8).reshape(t["h"], t["w"], 4).astype(float) / 255.0
    cells = s.get("cells")
    if cells:                                               # a flip-book: its first cell
        cw = t["w"] // cells
        raw = raw[:cw, :cw]
    return raw


def draw(canvas, s, parts, scale, cy, tex):
    h, w, _ = canvas.shape
    if not parts["age"].size:
        return
    order = np.argsort(-parts["age"])                       # oldest first
    x, y = project(parts["pos"], scale, w, h, cy)
    col = keyed(s["colors"], parts["age"], [0, 0, 0]) / 255.0
    if s["alphas"]:
        lo = keyed([(k[0], k[1]) for k in s["alphas"]], parts["age"], [0])[:, 0]
        hi = keyed([(k[0], k[2]) for k in s["alphas"]], parts["age"], [0])[:, 0]
        alpha = lo + (hi - lo) * parts["akey"]
    else:
        alpha = np.ones(parts["age"].size)
    th, tw = tex.shape[:2]
    shader = s["shader"]
    for i in order[-3000:]:
        r = parts["size"][i] * scale / 2
        if r < 0.5:
            continue
        ry = r * (math.sin(ELEV) if s["ground"] else 1.0)
        x0, x1 = int(max(0, x[i] - r)), int(min(w, x[i] + r + 1))
        y0, y1 = int(max(0, y[i] - ry)), int(min(h, y[i] + ry + 1))
        if x0 >= x1 or y0 >= y1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        u, v = (xx - x[i]) / r, (yy - y[i]) / ry
        ca, sa = math.cos(parts["angle"][i]), math.sin(parts["angle"][i])
        u, v = u * ca - v * sa, u * sa + v * ca
        inside = (np.abs(u) <= 1) & (np.abs(v) <= 1)
        tx = np.clip(((u + 1) / 2 * (tw - 1)).astype(int), 0, tw - 1)
        ty = np.clip(((v + 1) / 2 * (th - 1)).astype(int), 0, th - 1)
        texel = tex[ty, tx]
        rgb = texel[..., :3] * col[i]
        a = texel[..., 3] * inside
        dst = canvas[y0:y1, x0:x1]
        if shader == "ADDITIVE":
            dst += rgb * a[..., None]
        else:
            a = a * alpha[i]
            if shader == "ALPHA_TEST":
                a = (a > 0.5).astype(float)
            dst[:] = dst * (1 - a[..., None]) + rgb * a[..., None]


def bounds(parts_list, frames_sizes):
    pts = [p["pos"] for p in parts_list if p["age"].size]
    sizes = [p["size"] for p in parts_list if p["age"].size]
    if not pts:
        return 1.0, 0.0, 0.0, 1.0
    pos, size = np.concatenate(pts), np.concatenate(sizes)
    sx = np.abs(pos[:, 0]) + size / 2
    sy = pos[:, 2] * math.cos(ELEV) + pos[:, 1] * math.sin(ELEV)
    return float(np.percentile(sx, 98)), float(np.percentile(sy - size / 2, 2)), float(np.percentile(sy + size / 2, 98)), 1.0


def render(panel):
    w, h = panel["tile"]
    systems = panel["systems"]                              # [(EA's, ours)] master first
    frames = panel["frames"]
    sims = {}
    for which in (0, 1):
        for j, pair in enumerate(systems):
            for t in frames:
                sims[(which, j, t)] = simulate(pair[which], t, panel["seed"] + j)
    half, lo, hi, _ = bounds(list(sims.values()), None)
    span = max(2 * half, hi - lo, 1e-3)
    scale = 0.86 * min(w, h) / span
    cy = h / 2 + (lo + hi) / 2 * scale
    tiles = []
    for which in (0, 1):
        for t in frames:
            canvas = np.tile(BG if systems[0][0]["shader"] == "ADDITIVE" else LIGHT, (h, w, 1)).astype(float)
            for j, pair in enumerate(systems):
                s = pair[which]
                draw(canvas, s, sims[(which, j, t)], scale, cy, load_texture(s))
            tiles.append(np.clip(canvas, 0, 1))
    gap = np.tile(np.array([0.08, 0.08, 0.08]), (h, 6, 1))
    row = []
    for k, tile in enumerate(tiles):
        row.append(tile)
        row.append(gap if k != len(frames) - 1 else np.tile(np.array([0.9, 0.9, 0.9]), (h, 6, 1)))
    img = np.concatenate(row[:-1], 1)
    out = (img * 255 + 0.5).astype(np.uint8)
    with open(panel["out"], "wb") as fh:
        fh.write(b"P6\n%d %d\n255\n" % (out.shape[1], out.shape[0]))
        fh.write(out.tobytes())
    return dict(scale=scale)


def main():
    job = json.load(open(sys.argv[1]))
    out = [render(p) for p in job["panels"]]
    json.dump(out, open(sys.argv[1] + ".out", "w"))


if __name__ == "__main__":
    main()
