import bpy, sys, runpy
args = sys.argv[sys.argv.index('--')+1:]
group_name, socket_name, out = args[0], args[1], args[2]
scale = float(args[3]) if len(args) > 3 else 1.0
for m in bpy.data.materials:
    if not m.name.startswith('PK ') or m.node_tree is None:
        continue
    t = m.node_tree
    g = next((n for n in t.nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == group_name), None)
    if g is None:
        continue
    em = t.nodes.new('ShaderNodeEmission')
    mul = t.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = scale
    t.links.new(g.outputs[socket_name], mul.inputs[0])
    col = t.nodes.new('ShaderNodeCombineColor')
    for i in range(3): t.links.new(mul.outputs[0], col.inputs[i])
    t.links.new(col.outputs[0], em.inputs['Color'])
    outn = next(n for n in t.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    t.links.new(em.outputs[0], outn.inputs['Surface'])
sys.argv = [sys.argv[0], '--', out, '800', '520', '8', '4.5', '-5.5', '2.4', '-0.3', '0', '1.1']
runpy.run_path('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/kit/preview.py', run_name='__main__')
