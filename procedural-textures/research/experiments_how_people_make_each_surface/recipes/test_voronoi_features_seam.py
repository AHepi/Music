# What this does: test recipe: shows one Voronoi feature on the seamless 4D "donut" so the tile edges can be checked.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd

def build_node_group(parameters):
    feature = parameters.get('feature', 'F1')
    b = bd.Builder('test voronoi')
    node = b.tvoronoi(parameters.get('su', 7), parameters.get('sv', 55), seed=1.0, feature=feature, metric=parameters.get('metric', 'EUCLIDEAN'))
    out = node.outputs['Radius'] if feature == 'N_SPHERE_RADIUS' else node.outputs['Distance']
    value = b.maprange(out, 0.0, parameters.get('top', 0.5))
    return b.finish(b.grey_to_colour(value), value)
