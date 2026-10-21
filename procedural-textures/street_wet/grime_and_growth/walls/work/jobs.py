import json, sys
def J(name, look, cam='main', light='A', state='wet', size=(540,960,16), view='beauty', **kw):
    return dict(name=name, camera=cam, light=light, state=state, look=look, view=view, size=list(size), **kw)
PL=(1536,2730,48)
def plate_jobs(look, tag, cam='main', light='A', state='wet', parts=(), size=PL, mask=True):
    j=[J(f'{tag}_{cam}', look, cam, light, state, size, keep_png=True, plate_height=size[1])]
    return j
FACE_CAMS=[dict(name='right02',location=[-2.0,6.25,3.87],look_at=[4.15,6.25,3.87],fov_v=58.0),
           dict(name='left02',location=[2.0,6.25,3.87],look_at=[-4.15,6.25,3.87],fov_v=58.0),
           dict(name='right03',location=[-2.0,10.75,4.19],look_at=[4.15,10.75,4.19],fov_v=58.0),
           dict(name='left03',location=[2.0,10.75,4.19],look_at=[-4.15,10.75,4.19],fov_v=58.0)]
FS=(1000,1500,24)
def face_jobs(look, tag, cams=('right02','left02'), views=(), light='A', state='wet', dials=None, base=True):
    jobs=[]
    for c in cams:
        if base: jobs.append(J(f'f_base_{c}','base',cam=c,light=light,state=state,size=FS,plate_height=2730))
        d=dict(dials=dials) if dials else {}
        jobs.append(J(f'f_{tag}_{c}',look,cam=c,light=light,state=state,size=FS,plate_height=2730,**d))
        for v in views:
            jobs.append(J(f'fm_{tag}_{v.replace(":","_")}_{c}',look,cam=c,view=v,size=(FS[0],FS[1],1),plate_height=2730,**d))
        jobs.append(J(f'f_class_{c}','base',cam=c,view='class',size=(FS[0],FS[1],1),plate_height=2730))
    return jobs
