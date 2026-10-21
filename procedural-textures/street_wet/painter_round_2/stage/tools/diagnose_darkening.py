"""What this file does (plain words): finds WHY the film's stage shows a dark painting darker than it was painted. It uses finish_model.py (a Python copy of the stage's finishing step) and three kinds of evidence:
  A. does the copy explain the stage? It is run on three paintings whose stage pictures were really drawn: the first test's wet painting and the film's own dry painting (first test stills, read only) and the new wet front painting
     (this step's "before" still). The road's brightness arriving over its painted brightness is compared (the real stage against the copy), and so is the picture dot by dot.
  B. which step of the finish causes how much? On the new wet front painting the copy is run with each step switched off on its own, and with them switched off one after the other, and the road's arriving brightness is listed.
  C. the "painted value -> arriving value" table for a plain grey ramp, at the middle of the frame and at the road's usual place, with the film's look and with the steps switched off (same numbers the first test listed: 0.08 -> 0.02 ...).
Writes numbers/diagnosis_model.json and prints a printout. Run: python3 -I tools/diagnose_darkening.py
"""
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from finish_model import finish, lum, vignette_factor, srgb_to_lin, lin_to_srgb, aces, W, H
P = lambda *a: os.path.join(HERE, *a)
from stage_common import central, central_mask, masks, er, load01, stage01, TEST1, FILM, k
M = masks(TEST1 + 'alignment/facts_surfaces/')
road = er(central_mask(M['road'])); walls = er(central_mask(M['walls']))


out = {}
printout = []
def say(s=''):
    print(s); printout.append(s)

# ---------------------------------------------------------------- A. does the copy explain the stage?
cases = [('film_dry_painting', FILM + 'lockout-painted.jpg', TEST1 + 'stage/stills/dry_projector/still-6.00.jpg'),
         ('first_test_wet_painting', TEST1 + 'pictures/wet_painting_lined_up.png', TEST1 + 'stage/stills/wet_projector/still-6.00.jpg')]
new_still = P('stills/before/wet_projector/still-6.00.jpg')
if os.path.exists(new_still):
    cases.append(('new_wet_front_painting', P('../paint/front_painting_final.png'), new_still))
A = {}
say('A. does the Python copy of the finishing step explain the stage picture?  (road, plate view; "arrives" = stage brightness / painted brightness)')
for name, ppath, spath in cases:
    painting = central(load01(ppath)); stage = stage01(spath)
    pred = finish(painting)
    a, b, c = lum(painting), lum(stage), lum(pred)
    bs, cs = cv2.GaussianBlur(b, (0, 0), 3), cv2.GaussianBlur(c, (0, 0), 3)
    A[name] = {'painted_road_mean': float(a[road].mean()), 'stage_road_mean': float(b[road].mean()), 'copy_road_mean': float(c[road].mean()),
               'arrives_real_stage': float(b[road].mean() / a[road].mean()), 'arrives_in_the_copy': float(c[road].mean() / a[road].mean()),
               'copy_vs_stage_mean_abs_difference_blurred_road': float(np.abs(bs - cs)[road].mean()),
               'copy_vs_stage_correlation_blurred_road': float(np.corrcoef(bs[road], cs[road])[0, 1]),
               'copy_vs_stage_whole_picture_mean_abs_difference_blurred': float(np.abs(bs - cs).mean())}
    say(f"  {name:26s} painted {a[road].mean():.3f}  real stage {b[road].mean():.3f}  copy {c[road].mean():.3f}   arrives: real {b[road].mean() / a[road].mean():.3f}, copy {c[road].mean() / a[road].mean():.3f}"
        f"   copy vs stage: blurred difference {np.abs(bs - cs)[road].mean():.4f}, likeness {np.corrcoef(bs[road], cs[road])[0, 1]:.3f}")
out['A_does_the_copy_explain_the_stage'] = A

# ---------------------------------------------------------------- B. which step causes how much (new wet front painting)
painting = central(load01(P('../paint/front_painting_final.png')))
pl = lum(painting)[road].mean()
def arrives(look, painting=painting):
    o = finish(painting, look, with_grain=True)
    return float(lum(o)[road].mean() / lum(painting)[road].mean())
B = {'painted_road_mean': float(pl)}
steps = [('everything as the film has it (lockout look)', {}),
         ('only the filmic curve (ACES) off', dict(filmic=0.0)),
         ('only contrast 1.04 -> 1.0', dict(contrast=1.0)),
         ('only lift 0.015 -> 0', dict(lift=0.0)),
         ('only the cool/warm tint off', dict(tintAmount=0.0)),
         ('only the dark frame edge (vignette 0.3) off', dict(vignette=0.0)),
         ('only grain off', dict(grain=0.0)),
         ('ACES off and contrast 1.0 and lift 0', dict(filmic=0.0, contrast=1.0, lift=0.0)),
         ('ACES off, contrast 1.0, lift 0, tint off', dict(filmic=0.0, contrast=1.0, lift=0.0, tintAmount=0.0)),
         ('all of those and no frame edge (the painting passed through untouched)', dict(filmic=0.0, contrast=1.0, lift=0.0, tintAmount=0.0, vignette=0.0, grain=0.0))]
say(); say('B. which step of the finish costs how much?  (new wet front painting, road, plate view; the copy; painted road mean %.3f)' % pl)
B['steps'] = []
for label, look in steps:
    v = arrives(look); B['steps'].append({'what': label, 'look_changes': look, 'road_arrives_over_painted': v}); say(f"  {v:.3f}   {label}")
# one after the other, from the film's look
say('  -- switching the steps off one after the other (running ratio):')
B['one_after_the_other'] = []
run = {}
for label, change in (('ACES off', dict(filmic=0.0)), ('+ contrast 1.0', dict(contrast=1.0)), ('+ lift 0', dict(lift=0.0)), ('+ tint off', dict(tintAmount=0.0)), ('+ frame edge off', dict(vignette=0.0))):
    run.update(change); v = arrives(dict(run)); B['one_after_the_other'].append({'what': label, 'road_arrives_over_painted': v}); say(f"     {v:.3f}   {label}")
# painted-value bins: how much of the road's own light values lie where the curve crushes
road_vals = lum(painting)[road]
B['road_painted_value_shares'] = {'under_0.10': float((road_vals < 0.10).mean()), '0.10_to_0.20': float(((road_vals >= 0.10) & (road_vals < 0.20)).mean()), '0.20_to_0.30': float(((road_vals >= 0.20) & (road_vals < 0.30)).mean()),
                                  '0.30_to_0.50': float(((road_vals >= 0.30) & (road_vals < 0.50)).mean()), 'over_0.50': float((road_vals >= 0.50).mean())}
say('  shares of the wet road by painted brightness: ' + json.dumps({a: round(b_, 3) for a, b_ in B['road_painted_value_shares'].items()}))
out['B_which_step_costs_how_much'] = B

# ---------------------------------------------------------------- C. painted value -> arriving value, grey ramp
levels = [0.03, 0.05, 0.08, 0.10, 0.13, 0.17, 0.20, 0.24, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
ramp = np.array(levels)[None, :, None] * np.ones((1, len(levels), 3))
v0 = vignette_factor(1, 1, 0.3) if False else None
def table(look, with_edge):
    # a picture that is one grey per column, drawn at the frame's middle (no frame-edge darkening) or at the road's usual place (the road's mean vignette factor)
    img = np.ones((1, len(levels), 3)) * np.array(levels)[None, :, None]
    L = dict(look or {}); L['vignette'] = 0.0
    o = finish(img, L, with_grain=False)[0, :, 0]
    if with_edge: o = o * edge_at_road
    return o
vf = vignette_factor(H, W, 0.3)
edge_at_road = float(vf[road].mean())
C = {'painted_levels': levels, 'road_mean_frame_edge_factor': edge_at_road}
say(); say('C. painted grey -> arriving grey (the copy of the finish; grey ramp; "at the middle" = no frame-edge darkening; "on the road" = with the road\'s average frame-edge factor %.3f)' % edge_at_road)
rows = [('film look, at the middle', {}, False), ('film look, on the road', {}, True), ('ACES off (contrast 1.04, lift 0.015 stay), on the road', dict(filmic=0.0), True),
        ('ACES off, contrast 1.0, lift 0, on the road', dict(filmic=0.0, contrast=1.0, lift=0.0), True)]
say('     painted   ' + ' '.join(f'{l:5.2f}' for l in levels))
C['rows'] = []
for label, look, edge in rows:
    o = table(look, edge)
    C['rows'].append({'what': label, 'arrives': [round(float(x), 4) for x in o]})
    say(f'     {label[:48]:48s}' + ' '.join(f'{x:5.2f}' for x in o))
out['C_painted_to_arriving_grey_table'] = C
json.dump(out, open(P('numbers/diagnosis_model.json'), 'w'), indent=1)
open(P('numbers/diagnosis_model_printout.txt'), 'w').write('\n'.join(printout) + '\n')
