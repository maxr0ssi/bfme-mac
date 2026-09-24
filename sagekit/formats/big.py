"""EA .big archives, through tools/bigtool.py (the one implementation of the format)."""
import importlib.util
import os
import sys

from .. import paths

if "bigtool" not in sys.modules:
    _spec = importlib.util.spec_from_file_location("bigtool", os.path.join(paths.TOOLS, "bigtool.py"))
    sys.modules["bigtool"] = importlib.util.module_from_spec(_spec)   # before exec: its dataclass needs it
    _spec.loader.exec_module(sys.modules["bigtool"])
bigtool = sys.modules["bigtool"]


def norm(member):
    """Case- and separator-insensitive member key, as the game matches names."""
    return member.replace("/", "\\").lower()


class Archive:
    def __init__(self, path):
        self.path = path
        self._index = None

    def index(self):
        """{normalised member name: bigtool.Entry}"""
        if self._index is None:
            entries, _ = bigtool.read_index(self.path)
            self._index = {norm(e.name): e for e in entries}
        return self._index

    def __contains__(self, member):
        return norm(member) in self.index()

    def read(self, member):
        return bigtool.read_member(self.path, self.index()[norm(member)])

    def extract(self, member, dest_root):
        """Write member under dest_root with its archive path; returns the file path."""
        out = os.path.join(dest_root, *norm(member).split("\\"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as fh:
            fh.write(self.read(member))
        return out


def pack(members, out_path):
    """members: [(archive path with '\\', bytes)] -> a new archive (the format RotWK reads)."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(bigtool.build_big(sorted(members, key=lambda m: norm(m[0])), b"BIGF"))
