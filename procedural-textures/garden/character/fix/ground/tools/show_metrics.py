import json, sys
d = json.load(open(sys.argv[1]))
for k, v in d.items():
    print(k, 'ssim_vs_base', v.get('ssim_blur12_vs_base'), 'vs_integrated', v.get('ssim_blur12_vs_integrated'), '| lawn', v['lawn_box'], '| ver_fg', v['ver_fg_box'], '| sat', v['mean_sat'], 'med', v['pct'][3], 'p99', v['pct'][6], 'sat70', v['share_sat_above_0.70_outside_maple'])
    print('    energy', v['energy'])
