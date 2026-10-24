# Writes the fix round's final dial values into the kit's look (presets/sooty_1926.json) and prints the table old -> new (the table goes into the recipe and the tuning log).
import json, sys
K = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/'
FINAL = {
    'soot': {'film_mult': 0.80, 'washed_share': 0.07, 'washed_pale': 0.5, 'edge_sharp': 0.55, 'grey_pull': 0.10, 'pale_warm': 1.0},
    'steps': {'white_cream': 1.0, 'white_value': 0.85},
    'dirt': {'ring_pale': 0.0, 'dip_dark': 0.12, 'film_max_share': 0.15},
    'groundcracks': {'open_joint_share': 0.07, 'open_depth_mm': 0.8, 'sett_disturb': 0.35},
    'growth': {'colour_gain': 0.55, 'colour_sat': 0.85, 'cushions_amount': 0.3, 'dead_grass_share': 0.08, 'weed_cover': 0.02, 'gutter_tuft_share': 0.10},
    'foot': {'salt_bloom': 0.008},
    'runoff': {'width_dots': 14.0, 'stain_value': 1.0, 'iron_rust': 0.9, 'leak_share': 0.3, 'source_share': 0.9, 'pair_share': 1.0},
    'iron': {'rust_bright': 1.4},
}
p = K + 'presets/sooty_1926.json'
look = json.load(open(p))
rows = []
for layer, kv in FINAL.items():
    for dial, new in kv.items():
        old = look['layers'].setdefault(layer, {}).get(dial)
        look['layers'][layer][dial] = new
        rows.append((layer, dial, old, new))
json.dump(look, open(p, 'w'), indent=1)
for r in rows:
    print('| %s | `%s` | %s | %s |' % r)
