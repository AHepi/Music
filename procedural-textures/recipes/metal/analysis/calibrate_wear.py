# What this does (plain words): sets the "thresholds" of the procedural wear layers so that each layer paints the share of the picture you ask for.
# A wear layer is a noise picture (a value 0..1 at every dot) turned into colours by a ladder of thresholds ("stops"). Blender's noise values are not
# spread evenly, so the same threshold can mean 5 per cent of the picture for one noise setting and 30 per cent for another. This script asks Blender
# to draw each layer's noise value (the 'field' pictures), reads where the noise values lie over the bare steel, and sets every threshold so that the
# colour above it covers exactly the share named in the layer's 'targets' list.
# 'targets' = [[colour r,g,b, share], ...] listed from the LOWEST noise value to the highest; shares are fractions of the bare-steel picture.
# Use:  python3 -I calibrate_wear.py DESCRIPTION.json OUT_DESCRIPTION.json [--size 627]
import json, os, subprocess, sys, tempfile
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
BLENDER='/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

def render_fields(desc_path, folder, size, layer_count):
    chans=['basemask']+[f'field{i}' for i in range(layer_count)]
    subprocess.run([BLENDER,'-b','--disable-autoexec','-t','2','--python',PROC+'/recipes/metal/generator/metal_generator.py','--',desc_path,folder,'--size',str(size),'--samples','1','--channels',','.join(chans)],check=True,capture_output=True)
    base=cv2.imread(folder+'/basemask.png',cv2.IMREAD_UNCHANGED)
    base=(base[...,0] if base.ndim==3 else base).astype(np.float32); base/= (65535.0 if base.max()>255 else 255.0)
    fields=[]
    for i in range(layer_count):
        f=cv2.imread(folder+f'/field{i}.png',cv2.IMREAD_UNCHANGED); f=(f[...,0] if f.ndim==3 else f).astype(np.float32)/65535.0
        fields.append(f)
    return base,fields

def calibrate(desc, size=627):
    layers=desc['procedural']['layers']
    with tempfile.TemporaryDirectory(dir=PROC+'/recipes/metal/outputs') as tmp:
        dp=tmp+'/d.json'
        # the ramps do not matter for the field pictures, but the generator wants stops
        d2=json.loads(json.dumps(desc))
        for l in d2['procedural']['layers']: l.setdefault('stops',[[0,[0,0,0],0]])
        d2['procedural'].pop('grain',None)
        json.dump(d2,open(dp,'w'))
        base,fields=render_fields(dp,tmp,size,len(layers))
    inside=base>0.99
    report=[]
    for layer,f in zip(layers,fields):
        if 'targets' not in layer: continue
        v=f[inside]
        stops=[[0.0,[0,0,0],0.0]]
        cumulative=0.0
        # from the highest value down: the last target takes the top share
        items=layer['targets']
        positions=[None]*len(items)
        top=0.0
        for k in range(len(items)-1,-1,-1):
            top+=items[k][3]
            positions[k]=float(np.quantile(v,1.0-min(top,0.999)))
        if layer.get('blend')=='MULTIPLY' or layer.get('cover_all'):
            stops=[[0.0,list(items[0][:3]),1.0]]+[[round(positions[k],4),list(items[k][:3]),1.0] for k in range(1,len(items))]
        else:
            stops+= [[round(positions[k],4),list(items[k][:3]),1.0] for k in range(len(items))]
        layer['stops']=stops
        report.append((layer.get('name'),[round(p,3) for p in positions],'value range',round(float(v.min()),3),round(float(v.max()),3)))
    return desc,report

if __name__=='__main__':
    desc=json.load(open(sys.argv[1])); size=int(sys.argv[sys.argv.index('--size')+1]) if '--size' in sys.argv else 627
    desc,report=calibrate(desc,size)
    for r in report: print(r)
    json.dump(desc,open(sys.argv[2],'w'))
