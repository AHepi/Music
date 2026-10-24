import sys, os, json, shutil
import numpy as np, cv2
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from growth import sheet_growth as sg, plan_growth
G='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/growth/'
OUT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/25 Street grime, cracks, stains, weeds and moss - pictures/'
BASE=KIT+'/harness/baseline/'
os.makedirs(OUT, exist_ok=True)
sizes={}
# ---- plan
plan_growth.draw('pit_village_street','street',G+'full_street/pieces_plants_plate_main_A_wet.json',G+'pictures_work/plan_main.jpg',y0=-2,y1=24,scale=30,title='main plate camera')
plan_growth.draw('pit_village_street','lockout',G+'full_lockout/pieces_plants_plate_lockout_B_wet.json',G+'pictures_work/plan_lockout.jpg',y0=-2,y1=24,scale=30,title='lockout camera')
a=sg.read(G+'pictures_work/plan_main.jpg'); b=sg.read(G+'pictures_work/plan_lockout.jpg')
pm=json.load(open(G+'pictures_work/plan_main.json')); pl=json.load(open(G+'pictures_work/plan_lockout.json'))
sheet=sg.vstack([sg.title_band(a.shape[1]+b.shape[1]+6,['Growth: where the plants stand (ground seen from above, 0 to 24 m)','Blue = road crown, orange = trodden lanes, red = keep clear (doorsteps, fire).','Brown tint = litter. Plants in blue, orange or red: 0 on both plates.',f"main camera {pm['plants_drawn']} plants, lockout camera {pl['plants_drawn']} plants (white ring: 18 m)"]), sg.hstack([a,b])])
sizes['plan']=sg.save_jpg(OUT+'25 Growth - where pieces stand (plan with crown, lanes and rubbish).jpg', sheet)
# ---- before and after
def base_close(view, light, state): return sg.read(BASE+f'pictures/street/{view}_{light}_{state}.jpg')
def grow_close(view, light, state): return sg.read(G+f'full_street/{view}_{light}_{state}.jpg')
pairs=[('before: gutter view, dry',base_close('gutter_close','A','dry'),'after: growth on, dry',grow_close('gutter_close','A','dry')),
       ('before: gutter view, wet',base_close('gutter_close','A','wet'),'after: growth on, wet',grow_close('gutter_close','A','wet')),
       ('before: low view of the kerb foot, wet',sg.read(G+'spots_street/spots_spot_left_base.jpg'),'after: growth on, wet',sg.read(G+'spots_street/spots_spot_left_wet_growth.jpg'))]
pb=sg.read(BASE+'plates/plate_main_A_wet.png') if False else cv2.imread(BASE+'plates/plate_main_A_wet.png')
pg=sg.read(G+'full_street/plate_main_A_wet.jpg')
mask=cv2.imread(G+'keep_pngs/layer_growth_plate_main.png',cv2.IMREAD_UNCHANGED)
m=(mask[...,2]>127).astype(np.float32)
integral=cv2.integral(m); ch,cw=400,560; best=(-1,0,0)
for y in range(0,m.shape[0]-ch,40):
    for x in range(0,m.shape[1]-cw,40):
        s=integral[y+ch,x+cw]-integral[y,x+cw]-integral[y+ch,x]+integral[y,x]
        if s>best[0]: best=(s,x,y)
_,x,y=best
pairs.append(('before: main plate at 100 %',pb[y:y+ch,x:x+cw],'after: growth on, main plate at 100 %',pg[y:y+ch,x:x+cw]))
sizes['before_after']=sg.before_after(pairs, OUT+'25 growth - before and after.jpg', ['Growth layer: small 3D weeds and moss cushions on the street (wet evening, the lamps only)','left: the street as it is now (earlier layers only)   right: with the growth layer on at its default dials'])
# ---- main plate crop at 100 %
crop=pg[max(0,y-150):y+ch+250, max(0,x-100):x+cw+500]
sizes['crop']=sg.save_jpg(OUT+'25 Growth - the main plate crop at 100 percent.jpg', sg.label(crop,'main plate (1536 x 2730) at 100 %, wet evening, growth on: 295 plants in the first 18 m ahead of the camera'))
# ---- dials
items=[('before (no growth)',sg.read(G+'dials_street/dials_base.jpg'))]
names=[('default','default dials'),('weeds0','weeds_amount 0'),('weeds2','weeds_amount 2'),('cushions0','cushions_amount 0'),('cushions2','cushions_amount 2'),('size05','piece_size 0.5'),('size2','piece_size 2'),('dist10','distance 10 m'),('wet','wet evening (state)'),('gain05','colour_gain 0.6'),('gain15','colour_gain 1.5'),('dead0','no dead grass, no flowers'),('flowers','dead 30 %, flowers 30 %'),('spacing','min_spacing 0.30 m'),('cover2','weed_cover and cushion_cover 2 %')]
for k,t in names: items.append((t, sg.read(G+f'dials_street/dials_{k}.jpg')))
sizes['dials']=sg.dials_sheet(items, OUT+'25 Growth - what each main dial does.jpg', ['Growth layer: what each main dial does (same gutter view, one dial changed at a time, dry unless said)'], columns=3, cell=420)
# ---- pieces
g1=sg.read(G+'gallery/gallery_dry.jpg')[160:1100,240:1560]; g2=sg.read(G+'gallery/gallery_wet.jpg')[160:1100,240:1560]
top=sg.hstack([sg.label(sg.fit(g1,700),'the piece library at real size, dry (neutral light; one kind a row)'),sg.label(sg.fit(g2,700),'the same, wet')])
bot=sg.hstack([sg.label(sg.fit(sg.read(G+'spots_street/spots_spot_left_dry_growth.jpg'),700),'in the street, dry (evening lamps)'),sg.label(sg.fit(sg.read(G+'spots_street/spots_spot_left_wet_growth.jpg'),700),'in the street, wet')])
sizes['pieces']=sg.save_jpg(OUT+'25 Growth - the pieces (weeds and moss cushions) in a close view, dry and wet.jpg', sg.vstack([sg.title_band(top.shape[1],['Growth: the weeds and moss cushions. Library: grass, dead grass, pearlwort, dandelion (one in flower, one a seed-clock), plantain, groundsel, chickweed, shepherd\'s purse, toadflax, moss strings']),top,bot]))
# ---- thin rubbish
r=sg.read(G+'spots_street/spots_spot_right_wet_growth.jpg'); l=sg.read(G+'spots_street/spots_spot_left_wet_growth.jpg')
rb=sg.read(G+'spots_street/spots_spot_right_base.jpg'); lb=sg.read(G+'spots_street/spots_spot_left_base.jpg')
rows=[sg.hstack([sg.label(sg.fit(rb,640),'before: kerb foot and gutter, litter only'),sg.label(sg.fit(r,640),'after: weeds where the litter is thin, none on the heap')]),sg.hstack([sg.label(sg.fit(lb,640),'before'),sg.label(sg.fit(l,640),'after')])]
sizes['thin']=sg.save_jpg(OUT+'25 Growth - weeds through thin rubbish, none on heaps.jpg', sg.vstack([sg.title_band(1286,['Growth next to the litter: full density below litter mask 0.45, none above 0.75; no weed within 5 cm of a litter piece (0 of the weeds in every plate)'])]+rows))
print(sizes)
