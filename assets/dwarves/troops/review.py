"""Render the installed Dwarven troop sources for review; never changes or launches the game.

python3 -m assets.dwarves.troops.review [--render]
The explicit roster follows the active recruitment INIs, not the building-only draw parser.
"""
import argparse
import hashlib
import html
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sagekit import paths
from sagekit.formats.textures import compiled_path
from sagekit.formats.w3d import W3DFile

FOLDER = Path(paths.BUILD)/"dwarves/troops"
# Upgrade modules show these objects only after purchase. Idle arrows follow the animation.
ROSTER = [
    ("guardian", "Guardian", "eudwarfgua_skn", "eudwarfgua_idla", ["FORGED_BLADE", "HAMMER1"]),
    ("phalanx", "Phalanx", "duphalanx_skn", "duphalanx_idla", ["FORGED_BLADE"]),
    ("axe_thrower", "Axe Thrower", "eudwarfaxe_skn", "eudwarfaxe_idla", ["FORGED_BLADE"]),
    ("men_of_dale", "Men of Dale", "ruarcher_skn", "guarcher_idla", ["FIREAROWTIP"]),
    ("zealot", "Zealot — halberd source", "rudwrfhlbd_skn", "rugimli_idla", ["AXE02", "FORGED_BLADE"]),
    ("zealot_hammer", "Zealot — hammer source", "rudwrfhmr_skn", "rugimli_idla", ["AXE02", "FORGED_BLADE"]),
    ("battlewagon", "Battlewagon", "dubtlwagon_skn", "dubtlwagon_idla",
     ["DWARFHEARTH", "DWARFHEARTHFIRE", "BANNER_L"]),
    ("catapult", "Catapult", "ducatapult_skn", "ducatapult_idla", []),
    ("demolisher", "Demolisher", "eudwarfram_skn", "eudwarfram_idla", []),
]


def prepare():
    from sagekit.game import Install
    g = Install(pristine=False)
    src = FOLDER/"src"
    src.mkdir(parents=True, exist_ok=True)
    hashes, owners, entries = {}, {}, []

    def extract(member):
        data = g.read(member)
        path = src/member.rsplit("\\", 1)[-1]
        path.write_bytes(data)
        hashes[member] = hashlib.sha256(data).hexdigest()
        owners[member] = g.owner(member).path
        return str(path)

    for key, title, model, anim, hidden in ROSTER:
        path = extract(g.model_path(model))
        w = W3DFile(path)
        skeleton = extract(g.model_path(w.skeleton()[:-4])) if w.skeleton() else None
        textures = {}
        for name in {t.lower() for m in w.meshes.values() for t in m.textures}:
            member = next((compiled_path(name, ext) for ext in (".dds", ".tga")
                           if g.owner(compiled_path(name, ext))), None)
            assert member, (model, name)
            textures[name] = extract(member)
        entries.append(dict(key=key, title=title, model=path, skeleton=skeleton,
                            animation=extract(g.model_path(anim)), hidden=hidden, textures=textures))
    assert len({e["key"] for e in entries}) == len(entries)
    manifest = dict(entries=entries, hashes=hashes, owners=owners)
    (FOLDER/"sources.json").write_text(json.dumps(manifest, indent=2)+"\n")
    return entries


def render_sources():
    import bpy
    import numpy as np
    from assets.dwarves.porter.preview import animation
    from sagekit.blender import render, scene
    from sagekit.blender.lifecycle import Model
    from sagekit.formats.w3dlight import material

    entries = json.loads((FOLDER/"sources.json").read_text())["entries"]
    out = FOLDER/"renders"
    out.mkdir(exist_ok=True)
    for entry in entries:
        m = Model(entry["model"], entry["skeleton"])
        m.anim = animation(Path(entry["animation"]).read_bytes())
        assert m.anim.hierarchy.upper() == m.skel.name.upper()
        for f in range(m.anim.frames):
            assert np.isfinite(np.array(m.pose(f)[0])).all()
        pose = m.pose(0)
        scene.clear()
        points = []
        for name, mesh in m.w3d.meshes.items():
            if name in entry["hidden"]:
                continue
            bones = m.vertex_bones(name)
            faces = [t for t in mesh.tris if all(pose[1][bones[v]] for v in t)]
            if not faces:
                continue
            vertices = m.world(name, pose)
            points.extend(vertices[list({v for t in faces for v in t})].tolist())
            me = bpy.data.meshes.new(name)
            me.from_pydata(vertices.tolist(), [], faces)
            me.update()
            obj = bpy.data.objects.new(name, me)
            bpy.context.collection.objects.link(obj)
            uv = me.uv_layers.new(name="UVMap")
            for lp in me.loops:
                uv.data[lp.index].uv = mesh.uv[lp.vertex_index]
            if name in ("DWARF", "DWARF01", "BODY", "HEAD1", "GOAT_L", "GOAT_R"):
                me.shade_smooth()
            render.game_material(obj, mesh, entry["textures"])
            if not material(mesh.bytes)["alpha"]:
                for node in me.materials[0].node_tree.nodes:
                    if node.type == "TEX_IMAGE":
                        node.image.alpha_mode = "NONE"
        assert points, entry["key"]
        lo, hi = np.min(points, axis=0), np.max(points, axis=0)
        render.rig((850, 850), 24)
        sc = bpy.context.scene
        sc.camera = render.camera("troop", ((lo+hi)/2).tolist(),
                                  math.dist(lo, hi)*1.6, 22, -38, 52)
        sc.render.filepath = str(out/(entry["key"]+".png"))
        bpy.ops.render.render(write_still=True)
        print("REVIEW OK", entry["key"], flush=True)


def gallery(entries):
    from sagekit.pipeline import Render
    tiles = []
    for e in entries:
        tile = FOLDER/"renders"/(e["key"]+"_label.jpg")
        subprocess.run(["magick", str(FOLDER/"renders"/(e["key"]+".png")),
                        "-background", "#171b21", "-gravity", "south", "-splice", "0x62",
                        "-font", Render.FONT, "-pointsize", "27", "-fill", "white",
                        "-annotate", "+0+18", e["title"], str(tile)], check=True)
        tiles.append(str(tile))
    subprocess.run(["magick", "montage", "-font", Render.FONT, *tiles, "-tile", "3x3", "-geometry", "620x665+5+5",
                    "-background", "#171b21", str(FOLDER/"roster.jpg")], check=True)
    cards = "".join('<figure><img src="renders/'+e["key"]+'.png"><figcaption>'+
                    html.escape(e["title"])+"</figcaption></figure>" for e in entries)
    (FOLDER/"review.html").write_text('''<!doctype html><meta charset="utf-8">
<title>Dwarven troops — current installed art</title><style>
body{background:#171b21;color:#ece8de;font:18px system-ui;max-width:1500px;margin:40px auto;padding:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px}
figure{margin:0}img{width:100%}figcaption{padding:10px}p{line-height:1.5}a{color:#e6be74}
</style><h1>Dwarven troops — current installed art</h1>
<p>Source models in decoded idle poses, for design review. No troop art has been changed or
installed. Base equipment is shown; upgrade effects, game lighting and player-colour blending
are not simulated. The Zealot's two source models are shown separately to inspect both designs.</p>
<p><a href="upgrade-audit.md">Recruitment and upgrade audit</a></p><div class="grid">'''+cards+'</div>')


def main():
    from sagekit.pipeline import blender_slot, game_running
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--render", action="store_true")
    args = p.parse_args()
    if game_running():
        raise SystemExit("Close the game before preparing troop previews.")
    entries = prepare()
    if args.render:
        with blender_slot(), (FOLDER/"render.log").open("w") as log:
            subprocess.run([paths.BLENDER, "-b", "--python", str(Path(__file__).resolve()),
                            "--", "blender"], stdout=log, stderr=subprocess.STDOUT, check=True)
        gallery(entries)
    print("Troop source review prepared:", FOLDER)


if __name__ == "__main__":
    if "bpy" in sys.modules:
        render_sources()
    else:
        main()
