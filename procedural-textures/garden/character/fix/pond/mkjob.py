# usage: mkjob.py NAME  (reads variants from jobs_def_NAME.py) -> writes jobs/NAME.json (render) and jobs/mNAME.json (metrics)
import json, sys
G='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character'
name=sys.argv[1]
ns={}
exec(open('jobs_def_%s.py'%name).read(), ns)
O=G+'/fix/pond/previews/'+name
def full(n, cam, q=95):
    return {"name": n, "camera": cam, "size": "2400x1600", "samples": 128, "mode": "preview", "quality": q}
variants=[]; items=[]
reg_hero={"maple":[0,100,960,900],"pond_front":[300,1250,1560,1600],"pond_far":[200,1040,1260,1260],"pine":[1580,290,1980,670]}
reg_ver={"maple":[1040,60,2010,560],"pond":[880,820,1700,1100]}
for vname, opts in ns['VARIANTS']:
    pics=[full('hero_full','photo'), full('veranda_full','veranda')] + ns.get('EXTRA_PICS', [])
    variants.append({"name":vname,"apply_pond":opts,"stage_report":O+"/%s_stage_report.json"%vname,"pictures":pics})
    items.append({"name":vname+"_hero","png":O+"/%s_hero_full.jpg"%vname,"before":G+"/../fix/out/final/real_hero.png","outdir":O+"/m","no_jpg":True,"regions":reg_hero})
    items.append({"name":vname+"_veranda","png":O+"/%s_veranda_full.jpg"%vname,"before":G+"/../fix/out/final/real_veranda.png","outdir":O+"/m","no_jpg":True,"regions":reg_ver})
json.dump({"outdir":O,"variants":variants}, open('jobs/%s.json'%name,'w'), indent=1)
json.dump({"metrics_json":O+"/metrics.json","items":items}, open('jobs/m%s.json'%name,'w'), indent=1)
print('ok', name, len(variants), 'variants')
