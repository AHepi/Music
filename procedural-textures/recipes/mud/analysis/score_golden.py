# What this does (plain words): scores a baked folder against the golden-puddle mud picture (colour only: there are no height or normal maps for it) with both project tools, and writes
# score.json plus the two sheets. Use: python3 -I score_golden.py FOLDER. Plain Python; it reads the reference picture only to compare.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import score_tools as st
folder = sys.argv[1]
report = st.score_folder(folder, reference='mud_golden', texture=True, sheet=os.path.join(folder, 'diff_sheet.png'))
st.tc.make_sheet('mud_golden', folder, os.path.join(folder, 'kind_sheet.png'))
json.dump(report, open(os.path.join(folder, 'score.json'), 'w'), indent=1)
keys = ['colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'tier_reached', 'texture_compare_overall', 'seam_ratio']
print(json.dumps({k: report.get(k) for k in keys}))
