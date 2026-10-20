# What this does (plain words): gathers every measured number of the metal recipe (sizes, tiers, similarity, colour error, edge skill, height and normal errors,
# same-kind-of-surface score, seam tests, bake times, variation, area, resolution, transfer) into final_report.json. It only READS result files written by the other scripts.
import json, os
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..')); R=PROC+'/recipes/metal'
def jl(p):
    return json.load(open(p)) if os.path.exists(p) else None
report={'surface':'metal','classes':{},'rate_distortion':{}}
def entry(name):
    px=jl(f'{R}/scores/{name}_pixel.json'); tx=jl(f'{R}/scores/{name}_texture.json'); bk=jl(f'{R}/outputs/{name}/bake.json')
    if not px: return None
    size_file=f'{R}/description/{name}.json'
    return {'description_bytes':os.path.getsize(size_file) if os.path.exists(size_file) else None,'tier':px['tier_reached'],'colour_ssim':px['colour_ssim'],'colour_mean_delta_e':px['colour_mean_delta_e'],
            'edge_skill':px['edge_skill_2px'],'height_mae_best_fit_levels':px['height_mae_best_fit_levels'],'normal_mean_angle_degrees':px['normal_mean_angle_degrees'],
            'texture_compare_overall':tx['overall'] if tx else None,'texture_groups':tx['groups'] if tx else None,
            'bake_seconds_1254px_8_samples_all_channels':bk['timings']['seconds'] if bk else None,'shapes':bk['shapes'] if bk else None}
for n in ('S0','S','M','L'):
    e=entry(n)
    if e: report['classes'][n]=e
for n in ('layerA','layerB','S0','R16k','R32k','M','R128k','R256k','L','S'):
    e=entry(n)
    if e: report['rate_distortion'][n]=e
report['seam_tests']=jl(f'{R}/scores/seam_tests.json')
report['variation']=jl(f'{R}/variations/summary.json')
report['area']=jl(f'{R}/area/summary.json')
report['resolution']=jl(f'{R}/resolution/resolution_tests.json')
report['derivation_ceiling']=jl(f'{R}/analysis/derivation_ceiling.json')
report['height_routes_S0']=jl(f'{R}/scores/height_routes_S0.json')
report['height_routes_L']=jl(f'{R}/scores/height_routes_L.json')
report['transfer']=jl(f'{R}/transfer/transfer_notes.json')
report['geometry_route']=jl(f'{R}/outputs/geometry_route/geometry_route.json')
json.dump(report,open(R+'/final_report.json','w'),indent=1)
print('final_report.json written;',len(json.dumps(report)),'bytes')
