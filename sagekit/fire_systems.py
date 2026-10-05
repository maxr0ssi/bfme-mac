"""Particle systems of our own for sagekit's fire (sagekit/fire.py KINDS): copies of EA's own
FXParticleSystems with a few fields changed, for a fire EA never burns in place (green witch-fire:
EA's green systems are spells, hits, bursts and trails - CorpseRain, MorgulBladeHit, WitchKingPoison
- none a steady flame; Angmar's cold blue-white fire: EA's ice systems are arrows, meteors and
mists - IceArrowFire, IceMeteorTrail, IceWallMist - none a steady flame either).

How the game loads them (RotWK's Data\\INI\\Default\\SubsystemLegend*.ini): TheFXParticleSystemManager
reads Data\\INI\\FXParticleSystem.ini only (FXParticleSystemCustom.ini is commented out there), and
before TheThingFactory reads the objects whose ParticleSysBone lines name them. So each system of
ours goes into that file, right after the EA block it copies: the 2.02 patch's note at the file's
end asks for nothing below or directly above it. Names are EA's style (letters only, no length
limit in the file; EA's longest run past 30 characters), prefixed "Sagekit", and must not be one of
EA's names in either particle INI.

The blocks are made at build time from the player's own EA file (no EA text in git): the base
block renamed, the listed fields' values replaced, the Color module's keyframes replaced, and, for a
system in sagekit/fire_lean.py LEAN (the fire budget), the whole block made lean. Every
building that draws any of them ships the whole set (`ops`), so every faction archive's copy of
the file is the same and whichever one the game reads defines them all.
"""
import re

from .fire_lean import LEAN, lean, why as lean_why
from .formats.ini import strip

MEMBER = "data\\ini\\fxparticlesystem.ini"
LOADED = ("data\\ini\\fxparticlesystem.ini", "data\\ini\\particlesystem.ini")   # what the game reads

# name -> (EA's FXParticleSystem it copies, {(module, key): value}, the Color module's lines, why)
OWN = {
    # the Morgul witch-fire (appended 2026-09-30, the Mordor citadel's crowns): EA's furnaceFire
    # (EXFire01.tga is grey; the Color keyframes alone give EA's flames their orange) in the
    # sickly yellow-green of assets/mordor/style.py MORGUL, a little brighter than furnaceFire's
    # dim brown so it reads by day; size, rise and emission as EA's
    "SagekitWitchFire": ("furnaceFire", {}, ("Color2 = R:72 G:132 B:30 5", "Color3 = R:0 G:0 B:0 15",
                                             "ColorScale = -15 -1"),
                         "EA's furnaceFire, its flames Morgul green"),
    # a modest dark plume over the witch-fire: EA's SmokeChimney twice as broad and growing twice
    # as fast (SmokeBuildingLarge, the burning structures' plume, grows to several times this)
    "SagekitWitchSmoke": ("SmokeChimney", {("System", "Size"): "8 10", ("Update", "SizeRate"): "0.4 0.8"},
                          ("Color1 = R:36 G:36 B:34 0", "ColorScale = -20 20"),
                          "EA's SmokeChimney, twice as broad"),
    # Angmar's cold fire (appended 2026-10-01, the Angmar citadel's crown; the systems above are
    # unchanged): EA's furnaceFire burning pale ice-blue, near white as it is born, blue as it rises
    # (EA's own blue fire on KBFortress is a card, EXFireTorchSeqBlue on MBFDPF, not a particle
    # system: nothing of EA's to reuse); size, rise and emission as EA's
    "SagekitColdFire": ("furnaceFire", {}, ("Color1 = R:96 G:116 B:136 0", "Color2 = R:52 G:92 B:140 5",
                                            "Color3 = R:0 G:0 B:0 15", "ColorScale = -12 -1"),
                        "EA's furnaceFire, its flames ice-blue to white"),
    # a modest blue-black plume over the cold fire: SagekitWitchSmoke's size in a cold blue-black
    "SagekitColdSmoke": ("SmokeChimney", {("System", "Size"): "8 10", ("Update", "SizeRate"): "0.4 0.8"},
                         ("Color1 = R:30 G:34 B:44 0", "ColorScale = -16 16"),
                         "EA's SmokeChimney, twice as broad, blue-black"),
}
# the fire budget (appended 2026-10-04): lean copies of EA's systems, and the four above made lean the
# same way (sagekit/fire_lean.py: fewer, slightly larger, longer-lived particles over the same volume)
OWN.update({n: (spec[0], {}, None, None) for n, spec in LEAN.items() if n not in OWN})
HEAD_RE = r"^[ \t]*(?:FX)?ParticleSystem[ \t]+%s(?=[ \t;/\r\n]|$)"


def names():
    return {n.lower() for n in OWN}


def ea_block(text, name):
    """(first, last) line indices of EA's FXParticleSystem `name` in text (its header to its End),
    counting module openers (every line directly inside the block opens one) and Ends."""
    lines = text.splitlines()
    head = re.compile(HEAD_RE % re.escape(name), re.I)
    for i, raw in enumerate(lines):
        if head.match(raw) and raw.strip().lower().startswith("fxparticlesystem"):
            depth = 1
            for j in range(i + 1, len(lines)):
                s = strip(lines[j])
                if not s:
                    continue
                if s.lower() == "end":
                    depth -= 1
                    if depth == 0:
                        return i, j
                elif depth == 1:
                    depth += 1
            raise ValueError("%s: FXParticleSystem %s has no End" % (MEMBER, name))
    raise ValueError("%s: no FXParticleSystem %s" % (MEMBER, name))


def block(text, name):
    """The lines of our system `name` (unindented header, EA's indentation inside) made from its
    EA base block in `text` (EA's fxparticlesystem.ini)."""
    base, fields, colour, why = OWN[name]
    why = why or lean_why(name)
    a, z = ea_block(text, base)
    src = text.splitlines()[a + 1:z]
    out, module, depth, seen, in_colour, had_colour = [], None, 1, set(), False, False
    for raw in src:
        s = strip(raw)
        if not s:
            continue
        pad = raw[:len(raw) - len(raw.lstrip())]
        if s.lower() == "end":
            if in_colour:
                out += [pad + "  " + c for c in colour]
                in_colour = False
            depth -= 1
            module = None
            out.append(pad + "End")
            continue
        key, _, val = (x.strip() for x in s.partition("="))
        if depth == 1:
            depth, module = 2, key
            in_colour = key.lower() == "color" and colour is not None
            had_colour |= in_colour
            out.append(pad + s)
            continue
        if in_colour:
            continue
        want = next((v for (m, k), v in fields.items() if m.lower() == module.lower() and k.lower() == key.lower()), None)
        if want is not None:
            seen.add((module.lower(), key.lower()))
            s = "%s = %s" % (key, want)
        out.append(pad + s)
    missing = [k for k in fields if (k[0].lower(), k[1].lower()) not in seen]
    if missing:
        raise ValueError("%s: EA's %s has no %s" % (name, base, ", ".join("%s.%s" % k for k in missing)))
    if not had_colour and colour is not None:
        raise ValueError("%s: EA's %s has no Color module" % (name, base))
    if name in LEAN:
        out = lean(name, out)
    return ["; sagekit (sagekit/fire_systems.py): %s" % why, "FXParticleSystem %s" % name] + out + ["End"]


def ops(install):
    """The INI op adding every system of ours to EA's fxparticlesystem.ini (formats/ini.py
    add_systems): ("fx_systems", ((name, EA base, lines), ...)). ValueError when a name is EA's."""
    text = install.read(MEMBER).decode("latin-1")
    taken = [n for n in OWN if any(re.search(HEAD_RE % re.escape(n), install.read(m).decode("latin-1"), re.I | re.M)
                                   for m in LOADED)]
    if taken:
        raise ValueError("particle systems of ours named like EA's: %s" % ", ".join(taken))
    return ("fx_systems", tuple((n, OWN[n][0], tuple(block(text, n))) for n in OWN))


def add_systems(text, blocks):
    """Each (name, after, lines) of blocks inserted after the End of EA's FXParticleSystem `after`,
    a blank line before it, in the file's line endings. Idempotent: a system already defined is
    left as it is."""
    nl = "\r\n" if "\r\n" in text else "\n"
    for name, after, lines in blocks:
        if re.search(HEAD_RE % re.escape(name), text, re.I | re.M):
            continue
        _, z = ea_block(text, after)
        rows = text.splitlines(keepends=True)
        rows[z + 1:z + 1] = [nl] + [x + nl for x in lines]
        text = "".join(rows)
    return text
