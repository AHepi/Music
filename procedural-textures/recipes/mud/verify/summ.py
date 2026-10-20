# verifier: print the key numbers of a pixel.json and texture.json in one line
import json, sys
f = sys.argv[1]
p = json.load(open(f + '/pixel.json')); t = json.load(open(f + '/texture.json'))
keys = ['colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached']
out = {k: p.get(k) for k in keys}
out['kind'] = t.get('overall')
out['seam'] = t.get('facts', {}).get('seam_ratio_candidate')
out['groups'] = t.get('groups')
print(f.split('/')[-1], json.dumps(out))
