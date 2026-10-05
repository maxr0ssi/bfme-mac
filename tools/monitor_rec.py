#!/usr/bin/env python3
"""monitor_rec - the host side of scripts/monitor.sh: samples one running game (or bench) process
from outside until it exits, then writes the session report (tools/monitor_report.py).

    python3 tools/monitor_rec.py --pid PID --dir logs/sessions/<id> --log logs/rotwk-<date>.log [--any]

Every --interval s (0.5) it reads, through macOS's libproc (no signals, no ptrace, nothing runs
inside the game): every host thread's CPU time, name and priority (Wine gives a Windows thread's
name to its macOS thread: wined3d's render thread is "wined3d_cs", the game patch names the game's
main thread "bfme_main"), the process's resident memory and physical footprint. Every --gpu s (1)
it reads the GPU's "Device Utilization %" and "Renderer Utilization %" from `ioreg` (IOAccelerator;
the whole GPU, so other programs count too). It also reads the game log's new lines to pin the
clock of WINEDEBUG=+timestamp (Wine's tick count) to the wall clock: the smallest
(read time - tick) over the session is the offset, within the read interval.
Files in --dir: samples.jsonl (one line per sample), meta.json, and the report's files.
--any: the process need not be the game (tests on the D3D9 bench). Runs at nice 10.
"""
import ctypes
import json
import os
import re
import resource
import signal
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_RE = re.compile(r"(lotrbfme2(ep1)?\.exe|game\.dat) -win", re.I)
TICK_RE = re.compile(rb"^\s*(\d+)\.(\d{3}):")
_lp = ctypes.CDLL("/usr/lib/libproc.dylib")
_lp.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
_lp.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]


def _info(pid, flavor, arg, size):
    buf = ctypes.create_string_buffer(size)
    n = _lp.proc_pidinfo(pid, flavor, arg, buf, size)
    return buf.raw[:n] if n > 0 else b""


def threads(pid):
    """{handle: (name, priority, cpu_ns)} (PROC_PIDLISTTHREADS, PROC_PIDTHREADINFO: times in ns)"""
    raw = _info(pid, 6, 0, 8 * 2048)
    out = {}
    for h in struct.unpack("<%dQ" % (len(raw) // 8), raw):
        ti = _info(pid, 5, h, 112)
        if len(ti) < 112:
            continue
        u, s, _cpu, _pol, _run, _fl, _sl, cur, _pri, _maxp = struct.unpack("<QQ8i", ti[:48])
        out["%x" % h] = (ti[48:].split(b"\0")[0].decode("utf-8", "replace"), cur, u + s)
    return out


def memory(pid):
    """(resident MB, physical footprint MB)"""
    t = _info(pid, 4, 0, 96)
    rss = struct.unpack("<Q", t[8:16])[0] / 1048576.0 if len(t) >= 16 else 0.0
    buf = ctypes.create_string_buffer(512)
    fp = 0.0
    if _lp.proc_pid_rusage(pid, 2, buf) == 0:   # RUSAGE_INFO_V2; ri_phys_footprint at 72
        fp = struct.unpack("<Q", buf.raw[72:80])[0] / 1048576.0
    return round(rss, 1), round(fp, 1)


def gpu():
    try:
        out = subprocess.run(["ioreg", "-r", "-d", "1", "-w", "0", "-c", "IOAccelerator"],
                             capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    def num(key):
        m = re.search(r'"%s"=(\d+)' % re.escape(key), out)
        return int(m.group(1)) if m else -1
    return [num("Device Utilization %"), num("Renderer Utilization %"),
            round(num("In use system memory") / 1048576.0)]


def command(pid):
    r = subprocess.run(["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True)
    return r.stdout.strip()


def find_game():
    r = subprocess.run(["pgrep", "-f", GAME_RE.pattern], capture_output=True, text=True)
    pids = [int(x) for x in r.stdout.split()]
    return pids[0] if pids else None


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class LogClock:
    """tick (ms, WINEDEBUG=+timestamp) -> unix seconds: unix = tick / 1000 + offset"""
    def __init__(self, path):
        self.path, self.pos, self.offset, self.partial = path, 0, None, b""

    def poll(self):
        if not self.path or not os.path.exists(self.path):
            return
        with open(self.path, "rb") as f:
            f.seek(self.pos)
            data = f.read()
            self.pos = f.tell()
        now = time.time()
        if not data:
            return
        lines = (self.partial + data).split(b"\n")
        self.partial = lines[-1]
        for line in reversed(lines[:-1]):
            m = TICK_RE.match(line)
            if m:
                off = now - (int(m.group(1)) + int(m.group(2)) / 1000.0)
                self.offset = off if self.offset is None else min(self.offset, off)
                return


def main():
    a = sys.argv[1:]
    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a else default
    pid, d, log = int(opt("--pid", "0")), opt("--dir"), opt("--log")
    interval, gpu_every = float(opt("--interval", "0.5")), float(opt("--gpu", "1"))
    if not pid or not d:
        print(__doc__)
        return 2
    os.makedirs(d, exist_ok=True)
    os.nice(10)
    stop = []
    signal.signal(signal.SIGTERM, lambda *_: stop.append(1))
    signal.signal(signal.SIGINT, lambda *_: stop.append(1))
    signal.signal(signal.SIGHUP, signal.SIG_IGN)   # a closed Terminal window: keep recording the game
    gplog = os.path.join(ROOT, "logs", "gamepatch.log")
    meta = {"start": time.time(), "pid": pid, "log": log, "interval": interval,
            "gamepatch_log": gplog, "gamepatch_log_offset": os.path.getsize(gplog) if os.path.exists(gplog) else 0,
            "winedebug": os.environ.get("WINEDEBUG", ""), "any": "--any" in a}
    # wait until the game runs: the given pid once it has exec'd into the game (play-rotwk.sh starts us
    # just before its exec), else any process that matches the game's command line (2 minutes at most)
    t_wait = time.time()
    while "--any" not in a and not stop:
        if alive(pid) and GAME_RE.search(command(pid)):
            break
        g = find_game()
        if g:
            pid = g
            break
        if time.time() - t_wait > 120:
            meta["error"] = "no game process within 120 s"
            break
        time.sleep(0.5)
    meta["pid"], meta["command"] = pid, command(pid)
    clock = LogClock(log)
    prev, last_gpu, n = {}, 0.0, 0
    with open(os.path.join(d, "samples.jsonl"), "w") as out:
        while not stop and alive(pid):
            t0 = time.time()
            th = threads(pid)
            if not th:
                break
            rss, fp = memory(pid)
            rec = {"t": round(t0, 3), "rss": rss, "fp": fp,
                   "thr": [[h, v[0], v[1], round((v[2] - prev[h][2]) / 1e6, 2)]
                           for h, v in th.items() if h in prev and v[2] > prev[h][2]]}
            if n == 0:
                rec["thr0"] = [[h, v[0], v[1]] for h, v in th.items()]
            prev = th
            if t0 - last_gpu >= gpu_every:
                g = gpu()
                if g:
                    rec["gpu"] = g
                last_gpu = t0
            clock.poll()
            out.write(json.dumps(rec, separators=(",", ":")) + "\n")
            n += 1
            if n % 10 == 0:
                out.flush()
            time.sleep(max(0.05, interval - (time.time() - t0)))
    clock.poll()
    ru, rc = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    meta.update({"end": time.time(), "samples": n, "tick_offset": clock.offset,
                 "recorder_cpu_s": round(ru.ru_utime + ru.ru_stime + rc.ru_utime + rc.ru_stime, 2)})
    with open(os.path.join(d, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    if "--no-report" not in a:
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "monitor_report.py"), d])
    return 0


if __name__ == "__main__":
    sys.exit(main())
