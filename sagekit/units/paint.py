"""Atlas helpers for unit recipes: palette ramps, ImageMagick, swatch grain, the tiled house mask.

The atlas is 2048 x 1024: the left half EA's character sheet tiled to 1024 x 1024 (4 x 4 for EA's
256-pixel sheets; mesh.keep_uv), the right half 16 swatch tiles of 256 pixels (mesh.uv_for). A
recipe's paint(b) writes it however it likes and returns its path; these are the shared steps.
"""
import subprocess

TRANSPARENT_WHITE = bytes((255, 255, 255, 0))


def magick(*args):
    subprocess.run(["magick", *map(str, args)], check=True)


def raw(path, fmt="rgba"):
    """The image's pixels, 8 bits per channel."""
    return subprocess.check_output(["magick", str(path), "-depth", "8", fmt + ":-"])


def ramp_colour(ramp, value):
    """(r, g, b) floats at `value` (clamped to 0..1) on a palette ramp [(position, (r, g, b))]."""
    value = max(0, min(1, value))
    for (a, ca), (b, cb) in zip(ramp, ramp[1:]):
        if a <= value <= b:
            t = (value - a) / (b - a)
            return [x * (1 - t) + y * t for x, y in zip(ca, cb)]
    raise ValueError(value)


def ramp_bytes(ramp, value):
    return bytes(round(255 * c) for c in ramp_colour(ramp, value))


def crop_rgb(source, box, dest, size=256):
    """A crop (x, y, X, Y in a `size` grid) of an EA sheet, resized to size x size, as raw RGB:
    painted grain to modulate a swatch with."""
    x, y, X, Y = box
    magick(source, "-resize", "%dx%d!" % (size, size), "-crop", "%dx%d+%d+%d" % (X - x, Y - y, x, y), "+repage",
           "-resize", "%dx%d!" % (size, size), "-depth", "8", "rgb:" + str(dest))
    return dest.read_bytes()


def _mask_rows(mask, size):
    """EA's square mask tiled across a 1024 x 1024 left half; the right half transparent white."""
    if 1024 % size:
        raise ValueError("a %d-pixel mask does not tile 1024 pixels" % size)
    reps, row = 1024 // size, size * 4
    # Repeat raw rows: compositing would clear the RGB of neutral transparent white.
    return b"".join(mask[(y % size) * row:(y % size + 1) * row] * reps + TRANSPARENT_WHITE * 1024
                    for y in range(1024))


def _size(mask):
    size = int(round((len(mask) // 4) ** .5))
    if size * size * 4 != len(mask):
        raise ValueError("EA's house mask is not square")
    return size


def house_mask(source, dest):
    """Our house-colour mask (2048 x 1024 TGA): EA's mask exactly where EA's sheet repeats, and
    neutral (transparent white) under the swatches, so our new pieces take no player colour."""
    mask = raw(source)
    rgba = dest.with_name("mask.rgba")
    rgba.write_bytes(_mask_rows(mask, _size(mask)))
    magick("-size", "2048x1024", "-depth", "8", "rgba:" + str(rgba), dest)


def check_mask(source, built):
    mask, original = raw(built), raw(source)
    assert len(mask) == 2048 * 1024 * 4, "house mask is not 2048 x 1024"
    assert mask == _mask_rows(original, _size(original)), "house mask is not EA's, tiled"
