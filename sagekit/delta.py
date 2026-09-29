"""Copy/insert deltas: a file rebuilt from EA's files on the player's machine plus our own bytes.

    delta = b"SKD1" instruction*
    instruction = varint h, then
        h & 1 == 0: insert (h >> 1) bytes, which follow (ours)
        h & 1 == 1: copy (h >> 1) bytes from source s at offset o (varints s, o follow)

`encode` copies every run of BLOCK or more bytes it finds in a source (every shared run of
2*BLOCK-1 bytes is found; it extends each hit both ways), and inserts the rest. `shared_runs`
checks the inserted bytes independently: the longest run of them that any source also holds, at
any offset (every such run of WINDOW*2-1 bytes or more is found). Standard library only.
"""
MAGIC = b"SKD1"
BLOCK = 32
WINDOW = 64


def _varint(n):
    out = bytearray()
    while True:
        b, n = n & 0x7F, n >> 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _read_varint(d, p):
    n = shift = 0
    while True:
        b = d[p]
        p += 1
        n |= (b & 0x7F) << shift
        shift += 7
        if not b & 0x80:
            return n, p


def _forward(a, i, b, j):
    """Length of the common run a[i:], b[j:]."""
    n, k, step = min(len(a) - i, len(b) - j), 0, 4096
    while k < n:
        m = min(step, n - k)
        if a[i + k:i + k + m] == b[j + k:j + k + m]:
            k += m
            step = min(step * 2, 1 << 20)
        elif m > 16:
            step = m // 2
        else:
            while k < n and a[i + k] == b[j + k]:
                k += 1
            return k
    return k


def _backward(a, i, b, j, limit):
    """Length of the common run ending before a[i], b[j], at most limit."""
    n, k, step = min(i, j, limit), 0, 256
    while k < n:
        m = min(step, n - k)
        if a[i - k - m:i - k] == b[j - k - m:j - k]:
            k += m
            step *= 2
        elif m > 16:
            step = m // 2
        else:
            while k < n and a[i - k - 1] == b[j - k - 1]:
                k += 1
            return k
    return k


def _index(sources, size, stride, keep=1):
    idx = {}
    for s, src in enumerate(sources):
        for o in range(0, len(src) - size + 1, stride):
            hits = idx.setdefault(src[o:o + size], [])
            if len(hits) < keep:
                hits.append((s, o))
    return idx


def instructions(target, sources):
    """[(None, bytes) insert | (s, o, n) copy] rebuilding target from sources."""
    get, out = _index(sources, BLOCK, BLOCK).get, []
    start = i = 0
    end = len(target) - BLOCK
    while i <= end:
        hit = get(target[i:i + BLOCK])
        if hit is None:
            i += 1
            continue
        s, o = hit[0]
        src = sources[s]
        back = _backward(target, i, src, o, i - start)
        n = back + BLOCK + _forward(target, i + BLOCK, src, o + BLOCK)
        if i - back > start:
            out.append((None, target[start:i - back]))
        out.append((s, o - back, n))
        i = start = i - back + n
    if start < len(target):
        out.append((None, target[start:]))
    return out


def serialize(ops, renumber=None):
    """Delta bytes of instructions (renumber: {old source index: new})."""
    out = [MAGIC]
    for op in ops:
        if op[0] is None:
            out += [_varint(len(op[1]) << 1), op[1]]
        else:
            s, o, n = op
            out += [_varint(n << 1 | 1), _varint(renumber[s] if renumber else s), _varint(o)]
    return b"".join(out)


def encode(target, sources):
    """(delta, indices of the sources it copies from, in its numbering)."""
    ops = instructions(target, sources)
    used = sorted({op[0] for op in ops if op[0] is not None})
    return serialize(ops, {s: n for n, s in enumerate(used)}), used


def walk(delta):
    """Yield (None, memoryview) inserts and (s, o, n) copies."""
    d = memoryview(delta)
    if bytes(d[:4]) != MAGIC:
        raise ValueError("not a delta")
    p = 4
    while p < len(d):
        h, p = _read_varint(d, p)
        n = h >> 1
        if h & 1:
            s, p = _read_varint(d, p)
            o, p = _read_varint(d, p)
            yield s, o, n
        else:
            if p + n > len(d):
                raise ValueError("delta truncated")
            yield None, d[p:p + n]
            p += n


def apply(delta, sources):
    out = []
    for op in walk(delta):
        if op[0] is None:
            out.append(op[1])
            continue
        s, o, n = op
        if s >= len(sources) or o + n > len(sources[s]):
            raise ValueError("delta copies past its source")
        out.append(memoryview(sources[s])[o:o + n])
    return b"".join(out)


def inserted(delta):
    """[bytes] of every insert."""
    return [bytes(op[1]) for op in walk(delta) if op[0] is None]


def shared_runs(runs, sources):
    """(longest run of bytes any of `runs` shares with a source, at any offsets; which run)."""
    idx = _index(sources, WINDOW, WINDOW, keep=4)
    get, best, where = idx.get, 0, None
    for r, run in enumerate(runs):
        for i in range(len(run) - WINDOW + 1):
            for s, o in get(run[i:i + WINDOW], ()):
                src = sources[s]
                n = _backward(run, i, src, o, i) + WINDOW + _forward(run, i + WINDOW, src, o + WINDOW)
                if n > best:
                    best, where = n, r
    return best, where


def selfcheck():
    import os
    import random
    rnd = random.Random(1)
    ea = [os.urandom(50000), bytes(3000) + os.urandom(7000)]
    ours = os.urandom(2000)
    target = ea[0][100:9000] + ours + ea[1][:5000] + ea[0][20000:20100] + ours[:40] + ea[0][40000:]
    d, used = encode(target, ea)
    assert used == [0, 1] and apply(d, ea) == target
    lit = inserted(d)
    assert sum(map(len, lit)) <= 2040 + 2 * BLOCK, sum(map(len, lit))
    assert shared_runs(lit, ea)[0] < 2 * BLOCK
    leak = os.urandom(300) + ea[1][6000:6400] + os.urandom(300)
    assert shared_runs([leak], ea)[0] >= 400
    assert apply(encode(b"", ea)[0], ea) == b"" and apply(encode(ours, [])[0], []) == ours
    for _ in range(200):
        t = bytes(rnd.choice(b"ab") for _ in range(rnd.randrange(300)))
        src = [bytes(rnd.choice(b"ab") for _ in range(rnd.randrange(300)))]
        assert apply(encode(t, src)[0], src) == t
    try:
        apply(serialize([(0, 10, 99)]), [b"short"])
    except ValueError:
        pass
    else:
        raise AssertionError("copy past the source accepted")
    print("PASS: delta round trips, inserts hold no source run, a leaked run is found")


if __name__ == "__main__":
    selfcheck()
