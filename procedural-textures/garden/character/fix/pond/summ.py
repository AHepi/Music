# usage: summ.py NAME -> prints the metrics table of previews/NAME/metrics.json (fetches it first via dl.sh)
import json, sys, subprocess
name=sys.argv[1]
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/pond'
subprocess.run([D+'/dl.sh', D+'/previews/%s/metrics.json'%name, D+'/previews/%s/metrics.json'%name], capture_output=True)
m=json.load(open(D+'/previews/%s/metrics.json'%name))
print('%-14s %7s %7s %7s | detail: roof bridge grass maple sand wall rock | sat  p50 p99' % ('item','ssim','corr','lum'))
for k,v in m.items():
    de=v['detail_energy']
    print('%-14s %7.4f %7.4f %7.4f | %s | %.3f %.3f %.3f' % (k, v['ssim_blur12_vs_before'], v['corr_blur12_vs_before'], v['mean_lum'], ' '.join('%.2f'%b for a,b in de.items()), v['mean_saturation'], v['percentiles']['50'], v['percentiles']['99']))
for k,v in m.items():
    for rn,r in v.get('regions',{}).items():
        print('  %-14s %-10s ssim %.3f | lum %.3f (before %.3f) | R %.3f (before %.3f) | sat %.3f/%.3f | detail %.2f/%.2f' % (k, rn, r['ssim_blur12'], r['mean_lum_new'], r['mean_lum_before'], r['mean_rgb_new'][0], r['mean_rgb_before'][0], r['sat_new'], r['sat_before'], r['detail_new'], r['detail_before']))
