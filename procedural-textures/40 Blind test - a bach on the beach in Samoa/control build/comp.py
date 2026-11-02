import bpy

def setup(sc, bloom=0.35, vignette=0.40, thresh=0.9):
    ng = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
    sc.compositing_node_group = ng
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new('CompositorNodeRLayers')
    gl = ng.nodes.new('CompositorNodeGlare')
    gl.inputs['Type'].default_value = 'Bloom'
    gl.inputs['Threshold'].default_value = thresh
    gl.inputs['Strength'].default_value = bloom
    gl.inputs['Size'].default_value = 0.6
    ng.links.new(rl.outputs['Image'], gl.inputs['Image'])
    # vignette
    em = ng.nodes.new('CompositorNodeEllipseMask')
    em.inputs['Position'].default_value = (0.5, 0.5)
    em.inputs['Size'].default_value = (1.05, 0.95)
    bl = ng.nodes.new('CompositorNodeBlur')
    bl.inputs['Size'].default_value = (0.0, 0.0) if False else bl.inputs['Size'].default_value
    bl.name = 'VigBlur'
    bl.inputs['Size'].default_value = (100.0, 180.0)
    ng.links.new(em.outputs[0], bl.inputs['Image'])
    mm = ng.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY_ADD'
    ng.links.new(bl.outputs[0], mm.inputs[0]); mm.inputs[1].default_value = vignette; mm.inputs[2].default_value = 1.0 - vignette
    mx = ng.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    ng.links.new(gl.outputs[0], mx.inputs[6]); ng.links.new(mm.outputs[0], mx.inputs[7])
    go = ng.nodes.new('NodeGroupOutput')
    ng.links.new(mx.outputs[2], go.inputs[0])
    return ng
