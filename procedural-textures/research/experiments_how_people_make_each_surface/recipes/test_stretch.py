# What this does: a tiny test recipe: stretched seamless noise (long streaks) to prove the builder works and tiles.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd

def build_node_group(parameters):
    b = bd.Builder('test stretch')
    n = b.tnoise(3, 40, detail=5, roughness=0.6, seed=1.0)
    m = b.maprange(n, 0.3, 0.7)
    colour = b.ramp(m, [(0.0, '#2a1a10'), (1.0, '#c08a50')])
    return b.finish(colour, m)
