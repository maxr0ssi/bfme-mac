"""Our staged archives against EA's art, object by object (sagekit/drawcost.py has the cost model).

    python3 -m sagekit.drawcost_report [<archive name part> ...] [--rows] [--scene] [--json out.json]

For every object an archive's INIs define, or whose Draw shows a model the archive replaces in
place, the Draw modules of each state are resolved twice: EA's INI with EA's models, and the
archive's INI with its models (EA's where it ships none). A ChildObject draws its parent's modules.
`--scene` adds the 8-player late-game estimate (sagekit/drawcost_scene.py). `validate()` holds every
object's healthy state to EA's plus a margin (CAP); `sagekit validate` runs it.
"""
import json
import os
import sys

from .drawcost import STATES, Ini, ModelCost, object_cost
from .formats.big import Archive
from .fire_budget import BUDGET, rig_budgets
from .game import Install

# ours <= EA's main-view draws x 1.10 + 2, and EA's render objects + 2: a building may add its house-colour
# model and its fire rig (the two faction standards that are Draw modules of their own), nothing more
CAP = {"objects": 2, "main": 2, "ratio": 1.10}
SKIP = ("-ui2x", "-icons", "-hud", "-fx", "-scenery", "-units", "-cah", "english")


class Side:
    """Models by name: an archive's own first (if any), then the game's (EA's, pristine)."""

    def __init__(self, game, archive=None):
        self.game, self.archive, self._cache = game, archive, {}
        self._own = {}
        if archive is not None:
            self._own = {k.rsplit("\\", 1)[-1][:-4]: k for k in archive.index() if k.endswith(".w3d")}

    def model(self, name):
        key = name.lower()
        if key not in self._cache:
            data = None
            if key in self._own:
                data = self.archive.read(self._own[key])
            else:
                member = "art\\w3d\\%s\\%s.w3d" % (key[:2], key)
                if self.game.owner(member):
                    data = self.game.read(member)
            self._cache[key] = ModelCost(name, data) if data else None
        return self._cache[key]


class Game:
    """EA's side, read once: models, object INIs ({model: {member}}, {object: Ini}), particle rates."""

    def __init__(self):
        from .fire_budget import rates
        self.install = Install()
        self.side = Side(self.install)
        self.by_model, self.index = {}, {}
        for member in self.install.members("data\\ini\\object"):
            if not member.endswith(".ini"):
                continue
            ini = Ini(self.install.read(member).decode("latin-1"))
            for obj in ini.blocks:
                self.index.setdefault(obj, ini)
            for draws in ini.draws.values():
                for d in draws:
                    for m in d.models():
                        self.by_model.setdefault(m.lower(), set()).add(member)
        self.rates = rates(self.install)            # EA's particle INIs with our fire's systems (fire_budget.py)


def compare_archive(path, game, states=STATES):
    """[row] for one staged archive: {object, member, archive, <state>: {"ea": cost, "ours": cost}}."""
    a = Archive(str(path))
    g = game.install
    ours = Side(g, a)
    inis = {k for k in a.index() if k.startswith("data\\ini\\object") and k.endswith(".ini")}
    members = set(inis)
    for k in a.index():
        m = k.rsplit("\\", 1)[-1][:-4]
        if k.endswith(".w3d") and g.owner("art\\w3d\\%s\\%s.w3d" % (m[:2], m)):   # in place: who draws it
            members |= game.by_model.get(m, set())
    parsed = {m: Ini(a.read(m).decode("latin-1")) for m in inis}
    mine_index = dict(game.index)
    for ini in parsed.values():
        mine_index.update({obj: ini for obj in ini.blocks})
    rows = []
    for member in sorted(members):
        mine = parsed.get(member) or Ini(g.read(member).decode("latin-1"))
        ea = Ini(g.read(member).decode("latin-1") if g.owner(member) else "")
        for obj in mine.blocks:
            row = {"object": obj, "member": member, "archive": os.path.basename(str(path))}
            for st, flags in states.items():
                o = object_cost(mine, obj, ours.model, game.rates, flags, mine_index)
                e = object_cost(ea, obj, game.side.model, game.rates, flags, game.index) if obj in ea.blocks else None
                if o or e:
                    row[st] = {"ours": o, "ea": e}
            if "healthy" in row and row["healthy"]["ours"] and _changed(row):
                rows.append(row)
    return rows


def _changed(row):
    """Our art reaches this object: some state draws other counts than EA's (or EA has no such object)."""
    for st in STATES:
        o, e = (row.get(st) or {}).get("ours"), (row.get(st) or {}).get("ea")
        if (o is None) != (e is None) or (o and any(o[k] != e[k] for k in ("objects", "main", "tris", "particles"))):
            return True
    return False


def over_cap(row):
    """Why a row's healthy state breaks the cap against EA's, or None."""
    h = row.get("healthy") or {}
    o, e = h.get("ours"), h.get("ea")
    if not o or not e:
        return None
    why = []
    if o["main"] > e["main"] * CAP["ratio"] + CAP["main"]:
        why.append("main-view draws %d against EA's %d" % (o["main"], e["main"]))
    if o["objects"] > e["objects"] + CAP["objects"]:
        why.append("render objects %d against EA's %d" % (o["objects"], e["objects"]))
    return "; ".join(why) or None


def archives(filters=()):
    from .texbake import staged
    out = []
    for p in staged():
        name = p.name.lower()
        if any(x in name for x in SKIP) or (filters and not any(f.lower() in name for f in filters)):
            continue
        out.append(p)
    return out


def sweep(filters=(), game=None):
    game = game or Game()
    rows = []
    for p in archives(filters):
        rows += compare_archive(p, game)
    return rows


def validate():
    """sagekit validate: no staged object draws more than EA's healthy state plus the margin."""
    try:
        rows = sweep()
    except (FileNotFoundError, OSError) as e:       # no game here: nothing to compare against
        print("skip draw cost: %s" % e)
        return 0
    bad = [r for r in rows if over_cap(r)]
    for r in bad:
        print("FAIL draw cost %s (%s): %s" % (r["object"], r["archive"].strip("!"), over_cap(r)))
    hot = over_budget(rows)                         # the fire budget (sagekit/fire_budget.py, Max 2026-10-04)
    for obj, archive, rig, n, st, cap in hot:
        print("FAIL fire budget %s (%s): its fire %s burns %.1f live particles in the %s state, over %d" % (
            obj, archive.strip("!"), rig, n, st, cap))
    if not hot:
        print("ok   fire budget: every staged building's fire within its budget in every state (sagekit/fire_budget.py)")
    if not bad:
        print("ok   draw cost: %d objects within EA's draws x %.2f + %d and EA's render objects + %d" % (
            len(rows), CAP["ratio"], CAP["main"], CAP["objects"]))
    return len(bad) + len(hot)


def over_budget(rows):
    """[(object, archive, fire rig, live particles, state, budget)] of our fire over its building's budget in
    its worst state (a rig no recipe makes any more: the general budget)."""
    out, caps = [], rig_budgets()
    for r in rows:
        worst = {}
        for st in STATES:
            for rig, n in (((r.get(st) or {}).get("ours") or {}).get("fire") or {}).items():
                if n > worst.get(rig, (0.0, None))[0]:
                    worst[rig] = (n, st)
        for rig, (n, st) in sorted(worst.items()):
            cap = caps.get(rig.lower(), BUDGET)
            if n > cap + 1e-6:
                out.append((r["object"], r["archive"], rig, n, st, cap))
    return out


def plain(c):
    return None if c is None else {k: (sorted(v) if isinstance(v, set) else v) for k, v in c.items()}


def table(rows):
    print("%-34s %-22s %7s %7s %7s %13s %11s %7s %9s" % ("object", "archive", "objects", "main", "shadow",
                                                      "tris", "particles", "house", "us/frame"))
    for r in rows:
        o, e = r["healthy"]["ours"] or {}, r["healthy"]["ea"] or {}

        def pair(k, f="%d"):
            return "%s/%s" % (f % e[k] if e else "-", f % o[k] if o else "-")
        print("%-34s %-22s %7s %7s %7s %13s %11s %7s %9s %s" % (
            r["object"][:34], r["archive"].strip("!")[8:30], pair("objects"), pair("main"), pair("shadow"),
            pair("tris"), pair("particles", "%.0f"), pair("house"), pair("us", "%.0f"), over_cap(r) or ""))


def main(argv):
    out = None
    if "--json" in argv:
        out = argv[argv.index("--json") + 1]
        argv = [x for x in argv if x != out]
    game = Game()
    rows = sweep([x for x in argv if not x.startswith("--")], game)
    if "--rows" in argv:
        table(rows)
    bad = [r for r in rows if over_cap(r)]
    print("%d objects compared, %d over the cap (EA's draws x %.2f + %d, EA's render objects + %d)" % (
        len(rows), len(bad), CAP["ratio"], CAP["main"], CAP["objects"]))
    if "--scene" in argv:
        from .drawcost_scene import report
        report(rows)
    if out:
        with open(out, "w") as fh:
            json.dump([{k: ({side: plain(c) for side, c in v.items()} if k in STATES else v)
                        for k, v in r.items()} for r in rows], fh, indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
