"""Building packs: a faction's finished buildings for players without Blender, holding none of EA's files.

    bfme-mac-buildings-<faction>-<version>/
        members.bin     our bytes: per archive member a delta against EA's files, or the file itself
        pack.json       how to rebuild each archive from the player's game, and the asset.dat edits

The installer rebuilds `!!!!!!!!!!!sagekit-<faction>.big` (and the faction's builder,
`!!!!!!!!!!!!sagekit-<unit>-builder.big`, and its HUD icon pages, `!!!!!!!!!!!!!!sagekit-icons-<faction>.big`,
sagekit/icons/install.py) from the player's own EA files plus members.bin, checks
every member and archive by SHA-256, and installs it as `sagekit install` would.

pack.json:
    format, faction, version, buildings     2; the recipes built into the archive
    data     {name, sha256, size}           members.bin
    sources  {EA member: [sha256, archive]} every EA file a member is rebuilt from, as RotWK 2.02 has it
    archives [{name, sha256, size, magic, members: [member]}], each member in archive order:
        {name, sha256, size, at: [offset, length] in members.bin, kind, from: [EA member]}
        kind  delta   sagekit/delta.py against `from` (the EA files the build made it from)
              ours    the file itself: nothing of it is in an EA file (`why` says which were checked)
              append  EA's text (`from`) plus our lines; every chosen pack's lines for one member go
                      into it together, in faction order (the builders' housecolor.ini)
    literal  {inserted, bytes, longest_ea_run, member}: the build's check that the inserted bytes
             hold no run of more than MAX_SHARED bytes from any EA file they were checked against
    caches   {rotwk|bfme2: {
        ops       [op] in order, as sagekit install applies them: ["patch", model],
                  ["model", new, like] (a model of our own name, filed as a copy of EA's),
                  ["texture", new, like, model|null, object|null]
        models    {model: [[entry, tag, offset, size]]}: each model op's record, from the shipped file
        requires  [[key..., sha256]]: EA's records the ops read, as this Mac's pristine cache has them
        result    [[key..., sha256]]: every record the ops write, as it must come out
        pristine  sha256 of the whole pristine cache (an exact match is reported, not required)}}

A key is ["asset", name] (every asset record of that name), ["objects", model] (all of a model's
object records) or ["object", model, OBJECT]; its hash covers those records' bytes in cache order.

`build` (sagekit/packbuild.py; scripts/make-release.sh --buildings) reads the staged installation (`sagekit install
<faction> --check`, and `python3 -m sagekit unit <faction>/porter --stage` for a builder), EA's
files and this Mac's asset.dat.orig files. `install` (scripts/install.sh --buildings) works on any
prefix: every chosen pack in one transaction, a scoped receipt and backups in
<prefix>/bfme-mac-buildings/; `revert` restores exactly what it changed. A pack whose game does not
match (another version, a missing or different EA file or record) is skipped. The installer is
standard library only.

    python3 -m sagekit.pack build <faction> --version <v> --out <dir>
    python3 -m sagekit.pack install <pack dir>... [--prefix <wine prefix>]
    python3 -m sagekit.pack revert|status [--list] [--prefix <wine prefix>]
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from . import delta, paths
from .formats.assetcache import AssetCache, CacheError
from .formats.big import bigtool, norm
from .formats.w3d import W3DFile
from .game import Install
from .install import apply, atomic, revert_receipt, stage_ops
from .pipeline import game_running

FORMAT = 2
GAMES = {"rotwk": "RotWK", "bfme2": "BFME2"}
DONE = {}      # {faction: {building ids}} for a faction the release holds only part of
STATE = "bfme-mac-buildings"
DATA = "members.bin"
MAX_SHARED = 256        # longest run of inserted bytes an EA file may also hold


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pack_name(faction, version):
    return "bfme-mac-buildings-%s-%s" % (faction, version)


# ---------------------------------------------------------------------- cache records by key
def keys_of(op):
    """(keys the op reads, keys it writes)."""
    if op[0] == "model":
        new, like = op[1].lower(), op[2].lower()
        return [("asset", like), ("objects", like)], [("asset", new), ("objects", new)]
    if op[0] == "patch":
        return [("asset", op[1].lower())], [("asset", op[1].lower())]
    obj = [("object", op[3].lower(), op[4].upper())] if op[3] else []
    return [("asset", op[2].lower())] + obj, [("asset", op[1].lower())] + obj


def index(cache):
    """{key: [record bytes]} for every record, in cache order."""
    assets, _, objs = cache.sections()
    d, out = cache.data, {}
    for n, s, e in assets:
        out.setdefault(("asset", n.lower().decode("latin-1")), []).append(d[s:e])
    for f, o, s, e in objs:
        f, o = f.lower().decode("latin-1"), o.upper().decode("latin-1")
        out.setdefault(("objects", f), []).append(d[s:e])
        out.setdefault(("object", f, o), []).append(d[s:e])
    return out


def key_hash(idx, key):
    return sha(b"".join(idx.get(tuple(key), [])))


def coarse(key):
    """The key's model file for object records (a model op writes all of them), else the key."""
    return ("objects", key[1]) if key[0] == "object" else tuple(key)


def reads_and_writes(ops):
    """(keys read before any op wrote them, every key written), in first-use order."""
    reads, written = [], []
    for op in ops:
        r, w = keys_of(op)
        done = {coarse(k) for k in written} | set(written)
        reads += [k for k in r if k not in done and coarse(k) not in done and k not in reads]
        written += [k for k in w if k not in written]
    return reads, written


def model_reader(files):
    """files: {normalised member: bytes, or a () -> bytes}."""
    def read(model):
        f = files[norm(Install.model_path(model[:-4]))]
        return f() if callable(f) else f
    return read


def unfresh_models(files, caches):
    """Every .w3d in the archives the game would not draw: [(model, why)]. A model's record is
    the first cache's in search order (RotWK's, then BFME2's) that files it."""
    bad, read = [], model_reader(files)
    for member in sorted(files):
        if not member.endswith(".w3d"):
            continue
        model = member.split("\\")[-1]
        cache = next((c for c in caches if c.has_model(model)), None)
        if cache is None:
            bad.append((model, "not filed in asset.dat"))
            continue
        try:
            if cache.stale_entries(read(model), model):
                bad.append((model, "record does not match the file"))
        except CacheError as e:
            bad.append((model, str(e).splitlines()[0]))
    return bad


# ---------------------------------------------------------------------- install (player side)
def use_prefix(prefix):
    """Point sagekit at the games in this Wine prefix; return {game: folder}."""
    os.environ.pop("SAGEKIT_GAME_SNAPSHOT", None)
    ea = Path(prefix)/"drive_c"/"Program Files (x86)"/"Electronic Arts"
    dirs = {g: ea/d for g, d in GAMES.items()}
    for g, d in dirs.items():
        if not (d/"asset.dat").exists():
            raise SystemExit("no %s in %s" % (d/"asset.dat", prefix))
        paths.GAMEDIRS[g] = str(d)
    return dirs


def load(pack_dir):
    p = Path(pack_dir)
    raw = (p/"pack.json").read_bytes()
    m = json.loads(raw)
    if m.get("format") != FORMAT:
        raise SystemExit("%s: pack format %s; this installer reads %d (update the repo)" % (p, m.get("format"), FORMAT))
    m["dir"], m["id"] = p, sha(raw)
    return m


def mismatches(m, caches, g, dirs, seen):
    """Why this pack does not fit the player's game: [] when it does (seen: {EA member: sha256})."""
    out = []
    for a in m["archives"]:
        if (dirs["rotwk"]/a["name"]).exists():
            out.append("%s is already in the RotWK folder (a sagekit install or a copied pack: python3 -m "
                       "sagekit revert %s, or python3 -m sagekit unit <faction>/porter --revert, or remove the file)" % (a["name"], m["faction"]))
    for name, (want, archive) in sorted(m["sources"].items()):
        if name not in seen:
            try:
                seen[name] = sha(g.read(name))
            except FileNotFoundError:
                seen[name] = None
        if seen[name] != want:
            out.append("EA's %s is %s (the pack needs %s's, RotWK 2.02)" % (
                name, "missing" if seen[name] is None else "different", archive))
    for game, c in m["caches"].items():
        idx = index(caches[game])
        for k in c["requires"]:
            if tuple(k[:-1]) not in idx:
                out.append("%s asset.dat has no %s" % (GAMES[game], " ".join(k[:-1])))
            elif key_hash(idx, k[:-1]) != k[-1]:
                out.append("%s asset.dat has a different %s" % (GAMES[game], " ".join(k[:-1])))
    return out


def rebuild(m, g, appended):
    """{archive name: bytes}, each member rebuilt from the player's EA files and checked, the
    archive checked too unless another pack's lines were added to one of its members."""
    blob = (m["dir"]/m["data"]["name"]).read_bytes()
    if sha(blob) != m["data"]["sha256"]:
        raise SystemExit("%s is damaged (SHA-256); download the pack again" % (m["dir"]/m["data"]["name"]))
    view, out = memoryview(blob), {}
    for a in m["archives"]:
        members, shared = [], False
        for e in a["members"]:
            part = view[e["at"][0]:e["at"][0] + e["at"][1]]
            if e["kind"] == "append":
                lines = appended[norm(e["name"])]
                shared |= len(lines) > 1
                data = g.read(e["from"][0]) + b"".join(lines)
            else:
                data = delta.apply(part, [g.read(s) for s in e["from"]]) if e["kind"] == "delta" else bytes(part)
            if e["kind"] != "append" or len(lines) == 1:
                if len(data) != e["size"] or sha(data) != e["sha256"]:
                    raise SystemExit("%s: %s did not rebuild (EA's files or the pack differ)" % (m["faction"], e["name"]))
            members.append((e["name"], data))
        out[a["name"]] = bigtool.build_big(members, a["magic"].encode("latin-1"))
        del members
        if not shared and sha(out[a["name"]]) != a["sha256"]:
            raise SystemExit("%s: %s did not rebuild" % (m["faction"], a["name"]))
    return out


def install(pack_dirs, prefix, log=print):
    if game_running():
        raise SystemExit("close the game before installing")
    dirs = use_prefix(prefix)
    state = Path(prefix)/STATE
    packs = [load(d) for d in pack_dirs]
    have = installed(prefix)
    if have and have["packs"] == {m["faction"]: m["id"] for m in packs}:
        log("buildings already installed: %s" % ", ".join(have["packs"]))
        return
    if (state/"receipt.json").exists():                # another set: out first, never stacked
        revert(prefix, log)
    caches = {g: AssetCache(str(d/"asset.dat")) for g, d in dirs.items()}
    before = {g: c.data for g, c in caches.items()}
    g, chosen, seen, shipped = Install(), [], {}, set()
    used, written = {game: set() for game in GAMES}, {game: set() for game in GAMES}
    for m in sorted(packs, key=lambda m: m["faction"]):
        why = mismatches(m, caches, g, dirs, seen)
        reads = {game: {coarse(k[:-1]) for k in c["requires"]} for game, c in m["caches"].items()}
        writes = {game: {coarse(k[:-1]) for k in c["result"]} for game, c in m["caches"].items()}
        if any(writes[game] & used[game] or reads[game] & written[game] for game in writes):
            why.append("it changes asset.dat records another chosen pack uses")
        own = {norm(e["name"]) for a in m["archives"] for e in a["members"] if e["kind"] != "append"}
        if own & shipped:
            why.append("it ships files another chosen pack ships: %s" % ", ".join(sorted(own & shipped)[:3]))
        if why:
            log("skipping %s, which does not fit this game (the pack is for RotWK 2.02):\n  %s%s" % (
                m["faction"], "\n  ".join(why[:5]), "\n  and %d more" % (len(why) - 5) if len(why) > 5 else ""))
            continue
        for game in writes:
            used[game] |= reads[game] | writes[game]
            written[game] |= writes[game]
        shipped |= own
        chosen.append(m)
    if not chosen:
        raise SystemExit("no building pack installed")
    appended = {}                                      # {member: [our lines]} in faction order
    for m in chosen:
        blob = (m["dir"]/m["data"]["name"]).read_bytes()
        for a in m["archives"]:
            for e in a["members"]:
                if e["kind"] == "append":
                    appended.setdefault(norm(e["name"]), []).append(blob[e["at"][0]:e["at"][0] + e["at"][1]])
        del blob
    updates, expected, files = {}, {}, {}
    for m in chosen:
        built_ = rebuild(m, g, appended)
        for name, data in built_.items():
            dest = dirs["rotwk"]/name
            updates[dest], expected[dest] = data, None
            view = memoryview(data)
            files.update((norm(n), view[o:o + s]) for n, o, s in _entries(data))
        log("%s: rebuilt %s from your game's files" % (m["faction"], ", ".join(built_)))
    for m in chosen:
        read = model_reader(files)
        for game, c in m["caches"].items():
            cache = caches[game]
            exact = sha(before[game]) == c["pristine"]
            for model, entries in c["models"].items():
                if [[n, t.decode("latin-1"), o, s] for n, t, o, s in W3DFile(bytes(read(model))).cache_entries()] != entries:
                    raise SystemExit("%s: %s does not match pack.json" % (m["faction"], model))
            stage_ops(cache, [(tuple(op), lambda model: bytes(read(model))) for op in c["ops"]])
            idx = index(cache)
            wrong = [k[:-1] for k in c["result"] if key_hash(idx, k[:-1]) != k[-1]]
            if wrong:
                raise SystemExit("%s: %s asset.dat records came out different: %s" % (m["faction"], GAMES[game], wrong[:3]))
            if exact:
                log("%s: %s asset.dat is the one the pack was built against" % (m["faction"], GAMES[game]))
    bad = unfresh_models({n: (lambda v=v: bytes(v)) for n, v in files.items()}, [caches["rotwk"], caches["bfme2"]])
    if bad:
        raise SystemExit("models the game would not draw: %s" % bad[:5])
    files.clear()
    for game, d in dirs.items():
        if caches[game].data != before[game]:
            updates[d/"asset.dat"], expected[d/"asset.dat"] = caches[game].data, before[game]
    if game_running():
        raise SystemExit("the game started; nothing installed")
    apply(updates, state/"receipt.json", expected)
    atomic(state/"installed.json", (json.dumps(dict(
        packs={m["faction"]: m["id"] for m in chosen},
        versions={m["faction"]: m["version"] for m in chosen}), indent=1) + "\n").encode())
    log("installed buildings: %s (scripts/install.sh --no-buildings takes them out)" % ", ".join(m["faction"] for m in chosen))


def _entries(data):
    """[(name, offset, size)] of an archive in memory (the BIGF index: big-endian offset, size, name)."""
    import struct
    count, _ = struct.unpack_from(">II", data, 8)
    p, out = 16, []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, p)
        end = data.index(b"\0", p + 8)
        out.append((data[p + 8:end].decode("latin-1"), off, size))
        p = end + 1
    return out


def installed(prefix):
    f = Path(prefix)/STATE/"installed.json"
    return json.loads(f.read_text()) if f.exists() and (f.parent/"receipt.json").exists() else None


def revert(prefix, log=print):
    state = Path(prefix)/STATE
    if not (state/"receipt.json").exists():
        log("no buildings installed")
        return
    revert_receipt(state/"receipt.json")
    shutil.rmtree(state)
    log("buildings removed; asset.dat restored")


def status(prefix):
    have = installed(prefix)
    if not have:
        return "buildings: not installed"
    return "buildings: %s" % ", ".join("%s (%s)" % (f, have["versions"][f]) for f in have["packs"])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m sagekit.pack", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("faction")
    p.add_argument("--version", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--jobs", type=int)
    p = sub.add_parser("install")
    p.add_argument("packs", nargs="+")
    st = sub.add_parser("status")
    st.add_argument("--list", action="store_true", help="only the installed factions, comma-separated")
    for p in [p, sub.add_parser("revert"), st]:
        p.add_argument("--prefix", default=os.path.dirname(os.path.dirname(os.path.dirname(paths.ELECTRONIC_ARTS))))
    a = ap.parse_args(argv)
    if a.cmd == "build":
        from .packbuild import build
        build(a.faction, a.version, a.out, jobs=a.jobs)
    elif a.cmd == "install":
        install(a.packs, a.prefix)
    elif a.cmd == "revert":
        revert(a.prefix)
    elif a.list:
        print(",".join((installed(a.prefix) or {}).get("packs", {})))
    else:
        print(status(a.prefix))


if __name__ == "__main__":
    sys.exit(main())
