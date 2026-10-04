#!/usr/bin/env python3
"""Build the heroes pack: the Captain's and Aragorn's models, the portraits and icons, the INI
composed onto EA's 2.02 files and linted, the string table; nothing installed.

    python3 -m assets.heroes.build [--skip-art]     -> build/assets/heroes/{captain,aragorn,portraits,pack}/
    python3 -m assets.heroes.audit                  # EA's hidden heroes: what is complete
    python3 -m assets.heroes.render                 # the review sheets
    python3 -m sagekit.units.heroes --stage | --install | --revert [--dry-run]
"""
import json
import sys
from pathlib import Path

from sagekit import paths

from . import compose as C
from . import ea, lint, portraits, strings
from . import gamling_model
from .aragorn import design as aragorn
from .captain import design as captain

OUT = Path(paths.BUILD) / "heroes" / "pack"


def art(skip=False):
    """{archive member: local file} of every model, sheet, mask, portrait and icon."""
    if not skip or not (Path(paths.BUILD) / "heroes" / "portraits" / "report.json").exists():
        captain.build()
        aragorn.build()
        gamling_model.build()
        portraits.build()
    files = dict(captain.members())
    files.update(aragorn.members())
    files.update(gamling_model.members())
    rep = json.loads((Path(paths.BUILD) / "heroes" / "portraits" / "report.json").read_text())
    files.update({k: Path(v) for k, v in rep["files"].items()})
    missing = [str(v) for v in files.values() if not Path(v).exists()]
    if missing:
        raise SystemExit("heroes: built files missing: %s" % missing)
    return files


def build(skip_art=False):
    OUT.mkdir(parents=True, exist_ok=True)
    files = art(skip_art)
    ea_files = C.read_all()
    f, report = C.compose(ea_files)
    entries = C.strings()
    table, string_report = strings.compose(entries)
    strings.check(table, entries)
    labels = set(strings.labels_of(table))
    images = set(ea.mapped_images()) | {n.lower() for n in _our_images()}
    models = {captain.MODEL.lower(), aragorn.MODEL.lower(), gamling_model.MODEL.lower()}
    objects = set(ea.objects()) | set(lint.object_texts(f))
    problems = lint.check(ea_files, f, labels, images, models, objects)
    if problems:
        raise SystemExit("heroes: the lint fails:\n  " + "\n  ".join(problems))
    broken = lint.broken_copies(ea_files, f, labels, images, models, objects)
    caught = [what for what, errs in broken if errs]
    if len(caught) != len(broken):
        raise SystemExit("heroes: the lint missed a broken copy: %s" % [w for w, e in broken if not e])
    ini_dir = OUT / "ini"
    written = {}
    for member, data in C.members(f).items():
        p = ini_dir / member.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        written[member] = str(p)
    (OUT / "lotr.str").write_bytes(table)
    report.update(ini=written, changed_lines=C.changed_lines(ea_files, f), strings=string_report,
                  broken_copies_caught=caught, art={k: str(v) for k, v in files.items()})
    (OUT / "report.json").write_text(json.dumps(report, indent=1, default=str) + "\n")
    print("PASS heroes pack: %d INI members (%s), lint clean, %d broken copies caught; %d labels added, %d corrected; "
          "%d art members. Built into %s; nothing installed." % (
              len(written), ", ".join("%s %d" % (Path(k.replace("\\", "/")).name, v) for k, v in report["changed_lines"].items()),
              len(caught), len(string_report["added"]), len(string_report["replaced"]), len(files), OUT))
    return report


def _our_images():
    out = []
    for H in portraits.HEROES.values():
        out += [H["portrait"], H["icon"], H["icon"] + "_res"]
    return out


if __name__ == "__main__":
    build("--skip-art" in sys.argv)
