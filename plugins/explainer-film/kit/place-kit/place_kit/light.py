"""What this does: gives a place LIGHT when it has none, so a place built with no lamps and no sky does not draw black or flat. If the scene has no lamp of its own (a world colour or a glowing
window alone is not a key light: the scene would draw flat, with no raking shadows to show the normal maps), it adds a sun (the sun's direction matches the one the plan masks use for shade, so shady places in the masks are shady in the picture), a soft sky colour for the world, and a small warm lamp
inside every object that has the glow role (a lit window, a lantern) that has no lamp near it. Everything it adds is named "PK ..." and marked pk_made, so undo removes it, and a scene that
already has light is left exactly as it is. Starting values are the house numbers place_light.* (first tries, not tuned: judge by looking). It needs Blender (bpy).
A concrete example: on a bare scene light_place(settings) adds "PK sun" (3.5 W per square metre at 35 degrees) and a sky of strength 0.8; the audit's light check then passes.
"""
import math

import bpy
from mathutils import Vector

from . import house_numbers, names, roles as roles_module, scene_read

TOWARD_SUN_AZIMUTH_DEGREES = 135.0          # the direction the kit's own sun is put in, and the plan masks' fallback (wear/masks.py SUN_AZIMUTH_DEGREES)
FALLBACK_SUN_COMPASS_DEGREES = 135.0        # the wear layers' shade when the scene has no sun lamp, or more than one
FALLBACK_SUN_HEIGHT_DEGREES = 45.0


def scene_sun_direction(scene=None):
    """Where the sun stands for the wear layers' shade (which sides stay sheltered and damp: moss, soot, fade):
    {'compass_degrees', 'height_degrees', 'from', 'sun'}. The scene's own sun lamp when there is exactly one (a sun lamp shines along its own -Z,
    so the sun stands along +Z); otherwise the fallback, 135 degrees compass and 45 degrees up, with the reason. Compass is measured from +x
    toward +y, the kit's own way of writing a sun: (cos compass cos height, sin compass cos height, sin height).
    A concrete example: one sun lamp tipped so it shines from the west at 20 degrees up gives compass 180, height 20, from 'the scene's sun lamp "Sun"'."""
    scene = scene or bpy.context.scene
    suns = [o for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN' and not o.hide_render and getattr(o.data, 'energy', 0) > 0]
    if len(suns) == 1:
        toward = (suns[0].matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
        height = math.degrees(math.asin(max(-1.0, min(1.0, toward.z))))
        compass = math.degrees(math.atan2(toward.y, toward.x)) % 360.0
        return {'compass_degrees': round(compass, 2), 'height_degrees': round(height, 2), 'from': f'the scene\'s sun lamp "{suns[0].name}"', 'sun': suns[0].name}
    why = 'the scene has no sun lamp' if not suns else f'the scene has {len(suns)} sun lamps ({", ".join(o.name for o in suns[:4])}), so none is picked'
    return {'compass_degrees': FALLBACK_SUN_COMPASS_DEGREES, 'height_degrees': FALLBACK_SUN_HEIGHT_DEGREES,
            'from': f'the fallback, 135 degrees compass and 45 degrees up ({why})', 'sun': None}


def quiet_backdrops():
    """Far scenery (the role backdrop) casts no shadow, so it can never block the sun (hazy hills that cast shadows blocked it in an earlier
    place). Returns the names of the objects changed."""
    changed = []
    for obj in scene_read.mesh_objects(only_visible=True):
        if roles_module.role_class(str(obj.get(names.ROLE) or '')) == 'backdrop' and getattr(obj, 'visible_shadow', False):
            obj.visible_shadow = False
            changed.append(obj.name)
    return changed


def scene_has_light():
    """True when the scene has a lamp of its own (not one the kit added): the only thing that counts as a key light. A lit world or a glowing material is some light, but without a lamp
    the picture has no direction of light, so the kit still adds a sun."""
    scene = bpy.context.scene
    lamps = [o for o in scene.objects if o.type == 'LIGHT' and not o.hide_render and o.data.energy > 0 and not o.get(names.MADE)]
    return bool(lamps)


def light_place(settings, sun_only=False):
    """Adds light when there is none (see the note at the top). Returns {'summary', 'added': [...]}."""
    scene = bpy.context.scene
    added = []
    existing_sun = bpy.data.objects.get('PK sun')
    if scene_has_light() and existing_sun is None:
        return {'summary': 'the scene already has a lamp of its own (left as it is)', 'added': []}
    elevation = house_numbers.value('place_light.sun_elevation_degrees')
    if existing_sun is None:
        data = bpy.data.lights.new('PK sun', 'SUN')
        sun = bpy.data.objects.new('PK sun', data)
        scene.collection.objects.link(sun)
        sun[names.MADE] = 1
        added.append(sun.name)
    else:
        sun = existing_sun
        data = sun.data
    data.energy = house_numbers.value('place_light.sun_strength')
    azimuth, el = math.radians(TOWARD_SUN_AZIMUTH_DEGREES), math.radians(elevation)
    toward = Vector((math.cos(azimuth) * math.cos(el), math.sin(azimuth) * math.cos(el), math.sin(el)))
    sun.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
    if not sun_only and (scene.world is None or scene.world.get(names.MADE) or not scene.world.use_nodes):
        world = scene.world or bpy.data.worlds.new('PK world')
        world.use_nodes = True
        tree = world.node_tree
        background = next((n for n in tree.nodes if n.type == 'BACKGROUND'), None) or tree.nodes.new('ShaderNodeBackground')
        background.inputs['Color'].default_value = (0.45, 0.55, 0.72, 1.0)
        background.inputs['Strength'].default_value = house_numbers.value('place_light.sky_strength')
        output = next((n for n in tree.nodes if n.type == 'OUTPUT_WORLD'), None) or tree.nodes.new('ShaderNodeOutputWorld')
        if not output.inputs['Surface'].links:
            tree.links.new(background.outputs['Background'], output.inputs['Surface'])
        world[names.MADE] = 1
        scene.world = world
        added.append(world.name)
    if not sun_only:
        lamps = [o for o in scene.objects if o.type == 'LIGHT']
        for obj in scene_read.mesh_objects(only_visible=True):
            if obj.get(names.ROLE) != 'never.glow':
                continue
            low, high = scene_read.world_bounds(obj)
            centre = Vector(((low[0] + high[0]) / 2, (low[1] + high[1]) / 2, (low[2] + high[2]) / 2))
            if any((lamp.matrix_world.translation - centre).length < 0.5 for lamp in lamps):
                continue
            data = bpy.data.lights.new(f'PK glow {obj.name}', 'POINT')
            data.energy = 20.0
            data.color = (1.0, 0.72, 0.42)
            data.shadow_soft_size = 0.05
            lamp = bpy.data.objects.new(f'PK glow {obj.name}', data)
            lamp.location = centre
            scene.collection.objects.link(lamp)
            lamp[names.MADE] = 1
            added.append(lamp.name)
    return {'summary': (f'added {", ".join(added)}' if added else 'light already in place'), 'added': added}
