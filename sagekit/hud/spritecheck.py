"""Every sprite of EA's movies that samples one of our 2x textures, checked against EA's 1x (stdlib).

For each textured style of the movie's geometry (as the game reads it), the texels its triangles
sample at 1x (the bounding box of the mapped triangles) are compared with ours at 2x, box-filtered
back to 1x:

  alpha     on average within 8 of 255 of EA's (a 2x edge box-filtered back is half a texel softer)
  clear     where EA's alpha is 0 on a texel and its 8 neighbours, ours is 0 (at most 2): a glow,
            an additive flash or a masked button must not grow a visible square round itself
  solid     where EA's is 255 on a texel and its neighbours, ours is at least 250
  header    the texture declares 8 alpha bits (sagekit/hud/tga.py: D3DX drops alpha otherwise)
"""
from . import tga
from .apt import geometry, images, matrices


def _tri_boxes(text, ids):
    """[(image id, (l, t, r, b))] texel boxes (1x) of the styles sampling `ids`."""
    out, cur, pts = [], None, []
    for line in text.splitlines() + ["s end"]:
        line = line.strip()
        if line.startswith("s ") or line == "c":
            if cur and pts:
                img, (a, b, c, d, tx, ty) = cur
                us = [a * x + c * y + tx for x, y in pts]
                vs = [b * x + d * y + ty for x, y in pts]
                out.append((img, (min(us), min(vs), max(us), max(vs))))
            cur, pts = None, []
            m = matrices(line) if line.startswith("s ") else []
            if m and m[0][0] in ids:
                cur = m[0]
        elif line.startswith("t ") and cur:
            v = [float(x) for x in line[2:].split(":")]
            pts += list(zip(v[0::2], v[1::2]))
    return out


def check(apt, movie, ours, say):
    """ours: {texture id: (EA's TGA bytes, our 2x TGA bytes)}. Says one line per texture, and one per
    style that fails; returns the number of styles checked."""
    dec = {}
    for tid, (ea, two) in ours.items():
        say(tga.alpha_bits(two) == 8, "%s texture %d 2x: declares 8 alpha bits (EA's: %d)" % (
            movie, tid, tga.alpha_bits(ea)))
        dec[tid] = (tga.decode(ea), tga.decode(two))
    imgs = images(apt, movie)
    ids = {i for i, t in imgs.items() if t in ours}
    n = 0
    for member, data in sorted(geometry(apt, movie, own=True).items()):
        for img, box in _tri_boxes(data.decode("latin-1"), ids):
            (w, h, ea), (w2, h2, two) = dec[imgs[img]]
            l, t = max(int(box[0]), 0), max(int(box[1]), 0)
            r, b = min(int(box[2] + 1), w), min(int(box[3] + 1), h)
            if r <= l or b <= t:
                continue
            n += 1
            total = cnt = clear = solid = 0
            for y in range(t, b):
                for x in range(l, r):
                    e = ea[(y * w + x) * 4 + 3]
                    i = (2 * y * w2 + 2 * x) * 4 + 3
                    o = (two[i] + two[i + 4] + two[i + 4 * w2] + two[i + 4 * w2 + 4]) / 4
                    total += abs(o - e)
                    cnt += 1
                    near = [ea[(yy * w + xx) * 4 + 3] for yy in range(max(y - 1, 0), min(y + 2, h))
                            for xx in range(max(x - 1, 0), min(x + 2, w))]
                    if max(near) == 0 and o > 2:
                        clear += 1
                    if min(near) == 255 and o < 250:
                        solid += 1
            if total / cnt > 8 or clear or solid:
                say(False, "%s %s image %d, texels %s: alpha off by %.1f on average, %d clear texels "
                    "not clear, %d solid not solid" % (movie, member, img, (l, t, r, b), total / cnt, clear, solid))
    return n
