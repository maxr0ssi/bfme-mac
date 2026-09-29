"""Where things are. Everything else asks this module; nothing else hard-codes a path."""
import glob
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "assets")
TOOLS = os.path.join(REPO, "tools")
BUILD = os.path.join(REPO, "build", "assets")

def _electronic_arts():
    """The games inside the Wine prefix scripts/install.sh made (prefixes/w10; older setups: stable),
    or SAGEKIT_PREFIX."""
    for p in [os.environ.get("SAGEKIT_PREFIX"), os.path.join(REPO, "prefixes", "w10"),
              os.path.join(REPO, "prefixes", "stable")]:
        ea = p and os.path.join(p, "drive_c", "Program Files (x86)", "Electronic Arts")
        if ea and os.path.isdir(ea):
            return ea
    return os.path.join(REPO, "prefixes", "w10", "drive_c", "Program Files (x86)", "Electronic Arts")


ELECTRONIC_ARTS = _electronic_arts()
GAMEDIRS = {
    "rotwk": os.path.join(ELECTRONIC_ARTS, "RotWK"),
    "bfme2": os.path.join(ELECTRONIC_ARTS, "BFME2"),
}
# RotWK loads its own folder's archives first, then BFME2's (the first archive to provide a path wins)
SEARCH_ORDER = {"rotwk": ["rotwk", "bfme2"], "bfme2": ["bfme2"]}

# Archives this repo produces (group pack, built assets, tests) sort first with ten or more '!'
# (EA's HD Edition uses eight). Sources are always extracted from the game's own archives.
OURS_PREFIX = "!" * 10


def is_ours(archive_name):
    return os.path.basename(archive_name).startswith(OURS_PREFIX)


MAC_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
# SAGEKIT_BLENDER wins; else the Mac's app, else a `blender` on PATH (Linux: the official tarball's)
BLENDER = os.environ.get("SAGEKIT_BLENDER") or (MAC_BLENDER if os.path.exists(MAC_BLENDER) else
                                                shutil.which("blender") or MAC_BLENDER)

# the render labels' font: the Mac's Arial Bold, else DejaVu Sans Bold (Linux), or SAGEKIT_FONT
FONTS = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
FONT = os.environ.get("SAGEKIT_FONT") or next((f for f in FONTS if os.path.exists(f)), FONTS[0])


def blender_python():
    """Blender's bundled interpreter: numpy is there (the system python3 has none). The Mac app
    keeps it in Contents/Resources/<version>/python, the Linux tarball beside the binary."""
    exe = os.path.realpath(BLENDER)
    found = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(BLENDER)),
                                          "Resources", "*", "python", "bin", "python3.*")))
    found = found or sorted(glob.glob(os.path.join(os.path.dirname(exe), "*", "python", "bin", "python3.*")))
    if not found:
        raise SystemExit("no Python inside %s - set SAGEKIT_BLENDER" % BLENDER)
    return found[-1]


def work_dir(building_id):
    """build/assets/<faction>/<building>: extracted sources, intermediates, the shipped tree."""
    return os.path.join(BUILD, *building_id.split("/"))
