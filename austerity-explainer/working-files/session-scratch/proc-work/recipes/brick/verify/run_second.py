# verifier: second batch of re-bakes (fresh Blender processes, output only inside verify/)
import json, os, subprocess, sys
R='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/brick'
V=R+'/verify'
BL='/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
sys.path.insert(0,R+'/generator')
import sample_description as sd
brick=json.load(open(R+'/generator/sampler_model_brick.json'))
cob=json.load(open(R+'/generator/sampler_model_cobble.json'))
def bake(desc_path,out,size=1254,samples=8,extra=()):
    r=subprocess.run([BL,'-b','--disable-autoexec','-t','2','--python',R+'/generator/brick_generator.py','--',desc_path,out,'--size',str(size),'--samples',str(samples),*extra],capture_output=True,text=True)
    line=[l for l in r.stdout.splitlines() if l.startswith('[bake]')]
    print(out,line[-1] if line else r.stdout[-500:],flush=True)
# 1. the stored variation 14 description in a fresh process
bake(R+'/variations/description_14.json',V+'/var14_again')
# 2. half-tile test on variation 14 without grain
d=json.load(open(R+'/variations/description_14.json')); d.pop('grain',None)
json.dump(d,open(V+'/var14_nograin.json','w'),separators=(',',':'))
bake(V+'/var14_nograin.json',V+'/seam14_plain')
bake(V+'/var14_nograin.json',V+'/seam14_shift',extra=('--shift','627'))
# 3. my own seed, never used by the builder
d=sd.sample_description(777,brick,grain=0.14); json.dump(d,open(V+'/my_description_777.json','w'),separators=(',',':'))
bake(V+'/my_description_777.json',V+'/my_tile_777')
# 4. area description rendered at 1254 px (a 2508-dot picture at half size)
bake(R+'/area/description_area.json',V+'/area_at_1254',size=1254,samples=8)
# 5. cobble from an unseen seed
d=sd.sample_description(5,cob,grain=0.12,palette_strength=0.5); json.dump(d,open(V+'/my_description_cobble_5.json','w'),separators=(',',':'))
bake(V+'/my_description_cobble_5.json',V+'/my_cobble_5')
open(V+'/second_done.flag','w').write('done')
