"""Material masks of an atlas (the upscaled original sheet): colour rules plus the Atlas's hint
rectangles where colour alone is ambiguous.

compute() returns nine masks in a fixed order, three per baked image:
    mask1 = (bronze, gold, wood)   mask2 = (band ground, inlay/glyph, iron)   mask3 = (rock, plain stone, tiles)
Hint names an Atlas may declare (upscale pixels, y down): rune, tri (frieze bands), hex (hexagon
chain), grille, rock, tiles, strap (iron straps over wood), stone (plain wall stone whose painted
brown grime is not metal).
"""
import numpy as np

from .fields import hsv, roll_blur, smooth

NAMES = ("bronze", "gold", "wood", "ground", "glyph", "iron", "rock", "plain", "tiles")


def rect_mask(atlas, names, h, w):
    m = np.zeros((h, w), bool)
    for n in names:
        for x0, y0, x1, y1 in atlas.mask_hints.get(n, ()):
            m[h - y1:h - y0, x0:x1] = True          # pixel rows are bottom-up
    return m


def compute(a, atlas):
    """a: (h, w, 3) sRGB values, rows bottom-up. Returns the nine masks of NAMES."""
    H, S, Vv = hsv(a)
    h, w = a.shape[:2]
    lum = a @ np.array([0.3, 0.59, 0.11], np.float32)
    band_r = rect_mask(atlas, ["rune", "tri"], h, w)
    hexr = rect_mask(atlas, ["hex"], h, w)
    warm = smooth(S, 0.24, 0.36) * (H > 6) * (H < 64) * smooth(Vv, 0.18, 0.28)
    gold = warm * smooth(S, 0.42, 0.58) * smooth(Vv, 0.5, 0.68) * (H > 34)
    wood = warm * smooth(S, 0.52, 0.64) * (H < 32) * (1 - gold)
    stone = rect_mask(atlas, ["stone"], h, w)
    wood = wood * (1 - stone)
    bronze = np.clip(warm - gold - wood, 0, 1) * (1 - stone)
    teal = smooth(S, 0.08, 0.2) * (H > 120) * (H < 220)
    # glyphs: the light strokes inside the frieze bands; band ground: the rest of the band
    glyph = band_r * smooth(lum, 0.52, 0.66) * (1 - smooth(S, 0.25, 0.4))
    local = roll_blur(lum, 3)
    glyph = np.maximum(glyph, hexr * smooth(local - lum, 0.04, 0.12))   # the hex chain's carved outline
    ground = np.clip(np.maximum(band_r * (1 - glyph), teal * (1 - band_r)), 0, 1)
    grille = rect_mask(atlas, ["grille"], h, w)
    iron = grille * (1 - smooth(lum, 0.28, 0.42))
    iron = np.maximum(iron, np.clip(grille * 0.6 - bronze - gold, 0, 1))
    strap = rect_mask(atlas, ["strap"], h, w) * np.clip((wood + bronze) * 2, 0, 1)
    iron = np.maximum(iron, strap * (1 - gold))
    wood = wood * (1 - strap)
    bronze = bronze * (1 - strap)
    rock = rect_mask(atlas, ["rock"], h, w).astype(np.float32)
    tiles = rect_mask(atlas, ["tiles"], h, w).astype(np.float32)
    for m in (bronze, gold, wood):             # yellowish tiles and brown rock are not metal or wood
        m *= (1 - rock) * (1 - tiles)
    detail = np.abs(lum - local)
    plain = (1 - smooth(roll_blur(detail, 4), 0.025, 0.06)) * (1 - smooth(S, 0.12, 0.22))
    for m in (bronze, gold, wood, ground, glyph, iron):
        plain = plain * (1 - m)
    plain = plain * (1 - rock) * (1 - tiles) * (1 - band_r) * (1 - hexr)
    return [np.clip(roll_blur(x.astype(np.float32), 1), 0, 1) for x in
            (bronze, gold, wood, ground, glyph, iron, rock, plain, tiles)]
