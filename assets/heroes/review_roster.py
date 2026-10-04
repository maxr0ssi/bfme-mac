"""The roster and button-art review sheet: each faction's hero icons in roster order (EA's, ours
marked), the new heroes' portraits beside the EA hero they are graded against, and each new
hero's power buttons with their level and label (EA's images, our names)."""
import json
import re
import subprocess
from pathlib import Path

from sagekit import paths

from . import compose as C
from . import ea, portraits, roster
from . import render as R
from .captain import hero as captain
from . import gamling

OUT = Path(paths.BUILD) / "heroes" / "review"


def tile(img, label, size, dest, mark=False):
    """A labelled tile of an image (scaled to `size`), framed gold when it is ours."""
    args = ["magick", str(img), "-background", "#2a2d33", "-flatten", "-filter", "point", "-resize", "%dx%d" % (size, size),
            "-gravity", "South", "-background", "#171b21", "-splice", "0x34", "-font", paths.FONT, "-pointsize", "13",
            "-fill", "#f3d27a" if mark else "white", "-annotate", "+0+6", label]
    if mark:
        args += ["-bordercolor", "#c9a23c", "-border", "3"]
    else:
        args += ["-bordercolor", "#171b21", "-border", "3"]
    subprocess.run(args + [str(dest)], check=True)
    return str(dest)


def image_of(name, ours_dir):
    p = ours_dir / (name + ".png")
    if p.exists():
        return p, True
    dest = OUT / ("ea_%s.png" % name)
    if not dest.exists():
        portraits.ea_reference(name, dest)
    return dest, False


def review():
    OUT.mkdir(parents=True, exist_ok=True)
    f, report = C.compose()
    ours_dir = portraits.OUT
    rows = []
    new = {h for _, hs in C.ROSTER.items() for h, _ in hs}
    for faction in ("Men", "Dwarves"):
        row = []
        for hero in roster.rosters(f["playertemplate"])[faction]:
            if hero == "CreateAHero":
                continue
            body = f["gamling"] if hero == "RohanGamling" else f["captain"] if hero == captain.NAME else None
            img = (re.search(r"^[ \t]*ButtonImage[ \t]*=[ \t]*(\S+)", body, re.M).group(1) if body
                   else ea.fields(hero, "ButtonImage")[0].split()[0])
            path, ours = image_of(img, ours_dir)
            name = ea.labels().get((ea.fields(hero, "DisplayName") or ["OBJECT:" + hero])[0].split()[0].lower(), "")
            name = name or ("Captain of Erebor" if hero == captain.NAME else hero)
            row.append(tile(path, "%s%s" % (name, " (new)" if hero in new else ""), 150,
                            OUT / ("roster_%s_%s.png" % (faction, hero)), mark=hero in new))
        rows.append(row)
    pr = []
    for h, H in portraits.HEROES.items():
        ref = portraits.OUT / ("ea_%s.png" % H["ref"][0])
        pr.append(tile(ref, "EA: %s" % H["ref"][0], 192, OUT / ("p_ea_%s.png" % h)))
        pr.append(tile(ours_dir / (H["portrait"] + ".png"), "OURS: %s" % H["portrait"], 192, OUT / ("p_%s.png" % h), mark=True))
        for n in (H["icon"], H["icon"] + "_res"):
            pr.append(tile(ours_dir / (n + ".png"), n, 128, OUT / ("i_%s.png" % n), mark=True))
    rows.append(pr)
    for name, ps in (("Captain of Erebor", captain.POWERS), ("Gamling", gamling.POWERS)):
        row = []
        for p in ps:
            b = ea.all_blocks("CommandButton")[p.button]
            img = re.search(r"^\s*ButtonImage\s*=\s*(\S+)", "\n".join(re.split(r";", l)[0] for l in b.splitlines()), re.M).group(1)
            path, _ = image_of(img, ours_dir)
            label = (p.label[1] if p.label else ea.labels().get(re.search(r"TextLabel\s*=\s*(\S+)", b).group(1).lower(), "")).replace("&", "")
            row.append(tile(path, "%s L%d: %s" % (name.split()[0], p.level, label), 168, OUT / ("b_%s.png" % p.ours), mark=bool(p.label)))
        rows.append(row)
    return R.sheet(rows, R.REVIEW / "roster_and_buttons.jpg",
                   "Hero bar (Men, Dwarves; new heroes framed gold), portraits and icons, power buttons (gold: our name on EA's art)")
