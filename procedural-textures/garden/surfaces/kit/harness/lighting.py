# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE LIGHTING RIGS as data (settings lighting.rigs): A "the scene lit as its file lights it", B "the same, looking at a glare", C a low side sun, D flat overhead light,
# E light from behind. A rig names its suns ("file" or a list of {azimuth_deg, elevation_deg, colour, strength}), whether the file's own lamps stay on ("file" or "off"), whether
# house shadows are switched off, an optional base rig, and extra lights. set_rig(settings, name) puts the scene in that rig (everything put back first, so rigs never stack).
# The earlier pictures (A, C, E of the lighting test set) are reproduced to within one step of 255 on 99 % of dots (tested by selftests.lighting_matches_earlier).
import math
import re

import bpy
from mathutils import Vector

_ORIGINAL = {}


def _remember(settings):
    if _ORIGINAL:
        return
    off_patterns = (settings.get('lighting') or {}).get('shadow_off_objects', [])
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            _ORIGINAL[obj.name] = obj.hide_render
        elif obj.type == 'MESH' and any(re.match(p, obj.name) for p in off_patterns):
            _ORIGINAL[obj.name] = obj.visible_shadow


def _rig_object(name, kind):
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.lights.new(name, kind)
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
    return obj


def restore():
    for name, original in _ORIGINAL.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        if obj.type == 'LIGHT':
            obj.hide_render = original
        else:
            obj.visible_shadow = original
    for name in ('wk_rig_sun',):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = True
    for obj in list(bpy.data.objects):
        if obj.name.startswith('wk_rig_extra'):
            obj.hide_render = True


def set_rig(settings, name, overrides=None):
    lighting = settings.get('lighting') or {}
    rigs = lighting.get('rigs', {})
    if name not in rigs:
        raise KeyError(f'the set has no lighting rig {name!r}')
    _remember(settings)
    restore()
    rig = dict(rigs[name])
    if 'base' in rig and rig['base'] != name:
        base = dict(rigs[rig['base']])
        base.update({k: v for k, v in rig.items() if k not in ('base', 'describe')})
        rig = base
    scene = bpy.context.scene
    keep = set(lighting.get('keep_lights', []))
    if rig.get('lamps') == 'off':
        for obj in scene.objects:
            if obj.type == 'LIGHT' and obj.name not in keep and not obj.name.startswith('wk_rig'):
                obj.hide_render = True
    if rig.get('house_shadows') == 'off':
        for obj in scene.objects:
            if obj.name in _ORIGINAL and obj.type == 'MESH':
                obj.visible_shadow = False
    suns = rig.get('suns', 'file')
    if isinstance(suns, list) and suns:
        sun = _rig_object('wk_rig_sun', 'SUN')
        spec = dict(suns[0])
        spec.update(overrides or {})
        az, el = math.radians(spec['azimuth_deg']), math.radians(spec['elevation_deg'])
        direction = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        sun.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
        sun.data.energy = spec['strength']
        sun.data.color = spec['colour']
        sun.data.angle = math.radians(0.6)
        sun.hide_render = False
    for index, extra in enumerate(rig.get('extra_lights', [])):
        obj = _rig_object(f'wk_rig_extra_{index}', extra.get('kind', 'point').upper())
        obj.location = extra['location']
        obj.data.energy = (overrides or {}).get('watts', extra['watts'])
        obj.data.color = extra['colour']
        if hasattr(obj.data, 'shadow_soft_size'):
            obj.data.shadow_soft_size = extra.get('radius', 0.1)
        obj.hide_render = False
    return rig


def rig_names(settings):
    return list(((settings.get('lighting') or {}).get('rigs') or {}).keys())
