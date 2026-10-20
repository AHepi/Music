# What this does: creates the stylising compositor nodes in Blender 5.2.2 and prints their settings (with allowed values) and input sockets
# (with default values), so the guide quotes real names, not guesses. Also tests how to switch the compositor on in 5.x.
import bpy
scene = bpy.context.scene

try:
    tree = bpy.data.node_groups.new('probe', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    print('made a compositing node group:', tree.name, tree.bl_idname)
except Exception as e:
    print('FAILED to make compositing group:', repr(e))
    raise
kinds = ['CompositorNodeKuwahara', 'CompositorNodePosterize', 'CompositorNodePixelate', 'CompositorNodeFilter', 'CompositorNodeDilateErode',
         'CompositorNodeBlur', 'CompositorNodeBilateralblur', 'CompositorNodeDespeckle', 'CompositorNodeMaskToSDF', 'CompositorNodeConvolve',
         'CompositorNodeImage', 'CompositorNodeRLayers', 'CompositorNodeCrop', 'CompositorNodeTransform', 'CompositorNodeScale', 'CompositorNodeRGBToBW',
         'CompositorNodeAntiAliasing', 'CompositorNodeInpaint', 'CompositorNodeImageCoordinates', 'CompositorNodeOutputFile', 'CompositorNodeViewer',
         'CompositorNodeTranslate', 'CompositorNodeSeparateColor', 'CompositorNodeCombineColor', 'CompositorNodeNormal']
base = {p.identifier for p in bpy.types.Node.bl_rna.properties} | {p.identifier for p in bpy.types.NodeInternal.bl_rna.properties} | {'rna_type', 'type'}
for kind in kinds:
    try:
        node = tree.nodes.new(kind)
    except Exception as e:
        print('==', kind, 'FAILED', e)
        continue
    print('==', kind, '| label:', node.bl_label)
    for prop in node.bl_rna.properties:
        if prop.identifier in base or prop.identifier in ('inputs', 'outputs', 'internal_links', 'location_absolute'):
            continue
        extra = ''
        if prop.type == 'ENUM':
            extra = ' options=' + str([i.identifier for i in prop.enum_items])
        try:
            value = getattr(node, prop.identifier)
        except Exception:
            value = '?'
        print(f'   setting {prop.identifier} ({prop.type}) = {value!r}{extra}')
    for s in node.inputs:
        dv = getattr(s, 'default_value', None)
        try:
            dv = tuple(dv)
        except TypeError:
            pass
        print(f'   input  {s.name!r} [{s.type}] default={dv!r}')
    for s in node.outputs:
        print(f'   output {s.name!r} [{s.type}]')
