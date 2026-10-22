import bpy
g=bpy.data.objects['Lantern window glow']; l=bpy.data.objects['Lantern light']
vs=[g.matrix_world@v.co for v in g.data.vertices]
mn=[min(v[i] for v in vs) for i in range(3)]; mx=[max(v[i] for v in vs) for i in range(3)]
p=l.matrix_world.translation
print('LAMP light',[round(x,3) for x in p],'energy',l.data.energy,'type',l.data.type,'shadow',getattr(l.data,'use_shadow',None),'| glow box',[round(x,3) for x in mn],[round(x,3) for x in mx],'inside', all(mn[i]-1e-6<=p[i]<=mx[i]+1e-6 for i in range(3)))
fb=bpy.data.objects['Lantern firebox']; vs=[fb.matrix_world@v.co for v in fb.data.vertices]
mn=[min(v[i] for v in vs) for i in range(3)]; mx=[max(v[i] for v in vs) for i in range(3)]
print('LAMP firebox bbox',[round(x,3) for x in mn],[round(x,3) for x in mx],'light inside firebox bbox', all(mn[i]<=p[i]<=mx[i] for i in range(3)))
