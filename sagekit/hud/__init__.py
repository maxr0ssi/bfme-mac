"""The in-game palantir HUD: EA's APT frame, glass and button textures repainted in our metal, at 1x
and Retina 2x (docs/HUD.md). Stdlib only; the painting runs in sagekit/paint/hud.py (numpy)."""
import os

from .. import paths

ARCHIVE = "!!!!!!!!!!!!!!sagekit-hud.big"      # fourteen '!': before EA's apt/ archives and __patch202


def root():
    """build/assets/_hud: EA's sources, the upscales, our textures, the retina geometry, the sheets."""
    return os.path.join(paths.BUILD, "_hud")


def table():
    import sys
    sys.path.insert(0, paths.REPO)
    from assets.hud.frames import FRAMES, key, texture_member
    return FRAMES, key, texture_member
