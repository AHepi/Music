# What this does (plain words): ANALYSIS. Measures the numbers the wood SAMPLER needs to invent new boards, cracks, knots, splatters and pebbles of the same kind:
# board heights and gap wobble, how many cracks per megapixel and how long / wide / wavy they are, how many of them lie along the gaps, the knot sizes and ring
# tones, the splatter cloud sizes and counts, the pebble sizes. Reads analysis results (layout_fit.json, cracks_fitted.json) only. Output: sampler_stats.json.
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
fit = json.load(open(os.path.join(HERE, 'layout_fit.json')))
cracks = json.load(open(os.path.join(HERE, 'cracks_fitted.json')))
MP = 1254 * 1254 / 1e6
out = {}
lines = np.array(fit['gap_lines']['lines'], float)
tops = lines.mean(axis=1)
heights = np.diff(np.concatenate([tops, [tops[0] + 1254]]))
out['board_heights'] = {'values': [round(float(h)) for h in heights], 'log_mean': round(float(np.log(heights).mean()), 3), 'log_sd': round(float(np.log(heights).std()), 3), 'count': len(heights)}
dev = lines - lines.mean(axis=1, keepdims=True)
out['gap_wobble'] = {'sd': round(float(dev.std()), 2), 'max': round(float(np.abs(dev).max()), 1)}
widths = np.array(fit['gap_widths'], float)
out['gap_width'] = {'median': round(float(np.median(widths)), 2), 'sd': round(float(widths.std()), 2), 'min': round(float(widths.min()), 1), 'max': round(float(widths.max()), 1)}
long_lines = [c for c in cracks if c['length'] >= 25]
L = np.array([c['length'] for c in long_lines]); Wd = np.array([c['mean_width'] for c in long_lines])
gap_y = np.array(tops)
def near_gap(c):
    ys = np.array([p[1] for p in c['pts']], float).mean()
    return float(np.min(np.abs(((ys - gap_y + 627) % 1254) - 627))) < 22
ng = np.array([near_gap(c) for c in long_lines])
turn = []
for c in long_lines:
    p = np.array(c['pts'], float)
    if len(p) >= 3:
        ang = np.arctan2(np.diff(p[:, 1]), np.abs(np.diff(p[:, 0])) + 1e-9)
        turn.append(float(np.abs(ang).mean()))
out['cracks'] = {'per_megapixel_length_25_plus': round(len(long_lines) / MP, 1), 'length_log_mean': round(float(np.log(L).mean()), 3), 'length_log_sd': round(float(np.log(L).std()), 3),
                 'width_log_mean': round(float(np.log(np.maximum(Wd, 1.0)).mean()), 3), 'width_log_sd': round(float(np.log(np.maximum(Wd, 1.0)).std()), 3),
                 'share_along_gaps': round(float(ng.mean()), 3), 'mean_abs_angle_radians': round(float(np.mean(turn)), 4), 'corners_per_100_dots': round(float(np.mean([len(c['pts']) / c['length'] * 100 for c in long_lines])), 2)}
out['knots'] = {'count': len(fit['knots']), 'rx': [k['rx'] for k in fit['knots']], 'ry': [k['ry'] for k in fit['knots']], 'ring_lab_templates': [k['ring_lab_outer_last'] for k in fit['knots']]}
clouds = fit['blob_clouds']
out['blob_clouds'] = {'count': len(clouds), 'per_megapixel': round(len(clouds) / MP, 1), 'n_log_mean': round(float(np.log([c['n'] for c in clouds]).mean()), 3), 'n_log_sd': round(float(np.log([c['n'] for c in clouds]).std()), 3),
                      'spread_x_median': float(np.median([c['spread_x'] for c in clouds])), 'spread_y_median': float(np.median([c['spread_y'] for c in clouds])),
                      'r_min_median': float(np.median([c['r_min'] for c in clouds])), 'r_max_median': float(np.median([c['r_max'] for c in clouds])), 'single_blobs_total': fit['blob_stats']['count']}
out['pebbles'] = fit['pebbles']
json.dump(out, open(os.path.join(HERE, 'sampler_stats.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ('knots', 'pebbles')}, indent=1))
