# exec snippet: p['v'] = dict(nm=strength or None, bump=strength or None, mbump=strength or None, smooth=angle_deg or None)
import bpy, math
v = p['v']
m = bpy.data.materials.get('G6 roof / ceramic')
nt = m.node_tree
if '_orig' not in m:
    m['_orig'] = [nt.nodes['G6 NM'].inputs['Strength'].default_value, nt.nodes['Bump'].inputs['Strength'].default_value, nt.nodes['G6 moss bump'].inputs['Strength'].default_value]
o = m['_orig']
nt.nodes['G6 NM'].inputs['Strength'].default_value = o[0] if v.get('nm') is None else v['nm']
nt.nodes['Bump'].inputs['Strength'].default_value = o[1] if v.get('bump') is None else v['bump']
nt.nodes['G6 moss bump'].inputs['Strength'].default_value = o[2] if v.get('mbump') is None else v['mbump']
for me in bpy.data.meshes:
    if me.name in ('G6 roof / pan', 'G6 roof / pan chipped a', 'G6 roof / pan chipped b', 'G6 roof / pan chipped c', 'G6 roof / pan cracked'):
        if v.get('smooth'):
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(v['smooth']))
        else:
            me.shade_flat()
print('DBGROOF', v, flush=True)
