"""EA's compressed animations decoded with the OpenSAGE add-on's motion channels (inside Blender).

sagekit's own reader (formats/w3dpose.py) covers the building animations; the units' adaptive-delta
channels need the add-on's decoder, which only Blender's Python has.
"""
import importlib
import io

from ..formats.w3d import chunks
from ..formats.w3dpose import Animation


def animation(data):
    """Use the installed OpenSAGE decoder for motion channels the building reader lacks."""
    a = Animation(data)
    module = importlib.import_module("io_mesh_w3d.w3d.structs.compressed_animation")
    decode = importlib.import_module("io_mesh_w3d.w3d.adaptive_delta").decode
    for t, o, s, _ in chunks(data, 0, len(data)):
        if t != 0x280:
            continue
        for tag, p, size, _ in chunks(data, o + 8, o + 8 + s):
            if tag != 0x284:
                continue
            c = module.MotionChannel.read(io.BytesIO(data[p + 8:p + 8 + size]))
            if c.delta_type:
                values = decode(c.type, c.vector_len, c.num_time_codes, c.data.scale, c.data.data)
                values = list(enumerate(values))
            else:
                values = [(d.time_code, d.value) for d in c.data]
            if c.type == 15:
                a.vis[c.pivot] = (True, [(f, bool(v)) for f, v in values], True)
            elif c.type in (0, 1, 2, 6):
                a._add(c.pivot, c.type, [(f, (v.x, v.y, v.z, v.w) if c.type == 6 else (v,), False) for f, v in values])
            else:
                raise ValueError("Unsupported motion channel: %s" % c.type)
    assert a.keys, "An animated preview must contain decoded motion, never silently show the rest pose"
    return a
