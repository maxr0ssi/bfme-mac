"""The FX review sheets: for each system of ours, EA's effect and ours as still frames at three ages
(an approximation of the game's sprites, sagekit/paint/particles.py), and the colour keys swatched.

    build/assets/_review_finish/fx/<faction>.jpg    one sheet per faction with an fx.py
    build/assets/_fx/preview/                        textures, panels and the job (scratch)

Blender cannot draw the game's particles; the frames show colour, texture and rough shape, not the
game's exact look (no wind, no per-particle systems, no ColorScale). The in-game check is Max's.
"""
import json
import os
import re
import subprocess

from .. import paths
from ..formats.textures import sheet_member
from . import blocks, install
from .tint import keyframes, lightness

OUT = os.path.join(paths.BUILD, "_review_finish", "fx")
WORK = os.path.join(paths.BUILD, "_fx", "preview")
TILE = (220, 220)
FONT = paths.FONT


def pair(v, default=(0.0, 0.0)):
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", v or "")]
    return [nums[0], nums[1] if len(nums) > 1 else nums[0]] if nums else list(default)


def vec(v):
    m = re.findall(r"[XYZ]:\s*(-?\d+(?:\.\d+)?)", v or "")
    return [float(x) for x in m] if len(m) == 3 else [0.0, 0.0, 0.0]


def texture(g, name, cache):
    """{path, w, h} of the texture as raw RGBA (converted once), or None for a model particle."""
    if not name or name.lower().endswith(".w3d"):
        return None
    if name.lower() in cache:
        return cache[name.lower()]
    member = sheet_member(g, name)
    if member is None:
        cache[name.lower()] = None
        return None
    os.makedirs(WORK, exist_ok=True)
    src = os.path.join(WORK, member.split("\\")[-1])
    with open(src, "wb") as fh:
        fh.write(g.read(member))
    raw = src + ".rgba"
    subprocess.check_call(["magick", src + "[0]", "-resize", "128x128!", "-depth", "8", "rgba:" + raw])
    cache[name.lower()] = dict(path=raw, w=128, h=128)
    return cache[name.lower()]


def params(rows, g, cache):
    """The renderer's view of a particle system's rows (sagekit/paint/particles.py)."""
    mods = {n.split("=")[0].strip().lower(): (n, {k: v for k, v, _ in f}) for n, f in blocks.modules_of(rows)}
    system = mods.get("system", ("", {}))[1]
    upd = mods.get("update", ("", {}))[1]
    phys = mods.get("physics", ("", {}))[1]
    vel_name, vel = mods.get("emissionvelocity", ("= OrthoEmissionVelocity", {}))
    vol_name, vol = mods.get("emissionvolume", ("= PointEmissionVolume", {}))
    draw = mods.get("draw", ("= DefaultDraw", {}))
    keys, _ = keyframes(rows)
    colors = [[f] + list(rgb) for _, rgb, f, _ in keys]
    if not any(c[0] == 0 for c in colors):
        colors.insert(0, [0, 0, 0, 0])
    alphas = []
    for k, v in mods.get("alpha", ("", {}))[1].items():
        if re.match(r"Alpha\d+$", k):
            n = [float(x) for x in v.split()[:3]]
            alphas.append([n[2], n[0], n[1]])
    if alphas and not any(a[0] == 0 for a in alphas):
        alphas.insert(0, [0, 0, 0])
    vt = vel_name.split("=")[-1].strip().replace("EmissionVelocity", "").lower()
    vo = vol_name.split("=")[-1].strip().replace("EmissionVolume", "").lower()
    shader = (system.get("Shader") or "ADDITIVE").split()[0].upper()
    tex = texture(g, (system.get("ParticleName") or "").split()[0] if system.get("ParticleName") else None, cache)
    cells = int(pair(draw[1].get("FramesPerRow"))[0]) if "GpuDraw" in draw[0] and draw[1].get("FramesPerRow") else None
    return dict(lifetime=pair(system.get("Lifetime"), (30, 30)), system_lifetime=pair(system.get("SystemLifetime"))[0],
                size=pair(system.get("Size"), (1, 1)), burst_count=pair(system.get("BurstCount"), (1, 1)),
                burst_delay=pair(system.get("BurstDelay")), initial_delay=pair(system.get("InitialDelay")),
                start_size_rate=pair(system.get("StartSizeRate")),
                shader="ADDITIVE" if shader.startswith("ADD") or shader == "W3D_EMISSIVE" else
                "ALPHA_TEST" if shader == "ALPHA_TEST" else "ALPHA",
                ground=(system.get("IsGroundAligned") or "").lower().startswith("y"), tex=tex, cells=cells,
                colors=colors, alphas=alphas, size_rate=pair(upd.get("SizeRate")), size_damp=pair(upd.get("SizeRateDamping"), (1, 1)),
                angle_z=pair(upd.get("AngleZ")), ang_rate_z=pair(upd.get("AngularRateZ")),
                gravity=pair(phys.get("Gravity"))[0], vel_damp=pair(phys.get("VelocityDamping"), (1, 1)),
                drift=vec(phys.get("DriftVelocity")),
                vel=dict(type=vt, x=pair(vel.get("X")), y=pair(vel.get("Y")), z=pair(vel.get("Z")),
                         speed=pair(vel.get("Speed")), other=pair(vel.get("OtherSpeed")),
                         radial=pair(vel.get("Radial")), normal=pair(vel.get("Normal"))),
                vol=dict(type=vo, start=vec(vol.get("StartPoint")), end=vec(vol.get("EndPoint")),
                         half=vec(vol.get("HalfSize")), radius=pair(vol.get("Radius"))[0],
                         length=pair(vol.get("Length"))[0], offset=vec(vol.get("Offset")),
                         hollow=(vol.get("IsHollow") or "").lower().startswith("y")))


def ages(s):
    life = max(s["lifetime"])
    total = s["system_lifetime"] + life if s["system_lifetime"] > 0 else 2 * life
    start = max(s["initial_delay"])
    return [int(start + total * f) for f in (0.2, 0.45, 0.75)]


def ppm(path, rows):
    """A binary PPM from rows of (r, g, b) 0-255 tuples."""
    with open(path, "wb") as fh:
        fh.write(b"P6\n%d %d\n255\n" % (len(rows[0]), len(rows)))
        for r in rows:
            fh.write(bytes(v for px in r for v in px))


def swatches(path, ea_keys, our_keys):
    """Two rows of colour chips: EA's keys over ours."""
    chip, gap = 34, 4
    n = max(len(ea_keys), 1)
    w = n * (chip + gap)
    rows = []
    for keys in (ea_keys, our_keys):
        for _ in range(chip):
            row = []
            for i in range(n):
                c = keys[i][1] if i < len(keys) else (20, 20, 20)
                row += [c] * chip + [(20, 20, 20)] * gap
            rows.append(row[:w])
        rows += [[(20, 20, 20)] * w] * gap
    ppm(path, rows)


def ramp_bar(path, ramp, w=300, h=22):
    cols = [tuple(int(round(v * 255)) for v in ramp.colour(100.0 * i / (w - 1))) for i in range(w)]
    ppm(path, [cols] * h)


def magick(*args):
    subprocess.check_call(["magick"] + [str(a) for a in args])


def label(text, w, h, path, size=17, colour="#e8e2d4"):
    magick("-size", "%dx%d" % (w, h), "xc:#141414", "-font", FONT, "-fill", colour, "-pointsize", size,
           "-gravity", "NorthWest", "-annotate", "+8+6", text, path)


def review(factions=None):
    g, active, shipped, base, plans, counts, r = install.compose_all()
    if r.failed:
        raise SystemExit("fx: checks fail; run --stage for the report")
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    ours_text = shipped["data\\ini\\fxparticlesystem.ini"]
    ours_idx = blocks.systems(ours_text)
    cache = {}
    for p in plans:
        if factions and p.r.faction not in factions:
            continue
        sections, shown = [], {}
        for power, lists in p.powers.items():
            key = tuple(lists)
            if key in shown:                        # two powers, one FX list (Summon Orcs and Giants)
                i = shown[key]
                sections[i] = (sections[i][0].replace(" (", ", %s (" % power.replace("SpellBook", ""), 1), sections[i][1])
                continue
            masters = [ea for ea in _systems_of(p, lists) if ea in p.systems]
            if masters:
                shown[key] = len(sections)
                sections.append(("Spell book: %s (%s)" % (power.replace("SpellBook", ""), ", ".join(lists)), masters))
        building = [n for n in p.building_systems()]
        if building:
            sections.append(("Buildings: damage fire and smoke (%s ParticleSysBone lines moved in its pack)" %
                             counts.get(p.r.faction, "not staged:"), building))
        panels, rows_meta = [], []
        for title, masters in sections:
            for ea in masters:
                ea_rows = p.ps_rows(ea)
                our_rows = blocks.body(ours_text, ours_idx[p.systems[ea][0].lower()])
                pairs = [(params(ea_rows, g, cache), params(our_rows, g, cache))]
                for ref in blocks.refs(ea_rows):
                    if ref in p.systems and p.ps_rows(ref):
                        pairs.append((params(p.ps_rows(ref), g, cache),
                                      params(blocks.body(ours_text, ours_idx[p.systems[ref][0].lower()]), g, cache)))
                out = os.path.join(WORK, "%s_%s.ppm" % (p.r.faction, ea))
                panels.append(dict(out=out, tile=TILE, frames=ages(pairs[0][0]), seed=7,
                                   systems=[[a, b] for a, b in pairs]))
                rows_meta.append((title, ea, out, keyframes(ea_rows)[0], keyframes(our_rows)[0], p.systems[ea]))
        job = os.path.join(WORK, "%s_job.json" % p.r.faction)
        json.dump(dict(panels=panels), open(job, "w"))
        subprocess.check_call([paths.blender_python(), "-m", "sagekit.paint.particles", job], cwd=paths.REPO)
        _sheet(p, rows_meta)


def _systems_of(p, lists, depth=0):
    """EA systems the FX lists name (their ParticleSystem nuggets), in order, nested lists followed."""
    out = []
    for name in lists:
        span = p.fx_index.get(name.lower())
        if not span or depth > 4:
            continue
        for kind, fields, _, _ in blocks.nuggets(blocks.body(p.texts["data\\ini\\fxlist.ini"], span)):
            if kind.lower() == "particlesystem" and fields.get("Name"):
                n = fields["Name"].split()[0]
                rows = p.ps_rows(n)
                n = blocks.PS_HEAD.match(rows[0]).group(1) if rows else n
                if n not in out:
                    out.append(n)
            elif kind.lower() == "fxlistatbonepos" and fields.get("FX"):
                out += [x for x in _systems_of(p, [fields["FX"].split()[0]], depth + 1) if x not in out]
    return out


def _sheet(p, rows_meta):
    """The faction's sheet: a header with its ramps, then per system a label, the frames, the keys."""
    parts, n = [], 0
    strip_w = 6 * TILE[0] + 5 * 6
    head = os.path.join(WORK, "%s_head.png" % p.r.faction)
    label("%s effects: EA's (left three) and ours (right three), the same particles at three ages. "
          "Colour keys: EA's top row, ours below. An approximation of the game's sprites; check in game."
          % p.r.tag, 300 + 260 + strip_w, 40, head, size=20)
    parts.append(head)
    for cls, ramp in sorted(p.r.ramps.items()):
        bar = os.path.join(WORK, "%s_ramp_%s.ppm" % (p.r.faction, cls))
        ramp_bar(bar, ramp)
        lab = os.path.join(WORK, "%s_ramp_%s.png" % (p.r.faction, cls))
        label("%s ramp (%s)" % (cls, ramp.name), 260, 22, lab, size=15)
        line = os.path.join(WORK, "%s_rampline_%s.png" % (p.r.faction, cls))
        magick(lab, bar, "-background", "#141414", "+append", line)
        parts.append(line)
    last = None
    for title, ea, panel, ea_keys, our_keys, (ours, cls, why) in rows_meta:
        if title != last:
            t = os.path.join(WORK, "%s_title_%d.png" % (p.r.faction, n))
            label(title, 300 + 260 + strip_w, 34, t, size=19, colour="#f0c870")
            parts.append(t)
            last = title
        lab = os.path.join(WORK, "%s_label_%d.png" % (p.r.faction, n))
        bright = ", ".join("%.0f" % lightness([v / 255 for v in k[1]]) for k in ea_keys if k[1] != (0, 0, 0))
        label("%s\n-> %s\n%s: %s\nlightness kept: %s" % (ea, ours, cls, why[:40], bright), 300, TILE[1], lab, size=14)
        sw = os.path.join(WORK, "%s_sw_%d.ppm" % (p.r.faction, n))
        swatches(sw, [k for k in ea_keys], [k for k in our_keys])
        swp = os.path.join(WORK, "%s_sw_%d.png" % (p.r.faction, n))
        magick("-size", "260x%d" % TILE[1], "xc:#141414", sw, "-gravity", "center", "-composite", swp)
        row = os.path.join(WORK, "%s_row_%d.png" % (p.r.faction, n))
        magick(lab, panel, swp, "-background", "#141414", "+append", row)
        parts.append(row)
        n += 1
    out = os.path.join(OUT, "%s.jpg" % p.r.faction)
    magick(*parts, "-background", "#141414", "-gravity", "NorthWest", "-append", "-quality", "88", out)
    print("  " + os.path.relpath(out, paths.REPO))
