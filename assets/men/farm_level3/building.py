"""The Gondor farm at level 3 (FarmInterface's SubObjectsUpgrade: V2 shown, V2HIDE hidden): the
farmhouse's upper storey and its taller thatch, redesigned on the finished level-2 farm (`base`;
levels.py). EA's V2 raises the cottage's walls from z 25.2 by a storey with small windows under
a steeper roof whose ridge runs north-south, gables to the south and north, and the chimney.
Now:

    frieze      a sable band with gilt stars round the storey at its floor line
    quoins      long and short dressed stones up the storey's four corners
    windows     a pediment on consoles over each of the upper windows
    roundels    the White Tree in a steel ring high on the south and north gables
    kneelers    moulded blocks on the gables' corners under the eaves
    chimney     a coping and two pots on EA's stack (top 70.33)

No cloth and no lights (a level mesh). Painted from our own copy of GBFarm, GBFarP.

EA's V2 (mesh = model coordinates): the storey's walls x 8.25 and 34.22 (the eave sides, to
about 47 under the roof, whose eaves are at x 4.54 and 37.05 about z 49), y +-18.68 (the gables,
rising to about 65 at x 21.2); its windows' frames (3.0 wide, 0.7 proud) at z 36.22..44.5:
west y -12.05, -1.39, 11.0; east y -11.15, 1.23, 11.9; south and north x 16.05, 26.7. The body's
banner and roundel on the south wall end at z 24.3 below the storey."""
from ..barracks.levels import LevelMesh, chain

X0, X1, YH = 8.25, 34.22, 18.68
Z0, EAVE = 25.21, 47.0
WINDOWS = {"W": (-12.05, -1.39, 11.0), "E": (-11.15, 1.23, 11.9), "S": (16.05, 26.7), "N": (16.05, 26.7)}
WIN = (1.5, 44.5)                                   # half width, head
ROUNDEL = (21.24, 53.0, 2.6)


class FarmLevel3(LevelMesh):
    source = "GBFarm_SKN"
    target = "V2"
    base = chain("farm", 3)
    level = 3
    sheet = "GBFarm.tga"
    sheet_normal = "GBFarm_NRM.tga"
    own_textures = {"GBFarm.tga": "GBFarP.tga"}
    bake_hidden = ("V1HIDE", "V2HIDE", "N_WINDOW")
    views = {
        "rts": ((-1.1, 0.1, 20.0), 280, 50, -38, 50),
        "close": ((21.0, -5.0, 38.0), 120, 20, -45, 45),
        "ingame": ((-1.1, 0.1, 20.0), 620, 53, -62, 50),
    }

    def variants(self, install):
        from ..workshop.prodkit import same_length_variants
        return same_length_variants(self, install, super().variants(install))

    def decals(self):
        from ..workshop.prodkit import props_layer
        return [props_layer(sat=(0.12, 0.22), gate=(0.4, 0.65), hue=(22.0, 50.0), rects=[(0.16, 0.22, 0.42, 0.46), (0.0, 0.455, 0.27, 0.5)])]          # EA's thatch stays straw

    def design(self, kit):
        from ..barracks import motifs as M
        faces = {"W": M.face((X0, 0.0), (-1, 0)), "E": M.face((X1, 0.0), (1, 0)),
                 "S": M.face(((X0 + X1) / 2, -YH), (0, -1)), "N": M.face(((X0 + X1) / 2, YH), (0, 1))}
        out = []
        for key, (a, t, n) in faces.items():
            half = YH if key in "WE" else (X1 - X0) / 2
            out += M.star_frieze(kit, a, t, n, -half + 0.2, half - 0.2, Z0 + 0.25, h=2.0, d0=-0.3, d1=0.4, pitch=3.4)
            for side in (-1, 1):
                out += M.quoins(a, t, n, side * half, Z0 + 2.4, EAVE - 0.8, side=side, long=2.2, short=1.3, h=1.55, d=0.35)
            half_w, head = WIN
            for w in WINDOWS[key]:
                q = (a.x, w) if key in "WE" else (w, a.y)
                u = (q[0] - a.x) * t.x + (q[1] - a.y) * t.y
                out += M.window_pediment(a, t, n, u, half_w + 0.7, head + 0.35, rise=1.2, d=1.0)
            if key in "SN":
                for e in (-1, 1):                   # kneelers under the eaves, over the quoins
                    uc, ui = e * half, e * (half - 2.5)
                    u0, u1 = sorted((uc, ui))
                    out.append(M.slab(a, t, n, u0, u1, EAVE - 0.8, EAVE + 0.2, -0.3, 0.95, front="course"))
                x, z, r = ROUNDEL
                out += M.roundel(kit, a, t, n, (x - a.x) * t.x, z, r, d=0.25)
        from ..workshop.prodkit import chimney_cap, closed
        out += chimney_cap(23.84, 28.32, 9.17, 13.42, 70.33)        # a coping and pots on EA's stack
        return closed(out)                   # EA's walls are single planes: no buried backs
