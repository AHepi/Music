# What this does (plain words): quick "same kind of surface" tuning WITHOUT Blender. For each variant of the procedural gravel description it draws a picture
# with OpenCV, makes the height and normal from it with the generator's rule, and scores it with lib/texture_compare.py (the project's same-kind-of-surface
# tool). Used to choose between small changes (tone jitter, lump counts, brightness) before the slow real bake. Run: python3 -I tune_texture.py
import copy, json, os, subprocess, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
sys.path.insert(0, HERE)
import preview_tools as pt
import numpy_bake as nb
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def evaluate(desc, tag):
    picture, n, _, _ = pt.make_preview(desc, scale=2)
    folder = os.path.join(HERE, '..', 'scores', 'tmp_tune', tag)
    os.makedirs(folder, exist_ok=True)
    height, normal = nb.derive(picture, 10, 'central', 0.5)
    h = cv2.GaussianBlur(np.pad(height, 12, mode='wrap'), (0, 0), 0.8)[12:-12, 12:-12]
    h = (h - h.min()) / (h.max() - h.min())
    cv2.imwrite(os.path.join(folder, 'colour.png'), picture)
    cv2.imwrite(os.path.join(folder, 'height.png'), (h * 65535).astype(np.uint16))
    cv2.imwrite(os.path.join(folder, 'normal.png'), ((normal * 0.5 + 0.5) * 255).round().astype(np.uint8)[..., ::-1])
    out = os.path.join(folder, 'score.json')
    subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', 'texture_compare.py'), 'gravel', folder, '--json', out], capture_output=True)
    r = json.load(open(out))
    return {'overall': r['overall'], **r['groups'], 'scores': r['scores'], 'mean_lab': r['facts']['mean_lab_candidate'], 'corr_len': r['facts']['correlation_length_px_candidate'], 'shapes': n}


if __name__ == '__main__':
    base = json.load(open(sys.argv[1]))
    variants = {}
    variants['base'] = base
    v = copy.deepcopy(base); v['soil']['layers'][0]['jitter_tone'] = 7; v['soil']['layers'][1]['jitter_tone'] = 7; v['soil']['layers'][2]['jitter_tone'] = 7; v['stones']['tone_jitter'] = 5.0
    variants['more_tone_jitter'] = v
    w = copy.deepcopy(v)
    w['soil']['layers'][0]['count'] = int(w['soil']['layers'][0]['count'] * 0.55); w['soil']['layers'][1]['count'] = int(w['soil']['layers'][1]['count'] * 0.7)
    variants['fewer_fine_lumps'] = w
    x = copy.deepcopy(w)
    for c in x['stones']['classes']:
        c['rust'] = c.get('rust', 0.1) * 0.8
    x['soil']['tones'] = [[min(255, int(a * 1.12)) for a in t] for t in x['soil']['tones']]
    x['stones']['tones'] = [[min(255, int(a * 1.1) + 2) for a in t] for t in x['stones']['tones']]
    variants['lighter'] = x
    results = {}
    for name, d in variants.items():
        started = time.time()
        results[name] = evaluate(d, name)
        r = results[name]
        print(f"{name:20s} overall {r['overall']:.3f} colour {r['colour']:.3f} height {r['height']:.3f} normal {r['normal']:.3f} lab {r['mean_lab']} corr_len {r['corr_len']} ({time.time()-started:.0f}s)", flush=True)
    json.dump(results, open(os.path.join(HERE, '..', 'scores', 'tune_texture_round1.json'), 'w'), indent=1)
