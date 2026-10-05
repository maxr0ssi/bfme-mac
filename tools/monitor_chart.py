"""monitor_chart - the HTML page of a scripts/monitor.sh session (used by tools/monitor_report.py).

One page, no external files: the summary, then aligned strips on one time axis (frame time,
main / render thread CPU, memory, D3DX load time, GPU, objects), each with its own single y axis,
slow frames marked across all strips, a crosshair with every strip's value under the pointer, the
slowest-moment table and the log events. Light and dark colours follow the system setting.
"""
import html as H
import json
import statistics
import time

W, LM, RM, SH, GAP, TOP = 1000, 58, 14, 104, 34, 8
PW = W - LM - RM
COLS = 500

CSS = """
:root{--bg:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;
--s1:#2a78d6;--s1l:#9ec5f4;--s2:#eb6834;--s3:#1baf7a;--crit:#d03b3b;--ring:rgba(11,11,11,.10)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;
--grid:#2c2c2a;--axis:#383835;--s1:#3987e5;--s1l:#1c5cab;--s2:#d95926;--s3:#199e70;--ring:rgba(255,255,255,.10)}}
:root[data-theme="dark"]{--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--grid:#2c2c2a;--axis:#383835;
--s1:#3987e5;--s1l:#1c5cab;--s2:#d95926;--s3:#199e70;--ring:rgba(255,255,255,.10)}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 8px}
.card{background:var(--surface);border:1px solid var(--ring);border-radius:10px;padding:12px 14px}
pre{white-space:pre-wrap;font:12.5px/1.5 ui-monospace,Menlo,monospace;margin:0;color:var(--ink2)}
svg{width:100%;height:auto;display:block}
svg text{fill:var(--muted);font:12.5px system-ui,-apple-system,sans-serif}
svg .t{fill:var(--ink2);font-weight:600;font-size:13.5px}
.grid{stroke:var(--grid);stroke-width:1}.base{stroke:var(--axis);stroke-width:1}
.l1{stroke:var(--s1);fill:none;stroke-width:1.6}.l2{stroke:var(--s2);fill:none;stroke-width:1.6}
.l3{stroke:var(--s3);fill:none;stroke-width:1.6}.a1{fill:var(--s1l)}.b1{fill:var(--s1)}
.sp{stroke:var(--crit);stroke-width:1;opacity:.28}.spm{fill:var(--crit)}.ref{stroke:var(--axis);stroke-dasharray:3 3}
.lim{stroke:var(--crit);stroke-dasharray:4 3;opacity:.7}
.key{display:inline-flex;align-items:center;gap:6px;margin-right:14px;color:var(--ink2);font-size:12.5px}
.sw{width:14px;height:3px;border-radius:2px;display:inline-block}
#tip{position:fixed;pointer-events:none;background:var(--surface);border:1px solid var(--ring);border-radius:8px;
padding:6px 9px;font-size:12px;color:var(--ink);display:none;box-shadow:0 2px 8px rgba(0,0,0,.15);white-space:nowrap}
#xh{stroke:var(--ink2);stroke-width:1;opacity:.5}
table{border-collapse:collapse;width:100%;font-size:12.5px}td,th{text-align:left;padding:4px 8px;border-bottom:1px solid var(--grid);
vertical-align:top}th{color:var(--ink2);font-weight:600}td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.wrap{overflow-x:auto}
"""

JS = """
const D=JSON.parse(document.getElementById('data').textContent);
const svg=document.getElementById('chart'),tip=document.getElementById('tip'),xh=document.getElementById('xh');
function show(ev){const r=svg.getBoundingClientRect(),sx=(ev.clientX-r.left)*D.W/r.width;
 const c=Math.floor((sx-D.LM)/D.PW*D.COLS);if(c<0||c>=D.COLS){hide();return;}
 xh.setAttribute('x1',sx);xh.setAttribute('x2',sx);xh.style.display='';
 let h='<b>'+D.time[c]+'</b>';for(const s of D.rows){const v=s.v[c];if(v!==null&&v!==undefined)h+='<br>'+s.name+': '+v;}
 tip.innerHTML=h;tip.style.display='block';
 const x=ev.clientX+14,y=ev.clientY+14;tip.style.left=Math.min(x,innerWidth-tip.offsetWidth-8)+'px';
 tip.style.top=Math.min(y,innerHeight-tip.offsetHeight-8)+'px';}
function hide(){tip.style.display='none';xh.style.display='none';}
svg.addEventListener('mousemove',show);svg.addEventListener('mouseleave',hide);
"""


def _cols(t0, t1, items, val, agg):
    """items (t, ...) -> one aggregated value per column (None where empty)"""
    b = [[] for _ in range(COLS)]
    span = max(1e-6, t1 - t0)
    for it in items:
        c = int((it[0] - t0) / span * COLS)
        if 0 <= c < COLS:
            v = val(it)
            if v is not None:
                b[c].append(v)
    return [agg(x) if x else None for x in b]


def _path(vals, y, cls):
    """a line through the non-empty columns; a gap of more than 3 times the usual spacing (and more
    than 5 % of the axis) breaks it: no data there"""
    idx = [i for i, v in enumerate(vals) if v is not None]
    gaps = sorted(b - a for a, b in zip(idx, idx[1:]))
    brk = max(25, 3 * gaps[len(gaps) // 2]) if gaps else 25
    d, last = [], None
    for i, v in enumerate(vals):
        if v is None:
            continue
        x = LM + (i + 0.5) * PW / COLS
        d.append(("L" if last is not None and i - last <= brk else "M") + "%.1f %.1f" % (x, y(v)))
        last = i
    return '<path class="%s" d="%s"/>' % (cls, " ".join(d)) if d else ""


def _nice(v):
    """the smallest of 1, 2, 2.5, 4, 5, 8 x 10^k at or above v (axis tops with whole quarter ticks)"""
    k = 10 ** max(0, len(str(int(max(v, 1)))) - 1)
    for m in (1, 2, 2.5, 4, 5, 8, 10):
        if m * k >= v:
            return m * k
    return 10 * k


def _strip(out, top, title, unit, vmax, series, refs=(), area=None, bars=None, limit=None):
    """series: [(vals, cls)]; area: per-column max drawn as light bars; refs: [(value, label)]"""
    vmax = _nice(vmax)
    y = lambda v: top + SH - min(v, vmax) / vmax * SH
    out.append('<text class="t" x="%d" y="%d">%s</text>' % (LM, top - 8, H.escape(title)))
    for k in range(5):
        v = vmax * k / 4
        out.append('<line class="%s" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/>' % ("base" if k == 0 else "grid", LM, W - RM, y(v), y(v)))
        out.append('<text x="%d" y="%.1f" text-anchor="end">%s</text>' % (LM - 6, y(v) + 4, ("%g" % round(v, 1)) + (unit if k == 4 else "")))
    if area:
        for i, v in enumerate(area):
            if v:
                x = LM + i * PW / COLS
                out.append('<rect class="a1" x="%.1f" y="%.1f" width="%.2f" height="%.1f"/>' % (x, y(v), PW / COLS, top + SH - y(v)))
    if bars:
        for i, v in enumerate(bars):
            if v:
                x = LM + i * PW / COLS
                out.append('<rect class="b1" x="%.1f" y="%.1f" width="%.2f" height="%.1f"/>' % (x, y(v), max(1.0, PW / COLS), top + SH - y(v)))
    for k, (v, label) in enumerate(refs):
        if v < vmax:
            out.append('<line class="ref" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/><text x="%d" y="%.1f" text-anchor="%s">%s</text>'
                       % (LM, W - RM, y(v), y(v), (W - RM - 2) if k == 0 else LM + 4, y(v) - 3, "end" if k == 0 else "start", label))
    if limit:
        out.append('<line class="lim" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/><text x="%d" y="%.1f" text-anchor="end">%s</text>'
                   % (LM, W - RM, y(limit[0]), y(limit[0]), W - RM - 2, y(limit[0]) + 12, limit[1]))
    for vals, cls in series:
        out.append(_path(vals, y, cls))


def html(r, lines, moment):
    t0, t1 = r["t0"], r["t1"]
    fr, sm, gm = r["frames"], r["samples"], r["game"]
    fmt = lambda v, f: None if v is None else f % v
    rows, strips = [], []
    fmax = _cols(t0, t1, fr, lambda f: f[1], max)
    fmed = _cols(t0, t1, fr, lambda f: f[1], statistics.median)
    p999 = sorted(x[1] for x in fr)[int(len(fr) * 0.999)] if fr else 50
    vmax_f = min(250.0, max(60.0, p999 * 1.15))
    strips.append(("Frame time (%s): column median line, column max in light bars" % r["src"].split(" (")[0], "ms", vmax_f,
                   [(fmed, "l1")], [(33.3, "33 ms = 30 FPS"), (r["spike_ms"], "%.0f ms" % r["spike_ms"])], fmax, None, None))
    rows += [{"name": "frame median", "v": [fmt(v, "%.1f ms") for v in fmed]}, {"name": "frame max", "v": [fmt(v, "%.0f ms") for v in fmax]}]
    if sm:
        st = [(s["t"], s) for s in sm]
        mn = _cols(t0, t1, st, lambda s: s[1]["main"], statistics.mean)
        cs = _cols(t0, t1, st, lambda s: s[1]["cs"], statistics.mean)
        strips.append(("CPU, % of one core: main thread (blue) and render thread wined3d_cs (orange)", "%", 100.0,
                       [(mn, "l1"), (cs, "l2")], [], None, None, None))
        rows += [{"name": "main thread", "v": [fmt(v, "%.0f %%") for v in mn]}, {"name": "render thread", "v": [fmt(v, "%.0f %%") for v in cs]}]
        rss = _cols(t0, t1, st, lambda s: s[1]["rss"], max)
        mem_series, lim = [(rss, "l3")], None
        vm = gm["vm"] if gm else []
        used = _cols(t0, t1, vm, lambda v: v[1] + v[2], max) if vm else None
        vmax_m = max([x for x in rss if x] + [1])
        title = "Memory, MB: macOS resident (aqua)"
        if vm:
            mem_series.append((used, "l1"))
            total = vm[-1][6] or 4096
            vmax_m, lim, title = max(vmax_m, total * 1.05), (total, "32-bit limit %d MB" % total), title + ", 32-bit address space used (blue)"
            rows.append({"name": "address space used", "v": [fmt(v, "%d MB") for v in used]})
        strips.append((title, "", vmax_m * 1.05, mem_series, [], None, None, lim))
        rows.append({"name": "resident", "v": [fmt(v, "%.0f MB") for v in rss]})
        gp = [(s["t"], s["gpu"][0]) for s in sm if s.get("gpu")]
        if gp:
            g = _cols(t0, t1, gp, lambda x: x[1], statistics.mean)
            strips.append(("GPU device utilisation, % (whole Mac)", "%", 100.0, [(g, "l2")], [], None, None, None))
            rows.append({"name": "GPU", "v": [fmt(v, "%.0f %%") for v in g]})
    if gm and gm["frames"]:
        gf = [(f["t"], f) for f in gm["frames"]]
        ld = _cols(t0, t1, gf, lambda f: f[1]["load_ms"], sum)
        n = _cols(t0, t1, gf, lambda f: f[1]["loads"], sum)
        strips.append(("D3DX texture and effect loads on the game thread, ms per column", "", max([x for x in ld if x] + [10]) * 1.1,
                       [], [], None, ld, None))
        rows.append({"name": "D3DX loads", "v": [None if a is None else "%d (%.0f ms)" % (b or 0, a) for a, b in zip(ld, n)]})
        ob = [(o[0], o[1]) for o in gm["objects"] if o[1] >= 0]
        if ob and max(o[1] for o in ob) > 0:
            o = _cols(t0, t1, ob, lambda x: x[1], max)
            strips.append(("Objects in the game logic", "", max(x for x in o if x is not None) * 1.15 or 1, [(o, "l1")], [], None, None, None))
            rows.append({"name": "objects", "v": [fmt(v, "%d") for v in o]})
    hgt = TOP + 20 + len(strips) * (SH + GAP) + 24
    out = ['<svg id="chart" viewBox="0 0 %d %d" role="img" aria-label="session timeline">' % (W, hgt)]
    for i, s in enumerate(strips):
        _strip(out, TOP + 20 + i * (SH + GAP), *s)
    span = max(1e-6, t1 - t0)
    yb = TOP + 20 + len(strips) * (SH + GAP) - GAP + 4
    for c in r["spikes"]:
        x = LM + (c["t"] - t0) / span * PW
        out.append('<line class="sp" x1="%.1f" x2="%.1f" y1="%d" y2="%d"/>' % (x, x, TOP + 14, yb))
        out.append('<path class="spm" d="M%.1f %d l-4 -7 h8 z"><title>%s</title></path>' % (x, TOP + 18, H.escape(moment(c))))
    for k in range(7):
        t = t0 + span * k / 6
        x = LM + PW * k / 6
        out.append('<text x="%.1f" y="%d" text-anchor="%s">%s</text>' % (x, yb + 14, "start" if k == 0 else "end" if k == 6 else "middle",
                   time.strftime("%H:%M:%S", time.localtime(t))))
    out.append('<line id="xh" x1="0" x2="0" y1="%d" y2="%d" style="display:none"/></svg>' % (TOP + 14, yb))
    for row in rows:   # the tooltip shows the nearest earlier value of a sparse series (samples every 0.25-2 s)
        last, age = None, 0
        for i, v in enumerate(row["v"]):
            if v is None and last is not None and age < 40:
                row["v"][i], age = last, age + 1
            elif v is not None:
                last, age = v, 0
    data = {"W": W, "LM": LM, "PW": PW, "COLS": COLS, "rows": rows,
            "time": [time.strftime("%H:%M:%S", time.localtime(t0 + span * (i + 0.5) / COLS)) for i in range(COLS)]}
    sp = sorted(r["spikes"], key=lambda c: -c["ms"])[:200]
    tr = "".join("<tr><td>%s</td><td class=n>%.0f</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>"
                 "<td class=n>%s</td><td class=n>%s</td><td>%s</td><td>%s</td></tr>" % (
                     time.strftime("%H:%M:%S", time.localtime(c["t"])), c["ms"],
                     "%.0f" % c["main"] if "main" in c else "", "%.0f" % c["cs"] if "cs" in c else "",
                     "%+.0f" % c["rss_jump"] if "rss_jump" in c else "",
                     "%d / %.0f ms" % (c["loads"], c["load_ms"]) if "loads" in c else "",
                     "%.1f" % c["minute"] if c.get("minute") is not None else "", c["cause"],
                     H.escape(" | ".join(c["events"]))) for c in sp)
    ev = "".join("<tr><td>%s</td><td>%s</td></tr>" % (time.strftime("%H:%M:%S", time.localtime(t)), H.escape(m))
                 for t, m in r["events"][:300])
    keys = ('<span class="key"><span class="sw" style="background:var(--s1)"></span>frame median / main thread / address space</span>'
            '<span class="key"><span class="sw" style="background:var(--s2)"></span>render thread / GPU</span>'
            '<span class="key"><span class="sw" style="background:var(--s3)"></span>resident memory</span>'
            '<span class="key"><span class="sw" style="background:var(--crit)"></span>frame over %.0f ms (hover the triangle)</span>' % r["spike_ms"])
    title = "Session %s" % H.escape(r["dir"].rstrip("/").split("/")[-1])
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body><main><h1>%s</h1><div class=card><pre>%s</pre></div>"
            "<h2>Timeline</h2><div class=card>%s<div class=wrap>%s</div></div>"
            "<h2>Slowest frames (up to 200)</h2><div class='card wrap'><table><tr><th>time</th><th>ms</th><th>main %%</th>"
            "<th>render %%</th><th>resident MB</th><th>D3DX loads</th><th>match min</th><th>cause</th><th>game patch log</th></tr>%s</table></div>"
            "<h2>Game patch log events</h2><div class='card wrap'><table>%s</table></div></main><div id=tip></div>"
            "<script id=data type='application/json'>%s</script><script>%s</script></body></html>"
            % (title, CSS, title, H.escape("\n".join(lines)), keys, "".join(out), tr or "<tr><td colspan=9>none</td></tr>", ev or "<tr><td>none</td></tr>",
               json.dumps(data, separators=(",", ":")).replace("</", "<\\/"), JS))
