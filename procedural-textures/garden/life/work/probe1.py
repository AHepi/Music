import bpy, math
from mathutils import Vector
sc=bpy.context.scene
print('engine',sc.render.engine,'cam',sc.camera.name, sc.camera.location, sc.camera.data.lens)
for n in ['Maple trunk','Maple branch','Maple branch.001','Maple branch.002','Pine trunk','Pine limb','Pond water','Lily pads','Maple leaves','Maple inner mass','Pine pads','Fallen leaves','Bamboo stalks','Bamboo leaves','Bamboo fence','Astra / moss grouped bodies','Astra / pebbles grouped bodies','Astra / Courtyard receiving ground','Courtyard ground source']:
    o=bpy.data.objects[n]
    print(n,o.type,tuple(round(v,2) for v in o.location),[ (m.name) for m in o.data.materials], 'parent',o.parent.name if o.parent else None, 'hide',o.hide_render,o.hide_viewport, list(o.keys())[:8])
    if o.type=='MESH':
        me=o.data
        print('   attrs',[ (a.name,a.domain,a.data_type) for a in me.attributes][:12], 'uv',[u.name for u in me.uv_layers], 'smooth', sum(p.use_smooth for p in me.polygons),len(me.polygons))
# camera
cam=sc.camera
# materials of interest
for mn in ['Maple leaves','Maple inner mass','Pine needles','Pond water','Lily pad','Bark','Fallen leaves','Astra / moss tone 0','Astra / moss tone 1','Astra / moss tone 2','Astra / moss tone 3','Astra / pebbles tone 0','Bamboo stalk','Bamboo leaf colour','Lotus blossom','Moss and earth']:
    m=bpy.data.materials.get(mn)
    print('MAT',mn, m is not None and [ (n.bl_idname.replace('ShaderNode',''),n.name) for n in m.node_tree.nodes], m.use_backface_culling if m else None, m.blend_method if hasattr(m,'blend_method') else None)
    if m:
        b=m.node_tree.nodes.get('Principled BSDF')
        if b: print('   base',tuple(round(v,3) for v in b.inputs['Base Color'].default_value),'rough',b.inputs['Roughness'].default_value, 'ior',b.inputs['IOR'].default_value, 'trans', b.inputs['Transmission Weight'].default_value)
print([ (c.name,[o.name for o in c.objects][:3],len(c.objects)) for c in bpy.data.collections])
print('lights',[ (o.name,o.data.type,o.data.energy) for o in bpy.data.objects if o.type=='LIGHT'])
print('freestyle/world', sc.world.name)
print('sun', [o.rotation_euler for o in bpy.data.objects if o.name=='Golden hour sun'])
# stones positions
import re
for o in bpy.data.objects:
    if re.match(r'(Rock \d|Gravel rock|Stepping stone|Lantern (base|post|gallery|firebox|cap|finial|window))',o.name):
        print(o.name,tuple(round(v,2) for v in o.location),tuple(round(v,2) for v in o.dimensions))
