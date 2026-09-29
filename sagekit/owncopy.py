"""Own copies of shared models: a recipe redesigns EA model X but ships it as a new model Y.

Several of EA's models are drawn by more than one faction (the Dwarven castle-wall tower, postern
and trebuchet platform draw Gondor's GBWallTwr, GBWallPG, GBWallTreb, which Men and Arnor draw
too; Isengard, Mordor and the Goblins share WBCave). Redesigning X in place would change every
faction that shows it. A recipe declares instead

    source = "GBWallTwr"            # EA's model: what is measured, read and redesigned
    own_model = "DBWallTwr2"        # the name it ships under
    replaces = ("GBWALLUPGRD",)     # optional: EA's stand-in meshes the redesign takes over

and the pipeline works on a copy of X named Y from the extract step on:
  - the copy: X's hierarchy, containers and HLOD renamed (w3d.rename_model), the `replaces`
    meshes dropped (w3dcopy.drop_meshes); this is the build's source model, so every check that
    compares against "the original" compares against the copy, and EA's X is kept beside it
    (Workspace.reference_model) for the before render and the footprint;
  - lifecycle models: X_D1, X_A... that the covered Draw modules show become Y_D1, Y_A (shipped_name);
  - INI: `Model = X` -> `Model = Y` in the covered Draw modules' states only (ini.set_model), so
    the other factions' objects and this object's other modules keep EA's model;
  - asset cache: Y gets a record of its own, a copy of X's (AssetCache.add_model: X's timestamp
    and object records renamed, the file's own layout), filed where X is - the engine draws no
    model its caches do not file (the Men citadel, Elven barracks and mallorn were invisible
    in game on 2026-09-28 without one); the own texture gets its record like any recipe's and the
    copied object switches to it (Install.route_cache_ops);
  - texture: the target's own texture (own_textures), as for every recipe - X's sheet is never shipped.

Y must be a name no archive provides and no cache files: an EA record for it would describe EA's
layout (EA left unused DBWallTwr, DBWallPG and DBWallTreb in the archives, filed in BFME2's cache).
Animations keep playing from EA's files (AnimationName = X.anim loads X's file, which stays).
"""
from .formats.w3d import W3DFile, rename_model
from .formats.w3dcopy import drop_meshes


def shipped_name(b, model):
    """The name EA model `model` ships under: Y for X, Y_D1 for X_D1; unchanged without own_model."""
    if not b.own_model:
        return model
    src = b.source.lower()
    if model.lower() == src:
        return b.own_model
    if model.lower().startswith(src + "_"):
        return b.own_model + model[len(src):]
    # a skinned source names its family without the suffix: NBElvnBarx_SKN draws NBElvnBarx_A, _D1...
    if src.endswith("_skn") and b.own_model.lower().endswith("_skn") and model.lower().startswith(src[:-4] + "_"):
        return b.own_model[:-4] + model[len(src) - 4:]
    return model


def prepare(b, model, data):
    """EA's `model` as our copy: renamed, the `replaces` meshes dropped (the healthy model only)."""
    name = shipped_name(b, model)
    if name.lower() == model.lower():
        return data
    if len(name) > 15:
        raise ValueError("%s: own model name %s longer than 15 characters" % (b.id, name))
    out = rename_model(data, model, name)
    if b.replaces and model.lower() == b.source.lower():
        missing = [n for n in b.replaces if n.upper() not in W3DFile(out).meshes]
        if missing:
            raise ValueError("%s: %s has no mesh %s to replace" % (b.id, model, missing))
        out = drop_meshes(out, b.replaces)
    return out


def check_free(b, install, models):
    """Refuse own names some archive already provides or some cache already files."""
    for m in models:
        name = shipped_name(b, m)
        if name.lower() == m.lower():
            continue
        taken = install.has_model(name) or any(c.has_model(name.lower() + ".w3d") for c in install.asset_caches().values())
        if taken:
            raise ValueError("%s: own model name %s is taken by EA's files - pick another" % (b.id, name))


def ini_ops(b, install, models):
    """{INI archive path: [('model', object, tag, EA model, our model)]} for the covered Draw
    modules showing any of `models` (the source and its derived models)."""
    out = {}
    if not b.own_model:
        return out
    want = {m.lower() for m in models}
    for draws in b.objects(install).values():
        for d in draws:
            if not b.covers(d):
                continue
            for m in b.own_models(d):                   # (a build variation's own models only)
                if m.lower() in want and shipped_name(b, m).lower() != m.lower():
                    op = ("model", d.object, d.tag, m, shipped_name(b, m))
                    if op not in out.get(d.file, []):
                        out.setdefault(d.file, []).append(op)
    return out


def extent(b, ws, lo, hi):
    """The target's (lo, hi) box grown by the `replaces` meshes of EA's model, in the frame the
    checks measure the target in (mesh-local, or model space for world_space): the redesign takes
    their volume over, so the footprint and height limits are those of what EA showed there."""
    if not b.replaces:
        return lo, hi
    from .formats.w3dframes import apply, inverse, mesh_frames
    data = open(ws.reference_model, "rb").read()
    f, frames = W3DFile(data), mesh_frames(data)
    back = None if b.world_space else inverse(frames[b.target])
    lo, hi = list(lo), list(hi)
    for n in b.replaces:
        for v in f.meshes[n.upper()].verts:
            p = apply(frames[n.upper()], v)
            p = apply(back, p) if back else p
            for i in range(3):
                lo[i], hi[i] = min(lo[i], p[i]), max(hi[i], p[i])
    return lo, hi


def checks(b, ws, r):
    """The copy is EA's model under our name with only the declared meshes gone."""
    if not b.own_model:
        return
    ea, mine = W3DFile(ws.reference_model), W3DFile(ws.source_model)
    r.section("own copy: %s ships as %s" % (b.source, b.own_model))
    names = mine.object_names()
    r.check("every object name carries %s" % b.own_model.upper(),
            all(n.split(":")[-1].split("*")[-1].split(".")[0] == b.own_model.upper() for n in names), str(names))
    gone = sorted(set(ea.meshes) - set(mine.meshes))
    r.check("meshes dropped: exactly `replaces`", gone == sorted(n.upper() for n in b.replaces), str(gone))
    same = all(mine.meshes[n].verts == ea.meshes[n].verts and mine.meshes[n].textures == ea.meshes[n].textures
               for n in mine.meshes)
    r.check("the other meshes are EA's (geometry, textures)", same, ", ".join(sorted(mine.meshes)))
