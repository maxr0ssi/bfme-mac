"""A unit's asset.dat records, written and taken back one record at a time, in any order.

The faction installer restores a whole asset.dat from its backup, so its installs revert last in,
first out. A unit's records are its own: its model's record (patched, or filed under its own
name), its private textures and mask, and its meshes' object records. Revert puts exactly those
back as EA's pristine cache (asset.dat.orig) has them, after checking they are still the ones the
install wrote; every other record stays byte for byte, so builders, factions and later installs
come and go in any order.
"""
import struct

from ..formats.assetcache import AssetCache
from ..install import cache_records, op_scope, stage_ops
from ..pack import index, keys_of


def copy(cache, data=None):
    c = AssetCache.__new__(AssetCache)
    c.path, c.data = cache.path, cache.data if data is None else data
    return c


def written(ops):
    """The record keys the ops write; a model's 'objects' key covers its single objects."""
    keys = []
    for op in ops:
        keys += [k for k in keys_of(op)[1] if k not in keys]
    whole = {k[1] for k in keys if k[0] == "objects"}
    return [k for k in keys if not (k[0] == "object" and k[1] in whole)]


def staged(cache, ops, model):
    """A copy of `cache` with the ops applied (model(name) -> the shipped file's path or bytes)."""
    c = copy(cache)
    stage_ops(c, [(op, model) for op in ops])
    return c


def _spans(cache, key):
    """[(start, end)] of the records `key` names, in cache order."""
    assets, _, objs = cache.sections()
    if key[0] == "asset":
        return [(s, e) for n, s, e in assets if n.lower().decode("latin-1") == key[1]]
    return [(s, e) for f, o, s, e in objs if f.lower().decode("latin-1") == key[1]
            and (key[0] == "objects" or o.upper().decode("latin-1") == key[2])]


def restore(live, pristine, keys):
    """live's bytes with the records `keys` name as pristine has them: replaced in place where
    both have them, removed where pristine has none. Every other record is left as it is."""
    edits, delta = [], [0, 0]
    for key in keys:
        have, want = _spans(live, key), [pristine.data[s:e] for s, e in _spans(pristine, key)]
        if want and len(want) != len(have):
            raise SystemExit("asset.dat: %s has %d records, EA's cache %d; cannot put EA's back in place"
                             % (" ".join(key), len(have), len(want)))
        edits += [(s, e, want[i] if want else b"") for i, (s, e) in enumerate(have)]
        if not want:
            delta[0 if key[0] == "asset" else 1] -= len(have)
    data = live.data
    for s, e, rec in sorted(edits, reverse=True):
        data = data[:s] + rec + data[e:]
    count, objects = struct.unpack_from("<II", data, 8)
    data = data[:8] + struct.pack("<II", count + delta[0], objects + delta[1]) + data[16:]
    out = copy(live, data)
    out.sections()                                              # still parses end to end
    now, ea = index(out), index(pristine)
    bad = [k for k in keys if now.get(tuple(k), []) != ea.get(tuple(k), [])]
    if bad:
        raise SystemExit("asset.dat: %s did not come back as EA's" % bad[:3])
    return data


def unstage(live, pristine, ops, model):
    """live's bytes with the unit's records back to EA's. Refuses when they are not the records
    staging `ops` onto EA's cache writes (another install changed them since)."""
    keys = written(ops)
    ours, now = index(staged(pristine, ops, model)), index(live)
    changed = [k for k in keys if now.get(k, []) != ours.get(k, [])]
    if changed and any(now.get(k, []) != index(pristine).get(k, []) for k in changed):
        raise SystemExit("asset.dat %s: %s are not the records this unit wrote; refusing to change them"
                         % (live.path, ", ".join(" ".join(k) for k in changed[:3])))
    scope = op_scope(ops)
    data = restore(live, pristine, keys)
    if cache_records(copy(live, data), *scope) != cache_records(live, *scope):
        raise SystemExit("asset.dat %s: reverting would change unrelated records" % live.path)
    return data


def selfcheck():
    """Two units' records written in one order and taken back in the other, on a synthetic cache."""
    from types import SimpleNamespace
    from unittest.mock import patch

    def string(name):
        return bytes([len(name)]) + name.encode()

    def texture(name):
        n = name.encode()
        return bytes([len(n)]) + n + b"\0" * 8 + struct.pack("<H", 1) + bytes([len(n)]) + n + b"XET\0" + b"\0" * 8

    def model(name, body, size):
        return string(name + ".w3d") + b"\0" * 8 + struct.pack("<H", 1) + string("%s.%s" % (name.upper(), body)) \
            + b"HSEM" + struct.pack("<II", 8, size)

    def obj(name, body, tex):
        return string(name + ".w3d") + string("%s.%s" % (name.upper(), body)) + struct.pack("<H", 1) + string(tex)
    assets = [texture("a.tga"), model("am", "BODY", 64), texture("b.tga"), model("bm", "BODY", 64)]
    objects = [obj("am", "BODY", "a.tga"), obj("bm", "BODY", "b.tga")]
    ea = AssetCache.__new__(AssetCache)
    ea.path, ea.data = "pristine", b"ALAE" + struct.pack("<III", 1, len(assets), len(objects)) + b"".join(assets + objects)
    units = {"a": [("patch", "am.w3d"), ("texture", "ax.tga", "a.tga", "am.w3d", "AM.BODY")],
             "b": [("patch", "bm.w3d"), ("texture", "bx.tga", "b.tga", "bm.w3d", "BM.BODY")]}

    def entries(path):
        name = path if isinstance(path, str) else "am"
        return SimpleNamespace(cache_entries=lambda: [("%s.BODY" % name[:2].upper(), b"HSEM", 100, 200)])
    with patch("sagekit.formats.assetcache.W3DFile", side_effect=entries):
        live = copy(ea)
        for u in ("a", "b"):
            live = staged(live, units[u], lambda m: m[:2])
        for u in ("a", "b"):                                    # first in, first out
            live = copy(live, unstage(live, ea, units[u], lambda m: m[:2]))
        assert live.data == ea.data, "records did not come back as EA's"
        live = staged(staged(ea, units["a"], lambda m: m[:2]), units["b"], lambda m: m[:2])
        at = live.data.rfind(string("ax.tga"))                 # AM.BODY's dependency, changed since
        tampered = copy(live, live.data[:at] + string("zz.tga") + live.data[at + 7:])
        try:
            unstage(tampered, ea, units["a"], lambda m: m[:2])
        except SystemExit:
            pass
        else:
            raise AssertionError("a changed record was overwritten")
    print("PASS: unit records staged in one order and reverted in the other; changed records refused")
