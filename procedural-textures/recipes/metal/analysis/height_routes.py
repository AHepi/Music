# What this does (plain words): compares three ways of making the HEIGHT picture (and the normal picture that follows from it) for the same colour picture:
#   derived  = from the colour picture by the rule fitted on the reference (grey -> light blur -> tone curve)
#   geometry = from the real raised geometry photographed from above (straps, braces, rivets), with a straight-line fit of its height numbers
#   hybrid   = a mix of the two, share w of geometry
# For each, it writes a map set (colour from the painted route, height, normal) and runs pixel_compare, printing height error, normal angle and tier.
# The straight-line fit (gain and offset of the geometry height) is fitted on the reference height: 2 numbers, written into the printout.
# Use: python3 -I height_routes.py COLOUR_FOLDER GEOMETRY_FOLDER NAME
import json, os, sys
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE+'/../generator'); import preview_tools as pt, derive_maps as dm
colour_folder,geo_folder,name=sys.argv[1:4]
maps=json.load(open(PROC+'/recipes/metal/description/maps_rule.json'))
colour=cv2.imread(colour_folder+'/colour.png')[...,::-1]
geo=cv2.imread(geo_folder+'/height_geometry.png',cv2.IMREAD_UNCHANGED).astype(np.float64); geo=(geo[...,0] if geo.ndim==3 else geo)/65535.0
ref=cv2.imread(PROC+'/reference/metal/height_as_uploaded.png',0).astype(np.float64)/255.0
derived=dm.height_from_colour(colour.astype(np.float64),maps)
# fit ref ~ derived + g*geometry (the geometry's own contribution) to see what the geometry adds; and the pure geometry line
A=np.stack([geo.ravel(),np.ones(geo.size)],1); gain,offset=np.linalg.lstsq(A,ref.ravel(),rcond=None)[0]
print('geometry-only straight-line fit to the reference height: gain %.3f offset %.3f'%(gain,offset))
fitted_geo=np.clip(gain*geo+offset,0,1)
rows=[]
for label,h in [('derived',derived),('geometry',fitted_geo)]+[(f'hybrid w={w}',(1-w)*derived+w*fitted_geo) for w in (0.2,0.4,0.6)]:
    out=PROC+f'/recipes/metal/scores/height_routes_{name}_'+label.replace(' ','_').replace('=','')
    os.makedirs(out,exist_ok=True)
    cv2.imwrite(out+'/colour.png',colour[...,::-1])
    cv2.imwrite(out+'/height.png',np.round(np.clip(h,0,1)*65535).astype(np.uint16))
    cv2.imwrite(out+'/normal.png',np.round(dm.normal_from_height(h,maps['normal_strength'])*255).astype(np.uint8)[...,::-1])
    pixel,_=pt.compare(out,sheet=False,texture=False)
    rows.append((label,pixel['height_mae_levels'],pixel['height_mae_best_fit_levels'],pixel['height_correlation'],pixel['normal_mean_angle_degrees'],pixel['tier_reached']))
    print(label.ljust(14),'height mae %.2f  best-fit mae %.2f  corr %.3f  normal angle %.2f  tier %s'%rows[-1][1:])
json.dump({'gain':gain,'offset':offset,'rows':rows},open(PROC+f'/recipes/metal/scores/height_routes_{name}.json','w'),indent=1)
