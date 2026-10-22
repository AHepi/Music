"""stage_final.py - the INTEGRATION owner's small touch-ups, applied AFTER the four builders' stages (wood, roof, ground, pond).
Plain words: only for things that looked clearly broken once everything was put together. Everything here edits materials that a builder made
(the integration step owns this fix; it is listed in the report). apply(options) is safe to run twice.
options: wall_patches (bool, default True) - the plaster-loss patches on the long walls were flat brown stickers; they now melt into the plaster
         (lighter, less saturated clay, softer edge). Nothing else is touched."""
import bpy

OWNER = 'final'


def _lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    c = [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c]
    return tuple(c) + (1.0,)


def _close(a, b, tol=0.02):
    return all(abs(x - y) < tol for x, y in zip(a[:3], b[:3]))


def soften_wall_patches(factor=0.62, clay_a='#8a7761', clay_b='#9f8c76', clay_dark='#6e5c4a'):
    done = []
    for m in bpy.data.materials:
        nt = m.node_tree
        if nt is None or nt.nodes.get('G6 loss') is None or nt.nodes.get('G6 clay colour noise') is None:
            continue
        if nt.nodes.get('G6 final patch soften') is not None:
            continue
        cn = nt.nodes['G6 clay colour noise']
        clay0 = clay = final = None
        for n in nt.nodes:
            if n.bl_idname != 'ShaderNodeMix' or n.data_type != 'RGBA':
                continue
            a_in = [i for i in n.inputs if i.identifier == 'A_Color'][0]
            b_in = [i for i in n.inputs if i.identifier == 'B_Color'][0]
            f_in = [i for i in n.inputs if i.identifier == 'Factor_Float'][0]
            if f_in.is_linked and f_in.links[0].from_node == cn:
                clay0 = n
            if (not b_in.is_linked) and _close(b_in.default_value, _lin('#5a4a3a')):
                clay = n
        if clay0 is None or clay is None:
            continue
        for n in nt.nodes:
            if n.bl_idname == 'ShaderNodeMix' and n.data_type == 'RGBA':
                b_in = [i for i in n.inputs if i.identifier == 'B_Color'][0]
                if b_in.is_linked and b_in.links[0].from_node == clay:
                    final = n
        if final is None:
            continue
        [i for i in clay0.inputs if i.identifier == 'A_Color'][0].default_value = _lin(clay_a)
        [i for i in clay0.inputs if i.identifier == 'B_Color'][0].default_value = _lin(clay_b)
        [i for i in clay.inputs if i.identifier == 'B_Color'][0].default_value = _lin(clay_dark)
        f_in = [i for i in final.inputs if i.identifier == 'Factor_Float'][0]
        if f_in.is_linked:
            src = f_in.links[0].from_socket
            mul = nt.nodes.new('ShaderNodeMath')
            mul.operation = 'MULTIPLY'
            mul.name = mul.label = 'G6 final patch soften'
            mul.inputs[1].default_value = factor
            nt.links.new(src, mul.inputs[0])
            nt.links.new(mul.outputs[0], f_in)
        done.append(m.name)
    return done


def apply(options=None):
    o = dict(options or {})
    rep = {'owner': OWNER, 'changed_materials': []}
    if o.get('wall_patches', True):
        rep['changed_materials'] += soften_wall_patches(o.get('patch_factor', 0.62))
    print('[stage_final]', rep, flush=True)
    return rep
