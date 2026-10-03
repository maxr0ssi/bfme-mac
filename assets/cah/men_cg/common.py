"""What the Men of the West's two folders (men_cg, men_sm) and the Wizards share: budgets, the
abstract bones the designs ride (named per model by BONE_MAP), part naming and the head seat."""

# vertex caps per sub-object in game (_U, and _M mounted) / on the creation screen (_C): docs/CAH.md
BUDGET = {"CreateAHero_Helmet": (650, 950), "CreateAHero_ShoulderPlates": (700, 1100), "CreateAHero_Shield": (600, 900),
          "CreateAHero_Weapon": (540, 700)}
CLOAK = (900, 1350)


def bones(per_skeleton):
    """BONES {group: every real bone its parts may ride}."""
    use = {"CreateAHero_Helmet": "HEAD", "CreateAHero_Shield": "SHIELD", "CreateAHero_Weapon": "HAND"}
    out = {g: {m[a] for m in per_skeleton.values() if a in m} for g, a in use.items()}
    out["CreateAHero_ShoulderPlates"] = {m[a] for m in per_skeleton.values() for a in ("SPINE", "UARM_L", "UARM_R") if a in m}
    return out


def name_parts(entries, weapons):
    """PARTS in append order from [(sub-object, group, design, name, description, sheet, remap)]:
    the rows' shared upgrades (kit/ini.py row_upgrade: Upgrade_SKH_<CHH|CHSP|CHS><nn> from 01),
    weapons Upgrade_SKH_CHW<nn> on the class's weapon-set numbers `weapons` (docs/CAH.md: Men +
    Wizards 46-51)."""
    from ..kit.ini import row_upgrade
    count, out, w = {}, [], iter(weapons)
    for e in entries:
        g = e[1]
        count[g] = count.get(g, 0) + 1
        up = "Upgrade_SKH_CHW%02d" % next(w) if g == "CreateAHero_Weapon" else row_upgrade(g, count[g])
        out.append(tuple(e) + (up,))
    return out


def wrapped(spec, entries):
    """ENTRIES with every design drawn through fit.wrap (the group's fit, the model's bones;
    helmets seated by spec.HEAD_SEAT)."""
    from .fit import wrap
    return [(n, g, wrap(spec, g, fn, spec.HEAD_SEAT if g == "CreateAHero_Helmet" else None)) + tuple(rest)
            for n, g, fn, *rest in entries]


def budget_fn(own):
    def budget(name, group, kind):
        return own.get(name, BUDGET[group])[0 if kind in ("u", "m") else 1]
    return budget


def seat(cx, cz, k, tilt=0.0, kz=None):
    """Canonical head space (helms.py) -> a subclass's head: centre x, brow height, scale (kz: a
    taller head's own vertical scale)."""
    kz = k if kz is None else kz
    return lambda p: (cx + k * p[0], k * p[1], cz + kz * p[2] + tilt * p[0])
