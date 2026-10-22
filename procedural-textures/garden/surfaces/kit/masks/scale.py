# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE SCALE HELPER (node group WK SCALE) and the MARK-WIDTH HELPER (WK MARK WIDTH). Every mark a layer paints is sized in PLATE DOTS (one dot of the plate picture the painter
# repaints) and the kit turns that into metres from the camera, so a crack is never thinner than a few dots and a streak never thinner than about eight, however far away.
# WK SCALE inputs (the runner sets Dot Angle per picture from the camera and the plate size; the other four default from the set's `detail` block):
#   Dot Angle        tangent of the angle one plate dot covers = 2 x tan(half the camera's vertical field of view) / plate height in dots (a 540 x 960 test picture uses the
#                    PLATE's value, so a mark has the same physical size in a small test picture as in the plate)
#   Painter Widen    0.5 / painter scale (x1.11 at 0.45, x1.25 at 0.40): the painter receives the plate shrunk, so marks are widened to survive
#   Fade Start, Fade End      metres from the camera where fine detail starts and finishes giving way to the layer's average tone
#   Handover Start, Handover End   metres across which 3D pieces stop and the painted far band takes over
# outputs: Distance (straight, metres), Dot Across (metres per plate dot across the view at this point = depth x Dot Angle x Painter Widen),
#   Dot Along (how long a dot is ALONG the way the surface leans away = Dot Across / max(|normal . view direction|, 0.12)), Fade Near (1 near, 0 far), Far Blend (0 near, 1 far),
#   Cos View (|normal . view direction|).
# WK MARK WIDTH: inputs Real Width (m), Min Dots, Dot Size (m: Dot Across or Dot Along), Inflate Limit; outputs Width (m) = max(real, Min Dots x Dot Size) and Fade = 1 while the
# widening is within the limit, falling to 0 by twice the limit (beyond that the mark gives way to the layer's average tone instead of being drawn fatter).
import bpy

from apply import nodes

SCALE_NAME = 'WK SCALE'
MARK_NAME = 'WK MARK WIDTH'


def build_scale_group():
    existing = bpy.data.node_groups.get(SCALE_NAME)
    if existing is not None:
        return existing
    inputs = [('Dot Angle', 'NodeSocketFloat', 0.0002666), ('Painter Widen', 'NodeSocketFloat', 1.111), ('Fade Start', 'NodeSocketFloat', 12.0), ('Fade End', 'NodeSocketFloat', 40.0),
              ('Handover Start', 'NodeSocketFloat', 14.0), ('Handover End', 'NodeSocketFloat', 22.0)]
    outputs = [('Distance', 'NodeSocketFloat'), ('Dot Across', 'NodeSocketFloat'), ('Dot Along', 'NodeSocketFloat'), ('Fade Near', 'NodeSocketFloat'), ('Far Blend', 'NodeSocketFloat'),
               ('Cos View', 'NodeSocketFloat')]
    tree, gin, gout = nodes.new_group(SCALE_NAME, inputs, outputs)
    n = nodes.Net(tree)
    g = lambda name: gin.outputs[name]   # noqa: E731
    camera = n.new('ShaderNodeCameraData')
    geometry = n.geometry()
    depth, distance = camera.outputs['View Z Depth'], camera.outputs['View Distance']
    across = n.math('MULTIPLY', n.math('MULTIPLY', depth, g('Dot Angle')), g('Painter Widen'))
    incoming = n.vector_math('NORMALIZE', geometry.outputs['Incoming'])
    cos_view = n.math('ABSOLUTE', n.vector_math('DOT_PRODUCT', n.vector_math('NORMALIZE', geometry.outputs['Normal']), incoming))
    along = n.math('DIVIDE', across, n.math('MAXIMUM', cos_view, 0.12))
    fade_near = n.one_minus(n.map_range(distance, g('Fade Start'), n.math('MAXIMUM', g('Fade End'), n.math('ADD', g('Fade Start'), 0.01)), 0.0, 1.0, smooth=True))
    far_blend = n.map_range(distance, g('Handover Start'), n.math('MAXIMUM', g('Handover End'), n.math('ADD', g('Handover Start'), 0.01)), 0.0, 1.0, smooth=True)
    for name, socket in (('Distance', distance), ('Dot Across', across), ('Dot Along', along), ('Fade Near', fade_near), ('Far Blend', far_blend), ('Cos View', cos_view)):
        tree.links.new(socket, gout.inputs[name])
    return tree


def build_mark_width_group():
    existing = bpy.data.node_groups.get(MARK_NAME)
    if existing is not None:
        return existing
    inputs = [('Real Width', 'NodeSocketFloat', 0.02), ('Min Dots', 'NodeSocketFloat', 3.0), ('Dot Size', 'NodeSocketFloat', 0.003), ('Inflate Limit', 'NodeSocketFloat', 6.0)]
    tree, gin, gout = nodes.new_group(MARK_NAME, inputs, [('Width', 'NodeSocketFloat'), ('Fade', 'NodeSocketFloat')])
    n = nodes.Net(tree)
    g = lambda name: gin.outputs[name]   # noqa: E731
    real = n.math('MAXIMUM', g('Real Width'), 1e-6)
    width = n.math('MAXIMUM', real, n.math('MULTIPLY', n.math('MAXIMUM', g('Min Dots'), 0.0), n.math('MAXIMUM', g('Dot Size'), 0.0)))
    ratio = n.math('DIVIDE', width, real)
    limit = n.math('MAXIMUM', g('Inflate Limit'), 1.0)
    fade = n.one_minus(n.map_range(ratio, limit, n.math('MULTIPLY', limit, 2.0), 0.0, 1.0, smooth=True))
    tree.links.new(width, gout.inputs['Width'])
    tree.links.new(fade, gout.inputs['Fade'])
    return tree


def dot_angle(fov_vertical_deg, plate_height_dots):
    import math
    return 2.0 * math.tan(math.radians(fov_vertical_deg) / 2.0) / float(plate_height_dots)


def painter_widen(painter_scale):
    return 0.5 / float(painter_scale)


def add_scale_node(tree, settings=None, location=(0, 0)):
    node = tree.nodes.new('ShaderNodeGroup')
    node.node_tree = build_scale_group()
    node.name = 'WK SCALE'
    node.label = 'WK SCALE'
    node.location = location
    node['wk'] = 'scale'
    if settings is not None:
        detail = settings.get('detail') or {}
        plate = settings.get('plate') or {}
        node.inputs['Fade Start'].default_value = detail.get('fade_start_m', 12.0)
        node.inputs['Fade End'].default_value = detail.get('fade_end_m', 40.0)
        handover = detail.get('far_band_handover_m', [14.0, 22.0])
        node.inputs['Handover Start'].default_value, node.inputs['Handover End'].default_value = handover
        node.inputs['Painter Widen'].default_value = painter_widen(plate.get('painter_scale', 0.45))
        size = plate.get('size')
        if size:
            node.inputs['Dot Angle'].default_value = dot_angle(40.0, size[1])
    return node


def set_scale(kit, dot_angle_value=None, painter_widen_value=None):
    """Sets Dot Angle and Painter Widen on every WK SCALE node of the scene's materials (the runner calls this for each picture)."""
    count = 0
    for material in bpy.data.materials:
        tree = material.node_tree
        if tree is None:
            continue
        for node in tree.nodes:
            if node.get('wk') == 'scale':
                if dot_angle_value is not None:
                    node.inputs['Dot Angle'].default_value = dot_angle_value
                if painter_widen_value is not None:
                    node.inputs['Painter Widen'].default_value = painter_widen_value
                count += 1
    return count
