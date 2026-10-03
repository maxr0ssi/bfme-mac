"""The cah pack's INI: EA's effective 2.02 Create-a-Hero files with every class's entries appended.

A class build makes a FRAGMENT (fragment()): its text for each shared file, its additions to each
subclass's rows, its model renames. The pack composes all fragments onto EA's files in class order
(compose()), so classes build independently and still compose; the lint runs on the composition.

  createaheroupgrades.inc               an Upgrade per row position, SHARED by every class (Upgrade_SKH_CHH01 is
                                        each class's first appended helmet; the engine holds 1152 upgrades,
                                        sagekit/upgrades.py); per weapon its own (GroupOrder none, as EA's)
  createaherosystemappearancebling.inc  a CreateAHeroBling per non-weapon upgrade
  createaherosystemweapons.inc          a CreateAHeroBling per weapon
  createaherosystem<class>.inc          each upgrade APPENDED to its row in its subclasses
  object/createahero/createaheroweaponupgrades.inc
                                        a SubObjectsUpgrade per part; per weapon a WeaponSet on its own
                                        free flag (WEAPONSET_CREATE_A_HERO_WS_nn = its upgrade number)
  object/createahero/createaheroremoveupgradeupgrades.inc
                                        a RemoveUpgradeUpgrade per upgrade (clears its row's group)
  object/createahero/createaheromodels.inc
                                        each of EA's models a class edits -> its own copy (CH* -> SK*)
No strings: every entry shows EA's row label (LABELS); house-colour lines go through the shared
units archive (assets/cah/pack).
"""
import difflib
import re
from pathlib import Path

from sagekit import paths, upgrades as U
from sagekit.formats.big import Archive
from sagekit.game import Install

I = "data\\ini\\"
O = I + "object\\createahero\\"
SHARED = {"upgrades": I + "createaheroupgrades.inc", "bling": I + "createaherosystemappearancebling.inc",
          "weapons": I + "createaherosystemweapons.inc", "wupg": O + "createaheroweaponupgrades.inc",
          "remove": O + "createaheroremoveupgradeupgrades.inc", "models": O + "createaheromodels.inc"}
CLASSES = ["menofthewest", "archer", "wizard", "dwarf", "servantsofsauron", "corruptedman", "ologhai"]
OBJECT_INCS = ["createaherodrawmodules", "createaherorespawn", "createaheromodelconditionupgrades",
               "createaheroattributemodifiers", "createaheroarmorupgrades", "createaheropowers", "createaheroaipowers",
               "createaheroreaction", "createaheroaudio", "createaherodesign"]
NL = "\r\n"
HEAD = NL + "//---------------- sagekit cah pack (assets/cah): appended, never inserted (saved heroes index these lists)" + NL
LABELS = {"CreateAHero_Helmet": ("CAH:HelmetMenuLabel", "CAH:HelmetMenuDesc"),
          "CreateAHero_ShoulderPlates": ("CAH:ShouldersMenuLabel", "CAH:ShouldersMenuDesc"),
          "CreateAHero_Body": ("CAH:ChestMenuLabel", "CAH:ChestMenuDesc"),
          "CreateAHero_Gauntlets": ("CAH:ArmsMenuLabel", "CAH:ArmsMenuDesc"),
          "CreateAHero_Shield": ("CAH:ShieldMenuLabel", "CAH:ShieldMenuDesc"),
          "CreateAHero_Boots": ("CAH:LegsMenuLabel", "CAH:LegsMenuDesc"),
          "CreateAHero_Weapon": ("CAH:WeaponMenuLabel", "CAH:WeaponMenuDesc")}


def strip(text):
    return "\n".join(re.split(r";|//", l, maxsplit=1)[0] for l in text.splitlines())


def labels():
    """Every label of 2.02's English lotr.str (lang/englishpatch202.big)."""
    text = Archive(str(Path(paths.GAMEDIRS["rotwk"]) / "lang" / "englishpatch202.big")).read("data\\lotr.str")
    return {l.lower() for l in re.findall(r"^\s*([A-Za-z0-9_]+:[^\s\"]+)\s*$", text.decode("utf-8", "replace"), re.M)}


def read_all():
    """EA's effective files: the shared ones, every class file (class_<name>), the object includes."""
    g = Install()
    f = {k: g.read(v).decode("latin-1") for k, v in SHARED.items()}
    for c in CLASSES:
        f["class_" + c] = g.read(I + "createaherosystem%s.inc" % c).decode("latin-1")
    for c in OBJECT_INCS:
        f["obj_" + c] = g.read(O + c + ".inc").decode("latin-1")
    return f


def members(f):
    """{key: archive member} of every file a composition writes (shared plus the edited classes)."""
    return {**SHARED, **{k: I + "createaherosystem%s.inc" % k[6:] for k in f if k.startswith("class_")}}


def upgrades(text):
    return {m.group(1): dict(re.findall(r"^\s*(\w+)\s*=\s*(\S+)", m.group(2), re.M))
            for m in re.finditer(r"^Upgrade\s+(\S+)(.*?)^End", strip(text), re.M | re.S)}


def blings(text):
    out = {}
    for m in re.finditer(r"^\s*CreateAHeroBling\b(.*?)^\s*End", strip(text), re.M | re.S):
        f = dict(re.findall(r"^\s*(\w+)\s*=\s*(\S+)", m.group(1), re.M))
        out[f["BlingUpgradeName"]] = f
    return out


def subclasses(text):
    """[(name, index, start, end)] of the live SubClass blocks of a class file (offsets into
    `text`): a block opens at an uncommented SubClass line (its name is the line's // comment) and
    closes at its uncommented ViewInfo; commented-out subclasses (Servants of Sauron's troll) are
    skipped."""
    out, pos, cur = [], 0, None
    for line in text.splitlines(True):
        code = re.split(r";|//", line, maxsplit=1)[0].strip()
        if cur is None and re.match(r"SubClass\b", code):
            cur = [line.split("//", 1)[1].strip() if "//" in line else "", None, pos]
        elif cur is not None:
            m = re.search(r"Upgrade_CreateAHero_SubClass_(\d+)", code)
            if m and cur[1] is None:
                cur[1] = int(m.group(1))
            if code.startswith("ViewInfo"):
                out.append((cur[0], cur[1], cur[2], pos + len(line)))
                cur = None
        pos += len(line)
    return out


def lists(text, ups):
    """{subclass: {group: [upgrade]}} in the order the menu cycles them."""
    out = {}
    for name, _, a, b in subclasses(text):
        rows = {}
        for line in re.findall(r"^\s*BlingUpgrades\s*=([^\n]*)", strip(text[a:b]), re.M):
            for u in line.split():
                u = u.lstrip("@")
                rows.setdefault(ups.get(u, {}).get("GroupName", "?" + u), []).append(u)
        out[name] = rows
    return out


def modules(text):
    out = []
    for m in re.finditer(r"^\s*(Behavior|Draw)\s*=\s*(\w+)\s+(\w+)(.*?)^\s*End\b", strip(text), re.M | re.S):
        fields = {}
        for k, v in re.findall(r"^\s*(\w+)\s*=\s*([^\n]*)", m.group(4), re.M):
            fields.setdefault(k, []).append(v.strip())
        out.append((m.group(2), m.group(3), fields))
    return out


def weaponsets(text):
    return [set(m.group(1).split()) for m in re.finditer(r"^\s*WeaponSet\s*\n\s*Conditions\s*=\s*([^\n]*)", strip(text), re.M)]


def ea_weaponsets(text, flag):
    """[(other conditions, body lines)] of every EA WeaponSet whose Conditions carry `flag` (a bow
    has two: ranged with WEAPONSET_TOGGLE_1 and melee): a new weapon fights exactly like it."""
    out = []
    for m in re.finditer(r"^[ \t]*WeaponSet[^\n]*\n[ \t]*Conditions\s*=\s*([^\r\n]*)\r?\n(.*?)^[ \t]*End", text, re.M | re.S):
        conds = re.split(r";|//", m.group(1))[0].split()
        if flag in conds:
            out.append(([c for c in conds if c != flag], [l.rstrip("\r") for l in m.group(2).split("\n") if l.strip()]))
    if not out:
        raise SystemExit("EA has no WeaponSet on %s" % flag)
    return out


# ------------------------------------------------------------------ one class's fragment
ROW = {"CreateAHero_Helmet": "CHH", "CreateAHero_ShoulderPlates": "CHSP", "CreateAHero_Shield": "CHS"}
ROW_NAME = {"CreateAHero_Helmet": "helmet", "CreateAHero_ShoulderPlates": "shoulder", "CreateAHero_Shield": "shield"}


def row_upgrade(group, n):
    """The upgrade of our n-th (from 1) appended entry in a non-weapon row, SHARED by every class:
    each class's object shows its own sub-object for it (the engine holds 1152 upgrades in all,
    sagekit/upgrades.py). Weapons stay per class: each sets its own weapon-set flag."""
    return "Upgrade_SKH_%s%02d" % (ROW[group], n)


def ws_flag(up):
    return "WEAPONSET_CREATE_A_HERO_WS_%s" % up[-2:]


def first_slot(ea, group):
    """GroupOrder of our first entry in a row: past every EA list of that row in every class (a
    shared upgrade has one GroupOrder; EA's own shared ones do not match every list's index)."""
    ups = upgrades(ea["upgrades"])
    return max(len(r.get(group, [])) for c in CLASSES for r in lists(ea["class_" + c], ups).values())


def fragment(spec, ea):
    """spec: the class module (assets/cah/<class>/design.py). Its PARTS are
    (sub-object, group, design, name, description, sheet, remap, upgrade[, subclass indices]).
    upgrades: {upgrade: {file key: text}}, the same text in every class that shares the upgrade;
    append: the class's own SubObjectsUpgrade and weapon modules."""
    count, adds, shared, wupg = {}, {}, {}, ""
    slots = {g: first_slot(ea, g) for g in ROW}
    like = getattr(spec, "WEAPON_LIKE", None)
    sets_of = lambda name: [([], spec.WEAPON_LINES)] if getattr(spec, "WEAPON_LINES", None) else \
        ea_weaponsets(ea["wupg"], like[name] if isinstance(like, dict) else like)
    also = getattr(spec, "ALSO_SHOW", {})
    for part in spec.PARTS:
        name, group, _, title, _, _, _, up = part[:8]
        subs = part[8] if len(part) > 8 else [s["index"] for s in spec.SUBCLASSES]
        count[group] = count.get(group, 0) + 1
        for s in subs:
            adds.setdefault(s, {}).setdefault(group, []).append(up)
        weapon = group == "CreateAHero_Weapon"
        if not weapon and up != row_upgrade(group, count[group]):
            raise SystemExit("%s: %s is our %s %d, so its upgrade is %s" % (spec.NAME, name, ROW_NAME[group], count[group],
                                                                            row_upgrade(group, count[group])))
        note = title if weapon else "every class's %s %d" % (ROW_NAME[group], count[group])
        label, desc = LABELS[group]
        shared[up] = {
            "upgrades": ("Upgrade %s\t\t; sagekit cah: %s" % (up, note) + NL + "  Type              = OBJECT" + NL +
                         "  GroupName\t\t\t= %s" % group + NL +
                         ("" if weapon else "  GroupOrder\t\t= %d" % (slots[group] + count[group] - 1) + NL) +
                         "End" + NL + NL),
            "weapons" if weapon else "bling": (
                "CreateAHeroBling // sagekit cah: %s" % note + NL + "\tNameTag\t\t\t = %s" % label + NL +
                "\tDescriptionTag\t = %s" % desc + NL + "\tGroupName\t\t = %s" % group + NL +
                "\tBlingUpgradeName = %s" % up + NL + "End" + NL + NL),
            "remove": (NL + "Behavior = RemoveUpgradeUpgrade SKH_Remove_%s\t; sagekit cah" % up + NL +
                       "  TriggeredBy\t\t\t= %s" % up + NL + "  UpgradeGroupsToRemove\t= %s" % group + NL + "End" + NL)}
        if weapon:
            for extra, lines in sets_of(name):
                wupg += ("WeaponSet\t\t; sagekit cah: %s fights as %s" % (title, spec.WEAPON_NOTE) + NL +
                         "\tConditions\t\t  =\t%s" % " ".join([ws_flag(up)] + extra) + NL + NL.join(lines) + NL + "End" + NL)
            wupg += ("Behavior = WeaponSetUpgrade SKH_Weapon_%s" % up + NL + "\tTriggeredBy\t\t= %s" % up + NL +
                     "\tWeaponCondition\t= %s" % ws_flag(up) + NL + "End" + NL)
        wupg += ("Behavior = SubObjectsUpgrade SKH_Show_%s\t; sagekit cah" % name + NL + "\tTriggeredBy\t\t\t   = %s" % up + NL +
                 "\tShowSubObjects\t\t   = %s" % " ".join([name] + also.get(name, [])) + NL + "\tHideSubObjectsOnRemove = Yes" + NL +
                 "\tFadeTimeInSeconds      = 0.0" + NL + "End" + NL)
    return dict(name=spec.NAME, class_file=spec.CLASS_FILE, upgrades=shared, append={"wupg": wupg},
                lists={str(k): v for k, v in adds.items()}, models=dict(spec.MODELS), parts=[p[0] for p in spec.PARTS])


def _append_rows(text, adds, ups):
    """The class file with each subclass's additions appended at the end of its rows' lines."""
    def per_sub(body, index):
        want = adds.get(str(index), {})
        for group, names in want.items():
            def row(x):
                first = x.group(2).split()[0].lstrip("@") if x.group(2).split() else ""
                return ups.get(first, {}).get("GroupName") == group
            done = [False]

            def put(x):
                if done[0] or not row(x):
                    return x.group(0)
                done[0] = True
                tail = x.group(4) if not x.group(4).strip() else (x.group(3) or " ") + x.group(4)   # a trailing comment stays
                return x.group(1) + x.group(2).rstrip() + " " + " ".join(names) + tail
            body = re.sub(r"^(\s*BlingUpgrades\s*=\s*)([^\r\n/;]*?)([ \t]*)((?:(?://|;)[^\r\n]*)?\r?\n)", put, body, flags=re.M)
            if not done[0]:
                raise SystemExit("subclass %s has no %s row" % (index, group))
        return body
    out, last = [], 0
    for _, index, a, b in subclasses(text):
        out += [text[last:a], per_sub(text[a:b], index)]
        last = b
    return "".join(out) + text[last:]


def compose(ea, fragments):
    """EA's files with every fragment applied, in the given (class) order. A shared upgrade's
    Upgrade, bling and RemoveUpgradeUpgrade go in once, with the first class that uses it."""
    f = dict(ea)
    ups = upgrades(ea["upgrades"])
    seen = {}
    for frag in fragments:
        if "upgrades" not in frag:
            raise SystemExit("%s: an old fragment; rebuild it (python3 -m assets.cah.%s.build)" % (frag["name"], frag["name"]))
        add = {k: "" for k in ("upgrades", "bling", "weapons", "remove")}
        for up, texts in frag["upgrades"].items():
            if up in seen:
                if seen[up][1] != texts:
                    raise SystemExit("%s and %s define %s differently" % (seen[up][0], frag["name"], up))
                continue
            seen[up] = (frag["name"], texts)
            for k, t in texts.items():
                add[k] += t
        for k, t in dict(add, **frag["append"]).items():
            if t:
                f[k] = f[k].rstrip() + NL + HEAD + t
        key = "class_" + frag["class_file"]
        f[key] = _append_rows(f[key], frag["lists"], ups)
        for old, new in frag["models"].items():
            f["models"], n = re.subn(r"(^\s*Model\s*=\s*)%s\b" % old, r"\g<1>%s" % new, f["models"], flags=re.M | re.I)
            if not n:
                raise SystemExit("%s: createaheromodels.inc draws no %s" % (frag["name"], old))
    return f


# ------------------------------------------------------------------ lint
def lint(f, models, known, ours_models=()):
    """Problems in a composition. models: {model: set of mesh names} of our built models."""
    errs = []
    ups = upgrades(f["upgrades"])
    bl = {**blings(f["bling"]), **blings(f["weapons"])}
    mods = [m for k in f if k.startswith("obj_") or k in ("wupg", "remove") for m in modules(f[k])]
    tags = {}
    for _, tag, _ in mods:
        tags[tag] = tags.get(tag, 0) + 1
    errs += ["module tag %s defined %d times" % (t, n) for t, n in tags.items() if n > 1 and "SKH" in t]
    seen = {}
    for u in ups:
        seen[u.lower()] = seen.get(u.lower(), 0) + 1
    errs += ["Upgrade %s defined %d times" % (u, n) for u, n in seen.items() if n > 1 and "skh" in u]
    rem, show, wsu = {}, {}, {}
    for kind, _, fl in mods:
        for t in " ".join(fl.get("TriggeredBy", [])).split():
            if kind == "RemoveUpgradeUpgrade":
                rem.setdefault(t, set()).update(" ".join(fl.get("UpgradeGroupsToRemove", [])).split())
            elif kind == "SubObjectsUpgrade":
                show.setdefault(t, set()).update(" ".join(fl.get("ShowSubObjects", [])).split())
            elif kind == "WeaponSetUpgrade":
                wsu.setdefault(t, set()).update(" ".join(fl.get("WeaponCondition", [])).split())
    sets = weaponsets(f["wupg"])
    for c in CLASSES:
        for sub, rows in lists(f["class_" + c], ups).items():
            for group, names in rows.items():
                for u in names:
                    where = "%s/%s %s" % (c, sub, u)
                    if u not in ups:
                        errs.append(where + ": no Upgrade")
                    elif u not in bl:
                        errs.append(where + ": no CreateAHeroBling")
                    elif bl[u].get("GroupName") != ups[u].get("GroupName"):
                        errs.append(where + ": bling and upgrade groups differ")
                    elif "SKH" in u:
                        if any(bl[u].get(k, "").lower() not in known for k in ("NameTag", "DescriptionTag")):
                            errs.append(where + ": a label missing from EA's lotr.str")
                        if group not in rem.get(u, set()):
                            errs.append(where + ": clears no %s (parts would stack)" % group)
                        if not show.get(u):
                            errs.append(where + ": shows no sub-object")
                        if group == "CreateAHero_Weapon":
                            if not wsu.get(u):
                                errs.append(where + ": sets no weapon set")
                            errs += [where + ": %s has no WeaponSet" % w for w in wsu.get(u, ()) if not any(w in s for s in sets)]
    owners = {}
    for u, objs in show.items():
        for o in objs:
            if "SKH" not in u and o.upper().startswith("SKH_"):
                errs.append("EA's %s shows our %s" % (u, o))
            if "SKH" in u:
                owners.setdefault(o.upper(), set()).add(u)
                if not any(o.upper() in meshes for meshes in models.values()):
                    errs.append("%s shows %s, which no model of ours has" % (u, o))
    errs += ["sub-object %s is shown by %s" % (o, sorted(u)) for o, u in owners.items() if len(u) > 1 and o.startswith("SK")]
    model_lines = set(re.findall(r"^\s*Model\s*=\s*(\S+)", strip(f["models"]), re.M))
    errs += ["createaheromodels.inc draws no %s" % m for m in ours_models if m not in model_lines]
    if len({x for s in sets for x in s if x.startswith("WEAPONSET_CREATE_A_HERO_WS_")}) > 64:
        errs.append("more than the engine's 64 CaH weapon-set flags")
    return errs


def append_only(ea, ours):
    errs = []
    eu, ou = upgrades(ea["upgrades"]), upgrades(ours["upgrades"])
    for c in CLASSES:
        a, b = lists(ea["class_" + c], eu), lists(ours["class_" + c], ou)
        for sub in a:
            for g, names in a[sub].items():
                if b.get(sub, {}).get(g, [])[:len(names)] != names:
                    errs.append("%s/%s %s: EA's list is no longer a prefix (saved heroes would change)" % (c, sub, g))
    return errs


def upgrade_limit():
    """ours -> (total, problems, line): EA's upgrades, every other archive of ours in the game folder
    and the composition's against the engine's LIMIT (sagekit/upgrades.py)."""
    from assets.cah.pack.design import ARCHIVE
    ea, others = U.ea_names(), U.installed_ours(skip=(ARCHIVE,))
    return lambda ours: U.tally(dict(others, cah=U.names(ours["upgrades"])), ea)


def check(ea, ours, models, ours_models, fragments):
    """The lint on EA's data and on ours, then broken copies that must each fail."""
    known = labels()
    report = {"ea_lint": lint(ea, {}, known), "ours_lint": lint(ours, models, known, ours_models) + append_only(ea, ours)}
    limit = upgrade_limit()
    total, over, report["upgrades"] = limit(ours)
    print(report["upgrades"])
    report["ours_lint"] += over
    ups = upgrades(ours["upgrades"])
    frag = fragments[0]
    first = {}
    for sub, rows in frag["lists"].items():
        for g, names in rows.items():
            first.setdefault(g, names[0])
    cf = "class_" + frag["class_file"]
    broken = {}
    g0 = next(iter(first))
    ea_row = lists(ea[cf], upgrades(ea["upgrades"]))
    some_row = next(r[g0] for r in ea_row.values() if r.get(g0))
    b = dict(ours)
    b[cf] = re.sub(r"(%s)(\s+@?%s\b)" % (re.escape(some_row[0]), re.escape(some_row[1])), r"\1 %s\2" % first[g0], b[cf], 1) \
        if len(some_row) > 1 else b[cf].replace(some_row[0], "%s %s" % (first[g0], some_row[0]), 1)   # rows may mark a default @
    broken["inserted_mid_list"] = append_only(ea, b)
    b = dict(ours)
    label = LABELS[ups[first[g0]]["GroupName"]][0]
    key = "weapons" if g0 == "CreateAHero_Weapon" else "bling"
    b[key] = b[key].replace("NameTag\t\t\t = %s" % label, "NameTag\t\t\t = CAH:NoSuchLabel")
    broken["missing_label"] = lint(b, models, known, ours_models)
    b = dict(ours)
    b["remove"] = b["remove"].replace("TriggeredBy\t\t\t= %s" % first[g0], "TriggeredBy\t\t\t= Upgrade_NoSuchThing")
    broken["no_group_clear"] = lint(b, models, known, ours_models)
    gone = {m: meshes - {frag["parts"][0].upper()} for m, meshes in models.items()}
    broken["part_missing_from_model"] = lint(ours, gone, known, ours_models)
    weapons = [u for rows in frag["lists"].values() for u in rows.get("CreateAHero_Weapon", [])]
    if weapons:
        b = dict(ours)
        b["wupg"] = b["wupg"].replace("Conditions\t\t  =\t%s" % ws_flag(weapons[0]), "Conditions = NONE_SUCH")
        broken["weapon_set_missing"] = lint(b, models, known, ours_models)
    b = dict(ours)
    b["models"] = ea["models"]
    broken["models_not_ours"] = lint(b, models, known, ours_models)
    b = dict(ours)
    b["upgrades"] += "".join("Upgrade Upgrade_SKH_Spare%04d" % i + NL + "End" + NL for i in range(U.LIMIT - total + 1))
    broken["over_upgrade_limit"] = limit(b)[1]
    report["broken"] = {k: v[:1] for k, v in broken.items()}
    if report["ea_lint"] or report["ours_lint"] or not all(broken.values()):
        raise SystemExit("INI lint failed: %s" % ({k: v for k, v in report.items() if k != "broken" and v} or
                                                  {k: v for k, v in broken.items() if not v}))
    return report


def write(ours, ea, out, fragments):
    """The composed files into `out` (member paths); {key: member} of what it wrote."""
    keys = list(SHARED) + ["class_" + c for c in dict.fromkeys(fr["class_file"] for fr in fragments)]
    allm = members({k: 1 for k in keys})
    for k in keys:
        dst = Path(out) / allm[k].replace("\\", "/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(ours[k].encode("latin-1"))
    changed = {k: [sum(1 for l in difflib.unified_diff(ea[k].splitlines(), ours[k].splitlines(), lineterm="", n=0)
                       if l[:1] == s and l[:3] != s * 3) for s in "+-"] for k in keys}
    return {k: allm[k] for k in keys}, changed
