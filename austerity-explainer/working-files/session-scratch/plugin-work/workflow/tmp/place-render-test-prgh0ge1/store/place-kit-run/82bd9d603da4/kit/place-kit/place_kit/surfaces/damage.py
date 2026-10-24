"""What this does: damage as SHAPE. In the garden work it was designed shape, not painted wear, that read at film size: boards that bow and cup, stones with knocked corners, posts
that lean, thatch that sags, and above all no two parts alike. This step gives every object whose role needs it (timber, roof, stone; wanted for walls and props) a non-destructive,
different-for-every-object bend and lumpiness: a Subdivision Surface (simple) modifier adds the vertices to move, then a Displace modifier moves them with a slow noise read at the
object's world position (so two boards from one mesh come out different), by an amount that depends on the kind of object and the look (a derelict place sags more than a kept one).
Posts and fences also lean a little about their base. Everything the step adds is named "PK Damage ..." and the object is marked pk_shape_damage, so the audit can see it and undo can
remove it; running it twice gives the same result. The construction check reads the mesh as built, before these modifiers, so a bow never makes a part float.
Not done (said plainly): replaced boards, missing or slipped tiles and spalled corners as real holes; chips are painted by the cracks-and-chips layer. It needs Blender (bpy).
A concrete example: damage_objects(settings) bows a 1.2 m plank by up to about a centimetre (the house number place_wear.shape_damage_bow_per_length_max) and leans a post by under one degree.
"""
import json
import math

import numpy as np

import bpy
from mathutils import Matrix, Vector

from .. import house_numbers, names, roles as roles_module, scene_read, settings_file
from ..wear import seed as seed_module

STRENGTH_METRES = {'timber': 0.012, 'roof': 0.04, 'stone': 0.02, 'wall': 0.012, 'prop': 0.008, 'iron': 0.004}
NOISE_SCALE_METRES = {'timber': 1.2, 'roof': 2.5, 'stone': 0.6, 'wall': 1.5, 'prop': 0.8, 'iron': 0.8}
LEAN_DEGREES = 0.8
MAX_FACES_TO_SUBDIVIDE = 2500
TEXTURE_NAME = 'PK Damage Noise'
MATRIX_KEY = 'pk_matrix_before_damage'


def damage_strength(klass, longest_metres, look_amount):
    """How far (metres) the displace may move a point: the class's own strength, scaled by the look, and never more than the bow house number times the object's length."""
    base = STRENGTH_METRES.get(klass, 0.008)
    cap = house_numbers.value('place_wear.shape_damage_bow_per_length_max') * max(longest_metres, 0.05)
    return float(min(base * (0.4 + 1.2 * look_amount), max(cap, 0.004)))


def _texture(scale):
    name = f'{TEXTURE_NAME} {scale:g}'
    texture = bpy.data.textures.get(name)
    if texture is None:
        texture = bpy.data.textures.new(name, 'CLOUDS')
        texture.noise_scale = float(scale)
        texture.noise_depth = 2
        texture['pk_made'] = 1
    return texture


def remove_kit_modifiers(obj):
    for modifier in list(obj.modifiers):
        if modifier.name in (names.DAMAGE_MODIFIER, names.DAMAGE_SUBDIVIDE_MODIFIER):
            obj.modifiers.remove(modifier)


def lean_about_base(obj, degrees, seed_value):
    """Leans the object about the middle of its lowest face by up to `degrees` (a fixed direction from the seed), from its matrix as first found (so it never leans twice)."""
    if MATRIX_KEY not in obj.keys():
        obj[MATRIX_KEY] = json.dumps([list(row) for row in obj.matrix_world])
    original = Matrix(json.loads(obj[MATRIX_KEY]))
    obj.matrix_world = original
    low, high = scene_read.world_bounds(obj)
    pivot = Vector(((low[0] + high[0]) / 2, (low[1] + high[1]) / 2, low[2]))
    angle = math.radians(degrees) * (0.4 + 0.6 * seed_value)
    direction = 2 * math.pi * seed_module.hash01(seed_value, 'lean')
    axis = Vector((-math.sin(direction), math.cos(direction), 0.0))
    rotation = Matrix.Translation(pivot) @ Matrix.Rotation(angle, 4, axis) @ Matrix.Translation(-pivot)
    obj.matrix_world = rotation @ original
    return angle


def damage_object(obj, klass, look_amount, lean=False):
    """Adds the two modifiers (and a lean for posts). Returns a short note."""
    remove_kit_modifiers(obj)
    size = scene_read.object_size(obj)
    longest = float(max(size))
    faces = len(obj.data.polygons)
    notes = []
    if faces <= MAX_FACES_TO_SUBDIVIDE and faces > 0:
        spacing = max(NOISE_SCALE_METRES.get(klass, 1.0) / 8.0, 0.03)
        levels = int(min(3, max(1, math.ceil(math.log2(max(longest / spacing, 1.0))))))
        cuts = obj.modifiers.new(names.DAMAGE_SUBDIVIDE_MODIFIER, 'SUBSURF')
        cuts.subdivision_type = 'SIMPLE'
        cuts.levels = min(levels, 1)
        cuts.render_levels = min(levels, 2)
        notes.append(f'{levels} cut level(s)')
    displace = obj.modifiers.new(names.DAMAGE_MODIFIER, 'DISPLACE')
    displace.texture = _texture(NOISE_SCALE_METRES.get(klass, 1.0))
    displace.texture_coords = 'GLOBAL'
    displace.mid_level = 0.5
    displace.direction = 'NORMAL'
    displace.strength = damage_strength(klass, longest, look_amount)
    obj[names.SHAPE_DAMAGE] = 1
    notes.append(f'bend up to {displace.strength * 1000:.0f} mm')
    if lean:
        angle = lean_about_base(obj, LEAN_DEGREES * (0.5 + look_amount), seed_module.object_seed(obj.matrix_world.translation, obj.get(names.ROLE)))
        notes.append(f'leans {math.degrees(angle):.2f} degrees')
    return ', '.join(notes)


def damage_objects(settings, owner=None, amount=None):
    """The damage pass (see the note at the top). Returns {'summary', 'objects': [...], 'skipped': n}."""
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    objects = [o for o in scene_read.mesh_objects(only_visible=True) if not scene_read.is_scatter(o)]
    tagged = roles_module.tag_objects([scene_read.object_facts(o) for o in objects], rules, table)['by_object']
    done, skipped = [], 0
    for obj in objects:
        info = tagged[obj.name]
        role = info['role']
        if role is None or roles_module.is_never(role) or role.startswith('ground.'):
            continue
        if owner is not None and obj.get(names.OWNER) != owner:
            continue
        req = roles_module.requirements(role, table, rules)
        if 'shape_damage' not in (set(req['required']) | set(req['wanted'])) or roles_module.off_entries_for(role, 'shape_damage', rules):
            skipped += 1
            continue
        if min(scene_read.object_size(obj)) < 0.01:
            skipped += 1
            continue
        look_data = settings_file.look(settings.look_for_role(role))
        look_amount = float(amount if amount is not None else look_data['layers']['cracks_and_chips']['amount'])
        lean = role in ('timber.post', 'timber.fence')
        note = damage_object(obj, roles_module.role_class(role), look_amount, lean=lean)
        done.append(obj.name)
    bpy.context.view_layer.update()
    return {'summary': f'{len(done)} object(s) bent, leaned or lumped differently ({skipped} left alone)', 'objects': done, 'skipped': skipped}
