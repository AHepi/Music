# What this does: tests ways to get brush-streak looks: our own seamless streaky noise (different feature counts across u and v), seamless stretched
# cells as brush dabs, the Wave texture, the Gabor texture and a plain stretched Noise via Mapping. For each it shows what the settings do and checks
# whether the tile repeats (strict periodicity test) so the builders know which are safe for seamless tiles.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
import recipe_tools as rt

BASE = os.path.join(hp.OUT, 'pictures')
hp.SAMPLES = 4
period = {}

def streak_colour(scale_u, scale_v, steps=0, detail=2.0, warp=0.0, name='streak', cells=False, palette=hp.SLATE_PALETTE, randomness=1.0):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    src = ('in', 'Vector')
    if warp > 0:
        hp.instance(w, hp.warp_vector_group(), 'warp', x=0, Amount=warp, Scale=4.0); w.link('in', 'Vector', 'warp', 'Vector'); src = ('warp', 'Vector')
    hp.instance(w, hp.anisotropic_noise_group(f'{name} streaky'), 'noise', x=1, **{'Scale__U': scale_u, 'Scale__V': scale_v, 'Detail': detail, 'Randomness': randomness})
    w.link(*src, 'noise', 'Vector')
    if cells:
        hp.cell_random(w, 'pick', 'noise', 'Color', 0.0, x=2)
        hp.palette_ramp(w, 'palette', palette, x=3); w.link('pick', 'Value', 'palette', 'Fac')
    else:
        w.add('ShaderNodeMapRange', 'stretch', x=2, clamp=True)
        w.nodes['stretch'].inputs['From Min'].default_value = 0.30; w.nodes['stretch'].inputs['From Max'].default_value = 0.70
        w.link('noise', 'Fac', 'stretch', 'Value')
        hp.palette_ramp(w, 'palette', palette, x=3)
        if steps:
            w.add('ShaderNodeMapRange', 'steps', x=2, y=-1, interpolation_type='STEPPED', clamp=True)
            w.nodes['steps'].inputs['Steps'].default_value = float(steps)
            w.link('stretch', 'Result', 'steps', 'Value'); w.link('steps', 'Result', 'palette', 'Fac')
        else:
            w.link('stretch', 'Result', 'palette', 'Fac')
    w.link('palette', 'Color', 'out', 'Colour')
    return tree

# 1) stretch ratio sweep (long in v = vertical streaks), keep 36 features across u
vals = [(36, 36), (36, 18), (36, 9), (36, 4.5), (36, 2.25)]
labels = [f'U {u} / V {v}  (x{u / v:g} long)' for u, v in vals]
arrays = hp.sweep(lambda i: streak_colour(*vals[i], steps=0, name=f'st{i}'), list(range(len(vals))), os.path.join(BASE, 'c04_stretch_smooth'), labels=labels, size=320, title='Streaky noise: Scale V lower than Scale U = vertical streaks (smooth)', cell=250)
arrays = hp.sweep(lambda i: streak_colour(*vals[i], steps=5, name=f'stp{i}'), list(range(len(vals))), os.path.join(BASE, 'c04_stretch_painted'), labels=labels, size=320, title='Same, painted: 5 flat levels with the slate palette', cell=250)
# 2) wood-like: long in u
vals2 = [(4, 40), (3, 60), (2, 90)]
arrays = hp.sweep(lambda i: streak_colour(*vals2[i], steps=5, detail=3.0, name=f'wd{i}', palette=[('#1c1513', 7.3), ('#39261b', 9.1), ('#3e322e', 15.4), ('#51392b', 15.2), ('#57473f', 19.8), ('#6c4b36', 12.3), ('#715b4d', 13.2), ('#926a4d', 7.7)]), list(range(len(vals2))), os.path.join(BASE, 'c04_horizontal_streaks_wood'), labels=[f'U {u} / V {v}' for u, v in vals2], size=320, title='Horizontal streaks (wood palette): long in u', cell=250)
# 3) detail sweep on streaky noise
dv = [0, 1, 2, 4, 6]
arrays = hp.sweep(lambda d: streak_colour(30, 5, steps=6, detail=d, name=f'sd{d}'), dv, os.path.join(BASE, 'c04_streak_detail'), labels=[f'Detail {d}' for d in dv], size=320, title='Streaky noise: Detail (U 30, V 5, 6 levels)', cell=250)
# 4) brush dabs: stretched cells
vals3 = [(14, 14), (14, 7), (14, 3.5), (20, 4), (8, 2)]
arrays = hp.sweep(lambda i: streak_colour(*vals3[i], cells=True, name=f'dab{i}'), list(range(len(vals3))), os.path.join(BASE, 'c04_brush_dabs'), labels=[f'cells U {u} / V {v}' for u, v in vals3], size=320, title='Stretched cells as brush dabs (palette per cell)', cell=250)
arrays = hp.sweep(lambda i: streak_colour(14, 4, cells=True, warp=[0, 0.01, 0.03, 0.06][i], name=f'dabw{i}'), list(range(4)), os.path.join(BASE, 'c04_brush_dabs_warped'), labels=[f'dab cells + warp {a}' for a in [0, 0.01, 0.03, 0.06]], size=320, title='Brush dabs with domain warp', cell=250)

# 5) other streak sources (not seamless unless said)
def wave_group(scale=1.5708, distortion=0.0, direction='Y', profile='SIN', detail=0.0, name='wave'):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    w.add('ShaderNodeTexWave', 'wave', x=0, wave_type='BANDS', bands_direction=direction, wave_profile=profile, Scale=scale, Distortion=distortion, Detail=detail)
    w.link('in', 'Vector', 'wave', 'Vector'); w.link('wave', 'Color', 'out', 'Colour'); return tree
def gabor_group(orientation=0.0, frequency=2.0, anisotropy=1.0, scale=8.0, name='gabor'):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    w.add('ShaderNodeTexGabor', 'g', x=0, gabor_type='2D', Scale=scale, Frequency=frequency, Anisotropy=anisotropy)
    w.nodes['g'].inputs['Orientation'].default_value = orientation
    w.link('in', 'Vector', 'g', 'Vector')
    w.add('ShaderNodeMapRange', 'mr', x=1, clamp=True); w.nodes['mr'].inputs['From Min'].default_value = -1.0; w.nodes['mr'].inputs['From Max'].default_value = 1.0
    w.link('g', 'Value', 'mr', 'Value')
    w.add('ShaderNodeCombineColor', 'c', x=2)
    for ch in ('Red', 'Green', 'Blue'): w.link('mr', 'Result', 'c', ch)
    w.link('c', 'Color', 'out', 'Colour'); return tree
def mapped_noise(sx, sy, name='mapped'):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    w.add('ShaderNodeMapping', 'map', x=0); w.nodes['map'].inputs['Scale'].default_value = (sx, sy, 1.0)
    w.link('in', 'Vector', 'map', 'Vector')
    w.add('ShaderNodeTexNoise', 'n', x=1, Scale=1.0, Detail=2.0); w.link('map', 'Vector', 'n', 'Vector'); w.link('n', 'Color', 'out', 'Colour'); return tree

arr = hp.sweep(lambda d: wave_group(distortion=d, name=f'wv{d}'), [0, 1, 3, 6, 12], os.path.join(BASE, 'c04_wave_distortion'), labels=[f'Wave Distortion {d}' for d in [0, 1, 3, 6, 12]], size=320, title='Wave texture (Bands, Y, Sine, Scale 1.5708): Distortion', cell=250)
arr = hp.sweep(lambda i: wave_group(profile=['SIN', 'SAW', 'TRI'][i], distortion=3.0, name=f'wp{i}'), [0, 1, 2], os.path.join(BASE, 'c04_wave_profile'), labels=['Sine', 'Saw', 'Triangle'], size=320, title='Wave profile (Distortion 3)', cell=250)
ov = [0.0, 0.7854, 1.5708, 2.356]
arr = hp.sweep(lambda i: gabor_group(orientation=ov[i], name=f'gb{i}'), list(range(4)), os.path.join(BASE, 'c04_gabor_orientation'), labels=[f'Orientation {o:.2f} rad' for o in ov], size=320, title='Gabor texture: Orientation (2D, Frequency 2, Anisotropy 1)', cell=250)
av = [1.0, 0.7, 0.4, 0.0]
arr = hp.sweep(lambda i: gabor_group(anisotropy=av[i], name=f'ga{i}'), list(range(4)), os.path.join(BASE, 'c04_gabor_anisotropy'), labels=[f'Anisotropy {a}' for a in av], size=320, title='Gabor: Anisotropy (1 = all bands one way, 0 = every way)', cell=250)
fv = [0.5, 1.0, 2.0, 4.0]
arr = hp.sweep(lambda i: gabor_group(frequency=fv[i], name=f'gf{i}'), list(range(4)), os.path.join(BASE, 'c04_gabor_frequency'), labels=[f'Frequency {a}' for a in fv], size=320, title='Gabor: Frequency (bands across the stripe direction)', cell=250)
arr = hp.sweep(lambda i: mapped_noise(*[(8, 8), (8, 4), (8, 2), (8, 1), (8, 0.5)][i], name=f'mp{i}'), list(range(5)), os.path.join(BASE, 'c04_mapped_noise'), labels=['Mapping scale 8,8', '8,4', '8,2', '8,1', '8,0.5'], size=320, title='Noise streaked by Mapping Scale (NOT seamless)', cell=250)

# 6) periodicity
period['our streaky noise U30 V5'] = hp.periodicity_check(lambda: streak_colour(30, 5, steps=5, name='p1'), 'Colour', 192)
period['our stretched cells U14 V4'] = hp.periodicity_check(lambda: streak_colour(14, 4, cells=True, name='p2'), 'Colour', 192)
period['our streaky + warp 0.05'] = hp.periodicity_check(lambda: streak_colour(30, 5, steps=5, warp=0.05, name='p3'), 'Colour', 192)
period['Wave Y sine scale 1.5708 no distortion'] = hp.periodicity_check(lambda: wave_group(1.5708, 0.0, name='p4'), 'Colour', 192)
period['Wave Y sine scale 1.5708 distortion 3'] = hp.periodicity_check(lambda: wave_group(1.5708, 3.0, name='p5'), 'Colour', 192)
period['Wave Y sine scale 1.0 no distortion (non-whole cycles)'] = hp.periodicity_check(lambda: wave_group(1.0, 0.0, name='p6'), 'Colour', 192)
period['Gabor 2D'] = hp.periodicity_check(lambda: gabor_group(name='p7'), 'Colour', 192)
period['Noise with Mapping scale'] = hp.periodicity_check(lambda: mapped_noise(8, 2, name='p8'), 'Colour', 192)
for k, v in period.items(): print('periodicity', k, {a: round(b, 4) for a, b in v.items()})
json.dump(period, open(os.path.join(hp.OUT, 'data', 'c04_periodicity.json'), 'w'), indent=1)
