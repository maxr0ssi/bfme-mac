"""Check every inventoried troop animation against staged rigs, without running the game.

python3 -B -m assets.dwarves.troops.motion_check
Uses Blender's existing OpenSAGE decoder; writes redesign/motion-checks.json only.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from sagekit import paths

FOLDER = Path(paths.BUILD)/'dwarves/troops/redesign'


def run(folder=FOLDER, roster=None):
    FOLDER=folder
    import numpy as np
    from assets.dwarves.porter.preview import animation
    from assets.dwarves.troops import catalog
    if roster is not None:catalog=roster
    from assets.dwarves.troops.posing import Model, assert_original_skin
    from sagekit.formats.w3d import chunks, _cstr
    from sagekit.formats.w3dpose import Skeleton

    data = json.loads((FOLDER/'build.json').read_text())
    report = dict(status='PASS', build_manifest_sha256=hashlib.sha256(
        (FOLDER/'build.json').read_bytes()).hexdigest(), models={}, clips={}, skipped=[],
        authored_route_exceptions=[], counts={})
    groups = {}
    for name, item in data['models'].items():
        old, new = Model(item['source'], item['skeleton']), Model(item['work'], item['skeleton'])
        assert old.w3d.meshes.keys() == new.w3d.meshes.keys(), name
        assert old.bones == new.bones, (name, 'rigid attachment bones')
        if not old.w3d.skeleton():
            assert Skeleton(new.data).pivots == old.skel.pivots, (name, 'embedded rig')
        assert old.skel.name, name
        key = repr(old.skel.pivots)
        group = groups.setdefault(key, dict(skel=old.skel, models=[], added=[], bones=[], sampled=False))
        group['models'].append((name, old, new))
        count, added = 0, 0
        for mesh, before in old.w3d.meshes.items():
            after = new.w3d.meshes[mesh]
            assert_original_skin(before,after)
            n = len(before.verts)
            bones = new.vertex_bones(mesh)
            # Equal local coordinates and bone indices under the identical skeleton prove
            # the original vertex transforms identical for every decoded frame, not a sample.
            assert after.verts[:n] == before.verts, (name, mesh, 'original vertices')
            assert bones[:n] == old.vertex_bones(mesh), (name, mesh, 'original bones')
            assert all(0 <= b < len(old.skel.pivots) for b in bones), (name, mesh)
            assert np.isfinite(np.asarray(after.verts)).all(), (name, mesh)
            group['added'].extend(after.verts[n:]);group['bones'].extend(bones[n:])
            count += n;added += len(after.verts)-n
        report['models'][name] = dict(hierarchy=old.skel.name, original_vertices=count,
            added_vertices=added, lod_parent=data['geometry'][name]['lod_parent'],
            embedded_hierarchy=not bool(old.w3d.skeleton()), posed_comparison_frames=0,
            all_frame_equality_proved=True)
    for group in groups.values():
        group['added'] = np.asarray(group['added'], dtype=float).reshape(-1, 3)
        group['bones'] = np.asarray(group['bones'], dtype=int)

    files = {Path(member.replace('\\', '/')).stem.lower(): FOLDER/'src'/Path(member.replace('\\', '/'))
             for member in data['source_hashes'] if member.lower().endswith('.w3d')}
    for name, refs in data['animations']['missing'].items():
        report['skipped'].append(dict(animation=name, reason='Authored reference absent from active archives',
                                      source_references=refs))
    frames = transforms = model_clip_pairs = added_positions = comparison_frames = 0
    for name, refs in data['animations']['files'].items():
        raw = files[name].read_bytes()
        headers = [raw[p+8:p+8+n] for t, off, size, _ in chunks(raw, 0, len(raw))
                   if t in (0x200, 0x280) for tag, p, n, _ in chunks(raw, off+8, off+8+size)
                   if tag in (0x201, 0x281)]
        if not headers:
            report['skipped'].append(dict(animation=name,
                reason='Unchanged source file is empty' if not raw else 'Unchanged source file has no animation header',
                source_bytes=len(raw), source_sha256=hashlib.sha256(raw).hexdigest(), source_references=refs))
            continue
        assert len(headers) == 1, (name, 'multiple animation headers')
        hierarchy = _cstr(headers[0][20:36]).upper()
        matches = [g for g in groups.values() if g['skel'].name.upper() == hierarchy]
        if not matches:
            report['skipped'].append(dict(animation=name, hierarchy=hierarchy,
                reason='Source animation has no matching staged troop rig', source_references=refs))
            continue
        clip = animation(raw)
        assert clip.frames > 0, name
        valid = [g for g in matches if all(0 <= b < len(g['skel'].pivots)
                                         for b in {k[0] for k in clip.keys} | set(clip.vis))]
        if not valid:
            report['skipped'].append(dict(animation=name, hierarchy=hierarchy,
                reason='Unchanged source animation uses bone indices outside every matching staged rig',
                source_references=refs))
            continue
        record = dict(hierarchy=hierarchy, frames=clip.frames,
                      models=[m[0] for g in valid for m in g['models']], decoded=True)
        report['clips'][name] = record
        model_clip_pairs += len(record['models'])
        frames += clip.frames
        for group in valid:
            skel = group['skel']
            for frame in range(clip.frames):
                pose = skel.pose(clip, frame)
                mats = np.asarray(pose[0]).reshape(-1, 3, 4)
                assert np.isfinite(mats).all(), (name, frame, 'bone matrices')
                assert len(pose[1]) == len(skel.pivots), (name, frame, 'visibility')
                transforms += len(skel.pivots)
                if len(group['added']):
                    selected = mats[group['bones']]
                    world = np.einsum('nij,nj->ni', selected[:, :, :3], group['added'])+selected[:, :, 3]
                    assert np.isfinite(world).all(), (name, frame, 'added vertices')
                    added_positions += len(world)
                # Numerical confirmation of the equality proof once per distinct rig/model;
                # avoid repeating unchanged body/LOD work across every alternate idle clip.
                if not group['sampled'] and frame in {0, clip.frames//2, clip.frames-1}:
                    for model_name, old, new in group['models']:
                        for mesh, original in old.w3d.meshes.items():
                            a = old.world(mesh, pose)
                            b = new.world(mesh, pose)[:len(original.verts)]
                            assert np.array_equal(a, b), (name, frame, model_name, mesh)
                        report['models'][model_name]['posed_comparison_frames'] += 1
                        comparison_frames += 1
            group['sampled'] = True
    # The passenger file authors the ground Phalanx death clip against A/B passenger rigs.
    # The ground clip is still tested against its correct ground rig above; do not silently
    # present the mismatched passenger route as animation support or invent a replacement.
    source = catalog.UNIT_DIR+'dwarvenbattlewagonphalanx.ini'
    for name, refs in data['animations']['files'].items():
        if source not in refs or name not in report['clips']:
            continue
        if 'die' not in name and 'dth' not in name:
            continue
        for model in ('duphalanxa_skn', 'duphalanxb_skn'):
            expected = report['models'][model]['hierarchy']
            actual = report['clips'][name]['hierarchy']
            if expected.upper() != actual:
                report['authored_route_exceptions'].append(dict(model=model, animation=name,
                    model_hierarchy=expected, animation_hierarchy=actual,
                    reason='Unchanged authored passenger death route has incompatible ground hierarchy'))
    unchecked = [name for name, m in report['models'].items() if not m['posed_comparison_frames']]
    assert not unchecked, ('Built model has no validated animation', unchecked)
    report['counts'] = dict(models=len(report['models']), distinct_rigs=len(groups),
        inventoried_available_clips=len(data['animations']['files']), validated_clips=len(report['clips']),
        decoded_frames=frames, model_clip_pairs=model_clip_pairs, bone_transforms=transforms,
        added_vertex_positions=added_positions, original_model_pose_comparisons=comparison_frames,
        missing_references=len(data['animations']['missing']),
        available_clips_skipped=len(report['skipped'])-len(data['animations']['missing']),
        incompatible_passenger_death_routes=len(report['authored_route_exceptions']))
    report['method'] = ('Every frame of every matching source clip is decoded; all bone matrices and added '
        'vertex positions are finite. Exact original local vertices, bone assignments, rigid bindings and '
        'skeletons prove original world positions unchanged for every frame. Numerical original/new world '
        'comparisons confirm first/middle/last frames once per rig/model, including LOD and embedded death rigs. '
        'No game or visual approval is implied.')
    (FOLDER/'motion-checks.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['counts'], indent=2), flush=True)


if __name__ == '__main__':
    if 'bpy' in sys.modules:
        run()
    else:
        from sagekit.pipeline import blender_slot, game_running
        if game_running():
            raise SystemExit('Close the game before checking animation data.')
        with blender_slot(), (FOLDER/'motion-checks.log').open('w') as log:
            subprocess.run([paths.BLENDER, '-b', '--python-exit-code', '1', '--python', str(Path(__file__).resolve())],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        result = json.loads((FOLDER/'motion-checks.json').read_text())
        print(result['status'], json.dumps(result['counts'], sort_keys=True))
        print(FOLDER/'motion-checks.json')
