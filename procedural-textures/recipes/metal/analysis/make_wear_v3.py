# What this does (plain words): writes description/S_v3_uncal.json, the final procedural-wear layers (before the thresholds are calibrated): the version of
# wear_v2.py's layers after the tuning described in the guide (rust patches 44 x 30 noise features across the tile, coarse clustering noise 5 x 4, steel tone 34 x 23,
# dark streaks 80 x 35, rust drips 260 x 6, plus a brightness-only fine speckle layer and per-dot grain 0.12). Run wear_v2.py first. Then calibrate_wear.py / try_wear.py set the thresholds.
import json, os
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..')); D=PROC+'/recipes/metal/description/'
d=json.load(open(D+'S_v2_uncal.json')); L=d['procedural']['layers']
L[0]['fine'].update(scale_u=34,scale_v=23); L[0]['mod']['weight']=0.5
L[1]['fine'].update(scale_u=44,scale_v=30,detail=6); L[1]['mod'].update(weight=0.45,scale_u=5,scale_v=4)
L[2]['fine'].update(scale_u=80,scale_v=35)
L.append({'name':'speckle','blend':'MULTIPLY','fine':{'scale_u':210,'scale_v':150,'detail':2,'roughness':0.5,'seed':31},'targets':[[118,118,118,0.18],[128,128,128,0.64],[140,140,140,0.18]]})
d['procedural']['grain']['amount']=0.12
# rust drips: very long thin vertical streaks (260 x 6 noise features) that rust-coloured, attracted by bar edges and rivets (edge_gain), about 2.4 per cent of the steel
L.insert(2,{'name':'rust drips','fine':{'scale_u':260,'scale_v':6,'detail':2,'roughness':0.5,'seed':51},'mod':{'scale_u':9,'scale_v':5,'detail':2,'seed':52,'weight':0.35},'edge_gain':0.5,
            'targets':[[86,48,28,0.012],[110,62,32,0.012]],'rough':0.85,'metal':0.15})
json.dump(d,open(D+'S_v3_uncal.json.check','w'))
os.replace(D+'S_v3_uncal.json.check',D+'S_v3_uncal.json')
print('written',D+'S_v3_uncal.json','(layers:',[l['name'] for l in L],')')
