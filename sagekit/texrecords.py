"""asset.dat records for the textures our UI archives ship (sagekit/hud, sagekit/ui2x, sagekit/icons).

The game draws a texture only when asset.dat files it. A texture's record is its name, a timestamp
and one TEX entry with offset and size 0: no size, no format (formats/assetcache.py). Without a
record the engine draws its missing-texture magenta, as the per-faction palantir frames did in game
on 2026-10-04 (new names, apt_palantirexport_23..62, no record; EA's names in the same archive,
at twice EA's size, drew). So a texture at a new size or format under EA's name keeps EA's record
(EA's own 2.02 ResourceBarIcons, a 512x64 page, has the same zero-size record as every other), and
a texture of a new name needs one: a copy of a record of its own movie or page family (the record
is name and timestamp only), written and taken back one record at a time (sagekit/units/records.py),
every other record byte for byte.

    python3 -m sagekit.texrecords        the self-check (synthetic cache: plan, write, verify, revert)
"""
import os
import re
from pathlib import Path

from . import paths
from .formats.assetcache import AssetCache

TEXTURE = (".tga", ".dds")


def record_name(member):
    """The record name of an archive member: its file name, lower case, as .tga (EA files DDS pages
    under their .tga names)."""
    base = member.replace("\\", "/").split("/")[-1].lower()
    return base[:-4] + ".tga" if base.endswith(".dds") else base


def textures(members):
    return sorted(m for m in members if m.lower().endswith(TEXTURE))


def live_caches(game="rotwk", orig=False):
    """{live asset.dat path: AssetCache} in the game's search order (orig: EA's pristine copies)."""
    out = {}
    for g in paths.SEARCH_ORDER[game]:
        live = os.path.join(paths.GAMEDIRS[g], "asset.dat")
        src = live + ".orig" if orig and os.path.exists(live + ".orig") else live
        if os.path.exists(src):
            out[live] = AssetCache(src)
    return out


def unfiled(members, caches):
    """The texture members no cache files (caches: AssetCaches, or {path: AssetCache})."""
    caches = list(caches.values()) if isinstance(caches, dict) else list(caches)
    names = set()
    for c in caches:
        names.update(n.decode("latin-1") for n in c.texture_names())
    return [m for m in textures(members) if record_name(m) not in names]


def like_of(name, filed):
    """The record a new texture copies: the first filed texture of its family (`apt_<movie>_<n>.tga`:
    the same movie; `<page>_<nnn>.tga`: the same page set), else None."""
    stem = re.sub(r"_\d+\.tga$", "_", name)
    if stem == name:
        return None
    fam = sorted((f for f in filed if f.startswith(stem) and re.fullmatch(r"\d+\.tga", f[len(stem):])),
                 key=lambda f: int(f[len(stem):-4]))
    return fam[0] if fam else None


def plan(members, pristine=None):
    """[op] registering every texture member EA's caches do not file, as ("texture", new, like, None,
    None) (sagekit/install.py ops). Raises when a new name has no family record to copy."""
    pristine = live_caches(orig=True) if pristine is None else pristine
    filed = set()
    for c in pristine.values():
        filed.update(n.decode("latin-1") for n in c.texture_names())
    ops = []
    for m in unfiled(members, pristine):
        like = like_of(record_name(m), filed)
        if like is None:
            raise SystemExit("%s: a new texture name with no record of its family to copy" % m)
        ops.append(("texture", record_name(m), like, None, None))
    return ops


def route(ops):
    """{live asset.dat: [op]}: each record goes into the cache that files the record it copies."""
    from .game import Install
    return Install().route_cache_ops(ops) if ops else {}


def _nomodel(name):
    raise SystemExit("texture records only: %s" % name)


def update(old, new):
    """{Path(live asset.dat): bytes}: the live caches with the records `old` ({live: [op]}, what the
    installed archive registered) taken back and `new` ({live: [op]}) written; refuses records
    another install changed since. Only caches whose bytes change are returned."""
    from .units import records
    out = {}
    for live in sorted(set(old) | set(new)):
        cache, pristine = AssetCache(live), AssetCache(live + ".orig")
        data = cache.data
        if old.get(live):
            data = records.unstage(cache, pristine, [tuple(op) for op in old[live]], _nomodel)
        if new.get(live):
            base = records.copy(cache, data)
            staged = records.staged(base, [tuple(op) for op in new[live]], _nomodel)
            if records.unstage(staged, pristine, [tuple(op) for op in new[live]], _nomodel) != data:
                raise SystemExit("asset.dat %s: taking the records back would not give today's cache" % live)
            data = staged.data
        if data != cache.data:
            out[Path(live)] = data
    return out


def check(members, what):
    """(ok, line) for a check suite: on copies of EA's caches with the installer's records written,
    every texture member is filed (the per-faction palantir shipped 14 names with none)."""
    from .units import records
    pristine = live_caches(orig=True)
    try:
        ops = plan(members, pristine)
        copies = {p: records.copy(c) for p, c in pristine.items()}
        for live, o in route(ops).items():
            copies[live] = records.staged(copies[live], o, _nomodel)
    except SystemExit as e:
        return False, "asset.dat: %s: %s" % (what, e)
    missing = unfiled(members, copies)
    if missing:
        return False, "asset.dat: %s: no record for %s (drawn magenta)" % (what, ", ".join(map(record_name, missing[:8])))
    new = "; the installer registers %d new names (%s, copies of %s)" % (
        len(ops), ", ".join(o[1] for o in ops[:3]) + (", ..." if len(ops) > 3 else ""),
        ", ".join(sorted({o[2] for o in ops}))) if ops else ""
    return True, "asset.dat files every texture %s ships (%d)%s" % (what, len(textures(members)), new)


def verify(members, caches, what):
    """SystemExit naming every texture member `caches` do not file (after an install, or staged)."""
    missing = unfiled(members, caches)
    if missing:
        raise SystemExit("%s: asset.dat files no record for %d texture(s), which the game draws magenta: %s"
                         % (what, len(missing), ", ".join(record_name(m) for m in missing[:8])))
    return "asset.dat files every texture %s ships (%d)" % (what, len(textures(members)))


def selfcheck():
    """Plan, write, verify and take back a new texture's record on a synthetic cache."""
    import struct
    import tempfile

    def texture(name):
        n = name.encode()
        return bytes([len(n)]) + n + b"\1" * 8 + struct.pack("<H", 1) + bytes([len(n)]) + n + b"XET\0" + b"\0" * 8

    with tempfile.TemporaryDirectory() as tmp:
        live = os.path.join(tmp, "asset.dat")
        names = ["apt_palantirexport_17.tga", "apt_palantirexport_2.tga", "other.tga"]
        data = b"ALAE" + struct.pack("<III", 1, len(names), 0) + b"".join(texture(n) for n in names)
        for p in (live, live + ".orig"):
            with open(p, "wb") as fh:
                fh.write(data)
        members = ["art\\textures\\apt_palantirexport_17.tga", "art\\textures\\apt_palantirexport_29.tga",
                   "art\\compiledtextures\\ot\\other.dds"]
        pristine = {live: AssetCache(live + ".orig")}
        assert unfiled(members, pristine) == ["art\\textures\\apt_palantirexport_29.tga"]
        ops = plan(members, pristine)
        assert ops == [("texture", "apt_palantirexport_29.tga", "apt_palantirexport_2.tga", None, None)], ops
        written = update({}, {live: ops})[Path(live)]
        with open(live, "wb") as fh:
            fh.write(written)
        verify(members, {live: AssetCache(live)}, "the self-check")
        assert update({live: ops}, {live: ops}) == {}, "a reinstall changed the cache"
        back = update({live: ops}, {})[Path(live)]
        assert back == data, "the records did not come back as EA's"
        try:
            verify(members, pristine, "the self-check")
        except SystemExit:
            pass
        else:
            raise AssertionError("a texture without a record passed")
    print("PASS: a new texture name planned, registered, verified and taken back; an unfiled one refused")


if __name__ == "__main__":
    selfcheck()
