#!/usr/bin/env python3
"""Name RotWK 2.02 code from Open-BFME-2 (a byte-exact C++ rebuild of BFME2 1.06's game.dat).

  python3 tools/obfme_map.py build              # -> build/ext/rotwk_map.tsv (~2 min)
  python3 tools/obfme_map.py 0x6e8ce6 0x62e4e8  # what is this RotWK address?
  python3 tools/obfme_map.py --name WorldToCell # where is their function in RotWK?

Reads only build/ext/Open-BFME-2 (git-ignored clone, GPLv3: never copy its code into this repo)
and the installed lotrbfme2ep1.exe. Matching: each of their verified 1.06 bodies is searched for
in RotWK's .text with call/jump targets and absolute addresses masked (they move between builds).
Confidence, best first:
  exact   unique place, every unmasked byte identical
  near    same length, at most 5 % of the unmasked bytes differ (a struct offset or constant moved)
  call    found through a matched caller: the same call instruction in both builds targets it
  dup:N   identical body at N RotWK addresses (small accessors); each is listed
A lookup with no row in the map searches the 1.06 game.dat for the RotWK function's own bytes and
reports the 1.06 address (their docs and Ghidra exports use 1.06 addresses), the mapped functions
around it (a translation unit is contiguous, so neighbours suggest the source file) and the mapped
functions it calls."""
import bisect, csv, os, re, struct, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, 'build', 'ext', 'Open-BFME-2')
MAP = os.path.join(ROOT, 'build', 'ext', 'rotwk_map.tsv')
B106 = os.path.join(EXT, 'baselines', 'bfme2', 'workshop-vanilla-1.06', 'files', 'game.dat')
FUNCS = os.path.join(ROOT, 'build', 'rotwk-re', 'funcs.txt')   # RotWK function starts, if present


def rotwk_exe():
    pre = os.environ.get('WINEPREFIX') or os.path.join(ROOT, 'prefixes', 'w10')
    return os.path.join(pre, 'drive_c', 'Program Files (x86)', 'Electronic Arts', 'RotWK',
                        'lotrbfme2ep1.exe')


class PE:
    def __init__(self, path):
        d = self.data = open(path, 'rb').read()
        pe = struct.unpack_from('<I', d, 0x3c)[0]
        nsec = struct.unpack_from('<H', d, pe + 6)[0]
        opt = pe + 24
        self.base = struct.unpack_from('<I', d, opt + 28)[0]
        self.size_img = struct.unpack_from('<I', d, opt + 56)[0]
        first = opt + struct.unpack_from('<H', d, pe + 20)[0]
        self.secs = []
        for i in range(nsec):
            o = first + 40 * i
            vsz, va, rsz, rp = struct.unpack_from('<IIII', d, o + 8)
            self.secs.append((d[o:o + 8].rstrip(b'\0'), va, vsz, rp, rsz))
        t = next(s for s in self.secs if s[0] == b'.text')
        self.t0 = self.base + t[1]
        self.t1 = self.t0 + t[2]
        self.text = d[t[3]:t[3] + min(t[2], t[4])]

    def in_image(self, v):
        return self.base <= v < self.base + self.size_img

    def in_text(self, v):
        return self.t0 <= v < self.t1

    def code(self, va, n):
        o = va - self.t0
        return self.text[o:o + n] if 0 <= o and o + n <= len(self.text) else None


def fields(body, va, img):
    """{offset: 'rel'|'abs'} of the 4-byte address fields of a body at va (masked when matching)."""
    n, f, cl, i = len(body), {}, bytearray(len(body)), 0
    while i < n:
        b = body[i]
        o = 1 if b in (0xE8, 0xE9) else 2 if (b == 0x0F and i + 1 < n and 0x80 <= body[i + 1] <= 0x8F) else 0
        if o and i + o + 4 <= n:
            t = (va + i + o + 4 + struct.unpack_from('<i', body, i + o)[0]) & 0xffffffff
            if img.in_text(t):
                f[i + o] = 'rel'
                cl[i + o:i + o + 4] = b'\1\1\1\1'
                i += o + 4
                continue
        i += 1
    for i in range(max(0, n - 3)):
        if not any(cl[i:i + 4]) and img.in_image(struct.unpack_from('<I', body, i)[0]):
            f[i] = 'abs'
            cl[i:i + 4] = b'\1\1\1\1'
    return f, bytes(cl)


def runs(mask):
    r, s = [], None
    for i, m in enumerate(mask):
        if not m and s is None:
            s = i
        elif m and s is not None:
            r.append((s, i - s))
            s = None
    if s is not None:
        r.append((s, len(mask) - s))
    return sorted(r, key=lambda x: -x[1])


def search(body, mask, hay, cap=64):
    """(identical windows, best (diff, window) among the anchors) of body in hay, masked."""
    rs = runs(mask)
    if not rs or rs[0][1] < 6:
        return None, None
    same, best, size = [], None, len(body)
    for off, ln in rs[:3]:
        if ln < 6:
            break
        needle, p, k = body[off:off + min(ln, 48)], hay.find(body[off:off + min(ln, 48)]), 0
        while p >= 0 and k < cap:
            st = p - off
            if 0 <= st and st + size <= len(hay):
                w = hay[st:st + size]
                d = sum(1 for x, y, m in zip(body, w, mask) if not m and x != y)
                if d == 0 and st not in same:
                    same.append(st)
                if best is None or d < best[0]:
                    best = (d, st)
            p, k = hay.find(needle, p + 1), k + 1
        if same:
            break
    return same, best


PLACEHOLDER = re.compile(r'Rva[0-9A-F]{6}|FUN_|Unk\d|Address|Bfme\w*\d{3,}|Conv\d{3,}', re.I)


OPS = {'?0': '', '?1': '~', '?2': 'operator new', '?3': 'operator delete', '?4': 'operator=',
       '?8': 'operator==', '?9': 'operator!=', '?A': 'operator[]', '?R': 'operator()',
       '?_G': 'scalar deleting dtor', '?_E': 'vector deleting dtor', '?_7': 'vftable'}


def pretty(mangled):
    """Class::method from an MSVC mangled name (enough to read; the raw name stays in the map)."""
    m = re.match(r'\?(\?_?[0-9A-Z]|)([^@]*)@((?:[^@]+@)*)@', mangled)
    if not m or mangled.startswith('$$'):
        return mangled.lstrip('_')
    op, name, scope = m.groups()
    t = re.match(r'\?(\w+)@\?\$(\w+)@', mangled)
    if t and not op:
        return f'{t.group(2)}<>::{t.group(1)}'
    parts = [p for p in scope.split('@') if p and not p[0] in '?$' and not p[0].isdigit()][::-1]
    if op:                                      # ctor, dtor, operator: the name is the class
        cls = name[2:] + '<>' if name.startswith('?$') else name
        meth = OPS.get(op, 'operator' + op[1:])
        meth = meth + cls if op in ('?0', '?1') else meth
        return '::'.join(parts[-1:] + [cls, meth])
    return '::'.join(parts[-2:] + [name]) if name else '::'.join(parts)


def ledger():
    """{rva106: (name, source, size)} from their functions.csv and symbols.csv."""
    csv.field_size_limit(1 << 30)
    by = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(EXT, 'reverse', 'functions.csv'))):
        try:
            by[int(r['target_rva'], 16)].append((r['name'], r['source'], int(r['target_size'])))
        except ValueError:
            pass
    gh = {}
    for r in csv.DictReader(open(os.path.join(EXT, 'reverse', 'ghidra_functions.csv'))):
        gh[int(r['rva'], 16)] = int(r['size'])
    for r in csv.DictReader(open(os.path.join(EXT, 'reverse', 'symbols.csv'))):
        try:
            a = int(r['address'], 16)
        except ValueError:
            continue
        if a not in by and a in gh:
            by[a].append((r['name'], '', gh[a]))
    out = {}
    for a, rows in by.items():
        def score(r):
            return (bool(PLACEHOLDER.search(r[0])), 'gen_' in r[1], r[1] == '')
        out[a] = min(rows, key=score)
    return out


def build():
    A, B, led = PE(B106), PE(rotwk_exe()), ledger()
    fs = set(starts_rotwk(B))

    def is_start(va):                           # a body can also match inside a larger function
        if fs:
            return va in fs
        p = B.text[va - B.t0 - 3:va - B.t0]
        return p[-1:] in (b'\xcc', b'\x90', b'\xc3') or (p[:1] == b'\xc2' and p[2:] == b'\0')
    hit = {}                                    # rva106 -> (rotwk va, confidence)
    dups = {}
    n = len(led)
    for k, (rva, (name, src, size)) in enumerate(sorted(led.items())):
        if k % 5000 == 0:
            print(f'  {k}/{n}', file=sys.stderr)
        body = A.code(A.base + rva, size)
        if not body or size < 8:
            continue
        f, mask = fields(body, A.base + rva, A)
        same, best = search(body, mask, B.text)
        if same is None:
            continue
        same = [B.t0 + x for x in same] if same else same
        if same and (len(same) > 1 or size < 32):
            same = [x for x in same if is_start(x)]
            if not same:
                continue
        if len(same) == 1:
            hit[rva] = (same[0], 'exact')
        elif same:
            if len(same) <= 8:
                dups[rva] = same
        elif best and best[0] <= max(2, size // 20) and (size >= 64 or is_start(B.t0 + best[1])):
            hit[rva] = (B.t0 + best[1], 'near')
    # call propagation: a matched pair's call/jump at the same offset names the callee in RotWK
    work = list(hit.items())
    while work:
        votes = collections.defaultdict(collections.Counter)
        for rva, (rk, conf) in work:
            size = led[rva][2] if rva in led else 0
            a, b = A.code(A.base + rva, size), B.code(rk, size)
            if not a or not b:
                continue
            fa, mask = fields(a, A.base + rva, A)
            if sum(1 for x, y, m in zip(a, b, mask) if not m and x != y) > max(2, size // 20):
                continue                        # only bodies that line up name their callees
            for off, kind in fa.items():
                if kind != 'rel' or a[off - 1] != b[off - 1]:
                    continue
                ta = (A.base + rva + off + 4 + struct.unpack_from('<i', a, off)[0]) & 0xffffffff
                tb = (rk + off + 4 + struct.unpack_from('<i', b, off)[0]) & 0xffffffff
                if B.in_text(tb):
                    votes[ta - A.base][tb] += 1
        work = []
        for rva, v in votes.items():
            if rva in hit or rva not in led or len(v) != 1:
                continue
            tb = next(iter(v))
            hit[rva] = (tb, 'exact' if tb in dups.get(rva, ()) else 'call')
            dups.pop(rva, None)
            work.append((rva, hit[rva]))
    rows = []
    for rva, (rk, conf) in hit.items():
        rows.append((rk, conf, rva))
    for rva, l in dups.items():
        rows += [(rk, f'dup:{len(l)}', rva) for rk in l]
    rows.sort()
    with open(MAP, 'w') as fh:
        fh.write('# rotwk_va\tsize\tconfidence\tname\tsource\tva_106\tmangled  (tools/obfme_map.py build)\n')
        for rk, conf, rva in rows:
            name, src, size = led[rva]
            fh.write(f'{rk:#x}\t{size}\t{conf}\t{pretty(name)}\t{src}\t{A.base + rva:#x}\t{name}\n')
    c = collections.Counter(r[1].split(':')[0] for r in rows)
    print(f'{MAP}: {len(rows)} rows from {n} of their functions; ' +
          ', '.join(f'{k} {v}' for k, v in c.most_common()))


RANK = {'exact': 0, 'near': 1, 'call': 2}


def load_map():
    if not os.path.exists(MAP):
        sys.exit(f'no {MAP}: run python3 tools/obfme_map.py build')
    rows = []
    for line in open(MAP):
        if line.startswith('#'):
            continue
        va, size, conf, name, src, v106, mangled = line.rstrip('\n').split('\t')
        rows.append((int(va, 16), int(size), conf, name, src, v106, mangled))
    return rows


def fmt(r, addr=None):
    va, size, conf, name, src, v106, _ = r
    at = f'{va:#x}+{addr - va:#x}' if addr is not None and addr != va else f'{va:#x}'
    path = os.path.join('build/ext/Open-BFME-2', src) if src else '(no source file)'
    return f'{at} [{conf}, {size} B, 1.06 {v106}] {name}\n      {path}{line_of(src, name)}'


def line_of(src, name):
    p = os.path.join(EXT, src)
    short = name.split('::')[-1].lstrip('~')
    if not src or not short or not os.path.isfile(p):
        return ''
    try:
        for i, l in enumerate(open(p, errors='replace'), 1):
            if short + '(' in l and not l.rstrip().endswith(';'):
                return f':{i}'
    except OSError:
        pass
    return ''


def starts_rotwk(B):
    if os.path.exists(FUNCS):
        return sorted(int(l.split()[1], 16) for l in open(FUNCS) if l.startswith('F '))
    return []


def lookup(addrs):
    rows = load_map()
    vas = [r[0] for r in rows]
    A = B = fs = None
    for addr in addrs:
        i = bisect.bisect_right(vas, addr)
        cands = [r for r in rows[max(0, i - 40):i] if r[0] <= addr < r[0] + r[1]]
        print(f'{addr:#x}:')
        if cands:
            cands.sort(key=lambda r: (RANK.get(r[2], 3), -r[0]))
            for r in cands[:3]:
                print('  ' + fmt(r, addr))
            continue
        if A is None:
            A, B = PE(B106), PE(rotwk_exe())
            fs = starts_rotwk(B)
        print('  not in the map (their rebuild has no verified body for it yet)')
        j = bisect.bisect_right(fs, addr) - 1
        if j >= 0 and j + 1 < len(fs):
            s, e = fs[j], fs[j + 1]
            body = B.code(s, e - s)
            f, mask = fields(body, s, B)
            same, best = search(body, mask, A.text, cap=16)
            hits = [A.t0 + x for x in same] if same else []
            if not hits and best and best[0] <= max(2, len(body) // 20):
                hits = [A.t0 + best[1]]
            where = ', '.join(f'{h:#x}' for h in hits[:3]) if hits else 'none (changed or new in RotWK)'
            print(f'  function {s:#x} ({e - s} B); same code in 1.06 at {where}')
            callees = []
            for off, kind in f.items():
                if kind == 'rel' and body[off - 1] == 0xE8:
                    t = (s + off + 4 + struct.unpack_from('<i', body, off)[0]) & 0xffffffff
                    k = bisect.bisect_left(vas, t)
                    if k < len(rows) and rows[k][0] == t and rows[k][3] not in callees:
                        callees.append(rows[k][3])
            if callees:
                print('  calls (mapped): ' + ', '.join(callees[:12]) + (' ...' if len(callees) > 12 else ''))
        for lab, r in (('before', rows[i - 1] if i else None), ('after', rows[i] if i < len(rows) else None)):
            if r:
                print(f'  mapped {lab}: {r[0]:#x} {r[3]}  <{r[4] or "-"}>')


def by_name(pat):
    rx = re.compile(pat, re.I)
    n = 0
    for r in load_map():
        if rx.search(r[3]) or rx.search(r[6]) or rx.search(r[4]):
            print('  ' + fmt(r))
            n += 1
            if n >= 60:
                print('  ... (first 60)')
                break


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return
    if not os.path.isdir(EXT):
        sys.exit(f'no {EXT}: git clone --depth 1 https://github.com/Open-BFME/Open-BFME-2 {EXT}')
    if argv[0] == 'build':
        build()
    elif argv[0] == '--name':
        by_name(argv[1])
    else:
        lookup([int(a, 16) for a in argv])


if __name__ == '__main__':
    main(sys.argv[1:])
