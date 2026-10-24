"""What this does: rounds the hard edges of objects a little (a razor-sharp box edge reads as a computer model, and real things are never that sharp). It
adds a Bevel modifier that only touches sharp edges and hardens the normals, plus a Weighted Normal modifier so the rounded edges shade smoothly on flat
faces, with a width taken from the object's surface (walls 0.8 to 1.5 cm, trims 6 mm, planks 6 to 12 mm; the house numbers place_surfaces.bevel_metres) and
never more than a quarter of the object's thinnest side. Running it twice leaves one pair of modifiers, not two. An object that already has its own Bevel
modifier is left as it is. It needs Blender (bpy).
A concrete example: bevel_objects(objects_with_widths) puts "PK Bevel" and "PK Weighted Normal" on a wall box; the audit then sees bevelled_edges.
"""
import numpy as np

import bpy

from .. import house_numbers, names, scene_read, settings_file

SHARP_EDGE_DEGREES = 30.0


def width_for(surface_id, thinnest_metres):
    """The bevel width in metres for a surface: the middle of its range (or its single value), at most a quarter of the thinnest side; None for no bevel."""
    spec = settings_file.surface(surface_id).get('bevel_metres')
    if spec:
        value = settings_file.number(spec)
    else:
        value = house_numbers.value('place_surfaces.bevel_metres.trim')
    width = float(np.mean(value)) if isinstance(value, (list, tuple)) else float(value)
    return min(width, max(thinnest_metres / 4.0, 0.001))


def remove_kit_modifiers(obj):
    for modifier in list(obj.modifiers):
        if modifier.name in (names.BEVEL_MODIFIER, names.WEIGHTED_NORMAL_MODIFIER):
            obj.modifiers.remove(modifier)


def bevel_object(obj, surface_id):
    """Adds the kit's two modifiers (or refreshes them). Returns the width used, or None when the object already has its own bevel or is not a mesh."""
    if obj.type != 'MESH':
        return None
    if any(m.type == 'BEVEL' and m.name != names.BEVEL_MODIFIER for m in obj.modifiers) or obj.get('pk_bevelled'):
        return None
    remove_kit_modifiers(obj)
    thinnest = float(min(scene_read.object_size(obj))) or 0.05
    width = width_for(surface_id, thinnest)
    bevel = obj.modifiers.new(names.BEVEL_MODIFIER, 'BEVEL')
    bevel.width = width
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = np.radians(SHARP_EDGE_DEGREES)
    bevel.harden_normals = True
    weighted = obj.modifiers.new(names.WEIGHTED_NORMAL_MODIFIER, 'WEIGHTED_NORMAL')
    weighted.keep_sharp = True
    # the kit's bevel goes first among the kit's own modifiers (damage cuts and the displace come after it)
    index = 0
    for position, modifier in enumerate(obj.modifiers):
        if modifier.name == names.BEVEL_MODIFIER:
            index = position
    return width


def bevel_objects(items):
    """items: [(object, surface id)]. Returns {object name: width or None}."""
    return {obj.name: bevel_object(obj, surface_id) for obj, surface_id in items}
