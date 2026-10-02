"""EA's icon pages and ours: extract, compose, write the DDS the way EA's is, and check it.

EA's building pages are 256 x 256 DXT3 or DXT5 with a full mip chain (RotWK's expansion1icons
pages 512 x 512 DXT5, one uncompressed). Ours keeps the page's
format, size and mip count. Every 4 x 4 block of the top level that no rect of ours touches is EA's
bytes exactly; blocks our rects touch come from ImageMagick's DXT5 encoding of the composed page
(a rect off the block grid, like the wall page's 59-pixel buttons, re-encodes the few EA pixels
sharing its edge blocks); the mips are made again from the composed page. ImageMagick writes no
DXT3: for EA's DXT3 pages its blocks keep their colour half (the same in both formats) and their
DXT5 alpha is decoded and stored as DXT3's explicit 4 bits.
"""
import os
import struct
import subprocess
import tempfile

from . import pixels
from .mapped import page_member

HEADER = 128


def extract(g, page, dest):
    """EA's page (the archive's bytes) and its decoded PNG into dest/; returns (dds path, png path)."""
    os.makedirs(dest, exist_ok=True)
    member = page_member(g, page)
    if not member.endswith(".dds"):
        raise SystemExit("%s: a TGA page; only DDS pages are handled" % member)
    dds, png = os.path.join(dest, page + ".dds"), os.path.join(dest, page + ".png")
    data = g.read(member)
    if not os.path.exists(dds) or open(dds, "rb").read() != data:
        with open(dds, "wb") as fh:
            fh.write(data)
        pixels.write(png, *pixels.read(dds))
    return dds, png


def info(data):
    size, flags, h, w, pitch, depth, mips = struct.unpack_from("<7I", data, 4)
    return dict(width=w, height=h, mips=max(mips, 1), fourcc=data[84:88].decode("latin-1"))


def touched(rects, w, h):
    """The top level's blocks (bx, by) any rect covers a pixel of."""
    out = set()
    for l, t, r, b in rects:
        for by in range(t // 4, (b + 3) // 4):
            for bx in range(l // 4, (r + 3) // 4):
                if bx < (w + 3) // 4 and by < (h + 3) // 4:
                    out.add((bx, by))
    return out


def dxt5_alpha(block):
    """The 16 alphas (0..255) of a DXT5 alpha block (8 bytes)."""
    a0, a1 = block[0], block[1]
    if a0 > a1:
        pal = [a0, a1] + [((7 - k) * a0 + k * a1) // 7 for k in range(1, 7)]
    else:
        pal = [a0, a1] + [((5 - k) * a0 + k * a1) // 5 for k in range(1, 5)] + [0, 255]
    bits = int.from_bytes(block[2:8], "little")
    return [pal[(bits >> (3 * i)) & 7] for i in range(16)]


def dxt3_alpha(alphas):
    """A DXT3 alpha block: 16 explicit 4-bit alphas, two to a byte, the first in the low nibble."""
    q = [(a * 15 + 127) // 255 for a in alphas]
    return bytes(q[2 * i] | q[2 * i + 1] << 4 for i in range(8))


def as_dxt3(data):
    """A DXT5 file's blocks (after the header) with DXT3 alpha."""
    out = bytearray(data)
    for k in range(HEADER, len(data), 16):
        out[k:k + 8] = dxt3_alpha(dxt5_alpha(data[k:k + 8]))
    return bytes(out)


RAW = "\0\0\0\0"          # an uncompressed 32-bit page (RotWK's expansion1icons_021)
MASKS = struct.Struct("<4I")


def rgba_order(ours, ea):
    """An uncompressed DDS with red and blue swapped to EA's channel masks (ImageMagick writes BGRA,
    EA's uncompressed pages are RGBA); unchanged when the masks are not each other's swap."""
    r, g, b, a = MASKS.unpack_from(ours, 92)
    if MASKS.unpack_from(ea, 92) != (b, g, r, a):
        return ours
    px = bytearray(ours)
    px[HEADER::4], px[HEADER + 2::4] = ours[HEADER + 2::4], ours[HEADER::4]
    px[76:108] = ea[76:108]
    return bytes(px)


def write(ea_dds, page_png, rects, out):
    """The composed page as EA's format with EA's blocks wherever no rect of ours is."""
    ea = open(ea_dds, "rb").read()
    i = info(ea)
    if i["fourcc"] not in ("DXT3", "DXT5", RAW):
        raise SystemExit("%s: %r pages are not handled" % (ea_dds, i["fourcc"]))
    with tempfile.TemporaryDirectory() as tmp:
        enc = os.path.join(tmp, "page.dds")
        subprocess.check_call([pixels.MAGICK, page_png, "-define", "dds:compression=%s" % ("none" if i["fourcc"] == RAW
                                                                                          else "dxt5"),
                               "-define", "dds:mipmaps=%d" % (i["mips"] - 1), "-define", "dds:cluster-fit=true",
                               "-define", "dds:weight-by-alpha=false", enc])
        ours = open(enc, "rb").read()
    o = info(ours)
    want = "DXT5" if i["fourcc"] != RAW else RAW
    if want == RAW and ours[76:108] != ea[76:108]:
        ours = rgba_order(ours, ea)
    if (o["width"], o["height"], o["mips"], o["fourcc"]) != (i["width"], i["height"], i["mips"], want) \
            or len(ours) != len(ea) or (want == RAW and ours[76:108] != ea[76:108]):
        raise SystemExit("%s: ImageMagick wrote %s, EA's is %s (%d against %d bytes)" % (out, o, i, len(ours), len(ea)))
    data = bytearray(as_dxt3(ours) if i["fourcc"] == "DXT3" else ours)
    data[:HEADER] = ea[:HEADER]                     # EA's header, flags and all
    if i["fourcc"] == RAW:                          # uncompressed: EA's top level, our rects' pixels
        if MASKS.unpack_from(ea, 92) != (0xFF, 0xFF00, 0xFF0000, 0xFF000000):
            raise SystemExit("%s: an uncompressed page not in RGBA order" % ea_dds)
        w = i["width"]
        top = (w, i["height"], bytes(ea[HEADER:HEADER + w * i["height"] * 4]))
        page = pixels.read(page_png)
        for r in rects:
            top = pixels.paste(top, r, pixels.crop(page, r))
        data[HEADER:HEADER + len(top[2])] = top[2]
    else:
        bw = (i["width"] + 3) // 4
        mine = touched(rects, i["width"], i["height"])
        for by in range((i["height"] + 3) // 4):
            for bx in range(bw):
                if (bx, by) not in mine:
                    k = HEADER + (by * bw + bx) * 16
                    data[k:k + 16] = ea[k:k + 16]
    with open(out, "wb") as fh:
        fh.write(bytes(data))
    return out


def check(ea_dds, ours_dds, intended_png, rects):
    """Problems (strings) with a page of ours: the format, size and mips must be EA's; the top
    level outside our rects EA's (exactly, except the pixels sharing a block with a rect, which may
    move by DXT's error where they show), inside them the intended pixels within DXT's error on
    average; the alpha inside each rect EA's within DXT3's 4-bit step."""
    ea, ours = open(ea_dds, "rb").read(), open(ours_dds, "rb").read()
    probs = []
    if info(ea) != info(ours) or len(ea) != len(ours):
        probs.append("format %s (%d bytes), EA's %s (%d bytes)" % (info(ours), len(ours), info(ea), len(ea)))
    a, b, want = pixels.read(ea_dds), pixels.read(ours_dds), pixels.read(intended_png)
    w, h = a[0], a[1]
    near = [(bx * 4, by * 4, bx * 4 + 4, by * 4 + 4) for bx, by in touched(rects, w, h)]
    n, big, _ = pixels.differ(a, b, outside=near)
    if n:
        probs.append("%d pixels outside our rects differ from EA's (up to %d)" % (n, big))
    n, big, _ = pixels.differ(a, b, outside=rects, visible=True)
    if big > 96:                                # (an EA icon a pixel beside ours, off the block grid)
        probs.append("visible pixels sharing a block with our rects moved by up to %d" % big)
    for r in rects:
        _, big, mean = pixels.differ(want, b, rect=r, visible=True)
        if mean > 10:
            probs.append("rect %s: the DXT encoding is off the intended pixels by %.1f on average" % (r, mean))
        ea_a, our_a = pixels.crop(a, r)[2][3::4], pixels.crop(b, r)[2][3::4]
        worst = max(abs(x - y) for x, y in zip(ea_a, our_a))
        if worst > 20:
            probs.append("rect %s: alpha off EA's by up to %d" % (r, worst))
    return probs
