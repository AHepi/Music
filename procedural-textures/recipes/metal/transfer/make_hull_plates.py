# What this does (plain words): the TRANSFER test. It writes a description for a surface the generator was never given: painted ship's HULL PLATES (rows of overlapping
# steel plates, vertical joints that change place from row to row, small closely-spaced rivets along every edge, rust streaks running down from the rivets).
# Only the DESCRIPTION is new: it uses the same bars (here wide plates), the same edge-shading profiles, the same rivet picture (made smaller) and the same wear
# layers (different colours and stretch) as the metal generator. No line of generator code is changed. Writes description/hull_plates_uncal.json
# (then calibrate_wear.py sets the wear thresholds and metal_generator.py bakes it).
# Run: python3 -I make_hull_plates.py
import json, os, sys
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..')); D=PROC+'/recipes/metal/description/'
model=json.load(open(D+'sampler_model.json'))
rng=np.random.default_rng(11)
T=1254.0; rows=6; h=T/rows                       # six plate rows, 209 dots high
prof=dict(model['shared_profiles']); prof.update(model['seam_profiles'])
desc={'format':'metal_plate_v1','tile':T,'maps':model['maps'],'plate':[40,48,48],'plate_panels':[],'profiles':prof,'bands':[],'rivets':[]}
tones=[[66,80,76],[58,71,68],[72,86,81],[62,76,72],[69,83,78],[56,69,66]]
rivet=json.loads(json.dumps(model['rivet'])); rivet['radius']=7.5
desc['rivet']=rivet
for k in range(rows):
    yc=h*(k+0.5)
    # each plate is a wide bar; the plate above overlaps the one below it (higher order = on top)
    desc['bands'].append({'name':f'plate{k}','centre':[T/2,yc],'angle':0,'length':T*1.2,'half':h/2+3,'face':tones[k],'a':'lit_H','b':'shade_H','order':rows-k,'clip':None,'inner_a':None,'inner_b':None})
    # vertical butt joints: 3 per row, shifted by half a plate every second row
    for j in range(3):
        x=(j*418+(k%2)*209+60)%T
        desc['bands'].append({'name':'joint','centre':[x,yc],'angle':-90,'length':h-8,'half':3.0,'face':[20,22,22],'a':'seam_soft','b':'seam_lit','order':20,'clip':None,'inner_a':0,'inner_b':0})
        for yy in np.arange(yc-h/2+22,yc+h/2-10,36):
            desc['rivets'].append([x-13,float(yy)]); desc['rivets'].append([x+13,float(yy)])
    # two rows of rivets along the top and bottom edge of every plate
    for yy in (yc-h/2+17,yc+h/2-17):
        for x in np.arange(rng.uniform(0,38),T,38):
            desc['rivets'].append([float(x),float(yy+rng.normal(0,0.6))])
desc['rivets']=[[round(a,1),round(b,1)] for a,b in desc['rivets']]
# wear: the SAME layer structure as the metal tile, with new colours, new stretch (long vertical streaks), new shares
def t(items): return [[*c,s] for c,s in items]
desc['procedural']={'layers':[
 {'name':'paint tone','cover_all':True,'fine':{'scale_u':30,'scale_v':8,'detail':3,'roughness':0.55,'seed':5},'mod':{'scale_u':4,'scale_v':3,'detail':2,'seed':6,'weight':0.4},
  'targets':t([([46,57,56],0.15),([54,66,64],0.3),([62,76,72],0.3),([70,84,80],0.2),([80,93,88],0.05)])},
 {'name':'rust streaks','fine':{'scale_u':130,'scale_v':14,'detail':4,'roughness':0.6,'distortion':0.15,'seed':17},'mod':{'scale_u':7,'scale_v':3,'detail':3,'seed':18,'weight':0.4},'edge_gain':0.45,
  'targets':t([([78,58,44],0.03),([96,52,28],0.03),([120,66,32],0.03),([140,82,40],0.012),([170,150,120],0.01)]),'rough':0.8,'metal':0.2},
 {'name':'speckle','blend':'MULTIPLY','fine':{'scale_u':210,'scale_v':150,'detail':2,'roughness':0.5,'seed':31},'targets':[[118,118,118,0.18],[128,128,128,0.64],[140,140,140,0.18]]}],
 'grain':{'amount':0.08,'seed':9}}
json.dump(desc,open(D+'hull_plates_uncal.json','w'),separators=(',',':'))
print('hull plate description (before wear thresholds):',len(json.dumps(desc,separators=(',',':'))),'bytes;',len(desc['bands']),'bars;',len(desc['rivets']),'rivets')
