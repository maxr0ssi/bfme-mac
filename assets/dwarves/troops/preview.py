"""Offline, paired troop previews with real W3D motion. Never installs or starts the game.

python3 -m assets.dwarves.troops.preview [--stills|--motion] [--unit guardian]
"""
import argparse
import json
import math
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from sagekit import paths
from assets.dwarves.troops import catalog

FOLDER = Path(paths.BUILD) / 'dwarves/troops/redesign'
RUN_SCRIPT = Path(__file__).resolve()
TITLE = 'Dwarven troops'
NOTES = None


def configure(folder, roster, script, title, notes):
    global FOLDER, catalog, RUN_SCRIPT, TITLE, NOTES
    FOLDER, catalog, RUN_SCRIPT, TITLE, NOTES = folder, roster, script, title, notes



def jobs(args):
    out = []
    for e in catalog.ROSTER:
        if args.unit and e['key'] not in args.unit:
            continue
        motion_variants = {'base', e['variants'][-1]['key']}
        if e['key'] == 'guardian':
            motion_variants.add('forged_armor')
        if e['key'] == 'battlewagon':
            motion_variants.update(v['key'] for v in e['variants'] if v['key'].endswith('_armor'))
        for v in e['variants']:
            if args.variant and v['key'] not in args.variant:
                continue
            if args.stills:
                out.append(dict(unit=e['key'], variant=v['key'], pose='idle', kind='still'))
            if args.motion and (args.all_variants or args.variant or v['key'] in motion_variants):
                for pose in e['animations']:
                    if args.pose and pose not in args.pose:
                        continue
                    out.append(dict(unit=e['key'], variant=v['key'], pose=pose, kind='motion'))
    return out


def stem(job):
    return '_'.join(job[k] for k in ('unit', 'variant', 'pose', 'kind'))


def frame_delay(job, samples):
    """Centiseconds per sampled frame, retaining the source clip's nominal duration."""
    from sagekit.formats.w3d import chunks
    state=catalog.state(catalog.BY_KEY[job['unit']],job['variant'],job['pose'])
    name=state['animation']
    data=(FOLDER/'src/art/w3d'/name[:2]/(name+'.w3d')).read_bytes()
    for tag,offset,size,_ in chunks(data,0,len(data)):
        if tag not in (0x200,0x280):continue
        for kind,p,n,_ in chunks(data,offset+8,offset+8+size):
            if kind not in (0x201,0x281):continue
            frames=struct.unpack_from('<I',data,p+44)[0]
            fps=struct.unpack_from('<H' if kind==0x281 else '<I',data,p+48)[0]
            assert frames>0 and fps>0
            return max(1,round(100*frames/fps/samples))
    raise ValueError('No clip timing: '+name)


def draw():
    import bpy
    import numpy as np
    from mathutils import Vector
    from assets.dwarves.porter.preview import animation
    from sagekit.blender import render, scene
    from assets.dwarves.troops.posing import Model
    from sagekit.formats.w3dlight import material
    from sagekit.formats.w3dpose import mul

    args = json.loads(Path(sys.argv[sys.argv.index('--') + 1]).read_text())
    data = json.loads((FOLDER / 'build.json').read_text())
    out = FOLDER / 'renders'
    out.mkdir(exist_ok=True)
    models, animations, bounds = {}, {}, {}
    checks = {}

    def load(state, side):
        key = (state['model'], side)
        if key not in models:
            item = data['models'][state['model']]
            models[key] = Model(item['source' if side == 'before' else 'work'], item['skeleton'])
        m = models[key]
        name = state['animation']
        if name not in animations:
            path = FOLDER / 'src/art/w3d' / name[:2] / (name + '.w3d')
            animations[name] = animation(path.read_bytes())
        m.anim = animations[name]
        assert m.anim.hierarchy.upper() == m.skel.name.upper(), (state['model'], name)
        audit = (state['model'], side, name)
        if audit not in checks:
            for frame in range(m.anim.frames):
                assert np.isfinite(np.asarray(m.pose(frame)[0])).all(), audit
            checks[audit] = m.anim.frames
        return m

    def parts(e, upgrade, pose, side):
        state = catalog.state(e, upgrade, pose)
        m = load(state, side)
        result = [(state, m, None)]
        for key, bone in state.get('passengers', []):
            passenger = catalog.BY_KEY[key]
            passenger_pose = pose if pose in passenger['animations'] else 'idle'
            ps = catalog.state(passenger, 'base', passenger_pose)
            pm = load(ps, side)
            index = next(i for i, pivot in enumerate(m.skel.pivots) if pivot[0].upper() == bone)
            result.append((ps, pm, index))
        return result

    def posed(parts, fraction):
        root_state, root, _ = parts[0]
        root.anim = animations[root_state['animation']]
        root_pose = root.pose(round(fraction * (root.anim.frames - 1)))
        for state, m, attach in parts:
            m.anim = animations[state['animation']]
            pose = m.pose(round(fraction * (m.anim.frames - 1)))
            if attach is not None:
                pose = ([mul(root_pose[0][attach], mat) for mat in pose[0]], pose[1])
            for name, mesh in m.w3d.meshes.items():
                if name.upper() in state['hidden']:
                    continue
                bones = m.vertex_bones(name)
                faces = [tri for tri in mesh.tris if all(pose[1][bones[v]] for v in tri)]
                yield state, mesh, m.world(name, pose), faces

    def additive(obj, mesh, texmap):
        render.game_material(obj, mesh, texmap)
        info = material(mesh.bytes)
        mat = obj.data.materials[0]
        nt = mat.node_tree
        if info.get('additive'):
            image = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
            output = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
            emission = nt.nodes.new('ShaderNodeEmission')
            transparent = nt.nodes.new('ShaderNodeBsdfTransparent')
            add = nt.nodes.new('ShaderNodeAddShader')
            nt.links.new(image.outputs['Color'], emission.inputs['Color'])
            nt.links.new(emission.outputs[0], add.inputs[0])
            nt.links.new(transparent.outputs[0], add.inputs[1])
            nt.links.new(add.outputs[0], output.inputs['Surface'])
            if hasattr(mat, 'surface_render_method'):
                mat.surface_render_method = 'DITHERED'
        elif not info['alpha']:
            for node in nt.nodes:
                if node.type == 'TEX_IMAGE':
                    node.image.alpha_mode = 'NONE'

    def fill(me, verts, faces, mesh):
        me.clear_geometry()
        me.from_pydata(verts.tolist(), [], faces)
        me.update()
        for attr, vecs in (('gameT', mesh.tangents), ('gameB', mesh.bitangents)) if mesh.tangents else ():
            layer = me.attributes.get(attr) or me.attributes.new(attr, 'FLOAT_VECTOR', 'POINT')
            layer.data.foreach_set('vector', np.asarray(vecs, np.float32).ravel())
        uv = me.uv_layers.new(name='UVMap')
        for loop in me.loops:
            uv.data[loop.index].uv = mesh.uv[loop.vertex_index]
        if mesh.name.upper() in ('DWARF', 'DWARF01', 'BODY', 'HEAD1', 'HEAD2', 'GOAT_L', 'GOAT_R'):
            me.shade_smooth()

    for job in args['jobs']:
        name = stem(job)
        final = out / (name + ('.png' if job['kind'] == 'still' else '.gif'))
        if final.exists() and not args['force']:
            continue
        e = catalog.BY_KEY[job['unit']]
        both = {side: parts(e, job['variant'], job['pose'], side) for side in ('before', 'after')}
        # Full-clip bounds prevent a death/build/extreme attack frame escaping the shared camera.
        bound_key = (job['unit'], job['variant'], job['pose'])
        if bound_key not in bounds:
            lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
            count = max(m.anim.frames for parts_ in both.values() for _, m, _ in parts_)
            for frame in range(count):
                fraction = frame / max(1, count - 1)
                for parts_ in both.values():
                    for _, mesh, verts, faces in posed(parts_, fraction):
                        if faces and not material(mesh.bytes)['additive']:
                            visible = verts[list({v for tri in faces for v in tri})]
                            lo, hi = np.minimum(lo, visible.min(0)), np.maximum(hi, visible.max(0))
            assert np.isfinite(lo).all() and np.isfinite(hi).all(), name
            bounds[bound_key] = lo, hi
        lo, hi = bounds[bound_key]
        scene.clear()
        size = args['still_size'] if job['kind'] == 'still' else args['motion_size']
        render.rig((size * 2, size), 8)
        sc = bpy.context.scene
        sc.render.engine = 'CYCLES' if args['cycles'] else 'BLENDER_EEVEE_NEXT'
        sc.render.image_settings.file_format = 'PNG'
        sc.render.film_transparent = False
        centre = (lo + hi) / 2
        diameter = float(np.linalg.norm(hi - lo))
        camera = render.camera('pair', centre.tolist(), diameter * 2.3, 22, -38, 52)
        camera.data.type = 'ORTHO'
        # Orthographic scale is horizontal at this landscape aspect ratio.
        camera.data.ortho_scale = diameter * 2.35
        sc.camera = camera
        right = np.asarray(camera.rotation_euler.to_quaternion() @ Vector((1, 0, 0)))
        displacement = right * diameter * .59
        objects = {}
        for side, parts_ in both.items():
            shift = displacement * (-1 if side == 'before' else 1)
            for i, (state, mesh, verts, faces) in enumerate(posed(parts_, 0)):
                me = bpy.data.meshes.new(side + str(i))
                fill(me, verts + shift, faces, mesh)
                obj = bpy.data.objects.new(side + str(i), me)
                bpy.context.collection.objects.link(obj)
                swaps = catalog.texture_swaps(state, mesh.name)
                texmap = {}
                for texture in mesh.textures:
                    old = texture.lower()
                    selected = swaps.get(old, old)
                    texmap[old] = (data['textures'][selected]['output']
                                   if side == 'after' and selected in data['textures']
                                   else data['source_textures'][selected])
                additive(obj, mesh, texmap)
                objects[(side, i)] = obj
        frames = [0] if job['kind'] == 'still' else list(range(args['frames']))
        framepaths = []
        for frame in frames:
            fraction = frame / max(1, len(frames) - 1)
            for side, parts_ in both.items():
                shift = displacement * (-1 if side == 'before' else 1)
                for i, (_, mesh, verts, faces) in enumerate(posed(parts_, fraction)):
                    obj = objects[(side, i)]
                    fill(obj.data, verts + shift, faces, mesh)
            path = final if job['kind'] == 'still' else out / (name + '_%02d.png' % frame)
            sc.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            subprocess.run(['magick', str(path), '-background', '#171b21', '-gravity', 'north',
                '-splice', '0x30', '-font', '/System/Library/Fonts/Supplemental/Arial Bold.ttf', '-pointsize', '18', '-fill', 'white',
                '-annotate', '-' + str(size // 2) + '+5', 'Before',
                '-annotate', '+' + str(size // 2) + '+5', 'After', str(path)], check=True)
            framepaths.append(path)
        if job['kind'] == 'motion':
            subprocess.run(['magick', '-delay', str(frame_delay(job,len(framepaths))), '-loop', '0', *map(str, framepaths),
                            '-layers', 'Optimize', str(final)], check=True)
            for path in framepaths:
                path.unlink()
        print('PREVIEW OK', name, flush=True)
        # Each job owns its geometry/materials; retain source model/animation arrays only.
        scene.clear()
        for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
            for item in list(collection):
                if item.users == 0:
                    collection.remove(item)
    old = json.loads((FOLDER / 'animation-checks.json').read_text()) if (FOLDER / 'animation-checks.json').exists() else {}
    old.update({'/'.join(k): v for k, v in checks.items()})
    (FOLDER / 'animation-checks.json').write_text(json.dumps(old, indent=2) + '\n')


def gallery():
    records = []
    for e in catalog.ROSTER:
        for v in e['variants']:
            for pose in e['animations']:
                for kind, ext in (('still', '.png'), ('motion', '.gif')):
                    job = dict(unit=e['key'], variant=v['key'], pose=pose, kind=kind)
                    file = 'renders/' + stem(job) + ext
                    if (FOLDER / file).exists():
                        records.append(dict(**job, title=e['title'], upgrade=v['title'], file=file))
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Dwarven troops — redesign review</title><style>
body{margin:0;background:#161b20;color:#f0eadf;font:17px system-ui}main{max-width:1500px;margin:auto;padding:28px}
h1{font-size:32px}p{line-height:1.5;color:#c6c1b8}nav{display:flex;flex-wrap:wrap;gap:15px;margin:24px 0}
label{display:grid;gap:6px}select,button{font:inherit;color:inherit;background:#293038;border:1px solid #68717b;padding:10px}
figure{margin:0;background:#242a30;border:1px solid #48515a}img{display:block;width:100%;height:auto}.pair{display:grid;grid-template-columns:1fr 1fr;text-align:center;padding:15px;font-weight:600}figcaption{padding:16px}a{color:#e4bf80}small{color:#b5bfc9}
</style><main><h1>Dwarven troops — redesign review</h1><p>Original installed art on the left; proposed art on the right.
Both use the same authored animation, camera and lighting. The troop redesign is staged for review, not installed.</p>
<nav><label>Troop<select id="unit"></select></label><label>Equipment<select id="variant"></select></label>
<label>Pose<select id="pose"></select></label><label>View<select id="kind"></select></label></nav>
<figure><div class="pair"><span>Before</span><span>After</span></div><img id="image" alt="Paired troop preview"><figcaption id="caption"></figcaption></figure>
<p><small>Animation GIFs sample the complete source clip at its nominal duration; game speed modifiers are not simulated. Player-colour blending, particles, thrown projectiles and game lighting are not simulated. Separate Zealot source appearances do not establish runtime ExtraMesh selection. Wagon passengers retain their own visual states; armour applies to the wagon.</small></p>
<details><summary>Inherited animation limitations</summary><p>The original game data has several missing animation references, an empty Zealot idle clip, and incompatible standalone death references for the wagon's Phalanx passengers. Those source behaviours are unchanged. Available clips matching the troop rigs were checked frame by frame; incompatible or missing clips are recorded explicitly.</p></details>
<script>const rows=RECORDS;const ids=['unit','variant','pose','kind'];
function update(from=0){let filtered=rows;ids.forEach((id,index)=>{const el=document.getElementById(id);if(index>=from){const old=el.value;const values=[...new Set(filtered.map(r=>r[id]))];el.replaceChildren(...values.map(value=>{const r=filtered.find(r=>r[id]===value);const o=new Option(id==='unit'?r.title:id==='variant'?r.upgrade:value,value);return o}));if(values.includes(old))el.value=old;}filtered=filtered.filter(r=>r[id]===el.value)});const r=filtered[0];if(r){image.src=r.file;image.alt=r.title+' '+r.upgrade+' '+r.pose+' before and after';caption.textContent=r.title+' · '+r.upgrade+' · '+r.pose+' · '+r.kind;}}
ids.forEach((id,i)=>document.getElementById(id).addEventListener('change',()=>update(i+1)));update();</script></main></html>'''
    if NOTES is not None:
        start=html.index('<details>');end=html.index('</details>',start)+len('</details>')
        html=html[:start]+'<details><summary>Source and preview limitations</summary><p>'+NOTES+'</p></details>'+html[end:]
        html=html.replace('Separate Zealot source appearances do not establish runtime ExtraMesh selection. Wagon passengers retain their own visual states; armour applies to the wagon.','')
    (FOLDER / 'review.html').write_text(html.replace('RECORDS', json.dumps(records)).replace('Dwarven troops',TITLE))
    (FOLDER / 'previews.json').write_text(json.dumps(records, indent=2) + '\n')
    poster()


def poster():
    """A compact after-only overview; every paired original remains in the gallery."""
    from sagekit.pipeline import Render
    tiles=[]
    entries=[catalog.BY_KEY[k] for k in catalog.POSTER_KEYS] if hasattr(catalog,'POSTER_KEYS') else catalog.ROSTER[:9]
    for entry in entries:
        path=FOLDER/'renders'/(entry['key']+'_base_idle_still.png')
        if not path.exists():return
        w,h=map(int,subprocess.check_output(['magick','identify','-format','%w %h',str(path)]).split())
        tile=path.with_name(entry['key']+'_poster.jpg')
        subprocess.run(['magick',str(path),'-crop',f'{w//2}x{h-30}+{w//2}+30','+repage',
            '-resize','560x560!','-background','#171b21','-gravity','south','-splice','0x48',
            '-font',Render.FONT,'-pointsize','23','-fill','white','-annotate','+0+12',entry['title'],str(tile)],check=True)
        tiles.append(str(tile))
    subprocess.run(['magick','montage','-font',Render.FONT,*tiles,'-tile','3x3',
        '-geometry','560x608+5+5','-background','#171b21',str(FOLDER/'poster.jpg')],check=True)


def main():
    from sagekit.pipeline import blender_slot, game_running
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stills', action='store_true'); p.add_argument('--motion', action='store_true')
    p.add_argument('--unit', action='append', choices=list(catalog.BY_KEY))
    p.add_argument('--variant', action='append'); p.add_argument('--pose', action='append')
    p.add_argument('--all-variants', action='store_true', help='Animate every equipment combination')
    p.add_argument('--frames', type=int, default=12)
    p.add_argument('--still-size', type=int, default=850); p.add_argument('--motion-size', type=int, default=400)
    p.add_argument('--force', action='store_true'); p.add_argument('--cycles', action='store_true')
    p.add_argument('--gallery-only', action='store_true')
    p.add_argument('--timing-only', action='store_true', help='Refresh existing GIF delays from source clip headers')
    args = p.parse_args()
    if args.timing_only:
        gallery()
        for job in json.loads((FOLDER/'previews.json').read_text()):
            if job['kind']!='motion':continue
            path=FOLDER/job['file'];target=path.with_suffix('.timed.gif')
            count=int(subprocess.check_output(['magick','identify','-format','%n\n',str(path)]).splitlines()[0])
            subprocess.run(['magick',str(path),'-coalesce','-set','delay',str(frame_delay(job,count)),
                            '-layers','Optimize',str(target)],check=True)
            target.replace(path)
        return
    if args.gallery_only:
        gallery(); return
    if game_running():
        raise SystemExit('Close the game before rendering art.')
    if not args.stills and not args.motion:
        args.stills = args.motion = True
    assert args.frames >= 2 and min(args.still_size, args.motion_size) >= 64
    request = dict(vars(args), jobs=jobs(args))
    path = FOLDER / 'preview-request.json'; path.write_text(json.dumps(request))
    with blender_slot(), (FOLDER / 'preview.log').open('w') as log:
        subprocess.run([paths.BLENDER, '-b', '--python-exit-code', '1', '--python', str(RUN_SCRIPT), '--', str(path)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    gallery()
    print('Paired previews:', FOLDER / 'review.html')


if __name__ == '__main__':
    draw() if 'bpy' in sys.modules else main()
