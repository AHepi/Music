# What this does (plain words): the VARIATION test. For seeds 1..8 it makes a new description with sample_description.py, bakes it with the same Blender
# generator, and measures (a) how much it looks like the same KIND of surface as the reference (texture_compare), (b) how much it is the same PICTURE as the
# reference (pixel_compare, which should be poor: these are new tiles), and (c) how different the eight tiles are from each other (mean difference and
# structural similarity of every pair). Writes variations/seed_N/ (pictures, scores), variations/summary.json and variations/contact_sheet.png.
import json, os, subprocess, sys, time, itertools
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE)
import preview_tools as pt, sample_description as sd
sys.path.insert(0,PROC+'/lib'); import pixel_compare as pc
BLENDER='/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
V=PROC+'/recipes/metal/variations'; os.makedirs(V,exist_ok=True)
seeds=[int(s) for s in sys.argv[1:]] or list(range(1,9))
summary={}
model=sd.load_model()
for seed in seeds:
    out=f'{V}/seed_{seed}'; os.makedirs(out,exist_ok=True)
    desc=sd.sample_description(seed,1,model); json.dump(desc,open(out+'/description.json','w'),separators=(',',':'))
    t0=time.time()
    ch='colour,rough,metal' if seed==1 else 'colour'
    r=subprocess.run([BLENDER,'-b','--disable-autoexec','-t','2','--python',HERE+'/metal_generator.py','--',out+'/description.json',out,'--samples','8','--channels',ch],capture_output=True,text=True)
    secs=time.time()-t0
    pixel,tex=pt.compare(out,sheet=False)
    summary[seed]={'bake_seconds':round(secs,1),'description_bytes':os.path.getsize(out+'/description.json'),'texture_overall':tex['overall'],'texture_groups':tex['groups'],'pixel':{k:pixel[k] for k in ('colour_ssim','colour_mean_delta_e','edge_skill_2px','height_mae_best_fit_levels','normal_mean_angle_degrees','tier_reached')}}
    print(seed,round(secs,1),'s',pt.summary_line(pixel,tex),flush=True)
# pairwise differences between the tiles
imgs={s:cv2.imread(f'{V}/seed_{s}/colour.png')[...,::-1] for s in seeds}
ref=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1]
pairs=[]
for a,b in itertools.combinations(seeds,2):
    mae=float(np.abs(imgs[a].astype(float)-imgs[b].astype(float)).mean())
    ss=pc.ssim(cv2.cvtColor(imgs[a],cv2.COLOR_RGB2GRAY),cv2.cvtColor(imgs[b],cv2.COLOR_RGB2GRAY))
    pairs.append((a,b,round(mae,2),round(float(ss),3)))
# difference from the reference (colour mean abs difference and SSIM) for the table
for s in seeds:
    summary[s]['mae_vs_reference']=round(float(np.abs(imgs[s].astype(float)-ref.astype(float)).mean()),2)
summary['pairs']={'mean_abs_difference_mean':round(float(np.mean([p[2] for p in pairs])),2),'ssim_mean':round(float(np.mean([p[3] for p in pairs])),3),'ssim_max':max(p[3] for p in pairs),'list':pairs}
json.dump(summary,open(V+'/summary.json','w'),indent=1)
cells=[cv2.resize(imgs[s],(420,420),interpolation=cv2.INTER_AREA) for s in seeds]
row1=np.hstack(cells[:4]) if len(cells)>=4 else np.hstack(cells)
sheet=np.vstack([row1,np.hstack(cells[4:8])]) if len(cells)>=8 else row1
cv2.imwrite(V+'/contact_sheet.png',sheet[...,::-1])
print('pairs',summary['pairs']['mean_abs_difference_mean'],summary['pairs']['ssim_mean'],summary['pairs']['ssim_max'])
