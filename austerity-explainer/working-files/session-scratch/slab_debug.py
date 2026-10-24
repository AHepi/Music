import bpy, numpy as np
mesh=bpy.data.meshes.new('s')
# one square, wound the way the generator winds it (clockwise seen from +z after the y flip)
mesh.from_pydata([(0.2,0.2,0),(0.2,0.6,0),(0.6,0.6,0),(0.6,0.2,0)],[],[(0,1,2),(0,2,3)])
mesh.update()
print('normal z', [p.normal.z for p in mesh.polygons])
obj=bpy.data.objects.new('s',mesh); bpy.context.scene.collection.objects.link(obj)
for th in (0.02,-0.02):
    for off in (-1.0,1.0):
        m=obj.modifiers.new('slab','SOLIDIFY'); m.thickness=th; m.offset=off
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
        z=[v.co.z for v in me.vertices]; print('thickness',th,'offset',off,'z range',round(min(z),3),round(max(z),3), 'verts',len(z)); ev.to_mesh_clear()
        obj.modifiers.remove(m)
