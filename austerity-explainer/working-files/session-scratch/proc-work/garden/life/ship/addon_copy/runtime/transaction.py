"""Short-lived rollback for creation/detail operators, including finalization.

Only IDs allocated by explicitly captured creation/report calls are removed.
Existing IDs are never deleted; retained source/generation flags and the caller's
selection are restored separately. This is not a replacement for Blender Undo.
"""
import bpy


class CreationTransaction:
    _FLAGS = ('astra_landscape_active', 'astra_active', 'astra_superseded_by')

    def __init__(self, context, retained=()):
        self.context = context
        self.selected = tuple(context.selected_objects)
        self.active = context.view_layer.objects.active
        self.created = {}
        self.rollback_actions = []
        self.retained = []
        for obj in dict.fromkeys(o for o in retained if o is not None):
            self.retained.append((obj, obj.hide_render,
                obj.hide_get(view_layer=context.view_layer),
                {key: (key in obj, obj.get(key)) for key in self._FLAGS}))
        self.last_report = context.scene.astra_scene.last_report

    def __enter__(self):
        return self

    def on_rollback(self, function, *args, **kwargs):
        # Restore any changed preexisting receiver before deleting its new IDs.
        self.rollback_actions.append((function, args, kwargs))

    def capture(self, function, *args, **kwargs):
        # ID identity, not names, also protects shared materials and prior results.
        # Limit the allocation window to the actual creator/report call: unrelated
        # IDs added by later UI callbacks are not silently swept into this cleanup.
        before = {item.as_pointer() for item in bpy.data.user_map()}
        try:
            return function(*args, **kwargs)
        finally:
            for item in bpy.data.user_map():
                pointer = item.as_pointer()
                if pointer not in before:
                    self.created[pointer] = item

    def rollback(self):
        for function, args, kwargs in reversed(self.rollback_actions):
            function(*args, **kwargs)
        for obj, hide_render, hidden, flags in self.retained:
            for key, (present, value) in flags.items():
                if present:
                    obj[key] = value
                elif key in obj:
                    del obj[key]
            obj.hide_render = hide_render
            obj.hide_set(hidden, view_layer=self.context.view_layer)
        self.context.scene.astra_scene.last_report = self.last_report
        # Some inner creators already clean up their own failures. Intersect with
        # live IDs rather than dereferencing removed Blender RNA values.
        created = {item for item in bpy.data.user_map()
                   if item.as_pointer() in self.created}
        if created:
            bpy.data.batch_remove(ids=created)
        for obj in tuple(self.context.selected_objects):
            obj.select_set(False, view_layer=self.context.view_layer)
        for obj in self.selected:
            obj.select_set(True, view_layer=self.context.view_layer)
        self.context.view_layer.objects.active = self.active

    def __exit__(self, kind, error, traceback):
        if kind is not None:
            try:
                self.rollback()
            except Exception as cleanup_error:
                raise RuntimeError(f'{error}; creation rollback also failed: {cleanup_error}') from error
        return False
