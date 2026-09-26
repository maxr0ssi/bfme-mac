"""Faction copies of shared EA sheets: meshes we ship that EA paints from another faction's sheet.

Some meshes a building ships untouched are painted from a sheet other factions draw too: the
Dwarven siege works' ANVIL (in DBForge and every one of its state models) samples EBForge.tga, the
Elven forge's sheet, which the Elves' EregionForge and EBFAnvil models also draw; Isengard, Mordor
and the Goblins share WBCave, three factions MBLumberMill. Recolouring the sheet itself would
change the other factions, so the faction declares an own copy in its Style:

    shared_sheets = {"EBForge.tga": "DBAnvil.tga"}      # EA's shared sheet -> the faction's copy

Declared per faction rather than per recipe: the faction has one palette, so every building of it
that shows the sheet would get the same pixels - one copy per faction, one name, one record, and a
new building that shows the sheet picks it up without saying so. The pipeline's `shared` step then

  - finds the declared sheets (and their state variants: _D, _D1, _Snow...) in the models the build
    ships (healthy, derived, lifecycle - whatever is under out/art/w3d once those steps ran), and
    renames them in every mesh of those files, in place (W3D stores the names length-prefixed, so
    the copy's name keeps EA's length; the normal map stays EA's: it carries no colour);
  - recolours each sheet into the faction palette exactly as `sagekit sheets` does (the same module,
    size and layers), kept in build/assets/<faction>/_sheets/shared/ and redone when the style or
    the recolouring code is newer, and ships it under the copy's name;
  - adds `Texture = <copy> <copy variant>` next to the INI's own swaps of the EA sheet (damage,
    snow), shipping those variants too;
  - records it all in work/shared_sheets.json, from which the build and the install take the cache
    ops (the copy's record, copied from EA's; each shipped object's dependency switched to it).

EA's sheet, its variants and its normal map are never shipped. The checks compare our files with
EA's under the same renames (`renamed`), so "untouched" still means byte for byte apart from them.
"""
import json
import os
import re
import sys

from . import paths
from .formats.textures import compiled_path, dds_info, full_chain
from .formats.w3d import MESH, W3DFile, chunks
from .taxonomy import own_variant_name, variant_class

NAME_RE = re.compile(rb"(?<![A-Za-z0-9_])([A-Za-z0-9_]+)(\.(?:tga|dds))(?=\0)", re.I)
RECOLOUR_CODE = [os.path.join(paths.REPO, "sagekit", "paint", f) for f in ("sheets.py", "layers.py", "masks.py")]


# ------------------------------------------------------------------------------------ names
def declared(style):
    """{EA sheet: copy} from the style, checked: same length, .tga, no normal map or height field."""
    out = dict(getattr(style, "shared_sheets", None) or {})
    for ea, own in out.items():
        if len(ea) != len(own) or not ea.lower().endswith(".tga") or not own.lower().endswith(".tga"):
            raise ValueError("shared_sheets %s -> %s: both .tga names of the same length (W3D patches them in place)" % (ea, own))
        if any(k in ea.lower() for k in style.sheet_skip):
            raise ValueError("shared_sheets %s: normal maps and height fields carry no colour - leave them EA's" % ea)
    return out


def pair(texture, decl):
    """(EA name, our name) if `texture` is a declared sheet, its copy, or a state variant of either
    (EBForge_D.tga -> DBAnvil_D.tga), keeping the reference's extension; else None."""
    stem, ext = texture[:-4], texture[-4:]
    for ea, own in decl.items():
        for mine in (ea[:-4], own[:-4]):
            if stem.lower() == mine.lower():
                return ea[:-4] + ext, own[:-4] + ext
            if stem.lower().startswith(mine.lower() + "_") and variant_class(texture):
                tail = stem[len(mine):]
                return ea[:-4] + tail + ext, own[:-4] + tail + ext
    return None


def rename(data, decl):
    """Model bytes with every declared sheet (and variant) referenced in a mesh swapped for the
    faction's copy. Same length, so no chunk size or cache offset moves; idempotent."""
    if not decl:
        return data
    out = bytearray(data)
    for t, o, s, _ in chunks(data, 0, len(data)):
        if t != MESH:
            continue
        for m in NAME_RE.finditer(data, o, o + 8 + s):
            name = (m.group(1) + m.group(2)).decode("latin-1")
            p = pair(name, decl)
            if p and p[1] != name:
                out[m.start(1):m.end(2)] = p[1].encode("latin-1")
    return bytes(out)


def renamed(ws, data):
    """EA's model bytes as this faction ships them (for the checks' "untouched" comparisons)."""
    return rename(data, declared(ws.b.style))


# ------------------------------------------------------------------------------------ the record
def record_path(ws):
    return ws.path("work", "shared_sheets.json")


def record(ws):
    """{"textures": {copy: EA sheet}, "uses": [[model file, CONTAINER.MESH, copy, EA sheet]],
    "swaps": {ini member: {EA sheet: {EA variant: [copy, copy variant]}}}} as the step wrote it."""
    p = record_path(ws)
    return json.load(open(p)) if os.path.exists(p) else {"textures": {}, "uses": [], "swaps": {}}


def shipped_models(ws):
    """[(file name, path)] of every model under out/art/w3d."""
    root, out = ws.path("out", "art", "w3d"), []
    for d, _, names in os.walk(root):
        out += [(f, os.path.join(d, f)) for f in sorted(names) if f.lower().endswith(".w3d")]
    return out


def texture_map(ws):
    """{copy (lower case): shipped file} for the renders."""
    return {own.lower(): ws.shipped_texture(own, ".dds") for own in record(ws)["textures"]}


def cache_ops(b):
    """Building.cache_ops entries: each copy's record (copied from EA's sheet) and, per shipped
    object that draws it, the dependency switched from EA's sheet to the copy."""
    from .workspace import Workspace
    rec = record(Workspace(b))
    ops = [("texture", own.lower(), ea.lower(), None, None) for own, ea in sorted(rec["textures"].items())]
    return ops + [("texture", own.lower(), ea.lower(), model, obj) for model, obj, own, ea in rec["uses"]]


def ini_ops(b):
    """{INI member: [('swaps', EA sheet, {EA variant: (copy, copy variant)})]}: the copy's state
    swaps beside EA's (sagekit/formats/ini.py add_texture_swaps)."""
    from .workspace import Workspace
    out = {}
    for member, bases in record(Workspace(b))["swaps"].items():
        out[member] = [("swaps", ea, {v: tuple(p) for v, p in swaps.items()}) for ea, swaps in sorted(bases.items())]
    return out


# ------------------------------------------------------------------------------------ the step
def ini_swaps(b, install, copies):
    """{ini member: {EA sheet: {EA variant: [copy, copy variant]}}} for the building's objects' states
    that swap a copied sheet (EA's typos - a swap to a file no archive has - are left out)."""
    out = {}
    for draws in b.objects(install).values():
        for d in draws:
            for st in d.states:
                for old, new in st.textures:
                    ea = next((e for e in copies.values() if e.lower() == old.lower()), None)
                    if ea is None or not install.owner(compiled_path(new, ".dds")):
                        continue
                    own = next(o for o, e in copies.items() if e == ea)
                    out.setdefault(d.file, {}).setdefault(ea, {})[new] = [own, own_variant_name(ea, own, new)]
    return out


def check_free(b, install, names):
    """Refuse a copy name EA's archives or caches already use, or a building's own texture."""
    from .registry import building_ids, load
    theirs = set()
    for bid in building_ids():
        theirs |= {t.lower() for t in load(bid).texture_names().values()}
    for n in names:
        taken = install.owner(compiled_path(n, ".dds")) or install.owner(compiled_path(n, ".tga")) \
            or any(c.has_texture(n) for c in install.asset_caches().values()) or n.lower() in theirs
        if taken:
            raise ValueError("%s: shared-sheet copy name %s is taken - pick another in the style" % (b.id, n))


def recolour(step, ea, own):
    """The faction's recoloured copy of EA sheet `ea` (a DDS path), made like `sagekit sheets` makes
    the faction's own sheets; redone when the style or the recolouring code is newer."""
    import subprocess
    from .pipeline import REALESRGAN, StepFailed, blender_slot
    style, g = step.b.style, step.p.install
    member = compiled_path(ea, ".dds")
    root = os.path.join(paths.BUILD, style.faction, "_sheets")
    out = os.path.join(root, "shared", *compiled_path(own, ".dds").split("\\"))
    deps = RECOLOUR_CODE + [sys.modules[type(style).__module__].__file__]
    if os.path.exists(out) and os.path.getmtime(out) >= max(os.path.getmtime(p) for p in deps):
        return out
    src = os.path.join(root, "src", member.split("\\")[-1])
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "wb") as fh:
        fh.write(g.read(member))
    size = style.sheet_size(member.split("\\")[-1])
    with blender_slot():
        r = subprocess.run([paths.blender_python(), "-m", "sagekit.paint.sheets", style.faction, src, out, str(size), REALESRGAN],
                           capture_output=True, text=True, cwd=paths.REPO, env=dict(os.environ, PYTHONPATH=paths.REPO))
    if r.returncode:
        raise StepFailed("recolouring %s as %s failed\n%s" % (ea, own, r.stderr[-1500:]))
    print("  recoloured %s -> %s" % (ea, os.path.relpath(out, paths.REPO)))
    return out


def run(step):
    """The pipeline's `shared` step (after ship): rename, recolour, ship, record."""
    import shutil
    from .pipeline import StepFailed
    b, ws, g = step.b, step.ws, step.p.install
    try:
        decl = declared(b.style)
    except ValueError as e:
        raise StepFailed("%s: %s" % (b.id, e))
    copies, uses = {}, []
    for f, path in shipped_models(ws):
        data = open(path, "rb").read()
        new = rename(data, decl)
        for mesh in W3DFile(new).meshes.values():
            for t in mesh.textures:
                p = pair(t, decl)
                if p:
                    copies[p[1]] = p[0]
                    uses.append([f, "%s.%s" % (mesh.container.upper(), mesh.name), p[1], p[0]])
        if new != data:
            with open(path, "wb") as fh:
                fh.write(new)
            print("  %s: %s" % (f, ", ".join(sorted({"%s -> %s" % (u[3], u[2]) for u in uses if u[0] == f}))))
    swaps = ini_swaps(b, g, copies)
    textures = dict(copies)
    for bases in swaps.values():
        textures.update({p[1]: v for swap in bases.values() for v, p in swap.items()})
    try:
        check_free(b, g, textures)
    except ValueError as e:
        raise StepFailed(str(e))
    for own, ea in sorted(textures.items()):
        dest = ws.shipped_texture(own, ".dds")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(recolour(step, ea, own), dest)
        print("  shipped %s (the faction's copy of EA's %s)" % (os.path.relpath(dest, ws.path("out")), ea))
    with open(record_path(ws), "w") as fh:
        json.dump({"textures": textures, "uses": uses, "swaps": swaps}, fh, indent=1)
    if not textures:
        print("  no shared EA sheets in the shipped models")


# ------------------------------------------------------------------------------------ checks
def checks(b, ws, r):
    """Blender-side checks (sagekit/blender/checks_suite.py): copies shipped and registered, no
    shipped model still drawing a declared EA sheet, dependencies and INI swaps switched."""
    from .formats.assetcache import AssetCache
    decl, rec = declared(b.style), record(ws)
    if not decl and not rec["textures"]:
        return
    stale = sorted({"%s %s %s" % (f, n, t) for f, path in shipped_models(ws) for n, m in W3DFile(path).meshes.items()
                    for t in m.textures if (pair(t, decl) or ("",))[0].lower() == t.lower()})
    r.section("shared EA sheets: the faction's own copies (sagekit/sharedsheets.py)")
    r.check("no shipped model draws a shared EA sheet (%s)" % ", ".join(decl), not stale, "; ".join(stale))
    caches = [AssetCache(p) for p in ws.caches()]
    names = {n for c in caches for n in c.texture_names()}
    for own, ea in sorted(rec["textures"].items()):
        path, size = ws.shipped_texture(own, ".dds"), b.style.sheet_size(compiled_path(ea, ".dds").split("\\")[-1])
        i = dds_info(path) if os.path.exists(path) else None
        r.check("%s (copy of %s): %d, DXT, full mips" % (own, ea, size),
                i is not None and (i["width"], i["height"], i["mips"]) == (size, size, full_chain(size)) and i["fourcc"].startswith("DXT"),
                "missing" if i is None else "%dx%d %s %d mips" % (i["width"], i["height"], i["fourcc"], i["mips"]))
        r.check("%s registered in the caches" % own, own.lower().encode() in names, "")
    for model, obj, own, ea in rec["uses"]:
        dep = next((d for d in (c.dependencies(model, obj) for c in caches) if d is not None), None)
        if dep is None:
            r.info("%s %s" % (model, obj), "no object record: nothing to switch")
        else:
            low = [d.lower() for d in dep]
            r.check("%s %s depends on %s, not %s" % (model, obj, own.lower(), ea.lower()),
                    own.lower() in low and ea.lower() not in low, str(dep))
    for member, bases in rec["swaps"].items():
        text = open(ws.out(member), encoding="latin-1").read() if os.path.exists(ws.out(member)) else ""
        for swaps in bases.values():
            for own, var in swaps.values():
                r.check("%s: Texture = %s %s" % (member.split("\\")[-1], own, var),
                        re.search(r"Texture\s*=\s*%s\s+%s\b" % (re.escape(own), re.escape(var)), text, re.I), "")
