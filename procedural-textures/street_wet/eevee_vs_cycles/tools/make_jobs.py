# What this file does (plain words): writes the job files of the final pairs (run A = street copy: main street today / dry / wet and the cottage close view; run B = the film's lockout shot file).
# Use: python3 -I make_jobs.py
import json, os
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CY = 512      # Cycles samples (see the notes: 256 is almost the same, 512 is the least that leaves no visible blotches on the wet road at 100 %)
COT = dict(loc=[1.0, 1.0, 1.5], look=[4.15, 6.8, 1.6], fov=48)


def pair(name, camera, light, state, w, h, look='rubbish', ee_set=None, cycles=None, samples_cy=CY, **extra):
    e = dict(name=f'{name}_eevee', engine='eevee', camera=camera, light=light, state=state, w=w, h=h, samples=64, look=look, **extra)
    if ee_set:
        e['eevee_set'] = ee_set
    c = dict(name=f'{name}_cycles', engine='cycles', camera=camera, light=light, state=state, w=w, h=h, samples=samples_cy, look=look, **extra)
    if cycles:
        c['cycles'] = cycles
    return [e, c]


POOL = dict(shadow_pool_size='1024')
a = []
a += pair('main_today', 'main', 'A', 'today', 1080, 1920, look='today', ee_set=POOL)
a += pair('main_dry', 'main', 'A', 'dry', 1080, 1920, ee_set=POOL)
a += pair('main_wet', 'main', 'A', 'wet', 1080, 1920, ee_set=POOL)
a.append(dict(name='main_wet_puddlemask', camera='main', light='A', state='wet', w=1080, h=1920, samples=4, look='joints', view='puddles'))
a.append(dict(name='main_wet_dirt', camera='main', light='A', state='wet', w=1080, h=1920, samples=4, look='rubbish', view='dirt'))
a += pair('cottage_wet', 'cot_B', 'A', 'wet', 1600, 1200)
json.dump(dict(kind='street', masks=[['main', 1080, 1920]], ground_masks=[['main', 1080, 1920]], cameras={'cot_B': COT}, jobs=a), open(BASE + '/work/runA_jobs.json', 'w'), indent=1)

b = []
b += pair('lockout_wet', 'lockout', 'B', 'wet', 1536, 2730)
b.append(dict(name='lockout_wet_cycles_seed1', engine='cycles', camera='lockout', light='B', state='wet', w=1536, h=2730, samples=CY, look='rubbish', cycles=dict(seed=1)))
b += pair('lockout_wet_joints', 'lockout', 'B', 'wet', 1536, 2730, look='joints')
b += pair('lockout_wet_round2', 'lockout', 'B', 'wet', 1536, 2730, look='round2')
b.append(dict(name='lockout_wet_puddlemask', camera='lockout', light='B', state='wet', w=1536, h=2730, samples=4, look='joints', view='puddles'))
b.append(dict(name='lockout_wet_dirt', camera='lockout', light='B', state='wet', w=1536, h=2730, samples=4, look='rubbish', view='dirt'))
json.dump(dict(kind='lockout', masks=[['lockout', 1536, 2730]], ground_masks=[['lockout', 1536, 2730]], jobs=b), open(BASE + '/work/runB_jobs.json', 'w'), indent=1)
print(len(a), len(b))
