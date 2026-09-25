#!/usr/bin/env python3
"""perfprobe - measure a running BFME2/RotWK game in one pass, for docs/PERFORMANCE.md.

    python3 tools/perfprobe.py <label> [seconds] [--no-eip]

Over the same window it records:
  * frame rate and frame times, from wined3d's own trace channels. The game must have been
    started with them on:  WINEDEBUG=-all,+fps,+frametime scripts/play-rotwk.sh
    (+frametime is one line per frame, +fps one line per 1.5 s; cheap.)
  * CPU time of every host thread of the game process (`ps -M` user+system time, before/after)
  * where the busiest guest thread spends its time (build/eipsample.exe, tools/eipsample.c)

Output goes to logs/perf-<label>-<time>.txt and a summary to stdout. Run it only while the part
of the game you want to measure is on screen; it runs for `seconds` + ~4 s.
"""
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, "logs")
GAME_RE = re.compile(r"lotrbfme2|game\.dat", re.I)

# Guest return addresses worth naming (w10 engine opengl32.dll; docs/PERFORMANCE.md).
KNOWN_SITES = {
    "opengl32.dll+0x559dd": "glMapBufferRange (1st unix call: the driver's map)",
    "opengl32.dll+0xbcd3d": "glUnmapBuffer (unix call: WoW64 copy-back + unmap)",
}


def game_pid():
    out = subprocess.run(["ps", "-axo", "pid=,%cpu=,command="], capture_output=True, text=True).stdout
    best = None
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and GAME_RE.search(parts[2]) and "perfprobe" not in parts[2]:
            cpu = float(parts[1])
            if best is None or cpu > best[1]:
                best = (int(parts[0]), cpu, parts[2])
    return best


def cputime(s):
    """ps time 'M:SS.cc' or 'H:MM:SS' -> seconds"""
    total = 0.0
    for part in s.split(":"):
        total = total * 60 + float(part)
    return total


def thread_times(pid, prios=None):
    """per-thread user+system seconds; also fills prios with each thread's scheduling priority
    (ps PRI: 31 = default/interactive, 4 = background, which macOS keeps on efficiency cores)"""
    out = subprocess.run(["ps", "-M", "-p", str(pid)], capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines()[1:]:
        f = line.split()
        times = [x for x in f if re.fullmatch(r"\d+:\d+(:\d+)?(\.\d+)?", x)]
        if len(times) >= 2:   # ... STAT PRI STIME UTIME [COMMAND]
            rows.append(cputime(times[-2]) + cputime(times[-1]))
            if prios is not None:
                i = f.index(times[-2])
                prios.append(f[i - 1] if i > 0 else "?")
    return rows


def newest_game_log():
    cands = [os.path.join(LOGS, f) for f in os.listdir(LOGS)
             if re.match(r"(rotwk|bfme2|app-)", f) and f.endswith(".log")]
    return max(cands, key=os.path.getmtime) if cands else None


def pct(sorted_vals, p):
    k = min(len(sorted_vals) - 1, max(0, int(round(p / 100.0 * (len(sorted_vals) - 1)))))
    return sorted_vals[k]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    label = args[0]
    secs = int(args[1]) if len(args) > 1 else 30
    found = game_pid()
    if not found:
        print("perfprobe: no game process running")
        return 1
    pid = found[0]
    log = newest_game_log()
    log_off = os.path.getsize(log) if log else 0

    t0 = time.time()
    th0 = thread_times(pid)
    eip = ""
    if "--no-eip" not in sys.argv:
        env = dict(os.environ, WINE_BUILD=os.environ.get("WINE_BUILD", "w10"), BFME_ROOT=ROOT,
                   WINEDEBUG="-all")
        eip = subprocess.run(["/bin/zsh", "-c", ". ./env.sh && wine build/eipsample.exe %d 5" % secs],
                             cwd=ROOT, env=env, capture_output=True, text=True).stdout
    else:
        time.sleep(secs)
    prios = []
    th1 = thread_times(pid, prios)
    wall = time.time() - t0

    frames, fps = [], []
    if log:
        with open(log, "rb") as fh:
            fh.seek(log_off)
            for line in fh.read().decode("utf-8", "replace").splitlines():
                m = re.search(r"Frame duration (\d+)", line)
                if m:
                    frames.append(int(m.group(1)) / 1000.0)
                m = re.search(r"@ approx ([\d.]+)fps", line)
                if m:
                    fps.append(float(m.group(1)))

    out = ["perfprobe %s  %s  pid %d  window %.1f s" % (label, time.strftime("%Y-%m-%d %H:%M:%S"), pid, wall),
           "log: %s" % (os.path.relpath(log, ROOT) if log else "none")]
    if frames:
        s = sorted(frames)
        out.append("frames: %d  mean %.1f ms (%.1f FPS)  p50 %.1f  p95 %.1f  p99 %.1f  max %.1f ms"
                   % (len(s), sum(s) / len(s), 1000.0 * len(s) / sum(s),
                      pct(s, 50), pct(s, 95), pct(s, 99), s[-1]))
    if fps:
        out.append("fps (1.5 s windows): %s" % " ".join("%.1f" % f for f in fps))
    if not frames and not fps:
        out.append("frames: none - start the game with WINEDEBUG=-all,+fps,+frametime")
    if th0 and len(th0) == len(th1):
        d = sorted(((th1[i] - th0[i]) / wall * 100.0, i) for i in range(len(th0)))[::-1]
        out.append("process CPU %.0f%%; busiest host threads (%% of one core, priority): %s"
                   % (sum(x for x, _ in d), "  ".join("#%d %.0f pri %s" % (i, x, prios[i] if i < len(prios) else "?")
                                                   for x, i in d[:6])))
    else:
        out.append("thread count changed (%d -> %d); per-thread CPU skipped" % (len(th0), len(th1)))

    summary = list(out)
    if eip:
        leaf = eip.split("== leaf module")[-1].split("== owner module")[0]
        mods = re.findall(r"^\s+([\d.]+)%\s+\d+\s+(\S+)$", leaf, re.M)
        summary.append("busiest guest thread, leaf modules: %s"
                       % ", ".join("%s %s%%" % (m, p) for p, m in mods[:6]))
        sites = re.findall(r"^\s+([\d.]+)%\s+\d+\s+(\S+)$",
                           eip.split("call sites into system libraries")[-1].split("== modules")[0], re.M)
        for p, site in sites[:6]:
            summary.append("  call site %6s%%  %s  %s" % (p, site, KNOWN_SITES.get(site, "")))
        out += ["", eip]

    path = os.path.join(LOGS, "perf-%s-%s.txt" % (label, time.strftime("%Y%m%d-%H%M%S")))
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("\n".join(summary))
    print("full: %s" % os.path.relpath(path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
