import sys, os
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering')
from walls import sheet_walls as S
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/25 Street grime, cracks, stains, weeds and moss - pictures'
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/harness/baseline/plates/'
EV=sys.argv[1] if len(sys.argv)>1 else 'f3'
def save(items,cols,size,name,title=None,q=84):
    out=os.path.join(P,name); n=S.grid(items,cols,size,out,title,quality=q)
    while n>395000 and q>50:
        q-=8; n=S.grid(items,cols,size,out,title,quality=q)
    print(name,n//1024,'KB q',q)
a=KIT+'plate_main_A_wet.png'; b=f'out/{EV}_street/t_all_main.png'
L=(0,820,436,1480); R=(1100,820,1536,1480)
save([(a,'left wall: before',L),(b,'left wall: after',L),(a,'right wall: before',R),(b,'right wall: after',R)],4,(436,660),'25 Walls - soot, run-off streaks and wall foot at the main camera (before and after).jpg')
d='out/pic1/'; box=(120,150,960,720)
save([(d+'pc_base_doorstep_close.jpg','before',box),(d+'pc_kit_doorstep_close.jpg','after (the look: 55 % of steps whitened)',box),(d+'pc_kitwhite_doorstep_close.jpg','after, every step whitened',box)],3,(560,380),'25 Walls - doorsteps whitened and worn (close, before and after).jpg')
items=[(d+'fl_base_left03.jpg','before')]+[(d+f'fl_{l}_left03.jpg',l) for l in ('soot','runoff','foot','steps','wallcracks','wallgrowth')]+[(d+'fl_all_left03.jpg','all six layers')]
save(items,4,(400,600),'25 Walls - the layers one at a time on one house.jpg')
save([(d+'pc_base_pipe_close.jpg','before'),(d+'pc_kit_pipe_close.jpg','after: streaks, splash band, tide-mark'),(d+'pc_base_wall_close.jpg','wall foot before'),(d+'pc_kit_wall_close.jpg','wall foot after')],2,(640,480),'25 Walls - the downpipe close (streaks, splash, tide-mark).jpg')
d='out/cs1/'
items=[(d+'c_before.png','before'),(d+'c_kept.png','kept look, 5 layers'),(d+'c_neglected.png','neglected look, 5 layers')]+[(d+f'c_{l}.png',f'{l} alone (kept look)') for l in ('soot','runoff','foot','wallcracks','wallgrowth')]
save(items,4,(480,320),'25 Walls - the same layers on the courtyard plaster wall (reuse test).jpg')
pl=[('main','plate_main_A_wet',f'out/{EV}_street/t_all_main.png'),('notice','plate_notice_A_wet',f'out/{EV}_street/t_all_notice.png'),('lockout','plate_lockout_B_wet',f'out/{EV}_lockout/t_all_lockout.png')]
items=[(KIT+b+'.png',f'{c} before') for c,b,_ in pl]+[(k,f'{c} after (walls layers)') for c,_,k in pl]
save(items,3,(384,682),'25 walls - before and after.jpg')
d='out/pic1/'
rows=[('soot','film_mult',[1.0,0.6,0.4]),('soot','washed_pale',[0.0,0.5,1.0]),('runoff','strength',[0.3,0.6,1.0]),('foot','splash_strength',[0.3,0.6,1.0]),('wallgrowth','moss_amount',[0.0,0.5,1.5]),('wallcracks','crack_amount',[0.0,1.0,2.0])]
names={('wallgrowth','moss_amount',0.0):'moss_amount 0',('wallgrowth','moss_amount',0.5):'moss_amount 0.05 (the look)',('wallgrowth','moss_amount',1.5):'moss_amount 0.3'}
items=[(d+f'dl_{l}_{dd}_{v}.jpg',names.get((l,dd,v),f'{l} {dd} {v}')) for l,dd,vals in rows for v in vals]
save(items,3,(266,400),'25 walls - what each main dial does.jpg')
