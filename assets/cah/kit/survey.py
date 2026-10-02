"""Map every Create-a-Hero subclass from EA's data (the effective 2.02 INI and models): its class
file and index, its models (_U in game, _C creation screen, _M mounted) and skeletons, its body
sheet and 3-colour mask, the part sub-objects its models carry, each row's list length, the weapon
sets its weapons use, and the names the cah kit gives its additions (docs/CAH.md).

    python3 -m assets.cah.kit.survey [--markdown]
"""
import re
import sys

from sagekit.formats.w3d import W3DFile
from sagekit.game import Install

from .ini import CLASSES, I, O, lists, strip, subclasses, upgrades

PARTS_RE = r"(HLMT|SLDR|GNLT|BOOT|SHLD|AXE|HMR|SWRD|SWORD|BOW|STAF|CAPE|HOOD|BODY|CM|WEST|SPEAR|CLUB|MACE|HAMMER|PIPE)"
GROUPS = ["Helmet", "ShoulderPlates", "Body", "Gauntlets", "Weapon", "Shield", "Boots"]
SHORT = {"Helmet": "Hlm", "ShoulderPlates": "Sh", "Body": "Bd", "Gauntlets": "Gn", "Weapon": "Wp", "Shield": "Sd", "Boots": "Bt"}


def class_upgrades(text):
    """{class upgrade: [(subclass name, index, subclass block)]} of one class file."""
    cls = re.search(r"^\s*UpgradeName\s*=\s*(\S+)", strip(text), re.M).group(1)
    return cls, [(name, n, text[a:b]) for name, n, a, b in subclasses(text)]


def condition_flags(text):
    """{(class upgrade, subclass index, creation screen?): CREATE_A_HERO_nn}."""
    out = {}
    for m in re.finditer(r"Behavior\s*=\s*ModelConditionUpgrade\s+\S+(.*?)^\s*End", strip(text), re.M | re.S):
        trig = " ".join(re.findall(r"TriggeredBy\s*=\s*([^\n]*)", m.group(1)))
        add = re.search(r"AddConditionFlags\s*=\s*(\S+)", m.group(1))
        cls = re.search(r"(Upgrade_CreateAHero_Class\w+)", trig)
        sub = re.search(r"Upgrade_CreateAHero_SubClass_(\d+)", trig)
        if add and cls and sub:
            out[(cls.group(1), int(sub.group(1)), "Upgrade_CreateAHeroMapMode" in trig)] = add.group(1)
    return out


def model_states(text):
    """[(set of flags, model, skeleton)] of the CaH object's ModelConditionStates."""
    out = []
    for m in re.finditer(r"^\s*ModelConditionState\s*=\s*([^\n]*)\n(.*?)^\s*End", strip(text), re.M | re.S):
        model = re.search(r"^\s*Model\s*=\s*(\S+)", m.group(2), re.M)
        skel = re.search(r"^\s*Skeleton\s*=\s*(\S+)", m.group(2), re.M)
        if model:
            out.append((set(m.group(1).split()), model.group(1), skel.group(1) if skel else ""))
    return out


def weapon_sets(text):
    """{upgrade: [weapon condition]} from the WeaponSetUpgrades."""
    out = {}
    for m in re.finditer(r"Behavior\s*=\s*WeaponSetUpgrade\s+\S+(.*?)^\s*End", strip(text), re.M | re.S):
        t = re.search(r"TriggeredBy\s*=\s*(\S+)", m.group(1))
        c = re.search(r"WeaponCondition\s*=\s*(\S+)", m.group(1))
        if t and c:
            out.setdefault(t.group(1), []).append(c.group(1))
    return out


def house(text):
    return {b.lower(): h for b, h in re.findall(r"BaseTexture\s*=\s*(\S+)\s*\n\s*HouseTexture\s*=\s*(\S+)", strip(text))}


def survey():
    g = Install()
    read = lambda m: g.read(m).decode("latin-1")
    ups = upgrades(read(I + "createaheroupgrades.inc"))
    flags = condition_flags(read(O + "createaheromodelconditionupgrades.inc"))
    states = model_states(read(O + "createaheromodels.inc"))
    ws = weapon_sets(read(O + "createaheroweaponupgrades.inc"))
    hc = house(read(I + "housecolor.ini"))
    rows = []
    for c in CLASSES:
        text = read(I + "createaherosystem%s.inc" % c)
        cls, subs = class_upgrades(text)
        sub_lists = lists(text, ups)
        for name, idx, block in subs:
            models = {}
            for mm in (False, True):
                flag = flags.get((cls, idx, mm))
                for fl, model, skel in states:
                    if flag in fl:
                        kind = "M" if "MOUNTED" in fl else ("C" if mm else "U")
                        models.setdefault(kind, (model, skel))
            body, mask, parts = "", "", []
            if "U" in models:
                w = W3DFile(g.read("art\\w3d\\%s\\%s.w3d" % (models["U"][0].lower()[:2], models["U"][0].lower())))
                masked = [m for m in w.meshes.values() if any(t.lower() in hc for t in m.textures)]
                body_meshes = masked or [m for n, m in w.meshes.items() if not re.match(PARTS_RE, n)] or list(w.meshes.values())
                big = max(body_meshes, key=lambda m: len(m.verts))
                body = (big.textures or [""])[0]
                mask = hc.get(body.lower(), "")
                parts = sorted(n for n in w.meshes if re.match(PARTS_RE, n))
            r = sub_lists.get(name, {})
            weap = r.get("CreateAHero_Weapon", [])
            rows.append(dict(cls=c, sub=name, index=idx, models=models, body=body, mask=mask, parts=parts,
                             lengths={k: len(r.get("CreateAHero_" + k, [])) for k in GROUPS},
                             weapon_sets=sorted({w for u in weap for w in ws.get(u, [])})))
    return rows


def key(models):
    """The kit's name stem for a subclass: its U model's family and type (CHHW_SM_U_SKN -> HWSM)."""
    m = models.get("U", ("",))[0]
    return (m[2:4] + m[5:7]).upper() if m else ""


def markdown(rows):
    head = ("| Class file / # | Subclass | _U / _C / _M models (skeleton) | Body sheet / mask | Lists " +
            "(Hlm Sh Bd Gn Wp Sd Bt) | Weapon sets | Kit stem |")
    out = [head, "|---|---|---|---|---|---|---|"]
    for r in rows:
        mods = "<br>".join("%s %s (%s)" % (k, m, s) for k, (m, s) in sorted(r["models"].items(), key=lambda x: "UCM".index(x[0])))
        lens = " ".join(str(r["lengths"][g]) for g in GROUPS)
        out.append("| %s / %d | %s | %s | %s / %s | %s | %s | %s |" % (
            r["cls"], r["index"], r["sub"], mods, r["body"], r["mask"] or "-", lens,
            " ".join(w.replace("WEAPONSET_CREATE_A_HERO_", "") for w in r["weapon_sets"]) or "-", key(r["models"])))
    return "\n".join(out)


if __name__ == "__main__":
    rows = survey()
    if "--markdown" in sys.argv:
        print(markdown(rows))
    else:
        for r in rows:
            print(r["cls"], r["index"], r["sub"], r["models"], r["body"], r["mask"], r["lengths"], r["weapon_sets"], r["parts"])
