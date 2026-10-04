"""The scenery's flat-sheet paint (sagekit/scenery.py), on Blender's Python (numpy):

    python3.11 -m assets.scenery.paint <culture> <in> <out> <height> <upscaler>

The culture's palette and options are in cultures.py: a faction (its stone ramp on EA's grey,
StoneRecolour, or its own flat-sheet layers, both after a white balance) or "wilderland" (the
Wilderland grade, assets/scenery/style.py). sagekit/paint/sheets.py does the rest: the 4x upscale, the masks, the
layers, EA's size and format."""
import sys

import numpy as np

from assets.neutral.paint import Grade

W = np.array([0.3, 0.59, 0.11], np.float32)


class SheetGrade(Grade):
    """EA's sheet graded as the neutral buildings are: a little more contrast and colour, warm
    highlights. Every motif stays EA's; only the grade changes."""

    def apply(self, col, cv, pal):
        return self.grade(cv.rgb)


def white_balance(rgb, strength=1.0):
    """EA's tinted stone brought to neutral grey: the mean colour cast of the sheet's grey texels
    (low saturation, mid luminance) taken off every texel in proportion to how grey it is, so moss,
    wood and paint keep their colour. A faction's recolour reads a cast as a material of its own
    (Osgiliath's lilac stone as enamel and cloth: blue specks and red blotches on white stone)."""
    lum = (rgb @ W)[..., None]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    grey = (sat < 0.3) & (lum[..., 0] > 0.12) & (lum[..., 0] < 0.88)
    if grey.mean() < 0.05:
        return rgb
    cast = (rgb - lum)[grey].mean(0)
    w = np.clip(1 - sat / 0.45, 0, 1)[..., None]
    return np.clip(rgb - strength * cast * w, 0, 1).astype(np.float32)


class StoneRecolour(Grade):
    """A culture's stone in its faction's stone ramp, everything else EA's own colour graded.
    Stone is told by chroma (saturation x value, or saturation alone in the dark, blurred a little so single texels do not
    speckle): grey and faintly tinted texels take the ramp through the faction's own stone curve
    (`Recolour`'s pivot, gain and mid: Gondor's white is brighter than EA's grey; `spread` more
    contrast than a building's, which has its own baked shade; `detail` a high-pass of EA's
    luminance added back, so mortar and cracks read sharper), coloured ones (moss, ivy, timber,
    thatch, paint) keep EA's hue with the Wilderland grade. No material masks: EA's map sheets
    are painted otherwise than the faction sheets the masks were tuned on. Per culture
    (cultures.py): `stone_hues`, a hue window that is the culture's stone at any chroma
    (Osgiliath's lilac and blue bricks), and `earth_hues`, one kept as EA's even when faint (the
    brown earth and rubble on its ruins, which would otherwise turn to white stone)."""

    def __init__(self, pivot=0.45, gain=1.12, mid=0.47, chroma=(0.05, 0.11), spread=1.25, detail=0.5,
                 stone_hues=None, earth_hues=None, earth_chroma=(0.02, 0.045), contrast=1.12, saturation=1.15):
        super().__init__(contrast=contrast, saturation=saturation, warm=0.03, lift=0.0)
        self.pivot, self.sgain, self.smid, self.chroma = pivot, gain * spread, mid, chroma
        self.detail, self.stone_hues, self.earth_hues, self.earth_chroma = detail, stone_hues, earth_hues, earth_chroma

    def weight(self, rgb):
        """(h, w, 1): how much each texel is the culture's stone."""
        from sagekit.paint.fields import box_blur, hsv, smooth
        H, S, V = hsv(rgb)
        r = max(1, rgb.shape[1] // 512)
        c = box_blur(np.maximum(S * V, 0.45 * S * smooth(V, 0.04, 0.2)).astype(np.float32), r)   # dark leaves
                                                                                                # and timber count
        coloured = smooth(c, *self.chroma)
        if self.stone_hues:
            coloured = coloured * (1 - in_hue(H, *self.stone_hues))
        if self.earth_hues:
            coloured = np.maximum(coloured, in_hue(H, *self.earth_hues) * smooth(c, *self.earth_chroma))
        return box_blur((1 - coloured).astype(np.float32), r)[..., None]

    def apply(self, col, cv, pal):
        from sagekit.paint.fields import box_blur, ramp
        rgb, L = cv.rgb, cv.lum
        w = self.weight(rgb)
        fine = L - box_blur(L.astype(np.float32), 3 * max(1, rgb.shape[1] // 512))   # mortar, cracks: sharpened
        stone = ramp(np.clip((L - self.pivot) * self.sgain + self.smid + self.detail * fine, 0, 1), pal["stone"])
        return w * stone + (1 - w) * self.grade(rgb)


def in_hue(H, h0, h1, soft=8.0):
    from sagekit.paint.fields import smooth
    return smooth(H, h0, h0 + soft) * (1 - smooth(H, h1 - soft, h1))


class CultureStyle:
    """A faction's style for a culture's sheets: its palette and atlas as they are; the white
    balance first (sagekit/paint/sheets.py `sheet_prepare`); then StoneRecolour in its palette
    (mode "stone", with the faction's Recolour curve when its first sheet layer has one) or the
    faction's own flat-sheet layers (mode "faction")."""

    def __init__(self, base, opts):
        self.base, self.opts = base, dict(opts)

    def __getattr__(self, name):
        return getattr(self.base, name)

    @staticmethod
    def sheet_prepare(rgb):
        return white_balance(rgb)

    def sheet_layers(self):
        layers = self.base.sheet_layers()
        opts = dict(self.opts)
        if opts.pop("mode", "stone") == "faction":
            return layers
        r = layers[0]
        curve = dict(pivot=r.pivot, gain=r.gain, mid=r.mid) if type(r).__name__ == "Recolour" else {}
        return [StoneRecolour(**dict(curve, **opts))]


def style_for(culture):
    from sagekit.__main__ import _style

    from .cultures import CULTURES
    _, palette, *opts = CULTURES[culture]
    return _style("scenery") if palette == "wilderland" else CultureStyle(_style(palette), opts[0] if opts else {})


def main():
    from sagekit.paint.sheets import recolour_sheet
    culture, src, out, size, upscaler = sys.argv[1:6]
    print(recolour_sheet(style_for(culture), src, out, int(size), upscaler))


if __name__ == "__main__":
    main()
