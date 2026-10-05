"""The fire budget's particle systems: our copies of EA's flame, ember and smoke systems that draw
the same fire with fewer particles (docs/ART.md "Fire budget", docs/PERFORMANCE.md §15).

Our building fire once cost about 7,600 live particles over eight late-game bases, against EA's 809
and the game's 4,000 cap (above it the engine drops the oldest particles of everything, combat
effects included). A lean copy keeps EA's texture, shader, colours, emission volume and each
particle's path, and changes four things, all derived from one spec per system:

    rate        BurstCount / BurstDelay as the spec gives them (fewer particles a frame)
    stretch L   each particle lives L times as long and moves L times slower over the same path:
                Lifetime and every Color / Alpha keyframe's frame x L; DriftVelocity, the
                EmissionVelocity values, SizeRate and the angular rates / L; Gravity / L^2; the
                per-frame dampings to the power 1/L (so a particle reaches EA's height, width and
                colour at the same point of its life)
    grow s      Size and SizeRate x s: each particle covers s^2 the area
    gain        what the cut leaves of the glow (additive) or cover (alpha) at a pixel, given back:
                k = EA's rate / ours, from 1 to GAIN_MAX; on the Color keys of an additive system,
                k / (L s) (the larger sprites spread the same light over a wider footprint; no
                channel past 255, so the hue stays), on the Alpha keys of an alpha one k / (L s^2)
                (the cover a pixel gets from the fewer, larger puffs), at most ALPHA_GAIN_MAX

Live particles (sagekit/drawcost.py Rates: BurstCount / BurstDelay x Lifetime) fall by k / L.
"""
import re

GAIN_MAX = 2.5
ALPHA_GAIN_MAX = 1.3        # thicker puffs would hide the flames under them (the review, 2026-10-04)
# our name: (EA's system, BurstCount, BurstDelay, stretch L, grow s); live counts: drawcost.Rates
LEAN = {
    "SagekitLeanSiegeWorkFire": ("SiegeWorkFire", "1 1", "3 3", 1.2, 1.35),             # 20 -> 8
    "SagekitLeanFurnaceFire": ("furnaceFire", "1 1", "2 3", 1.2, 1.4),                 # 22.5 -> 7.2
    "SagekitLeanFurnaceSparks": ("furnaceSparks", "1 1", "40 60", 1.0, 1.2),           # 12.5 -> 2.5
    "SagekitLeanForgeCoal": ("ForgeCoal", "1 1", "16 17", 1.0, 1.3),                   # 10 -> 3
    "SagekitLeanForgeEmbers": ("ForgeEmbers", "1 1", "8 10", 1.0, 1.2),                # 7.1 -> 2.8
    "SagekitLeanCampfireEmbers": ("CampfireEmbersSmall", "1 1", "14 16", 1.0, 1.2),    # 5.7 -> 2.8
    "SagekitLeanFireTorch": ("FireTorch", "1 1", "2 2", 1.2, 1.3),                     # 5 -> 3
    "SagekitLeanTorchSmoke": ("TorchSmokeBlack", "1 1", "28 28", 1.1, 1.8),            # 26.2 -> 3
    "SagekitLeanSmokeChimney": ("SmokeChimney", "1 1", "20 25", 1.15, 1.25),           # 13.3 -> 5.1
    "SagekitLeanSmokePlume": ("SmokeBuildingLarge", "1 1", "20 25", 1.15, 1.25),       # 13.3 -> 5.1
    # our coloured copies (sagekit/fire_systems.py OWN) made lean like their EA bases
    "SagekitWitchFire": ("furnaceFire", "1 1", "2 3", 1.2, 1.4),
    "SagekitColdFire": ("furnaceFire", "1 1", "2 3", 1.2, 1.4),
    "SagekitWitchSmoke": ("SmokeChimney", "1 1", "20 25", 1.15, 1.25),
    "SagekitColdSmoke": ("SmokeChimney", "1 1", "20 25", 1.15, 1.25),
}
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def fmt(x):
    s = ("%.4f" % x).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def frame(x):
    return int(x + 0.5)


def mean(v, default):
    n = [float(x) for x in NUM.findall(v or "")[:2]]
    return sum(n) / len(n) if n else default


def scale(v, f):
    """Every number of a field's value (the first two: a min max pair) times f."""
    nums = NUM.findall(v)
    out, i = v, 0
    for n in nums[:2]:
        j = out.index(n, i)
        new = fmt(float(n) * f)
        out = out[:j] + new + out[j + len(n):]
        i = j + len(new)
    return out


def power(v, p):
    return " ".join(fmt(float(n) ** p) if float(n) > 0 else n for n in NUM.findall(v)[:2])


def axes(v, f):
    return re.sub(r"([XYZ]:\s*)(-?\d+(?:\.\d+)?)", lambda m: m.group(1) + fmt(float(m.group(2)) * f), v)


def modules(lines):
    """[(module, key, value, index)] of a block's field lines (no header, modules not nested)."""
    out, module = [], None
    for i, raw in enumerate(lines):
        s = raw.split(";")[0].strip()
        if not s:
            continue
        key, _, val = (x.strip() for x in s.partition("="))
        if module is None:
            module = key
        elif s.lower() == "end":
            module = None
        else:
            out.append((module, key, val, i))
    return out


def rate(fields):
    return mean(fields.get("burstcount"), 1.0) / max(1.0, mean(fields.get("burstdelay"), 1.0))


def gain(name, ea_rate, alpha):
    _, count, delay, stretch, grow = LEAN[name]
    k = ea_rate / (mean(count, 1.0) / max(1.0, mean(delay, 1.0)))
    return min(ALPHA_GAIN_MAX if alpha else GAIN_MAX, max(1.0, k / (stretch * grow ** (2 if alpha else 1))))


def lean(name, lines):
    """The block's lines (EA's indentation, header and the final End excluded) made lean by LEAN[name]."""
    _, count, delay, L, s = LEAN[name]
    lines = list(lines)
    fields = modules(lines)
    system = {k.lower(): v for m, k, v, _ in fields if m.lower() == "system"}
    alpha = (system.get("shader") or "ADDITIVE").split()[0].upper().startswith("ALPHA")
    g = gain(name, rate(system), alpha)
    colours = [v for m, k, v, _ in fields if m.lower() == "color" and re.match(r"color\d+$", k, re.I)]
    peak = max([max(int(x) for x in re.findall(r"[RGB]:\s*(\d+)", v)) for v in colours] or [255])
    cg = 1.0 if alpha else min(g, 255.0 / max(1, peak))
    ag = g if alpha else 1.0
    for m, k, v, i in fields:
        mod, key = m.lower(), k.lower()
        new = v
        if mod == "system" and key == "lifetime":            # whole frames, like the keyframes
            new = " ".join(str(frame(float(n) * L)) for n in NUM.findall(v)[:2])
        elif mod == "system" and key == "size":
            new = scale(v, s)
        elif mod == "system" and key == "burstcount":
            new = count
        elif mod == "system" and key == "burstdelay":
            new = delay
        elif mod == "color" and re.match(r"color\d+$", key):
            rgb = re.sub(r"([RGB]:\s*)(\d+)", lambda x: x.group(1) + str(min(255, int(round(int(x.group(2)) * cg)))), v)
            new = re.sub(r"(\s)(\d+)\s*$", lambda x: x.group(1) + str(frame(int(x.group(2)) * L)), rgb)
        elif mod == "alpha" and re.match(r"alpha\d+$", key):
            n = NUM.findall(v)
            new = "%s %s %d" % (fmt(min(1.0, float(n[0]) * ag)), fmt(min(1.0, float(n[1]) * ag)), frame(float(n[2]) * L))
        elif mod == "update" and key == "sizerate":
            new = scale(v, s / L)
        elif mod == "update" and key in ("angularratez", "angularratex", "angularratey"):
            new = scale(v, 1.0 / L)
        elif (mod, key) in (("update", "sizeratedamping"), ("update", "angulardamping"),
                            ("update", "angulardampingxy"), ("physics", "velocitydamping")):
            new = power(v, 1.0 / L)
        elif mod == "physics" and key == "driftvelocity":
            new = axes(v, 1.0 / L)
        elif mod == "physics" and key == "gravity":
            new = scale(v, 1.0 / (L * L))
        elif mod == "emissionvelocity" and key in ("x", "y", "z", "speed", "otherspeed", "radial", "normal"):
            new = scale(v, 1.0 / L)
        if new != v:
            raw = lines[i]
            pad = raw[:len(raw) - len(raw.lstrip())]
            lines[i] = "%s%s = %s" % (pad, k, new)
    if "burstdelay" not in system:                  # EA's emits every frame: our delay before the System's End
        _, _, _, last = [f for f in fields if f[0].lower() == "system"][-1]
        raw = lines[last]
        lines.insert(last + 1, "%sBurstDelay = %s" % (raw[:len(raw) - len(raw.lstrip())], delay))
    return lines


def why(name):
    ea, count, delay, L, s = LEAN[name]
    return "EA's %s, lean: BurstCount %s, BurstDelay %s, life and path x%s slower, size x%s (the fire budget)" % (
        ea, count, delay, fmt(L), fmt(s))
