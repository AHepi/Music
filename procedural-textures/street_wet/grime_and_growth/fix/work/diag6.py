import sys
sys.path.insert(0, '.')
from fixrun import job, run, full_dials
from v1 import V0_NEW, V1, V2, V3, touched, merged
extra = {'growth': {'weed_cover': 0.01, 'gutter_tuft_share': 0.05, 'cushions_amount': 0.6, 'cushion_cover': 0.008, 'wall_foot_share': 0.035, 'weeds_amount': 1.0}}
T = touched(V0_NEW, V1, V2, V3, extra)
variants = {
    'V3': {},
    'cov022': {'growth': {'weed_cover': 0.022, 'gutter_tuft_share': 0.10}},
    'cov03': {'growth': {'weed_cover': 0.03, 'gutter_tuft_share': 0.15}},
    'cov03c5': {'growth': {'weed_cover': 0.03, 'gutter_tuft_share': 0.15, 'cushions_amount': 0.5}},
    'cushcover': {'growth': {'weed_cover': 0.022, 'gutter_tuft_share': 0.10, 'cushion_cover': 0.016, 'cushions_amount': 0.5}},
    'orig_mix': {'growth': {'weed_cover': 0.01, 'gutter_tuft_share': 0.05, 'cushions_amount': 0.6}},
}
jobs = []
for name, ov in variants.items():
    d = full_dials(T, merged(V0_NEW, V3, ov)) if name != 'orig_mix' else full_dials(T, merged(V0_NEW, V3, ov))
    jobs.append(job(f'cnt_{name}', 'main', 'A', 'wet', size=(135, 240, 1), plate_height=2730, dials=d, pieces_json=True))
run('street', jobs, 'diag6')
