#!/usr/bin/env python3
"""monitor_stalls - the stall section of a session report: where the game's main thread was while a
frame took longer than the stall sampler's threshold (150 ms).

    python3 tools/monitor_stalls.py logs/sessions/<id>/game.txt [--top 5]

Reads the stall sampler's lines in game.txt (gamepatch/src/p_stall.c; d3d9bench --monitor writes the
same): X (the exe, its code range), M (a module a sample's EIP was in), e (one sample: time, the last
frame's time, logic frame, EIP, us the thread was held, logic phase, return addresses into the exe).
Each stall's samples are grouped by the last frame's time and reported as histograms:
  exe      the innermost function of the exe on the stack (EIP's function, or the caller of the system
           library EIP is in): where the frame's time goes, library time charged to its caller
  incl     every function on the recovered call chain (tools/callstacks.py Chainer: return addresses
           that do not chain to the next frame are dropped)
  leaf     where EIP was: an exe function or [module]
  phase    the GameLogic::update phase (1-6) the samples fell in, when logicstats is on (0 = outside it)
Symbols: RotWK's exe uses build/rotwk-re/ (disk.exe, funcs.txt, names.txt, names-auto.txt; made by
build/rotwk-re/funcs.py and namematch.py); any other exe (the D3D9 bench) build/<exe name> and its COFF
symbols (i686-w64-mingw32-nm). Without them, addresses only.
"""
import bisect
import collections
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from callstacks import Chainer, load_names, load_text  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE_DIR = os.path.join(ROOT, "build", "rotwk-re")
NM = os.environ.get("NM", "/opt/homebrew/bin/i686-w64-mingw32-nm")


def load(path):
    """(exe dict or None, [(base, size, name)], [event], [frame us]) from game.txt"""
    exe, mods, ev, fus = None, [], [], []
    for line in open(path, errors="replace"):
        p = line.split()
        if not p:
            continue
        try:
            if p[0] == "f":
                fus.append(int(p[1]))
            elif p[0] == "e" and len(p) >= 7:
                ev.append({"us": int(p[1]), "since": int(p[2]), "logic": int(p[3]), "eip": int(p[4], 16),
                           "held": int(p[5]), "phase": int(p[6]), "rets": [int(x, 16) for x in p[7:]]})
            elif p[0] == "X" and len(p) >= 5:
                exe = {"base": int(p[1], 16), "lo": int(p[2], 16), "hi": int(p[3], 16), "name": " ".join(p[4:])}
            elif p[0] == "M" and len(p) >= 4:
                mods.append((int(p[1], 16), int(p[2], 16), " ".join(p[3:])))
        except ValueError:
            continue
    return exe, mods, ev, sorted(fus)


def nm_symbols(path):
    """{address: name} of the text symbols in a mingw-built PE (COFF symbol table)"""
    try:
        out = subprocess.run([NM, "--defined-only", path], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    syms = {}
    for line in out.splitlines():
        f = line.split()
        if len(f) == 3 and f[1] in "tT" and not f[2].startswith("."):
            syms[int(f[0], 16)] = f[2][1:] if f[2].startswith("_") else f[2]
    return syms


class Symbols:
    def __init__(self, exe):
        self.chainer, self.names, self.source = None, {}, "none (addresses)"
        name = (exe or {}).get("name", "").lower()
        if name in ("lotrbfme2ep1.exe", "game.dat"):
            disk, funcs = os.path.join(RE_DIR, "disk.exe"), os.path.join(RE_DIR, "funcs.txt")
            if os.path.exists(disk) and os.path.exists(funcs):
                self.chainer = Chainer.from_files(disk, funcs)
                self.names = load_names([p for p in (os.path.join(RE_DIR, "names.txt"), os.path.join(RE_DIR, "names-auto.txt"))
                                         if os.path.exists(p)])
                self.source = "build/rotwk-re (funcs.txt, names)"
        elif name:
            path = os.path.join(ROOT, "build", os.path.basename(name))
            if os.path.exists(path):
                self.names = nm_symbols(path)
                if self.names:
                    lo, code = load_text(path)
                    st = sorted(self.names)
                    self.chainer = Chainer(lo, code, st)   # direct calls only: no taken-address data
                    self.source = "build/%s (COFF symbols)" % os.path.basename(name)

    def label(self, f):
        if isinstance(f, str):
            return f
        n = self.names.get(f)
        return "%06x %s" % (f, n) if n else "%06x" % f


def modname(mods, x):
    for b, s, n in mods:
        if b <= x < b + s:
            return n
    return "?"


def stack(sym, exe, mods, e):
    """(chain outermost first ending in the leaf, innermost exe function or None)"""
    in_exe = exe and exe["lo"] <= e["eip"] < exe["hi"]
    if sym.chainer:
        chain, leaf, _ = sym.chainer.chain(e["eip"], e["rets"])
        if leaf == Chainer.EXT:
            return chain + ["[%s]" % modname(mods, e["eip"])], (chain[-1] if chain else None)
        return chain + [leaf], leaf
    # no function starts: the leaf is EIP itself, callers the raw return sites (stale ones included)
    callers = ["site %06x" % r for r in reversed(e["rets"][:12])]
    leaf = ("%06x" % e["eip"]) if in_exe else "[%s]" % modname(mods, e["eip"])
    return callers + [leaf], leaf if in_exe else (callers[-1] if callers else None)


def analyse(path, min_samples=5):
    exe, mods, ev, fus = load(path)
    if not ev:
        return None
    sym = Symbols(exe)
    groups = collections.OrderedDict()
    for e in ev:
        groups.setdefault(e["since"], []).append(e)
    stalls = []
    for since, es in groups.items():
        if len(es) < min_samples:
            continue
        i = bisect.bisect_right(fus, since)
        end = fus[i] if i < len(fus) else es[-1]["us"]
        s = {"since": since, "ms": (end - since) / 1000.0, "logic": es[0]["logic"], "n": len(es),
             "held": sum(e["held"] for e in es) / len(es), "exe": collections.Counter(), "incl": collections.Counter(),
             "leaf": collections.Counter(), "phase": collections.Counter(e["phase"] for e in es)}
        for e in es:
            st, inner = stack(sym, exe, mods, e)
            s["leaf"][st[-1]] += 1
            s["exe"][inner if inner is not None else "(no exe frame)"] += 1
            for f in set(st):
                s["incl"][f] += 1
        stalls.append(s)
    return {"exe": exe, "sym": sym, "stalls": stalls, "samples": len(ev)}


def _top(c, n, total, sym):
    return ", ".join("%.0f %% %s" % (100.0 * k / total, sym.label(f)) for f, k in c.most_common(n))


def lines(r, clock=None, off=0.0, top=5, most=12):
    """summary lines for the report (clock: unix seconds -> text; off: unix - us / 1e6)"""
    if not r or not r["stalls"]:
        return []
    sym, st = r["sym"], r["stalls"]
    L = ["Stalls (frames the stall sampler caught, game patch: main thread EIP + stack every ~2 ms past 150 ms; "
         "symbols: %s): %d stalls, %d samples" % (sym.source, len(st), sum(s["n"] for s in st))]
    allc = {k: collections.Counter() for k in ("exe", "incl")}
    for s in st:
        for k in allc:
            allc[k].update(s[k])
    n = sum(s["n"] for s in st)
    L.append("  all stalls, innermost exe function: " + _top(allc["exe"], top + 3, n, sym))
    L.append("  all stalls, on the call chain: " + _top(allc["incl"], top + 5, n, sym))
    ins = [s for s in st if s["logic"] > 0]          # in a match: menu and load-screen frames left out
    if ins and len(ins) < len(st):
        mc = {k: collections.Counter() for k in ("exe", "incl")}
        for s in ins:
            for k in mc:
                mc[k].update(s[k])
        m = sum(s["n"] for s in ins)
        hist = collections.Counter(min(int(s["ms"]) // 100 * 100, 1000) for s in ins)
        L.append("  in a match (logic frame > 0): %d stalls, %d samples; frame ms: %s" % (
            len(ins), m, ", ".join("%d-%s %d" % (b, b + 99 if b < 1000 else "", k) for b, k in sorted(hist.items()))))
        L.append("  in a match, innermost exe function: " + _top(mc["exe"], top + 3, m, sym))
        L.append("  in a match, on the call chain: " + _top(mc["incl"], top + 5, m, sym))
    for s in sorted(st, key=lambda s: -s["ms"])[:most]:
        when = clock(s["since"] / 1e6 + off) if clock else "%.1f s" % (s["since"] / 1e6)
        ph = [(p, k) for p, k in s["phase"].most_common() if p >= 0]
        phs = ("; logic phase " + ", ".join("%s %.0f %%" % (p or "outside", 100.0 * k / s["n"]) for p, k in ph[:3])) if ph else ""
        L.append("  %s frame %.0f ms (logic %d): %d samples, held %.0f us each%s" % (when, s["ms"], s["logic"], s["n"], s["held"], phs))
        L.append("      exe: " + _top(s["exe"], top, s["n"], sym))
        L.append("      chain: " + _top(s["incl"], top + 2, s["n"], sym))
        L.append("      leaf: " + _top(s["leaf"], 3, s["n"], sym))
    return L


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a:
        print(__doc__)
        sys.exit(2)
    t = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 5
    res = analyse(a[0])
    print("\n".join(lines(res, top=t)) or "no stall samples in %s" % a[0])
