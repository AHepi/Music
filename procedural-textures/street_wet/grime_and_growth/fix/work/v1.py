# Variant V1 of the fix round: every dial the checkers' findings point at (first guess).
V0_NEW = {  # the kit's own defaults for dials that did not exist (or were not in the look) before this round: what the integrated look effectively used
    'dirt': {'ring_pale': 0.45, 'dip_dark': 0.12},
    'groundcracks': {'open_depth_mm': 3.0},
    'steps': {'white_cream': 0.0, 'white_value': 1.0},
    'growth': {'colour_sat': 1.0},
}
V1 = {
    'growth': {'colour_gain': 0.55, 'colour_sat': 0.9, 'cushions_amount': 0.3},
    'soot': {'washed_share': 0.07, 'washed_pale': 0.5, 'edge_sharp': 0.55, 'grey_pull': 0.10},
    'steps': {'white_cream': 1.0, 'white_value': 0.85},
    'dirt': {'ring_pale': 0.0},
    'groundcracks': {'open_joint_share': 0.07, 'open_depth_mm': 0.8, 'sett_disturb': 0.35},
}
def touched(*variants):
    t = []
    for v in variants:
        for l, kv in v.items():
            for d in kv:
                if (l, d) not in t:
                    t.append((l, d))
    return t
def merged(*dicts):
    out = {}
    for d in dicts:
        for l, kv in d.items():
            out.setdefault(l, {}).update(kv)
    return out

# ---- V2: V1 plus the second look at the walls (film back up so the walls do not go dark mush), warm steps and washed patches, dimmer plants with fewer pale tufts
V0_NEW['soot'] = {'pale_warm': 0.0}
V0_NEW['growth']['dead_grass_share'] = 0.15
V2 = merged(V1, {
    'soot': {'film_mult': 0.72, 'pale_warm': 1.0},
    'growth': {'colour_gain': 0.5, 'colour_sat': 0.85, 'dead_grass_share': 0.08},
    'steps': {'white_cream': 1.0, 'white_value': 0.85},
})
# run-off: streaks that can be seen from the camera (wider, rust-coloured under the pipe joints, only the heavy ones)
R1 = {'runoff': {'strength': 1.0, 'width_dots': 14.0, 'stain_value': 1.0, 'iron_rust': 1.0, 'leak_share': 0.45, 'source_share': 0.9, 'pair_share': 1.0}}

# ---- V3: film back up to 0.80, a few more plants outside puddles, smaller film patches, fewer wall-foot salt flecks, gentler run-off boost
V3 = merged(V2, {
    'soot': {'film_mult': 0.80},
    'growth': {'weed_cover': 0.016, 'gutter_tuft_share': 0.08},
    'dirt': {'film_max_share': 0.15},
    'foot': {'salt_bloom': 0.008},
    'runoff': {'strength': 1.0, 'width_dots': 14.0, 'stain_value': 1.0, 'iron_rust': 0.9, 'leak_share': 0.3, 'source_share': 0.9, 'pair_share': 1.0},
})
