# What this does (plain words): searches the settings of the traced description (how many patches, how loosely thick patches are outlined, how many palette colours)
# for the best picture at each size limit of the wood ladder (about 8, 64 and 512 kilobytes). Prints one line per try. Analysis only (reads the reference).
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import describe_tools as dt, preview as pv, score_tools as st
bgr = dt.load_reference(); state = dt.load_merge_state(bgr)
rows = []
tries = [(n, rule, pal) for rule in [(1.5, 5.0, 0.35), (2.5, 7.0, 0.55), (0.9, 3.0, 0.2)] for n in (60, 120, 250, 500, 900, 1600, 2600, 4000) for pal in (32,)]
for n, rule, pal in tries:
    t0 = time.time()
    regions, palette = dt.traced_regions(bgr, state, n, pal, rule)
    d = dt.traced_description(regions, palette, 'search')
    size = dt.write_description(d, '/tmp/search_m.json')
    pv.run('/tmp/search_m.json', '/tmp/search_m_out', 2, False)
    rr = st.score_folder('/tmp/search_m_out', texture=False)
    row = dict(n=n, rule=list(rule), palette=pal, kilobytes=round(size / 1024, 1), patches=len(regions), ssim=rr['colour_ssim'], dE=rr['colour_mean_delta_e'], edge=rr['edge_skill_2px'], hMAE=rr['height_mae_best_fit_levels'], normal=rr['normal_mean_angle_degrees'], tier=rr['tier_reached'], s=round(time.time() - t0))
    print(json.dumps(row), flush=True); rows.append(row)
    json.dump(rows, open(os.path.join(HERE, 'search_m_class.json'), 'w'), indent=1)
