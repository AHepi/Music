"""Selection-only copy-on-write preview transactions.

Preview state lives in Blender properties, so save/reload and undo retain the
original data pointers. No global scene/world/compositor mutation occurs here.
"""
import datetime
import hashlib
import json
import uuid
import bpy
from . import config, geometry, response

SNAPSHOT_VERSION = "1.1"
STATIC_MODIFIERS = {"BEVEL", "SUBSURF", "TRIANGULATE", "WEIGHTED_NORMAL", "EDGE_SPLIT"}


def _instance_dependents(obj):
    """Conservative source-ID exclusion, including references in other scenes."""
    users = []
    for candidate in bpy.data.objects:
        collection = candidate.instance_collection if candidate.instance_type == "COLLECTION" else None
        if collection and obj in collection.all_objects.values():
            users.append(candidate.name)
    parent = obj.parent
    while parent:
        if parent.instance_type in {"VERTS", "FACES"}:
            users.append(parent.name)
        parent = parent.parent
    for settings in bpy.data.particles:
        if settings.instance_object == obj or (settings.instance_collection and
                obj in settings.instance_collection.all_objects.values()):
            users.append("particle settings: " + settings.name)
    return sorted(set(users))


def _animated_hierarchy(obj):
    while obj:
        if obj.animation_data or obj.constraints:
            return True
        obj = obj.parent
    return False


def modifier_state(obj, mod):
    """Serializable state guard, not a claim of historical modifier identity.

    Blender may reuse a removed modifier's UID. Reject changed scalar/array RNA
    settings, profile control points, name, UID or stack position. An exact clone
    of every recorded field is indistinguishable; users must Keep before rebuilding.
    """
    values = {"type": mod.type, "persistent_uid": mod.persistent_uid,
              "stack_index": obj.modifiers.find(mod.name)}
    for prop in mod.bl_rna.properties:
        if prop.is_readonly or prop.identifier in {"rna_type", "is_active", "show_expanded"}:
            continue
        if prop.type not in {"BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"}:
            continue
        value = getattr(mod, prop.identifier)
        if getattr(prop, "is_array", False):
            value = list(value)
        elif isinstance(value, set):
            value = sorted(value)
        values[prop.identifier] = value
    if mod.type == "BEVEL":
        profile = mod.custom_profile
        values["custom_profile_points"] = [
            {"location": list(point.location), "handle_type_1": point.handle_type_1,
             "handle_type_2": point.handle_type_2} for point in profile.points]
    return json.dumps(values, sort_keys=True, allow_nan=False, separators=(",", ":"))


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def runtime(context):
    context.view_layer.update()
    scene = context.scene
    camera = scene.camera
    lights = []
    for o in scene.objects:
        if o.type != "LIGHT":
            continue
        data = o.data
        fields = {"name": o.name, "type": data.type, "energy": data.energy,
                  "color": list(data.color), "hide_render": o.hide_render,
                  "visible_in_current_view_layer": o.visible_get(view_layer=context.view_layer),
                  "matrix_world": [list(r) for r in o.matrix_world]}
        for attr in ("size", "size_y", "shape", "angle", "shadow_soft_size", "spot_size",
                     "spot_blend", "spread", "use_shadow", "normalize", "exposure"):
            if hasattr(data, attr):
                fields[attr] = getattr(data, attr)
        lights.append(fields)
    return {"blender": bpy.app.version_string, "scene": scene.name,
            "file": bpy.data.filepath, "frame": scene.frame_current,
            "render_engine": scene.render.engine,
            "camera": {"name": camera.name, "matrix_world": [list(r) for r in camera.matrix_world],
                       "lens_mm": camera.data.lens, "type": camera.data.type,
                       "shift_x": camera.data.shift_x, "shift_y": camera.data.shift_y,
                       "sensor_fit": camera.data.sensor_fit,
                       "sensor_width_mm": camera.data.sensor_width,
                       "sensor_height_mm": camera.data.sensor_height} if camera else None,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
            "view_transform": scene.view_settings.view_transform,
            "exposure": scene.view_settings.exposure, "gamma": scene.view_settings.gamma,
            "look": scene.view_settings.look,
            "world": {"name": scene.world.name, "use_nodes": scene.world.use_nodes,
                      "color": list(scene.world.color)} if scene.world else None,
            "world_record_limit": "World graph/volume internals are not fully captured; bind the actual saved scene hash separately",
            "cycles": {"samples": scene.cycles.samples, "seed": scene.cycles.seed,
                       "use_denoising": scene.cycles.use_denoising} if hasattr(scene, "cycles") else None,
            "lights": lights}


def write_report(scene, kind, payload):
    text = bpy.data.texts.new("Astra " + kind + " " + _utc().replace(":", "-")[:19])
    text.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    scene.astra_style.last_report = text.name
    return text


def _plain_light(data):
    """Blender 5.1 lights have a node tree by default; allow its plain emission."""
    tree = getattr(data, "node_tree", None)
    if not tree:
        return True
    outputs = [n for n in tree.nodes if n.type == "OUTPUT_LIGHT" and n.is_active_output]
    if len(outputs) != 1 or not outputs[0].inputs["Surface"].is_linked:
        return False
    source = outputs[0].inputs["Surface"].links[0].from_node
    return source.type == "EMISSION" and not any(s.is_linked for s in source.inputs)


def preflight(context, spec, objects=None):
    spec = config.validate(spec)
    if context.mode != "OBJECT":
        raise ValueError("Use Object Mode; edit/sculpt modes are intentionally excluded")
    if context.scene.render.engine != "CYCLES" and config.is_effective(spec, "material"):
        raise ValueError("Response preview requires Cycles; render engine is never changed automatically")
    context.view_layer.update()
    objects = list(context.selected_objects if objects is None else objects)
    rows = []
    for obj in sorted(objects, key=lambda o: o.name):
        row = {"object": obj.name, "type": obj.type, "actions": [], "skipped": [], "material_slots": []}
        rows.append(row)
        if obj.library or obj.override_library or (obj.data and (obj.data.library or obj.data.override_library)):
            row["skipped"].append("Linked/library-overridden object or data is preserved")
            continue
        if len(obj.users_scene) != 1:
            row["skipped"].append("Object shared by multiple scenes is preserved")
            continue
        if obj.hide_render or not obj.visible_get(view_layer=context.view_layer):
            row["skipped"].append("Hidden object is preserved")
            continue
        dependents = _instance_dependents(obj)
        if dependents:
            row["skipped"].append("Instanced source object is preserved; dependent instances: " + ", ".join(dependents))
            continue
        if _animated_hierarchy(obj):
            row["skipped"].append("Animated/driven/constrained object or parent is outside the static preview contract")
            continue
        if obj.type == "MESH":
            if not len(obj.data.vertices):
                row["skipped"].append("Empty mesh")
                continue
            if obj.data.shape_keys or obj.data.animation_data or any(m.type not in STATIC_MODIFIERS for m in obj.modifiers):
                row["skipped"].append("Unqualified modifier/deformation: only Bevel, Subdivision, Triangulate, Weighted Normal and Edge Split are admitted")
                continue
            if config.is_effective(spec, "material"):
                if not geometry.orthogonal_transform(obj):
                    row["skipped"].append("Material bind excludes sheared/singular transforms")
                else:
                    indices = range(len(obj.material_slots)) if spec["material"]["slot_scope"] == "ALL" else [obj.active_material_index]
                    for index in indices:
                        if index >= len(obj.material_slots):
                            row["skipped"].append("No active material slot")
                            continue
                        mat = obj.material_slots[index].material
                        ok, reason = response.inspect_material(mat)
                        row["material_slots"].append({"index": index, "material": mat.name if mat else None,
                                                       "eligible": ok, "reason": reason})
                    if any(s["eligible"] for s in row["material_slots"]):
                        row["actions"].append("material")
            if config.is_effective(spec, "geometry"):
                ok, reason = geometry.bevel_contract(obj, spec["geometry"], context.scene.unit_settings.scale_length)
                if ok:
                    row["actions"].append("geometry")
                row["geometry_note"] = reason
        elif obj.type == "LIGHT" and config.is_effective(spec, "lighting"):
            if obj.data.animation_data or (getattr(obj.data, "node_tree", None) and obj.data.node_tree.animation_data):
                row["skipped"].append("Animated/driven light is preserved")
            elif not _plain_light(obj.data):
                row["skipped"].append("Custom node-based light is outside the energy/color adapter")
            else:
                row["actions"].append("lighting")
        elif obj.type not in {"MESH", "LIGHT"}:
            row["skipped"].append("Only selected meshes and lights can be edited")
    return {"schema_version": config.SCHEMA_VERSION, "addon_version": config.ADDON_VERSION,
            "kind": "selection_preflight", "utc": _utc(), "config": spec,
            "config_sha256": hashlib.sha256(config.canonical(spec).encode()).hexdigest(),
            "targets": rows, "eligible_objects": sum(bool(r["actions"]) for r in rows),
            "runtime": runtime(context),
            "art_status": "experimental" if any(config.is_effective(spec, k) for k in ("material", "geometry", "lighting")) else "neutral_identity",
            "limits": ["Preview assigns only selected eligible object IDs using private data copies; this does not isolate their visible lighting/transport effects.",
                       "Known collection, vertex/face and particle instance sources are excluded across scenes; arbitrary Geometry Nodes/dependency references are not exhaustively analyzed.",
                       "Unsupported slots remain unchanged and are reported.",
                       "No painting algorithm or light value certifies reference matching.",
                       "No camera, world, compositor, actor transform or support correction is applied.",
                       "Bevels require new contact/silhouette review; clamp overlap is not certification."]}


def _snapshot(entry, obj):
    entry.snapshot_version = SNAPSHOT_VERSION
    entry.object_type = obj.type
    entry.obj = obj
    entry.object_name = obj.name
    entry.original_mesh = obj.data if obj.type == "MESH" else None
    entry.original_light = obj.data if obj.type == "LIGHT" else None
    entry.active_material_index = obj.active_material_index
    if obj.type == "MESH":
        for index, slot in enumerate(obj.material_slots):
            item = entry.slots.add()
            item.index, item.link, item.original_material = index, slot.link, slot.material
            item.original_data_material = obj.data.materials[index]
            item.had_original_material = slot.material is not None
            item.had_original_data_material = obj.data.materials[index] is not None


def _clean_unused(meshes, lights, materials):
    # Delete only private zero-user data; never purge user data or shared originals.
    for datablocks, items in ((bpy.data.meshes, meshes), (bpy.data.lights, lights), (bpy.data.materials, materials)):
        for data in set(items):
            if data and data.users == 0 and data.get("astra_preview_owner"):
                datablocks.remove(data)


def conflicts(scene):
    errors = []
    state = scene.astra_style
    for entry in state.preview_entries:
        obj = entry.obj
        if obj is None:
            # Deleted objects are not recreated. Their snapshots can still be safely released.
            continue
        if entry.snapshot_version != SNAPSHOT_VERSION:
            errors.append(f"{obj.name}: legacy/unqualified preview snapshot; use Keep or a saved baseline")
            continue
        if obj.type != entry.object_type or obj.mode != "OBJECT" or obj.library or obj.override_library:
            errors.append(f"{obj.name}: target type, mode or editability changed")
            continue
        preview = entry.preview_mesh if obj.type == "MESH" else entry.preview_light
        if not preview or obj.data != preview:
            errors.append(f"{obj.name}: data changed outside preview")
        if obj.type == "MESH":
            # Validate every destination before any object/modifier is restored.
            # Shared originals remain editable through unselected users.
            original = entry.original_mesh
            if not original or original.library or original.override_library:
                errors.append(f"{obj.name}: original mesh destination is missing or no longer editable")
            elif len(original.materials) != len(entry.slots):
                errors.append(f"{obj.name}: original mesh material slot count changed outside preview")
            else:
                for slot in entry.slots:
                    if (slot.index >= len(original.materials) or
                            (slot.had_original_data_material and not slot.original_data_material) or
                            original.materials[slot.index] != slot.original_data_material or
                            (slot.had_original_material and not slot.original_material)):
                        errors.append(f"{obj.name}: original mesh slot {slot.index} changed outside preview")
            if len(obj.material_slots) != len(entry.slots):
                errors.append(f"{obj.name}: material slot count changed outside preview")
            else:
                for slot in entry.slots:
                    expected = slot.preview_material or slot.original_material
                    current = obj.material_slots[slot.index]
                    if current.material != expected or current.link != slot.link:
                        errors.append(f"{obj.name}: slot {slot.index} changed outside preview")
            if entry.bevel_name:
                mod = obj.modifiers.get(entry.bevel_name)
                if not mod or mod.type != "BEVEL":
                    errors.append(f"{obj.name}: preview bevel was removed or renamed")
                elif not entry.bevel_state or modifier_state(obj, mod) != entry.bevel_state:
                    errors.append(f"{obj.name}: preview bevel state changed or was replaced; Keep preserves it")
        elif not entry.original_light or entry.original_light.library or entry.original_light.override_library:
            errors.append(f"{obj.name}: original light destination is missing or no longer editable")
    return errors


def revert(scene, check_conflicts=True):
    state = scene.astra_style
    errors = conflicts(scene) if check_conflicts else []
    if errors:
        raise ValueError("Revert stopped to preserve outside edits: " + "; ".join(errors) + ". Keep Preview preserves them.")
    meshes, lights, materials = [], [], []
    names = []
    for entry in state.preview_entries:
        obj = entry.obj
        if entry.preview_mesh:
            meshes.append(entry.preview_mesh)
        if entry.preview_light:
            lights.append(entry.preview_light)
        materials.extend(s.preview_material for s in entry.slots if s.preview_material)
        if obj is None:
            continue
        names.append(obj.name)
        if entry.bevel_name:
            mod = obj.modifiers.get(entry.bevel_name)
            if mod and mod.type == "BEVEL":
                obj.modifiers.remove(mod)
        if entry.original_mesh:
            obj.data = entry.original_mesh
            # Assignment to the original DATA slot is unnecessary and could touch other users.
            for s in entry.slots:
                current = obj.material_slots[s.index]
                current.link = s.link
                if s.link == "OBJECT":
                    current.material = s.original_material
            obj.active_material_index = entry.active_material_index
        elif entry.original_light:
            obj.data = entry.original_light
    state.preview_entries.clear()
    state.preview_token = ""
    state.preview_config = ""
    _clean_unused(meshes, lights, materials)
    return {"kind": "reverted", "objects": names, "utc": _utc()}


def keep(scene):
    state = scene.astra_style
    if not state.preview_token:
        raise ValueError("No active preview")
    names = [e.obj.name for e in state.preview_entries if e.obj]
    # References to originals are released without deleting them. Normal Blender Undo remains.
    record = {"kind": "kept_preview", "utc": _utc(), "objects": names,
              "config": json.loads(state.preview_config), "art_status": "experimental",
              "note": "Keeping edits is not an independent artistic acceptance verdict"}
    state.preview_entries.clear()
    state.preview_token = ""
    state.preview_config = ""
    return record


def preview(context, spec, acknowledged=False):
    spec = config.validate(spec)
    scene, state = context.scene, context.scene.astra_style
    if state.preview_token or len(state.preview_entries):
        raise ValueError("Revert or Keep the existing preview before starting another")
    plan = preflight(context, spec)
    if not plan["eligible_objects"]:
        raise ValueError("No eligible effective edits. Inspect Selection shows skipped targets; neutral settings do nothing")
    if not acknowledged:
        raise ValueError("Acknowledge experimental art controls before previewing")
    token = uuid.uuid4().hex
    state.preview_token = token
    state.preview_config = config.canonical(spec)
    applied = []
    try:
        for row in plan["targets"]:
            if not row["actions"]:
                continue
            obj = scene.objects.get(row["object"])
            if obj is None:
                raise ValueError("Selection changed before preview")
            entry = state.preview_entries.add()
            _snapshot(entry, obj)
            if obj.type == "MESH":
                copied = obj.data.copy()
                copied.name = obj.data.name + " | Astra preview"
                copied.use_fake_user = False
                copied["astra_preview_owner"] = token
                entry.preview_mesh = copied
                obj.data = copied
                if "material" in row["actions"]:
                    response.bind_rest_coordinates(copied, geometry.world_scale(obj, scene.unit_settings.scale_length))
                    material_cache = {}
                    for slot_row in row["material_slots"]:
                        if not slot_row["eligible"]:
                            continue
                        i = slot_row["index"]
                        old = entry.slots[i].original_material
                        mat = material_cache.get(old)
                        if mat is None:
                            mat = old.copy()
                            mat.name = old.name + " | Astra response"
                            mat.use_fake_user = False
                            mat["astra_preview_owner"] = token
                            # Track before node construction so an exception remains reversible.
                            entry.slots[i].preview_material = mat
                            response.apply_material(mat, spec["material"])
                            material_cache[old] = mat
                        entry.slots[i].preview_material = mat
                        obj.material_slots[i].material = mat
                if "geometry" in row["actions"]:
                    entry.bevel_name = geometry.add_bevel(obj, spec["geometry"], token, scene.unit_settings.scale_length)
                    entry.bevel_state = modifier_state(obj, obj.modifiers[entry.bevel_name])
            else:
                copied = obj.data.copy()
                copied.name = obj.data.name + " | Astra preview"
                copied.use_fake_user = False
                copied["astra_preview_owner"] = token
                entry.preview_light = copied
                obj.data = copied
                copied.energy *= 2 ** spec["lighting"]["exposure_delta"]
                copied.color = [a * b for a, b in zip(copied.color, spec["lighting"]["tint"])]
            applied.append({"object": obj.name, "actions": row["actions"]})
        context.view_layer.update()
    except Exception:
        revert(scene, check_conflicts=False)
        raise
    return {"kind": "preview_started", "utc": _utc(), "preview_token": token,
            "plan": plan, "applied": applied, "runtime_after": runtime(context),
            "note": "Render/view this preview, then Revert or Keep. Selection changes do not alter tracked targets."}
