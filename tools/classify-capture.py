#!/usr/bin/env python3
"""Classify a screenshot of the RotWK or BFME2 game window.

Usage: classify-capture.py capture.png [--json]

Prints one word on stdout: MAP, LOADING, HANGBG, MOVIE, MENU or UNKNOWN, followed by the
metrics when --json is given. Uses only `sips` (macOS) and the Python stdlib: the PNG is
downscaled to a small 24/32-bit BMP and the raw pixels are read from that.

Screens (as seen at 1512x982 points, 2x Retina capture):
  LOADING  RotWK: dark blue-black rune-ring background, low colour saturation, a bright cyan
           "LOADING" banner top-centre and a player/progress table in the middle. BFME2 uses the
           same layout on a green background, so it is matched on the two thumbnails instead.
  HANGBG   the same dark background but the loading UI has vanished (the hang we bisect).
  MAP      the rendered 3D map: green/brown terrain, HUD (palantir, command bar) at the bottom,
           much higher share of warm/green pixels and higher brightness.
  MENU     main menu / skirmish setup: bright, colourful key art, blue UI buttons.
"""
import json
import os
import struct
import subprocess
import sys
import tempfile

W, H = 378, 245  # downscaled size (1/8 of the 3024x1964 capture)


def load_pixels(png):
    tmp = tempfile.NamedTemporaryFile(suffix=".bmp", delete=False)
    tmp.close()
    try:
        subprocess.run(["sips", "-s", "format", "bmp", "-z", str(H), str(W), png, "--out", tmp.name],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        data = open(tmp.name, "rb").read()
    finally:
        os.unlink(tmp.name)
    off = struct.unpack_from("<I", data, 10)[0]
    w, h = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]
    if bpp not in (24, 32):
        raise SystemExit("unexpected bmp depth %d" % bpp)
    bypp = bpp // 8
    flip = h > 0
    h = abs(h)
    stride = (w * bypp + 3) & ~3
    rows = []
    for y in range(h):
        base = off + y * stride
        row = [(data[base + x * bypp + 2], data[base + x * bypp + 1], data[base + x * bypp])
               for x in range(w)]
        rows.append(row)
    if flip:
        rows.reverse()  # BMP bottom-up -> top-down
    return rows


def metrics(rows):
    h = len(rows)
    w = len(rows[0])
    n = 0
    lum_sum = 0.0
    lum_sq = 0.0
    warm = 0       # green/brown terrain-like pixels: red or green clearly above blue
    blueish = 0    # blue-dominant pixels (loading background, rune ring)
    dark = 0       # very dark pixels
    sat_sum = 0.0
    for y in range(h):
        for r, g, b in rows[y]:
            n += 1
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            lum_sum += lum
            lum_sq += lum * lum
            mx, mn = max(r, g, b), min(r, g, b)
            sat_sum += (mx - mn) / mx if mx else 0.0
            if (r > b + 18 or g > b + 18) and mx > 40:
                warm += 1
            if b >= r and b >= g:
                blueish += 1
            if lum < 28:
                dark += 1
    mean = lum_sum / n
    std = (lum_sq / n - mean * mean) ** 0.5
    # bottom HUD band (bottom 14% of the screen): in-game HUD is busy and warm-toned
    y0 = int(h * 0.86)
    hud_n = 0
    hud_warm = 0
    hud_lum = 0.0
    for y in range(y0, h):
        for r, g, b in rows[y]:
            hud_n += 1
            hud_lum += 0.299 * r + 0.587 * g + 0.114 * b
            if (r > b + 18 or g > b + 18) and max(r, g, b) > 40:
                hud_warm += 1
    # Loading-screen thumbnails: map picture (left) and parchment minimap (right). Both are
    # warm-toned; when the loading UI vanishes (the hang) these regions are dark blue.
    def warm_frac(x0, x1, y0, y1):
        px = [p for y in range(int(h * y0), int(h * y1)) for p in rows[y][int(w * x0):int(w * x1)]]
        k = sum(1 for r, g, b in px if (r > b + 18 or g > b + 18) and max(r, g, b) > 40)
        return k / len(px)
    left_thumb = warm_frac(0.18, 0.31, 0.30, 0.46)
    right_thumb = warm_frac(0.70, 0.82, 0.30, 0.46)
    return {
        "mean_lum": round(mean, 1),
        "std_lum": round(std, 1),
        "sat": round(sat_sum / n, 3),
        "warm_frac": round(warm / n, 3),
        "blue_frac": round(blueish / n, 3),
        "dark_frac": round(dark / n, 3),
        "hud_warm_frac": round(hud_warm / hud_n, 3),
        "hud_mean_lum": round(hud_lum / hud_n, 1),
        "left_thumb_warm": round(left_thumb, 3),
        "right_thumb_warm": round(right_thumb, 3),
    }


def classify(m):
    # Loading / hang background: blue-dominant, dark, few warm pixels (RotWK's rune-ring screen).
    darkbg = m["blue_frac"] > 0.75 and m["warm_frac"] < 0.12 and m["mean_lum"] < 45
    if darkbg:
        ui = m["right_thumb_warm"] > 0.3 or m["left_thumb_warm"] > 0.3
        return "LOADING" if ui else "HANGBG"
    # Rendered map, tested BEFORE the BFME2 loading rule (a map's thumbnail regions are terrain
    # and pass that rule too). The discriminator is the HUD strip: the command bar and palantir
    # are warm-toned regardless of the map's lighting (night, snow and grey terrain would fail a
    # scene-colour test), and a live 3D view has few dark pixels. Measured: BFME2 map hud 0.75 /
    # dark 0.05, RotWK map hud 0.90 / dark 0.05; BFME2's Create-a-Hero and skirmish-setup menus
    # hud 0.26 / dark 0.51; both loading screens hud <= 0.09.
    if m["hud_warm_frac"] > 0.30 and m["dark_frac"] < 0.40:
        return "MAP"
    # BFME2's loading screen has RotWK's layout on a green, not blue, background, so the darkbg
    # test misses it. Both thumbnails (map photo left, parchment minimap right) are warm (0.43 /
    # 0.86 measured) and the HUD strip is not; on a hang both thumbnails go to 0.0.
    if m["left_thumb_warm"] > 0.35 and m["right_thumb_warm"] > 0.35 and m["hud_warm_frac"] < 0.20:
        return "LOADING"
    if m["mean_lum"] > 60 and m["sat"] > 0.2:
        return "MENU"
    if m["mean_lum"] > 40:
        return "MOVIE"
    return "UNKNOWN"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    rows = load_pixels(args[0])
    m = metrics(rows)
    label = classify(m)
    if "--json" in sys.argv:
        print(label, json.dumps(m))
    else:
        print(label)


if __name__ == "__main__":
    main()
