# What this does (plain words): writes the LAYOUT half of the metal description from numbers measured in the reference: where the straps, braces,
# seam lines and rivets are; each strap's face colour; how each strap edge is shaded (shadow, dark crease, bright edge line); and the typical rivet.
# Analysis only: it reads the reference (to measure) and the measurement files in this folder. The output, description/layout_v0.json, holds numbers only.
# Run: python3 -I make_layout.py
import json, math, os, sys
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,os.path.join(HERE,'..','generator'))
import metal_shapes as ms, preview_tools as pt
ref=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1]
H=W=1254
prof=json.load(open(HERE+'/edge_profiles.json'))
rivet_pts=[r for r in json.load(open(HERE+'/rivets_found.json')) if r[2]>=0.68 and not (abs(r[0]-1061)<3 and abs(r[1]-23)<3) and not (abs(r[0]-472)<3 and abs(r[1]-624)<3)]+[[840,683,0.67]]

def simplify(table,tol=3.0):
    """Keep as few (d,r,g,b) points as possible so that straight lines between them stay within tol levels of the measured curve."""
    t=np.array(table,float); keep=[0,len(t)-1]
    def worst(i,j):
        a,b=t[i],t[j]; best=(0,None)
        for k in range(i+1,j):
            f=(t[k,0]-a[0])/(b[0]-a[0]); err=np.abs(t[k,1:]-(a[1:]+f*(b[1:]-a[1:]))).max()
            if err>best[0]: best=(err,k)
        return best
    stack=[(0,len(t)-1)]
    while stack:
        i,j=stack.pop(); err,k=worst(i,j)
        if err>tol: keep.append(k); stack+= [(i,k),(k,j)]
    return t[sorted(set(keep))]

def profile_table(name,side_is_a,inner,outer):
    p=prof[name]; off=np.array(p['offsets'],float); rgb=np.array(p['median_rgb'],float)
    d=off if side_is_a else -off
    order=np.argsort(d); d,rgb=d[order],rgb[order]
    sel=(d>=-inner)&(d<=outer)
    tab=np.column_stack([d[sel],rgb[sel]])
    return simplify(tab)

def raw_table(src,side_is_a,inner,outer):
    p=prof[src]; off=np.array(p['offsets'],float); rgb=np.array(p['median_rgb'],float)
    d=off if side_is_a else -off
    order=np.argsort(d); d,rgb=d[order],rgb[order]
    sel=(d>=-inner)&(d<=outer)
    return d[sel],rgb[sel]
# six shared edge profiles (average of the measured ones of the same kind): lit = the upper / left edge of a bar, shade = the lower / right edge
classes={
 'lit_H':[('H1_top',True),('H2_top',True)], 'shade_H':[('H1_bot',False),('H2_bot',False)],
 'lit_V':[('V1_left',False),('V2_left',False)], 'shade_V':[('V1_right',True),('V2_right',True)],
 'lit_D':[('B1_ur',True),('B2_ur',True)], 'shade_D':[('B1_ll',False),('B2_ll',False)]}
reach={'lit_H':(12,12),'shade_H':(12,24),'lit_V':(14,16),'shade_V':(14,24),'lit_D':(12,14),'shade_D':(12,24)}
shared={}
for cname,members in classes.items():
    tabs=[raw_table(src,isa,*reach[cname]) for src,isa in members]
    d0=tabs[0][0]; avg=np.mean([t[1] for t in tabs],axis=0)
    shared[cname]=[[round(float(v)) for v in row] for row in simplify(np.column_stack([d0,avg]),tol=3.5)]
json.dump(shared,open(HERE+'/../description/profiles_shared.json','w'),separators=(',',':'))
# the faithful fit: one profile per bar side (each bar's own shading), simplified so that lines stay within 4 levels
element_sides={'H1':('H1_top',True,'H1_bot',False,'H'),'H2':('H2_top',True,'H2_bot',False,'H'),'V1':('V1_left',False,'V1_right',True,'V'),'V2':('V2_left',False,'V2_right',True,'V'),
               'B1':('B1_ur',True,'B1_ll',False,'D'),'B2':('B2_ur',True,'B2_ll',False,'D')}
profiles={}
for el,(sa,ia,sb,ib,kind) in element_sides.items():
    for side,src,isa,cname in (('a',sa,ia,'lit_'+kind),('b',sb,ib,'shade_'+kind)):
        d,rgb=raw_table(src,isa,*reach[cname])
        profiles[f'{el}{side}']=[[round(float(v)) for v in row] for row in simplify(np.column_stack([d,rgb]),tol=4.0)]
# thin seam lines between plates: a dark core and a bright lower / right edge
profiles['seam_lit']=[[0,24,22,22],[1,36,34,34],[2,66,66,66],[4,60,60,60],[6,56,57,58]]
profiles['seam_soft']=[[0,24,22,22],[2,40,38,38],[4,54,55,56]]

def band_dict(name,centre,angle,length,half,order,a,b,face=(60,60,62),clip=None,inner=(None,None)):
    return {'name':name,'centre':[round(centre[0],1),round(centre[1],1)],'angle':angle,'length':length,'half':half,'face':list(face),'a':a,'b':b,'order':order,'clip':clip,'inner_a':inner[0],'inner_b':inner[1]}
def brace_centre(angle,pn,t):
    a=math.radians(angle); n=np.array([math.sin(a),-math.cos(a)]); d=np.array([math.cos(a),math.sin(a)])
    return n*pn+d*t
bands=[
 band_dict('S1',(272,264.5),0,192,2.5,-1,'seam_soft','seam_lit',face=(24,22,22),inner=(0,0)),
 band_dict('S2',(419.5,978.5),0,485,2.5,-1,'seam_soft','seam_lit',face=(24,22,22),inner=(0,0)),
 band_dict('S3',(927.5,905.5),-90,551,2.5,-1,'seam_soft','seam_lit',face=(24,22,22),inner=(0,0)),
 band_dict('B2',brace_centre(50.5,213.5,1425),50.5,850,49.5,0,'B2a','B2b'),
 band_dict('H2',(627,1262.5),0,1400,81.5,1,'H2a','H2b'),
 band_dict('B1',brace_centre(48.3,143.3,520),48.3,740,51.0,2,'B1a','B1b',clip=[-1e6,0,1e6,1e6]),
 band_dict('V1',(108.5,627),-90,1400,67.5,3,'V1a','V1b'),
 band_dict('H1',(627,576),0,1400,50,4,'H1a','H1b'),
 band_dict('V2',(731,627),-90,1400,68.5,5,'V2a','V2b'),
]
desc={'format':'metal_plate_v1','tile':1254,'plate':[54,56,58],'plate_panels':[],'profiles':profiles,'bands':bands}
# face colours: median reference colour over each face, away from rivets
tmp=ms.build_layout_shapes(dict(desc,rivet=None)) if False else None
def face_mask(b):
    shapes=[s for s in ms.band_shapes(b,profiles) if s['kind']=='face']
    mask=np.zeros((H,W),np.uint8)
    for s in shapes:
        for sh in ms.wrap_copies([s],1254.0):
            pts=np.round(sh['points']).astype(np.int32)
            cv2.fillPoly(mask,[pts.reshape(-1,1,2)],1)
    return mask
rivet_mask=np.zeros((H,W),np.uint8)
for x,y,_ in rivet_pts:
    for dx in (-W,0,W):
        for dy in (-H,0,H): cv2.circle(rivet_mask,(int(x+dx),int(y+dy)),30,1,-1)
for b in bands:
    m=face_mask(b).astype(bool)&~rivet_mask.astype(bool)
    if b['name']=='B1': m[:100,:]=False
    b['face']=[int(round(v)) for v in np.median(ref[m],axis=0)]
    print(b['name'],'face pixels',int(m.sum()),'median colour',b['face'])
# panels (the plate between the straps)
panels={'Pa':(186,100,650,515),'Pb':(186,640,650,1170),'Pc':(815,100,1254,515),'Pd':(815,640,1254,1170)}
for k,(x0,y0,x1,y1) in panels.items():
    print(k,np.median(ref[y0:y1,x0:x1].reshape(-1,3),axis=0))
left=np.median(ref[100:500,0:35].reshape(-1,3),axis=0); print('left margin',left)
json.dump(desc,open(PROC+'/recipes/metal/description/layout_v0_noRivets.json','w'),indent=0)

# ---- rivets: typical rivet by ring and sector (median over all rivets), centres as found
R=19.5
ring_edges=[0.0,0.45,0.93,1.12,1.6]      # fractions of the radius: dome core, dome slope, dark rim, soft shadow
P=80
refp=cv2.copyMakeBorder(ref.astype(np.float32),P,P,P,P,cv2.BORDER_WRAP)
def ring_sector_colours(cx,cy,sectors=8):
    out=np.zeros((len(ring_edges)-1,sectors,3),np.float32)
    for ri in range(len(ring_edges)-1):
        rs=np.linspace(ring_edges[ri],ring_edges[ri+1],5)[1:-1]*R if ri>0 else np.linspace(0.1,ring_edges[1],4)*R
        for si in range(sectors):
            vals=[]
            for r in rs:
                for da in (-0.25,0,0.25):
                    a=2*math.pi*(si+0.5+da)/sectors
                    xs=np.array([[cx+r*math.cos(a)+P]],np.float32); ys=np.array([[cy+r*math.sin(a)+P]],np.float32)
                    vals.append(cv2.remap(refp,xs,ys,cv2.INTER_LINEAR)[0,0])
            out[ri,si]=np.mean(vals,axis=0)
    return out
cells=np.median(np.array([ring_sector_colours(x,y) for x,y,_ in rivet_pts]),axis=0)
desc['rivet']={'radius':R,'rings':ring_edges[1:],'cells':[[[int(round(v)) for v in c] for c in ring] for ring in cells]}
desc['rivets']=[[round(x,1),round(y,1)] for x,y,_ in rivet_pts]
desc['plate']=[56,57,58]
desc['maps']=json.load(open(HERE+'/../description/maps_rule.json')) if os.path.exists(HERE+'/../description/maps_rule.json') else None
json.dump(desc,open(PROC+'/recipes/metal/description/layout_v0.json','w'),separators=(',',':'))
print('description bytes',len(json.dumps(desc)))
stack=ms.build_stack(desc)
print('shapes',len(stack))
maps=json.load(open(HERE+'/derivation_ceiling.json'))['tone_curve_and_blur']
maps={'blur_sigma':maps['sigma'],'curve_x':maps['curve_x'],'curve_y':maps['curve_y'],'normal_strength':5.0}
json.dump(maps,open(PROC+'/recipes/metal/description/maps_rule.json','w'))
maps=desc['maps'] or maps
img=pt.paint_stack(stack)
out=PROC+'/recipes/metal/scores/layout_v0'
pt.write_map_set(img,out,maps)
pixel,tex=pt.compare(out)
print(pt.summary_line(pixel,tex))
