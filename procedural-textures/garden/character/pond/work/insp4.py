import bpy, numpy as np, math
for o in sorted(bpy.data.objects, key=lambda o:o.name):
    if o.name.startswith(('Maple trunk','Maple branch','Pine trunk','Pine limb')):
        sp=o.data.splines[0]
        print(o.name, o.type, "type", sp.type, "bevel", round(o.data.bevel_depth,3), "res", o.data.bevel_resolution, "cols", [c.name for c in o.users_collection])
        print("   pts", [(round(p.co.x,2),round(p.co.y,2),round(p.co.z,2),round(p.radius,3)) for p in sp.points])
lp=bpy.data.objects['Lily pads']; print("pad centres prop", lp.get('life_pad_centres'))
lb=bpy.data.objects['Lotus blossoms']; V=np.array([v.co[:] for v in lb.data.vertices]); print("lotus verts", V.round(2).tolist()[:36])
ic=bpy.data.objects['Life / iris clumps']; V=np.array([v.co[:] for v in ic.data.vertices]); print("iris bbox", V.min(0).round(2), V.max(0).round(2))
# cluster iris by xy
from collections import defaultdict
cl=defaultdict(list)
for v in V: cl[(round(v[0]/0.4),round(v[1]/0.4))].append(v)
for k,vs in cl.items(): a=np.array(vs); print("iris cluster", a.mean(0).round(2), len(a), a[:,2].max().round(2))
ls=bpy.data.objects['Life / lily stems']; V=np.array([v.co[:] for v in ls.data.vertices]); print("stems bbox", V.min(0).round(2), V.max(0).round(2), len(V))
# pad blobs: cluster pads vertices
pa=bpy.data.objects['Lily pads']; V=np.array([v.co[:] for v in pa.data.vertices]); print("pads z", V[:,2].min().round(3), V[:,2].max().round(3))
# Pine pad centres: find via vertex clustering in xy,z
pp=bpy.data.objects['Pine pads']; V=np.array([v.co[:] for v in pp.data.vertices]); print("pine pads bbox", V.min(0).round(2), V.max(0).round(2))
zs=np.histogram(V[:,2],bins=18); print("pine z hist", zs[0].tolist(), zs[1].round(2).tolist())
ml=bpy.data.objects['Maple leaves']; V=np.array([v.co[:] for v in ml.data.vertices]); print("maple pts", len(V), V.min(0).round(2), V.max(0).round(2))
mi=bpy.data.objects['Maple inner mass']; V=np.array([v.co[:] for v in mi.data.vertices]); print("inner mass", V.min(0).round(2), V.max(0).round(2))
# GN modifier details
md=ml.modifiers[0]; print("modifier", md.name, md.node_group.name, [ (k, md[k]) for k in md.keys()])
for a in ml.data.attributes:
    if not a.name.startswith('.'): 
        print("attr", a.name, a.data_type, a.domain)
ng=bpy.data.node_groups['Life / maple leaf instancer']; print([ (n.name,n.bl_idname) for n in ng.nodes])
for i in range(5):
    s=bpy.data.objects['Maple leaf source %d'%i]; print(s.name, len(s.data.vertices), len(s.data.polygons), [c.name for c in s.users_collection], s.hide_render, s.hide_viewport)
sc=bpy.context.scene
print("view layers", [vl.name for vl in sc.view_layers], "lightgroups", [lg.name for lg in sc.view_layers[0].lightgroups])
for c in sc.collection.children_recursive: pass
# light linking info for tree objects
for n in ['Maple leaves','Maple trunk','Maple inner mass','Pine pads','Pine trunk','Pond water']:
    o=bpy.data.objects[n]; print(n, "visible_shadow", o.visible_shadow, "visible_camera", o.visible_camera, "holdout", o.is_holdout)
