#!/usr/bin/env python3
"""fpsym.py - inclusive/self profile by function from tools/fpsample.c output.

  python3 tools/fpsym.py fp.txt wined3d.dll=wine/build-X/dlls/wined3d/i386-windows/wined3d.dll \
      d3d9.dll=... d3dx9_27-x.dll=... [--top N] [--children FUNC]... [--parents FUNC]... [--exclude-wait]

Each module=path names the -g build that was loaded (the -x suffix a renamed copy got is dropped from the
printed names); frames are symbolized with i686-w64-mingw32-addr2line (return addresses minus one).
Modules without a path are reported as module+page. --exclude-wait (needs d3d9.dll=) drops samples with a Present frame
(the application thread waiting for the render thread). --children FUNC splits FUNC's inclusive time by
its callees, --parents FUNC by its callers. A frameless leaf hides its caller, so a callee can show up
one level too high; totals per function are right."""
import collections, re, struct, subprocess, sys
a = sys.argv[1:]; rep = a.pop(0); paths = {}; top = 50; kids = []; pars = []; exw = False
while a:
    x = a.pop(0)
    if x == '--top': top = int(a.pop(0))
    elif x == '--children': kids.append(a.pop(0))
    elif x == '--parents': pars.append(a.pop(0))
    elif x == '--exclude-wait': exw = True
    elif '=' in x: k, v = x.split('=', 1); paths[k.lower()] = v
mods, samples = [], []
for l in open(rep, errors='replace'):
    f = l.split()
    if not f: continue
    if f[0] == 'M': mods.append((f[1].lower(), int(f[2], 16), int(f[3], 16)))
    elif f[0] == 'S': samples.append([int(x, 16) for x in f[1:]])
def modof(x):
    for n, b, s in mods:
        if b <= x < b + s: return n, x - b
    return None, x
def ib(p):
    b = open(p, 'rb').read(4096); pe = struct.unpack_from('<I', b, 0x3c)[0]; return struct.unpack_from('<I', b, pe + 52)[0]
need = collections.defaultdict(set)
for s in samples:
    for i, x in enumerate(s):
        m, r = modof(x if i == 0 else x - 1)
        if m in paths: need[m].add(r)
sym = {}
for m, rs in need.items():
    base = ib(paths[m]); rs = sorted(rs)
    out = subprocess.run(['i686-w64-mingw32-addr2line', '-f', '-e', paths[m]], input='\n'.join('%x' % (base + r) for r in rs),
                         capture_output=True, text=True).stdout.split('\n')
    for i, r in enumerate(rs): sym[(m, r)] = m.split('.')[0].replace('-x', '') + '!' + out[2 * i]
def name(x, leaf):
    m, r = modof(x if leaf else x - 1)
    if m is None: return '?'
    return sym.get((m, r), m + '+%x' % (r & ~0xfff))
incl, selfc, child = collections.Counter(), collections.Counter(), collections.defaultdict(collections.Counter)
par = collections.defaultdict(collections.Counter)
n = 0
for s in samples:
    fr = [name(x, i == 0) for i, x in enumerate(s)]
    if exw and any('Present' in f for f in fr): continue
    n += 1; selfc[fr[0]] += 1
    seen = set()
    for i, f in enumerate(fr):
        if f not in seen: incl[f] += 1; seen.add(f)
        if f in kids and i > 0:
            child[f][fr[i - 1]] += 1
        if f in kids and i == 0: child[f]['<self>'] += 1
        if f in pars and i + 1 < len(fr) and (i == 0 or fr[i - 1] != f): par[f][fr[i + 1]] += 1
print('%d samples%s' % (n, ' (Present excluded)' if exw else ''))
print('\n== inclusive ==')
for f, c in incl.most_common(top): print('  %6.2f%%  %6.2f%% self  %s' % (100.0 * c / n, 100.0 * selfc[f] / n, f))
for k in kids:
    t = sum(child[k].values())
    print('\n== children of %s (%.2f%% incl) ==' % (k, 100.0 * incl[k] / max(n, 1)))
    for f, c in child[k].most_common(25): print('  %6.2f%%  %s' % (100.0 * c / n, f))
for k in pars:
    print('\n== callers of %s (%.2f%% incl) ==' % (k, 100.0 * incl[k] / max(n, 1)))
    for f, c in par[k].most_common(20): print('  %6.2f%%  %s' % (100.0 * c / n, f))
