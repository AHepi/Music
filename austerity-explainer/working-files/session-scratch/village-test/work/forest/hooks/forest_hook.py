"""A variation hook for the FOREST part: it runs the forest stage file again on the finished scene with the variation's numbers, then gives the new objects what the surface pass had given the old ones
(the wear numbers, the bark and rock materials), so a picture of a variation differs from the baseline only by the dials. It runs inside Blender on a freshly opened copy; the scene is never saved.
args (all optional): crown_lump (0.05 to 0.35, how rough each crown lump is), crown_scale (0.8 to 1.3, crown size against trunk), density (0.5 to 1.7, how many clusters), tone_olive (0 to 1, dark greens to olive
greens), golden (0 to 6 golden-brown trees), moss_scale (0.4 to 1.9), lump_detail (1 to 3, facets in a crown lump), lean_share (0 to 0.4, leaning trees at the rim).
"""
import importlib.util
import os
import zlib

import bpy

STAGE_FILE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages/stage_forest.py'
KEEP_PREFIX = 'pk_'
SKIP = ('pk_original_materials', 'pk_seed', 'pk_zmin', 'pk_top_z', 'pk_height', 'pk_size_x', 'pk_size_y', 'pk_size_z')


def apply(variation):
    a = dict(variation.get('args') or {})
    example = {}
    materials = {}
    for obj in bpy.data.objects:
        if obj.get('place_owner') != 'forest' or obj.type != 'MESH':
            continue
        role = obj.get('place_role')
        example.setdefault(role, {k: obj[k] for k in obj.keys() if k.startswith(KEEP_PREFIX) and k not in SKIP})
        for slot in obj.material_slots:
            if slot.material is not None and slot.material.name.startswith('PK '):
                materials.setdefault(role, slot.material)
    density = float(a.get('density', 1.0))
    olive = float(a.get('tone_olive', 0.25))
    options = {
        'crown_lump': float(a.get('crown_lump', 0.16)),
        'crown_scale': float(a.get('crown_scale', 1.0)),
        'rim_clusters': int(round(14 * density)),
        'far_clusters': int(round(20 * density)),
        'w_dark': max(0.02, 0.55 - 0.8 * olive),
        'w_mid': 0.4,
        'w_olive': 0.05 + 0.8 * olive,
        'golden': int(round(float(a.get('golden', 2)))),
        'moss_scale': float(a.get('moss_scale', 1.0)),
        'lump_detail': int(round(float(a.get('lump_detail', 2)))),
        'lean_share': float(a.get('lean_share', 0.18)),
    }
    spec = importlib.util.spec_from_file_location('stage_forest_try', STAGE_FILE)
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    stage.apply(options)
    for obj in bpy.data.objects:
        if obj.get('place_owner') != 'forest' or obj.type != 'MESH':
            continue
        role = obj.get('place_role')
        for key, value in example.get(role, {}).items():
            obj[key] = value
        obj['pk_seed'] = (zlib.crc32(obj.name.encode()) % 1000) / 1000.0
        if not obj.material_slots and role in materials:
            obj.data.materials.append(materials[role])
