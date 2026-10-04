"""Which of EA's hidden heroes are complete in the 2.02 files: model, animations, portrait, button,
strings, powers, voice and experience levels, checked from the player's own install.

    python3 -m assets.heroes.audit [--markdown]   -> build/assets/heroes/audit.json

A hero is "borrowed" where it works only through another hero's data (Gamling's Boromir voice and
button image); "missing" where the game would show nothing or a MISSING string.
"""
import json
import re
import sys
from pathlib import Path

from sagekit import paths
from sagekit.formats.ini import parse_draws

from . import ea

CANDIDATES = ["RohanGamling", "GondorDamrod", "GondorEarnur", "GondorIsildur", "TomBombadil",
              "OrcChief01", "OrcChief02", "OrcChief03", "OrcChief04", "OrcChief05", "DwarftHero"]
GENERIC_COMMANDS = {"command_togglestance", "command_capturebuilding", "command_attackmove", "command_stop",
                    "command_setstancebattle", "command_setstanceaggressive", "command_setstanceholdground"}
OUT = Path(paths.BUILD) / "heroes" / "audit.json"


def first(name, key):
    v = ea.fields(name, key)
    return v[0].split()[0] if v else None


def draw_report(name):
    """Models and animations of the object's Draw modules (its own, else its parent's)."""
    g = ea.install()
    models, anims = set(), set()
    for o in ea.chain(name):
        info = ea.objects()[o]
        t = ea.text(info["member"])
        body = t[info["start"]: info["start"] + len(info["body"]) + 200]
        for d in parse_draws(body, ea.defines()):
            if d.object != o:
                continue
            models |= set(d.models())
            anims |= {a.split(".")[-1] for s in d.states for x in s.animations for a in x.split() if "#" not in a}
        if models:
            break
    miss_m = sorted(m for m in models if not g.has_model(m))
    miss_a = sorted(a for a in anims if not g.has_model(a))
    return dict(models=sorted(models), missing_models=miss_m, animations=len(anims), missing_animations=miss_a)


def powers(name):
    """The command set's power buttons: each defined, labelled, imaged, its power defined and
    carried by the object."""
    cs = first(name, "CommandSet")
    sets, buttons = ea.all_blocks("CommandSet"), ea.all_blocks("CommandButton")
    sp = ea.all_blocks("SpecialPower")
    if not cs or cs not in sets:
        return dict(command_set=cs, defined=False, powers=[], problems=["no command set %s" % cs])
    slots = re.findall(r"^\s*\d+\s*=\s*(\S+)", "\n".join(ea.strip(l) for l in sets[cs].splitlines()), re.M)
    carried = {v.split()[0].lower() for v in ea.fields(name, "SpecialPowerTemplate")} | \
              {v.split()[0].lower() for v in ea.fields(name, "SpecialAbility")}
    out, problems = [], []
    for s in slots:
        if s.lower() in GENERIC_COMMANDS:
            continue
        b = buttons.get(s)
        if b is None:
            problems.append("%s: no such button" % s)
            continue
        get = lambda k: (re.search(r"^\s*%s\s*=\s*(\S+)" % k, "\n".join(ea.strip(l) for l in b.splitlines()), re.M | re.I) or [None, None])[1]
        p = get("SpecialPower")
        label, image = get("TextLabel"), get("ButtonImage")
        row = dict(button=s, power=p, label=label, image=image)
        if p and p not in sp:
            problems.append("%s: power %s undefined" % (s, p))
        if p and p.lower() not in carried:
            problems.append("%s: %s not carried by %s" % (s, p, name))
        if label and label.lower() not in ea.labels():
            problems.append("%s: label %s missing" % (s, label))
        if image and image.lower() not in ea.mapped_images():
            problems.append("%s: image %s missing" % (s, image))
        out.append(row)
    return dict(command_set=cs, defined=True, powers=out, problems=problems)


def levels(name):
    lv = [n for n, body in ea.all_blocks("ExperienceLevel").items()
          if name.lower() in [x.lower() for x in re.findall(r"TargetNames\s*=\s*([^;\r\n]*)", body)[0].split()]]
    grants = [n for n in lv if re.search(r"^\s*Upgrades\s*=\s*Upgrade_ObjectLevel", ea.all_blocks("ExperienceLevel")[n], re.M)]
    return dict(levels=len(lv), granting=len(grants))


def image(nm):
    if not nm:
        return "none"
    tex = ea.mapped_images().get(nm.lower())
    if tex is None:
        return "missing"
    return "ok" if ea.texture_exists(tex) else "texture missing"


def audit(name):
    if name not in ea.objects():
        return dict(name=name, exists=False)
    o = ea.objects()[name]
    r = dict(name=name, exists=True, member=o["member"], side=first(name, "Side"))
    r["draw"] = draw_report(name)
    r["portrait"], r["portrait_state"] = first(name, "SelectPortrait"), image(first(name, "SelectPortrait"))
    r["button"], r["button_state"] = first(name, "ButtonImage"), image(first(name, "ButtonImage"))
    strings = {}
    for k in ("DisplayName", "RecruitText", "ReviveText", "Hotkey", "Description"):
        v = first(name, k)
        strings[k] = (v, "none" if not v else "ok" if v.lower() in ea.labels() else "missing")
    r["strings"] = strings
    voice = {k: first(name, k) for k in ("VoiceSelect", "VoiceMove", "VoiceAttack")}
    r["voice"] = {k: (v, "none" if not v else "ok" if v.lower() in ea.audio_events() else "missing") for k, v in voice.items()}
    r["powers"] = powers(name)
    r["levels"] = levels(name)
    cost = first(name, "BuildCost")
    r["cost"] = ea.defines().get(cost, cost)
    return r


def verdict(r):
    """(complete?, [what is missing or borrowed])"""
    if not r["exists"]:
        return False, ["no object"]
    gaps = []
    d = r["draw"]
    if not d["models"] or d["missing_models"]:
        gaps.append("model missing")
    if d["missing_animations"]:
        gaps.append("%d animations missing" % len(d["missing_animations"]))
    if r["portrait_state"] != "ok":
        gaps.append("portrait %s" % r["portrait_state"])
    if r["button_state"] != "ok":
        gaps.append("button %s" % r["button_state"])
    for k, (v, s) in r["strings"].items():
        if k in ("DisplayName", "RecruitText", "ReviveText") and s != "ok":
            gaps.append("%s %s" % (k, s))
    if any(s != "ok" for _, s in r["voice"].values()):
        gaps.append("voice missing")
    p = r["powers"]
    if not p["defined"]:
        gaps.append("no command set")
    elif not p["powers"]:
        gaps.append("no power buttons")
    gaps += p["problems"]
    if r["levels"]["levels"] < 10:
        gaps.append("%d experience levels" % r["levels"]["levels"])
    return not gaps, gaps


def borrowed(r):
    """Data that belongs to another hero (it works, but the hero speaks or looks like someone else)."""
    out = []
    own = re.sub(r"^(Rohan|Gondor|Dwarven|Elven|Isengard|Mordor|Angmar|Wild)", "", r["name"]).lower()
    for k, (v, _) in r["voice"].items():
        if v and own[:4] not in v.lower() and not v.lower().startswith("hero"):
            out.append("%s %s" % (k, v))
            break
    if r.get("button") and own[:4] not in r["button"].lower():
        out.append("button %s" % r["button"])
    for k in ("RecruitText", "ReviveText"):
        v = r["strings"][k][0]
        if v and own[:4] not in v.lower():
            out.append("%s %s" % (k, v))
    return out


def run(markdown=False):
    rows = []
    for n in CANDIDATES:
        r = audit(n)
        ok, gaps = verdict(r)
        r.update(complete=ok, gaps=gaps, borrowed=borrowed(r) if r["exists"] else [])
        rows.append(r)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=1) + "\n")
    if markdown:
        print("| Hero | File | Side | Model | Portrait | Button | Strings | Voice | Powers | Levels | Verdict |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        if not r["exists"]:
            print("%s: no object" % r["name"])
            continue
        np = len(r["powers"]["powers"])
        cells = [r["name"], r["member"].split("\\")[-1], r["side"], ", ".join(r["draw"]["models"]),
                 "%s (%s)" % (r["portrait"], r["portrait_state"]), "%s (%s)" % (r["button"], r["button_state"]),
                 "ok" if all(s in ("ok",) for k, (v, s) in r["strings"].items() if k in ("DisplayName", "RecruitText", "ReviveText"))
                 else "missing", (r["voice"]["VoiceSelect"][0] or "none"), "%d" % np, "%d" % r["levels"]["levels"],
                 "complete" if r["complete"] else "; ".join(r["gaps"])]
        if r["borrowed"]:
            cells[-1] += " (borrowed: %s)" % "; ".join(r["borrowed"])
        print(("| " + " | ".join(cells) + " |") if markdown else " / ".join(cells))
    return rows


if __name__ == "__main__":
    run("--markdown" in sys.argv)
