"""The palantir's metal, Good and Evil (numpy; sagekit/paint/hud.py paints with it).

EA's RotWK skins the palantir twice: bronze for the Good side, grey iron for the Evil side. Both
keep EA's layout and EA's ring cross-section (sagekit/paint/hudrings.py); what changes is the metal:

  Good   burnished bronze and polished gold: gold beads, a gold rope where EA has a plain second
         bead, the broad band aged bronze engraved with a running lozenge-and-pellet border (the
         Númenórean border the Men and Dwarves carry on their own trim).
  Evil   blackened iron and hard steel, the Mordor/Isengard/Angmar metal: steel-edged beads, a
         saw-toothed second bead, the broad band riveted iron plates with dark seams, the faintest
         ember in the deepest grooves.

A look's ramps colour a shade (0..1) per material; `regrade` colours EA's own pixels (the scroll
joint, the resource bar, the spikes: everything not redrawn) from their luminance, so the redrawn
rings and EA's ornaments are one metal.
"""
import numpy as np

MATERIALS = ("lip", "bead1", "groove", "bead2", "band", "rivet", "engraved")


def ramp(stops, t):
    t = np.clip(t, 0, 1)
    xs = [s[0] for s in stops]
    return np.stack([np.interp(t, xs, [s[1][c] for s in stops]) for c in range(3)], -1).astype(np.float32)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


class Look:
    name = None
    side = None
    # where each element of EA's cross-section lies across the band (s: 0 inner edge, 1 outer)
    bands = {"bead1": (0.07, 0.25), "groove1": (0.25, 0.33), "bead2": (0.33, 0.53),
             "groove2": (0.53, 0.60), "band": (0.60, 0.95)}
    height_px = 1.6                 # the tallest bead, in 1x pixels (how steep the light finds it)
    bead_height = 1.0
    period = 2.1                    # one motif of the broad band: this many band widths
    rope = 1.3                      # one strand of the rope (or tooth): this many bead widths
    twist = 1.4
    engrave_depth = 0.45
    rivet_height = 0.95
    light = (-0.45, -0.75, 0.75)    # from the top left, as EA lights its frames
    ambient, diffuse, env, shininess = 0.16, 0.62, 0.22, 36
    spec_colour = (1.0, 0.95, 0.82)
    spec_gain = 0.55
    ramps = {}
    mat_ramp = {}                   # material -> ramp name
    ornament = []                   # EA's pixels: luminance (0..1) -> colour
    ornament_gain = 1.0

    @property
    def mat(self):
        return {m: i for i, m in enumerate(MATERIALS)} | {"groove": MATERIALS.index("groove")}

    def bead1(self, u):
        """The inner bead's height across it (u: -1 inner edge .. 1 outer edge)."""
        return np.sqrt(np.clip(1 - u * u, 0, 1))

    def bead2(self, u, ph):
        """The second bead's height at u across it and phase ph along the ring (0..1 per strand)."""
        return np.sqrt(np.clip(1 - u * u, 0, 1))

    def engrave(self, p, v, period, bandw):
        raise NotImplementedError

    def colour(self, mat, shade, spec):
        out = np.zeros(shade.shape + (3,), np.float32)
        for i, m in enumerate(MATERIALS):
            sel = mat == i
            if sel.any():
                out[sel] = ramp(self.ramps[self.mat_ramp[m]], shade[sel])
        return np.clip(out + self.spec_gain * spec[..., None] * np.array(self.spec_colour, np.float32), 0, 1)

    def regrade(self, lum):
        """EA's (upscaled) pixels by luminance: the frame's dark glass and shadow stay dark."""
        return ramp(self.ornament, np.clip(lum * self.ornament_gain, 0, 1))


class Good(Look):
    name = "Good: burnished bronze and gold"
    side = "good"
    ambient, diffuse, env = 0.10, 0.55, 0.20
    ramps = {
        "gold": [(0, (.07, .05, .025)), (.3, (.30, .21, .09)), (.55, (.58, .44, .20)), (.75, (.80, .66, .36)),
                 (.9, (.93, .84, .60)), (1, (1, .96, .86))],
        "bronze": [(0, (.045, .032, .02)), (.3, (.17, .12, .07)), (.55, (.33, .25, .14)), (.75, (.50, .39, .23)),
                   (.9, (.68, .56, .38)), (1, (.86, .77, .60))],
        "dark": [(0, (.012, .009, .006)), (.6, (.07, .05, .03)), (1, (.17, .12, .07))],
    }
    mat_ramp = {"lip": "dark", "bead1": "gold", "groove": "dark", "bead2": "gold", "band": "bronze",
                "rivet": "gold", "engraved": "dark"}
    # EA's bronze pixels onto ours: black stays black, its mid olive becomes bronze, its lights gold
    ornament = [(0, (0, 0, 0)), (.1, (.06, .045, .025)), (.25, (.19, .14, .075)), (.45, (.42, .32, .16)),
                (.65, (.70, .56, .30)), (.82, (.90, .79, .55)), (1, (1, .96, .86))]
    ornament_gain = 1.08

    def bead2(self, u, ph):
        """A twisted rope: round across, each strand swelling along the ring."""
        return np.sqrt(np.clip(1 - u * u, 0, 1)) * (0.45 + 0.55 * np.sin(np.pi * ph) ** 0.6)

    def engrave(self, p, v, period, bandw):
        """A lozenge outlined in a cut line, a domed pellet between lozenges."""
        x = (p - 0.5) * period / bandw                     # band widths from the motif's middle
        y = v - 0.5
        half = 0.5 * period / bandw - 0.22                 # the lozenge stops short of the pellet
        d = np.abs(x) / max(half, 0.3) + np.abs(y) / 0.34
        cut = 1 - smoothstep(0.07, 0.17, np.abs(d - 1))
        inner = 1 - smoothstep(0.05, 0.12, np.abs(d - 0.45)) * 1.0
        xp = np.where(p < 0.5, p, p - 1) * period / bandw
        dist = np.hypot(xp, y) / 0.16
        stud = np.sqrt(np.clip(1 - dist * dist, 0, 1))
        return np.clip(cut + 0.6 * inner * (d < 0.6), 0, 1), stud


class Evil(Look):
    name = "Evil: blackened iron and steel"
    side = "evil"
    period = 3.0
    rope = 2.2
    twist = 0.0
    engrave_depth = 0.55
    shininess = 60
    spec_colour = (0.86, 0.90, 0.98)
    spec_gain = 0.22
    ambient, diffuse, env = 0.12, 0.62, 0.22
    ramps = {
        "steel": [(0, (.02, .02, .024)), (.35, (.11, .115, .13)), (.6, (.26, .27, .30)), (.8, (.46, .48, .52)),
                  (.93, (.68, .70, .75)), (1, (.86, .88, .92))],
        "iron": [(0, (.015, .015, .017)), (.35, (.065, .065, .07)), (.6, (.16, .16, .17)), (.8, (.29, .29, .31)),
                 (.93, (.40, .40, .42)), (1, (.58, .58, .61))],
        # the deepest grooves: black with the faintest forge-ember in them
        "dark": [(0, (.01, .006, .004)), (.6, (.05, .025, .014)), (1, (.15, .06, .02))],
    }
    mat_ramp = {"lip": "dark", "bead1": "steel", "groove": "dark", "bead2": "steel", "band": "iron",
                "rivet": "steel", "engraved": "dark"}
    # EA's grey iron onto ours: a darker body, its bright edges kept as cold steel
    ornament = [(0, (0, 0, 0)), (.1, (.03, .03, .033)), (.3, (.115, .115, .125)), (.5, (.26, .26, .28)),
                (.68, (.45, .46, .49)), (.85, (.70, .72, .76)), (1, (.93, .94, .97))]
    ornament_gain = 1.15            # EA's grey iron is dark already; its dragon and thorns must still read

    def bead1(self, u):
        """A chamfered bar: flat top, hard bevels (machined, not polished round)."""
        return np.clip((1 - np.abs(u)) / 0.4, 0, 1) ** 0.8

    def bead2(self, u, ph):
        """A blade edge: a V ridge, notched once per tooth (a dip that falls steeply, rises slowly)."""
        ridge = np.clip(1 - np.abs(u), 0, 1)
        notch = 0.45 + 0.55 * smoothstep(0.0, 0.18, ph)
        return ridge * notch

    def engrave(self, p, v, period, bandw):
        """Riveted iron plates: a dark seam between plates with a rivet either side of it, a barbed
        chevron cut into each plate pointing along the ring."""
        xs = np.where(p < 0.5, p, p - 1) * period / bandw        # band widths from the nearest seam
        seam = 1 - smoothstep(0.03, 0.08, np.abs(xs))
        y = v - 0.5
        stud = 0
        for xc in (-0.32, 0.32):
            dist = np.hypot(xs - xc, y) / 0.15
            stud = np.maximum(stud, np.sqrt(np.clip(1 - dist * dist, 0, 1)))
        x = (p - 0.5) * period / bandw                           # from the plate's middle
        chev = 0
        for x0 in (-0.35, 0.25):
            d = np.abs((x - x0) - 1.1 * np.abs(y))
            chev = np.maximum(chev, (1 - smoothstep(0.04, 0.10, d)) * (np.abs(y) < 0.33))
        return np.clip(seam + chev, 0, 1), stud


LOOKS = {"good": Good(), "evil": Evil()}
