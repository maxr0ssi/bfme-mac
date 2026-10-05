#!/usr/bin/env python3
"""callstacks.py - inclusive profile and call tree from eipsample's stack scan ("R" lines).

  python3 tools/callstacks.py logs/battle-X/eipsample-main.txt --exe build/rotwk-re/disk.exe \
      --funcs build/rotwk-re/funcs.txt [--names build/rotwk-re/names.txt ...] [--root 0x449cf8 ...]

eipsample keeps every stack dword that follows a CALL into the exe; some are stale (left in
uninitialised locals). Per sample this keeps the longest chain that links up: the call at each
kept return site must target the function holding the next-inner frame (directly, through a
tail jump, or indirectly when that function's address is taken), starting from the function
holding EIP. funcs.txt (F start [d] / T src dst / I thunk) comes from build/rotwk-re/funcs.py.
Reports: chain coverage, top functions by inclusive and self time, and a call tree under each root.
"""
import argparse, bisect, collections, re, struct, sys


def load_text(path):
    b = open(path, 'rb').read()
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    nsec = struct.unpack_from('<H', b, pe + 6)[0]
    optsz = struct.unpack_from('<H', b, pe + 20)[0]
    base = struct.unpack_from('<I', b, pe + 24 + 28)[0]
    sh = pe + 24 + optsz
    for i in range(nsec):
        vsz, va, rsz, raw = struct.unpack_from('<IIII', b, sh + 40 * i + 8)
        ch = struct.unpack_from('<I', b, sh + 40 * i + 36)[0]
        if ch & 0x20000000:
            return base + va, b[raw:raw + min(vsz, rsz)]
    sys.exit('no code section in ' + path)


class Chainer:
    """Function starts, tail jumps and call-site decoding for one exe, and the stack-chain rule above.
    Used by main() and by tools/monitor_stalls.py (the session report's stall histograms)."""
    EXT = -1

    def __init__(self, lo, code, starts, taken=(), thunks=(), tails=None):
        self.lo, self.code, self.hi = lo, code, lo + len(code)
        self.starts, self.taken, self.thunks = sorted(starts), set(taken), set(thunks)
        self.tails = tails or collections.defaultdict(set)
        self.reach_cache, self.site = {}, {}

    @classmethod
    def from_files(cls, exe, funcs):
        lo, code = load_text(exe)
        starts, taken, thunks, tails = [], set(), set(), collections.defaultdict(set)
        for line in open(funcs):
            f = line.split()
            if not f: continue
            if f[0] == 'F':
                starts.append(int(f[1], 16))
                if len(f) > 2: taken.add(starts[-1])
            elif f[0] == 'T': tails[int(f[1], 16)].add(int(f[2], 16))
            elif f[0] == 'I': thunks.add(int(f[1], 16))
        return cls(lo, code, starts, taken, thunks, tails)

    def fof(self, x):
        i = bisect.bisect_right(self.starts, x) - 1
        return self.starts[i] if i >= 0 else x   # before any known start: the address stands for itself

    def reach(self, t, depth=3):   # t plus the functions it tail-jumps to
        if t not in self.reach_cache:
            out, fr = {t}, {t}
            for _ in range(depth):
                fr = {d for s in fr for d in self.tails.get(s, ())} - out
                out |= fr
            self.reach_cache[t] = out
        return self.reach_cache[t]

    def decode(self, r):           # (direct target or None, indirect form possible)
        if r in self.site: return self.site[r]
        o = r - self.lo; d = None; ind = False; code = self.code
        if 5 <= o <= len(code) and code[o - 5] == 0xE8:
            t = (r + struct.unpack_from('<i', code, o - 4)[0]) & 0xffffffff
            if self.lo <= t < self.hi: d = t
        for n in (2, 3, 4, 6, 7):
            if n <= o <= len(code) and code[o - n] == 0xFF and (code[o - n + 1] & 0x38) == 0x10: ind = True
        self.site[r] = (d, ind)
        return d, ind

    def link(self, callee, r):     # can the call before return address r have entered callee?
        d, ind = self.decode(r)
        if d is not None:
            if d in self.thunks: return callee == self.EXT
            if callee != self.EXT and callee in self.reach(d): return True
        return ind and (callee == self.EXT or callee in self.taken)

    def chain(self, eip, rets):
        """(callers outermost first, leaf function or EXT, innermost caller linked to the leaf);
        rets: return addresses into the exe, nearest ESP (innermost) first"""
        lo, hi, fof, link = self.lo, self.hi, self.fof, self.link
        rets = [r for r in rets if lo <= r < hi]
        leaf = fof(eip) if lo <= eip < hi else self.EXT
        # score = links verified; any site may start a chain (a tail call or a missed function
        # start can hide the leaf's caller), a start that links to the leaf scores 1
        k = len(rets); best = [0] * k; prev = [-1] * k
        for j in range(k):
            best[j] = 1 if link(leaf, rets[j]) else 0
            for i in range(j):
                if best[i] + 1 > best[j] and link(fof(rets[i] - 1), rets[j]):
                    best[j] = best[i] + 1; prev[j] = i
        chain, linked = [], True
        if k:
            j = max(range(k), key=lambda x: (best[x], x))
            if best[j] == 0: j = -1
            inner = j
            while j >= 0: chain.append(fof(rets[j] - 1)); inner = j; j = prev[j]
            if chain and not link(leaf, rets[inner]): linked = False
        return chain, leaf, linked


def load_names(paths):
    names = {}
    for nf in paths:
        for line in open(nf):
            f = line.split(None, 1)
            if len(f) == 2 and not line.startswith('#'): names[int(f[0], 16)] = f[1].strip()
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('profile'); ap.add_argument('--exe', required=True); ap.add_argument('--funcs', required=True)
    ap.add_argument('--names', action='append', default=[], help='"addr name" files (repeatable)')
    ap.add_argument('--root', action='append', default=[])
    ap.add_argument('--top', type=int, default=40); ap.add_argument('--min', type=float, default=0.5,
                    help='prune call-tree nodes below this %% of all samples')
    ap.add_argument('--depth', type=int, default=14, help='tree depth; deeper frames fold into the last node')
    a = ap.parse_args()

    ch = Chainer.from_files(a.exe, a.funcs)
    lo, hi, EXT = ch.lo, ch.hi, ch.EXT
    names = load_names(a.names)

    mods, samples = [], []
    for line in open(a.profile):
        if line.startswith('R '):
            f = line.split()
            rets = [int(x.split(':')[1], 16) for x in f[3:]]
            samples.append((int(f[1], 16), [r for r in rets if lo <= r < hi]))
        else:
            m = re.match(r'\s+(\S+)\s+base 0x([0-9a-f]+) size 0x([0-9a-f]+)', line)
            if m: mods.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16)))
    if not samples: sys.exit('no R lines: rerun eipsample built with the stack scan')

    def modname(x):
        for n, b, s in mods:
            if b <= x < b + s: return n
        return '<unmapped>'

    def label(f):
        return f if isinstance(f, str) else '%08x %s' % (f, names.get(f, ''))

    N = len(samples)
    unlinked = 0
    stacks = []              # per sample, outermost first; last = leaf function or '[module]'
    for eip, rets in samples:
        chain, leaf, linked = ch.chain(eip, rets)
        unlinked += not linked
        stacks.append(chain + ([leaf] if leaf != EXT else ['[%s]' % modname(eip)]))

    outer = collections.Counter(s[0] for s in stacks)
    print('%d samples; outermost frame of the recovered chains:' % N)
    for f, c in outer.most_common(6): print('  %6.2f%%  %s' % (100 * c / N, label(f)))
    print('mean chain length %.1f frames; innermost caller not linked to the leaf in %.1f%%' % (
        sum(len(s) for s in stacks) / N, 100 * unlinked / N))

    inc, slf, sx = collections.Counter(), collections.Counter(), collections.Counter()
    for s in stacks:
        for f in set(s): inc[f] += 1
        slf[s[-1]] += 1
        ex = [f for f in s if not isinstance(f, str)]
        if ex: sx[ex[-1]] += 1
    print('\n== top functions by inclusive time (self: EIP in it; self+ext: innermost exe frame) ==')
    print('   incl%   self%  self+ext%  function')
    for f, c in inc.most_common(a.top):
        print('  %6.2f  %6.2f  %8.2f   %s' % (100 * c / N, 100 * slf[f] / N, 100 * sx[f] / N, label(f)))

    for rs in a.root:
        root = int(rs, 16)
        sub = [s[s.index(root):] for s in stacks if root in s]
        print('\n== call tree under %s: %.2f%% of samples (incl%%, self%%; nodes >= %.2f%%) ==' % (label(root), 100 * len(sub) / N, a.min))
        tree = {}
        for s in sub:
            node = tree
            for f in s[:a.depth]:
                e = node.setdefault(f, [0, 0, {}]); e[0] += 1
                last = e; node = e[2]
            last[1] += 1
        def show(node, ind):
            for f, (c, own, ch) in sorted(node.items(), key=lambda kv: -kv[1][0]):
                if 100 * c / N < a.min: continue
                print('  %6.2f%% %6.2f%%  %s%s' % (100 * c / N, 100 * own / N, '  ' * ind, label(f)))
                show(ch, ind + 1)
        show(tree, 0)
        fl = collections.Counter()
        for s in sub:
            for f in set(s[1:]): fl[f] += 1
        print('-- functions under it by inclusive time --')
        for f, c in fl.most_common(a.top):
            print('  %6.2f%%  %s' % (100 * c / N, label(f)))


if __name__ == '__main__':
    main()
