import bpy
m = bpy.data.materials['street_setts']
t = m.node_tree
p = next(n for n in t.nodes if n.type=='BSDF_PRINCIPLED')
print('PRINCIPLED', [i.name for i in p.inputs][:12], [ (i.name, i.identifier) for i in p.inputs if i.name in ('Specular IOR Level','Coat Weight','Metallic','Normal','Base Color','Roughness')])
n = t.nodes.new('ShaderNodeValue'); n['wk'] = 'origin'; print('TAG', n['wk'], n.get('wk'), n.get('missing'), 'wk' in n)
print('NODES', [(x.name, x.bl_idname) for x in t.nodes])
print('LINKS', [(l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in t.links])
out = next(n for n in t.nodes if n.type=='OUTPUT_MATERIAL'); print('OUT', out.target, out.is_active_output)
print('ID props on mesh obj ok:', bpy.data.objects['street_setts'].get('x'))
# counts of materials
import collections
c = collections.Counter()
for mat in bpy.data.materials:
    if not mat.node_tree: c['none']+=1; continue
    pr = [n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED']
    c[len(pr)] += 1
print('PRINCIPLED COUNTS', dict(c), len(bpy.data.materials))
