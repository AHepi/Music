# What this does: tests whether Blender 5.2 lets a SHADER material use a repeat zone (a loop of nodes), made from Python, and renders it.
# The loop visits the 9 neighbouring grid cells of each dot and paints a soft round dot for each cell that has a random "stamp";
# that is exactly the loop that texture bombing needs. It renders a small picture and prints whether it worked.
import os, sys, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = 'proc-work/'
sys.path.insert(0, HERE); sys.path.insert(0, PROC + 'lib')
import bake_harness as bh, nodekit as nk
scene, tile = bh.new_bake_scene(512)
scene.cycles.samples = 4
mat = bpy.data.materials.new('zone'); mat.use_nodes = True
tree = mat.node_tree; tree.nodes.clear()
kit = nk.Kit(tree)
try:
    rin = tree.nodes.new('GeometryNodeRepeatInput')
    rout = tree.nodes.new('GeometryNodeRepeatOutput')
    rin.pair_with_output(rout)
    print('REPEAT ZONE nodes created in a shader tree: OK')
    print('repeat_items api:', [a for a in dir(rout.repeat_items) if not a.startswith('_')])
    rout.repeat_items.clear()
    rout.repeat_items.new('FLOAT', 'acc')
    rout.repeat_items.new('FLOAT', 'i')
    print('inputs of repeat input:', [s.name for s in rin.inputs], 'outputs:', [s.name for s in rin.outputs])
    print('outputs of repeat output:', [s.name for s in rout.outputs], 'inputs:', [s.name for s in rout.inputs])
except Exception as error:
    print('REPEAT ZONE FAILED to create:', repr(error))
    raise SystemExit
# loop body: iteration counter i (0..8) gives the neighbour cell offset (dx, dy); acc = max(acc, dot of that neighbour cell)
u, v = kit.uv()
cells = 6.0
cx, cy = kit.floor(u * cells), kit.floor(v * cells)
rin.inputs['Iterations'].default_value = 9
# state inputs: acc and i start at 0
rin.inputs['acc'].default_value = 0.0
rin.inputs['i'].default_value = 0.0
i_in = nk.S(kit, rin.outputs['i']); acc_in = nk.S(kit, rin.outputs['acc'])
dx = (i_in % 3.0) - 1.0
dy = kit.floor(i_in / 3.0) - 1.0
nx, ny = cx + dx, cy + dy
q1, q2, q3 = kit.rand(nx, ny, 3.0, 1.0)
px, py = (nx + 0.2 + 0.6 * q1) / cells, (ny + 0.2 + 0.6 * q2) / cells
dist = kit.sqrt((u - px) * (u - px) + (v - py) * (v - py)) * cells
dot = (1.0 - kit.smoothstep(0.35, 0.5, dist)) * kit.less(q3, 0.7)
new_acc = kit.maximum(acc_in, dot)
tree.links.new(new_acc.sock, rout.inputs['acc'])
tree.links.new((i_in + 1.0).sock, rout.inputs['i'])
result = nk.S(kit, rout.outputs['acc'])
kit.emit_grey(result)
tile.data.materials.append(mat)
try:
    bh.render_to(scene, os.path.join(HERE, 'renders', 'repeat_zone_dots.png'), True)
    print('RENDER with repeat zone in Cycles: done')
except Exception as error:
    print('RENDER FAILED', repr(error))
