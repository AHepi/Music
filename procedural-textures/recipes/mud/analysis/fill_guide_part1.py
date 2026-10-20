# What this does (plain words): helper for fill_guide.py: loads every number file and builds the markdown tables (ladder, classes, golden, variation, area, resolution, seam) so the
# guide text never has a number typed by hand. Plain Python.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
def load(p, default=None):
    p = os.path.join(ROOT, p)
    return json.load(open(p)) if os.path.exists(p) else default
R = load('final_report.json', {})
def f(v, nd=3):
    if v is None: return 'no map' if False else 'n/a'
    if isinstance(v, str): return v
    return f'{v:.{nd}f}'.rstrip('0').rstrip('.') if nd else str(int(v))
def kb(b):
    return 'n/a' if b is None else (f'{b / 1000:.1f} KB')
NAMES = {'R0_flat_ground': 'flat ground only', 'R1_plus_puddle_outlines': '+ 8 puddle outlines (coarse)', 'R2_plus_40_big_stones': '+ 40 biggest stones (outline only)', 'R3_plus_ruts': '+ wheel ruts (34 curves)',
         'S_layout_ruts_clods': 'S class: smaller layout + ruts + 14,000 clods', 'M_puddle_tones_stone_faces': 'M class: puddle water tones, 590 stones with faces, ruts, clods',
         'L2_traced_ground_2000_patches': 'traced ground, 2000 patches + fine puddles and stones', 'L_traced_ground_5000_patches': 'traced ground, 5000 patches + fine puddles and stones',
         'L_final_traced_ground_plus_corrections': 'L class (final): traced ground 5000 + corrections last'}
def table(rows, golden=False, names=None):
    head = '| layer or class | description size | tier | SSIM | colour difference | edge skill | height error | normal angle | same-kind score | bake seconds |\n|---|---|---|---|---|---|---|---|---|---|\n'
    body = ''
    for name, r in rows.items():
        body += f"| {(names or NAMES).get(name, name)} | {kb(r.get('description_bytes'))} | {r.get('tier_reached')} | {f(r.get('colour_ssim'))} | {f(r.get('colour_mean_delta_e'), 2)} | {f(r.get('edge_skill_2px'))} | {f(r.get('height_mae_best_fit_levels'), 1)} | {f(r.get('normal_mean_angle_degrees'), 1)} | {f(r.get('texture_compare_overall'))} | {f(r.get('bake_seconds'), 1)} |\n"
    return head + body
