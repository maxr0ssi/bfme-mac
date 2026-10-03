#!/usr/bin/env python3
"""An Evil class's contents list (Markdown): every appended choice per row with its upgrade, the
subclasses that list it, its colours and its vertex counts per model (from the build's report.json).

    python3 -m assets.cah.evil.contents <class> [out.md]
"""
import importlib
import json
import sys

from ..kit.models import folder

ROWS = [("CreateAHero_Helmet", "Helmets"), ("CreateAHero_ShoulderPlates", "Shoulders (pauldrons, cloaks, the tutu)"),
        ("CreateAHero_Shield", "Shields"), ("CreateAHero_Weapon", "Weapons")]
CHANNEL = {1: "cloth", 0: "wraps", 2: "gems"}


def colours(spec, part, model):
    """Which of the hero's colours a part takes: the tinted tiles its UVs reach in our model."""
    from sagekit.formats.w3d import W3DFile
    from .paint import FUN_TILES, TILES
    me = W3DFile(str(folder(spec)[2] / (spec.MODELS[model.upper()].lower() + ".w3d"))).meshes[part[0]]
    tiles = FUN_TILES if part[5] == "fun" else TILES
    used = {min(7, int(u * 8)) + 8 * min(3, int((1 - v) * 4)) for u, v in me.uv}
    ch = sorted({tiles[t][4] for t in used if t in tiles and tiles[t][4] is not None}, key=lambda c: (1, 0, 2).index(c))
    return "3 colours (%s)" % ", ".join(CHANNEL[c] for c in ch) if ch else "fixed colours"


def markdown(spec):
    report = json.loads((folder(spec)[0] / "report.json").read_text())
    verts = {}
    for r in report["models"]:
        for n, s in r["parts"].items():
            verts.setdefault(n, []).append("%s %d" % (r["shipped"][2:9], s["verts"]))
    subs = {s["index"]: s["name"] for s in spec.SUBCLASSES}
    out = ["# cah pack: %s (%s)" % (spec.NAME, ", ".join(subs.values())), "",
           "Rows after the pack, per subclass: " + "; ".join("%s %s" % (k, ", ".join("%s %d" % (g, n) for g, n in v.items()
                                                                                    if g in ("Helmet", "ShoulderPlates", "Shield", "Weapon")))
                                                         for k, v in report["ini"]["lists"].items()), ""]
    for group, title in ROWS:
        parts = [p for p in spec.PARTS if p[1] == group]
        if not parts:
            continue
        out += ["## " + title, "", "| Choice | Note | Upgrade | Subclasses | Colours | Verts per model |", "|---|---|---|---|---|---|"]
        for p in parts:
            model = next(m for s in spec.SUBCLASSES if s["index"] == p[8][0] for m in s["models"])
            out.append("| %s | %s | `%s` | %s | %s | %s |" % (p[3], p[4], p[7], ", ".join(subs[i] for i in p[8]), colours(spec, p, model),
                                                          ", ".join(verts.get(p[0], []))))
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    spec = importlib.import_module("assets.cah.%s.design" % sys.argv[1])
    text = markdown(spec)
    if len(sys.argv) > 2:
        open(sys.argv[2], "w").write(text + "\n")
    else:
        print(text)
