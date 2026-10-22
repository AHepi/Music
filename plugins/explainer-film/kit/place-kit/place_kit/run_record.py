"""What this does: keeps one small record in the Blender scene (a custom property on the scene called pk_run) of how the kit last
finished it: the look and state, whether it was a quick trial, the size of the maps, how the plan masks were made and how long that took.
The audit reads it so the verdict can say "this was a quick trial" or "the masks took too long". The record is plain JSON text and is
saved with the scene.

A concrete example: after `finish --quick` the record holds {"quick": true, "map_size_pixels": 256, "mask": {"cell_metres": 0.5, ...}}.
It needs Blender (bpy).
"""
import json

import bpy

KEY = 'pk_run'


def read():
    """The record as a dict ({} when the kit has not finished this scene)."""
    raw = bpy.context.scene.get(KEY)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {}


def write(**fields):
    """Adds fields to the record (existing ones are kept unless named) and stores it."""
    record = read()
    record.update(fields)
    bpy.context.scene[KEY] = json.dumps(record)
    return record


def clear():
    if KEY in bpy.context.scene:
        del bpy.context.scene[KEY]
