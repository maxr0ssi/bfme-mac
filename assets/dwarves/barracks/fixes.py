"""Recipe-side workaround for a framework limit the barracks was the first to hit. It is a no-op for
every other building's files.

EA's degenerate triangles (sagekit/blender/checks.py snapshot): EA's RACKPIKE (a weapon rack we do
not touch; its chunk is checked byte for byte) has 2 zero-area triangles of its own, which the
"zero-area faces" check counts against us. They are discounted for that mesh only.
Blender side only (the host has no numpy and never runs this).

(The 32-bit normal-map workaround that lived here is now in sagekit/paint/imageio.py.)"""

EA_DEGENERATE = {"RACKPIKE": 2}       # zero-area triangles in EA's own (untouched) meshes


def _patch_snapshot():
    try:
        from sagekit.blender import checks
    except ImportError:
        return
    if getattr(checks.snapshot, "degenerate_fix", False):
        return
    snapshot = checks.snapshot

    def fixed(path, skeletons=None):
        s = snapshot(path, skeletons)
        for name, n in EA_DEGENERATE.items():
            m = s["meshes"].get(name)
            if m is not None:
                m["zero_area"] = max(0, m["zero_area"] - n)
        return s
    fixed.degenerate_fix = True
    checks.snapshot = fixed


def apply():
    _patch_snapshot()
