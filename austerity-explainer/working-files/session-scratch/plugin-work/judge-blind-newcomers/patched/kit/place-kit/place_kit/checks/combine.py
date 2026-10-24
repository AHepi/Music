"""What this does: COMBINES builders' stage files safely. Parts of a place are built by different owners at the same time, each in a stage file (stage_<owner>.py with apply(options)); this runs
them one after another in the open scene, takes a fingerprint of the whole scene before and after each, and checks every change against ownership.json (ownership.py): who changed what they do not
own, new objects with no owner, shared node groups changed, frozen state changed. It also runs the whole chain a second time and says whether the scene came out the same (a stage must be
idempotent: it removes what it made before making it again). The order matters only if a stage is wrong, so the integrator runs the chain in plain order and in reverse and compares (the
`combine` verb with --order both does both from the same starting file). It needs Blender (bpy).
A concrete example: combine_stages(['stage_roads.py', 'stage_cottages.py'], owners) returns {'stages': [{'name': 'roads', 'added': 12, 'violations': []}, ...], 'violations': [], 'idempotent': True}.
"""
import importlib.util
import os
import time

from . import fingerprint, ownership


def _load(path):
    name = 'pk_stage_' + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'apply'):
        raise ValueError(f'{path} has no apply(options) function (a stage file must have one)')
    return module


def run_chain(stage_files, owners_spec, options=None):
    """Runs the stages in the order given; returns the per-stage reports and the final fingerprint."""
    stages, all_violations = [], []
    previous = fingerprint.fingerprint_scene()
    for path in stage_files:
        module = _load(path)
        owner = getattr(module, 'OWNER', os.path.splitext(os.path.basename(path))[0].replace('stage_', ''))
        began = time.time()
        module.apply(options or {})
        now = fingerprint.fingerprint_scene()
        result = ownership.diff(previous, now, owners_spec, actor=owner)
        stages.append({'name': owner, 'file': os.path.basename(path), 'seconds': round(time.time() - began, 2), 'added': len(result['added']), 'changed': len(result['changed']),
                       'deleted': len(result['deleted']), 'violations': result['violations'], 'warnings': result['warnings']})
        all_violations += [f'{owner}: {v}' for v in result['violations']]
        previous = now
    return stages, all_violations, previous


def same_scene(first, second):
    """True when two fingerprints describe the same scene: the same objects with the same meshes, places, owners, materials and modifiers, and the same materials."""
    same_objects = set(first['objects']) == set(second['objects']) and all(
        all(first['objects'][n].get(key) == second['objects'][n].get(key) for key in ('mesh', 'matrix', 'owner', 'slots', 'modifiers')) for n in first['objects'])
    return bool(same_objects and first['materials'] == second['materials'])


def combine_stages(stage_files, owners, order='plain', options=None):
    """Runs the chain (plain or reverse order), then runs it again to see whether it is idempotent. Returns the report (see the note at the top)."""
    files = list(stage_files)[::-1] if order == 'reverse' else list(stage_files)
    stages, violations, first = run_chain(files, owners, options)
    _, _, second = run_chain(files, owners, options)
    return {'order': order, 'stages': stages, 'violations': violations, 'idempotent': same_scene(first, second), 'fingerprint_objects': len(first['objects']),
            'fingerprint': {'objects': len(first['objects']), 'materials': len(first['materials'])}, '_final': first}


def combine_both(stage_files, owners, options=None):
    """Runs the chain in plain order and in reverse order, each from the same starting file (the open scene's own saved file is reopened between runs), and says whether the two scenes
    came out the same. The scene is left as the plain order made it. A stage that only works in one order is wrong: it should find its own inputs, not rely on the stage before it."""
    import bpy
    start = bpy.data.filepath
    if not start or not os.path.exists(start):
        raise ValueError('--order both needs the scene saved on disk (it is reopened between the two runs): give --scene FILE.blend')
    plain = combine_stages(stage_files, owners, 'plain', options)
    bpy.ops.wm.open_mainfile(filepath=start, load_ui=False)
    reverse = combine_stages(stage_files, owners, 'reverse', options)
    bpy.ops.wm.open_mainfile(filepath=start, load_ui=False)
    run_chain(list(stage_files), owners, options)             # leave the scene as the plain order made it
    different = not same_scene(plain['_final'], reverse['_final'])
    for report in (plain, reverse):
        report.pop('_final', None)
    return {'order': 'both', 'plain': plain, 'reverse': reverse, 'violations': plain['violations'] + [f'(reverse order) {v}' for v in reverse['violations']],
            'idempotent': bool(plain['idempotent'] and reverse['idempotent']), 'order_independent': not different, 'stages': plain['stages']}
