"""Pixels for the icon steps, through ImageMagick (the system python3 has no numpy; this module needs
none). An image is (width, height, RGBA bytes, rows top-down)."""
import struct
import subprocess

MAGICK = "magick"


def raw_dds(path):
    """An uncompressed 32-bit DDS's top level as RGBA by its channel masks, or None for any other
    file (ImageMagick reads such a page as BGRA whatever its masks say: RotWK's RGBA pages came out
    with red and blue swapped)."""
    with open(path, "rb") as fh:
        head = fh.read(128)
        if head[:4] != b"DDS " or head[84:88] != b"\0\0\0\0" or struct.unpack_from("<I", head, 88)[0] != 32:
            return None
        h, w = struct.unpack_from("<2I", head, 12)
        px = fh.read(w * h * 4)
    masks = struct.unpack_from("<4I", head, 92)
    shift = [m.bit_length() // 8 - 1 if m else 3 for m in masks]
    out = bytearray(len(px))
    for c, k in enumerate(shift):
        out[c::4] = px[k::4]
    if not masks[3]:
        out[3::4] = b"\xff" * (w * h)
    return w, h, bytes(out)


def read(path):
    if path.lower().endswith(".dds"):
        img = raw_dds(path)
        if img:
            return img
    w, h = (int(x) for x in subprocess.check_output([MAGICK, "identify", "-format", "%w %h", path + "[0]"]).split())
    data = subprocess.check_output([MAGICK, path + "[0]", "-depth", "8", "RGBA:-"])
    if len(data) != w * h * 4:
        raise ValueError("%s: %d bytes for %dx%d RGBA" % (path, len(data), w, h))
    return w, h, data


def write(path, w, h, data):
    subprocess.run([MAGICK, "-size", "%dx%d" % (w, h), "-depth", "8", "RGBA:-", path], input=data, check=True)


def crop(img, rect):
    """The pixels of rect (left, top, right, bottom; right and bottom exclusive)."""
    w, _, data = img
    l, t, r, b = rect
    return r - l, b - t, b"".join(data[(y * w + l) * 4:(y * w + r) * 4] for y in range(t, b))


def paste(img, rect, part):
    """img with part's pixels at rect (sizes must agree)."""
    w, h, data = img
    pw, ph, pd = part
    l, t, r, b = rect
    if (r - l, b - t) != (pw, ph):
        raise ValueError("%dx%d into a %dx%d rect" % (pw, ph, r - l, b - t))
    out = bytearray(data)
    for y in range(ph):
        out[((t + y) * w + l) * 4:((t + y) * w + r) * 4] = pd[y * pw * 4:(y + 1) * pw * 4]
    return w, h, bytes(out)


def differ(a, b, rect=None, outside=None, visible=False):
    """Pixels whose RGBA differ between images a and b (same size): inside rect, or outside every
    rect of `outside` (visible: only where a's alpha is above 0). Returns (count, largest channel
    difference, mean channel difference over the pixels looked at)."""
    w, h, da = a
    db = b[2]
    n = big = total = seen = 0
    for y in range(h):
        for x in range(w):
            if rect and not (rect[0] <= x < rect[2] and rect[1] <= y < rect[3]):
                continue
            if outside and any(r[0] <= x < r[2] and r[1] <= y < r[3] for r in outside):
                continue
            i = (y * w + x) * 4
            if visible and not da[i + 3]:
                continue
            diffs = [abs(da[i + k] - db[i + k]) for k in range(4)]
            seen += 1
            total += sum(diffs[:3])
            d = max(diffs)
            if d:
                n += 1
                big = max(big, d)
    return n, big, total / max(seen * 3, 1)
