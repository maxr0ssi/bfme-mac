#!/usr/bin/env python3
"""monitor_report - the report of one scripts/monitor.sh session folder.

    python3 tools/monitor_report.py logs/sessions/<id> [--spike-ms 50]

Reads the folder (meta.json and samples.jsonl from tools/monitor_rec.py, game.txt from the game
patch's monitor when it is installed), the game log's per-frame lines (WINEDEBUG=+timestamp,
+frametime: wined3d's time between two presents) and the session's part of logs/gamepatch.log, and
writes report.html (graphs, tools/monitor_chart.py) and summary.txt, and prints the summary; the stall
sampler's per-stall function histograms come from tools/monitor_stalls.py.
Every number comes from those files; the "cause" of a slow frame is a fixed rule (see CAUSE_RULE).
"""
import bisect
import json
import os
import re
import statistics
import sys
import time

import monitor_chart
try:
    import monitor_stalls
except Exception:   # noqa: BLE001 - the report works without the stall section
    monitor_stalls = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_RE = re.compile(rb"^\s*(\d+)\.(\d{3}):[0-9a-f]+:trace:frametime:\S+ Frame duration (\d+)")
GPLOG_RE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3}) \[\d+\] (.*)")
EVENT_RE = re.compile(r"display switch|static LOD|highmem|monitor:|failed|differ|off for the session|exit:")
CAUSE_RULE = ("loads: D3DX texture/effect time in the frame >= half of its time over 33 ms; else game thread: "
              "main thread >= 90 % of a core in the 0.25 s sample; else render thread: wined3d_cs >= 90 %; "
              "else GPU: device utilisation >= 90 %; else memory: resident +50 MB within 1 s; else waiting")


def pct(s, p):
    return s[min(len(s) - 1, max(0, int(round(p / 100.0 * (len(s) - 1)))))] if s else 0.0


def clock(t):
    return time.strftime("%H:%M:%S", time.localtime(t))


def load_game(path):
    """game.txt -> dict of lists, times in unix seconds"""
    g = {"f": [], "s": [], "m": [], "t": [], "dropped": 0}
    if not os.path.exists(path):
        return None
    for line in open(path, errors="replace"):
        p = line.split()
        if not p or p[0] not in ("t", "f", "s", "m", "d"):
            continue
        try:
            v = [int(x) for x in p[1:]]
        except ValueError:
            continue
        if p[0] == "d":
            g["dropped"] += v[0]
        else:
            g[p[0]].append(v)
    if not g["t"]:
        return None
    off = statistics.median(t[1] / 1000.0 - t[0] / 1e6 for t in g["t"])
    g["tick_offset"] = statistics.median(t[1] / 1000.0 - t[2] / 1000.0 for t in g["t"])
    out = {"dropped": g["dropped"], "tick_offset": g["tick_offset"], "off": off}
    fr, prev = [], None
    for f in g["f"]:   # us logic load_n load_us create_n create_us fx_n fx_us
        t = f[0] / 1e6 + off
        if prev is not None and f[0] > prev:
            fr.append({"t": t, "ms": (f[0] - prev) / 1000.0, "logic": f[1], "loads": f[2] + f[4] + f[6],
                       "tex": f[2], "load_ms": (f[3] + f[5] + f[7]) / 1000.0, "create": f[4], "fx": f[6]})
        prev = f[0]
    out["frames"] = fr
    out["objects"] = [(s[0] / 1e6 + off, s[1], s[2], s[3]) for s in g["s"]]
    # (t, committed, reserved, free, largest free, regions, total) in MB
    out["vm"] = [(m[0] / 1e6 + off, m[1], m[2], m[3], m[4], m[5], m[7] if len(m) > 7 else 0) for m in g["m"]]
    return out


def load_frames(log, tick_offset):
    fr = []
    if not log or not os.path.exists(log) or tick_offset is None:
        return fr
    with open(log, "rb") as f:
        for line in f:
            m = FRAME_RE.match(line)
            if m:
                fr.append((int(m.group(1)) + int(m.group(2)) / 1000.0 + tick_offset, int(m.group(3)) / 1000.0))
    return fr


def load_samples(path):
    """-> list of dicts: t, dt, rss, fp, main, cs, proc (% of one core), top (name, %), gpu"""
    out, names, prev_t, main_h = [], {}, None, None
    rows = [json.loads(l) for l in open(path)] if os.path.exists(path) else []
    totals = {}
    for r in rows:
        for h, name, *_ in r.get("thr0", []):
            names[h] = name
        for h, name, pri, ms in r["thr"]:
            names[h] = name or names.get(h, "")
            totals[h] = totals.get(h, 0) + ms
    named = [h for h, n in names.items() if n == "bfme_main"]
    unnamed = sorted((v, h) for h, v in totals.items() if not names.get(h))
    main_h = named[0] if named else (unnamed[-1][1] if unnamed else None)
    cs_h = [h for h, n in names.items() if n == "wined3d_cs"]
    for r in rows:
        if prev_t is None:
            prev_t = r["t"]
            continue
        dt = max(1e-3, r["t"] - prev_t)
        prev_t = r["t"]
        c = {h: ms for h, _n, _p, ms in r["thr"]}
        per = lambda ms: min(100.0, 100.0 * ms / (dt * 1000.0))   # one thread: at most one core
        others = sorted(((ms, h) for h, ms in c.items() if h != main_h and h not in cs_h), reverse=True)
        out.append({"t": r["t"], "dt": dt, "rss": r["rss"], "fp": r["fp"], "main": per(c.get(main_h, 0)),
                    "cs": per(sum(c.get(h, 0) for h in cs_h)), "proc": 100.0 * sum(c.values()) / (dt * 1000.0),
                    "top": (names.get(others[0][1]) or "#" + others[0][1][-4:], per(others[0][0])) if others else ("", 0),
                    "gpu": r.get("gpu")})
    ident = "named bfme_main (game patch)" if named else "busiest unnamed thread (no game patch monitor)"
    return out, ident, totals and len(totals)


def skirmish(start, end):
    """map and players from the game's Skirmish.ini, if the game wrote it during the session"""
    d = os.path.join(ROOT, "prefixes", "w10", "drive_c", "users")
    for user in (os.listdir(d) if os.path.isdir(d) else []):
        p = os.path.join(d, user, "AppData", "Roaming", "My Rise of the Witch-king Files", "Skirmish.ini")
        if os.path.exists(p) and start - 5 <= os.path.getmtime(p) <= end + 60:
            txt = open(p, errors="replace").read()
            m = re.search(r"GameInfo = M=\d*([^;]+);.*?;S=([^;]*);", txt)
            if m:
                slots = [s for s in m.group(2).split(":") if s]
                return {"map": m.group(1).split("/")[-1], "humans": sum(s[0] == "H" for s in slots),
                        "ai": sum(s[0] == "C" for s in slots)}
    return None


def gp_events(meta, t0, t1):
    path, off = meta.get("gamepatch_log"), meta.get("gamepatch_log_offset", 0)
    ev, diag = [], {}
    if not path or not os.path.exists(path):
        return ev, diag
    with open(path, "rb") as f:
        f.seek(off)
        for raw in f:
            line = raw.decode("utf-8", "replace").rstrip()
            m = GPLOG_RE.match(line)
            if not m:
                continue
            t = time.mktime(time.strptime(m.group(1)[:19], "%Y-%m-%d %H:%M:%S")) + int(m.group(1)[20:]) / 1000.0
            msg = m.group(2)
            for k in ("passtimers", "renderstats", "particlestats", "shadowstats", "monitor", "stalls", "logicstats", "highmem"):
                if msg.startswith(k + ": off"):
                    diag[k] = "off"
                elif msg.startswith(k + ":") and k not in diag:
                    diag[k] = "on"
            if t0 - 5 <= t <= t1 + 5 and EVENT_RE.search(msg) and not msg.startswith(("renderstats: last", "renderstats: ms")):
                ev.append((t, msg[:200]))
    return ev, diag


_KEYS = {}


def _keys(seq, key):
    k = _KEYS.get(id(seq))
    if k is None or len(k) != len(seq):
        k = _KEYS[id(seq)] = [key(x) for x in seq]
    return k


def at(seq, t, key=lambda x: x["t"]):
    """the first item at or after t (its interval covers t), else the last"""
    i = bisect.bisect_left(_keys(seq, key), t)
    return seq[min(i, len(seq) - 1)] if seq else None


def before(seq, t, key):
    i = bisect.bisect_right(_keys(seq, key), t) - 1
    return seq[i] if i >= 0 else None


def analyse(d, spike_ms=50.0):
    meta = json.load(open(os.path.join(d, "meta.json")))
    game = load_game(os.path.join(d, "game.txt"))
    tick_off = (game or {}).get("tick_offset") or meta.get("tick_offset")
    frames = load_frames(meta.get("log"), tick_off)
    src = "wined3d presents (WINEDEBUG=+frametime)"
    if not frames and game and game["frames"]:
        frames, src = [(f["t"], f["ms"]) for f in game["frames"]], "game patch frame hook (game thread)"
    samples, ident, nthreads = load_samples(os.path.join(d, "samples.jsonl"))
    t0 = frames[0][0] - frames[0][1] / 1000.0 if frames else meta["start"]
    t1 = max(frames[-1][0] if frames else meta["end"], meta.get("end", 0))
    events, diag = gp_events(meta, t0, t1)
    gf = game["frames"] if game else []
    gf_t = [f["t"] for f in gf]
    gsm = [x for x in samples if x.get("gpu")]
    objs = game["objects"] if game else []
    vm = game["vm"] if game else []
    # logic rate (logic frames per second while the match runs)
    rates = [(b[3] - a[3]) / (b[0] - a[0]) for a, b in zip(objs, objs[1:]) if b[3] > a[3] and b[0] > a[0]]
    logic_rate = round(statistics.median(rates)) if rates else None

    def ctx(t, ms):
        s = at(samples, t)
        c = {"t": t, "ms": ms}
        if s:
            c.update(main=s["main"], cs=s["cs"], top=s["top"])
            a = before(samples, t - ms / 1000.0 - 0.25, lambda x: x["t"]) or samples[0]
            b = at(samples, t + 1.0) or samples[-1]
            c["rss_jump"] = b["rss"] - a["rss"]
        g = before(gsm, t + 0.5, lambda x: x["t"])
        if g and abs(g["t"] - t) <= 1.5:
            c["gpu"] = g["gpu"][0]
        if gf:   # the game-thread frame intervals that overlap this present's interval
            lo, hi = t - ms / 1000.0 - 0.05, t + 0.02
            i0 = bisect.bisect_right(gf_t, lo)
            ov = [f for f in gf[i0:bisect.bisect_left(gf_t, hi + 2.0)] if f["t"] - f["ms"] / 1000.0 < hi]
            c["loads"] = sum(f["loads"] for f in ov)
            c["tex"] = sum(f["tex"] for f in ov)
            c["load_ms"] = sum(f["load_ms"] for f in ov)
            c["game_ms"] = max((f["ms"] for f in ov), default=0)
        o = before(objs, t, lambda x: x[0])
        if o:
            c["objects"], c["logic"] = o[1], o[3]
            if logic_rate and o[3]:
                c["minute"] = o[3] / logic_rate / 60.0
        v = before(vm, t, lambda x: x[0])
        v0 = before(vm, t - ms / 1000.0 - 2.5, lambda x: x[0])
        if v and v0:
            c["vm_jump"] = (v[1] + v[2]) - (v0[1] + v0[2])
        c["events"] = [m for (te, m) in events if t - 2 <= te <= t + 1][:3]
        over = max(0.0, ms - 33.3)
        if c.get("load_ms", 0) >= 0.5 * over and c.get("load_ms", 0) > 0:
            c["cause"] = "loads"
        elif c.get("main", 0) >= 90:
            c["cause"] = "game thread"
        elif c.get("cs", 0) >= 90:
            c["cause"] = "render thread"
        elif c.get("gpu", 0) >= 90:
            c["cause"] = "GPU"
        elif c.get("rss_jump", 0) >= 50:
            c["cause"] = "memory"
        else:
            c["cause"] = "waiting"
        return c

    spikes = [ctx(t, ms) for t, ms in frames if ms > spike_ms]
    # 10 s windows
    wins = []
    if frames:
        w, start = [], frames[0][0]
        for t, ms in frames + [(1e18, 0)]:
            if t - start >= 10 and w:
                st_ = _keys(samples, lambda x: x["t"])
                ss = samples[bisect.bisect_left(st_, start):bisect.bisect_right(st_, start + 10)]
                wins.append({"t": start, "fps": len(w) / sum(w) * 1000.0, "mean": sum(w) / len(w),
                             "p95": pct(sorted(w), 95), "main": statistics.mean(s["main"] for s in ss) if ss else 0,
                             "cs": statistics.mean(s["cs"] for s in ss) if ss else 0, "n": len(w)})
                w, start = [], t
            w.append(ms)
    return {"meta": meta, "game": game, "frames": frames, "src": src, "samples": samples, "ident": ident,
            "spikes": spikes, "wins": wins, "events": events, "diag": diag, "logic_rate": logic_rate,
            "skirmish": skirmish(meta["start"], meta.get("end", t1)), "t0": t0, "t1": t1, "spike_ms": spike_ms,
            "nthreads": nthreads}


def moment(c):
    bits = ["%s" % clock(c["t"]) + (" (match minute %d)" % c["minute"] if c.get("minute") is not None else ""),
            "%.0f ms" % c["ms"]]
    if "main" in c:
        bits.append("main thread %.0f %%, render thread %.0f %%" % (c["main"], c["cs"]))
    if "rss_jump" in c:
        bits.append("%+.0f MB resident" % c["rss_jump"])
    if "vm_jump" in c:
        bits.append("%+d MB address space" % c["vm_jump"])
    if "loads" in c:
        bits.append("%d texture/effect loads (%.0f ms)" % (c["loads"], c["load_ms"]))
    if "gpu" in c:
        bits.append("GPU %d %%" % c["gpu"])
    if "objects" in c:
        bits.append("%d objects" % c["objects"])
    s = ", ".join(bits) + " -> " + c["cause"]
    if c["events"]:
        s += "; log: " + " | ".join(e[:90] for e in c["events"])
    return s


def summary(r):
    m, fr, sm = r["meta"], [ms for _, ms in r["frames"]], r["samples"]
    L = ["Session %s, %s - %s (%.1f min), pid %s" % (os.path.basename(r["dir"]), clock(r["t0"]), clock(r["t1"]),
         (r["t1"] - r["t0"]) / 60.0, m.get("pid"))]
    sk = r["skirmish"]
    if sk:
        L.append("Skirmish: %s, %d human + %d AI players (Skirmish.ini)" % (sk["map"], sk["humans"], sk["ai"]))
    if r["diag"]:
        on = [k for k, v in r["diag"].items() if v == "on" and k in ("passtimers", "highmem")]
        L.append("game patch: " + ", ".join("%s %s" % kv for kv in sorted(r["diag"].items()))
                 + ("  (NOTE: %s on; passtimers costs ~2 ms a frame)" % ", ".join(on) if on else ""))
    if fr:
        s = sorted(fr)
        n50, n100 = sum(x > r["spike_ms"] for x in fr), sum(x > 100 for x in fr)
        L.append("Frames (%s): %d, %.1f FPS mean; p50 %.1f, p95 %.1f, p99 %.1f, max %.0f ms; %.1f %% over 34 ms, "
                 "%d over %.0f ms, %d over 100 ms" % (r["src"], len(s), 1000.0 * len(s) / sum(s), pct(s, 50), pct(s, 95),
                 pct(s, 99), s[-1], 100.0 * sum(x > 34 for x in fr) / len(fr), n50, r["spike_ms"], n100))
    else:
        L.append("Frames: none recorded (the game must run with WINEDEBUG=...+timestamp,+frametime: play-rotwk.sh does that)")
    if sm:
        sat = 100.0 * sum(s["main"] >= 90 for s in sm) / len(sm)
        L.append("Threads (%% of one core, %s): main %.0f %% mean, >= 90 %% in %.0f %% of samples; render (wined3d_cs) "
                 "%.0f %% mean; whole process %.0f %%" % (r["ident"], statistics.mean(s["main"] for s in sm), sat,
                 statistics.mean(s["cs"] for s in sm), statistics.mean(s["proc"] for s in sm)))
        L.append("Memory (macOS side): resident peak %.0f MB, footprint peak %.0f MB" % (max(s["rss"] for s in sm),
                 max(s["fp"] for s in sm)))
        g = [s["gpu"][0] for s in sm if s.get("gpu")]
        if g:
            L.append("GPU (whole Mac): device utilisation mean %.0f %%, max %d %%" % (statistics.mean(g), max(g)))
    gm = r["game"]
    if gm:
        vm = gm["vm"]
        if vm:
            pk = max(vm, key=lambda v: v[1] + v[2])
            L.append("32-bit address space (game patch): peak used %d MB of %d (committed %d + reserved %d), smallest "
                     "largest-free-block %d MB" % (pk[1] + pk[2], pk[6] or 0, pk[1], pk[2], min(v[4] for v in vm)))
        gf = gm["frames"]
        if gf:
            L.append("D3DX loads (game thread): %d texture loads, %d creations, %d effects, %.0f ms in all; worst frame %.0f ms"
                     % (sum(f["tex"] for f in gf), sum(f["create"] for f in gf), sum(f["fx"] for f in gf),
                        sum(f["load_ms"] for f in gf), max(f["load_ms"] for f in gf)))
        ob = [o[1] for o in gm["objects"] if o[1] >= 0]
        if ob:
            L.append("Objects (TheGameLogic list): peak %d; logic rate %s frames/s" % (max(ob), r["logic_rate"]))
        if gm["dropped"]:
            L.append("game patch monitor dropped %d frame records" % gm["dropped"])
    sp = r["spikes"]
    if sp:
        causes = {}
        for c in sp:
            causes[c["cause"]] = causes.get(c["cause"], 0) + 1
        L.append("Frames over %.0f ms by cause: %s  (rule: %s)" % (r["spike_ms"], ", ".join(
            "%s %d" % kv for kv in sorted(causes.items(), key=lambda kv: -kv[1])), CAUSE_RULE))
        L.append("Slowest moments:")
        for c in sorted(sp, key=lambda c: -c["ms"])[:10]:
            L.append("  " + moment(c))
    L += stall_lines(r)
    if r["wins"]:
        L.append("Slowest 10 s stretches (FPS, mean / p95 ms, main / render thread %):")
        for w in sorted(r["wins"], key=lambda w: w["fps"])[:5]:
            L.append("  %s  %.1f FPS, %.1f / %.1f ms, main %.0f %%, render %.0f %%" % (clock(w["t"]), w["fps"], w["mean"],
                     w["p95"], w["main"], w["cs"]))
    L.append("Recorder: %d samples, %.1f s of CPU on other cores (%.2f %% of one core)" % (m.get("samples", 0),
             m.get("recorder_cpu_s", 0), 100.0 * m.get("recorder_cpu_s", 0) / max(1, m.get("end", 1) - m["start"])))
    return L


def stall_lines(r):
    """the stall sampler's histograms (tools/monitor_stalls.py); a failure there never stops the report"""
    p = os.path.join(r["dir"], "game.txt")
    if not monitor_stalls or not r["game"] or not os.path.exists(p):
        return []
    try:
        return monitor_stalls.lines(monitor_stalls.analyse(p), clock, r["game"]["off"])
    except Exception as e:   # noqa: BLE001 - the rest of the report still matters
        return ["Stalls: could not be analysed (%s: %s)" % (type(e).__name__, e)]


def run(d, spike_ms=50.0):
    r = analyse(d, spike_ms)
    r["dir"] = d
    lines = summary(r)
    with open(os.path.join(d, "summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(d, "report.html"), "w") as f:
        f.write(monitor_chart.html(r, lines, moment))
    print("\n".join(lines))
    print("report: %s" % os.path.relpath(os.path.join(d, "report.html"), ROOT))
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    sms = float(sys.argv[sys.argv.index("--spike-ms") + 1]) if "--spike-ms" in sys.argv else 50.0
    if "--spike-ms" in sys.argv:
        args = [a for a in args if a != sys.argv[sys.argv.index("--spike-ms") + 1]]
    sys.exit(run(args[0], sms))
