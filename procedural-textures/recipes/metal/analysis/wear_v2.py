# What this does (plain words): second guess of the PROCEDURAL wear: every layer is a fine noise blended with a coarse noise, turned into colours by
# thresholds that calibrate_wear.py sets from the shares written here. Writes description/S_v2_uncal.json (shares, no thresholds yet).
import json, os
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
d=json.load(open(PROC+'/recipes/metal/description/layout_v0.json'))
def t(items): return [[*c,s] for c,s in items]
d['procedural']={
 'layers':[
  {'name':'steel tone','cover_all':True,'fine':{'scale_u':70,'scale_v':50,'detail':3,'roughness':0.55,'seed':1},'mod':{'scale_u':5,'scale_v':4,'detail':2,'seed':2,'weight':0.4},
   'targets':t([([41,37,38],0.095),([49,51,53],0.28),([56,60,61],0.333),([57,52,49],0.132),([68,68,66],0.157)])},
  {'name':'rust and chips','fine':{'scale_u':90,'scale_v':64,'detail':5,'roughness':0.6,'distortion':0.2,'seed':7},'mod':{'scale_u':8,'scale_v':6,'detail':3,'seed':8,'weight':0.35},'edge_gain':0.25,
   'targets':t([([73,58,48],0.047),([63,37,26],0.054),([79,42,26],0.041),([86,58,40],0.034),([98,56,31],0.048),([120,75,43],0.016),([106,81,62],0.022),([93,86,78],0.047),([124,115,105],0.012)]),'rough':0.8,'metal':0.2},
  {'name':'dark streaks','fine':{'scale_u':120,'scale_v':10,'detail':3,'roughness':0.5,'seed':21},'mod':{'scale_u':6,'scale_v':4,'detail':2,'seed':22,'weight':0.3},'edge_gain':0.2,
   'targets':t([([46,32,26],0.04),([25,19,17],0.015)])},
 ],
 'grain':{'amount':0.06,'seed':3}}
json.dump(d,open(PROC+'/recipes/metal/description/S_v2_uncal.json','w'))
