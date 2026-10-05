"""`python3 -m sagekit hud --factions`: one palantir frame per faction on top of the Good/Evil 2x pack
(docs/HUD.md, "One palantir per faction").

build/assets/_hud/factions/
    swatch/<look>/<name>.png           the look's materials cut from its citadel's sheets (sagekit/hud/swatch.py)
    pieces/<look>_<kind>.png           the look's 3D ornaments rendered in Blender (sagekit/hud/pieces.py)
    paint/<look>_<kind>_4.png, _2.png  each look's double and single frame at 4x (review) and 2x (ships)
    paint/sockets_2.png                the portrait's button rings toned gunmetal (libInGameImagesMain_1, 2x)
    files/...                          what the archive adds to the 2x pack: palantir.apt/.const,
                                       palantirexport.apt/.dat, the new shapes' .ru (matrices doubled)
                                       and the new frames' textures (art\\textures\\apt_palantirexport_<n>.tga)
    sheet/                             the mock-ups for the review sheet
    checks.txt, trace.txt              the checks; per side and state, the texture the frame draws
"""
import json
import os
import subprocess

from .. import paths, texrecords
from ..icons import pixels
from . import root, tga
from .apt import Apt, matrices, scale
from .build import check as pack_check, files as pack_files
from .factionapt import build as build_apt
from .factioncheck import header_words, placements, references, structure, trace


def froot(*parts):
    p = os.path.join(root(), "factions", *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def factions():
    import sys
    sys.path.insert(0, paths.REPO)
    from assets.hud.factions import FACTIONS
    return FACTIONS


def paint(names, mockups=True):
    from .sheet import ABOVE, PLACE
    from .pieces import folder, render
    from .swatch import cut
    print("swatches cut from the citadels: %d new" % cut(names))
    print("3D ornaments rendered: %d" % render(names))
    job = dict(hud=root(), out=os.path.dirname(froot("paint", "x")), factions=list(names),
               swatch=os.path.dirname(froot("swatch", "x")), pieces=folder(), sockets=True,
               backdrop=os.path.join(root(), "backdrop.png") if mockups else "", place=list(PLACE),
               keep=ABOVE, mock_out=os.path.dirname(froot("sheet", "x")))
    path = froot("paint", "job.json")
    with open(path, "w") as fh:
        json.dump(job, fh, indent=1)
    res = subprocess.run([paths.blender_python(), "-m", "sagekit.paint.palantir", path], cwd=paths.REPO,
                         env=dict(os.environ, PYTHONPATH=paths.REPO), capture_output=True, text=True)
    if res.returncode:
        raise SystemExit("painting failed:\n" + res.stderr[-3000:])
    print(res.stdout.rstrip())


def texture(apt, look, kind, ea_img):
    ref = apt.read("art\\textures\\apt_palantirexport_%d.tga" % ea_img)
    w, h, rgba = pixels.read(froot("paint", "%s_%s_2.png" % (look, kind)))
    return tga.encode(ref, w, h, rgba)


def assemble(apt):
    """{member: bytes} the faction pack adds to the 2x pack, the images, labels and script address."""
    members, images, labels, act = build_apt(apt, factions())
    for i, (look, kind, ea_img) in images.items():
        members["art\\textures\\apt_palantirexport_%d.tga" % i] = texture(apt, look, kind, ea_img)
    # the portrait's button rings in a neutral gunmetal (the pack's texture, every side)
    member = "art\\textures\\apt_libingameimagesmain_1.tga"
    w, h, rgba = pixels.read(froot("paint", "sockets_2.png"))
    members[member] = tga.encode(apt.read(member), w, h, rgba)
    for m in [k for k in members if k.endswith(".ru")]:
        text, n = scale(members[m].decode("latin-1"), set(images), 2)
        if n != 1:
            raise SystemExit("%s: %d texture styles, expected 1" % (m, n))
        members[m] = text.encode("latin-1")
    return members, images, labels, act


def write(members):
    base = os.path.dirname(froot("files", "x"))
    for dirpath, _, names in os.walk(base):
        for n in names:
            os.remove(os.path.join(dirpath, n))
    for m, data in members.items():
        with open(froot("files", *m.split("\\")), "wb") as fh:
            fh.write(data)


def ours():
    """{archive member: path} of what the faction pack adds."""
    base = os.path.dirname(froot("files", "x"))
    out = {}
    for dirpath, _, names in os.walk(base):
        for n in names:
            p = os.path.join(dirpath, n)
            out["\\".join(os.path.relpath(p, base).split(os.sep))] = p
    return out


def files():
    """{archive member: path} of the faction archive: the 2x pack plus ours (ours win)."""
    out = pack_files("2x")
    out.update(ours())
    return out


def new_members():
    """Members the faction archive adds that EA's archives do not have (allowed by --stage)."""
    apt = Apt()
    return {m.lower() for m in ours() if apt.owner(m) is None}


def check(apt):
    """(lines, failures) over the built files: the 2x pack's checks, then ours."""
    lines, bad = pack_check(apt)
    lines = [x for x in lines if x.startswith("FAIL")] or ["ok   the Good/Evil 2x pack's checks (build/assets/_hud/checks.txt)"]

    def say(ok, text, quiet=False):
        nonlocal bad
        bad += not ok
        if not (ok and quiet):
            lines.append(("ok   " if ok else "FAIL ") + text)

    members = {m: open(p, "rb").read() for m, p in files().items()}
    mine = {m: open(p, "rb").read() for m, p in ours().items()}
    _, images, labels, act = build_apt(apt, factions())
    structure(apt.read("palantir.apt"), apt.read("palantir.const"), members["palantir.apt"],
              members["palantir.const"], act, say)
    ex = header_words(apt.read("palantirexport.apt"), members["palantirexport.apt"])
    say(len(ex) == 4, "palantirexport.apt: EA's bytes kept but %d header words (characters, exports)" % len(ex))
    fresh = assemble(apt)[0]
    say(all(fresh[m] == mine.get(m) for m in fresh) and set(fresh) == set(mine),
        "the staged files are what the APT builder and the paint make now (%d files)" % len(fresh))

    def size2x(img):
        w, h = tga.info(apt.read("art\\textures\\apt_palantirexport_%d.tga" % img))[:2]
        return 2 * w, 2 * h

    references(members, apt.read, factions(), images, size2x, say)
    placements(apt.read("palantir.apt"), apt.read("palantir.const"), members, factions(), say)
    for i, (look, kind, ea_img) in sorted(images.items()):
        first = {m: matrices(d.decode("latin-1"))[:1] for m, d in members.items() if m.endswith(".ru")
                 and m.startswith("palantirexport_geometry")}
        shape = [m for m in mine if first.get(m) and first[m][0][0] == i]
        base = [m for m in first if m not in mine and first[m] and first[m][0][0] == ea_img]
        same = len(shape) == 1 and len(base) == 1 and first[shape[0]][0][1] == first[base[0]][0][1]
        say(same, "%s %s: %s draws image %d with the 2x pack's doubled matrix of EA's %s" % (
            look, kind, shape[0].split("\\")[-1] if shape else "?", i, base[0].split("\\")[-1] if base else "?"))
    say(*texrecords.check(members, "the faction palantir"))     # new names need asset.dat records
    tl = trace(members, apt.read, act, factions(), images, say)
    with open(froot("trace.txt"), "w") as fh:
        fh.write("\n".join(tl) + "\n")
    with open(froot("checks.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return lines, bad


def run(paint_too=True):
    apt = Apt()
    if not pack_files("2x"):
        raise SystemExit("build the Good/Evil pack first: python3 -m sagekit hud")
    if paint_too:
        paint(factions())
    members, images, labels, act = assemble(apt)
    write(members)
    print("faction palantir: %d looks, %d sides, %d files over the 2x pack" % (
        len(factions()), len(labels) // 2, len(members)))
    lines, bad = check(apt)
    print("\n".join(lines))
    return bad
