# What this does (plain words): the remaining proofs for the metal generator, one command per test (it runs Blender itself where needed):
#   seam NAME ...        the half-tile-shift test: bake the description shifted by half a tile and compare with the first bake rolled by half a tile
#                        (a seamless generator gives the same picture; a wrongly rolled copy gives a different one, shown as a control)
#   resolution NAME      the same description baked at 512, 1254 and 2508 dots: time and what changes (pixel scores against the reference, sharpness)
#   area SEED            one bigger picture of NEW unique content (2 x 2 tiles = 2508 dots) from sample_description(seed, tile_multiple=2); measures its seams
# Results go to seam_tests.json / resolution_tests.json / area/summary.json in this recipe's folder.
import json, os, subprocess, sys, time
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..')); R=PROC+'/recipes/metal'
sys.path.insert(0,HERE); sys.path.insert(0,PROC+'/lib')
import preview_tools as pt, sample_description as sd, texture_compare as tc
BLENDER='/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
def bake(desc_path,out,size=1254,samples=8,shift=0,channels='colour'):
    t0=time.time()
    r=subprocess.run([BLENDER,'-b','--disable-autoexec','-t','2','--python',HERE+'/metal_generator.py','--',desc_path,out,'--size',str(size),'--samples',str(samples),'--shift',str(shift),'--channels',channels],capture_output=True,text=True)
    if 'bake]' not in r.stdout: raise SystemExit(r.stdout[-800:]+r.stderr[-800:])
    return round(time.time()-t0,1)
def load(p): return cv2.imread(p)[...,::-1].astype(float)
def seam_test(name):
    desc=R+'/description/'+name+'.json'
    base=R+'/outputs/'+name+'_seamtest_0'; shifted=R+'/outputs/'+name+'_seamtest_627'
    bake(desc,base,shift=0); bake(desc,shifted,shift=627)
    a=load(base+'/colour.png'); b=load(shifted+'/colour.png')
    rolled=np.roll(np.roll(a,627,0),627,1)
    wrong=np.roll(np.roll(a,400,0),213,1)
    d=lambda x,y:np.abs(x-y).mean(axis=2)
    res={'seamless_test':{'share_over_40_levels':float((d(rolled,b)>40).mean()),'mean_abs_difference':float(d(rolled,b).mean())},
         'wrongly_rolled_control':{'share_over_40_levels':float((d(wrong,b)>40).mean()),'mean_abs_difference':float(d(wrong,b).mean())}}
    return res
def resolution_test(name):
    desc=R+'/description/'+name+'.json'; out={}
    for size in (512,1254,2508):
        folder=R+f'/resolution/{name}_{size}'; os.makedirs(folder,exist_ok=True)
        secs=bake(desc,folder,size=size,samples=8,channels='colour,rough,metal')
        pixel,tex=pt.compare(folder,sheet=False)
        grey=cv2.cvtColor(cv2.imread(folder+'/colour.png'),cv2.COLOR_BGR2GRAY).astype(np.float32)
        sharp=float(np.abs(cv2.Laplacian(grey,cv2.CV_32F)).mean()*1254.0/size)   # edge sharpness measure, rescaled so that sizes can be compared
        out[size]={'bake_seconds':secs,'colour_ssim':pixel['colour_ssim'],'delta_e':pixel['colour_mean_delta_e'],'edge_skill':pixel['edge_skill_2px'],'height_mae_best_fit':pixel['height_mae_best_fit_levels'],'normal_angle':pixel['normal_mean_angle_degrees'],'texture_overall':tex['overall'],'laplacian_sharpness_per_dot_scaled':round(sharp,3)}
        print(name,size,out[size],flush=True)
    return out
def area_test(seed):
    folder=R+'/area'; os.makedirs(folder,exist_ok=True)
    desc=sd.sample_description(seed,2); json.dump(desc,open(folder+f'/area_seed{seed}.json','w'),separators=(',',':'))
    secs=bake(folder+f'/area_seed{seed}.json',folder+f'/seed{seed}',size=2508,samples=8,channels='colour,rough,metal')
    img=cv2.imread(folder+f'/seed{seed}/colour.png'); g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float64)
    inner=(np.abs(np.diff(g,axis=1)).mean()+np.abs(np.diff(g,axis=0)).mean())/2
    wrap=(np.abs(g[:,0]-g[:,-1]).mean()+np.abs(g[0,:]-g[-1,:]).mean())/2
    mid_x=np.abs(g[:,1253]-g[:,1254]).mean(); mid_y=np.abs(g[1253,:]-g[1254,:]).mean()
    q=[g[:1254,:1254],g[:1254,1254:],g[1254:,:1254],g[1254:,1254:]]
    import pixel_compare as pc
    qs=[round(float(pc.ssim(q[i],q[j])),3) for i in range(4) for j in range(i+1,4)]
    # biggest repeat: 2D autocorrelation peak away from the origin
    f=g-g.mean(); F=np.fft.fft2(f); ac=np.fft.ifft2(np.abs(F)**2).real; ac/=ac[0,0]
    ys,xs=np.indices(ac.shape); dist=np.hypot(np.minimum(xs,2508-xs),np.minimum(ys,2508-ys))
    far=ac.copy(); far[dist<60]=-1
    iy,ix=np.unravel_index(np.argmax(far),far.shape)
    res={'seed':seed,'bake_seconds':secs,'size':2508,'description_bytes':os.path.getsize(folder+f'/area_seed{seed}.json'),'inner_jump':round(float(inner),3),'wrap_jump_ratio':round(float(wrap/inner),3),
         'middle_cross_jump_ratio':[round(float(mid_x/inner),3),round(float(mid_y/inner),3)],'quadrant_pair_ssim':qs,'largest_repeat_correlation':round(float(far.max()),3),'largest_repeat_at':[int(ix),int(iy)]}
    json.dump(res,open(folder+'/summary.json','w'),indent=1); print(res)
    return res
if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='seam':
        allres={}
        for n in sys.argv[2:]:
            allres[n]=seam_test(n); print(n,allres[n],flush=True)
        path=R+'/scores/seam_tests.json'; old=json.load(open(path)) if os.path.exists(path) else {}; old.update(allres); json.dump(old,open(path,'w'),indent=1)      # merge with earlier runs
    elif cmd=='resolution':
        path=R+'/resolution/resolution_tests.json'; old=json.load(open(path)) if os.path.exists(path) else {}
        for n in sys.argv[2:]:
            old[n]=resolution_test(n); json.dump(old,open(path,'w'),indent=1)      # merge with earlier runs
    elif cmd=='area':
        area_test(int(sys.argv[2]))
