# Plain note: tiny helper that writes a Material Maker graph file (.ptex, plain JSON) from Python, so graphs can be made by a script
# (no mouse needed). Add nodes by their type name (the file name in the app's nodes/ folder, e.g. 'bricks3', 'colorize'),
# join them with connect(from, from_port, to, to_port), save with save(path).
# Colours are (r, g, b) numbers 0..1; a gradient is a list of (position, (r, g, b)) pairs.
import json
import os

NODE_FOLDER = 'proc-work/third-party/material_maker/app/material_maker_1_7_linux/nodes/'


def colour(rgb, a=1.0):
    return {'a': a, 'r': rgb[0], 'g': rgb[1], 'b': rgb[2], 'type': 'Color'}


def gradient(points, interpolation=1):
    """points: [(pos, (r,g,b)) or (pos, (r,g,b,a))]; interpolation 0=constant,1=linear,2=smoothstep,3=cubic"""
    out = []
    for p in points:
        pos, c = p
        a = c[3] if len(c) > 3 else 1.0
        out.append({'pos': pos, 'r': c[0], 'g': c[1], 'b': c[2], 'a': a})
    return {'type': 'Gradient', 'interpolation': interpolation, 'points': out}


class Graph:
    def __init__(self, name='graph'):
        self.name = name
        self.nodes = []
        self.connections = []
        self._n = 0

    def add(self, type_, name=None, params=None, seed=None, pos=None):
        name = name or f'{type_}_{self._n}'
        self._n += 1
        node = {'name': name, 'type': type_, 'node_position': {'x': (pos or (self._n * 200, 0))[0], 'y': (pos or (self._n * 200, 0))[1]}, 'parameters': params or {}}
        if seed is not None:
            # found by testing: the graph file key is 'seed' (a number); the key 'seed_int' (used inside the app's node definition files) is ignored
            node['seed'] = float(seed)
            node['seed_locked'] = True
        self.nodes.append(node)
        return name

    def connect(self, a, a_port, b, b_port):
        self.connections.append({'from': a, 'from_port': a_port, 'to': b, 'to_port': b_port})

    def material(self, name='Material', size_exponent=11, **params):
        p = {'albedo_color': colour((1, 1, 1)), 'ao': 1, 'depth_scale': 0.5, 'emission_energy': 1, 'flags_transparent': False,
             'metallic': 0, 'normal': 1, 'roughness': 1, 'size': size_exponent, 'sss': 0}
        p.update(params)
        return self.add('material', name, p)

    def to_dict(self):
        return {'connections': self.connections, 'label': 'Graph', 'name': self.name, 'node_position': {'x': 0, 'y': 0}, 'nodes': self.nodes, 'parameters': {}, 'type': 'graph'}

    def check_names(self):
        """Material Maker silently ignores setting names it does not know (found by testing: 'amount' on a Blend node did nothing because
        the real name is 'amount1'). This compares every setting name with the names in the node's own definition file and returns a list of complaints."""
        problems = []
        for n in self.nodes:
            f = NODE_FOLDER + n['type'] + '.mmg'
            if not os.path.exists(f):
                problems.append(f"{n['name']}: unknown node type '{n['type']}'")
                continue
            d = json.load(open(f))
            known = set(d.get('parameters', {}).keys())
            for pdef in d.get('shader_model', {}).get('parameters', []):
                known.add(pdef['name'].replace('#', '1'))
            for k in n.get('parameters', {}):
                if known and k not in known:
                    problems.append(f"{n['name']} ({n['type']}): setting '{k}' is not one of {sorted(known)}")
        return problems

    def save(self, path):
        for problem in self.check_names():
            print('WARNING', problem)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=1)
