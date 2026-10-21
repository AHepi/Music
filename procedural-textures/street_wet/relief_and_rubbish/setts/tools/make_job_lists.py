# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes a JOB FILE for the study's picture runner (study/tools/b03_render_jobs.py): the list of pictures one Blender run should draw. The study's own
# b09_lighting_test_set.py can only write the two fixed sets; this one writes any list, so that several road variants can be tried in ONE Blender run
# (loading the street costs about a minute for the lockout file, so it pays to draw many pictures per run).
# A picture = a camera (main, close or lockout), a lighting (A to E), a state (dry, wet, heavy or "w0.85p0.5"), and a road variant with its settings (the variant
# "joints_layer" of joint_layer.py, or "baseline" = round 2 as it is). Its name is  <camera>_<light>_<state>  or  <camera>_<light>_<state>_<tag>.
# It also adds the puddle-mask pictures (a checking view, plain light) for every camera and wet state it draws, because the measure leaves puddle dots out.
# Use:  python3 -I make_job_lists.py SPEC.json
#   SPEC.json: {"folder": "/path/out", "kind": "street" or "lockout", "pictures": [{"cam": "main", "light": "A", "state": "wet", "tag": "v1", "variant": "joints_layer",
#               "args": {"darkness": 0.2}}, ...], "size": {"main": [540, 960]} (optional override of a camera's size/samples: [w, h, samples])}
#   or, to draw the WHOLE lighting test set (or the quick one) once for each of several road variants in one Blender run:
#              (a picture may carry its own "size": [w, h, samples]; with "set", a list "extra": [pictures] is added after the set)
#              {"folder": "/path/out", "kind": "street" or "lockout", "set": "full" or "quick", "variants": {"before": {"variant": "baseline"},
#               "after": {"variant": "joints_layer", "args": {...}}}}      (a picture is named <camera>_<light>_<state>_<variant tag>)
# Writes  <folder>/jobs_<kind>.json  and prints its path.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY_TOOLS = os.path.abspath(os.path.join(HERE, '..', '..', 'study', 'tools'))
sys.path.insert(0, STUDY_TOOLS)
sys.dont_write_bytecode = True
from b09_lighting_test_set import CAMERAS  # noqa: E402

AFTER_APPLY = os.path.join(HERE, 'register_variants.py')


def expand_set(spec):
    """Turns {"set": "full", "variants": {tag: {variant, args}}} into the plain list of pictures for the spec's file kind."""
    from b09_lighting_test_set import SETS
    pictures = []
    for tag, v in spec['variants'].items():
        for label, rows in SETS[spec['set']].items():
            if CAMERAS[label]['file'] != spec['kind']:
                continue
            for light, states in rows:
                for state in states:
                    pictures.append(dict(cam=label, light=light, state=state, tag=tag, variant=v.get('variant', 'baseline'), args=v.get('args', {})))
    return pictures


def make(spec):
    if 'set' in spec:
        spec = dict(spec, pictures=expand_set(spec) + spec.get('extra', []))
    folder = spec['folder']
    os.makedirs(folder, exist_ok=True)
    kind = spec['kind']
    masks, jobs, wet_seen = [], [], set()
    for p in spec['pictures']:
        cam = CAMERAS[p['cam']]
        assert cam['file'] == kind, (p, kind)
        w, h, samples = p.get('size') or spec.get('size', {}).get(p['cam'], [cam['w'], cam['h'], cam['samples']])
        if [cam['camera'], w, h] not in masks:
            masks.append([cam['camera'], w, h])
        name = f"{p['cam']}_{p['light']}_{p['state']}" + (f"_{p['tag']}" if p.get('tag') else '')
        jobs.append(dict(name=name, camera=cam['camera'], light=p['light'], state=p['state'], variant=p.get('variant', 'baseline'), args=p.get('args', {}), w=w, h=h, samples=samples))
        if p['state'] != 'dry':
            wet_seen.add((p['cam'], p['state'], w, h))
    for label, state, w, h in sorted(wet_seen):
        cam = CAMERAS[label]
        jobs.append(dict(name=f'{label}_A_{state}_puddlemask', camera=cam['camera'], light='A', state=state, variant='show_masks', args={}, w=w, h=h, samples=4))
    path = os.path.join(folder, f'jobs_{kind}.json')
    json.dump(dict(masks=masks, jobs=jobs, after_apply=AFTER_APPLY), open(path, 'w'), indent=1)
    return path


if __name__ == '__main__':
    print(make(json.load(open(sys.argv[1]))))
