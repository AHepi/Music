# What this does (plain words): first guess of the PROCEDURAL wear (the shader noise layers laid over the bare steel): steel tone changes, rust patches in
# four tones, pale chips, dark streaks. Writes description/S_v1.json = layout_v0 + these layers. Numbers are guesses to be tuned.
import json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
d=json.load(open(PROC+'/recipes/metal/description/layout_v0.json'))
def stops(*items): return [list(i) for i in items]
d['procedural']={
 'layers':[
  {'name':'steel tone','scale_u':34,'scale_v':22,'detail':4,'roughness':0.55,'seed':1,'gain':1.0,
   'stops':stops((0.0,[49,51,53],1.0),(0.30,[56,60,61],1.0),(0.62,[57,52,49],1.0),(0.80,[68,68,66],1.0),(0.93,[41,37,38],1.0))},
  {'name':'rust','scale_u':36,'scale_v':26,'detail':5,'roughness':0.6,'distortion':0.25,'seed':7,'gain':1.0,'edge_gain':0.35,
   'stops':stops((0.0,[0,0,0],0.0),(0.60,[63,37,26],1.0),(0.68,[79,42,26],1.0),(0.77,[98,56,31],1.0),(0.86,[120,75,43],1.0)),'rough':0.9,'metal':0.1},
  {'name':'chips','scale_u':55,'scale_v':40,'detail':4,'roughness':0.55,'seed':13,'gain':1.0,
   'stops':stops((0.0,[0,0,0],0.0),(0.80,[93,86,78],1.0),(0.90,[124,115,105],1.0)),'rough':0.35,'metal':1.0},
  {'name':'dark streaks','scale_u':80,'scale_v':8,'detail':3,'roughness':0.5,'seed':21,'gain':1.0,'edge_gain':0.2,
   'stops':stops((0.0,[0,0,0],0.0),(0.74,[41,37,38],1.0),(0.86,[25,19,17],1.0))},
 ],
 'grain':{'amount':0.07,'seed':3}}
json.dump(d,open(PROC+'/recipes/metal/description/S_v1.json','w'))
print(len(json.dumps(d,separators=(',',':'))))
