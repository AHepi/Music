# What this does: tests the "Geometry Nodes route": real board meshes (one flat quad per board, with a gap between boards), each board
# given its own random window of the wood maps by writing a new UV map per board. The shader is then only a plain Image Texture
# reading the UV map. It renders a 4 x 4 tile area from above and prints how long it took and how many boards it made.
# Use:  blender -b --disable-autoexec -t 2 --python gn_boards.py
import math
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = 'proc-work/'
sys.path.insert(0, HERE)
sys.path.insert(0, PROC + 'lib')
import bake_harness as bh  # noqa: E402
import woodtests as wt  # noqa: E402

AREA = 4.0
SIZE = 1254.0


def enabled(sockets):
    for s in sockets:
        if s.enabled:
            return s
    raise RuntimeError('no enabled socket')


class GN:
    """Tiny helper: add nodes to a Geometry Nodes tree and link them; numbers are sockets, fields work like in the editor."""

    def __init__(self, tree):
        self.t = tree
        self.n = 0

    def node(self, idname, **settings):
        node = self.t.nodes.new(idname)
        node.location = ((self.n % 30) * 190, -(self.n // 30) * 240)
        self.n += 1
        for key, value in settings.items():
            setattr(node, key, value)
        return node

    def feed(self, socket, value):
        if isinstance(value, bpy.types.NodeSocket):
            self.t.links.new(value, socket)
        elif value is not None:
            socket.default_value = value

    def math(self, op, a, b=None, c=None):
        node = self.node('ShaderNodeMath', operation=op)
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.feed(node.inputs[i], float(v) if not isinstance(v, bpy.types.NodeSocket) else v)
        return node.outputs[0]

    def add(self, a, b): return self.math('ADD', a, b)
    def sub(self, a, b): return self.math('SUBTRACT', a, b)
    def mul(self, a, b): return self.math('MULTIPLY', a, b)
    def div(self, a, b): return self.math('DIVIDE', a, b)
    def greater(self, a, b): return self.math('GREATER_THAN', a, b)

    def combine(self, x, y, z=0.0):
        node = self.node('ShaderNodeCombineXYZ')
        for name, v in zip(('X', 'Y', 'Z'), (x, y, z)):
            self.feed(node.inputs[name], v)
        return node.outputs[0]

    def separate(self, vec):
        node = self.node('ShaderNodeSeparateXYZ')
        self.feed(node.inputs[0], vec)
        return node.outputs['X'], node.outputs['Y']

    def random(self, seed, id_socket, lo=0.0, hi=1.0):
        node = self.node('FunctionNodeRandomValue', data_type='FLOAT')
        self.feed(enabled([s for s in node.inputs if s.name == 'Min' and s.type == 'VALUE']), lo)
        self.feed(enabled([s for s in node.inputs if s.name == 'Max' and s.type == 'VALUE']), hi)
        self.feed(node.inputs['ID'], id_socket)
        node.inputs['Seed'].default_value = seed
        return enabled([s for s in node.outputs if s.name == 'Value' and s.type == 'VALUE'])

    def named(self, name, data_type):
        node = self.node('GeometryNodeInputNamedAttribute', data_type=data_type)
        node.inputs['Name'].default_value = name
        return enabled([s for s in node.outputs if s.name == 'Attribute'])

    def store(self, geometry, name, value, data_type, domain):
        node = self.node('GeometryNodeStoreNamedAttribute', data_type=data_type, domain=domain)
        node.inputs['Name'].default_value = name
        self.feed(node.inputs['Geometry'], geometry)
        self.feed(enabled([s for s in node.inputs if s.name == 'Value']), value)
        return node.outputs['Geometry']


def build_boards_tree(seed=3):
    tree = bpy.data.node_groups.new('wood boards', 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g = GN(tree)
    out = g.node('NodeGroupOutput')
    # ---- 1. where the boards go: a grid of board centres (10 per row, 20 rows), each row shifted sideways by chance
    grid = g.node('GeometryNodeMeshGrid')
    grid.inputs['Size X'].default_value, grid.inputs['Size Y'].default_value = 4.5, 3.8
    grid.inputs['Vertices X'].default_value, grid.inputs['Vertices Y'].default_value = 10, 20
    pts = g.node('GeometryNodeMeshToPoints')
    g.feed(pts.inputs['Mesh'], grid.outputs['Mesh'])
    pos = g.node('GeometryNodeInputPosition').outputs['Position']
    px, py = g.separate(pos)
    row = g.math('ROUND', g.div(g.add(py, 1.9), 0.2))                      # row number from the height of the point
    shift = g.random(seed, row, 0.0, 0.5)
    setpos = g.node('GeometryNodeSetPosition')
    g.feed(setpos.inputs['Geometry'], pts.outputs['Points'])
    g.feed(setpos.inputs['Offset'], g.combine(g.sub(2.25, shift), 2.0, 0.0))
    # ---- 2. the board: one quad with its own local UV (0..1), instanced on every point and made a little smaller than its cell (the gap)
    quad = g.node('GeometryNodeMeshGrid')
    quad.inputs['Size X'].default_value = quad.inputs['Size Y'].default_value = 1.0
    quad.inputs['Vertices X'].default_value = quad.inputs['Vertices Y'].default_value = 2
    quad_mesh = g.store(quad.outputs['Mesh'], 'UVMap', quad.outputs['UV Map'], 'FLOAT2', 'CORNER')
    inst = g.node('GeometryNodeInstanceOnPoints')
    g.feed(inst.inputs['Points'], setpos.outputs['Geometry'])
    g.feed(inst.inputs['Instance'], quad_mesh)
    g.feed(inst.inputs['Scale'], g.combine(0.485, 0.19, 1.0))
    index = g.node('GeometryNodeInputIndex').outputs['Index']
    with_id = g.store(inst.outputs['Instances'], 'board_id', index, 'INT', 'INSTANCE')
    real = g.node('GeometryNodeRealizeInstances')
    g.feed(real.inputs['Geometry'], with_id)
    # ---- 3. each board's own window of the maps, written as a new UV map
    board = g.named('board_id', 'INT')
    x0 = g.random(seed + 1, board, 0.0, 1.0)                               # where along the source row this board starts (0..1, scaled below)
    flip = g.greater(g.random(seed + 2, board, 0.0, 1.0), 0.5)             # read it backwards?
    band = g.math('FLOOR', g.random(seed + 3, board, 0.0, 3.999))          # which of the 4 clean source rows
    ge = lambda k: g.greater(band, k - 0.5)
    start = g.add(g.add(g.add(180.0, g.mul(ge(1), 277.0)), g.mul(ge(2), 240.0)), g.mul(ge(3), 270.0))
    length = g.add(g.add(g.add(277.0, g.mul(ge(1), -37.0)), g.mul(ge(2), 30.0)), g.mul(ge(3), 17.0))
    uv = g.named('UVMap', 'FLOAT_VECTOR')
    u, v = g.separate(uv)
    uf = g.add(u, g.mul(flip, g.sub(g.mul(u, -2.0), -1.0)))                # u, or 1 - u when flipped
    window = g.mul(length, 2.425)                                          # the board is 0.485 tile wide, a row is 0.2 tile high: same dots per dot
    x_dots = g.add(g.mul(x0, g.sub(SIZE, window)), g.mul(uf, window))
    y_dots = g.add(start, g.mul(g.sub(1.0, v), length))
    new_uv = g.combine(g.div(x_dots, SIZE), g.sub(1.0, g.div(y_dots, SIZE)))
    stored = g.store(real.outputs['Geometry'], 'UVMap', new_uv, 'FLOAT2', 'CORNER')
    setmat = g.node('GeometryNodeSetMaterial')
    g.feed(setmat.inputs['Geometry'], stored)
    tree.links.new(setmat.outputs['Geometry'], out.inputs[0])
    return tree, setmat


def material_for(channel):
    material = bpy.data.materials.new('boards ' + channel)
    material.use_nodes = True
    t = material.node_tree
    t.nodes.clear()
    coord = t.nodes.new('ShaderNodeTexCoord')
    img = t.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(wt.PATH_C if channel == 'colour' else wt.PATH_H, check_existing=True)
    img.image.colorspace_settings.name = 'sRGB' if channel == 'colour' else 'Non-Color'
    img.extension = 'EXTEND'
    t.links.new(coord.outputs['UV'], img.inputs['Vector'])
    emit = t.nodes.new('ShaderNodeEmission')
    out = t.nodes.new('ShaderNodeOutputMaterial')
    t.links.new(img.outputs['Color'], emit.inputs['Color'])
    t.links.new(emit.outputs[0], out.inputs['Surface'])
    return material


def main():
    scene, tile = bh.new_bake_scene(1024)
    scene.cycles.samples = 8
    tile.hide_render = True
    camera = scene.camera
    camera.data.ortho_scale = AREA
    camera.location = (AREA / 2.0, AREA / 2.0, 5.0)
    mesh = bpy.data.meshes.new('wood floor')
    obj = bpy.data.objects.new('wood floor', mesh)
    scene.collection.objects.link(obj)
    started = time.time()
    tree, setmat = build_boards_tree()
    modifier = obj.modifiers.new('boards', 'NODES')
    modifier.node_group = tree
    for channel in ('colour', 'height'):
        material = material_for(channel)
        setmat.inputs['Material'].default_value = material
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = obj.evaluated_get(depsgraph)
        eval_mesh = evaluated.to_mesh()
        print(f'[gn] {channel}: faces made = {len(eval_mesh.polygons)}, uv layers = {[l.name for l in eval_mesh.uv_layers]}, attributes = {[a.name for a in eval_mesh.attributes][:12]}', flush=True)
        evaluated.to_mesh_clear()
        path = os.path.join(HERE, 'renders', f'gn_boards_4x4_{channel}.png')
        bh.render_to(scene, path, linear_data=(channel == 'height'), sixteen_bit=False)
        print(f'[gn] {channel} done, {time.time() - started:.1f} s since start -> {path}', flush=True)


if __name__ == '__main__':
    main()
