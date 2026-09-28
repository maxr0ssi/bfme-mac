#!/usr/bin/env python3
"""memwatch.py - the macOS half of the game memory probe, and its summary.

  wine build/memwatch.exe ... | tools/memwatch.py join > logs/memwatch-<date>.csv
      passes the guest rows through and appends the macOS side of the same process at the moment
      each row arrives: resident size and physical footprint (proc_pid_rusage, which reads kernel
      counters and never touches the target). Under WoW64 the Unix side of the game - wined3d.so,
      the GL driver, Rosetta's translations - lives outside the 32-bit address space, so the host
      figures grow independently of the 2 GB limit; the footprint includes GPU memory the process
      owns. A one-line status goes to stderr per row.
  tools/memwatch.py summary <csv> [--png out.png]
      peak committed, smallest largest-free-block and when, peak host footprint, probe cost;
      --png draws committed, largest free block and host footprint over time.
"""
import argparse
import csv
import ctypes
import struct
import subprocess
import sys
import zlib

SPAN_MB = 2048.0


# --------------------------------------------------------------------------------------------
# join: guest rows in, guest + host rows out
# --------------------------------------------------------------------------------------------

def unix_pid(exe):
    """The macOS process whose command's first word is the Windows exe (Wine sets the process
    title to the Windows command line); the largest if several match (a launcher stub)."""
    out = subprocess.run(["ps", "-axo", "pid=,rss=,command="], capture_output=True, text=True).stdout
    best = (0, None)
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 3 or not parts[2].split():
            continue
        first = parts[2].split()[0].replace("\\", "/").rsplit("/", 1)[-1]
        if first.lower() == exe.lower() and int(parts[1]) > best[0]:
            best = (int(parts[1]), int(parts[0]))
    return best[1]


_libproc = None


def rusage(pid):
    """(resident MB, footprint MB, lifetime peak footprint MB) from proc_pid_rusage flavor 4."""
    global _libproc
    if _libproc is None:
        _libproc = ctypes.CDLL("/usr/lib/libproc.dylib")
    buf = ctypes.create_string_buffer(16 + 8 * 48)
    if _libproc.proc_pid_rusage(ctypes.c_int(pid), ctypes.c_int(4), buf) != 0:
        return None
    v = struct.unpack_from("<48Q", buf.raw, 16)
    mb = 1024.0 * 1024.0
    # rusage_info_v4: [6] resident_size, [7] phys_footprint, [28] lifetime_max_phys_footprint
    return v[6] / mb, v[7] / mb, v[28] / mb


def join(args):
    exe, pid = None, None
    host_cols = "host_rss_mb,host_footprint_mb,host_peak_footprint_mb"
    for line in sys.stdin:
        line = line.rstrip("\r\n")
        if line.startswith("#"):
            print(line, flush=True)
            for tok in line.split():
                if tok.startswith("target="):
                    exe = tok[len("target="):]
            print(line, file=sys.stderr)
            continue
        if line.startswith("time,"):
            print(f"{line},{host_cols}", flush=True)
            head = line.split(",")
            continue
        if exe and (pid is None or rusage(pid) is None):
            pid = unix_pid(exe)
            if pid:
                print(f"# host pid={pid}", flush=True)
        h = rusage(pid) if pid else None
        host = ",".join(f"{x:.1f}" for x in h) if h else ",,"
        print(f"{line},{host}", flush=True)
        row = dict(zip(head, line.split(",")))
        print(f"{row.get('time')}  committed {row.get('committed_mb')} MB  largest free "
              f"{row.get('largest_free_mb')} MB  host {h[1]:.0f} MB" if h else
              f"{row.get('time')}  committed {row.get('committed_mb')} MB  largest free "
              f"{row.get('largest_free_mb')} MB", file=sys.stderr, flush=True)


# --------------------------------------------------------------------------------------------
# summary
# --------------------------------------------------------------------------------------------

def load(path):
    global SPAN_MB
    with open(path, newline="") as f:
        lines = list(f)
    for l in lines:                                   # the game's own limit: 2 GB, or 4 GB with LAA
        if l.startswith("# memwatch") and " MB)" in l:
            SPAN_MB = float(l.rsplit("(", 1)[1].split()[0])
    lines = [l for l in lines if not l.startswith("#")]
    rows = []
    for r in csv.DictReader(lines):
        try:
            rows.append({k: (v if k in ("time", "largest_free_at") else float(v) if v else None)
                         for k, v in r.items()})
        except ValueError:
            continue                                  # a row cut short when the probe stopped
    return rows


def median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0.0


def summary(args):
    rows = load(args.csv)
    if not rows:
        sys.exit(f"{args.csv}: no samples")
    dur = rows[-1]["t_s"] - rows[0]["t_s"]
    pk = max(rows, key=lambda r: r["committed_mb"])
    lf = min(rows, key=lambda r: r["largest_free_mb"])
    used = max(rows, key=lambda r: r["committed_mb"] + r["reserved_mb"])
    print(f"{args.csv}: {len(rows)} samples over {dur / 60:.1f} min ({rows[0]['time']} - {rows[-1]['time']})")
    print(f"peak committed      {pk['committed_mb']:7.0f} MB at {pk['time']}  (private {pk['private_mb']:.0f}, "
          f"image {pk['image_mb']:.0f}, mapped {pk['mapped_mb']:.0f})")
    print(f"peak address used   {used['committed_mb'] + used['reserved_mb']:7.0f} MB at {used['time']}  "
          f"(committed + reserved, of {SPAN_MB:.0f})")
    print(f"min largest free    {lf['largest_free_mb']:7.0f} MB at {lf['time']}  (free {lf['free_mb']:.0f} MB "
          f"in total, {lf['free_blocks_16mb']:.0f} blocks over 16 MB)")
    print(f"  -> the biggest single allocation that would still have succeeded at the worst moment")
    hosts = [r for r in rows if r.get("host_footprint_mb") is not None]
    if hosts:
        hp = max(hosts, key=lambda r: r["host_footprint_mb"])
        print(f"peak host footprint {hp['host_footprint_mb']:7.0f} MB at {hp['time']}  (resident "
              f"{hp['host_rss_mb']:.0f} MB; macOS side, outside the {SPAN_MB / 1024:.0f} GB)")
    q = [r["queries"] for r in rows]
    qm = [r["query_ms"] for r in rows]
    gaps = [b["t_s"] - a["t_s"] for a, b in zip(rows, rows[1:])]
    print(f"probe cost          {median(q):.0f} queries/sample, {median(qm):.0f} ms median "
          f"({max(qm):.0f} max) of target time per sample, one sample every {median(gaps) if gaps else 0:.1f} s")
    if args.png:
        chart(rows, args.png)
        print(f"chart: {args.png}")


# --------------------------------------------------------------------------------------------
# chart: a stdlib-only PNG (one MB axis; three series from the reference categorical order)
# --------------------------------------------------------------------------------------------

SURFACE, INK, MUTED, GRID = (0xfc, 0xfc, 0xfb), (0x0b, 0x0b, 0x0b), (0x52, 0x51, 0x4e), (0xe5, 0xe4, 0xe0)
SERIES = [("committed", "COMMITTED", (0x2a, 0x78, 0xd6)),
          ("largest_free_mb", "LARGEST FREE BLOCK", (0xeb, 0x68, 0x34)),
          ("host_footprint_mb", "HOST FOOTPRINT", (0x1b, 0xaf, 0x7a))]
# 3x5 glyphs, rows top to bottom, 3 bits each (4 = left column)
FONT = {
    "0": (7, 5, 5, 5, 7), "1": (2, 6, 2, 2, 7), "2": (7, 1, 7, 4, 7), "3": (7, 1, 7, 1, 7),
    "4": (5, 5, 7, 1, 1), "5": (7, 4, 7, 1, 7), "6": (7, 4, 7, 5, 7), "7": (7, 1, 1, 1, 1),
    "8": (7, 5, 7, 5, 7), "9": (7, 5, 7, 1, 7), " ": (0, 0, 0, 0, 0), ":": (0, 2, 0, 2, 0),
    ".": (0, 0, 0, 0, 2), "-": (0, 0, 7, 0, 0), "A": (2, 5, 7, 5, 5), "B": (6, 5, 6, 5, 6),
    "C": (7, 4, 4, 4, 7), "D": (6, 5, 5, 5, 6), "E": (7, 4, 6, 4, 7), "F": (7, 4, 6, 4, 4),
    "G": (7, 4, 5, 5, 7), "H": (5, 5, 7, 5, 5), "I": (7, 2, 2, 2, 7), "K": (5, 5, 6, 5, 5),
    "L": (4, 4, 4, 4, 7), "M": (5, 7, 7, 5, 5), "N": (6, 5, 5, 5, 5), "O": (7, 5, 5, 5, 7),
    "P": (7, 5, 7, 4, 4), "R": (6, 5, 6, 5, 5), "S": (7, 4, 7, 1, 7), "T": (7, 2, 2, 2, 2),
    "U": (5, 5, 5, 5, 7), "W": (5, 5, 7, 7, 5), "X": (5, 5, 2, 5, 5), "Y": (5, 5, 2, 2, 2),
}


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [bytearray(bytes(SURFACE) * w) for _ in range(h)]

    def dot(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][3 * x:3 * x + 3] = bytes(c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.dot(x, y, c)

    def line(self, x0, y0, x1, y1, c, width=2):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            y = round(y0 + (y1 - y0) * i / n)
            self.rect(x - width // 2, y - width // 2, x - width // 2 + width, y - width // 2 + width, c)

    def text(self, x, y, s, c, scale=2):
        for ch in s.upper():
            for r, bits in enumerate(FONT.get(ch, FONT[" "])):
                for col in range(3):
                    if bits & (4 >> col):
                        self.rect(x + col * scale, y + r * scale, x + (col + 1) * scale, y + (r + 1) * scale, c)
            x += 4 * scale
        return x

    def png(self, path):
        raw = b"".join(b"\x00" + bytes(r) for r in self.px)

        def chunk(kind, body):
            return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
                    + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def chart(rows, path):
    W, H, L, R, T, B = 1000, 480, 70, 30, 60, 50
    cv = Canvas(W, H)
    for r in rows:
        r["committed"] = r["committed_mb"]
    ymax = max([SPAN_MB] + [r[k] for r in rows for k, _, _ in SERIES if r.get(k) is not None])
    ymax = 512 * (int(ymax) // 512 + 1)
    t0, t1 = rows[0]["t_s"], max(rows[-1]["t_s"], rows[0]["t_s"] + 1)

    def X(t):
        return L + round((t - t0) / (t1 - t0) * (W - L - R))

    def Y(v):
        return H - B - round(v / ymax * (H - T - B))
    for v in range(0, ymax + 1, 256):
        cv.rect(L, Y(v), W - R, Y(v) + 1, GRID)
        if v % 512 == 0:
            cv.text(L - 8 - 8 * len(str(v)), Y(v) - 5, str(v), MUTED)
    for x in range(L, W - R, 12):                    # the address-space limit, dashed
        cv.rect(x, Y(SPAN_MB), x + 6, Y(SPAN_MB) + 2, MUTED)
    cv.text(W - R - 8 * 13, Y(SPAN_MB) - 16, f"{SPAN_MB / 1024:.0f} GB ADDRESS", MUTED)
    cv.rect(L, H - B, W - R, H - B + 1, MUTED)
    cv.text(L - 8 * 2, T - 40, "MB", MUTED)
    step = max(60, int((t1 - t0) / 8 / 60 + 1) * 60)
    for t in range(0, int(t1 - t0) + 1, step):
        cv.rect(X(t0 + t), H - B, X(t0 + t) + 1, H - B + 6, MUTED)
        cv.text(X(t0 + t) - 8, H - B + 12, f"{t // 60}", MUTED)
    cv.text(W - R - 8 * 7, H - B + 30, "MINUTES", MUTED)
    lx = L
    for key, label, col in SERIES:
        pts = [(X(r["t_s"]), Y(r[key])) for r in rows if r.get(key) is not None]
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            cv.line(xa, ya, xb, yb, col)
        if pts:                                        # direct label at the line's end
            cv.rect(pts[-1][0] - 4, pts[-1][1] - 4, pts[-1][0] + 4, pts[-1][1] + 4, col)
        cv.rect(lx, T - 26, lx + 14, T - 12, col)      # legend
        lx = cv.text(lx + 20, T - 24, label, INK) + 24
    cv.png(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("join")
    s = sub.add_parser("summary")
    s.add_argument("csv")
    s.add_argument("--png")
    args = ap.parse_args()
    try:
        join(args) if args.cmd == "join" else summary(args)
    except (KeyboardInterrupt, BrokenPipeError):
        pass


if __name__ == "__main__":
    main()
