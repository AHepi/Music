"""
What this file does:
Puts what a tree drops at its foot. Under a palm: dead fronds lying where they fell, coconuts, split husks and husk
fibre. Under any other tree: fallen leaves and twigs, thickest near the trunk and thinning out to the edge of the crown.

Trees are found by their trunks: wood-role things named trunk, tree, palm, coconut, bark, branch or bough that stand
more than 1.5 m tall. Palms are the ones named palm or coconut. A mast, a flagpole or a post is not a tree. Only what the camera can see,
nearer than 40 metres, is placed, and everything rests on the ground found below it.

    import lay_trees
    report = lay_trees.lay_tree_fall(seen, roles, collection, litter=1.0)

Everything added is named "DETAIL • tree ..." and goes with lay_details.remove_details().
"""

import math
import random
import re

import bpy
from mathutils import Vector

import lay_timber

PREFIX = 'DETAIL • tree '
PALM_WORDS = {'palm', 'coconut', 'niu'}


def _material(name, low, high, roughness, scale=30.0):
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    principled.inputs['Roughness'].default_value = roughness
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    tex = nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = 5.0
    links.new(position, tex.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*low, 1)
    ramp.color_ramp.elements[1].color = (*high, 1)
    links.new(tex.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    material.diffuse_color = (*low, 1)
    return material


def trees(scene, roles):
    """(trunk object, foot point, height, is_palm, trunk radius) for every trunk."""
    found = []
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.name.startswith(('DETAIL •', 'LOOK •', 'TIMBER •', 'FACADE •')) or obj.get('prototype'):
            continue
        role = roles.get(obj.name)
        if lay_timber.timber_kind(obj, role) != 'bark':
            continue
        matrix = obj.matrix_world
        points = [matrix @ v.co for v in obj.data.vertices]
        if not points:
            continue
        low = min(p.z for p in points)
        high = max(p.z for p in points)
        if high - low < 1.5:
            continue
        bottom = [p for p in points if p.z < low + 0.3]
        foot = sum(bottom, Vector((0, 0, 0))) / len(bottom)
        radius = max(((p - foot).to_2d().length for p in bottom), default=0.2)
        words = set(re.findall(r'[a-z]+', obj.name.lower()))
        found.append((obj, foot, high - low, bool(words & PALM_WORDS), radius))
    return found


def _frond(rng, ground_z_at, base, heading, verts, faces, slots):
    """A dead palm frond lying on the ground: a curved midrib and two rows of drooping, splayed leaflets."""
    length = rng.uniform(1.8, 3.3)
    pairs = rng.randint(16, 26)
    curl = rng.uniform(-0.25, 0.25)
    rib = []
    for k in range(pairs + 1):
        t = k / pairs
        angle = heading + curl * t * t
        p = base + Vector((math.cos(angle), math.sin(angle), 0)) * (length * t)
        rib.append((p, angle))
    # midrib: a flat strip, wide at the base
    rib_z = []
    for p, angle in rib:
        z = ground_z_at(p)
        rib_z.append(z)
    start = len(verts)
    for (p, angle), z, k in zip(rib, rib_z, range(len(rib))):
        width = 0.045 * (1.0 - 0.8 * k / pairs) + 0.008
        side = Vector((-math.sin(angle), math.cos(angle), 0)) * width
        lift = 0.03 * (1.0 - k / pairs) + 0.008
        verts.extend([tuple(p - side + Vector((0, 0, z + lift - p.z))), tuple(p + side + Vector((0, 0, z + lift - p.z)))])
    for k in range(pairs):
        a = start + 2 * k
        faces.append((a, a + 1, a + 3, a + 2))
        slots.append(0)
    # leaflets: long, narrow, bending down to the ground, some broken short
    for k in range(2, pairs + 1):
        p, angle = rib[k]
        z = rib_z[k]
        t = k / pairs
        for side in (-1, 1):
            if rng.random() < 0.12:
                continue
            leaf_length = rng.uniform(0.32, 0.72) * (1.0 - 0.55 * t) * (0.4 if rng.random() < 0.15 else 1.0)
            spread = angle + side * rng.uniform(0.7, 1.25) + rng.uniform(-0.15, 0.15)
            direction = Vector((math.cos(spread), math.sin(spread), 0))
            width = rng.uniform(0.012, 0.024)
            normal_side = Vector((-direction.y, direction.x, 0)) * width
            tip = p + direction * leaf_length
            tip_z = ground_z_at(tip) + 0.004
            middle = p + direction * leaf_length * 0.45
            middle_z = max(ground_z_at(middle) + 0.006, z + 0.02)
            base_z = z + 0.02
            s = len(verts)
            for q, qz, w in ((p, base_z, 0.6), (middle, middle_z, 1.0), (tip, tip_z, 0.15)):
                verts.extend([(q.x - normal_side.x * w, q.y - normal_side.y * w, qz), (q.x + normal_side.x * w, q.y + normal_side.y * w, qz)])
            faces.append((s, s + 1, s + 3, s + 2))
            faces.append((s + 2, s + 3, s + 5, s + 4))
            slots.extend([1, 1])


def _coconut(verts, faces, slots, centre, radius, rng, slot, split=False):
    """A slightly squashed, three-sided ball; split ones are a half shell lying open side up."""
    rings, sides = 6, 9
    start = len(verts)
    for r in range(rings + 1):
        polar = math.pi * r / rings
        if split and polar < math.pi * 0.45:
            polar = math.pi * 0.45
        for s in range(sides):
            a = math.tau * s / sides
            bulge = 1.0 + 0.08 * math.cos(3 * a)
            verts.append((centre.x + math.sin(polar) * math.cos(a) * radius * bulge,
                          centre.y + math.sin(polar) * math.sin(a) * radius * bulge * 0.92,
                          centre.z + math.cos(polar) * radius * 0.85))
    for r in range(rings):
        for s in range(sides):
            a = start + r * sides + s
            b = start + r * sides + (s + 1) % sides
            faces.append((a, b, b + sides, a + sides))
            slots.append(slot)


def lay_tree_fall(seen, roles, collection, *, litter=1.0, seed=31337):
    rng = random.Random(seed)
    report = {'trees': 0, 'palm_fronds_on_the_ground': 0, 'coconuts_and_husks': 0, 'fallen_leaves_under_trees': 0}
    if seen is None or not seen.grid or litter <= 0:
        return report
    scene = seen.scene
    camera = seen.origin
    from lay_shore import _in_view
    frond_verts, frond_faces, frond_slots = [], [], []
    nut_verts, nut_faces, nut_slots = [], [], []
    leaf_verts, leaf_faces, leaf_slots = [], [], []

    def ground_z_at(p, fallback=None):
        ground = seen.ground_under(Vector((p.x, p.y, (fallback if fallback is not None else p.z) + 0.0)), above=1.5)
        return ground[0] if ground is not None else (fallback if fallback is not None else p.z)

    for obj, foot, height, palm, radius in trees(scene, roles):
        report['trees'] += 1
        if (foot - camera).length > 45.0:
            continue
        crown = min(max(height * 0.35, 1.5), 5.0)
        if palm:
            for _ in range(max(0, int(round(rng.uniform(1, 4) * litter)))):
                distance = rng.uniform(radius + 0.4, crown + radius)
                angle = rng.uniform(0, math.tau)
                base = foot + Vector((math.cos(angle), math.sin(angle), 0)) * distance
                if not _in_view(seen, base, 40.0):
                    continue
                base.z = ground_z_at(base, foot.z)
                heading = angle + rng.uniform(-1.2, 1.2)
                _frond(rng, lambda q: ground_z_at(q, base.z), base, heading, frond_verts, frond_faces, frond_slots)
                report['palm_fronds_on_the_ground'] += 1
            for _ in range(max(0, int(round(rng.uniform(2, 6) * litter)))):
                distance = rng.expovariate(1 / 0.9) + radius + 0.16
                angle = rng.uniform(0, math.tau)
                spot = foot + Vector((math.cos(angle), math.sin(angle), 0)) * min(distance, crown + radius)
                if not _in_view(seen, spot, 40.0):
                    continue
                split = rng.random() < 0.4
                nut = rng.uniform(0.09, 0.13)          # the coconut's own size (the trunk's radius keeps it outside the trunk)
                z = ground_z_at(spot, foot.z)
                _coconut(nut_verts, nut_faces, nut_slots, Vector((spot.x, spot.y, z + (nut * 0.2 if split else nut * 0.62))), nut, rng,
                         1 if split else 0, split=split)
                report['coconuts_and_husks'] += 1
        else:
            for _ in range(int(220 * litter * crown / 3.0)):
                distance = abs(rng.gauss(0, crown * 0.55)) + radius + 0.05
                if distance > crown * 1.2 + radius:
                    continue
                angle = rng.uniform(0, math.tau)
                spot = foot + Vector((math.cos(angle), math.sin(angle), 0)) * distance
                if not _in_view(seen, spot, 30.0):
                    continue
                z = ground_z_at(spot, foot.z)
                rad = rng.uniform(0.015, 0.05)
                length = rad * rng.uniform(1.3, 2.2)
                a = rng.uniform(0, math.tau)
                dx, dy = math.cos(a), math.sin(a)
                px, py = -dy, dx
                k = len(leaf_verts)
                leaf_verts.extend([(spot.x - dx * length, spot.y - dy * length, z + 0.003), (spot.x + px * rad, spot.y + py * rad, z + 0.004),
                                   (spot.x + dx * length, spot.y + dy * length, z + 0.003), (spot.x - px * rad, spot.y - py * rad, z + 0.005),
                                   (spot.x, spot.y, z + 0.008)])
                slot = 0 if rng.random() < 0.6 else 1
                for b in range(4):
                    leaf_faces.append((k + b, k + (b + 1) % 4, k + 4))
                    leaf_slots.append(slot)
                report['fallen_leaves_under_trees'] += 1

    def make(name, verts, faces, slots, materials, role):
        data = bpy.data.meshes.new(name)
        data.from_pydata(verts, [], faces)
        for material in materials:
            data.materials.append(material)
        for polygon, slot in zip(data.polygons, slots):
            polygon.material_index = slot
        data.update()
        made = bpy.data.objects.new(name, data)
        made['place_role'] = role
        collection.objects.link(made)
        return made

    if frond_faces:
        rib = _material('TREE • dry frond midrib', (0.10, 0.075, 0.045), (0.20, 0.16, 0.10), 0.75)
        leaflets = _material('TREE • dead frond leaflets', (0.085, 0.07, 0.04), (0.23, 0.19, 0.12), 0.8, scale=12.0)
        make(PREFIX + 'dead palm fronds', frond_verts, frond_faces, frond_slots, [rib, leaflets], 'leaf')
    if nut_faces:
        nut = _material('TREE • coconut husk', (0.045, 0.035, 0.02), (0.13, 0.10, 0.055), 0.7, scale=50.0)
        inside = _material('TREE • split husk fibre', (0.10, 0.06, 0.03), (0.22, 0.15, 0.08), 0.95, scale=140.0)
        make(PREFIX + 'coconuts and split husks', nut_verts, nut_faces, nut_slots, [nut, inside], 'wood')
    if leaf_faces:
        import apply_by_role
        leaves = apply_by_role.append_materials(apply_by_role.DETAIL_LEAVES)
        make(PREFIX + 'fallen leaves', leaf_verts, leaf_faces, leaf_slots, [leaves[n] for n in apply_by_role.DETAIL_LEAVES], 'leaf')
    return report
