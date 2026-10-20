# What this does: prints the allowed options of every menu socket of the stylising compositor nodes (by setting a wrong value on purpose and reading the error).
import bpy
tree = bpy.data.node_groups.new('probe', 'CompositorNodeTree')
for kind in ('CompositorNodeKuwahara', 'CompositorNodeFilter', 'CompositorNodeDilateErode', 'CompositorNodeBlur', 'CompositorNodeConvolve', 'CompositorNodeTransform', 'CompositorNodeScale', 'CompositorNodeTranslate'):
    node = tree.nodes.new(kind)
    for s in node.inputs:
        if s.type == 'MENU':
            try:
                s.default_value = '__nope__'
            except TypeError as e:
                text = str(e)
                print(kind, '|', s.name, '|', text[text.index('not found in'):] if 'not found in' in text else text)
for kind in ('ShaderNodeMath', 'ShaderNodeMix', 'ShaderNodeValToRGB', 'ShaderNodeMapRange'):
    try:
        tree.nodes.new(kind); print('shader node usable in the compositor tree:', kind)
    except Exception as e:
        print('NOT usable in compositor tree:', kind, repr(e)[:100])
