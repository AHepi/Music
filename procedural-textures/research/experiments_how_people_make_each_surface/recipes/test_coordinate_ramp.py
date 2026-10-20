# What this does: test recipe: colour = u in red, v in green, so the exact coordinate seen by every pixel can be read back from the picture.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd

def build_node_group(parameters):
    b = bd.Builder('test coordinate ramp')
    u, v = b.uv_xy()
    node = b.node('ShaderNodeCombineColor')
    b._put(node, 'Red', u); b._put(node, 'Green', v); b._put(node, 'Blue', 0.0)
    return b.finish(node.outputs[0], v)
