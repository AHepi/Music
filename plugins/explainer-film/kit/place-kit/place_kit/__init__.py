"""What this does: the public face of the place kit. `import place_kit as pk` inside Blender gives one function per job (read_settings, tag_roles,
give_surfaces, shape_roads, damage_objects, age_place, grow_things, check_construction, audit_place, finish_place, finish_part, undo_finish, ...) and the
part helpers a builder uses (begin_part, new_part_object, forget_part, seat_on_ground, ground_height_at, is_keep_clear). Every function is idempotent:
running it twice leaves the same scene.
The functions are looked up when first used, so importing the package needs no Blender (the plain-Python tools and `--help` rely on that).

A concrete example, inside Blender:
    import sys; sys.path.insert(0, '<kit>/place-kit'); import place_kit as pk
    settings = pk.read_settings('place-settings.json')
    result = pk.finish_place(settings, look='neglected', state='damp')     # the whole pass; result['audit'] is the audit
"""
import importlib

__version__ = '1.4.0'

_LAZY = {
    'read_settings': ('commands', 'read_settings'),
    'new_settings': ('commands', 'new_settings'),
    'tag_roles': ('commands', 'tag_roles'),
    'give_surfaces': ('commands', 'give_surfaces'),
    'shape_roads': ('commands', 'shape_roads'),
    'damage_objects': ('commands', 'damage_objects'),
    'age_place': ('wear.door', 'age_place'),
    'grow_things': ('commands', 'grow_things'),
    'light_place': ('commands', 'light_place'),
    'set_picture_size': ('wear.door', 'set_picture_size'),
    'check_construction': ('checks.construction', 'check_construction'),
    'test_normal_maps': ('checks.normals_test', 'test_normal_maps'),
    'audit_place': ('checks.scene_audit', 'audit_place'),
    'finish_place': ('commands', 'finish_place'),
    'finish_part': ('commands', 'finish_part'),
    'undo_finish': ('undo', 'undo_finish'),
    'renderer_for_scene': ('render.renderer_choice', 'renderer_for_scene'),
    'fingerprint_scene': ('checks.fingerprint', 'fingerprint_scene'),
    'combine_stages': ('checks.combine', 'combine_stages'),
    'begin_part': ('parts', 'begin_part'),
    'new_part_object': ('parts', 'new_part_object'),
    'forget_part': ('parts', 'forget_part'),
    'seat_on_ground': ('parts', 'seat_on_ground'),
    'reseat_on_ground': ('parts', 'reseat_on_ground'),
    'ground_height_at': ('parts', 'ground_height_at'),
    'is_keep_clear': ('parts', 'is_keep_clear'),
}


def __getattr__(name):
    if name in _LAZY:
        module_name, attribute = _LAZY[name]
        module = importlib.import_module(f'{__name__}.{module_name}')
        return getattr(module, attribute)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def __dir__():
    return sorted(list(globals()) + list(_LAZY))
