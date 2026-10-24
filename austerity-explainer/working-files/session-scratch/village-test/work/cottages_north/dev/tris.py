import bpy, sys
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit import scene_read
rows=[]
for o in bpy.data.objects:
    if o.get('place_owner')=='cottages_north':
        o.data.calc_loop_triangles()
        b=len(o.data.loop_triangles); e=scene_read.triangle_count(o, evaluated=True)
        rows.append((e,b,o.name,[m.name+':'+str(getattr(m,'levels',''))+'/'+str(getattr(m,'render_levels','')) for m in o.modifiers]))
rows.sort(reverse=True)
for e,b,n,m in rows[:30]: print(f'{e:8d} {b:7d} {n:45s} {m}')
