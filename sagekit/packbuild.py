"""Building packs, the release side of sagekit/pack.py: each archive member as a delta against the EA
files the build made it from (sagekit/delta.py), checked to insert no long run of EA's bytes."""
import json
import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from . import delta, paths
from .formats.assetcache import AssetCache
from .formats.big import bigtool, norm
from .formats.textures import compiled_path
from .formats.w3d import W3DFile
from .game import Install
from .install import archive_name, built, stage_ops
from .pack import (DATA, DONE, FORMAT, GAMES, MAX_SHARED, index, key_hash, model_reader, pack_name,
                   reads_and_writes, sha, unfresh_models)


# ---------------------------------------------------------------------- build: what each member came from
def family(name):
    ext = name.rsplit(".", 1)[-1].lower()
    return "texture" if ext in ("dds", "tga") else ext


def ea_name(path, g):
    """The EA member a build's extracted file is a byte copy of, or None."""
    stem, ext = os.path.splitext(os.path.basename(path).lower())
    names = [Install.model_path(stem)] if ext == ".w3d" else \
        [compiled_path(stem, e) for e in (".dds", ".tga")] if ext in (".dds", ".tga") else []
    for name in names:
        a = g.owner(name)
        if a is not None and a.index()[name].size == os.path.getsize(path) \
                and a.read(name) == Path(path).read_bytes():
            return name
    return None


def extracted(faction):
    """{member: {folders of the EA files its build extracted}}: a building's out/ from its src/ and
    work/ref/, the recoloured sheets from _sheets/src, the house-colour models from _house/src."""
    out = {}

    def add(tree, dirs):
        for root, _, names in os.walk(tree):
            for n in names:
                rel = norm(os.path.relpath(os.path.join(root, n), tree))
                out.setdefault(rel, set()).update(d for d in dirs if os.path.isdir(d))
    base = os.path.join(paths.BUILD, faction)
    add(os.path.join(base, "_sheets", "out"), [os.path.join(base, "_sheets", "src")])
    for _, ws in built(faction):
        add(ws.path("out"), [ws.path("src"), ws.path("work", "ref")])
    house_out = os.path.join(base, "_house", "out")
    add(house_out, [os.path.join(base, "_house", "src")])
    return out


def made_from(member, likes, dirs, g, resolved):
    """EA members to rebuild `member` from, best first: EA's file of the same path, the EA sheet or
    model an op copies (likes: {our stem: [EA stems]}), then its build's extracts of its kind."""
    stem, fam = member.split("\\")[-1].rsplit(".", 1)[0], family(member)
    out = [member] if g.owner(member) is not None else []
    for like in likes.get(stem, []):
        names = [Install.model_path(like)] if fam == "w3d" else \
            [compiled_path(like, ".dds"), compiled_path(like, ".tga")] if fam == "texture" else []
        out += [n for n in names if g.owner(n) is not None]
    if fam in ("w3d", "texture"):
        for d in sorted(dirs):
            for f in sorted(os.listdir(d)):
                p = os.path.join(d, f)
                if family(f) == fam and os.path.isfile(p):
                    if p not in resolved:
                        resolved[p] = ea_name(p, g)
                    if resolved[p]:
                        out.append(resolved[p])
    return list(dict.fromkeys(out))


def op_likes(ops):
    """{our texture or model stem: [EA stems it copies]} from cache ops."""
    out = {}
    for op in ops:
        if op[0] in ("model", "texture"):
            out.setdefault(op[1].lower().rsplit(".", 1)[0], []).append(op[2].lower().rsplit(".", 1)[0])
    return out


def _slice(ref):
    path, offset, size = ref
    with open(path, "rb") as f:
        f.seek(offset)
        return f.read(size)


def _encode(job):
    """(delta or our bytes, sources used, inserted bytes, longest inserted run an EA source holds)."""
    target_ref, source_refs = job
    target, sources = _slice(target_ref), [_slice(r) for r in source_refs]
    d, used = delta.encode(target, sources)
    if delta.apply(d, [sources[u] for u in used]) != target:
        raise AssertionError("delta does not rebuild %s" % (target_ref,))
    runs = delta.inserted(d)
    shared = delta.shared_runs(runs, sources)[0]
    return (d if used else target), used, sum(map(len, runs)), shared


def ref(g, name):
    a = g.owner(name)
    e = a.index()[norm(name)]
    return a.path, e.offset, e.size


# ---------------------------------------------------------------------- build (release side)
def parts(faction):
    """[(staged archive, {game: [op]}, {INI member: our lines}, {member: {dirs}})]: the faction's
    buildings, then each of its unit recipes that ships an archive (sagekit/units/install.py release())."""
    stage = Path(paths.BUILD)/faction/"_install"
    archive, ops_file = stage/archive_name(faction), stage/"cache-ops.json"
    if not (archive.exists() and ops_file.exists()):
        raise SystemExit("%s is not staged: python3 -m sagekit install %s --check" % (faction, faction))
    staged = json.loads(ops_file.read_text())
    if sha(archive.read_bytes()) != staged["archive_sha256"]:
        raise SystemExit("%s: the staged archive and cache-ops.json differ; stage again" % faction)
    out = [(archive, {g: [tuple(op) for op in o] for g, o in staged["caches"].items()}, {}, extracted(faction))]
    from .units import ids, load
    from .units.install import release
    for uid in ids(faction):                    # its units (the builder), staged: sagekit unit <id> --stage
        u = load(uid)
        if not u.archive or not u.privates():
            continue                            # a stub ships nothing
        archive, ops, appended, dirs = release(u)
        names = [norm(e.name) for e in bigtool.read_index(str(archive))[0]]
        out.append((Path(archive), ops, appended, {n: set(map(str, dirs)) for n in names}))
    return out


def build(faction, version, out, log=print, jobs=None):
    buildings = sorted(b.id for b, _ in built(faction))
    extra = set(buildings) - DONE.get(faction, set(buildings))
    if extra:
        raise SystemExit("%s: not in the release yet: %s (sagekit/pack.py DONE)" % (faction, ", ".join(sorted(extra))))
    g, plan = Install(), parts(faction)
    ops = {game: [op for p in plan for op in p[1].get(game, [])] for game in GAMES}
    likes, resolved = op_likes([op for o in ops.values() for op in o]), {}
    dest = Path(out)/pack_name(faction, version)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    archives, sources, files, total = [], {}, {}, dict(inserted=0, bytes=0, longest_ea_run=0, member=None)
    with open(dest/DATA, "wb") as data, ProcessPoolExecutor(jobs or min(8, os.cpu_count() or 1)) as pool:
        for archive, _, appended, dirs in plan:
            entries, _ = bigtool.read_index(str(archive))
            with open(archive, "rb") as f:
                magic = f.read(4)
            members, work = [], {}                      # {member index: (target, [source])}
            for e in entries:
                n = norm(e.name)
                files[n] = lambda e=e, a=str(archive): bigtool.read_member(a, e)
                if n in appended:
                    ea = g.read(n)
                    files[n] = ea + appended[n]
                    members.append(dict(name=e.name, sha256=sha(files[n]), size=len(files[n]), kind="append",
                                        from_=[n], add=appended[n]))
                    continue
                cands = made_from(n, likes, dirs.get(n, ()), g, resolved)
                members.append(dict(name=e.name, from_=cands))
                work[len(members) - 1] = ((str(archive), e.offset, e.size), [ref(g, c) for c in cands])
            order = sorted(work, key=lambda i: -work[i][0][2])      # the largest first
            results = dict(zip(order, pool.map(_encode, [work[i] for i in order], chunksize=1)))
            for i, m in enumerate(members):
                if m.get("kind") == "append":
                    blob = m.pop("add")
                else:
                    blob, used, ins, shared = results[i]
                    m.update(sha256=sha(_slice(work[i][0])), size=work[i][0][2])
                    checked, m["from_"] = m["from_"], [m["from_"][u] for u in used]
                    m["kind"] = "delta" if used else "ours"
                    if not used:
                        m["why"] = "checked against %s" % ", ".join(checked) if checked else "no EA file it was made from"
                    total["inserted"] += ins
                    if shared > total["longest_ea_run"]:
                        total.update(longest_ea_run=shared, member=m["name"])
                total["bytes"] += m["size"]
                m["at"] = [data.tell(), len(blob)]
                data.write(blob)
                m["from"] = m.pop("from_")
                for s in m["from"]:
                    sources.setdefault(s, None)
            rebuilt = bigtool.build_big([(m["name"], files[norm(m["name"])] if not callable(files[norm(m["name"])])
                                          else files[norm(m["name"])]()) for m in members], magic)
            same = rebuilt == Path(archive).read_bytes()
            log("%s: %d members; %s" % (archive.name, len(members), "as staged" if same else
                "rebuilt with EA's text plus its own lines in %s (the staged one differs)" % ", ".join(appended)))
            archives.append(dict(name=archive.name, sha256=sha(rebuilt), size=len(rebuilt),
                                 magic=magic.decode("latin-1"), members=members))
            del rebuilt
    if total["longest_ea_run"] > MAX_SHARED:
        shutil.rmtree(dest)
        raise SystemExit("%s: %s holds a run of %d bytes from an EA file (limit %d)" % (
            faction, total["member"], total["longest_ea_run"], MAX_SHARED))
    for s in sources:
        sources[s] = [sha(g.read(s)), os.path.basename(g.owner(s).path)]
    caches, results = {}, {}
    for game in GAMES:
        orig = Path(paths.GAMEDIRS[game])/"asset.dat.orig"
        if not orig.exists():
            raise SystemExit("no pristine %s (asset.dat.orig)" % orig)
        cache = AssetCache(str(orig))
        results[game] = cache
        if not ops[game]:
            continue
        idx = index(cache)
        reads, written = reads_and_writes(ops[game])
        missing = [k for k in reads if k not in idx]
        if missing:
            raise SystemExit("%s: EA records missing from %s: %s" % (faction, orig, missing[:5]))
        read = model_reader(files)
        stage_ops(cache, [(op, read) for op in ops[game]])
        after = index(cache)
        caches[game] = dict(
            ops=ops[game],
            models={op[1]: [[n, t.decode("latin-1"), o, s] for n, t, o, s in W3DFile(read(op[1])).cache_entries()]
                    for op in ops[game] if op[0] in ("model", "patch")},
            requires=[list(k) + [key_hash(idx, k)] for k in reads],
            result=[list(k) + [key_hash(after, k)] for k in written],
            pristine=sha(orig.read_bytes()))
    bad = unfresh_models(files, [results["rotwk"], results["bfme2"]])
    if bad:
        raise SystemExit("%s: models the game would not draw: %s" % (faction, bad[:5]))
    installed = [a["name"] for a in archives if (Path(paths.GAMEDIRS["rotwk"])/a["name"]).exists()
                 and sha((Path(paths.GAMEDIRS["rotwk"])/a["name"]).read_bytes()) == a["sha256"]]
    blob = (dest/DATA).read_bytes()
    manifest = dict(format=FORMAT, faction=faction, version=version, buildings=buildings,
                    data=dict(name=DATA, sha256=sha(blob), size=len(blob)), sources=sources,
                    archives=archives, literal=total, caches=caches)
    (dest/"pack.json").write_text(json.dumps(manifest, indent=1) + "\n")
    kinds = {}
    for a in archives:
        for m in a["members"]:
            kinds[m["kind"]] = kinds.get(m["kind"], 0) + 1
    log("%s: %d buildings, %s, %d EA files; %s cache ops; inserted %.1f%% of %d bytes, the longest run of "
        "them in an EA file %d bytes (0: none of %d+; limit %d); installed here: %s" % (
            faction, len(buildings), ", ".join("%d %s" % (n, k) for k, n in sorted(kinds.items())), len(sources),
            "+".join("%d %s" % (len(c["ops"]), g) for g, c in caches.items()),
            100.0 * total["inserted"] / max(1, total["bytes"]), total["bytes"],
            total["longest_ea_run"], 2 * delta.WINDOW - 1, MAX_SHARED,
            ", ".join(installed) or "none (not play-tested)"))
    return dest
