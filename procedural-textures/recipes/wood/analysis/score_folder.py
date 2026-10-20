# What this does (plain words): scores one baked wood folder (colour.png, height.png, normal.png) with BOTH project tools and writes the numbers to
# <folder>/score.json plus a difference sheet <folder>/diff_sheet.png and the "same kind" sheet <folder>/kind_sheet.png.
# Use: python3 -I score_folder.py FOLDER [--no-sheets]. Plain Python; it reads the reference pictures only to compare.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score_tools as st
folder = sys.argv[1]
sheets = '--no-sheets' not in sys.argv
report = st.score_folder(folder, texture=True, sheet=os.path.join(folder, 'diff_sheet.png') if sheets else None)
if sheets:
    st.tc.make_sheet('wood', folder, os.path.join(folder, 'kind_sheet.png'))
json.dump(report, open(os.path.join(folder, 'score.json'), 'w'), indent=1)
keys = ['colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'texture_compare_overall', 'seam_ratio']
print(json.dumps({k: report.get(k) for k in keys}))
