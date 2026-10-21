# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes the job files (lists of pictures to draw) for the study's runs. Plain Python, no Blender. Each run is one Blender start, so jobs for one file go together.
#   base_street.json   the BASELINE: the road as it is (round 2), main camera 540 x 960 and close road camera 640 x 480, lighting A to E, dry / wet / heavy.
#   diag_street.json   the DIAGNOSIS: one setting changed at a time, wet 0.85 / 0.5, lighting A (close camera for all, main camera for the key ones).
#   base_lockout.json  the BASELINE in the film's lockout shot file (brazier glare), 540 x 960.
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'jobs')
os.makedirs(OUT, exist_ok=True)


def job(cam_label, camera, light, state, variant='baseline', args=None, w=540, h=960, samples=16, tag=None):
    name = f'{cam_label}_{light}_{state}' + (f'_{tag or variant}' if variant != 'baseline' else '')
    return dict(name=name, camera=camera, light=light, state=state, variant=variant, args=args or {}, w=w, h=h, samples=samples)


def write(name, masks, jobs):
    json.dump(dict(masks=masks, jobs=jobs), open(os.path.join(OUT, name), 'w'), indent=1)
    print(name, len(jobs), 'jobs')


if __name__ == '__main__':
    base = []
    for light, states in (('A', ('dry', 'wet', 'heavy')), ('C', ('dry', 'wet')), ('D', ('dry', 'wet')), ('E', ('dry', 'wet', 'heavy'))):
        for state in states:
            base.append(job('main', 'main', light, state))
    for light, states in (('A', ('dry', 'wet', 'heavy')), ('C', ('wet',)), ('D', ('wet',)), ('E', ('wet',))):
        for state in states:
            base.append(job('close', 'close_road', light, state, w=640, h=480, samples=24))
    write('base_street.json', [['main', 540, 960], ['close_road', 640, 480]], base)

    diag = []
    variants = [('normal_strength', {'strength': 3.0}, 'normal3'), ('normal_strength', {'strength': 6.0}, 'normal6'), ('relief_kept', {}, None), ('no_film', {}, None), ('dull_wet', {}, None),
                ('wet_roughness', {'value': 0.9}, 'rough09'), ('dry_tops', {'value': 1.0}, 'drytops1'), ('normal_off', {}, None), ('colour_flat', {}, None)]
    for v, a, tag in variants:
        diag.append(job('close', 'close_road', 'A', 'wet', v, a, w=640, h=480, samples=24, tag=tag))
    diag.append(job('close', 'close_road', 'A', 'w0.85p0.0', 'baseline', None, w=640, h=480, samples=24, tag='nopuddles'))
    diag[-1]['name'] = 'close_A_wet_nopuddles'
    diag.append(job('close', 'close_road', 'A', 'dry', 'colour_flat', {}, w=640, h=480, samples=24))
    diag.append(job('close', 'close_road', 'A', 'dry', 'normal_off', {}, w=640, h=480, samples=24))
    for v, a, tag in (('relief_kept', {}, None), ('no_film', {}, None), ('dull_wet', {}, None), ('normal_strength', {'strength': 3.0}, 'normal3'), ('normal_off', {}, None), ('colour_flat', {}, None)):
        diag.append(job('main', 'main', 'A', 'wet', v, a, tag=tag))
    diag.append(job('main', 'main', 'A', 'dry', 'colour_flat', {}))
    write('diag_street.json', [['main', 540, 960], ['close_road', 640, 480]], diag)

    lock = []
    for light, states in (('A', ('dry', 'wet', 'heavy')), ('C', ('wet',)), ('D', ('wet',)), ('E', ('wet',))):
        for state in states:
            lock.append(job('lockout', 'main', light, state))
    write('base_lockout.json', [['main', 540, 960]], lock)
