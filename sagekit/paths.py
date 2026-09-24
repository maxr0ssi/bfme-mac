"""Where things are. Everything else asks this module; nothing else hard-codes a path."""
import glob
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "assets")
TOOLS = os.path.join(REPO, "tools")
BUILD = os.path.join(REPO, "build", "assets")

ELECTRONIC_ARTS = os.path.join(REPO, "prefixes", "stable", "drive_c", "Program Files (x86)", "Electronic Arts")
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


BLENDER = os.environ.get("SAGEKIT_BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")


def blender_python():
    """Blender's bundled interpreter: numpy is there (the system python3 has none)."""
    found = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(BLENDER)),
                                          "Resources", "*", "python", "bin", "python3.*")))
    if not found:
        raise SystemExit("no Python inside %s - set SAGEKIT_BLENDER" % BLENDER)
    return found[-1]


def work_dir(building_id):
    """build/assets/<faction>/<building>: extracted sources, intermediates, the shipped tree."""
    return os.path.join(BUILD, *building_id.split("/"))
