"""Read-only evaluated diagnostics and a deliberately small bevel control."""
import hashlib
import math
import struct
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def world_scale(obj, unit_scale=1.0):
    return tuple(obj.matrix_world.to_3x3().col[i].length * unit_scale for i in range(3))


def orthogonal_transform(obj, tolerance=1e-5):
    axes = [obj.matrix_world.to_3x3().col[i] for i in range(3)]
    if min(a.length for a in axes) < 1e-8:
        return False
    return all(abs(axes[i].normalized().dot(axes[j].normalized())) < tolerance
               for i in range(3) for j in range(i + 1, 3))


def bevel_contract(obj, spec, unit_scale):
    if not orthogonal_transform(obj):
        return False, "Sheared/singular transforms are not supported"
    scale = world_scale(obj, unit_scale)
    if max(scale) / min(scale) > 1.00001:
        return False, "Metric bevel requires uniform world scale; transforms are not auto-applied"
    spans = [max(v.co[i] for v in obj.data.vertices) - min(v.co[i] for v in obj.data.vertices)
             for i in range(3)] if obj.data.vertices else [0, 0, 0]
    positive = [spans[i] * scale[i] for i in range(3) if spans[i] * scale[i] > 1e-8]
    if len(positive) != 3:
        return False, "Bevel is limited to non-flat solids"
    if spec["bevel_width_m"] > .1 * min(positive):
        return False, "Width exceeds 10% of the smallest base-mesh dimension"
    return True, "Unapplied angle-limited bevel; contact and silhouette still require review"


def add_bevel(obj, spec, token, unit_scale):
    mod = obj.modifiers.new("Astra Preview " + token[:12], "BEVEL")
    mod.width = spec["bevel_width_m"] / world_scale(obj, unit_scale)[0]
    mod.segments = spec["segments"]
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(spec["angle_degrees"])
    mod.use_clamp_overlap = True
    return mod.name


def evaluated_mesh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        if mesh is None:
            return [], []
        mesh.calc_loop_triangles()
        vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]
        triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
        return vertices, triangles
    finally:
        evaluated.to_mesh_clear()


def audit(context, objects):
    if context.mode != "OBJECT":
        raise ValueError("Evaluated diagnostics require Object Mode")
    # Required after copied objects or transforms: source intent is not runtime geometry.
    context.view_layer.update()
    depsgraph = context.evaluated_depsgraph_get()
    items = []
    for obj in sorted(objects, key=lambda o: o.name):
        if obj.type != "MESH":
            continue
        vertices, triangles = evaluated_mesh(obj, depsgraph)
        finite = all(math.isfinite(x) for v in vertices for x in v)
        digest = hashlib.sha256()
        for v in vertices:
            digest.update(struct.pack("<ddd", *v))
        for t in triangles:
            digest.update(struct.pack("<III", *t))
        bounds = [[min(v[i] for v in vertices) for i in range(3)],
                  [max(v[i] for v in vertices) for i in range(3)]] if vertices and finite else None
        zero = sum((vertices[b] - vertices[a]).cross(vertices[c] - vertices[a]).length == 0
                   for a, b, c in triangles) if finite else None
        items.append({"object": obj.name, "evaluated_vertices": len(vertices),
                      "evaluated_triangles": len(triangles), "finite": finite,
                      "exact_zero_area_triangles": zero, "world_bounds_blender_units": bounds,
                      "geometry_sha256_float64": digest.hexdigest(),
                      "hide_render": obj.hide_render,
                      "visible_in_current_view_layer": obj.visible_get(view_layer=context.view_layer),
                      "declared_role": obj.get("astra_role", "unspecified"),
                      "matrix_world": [list(row) for row in obj.matrix_world]})
    candidates = []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            x, y = a["world_bounds_blender_units"], b["world_bounds_blender_units"]
            if x and y and all(min(x[1][k], y[1][k]) > max(x[0][k], y[0][k]) for k in range(3)):
                candidates.append([a["object"], b["object"]])
    return {"schema_version": "1.0.0", "kind": "evaluated_selection_audit",
            "mode": "current_view_layer_evaluation", "unit_scale_metres": context.scene.unit_settings.scale_length,
            "objects": items, "aabb_overlap_candidates_only": candidates,
            "limitations": ["AABB candidates are not confirmed intersections or defects.",
                "No instances are flattened; no global collision, watertightness or contact verdict.",
                "Viewport and render modifier states can differ; this is current view-layer evaluation.",
                "Intentional structural overlaps and under-deck contacts can be valid.",
                "Visibility and support identity changes invalidate old contact evidence.",
                "No automatic art score or reference-match claim."]}


def sample_support(context, support, targets, max_samples=128):
    """Downward finite probes, explicit active support only; no support inference."""
    if context.mode != "OBJECT":
        raise ValueError("Support diagnostics require Object Mode")
    if not isinstance(max_samples, int) or max_samples < 2 or max_samples > 4096:
        raise ValueError("max_samples must be an integer from 2 to 4096")
    if support is None or support.type != "MESH":
        raise ValueError("The active object must be the explicitly chosen mesh support")
    if support.hide_render or not support.visible_get(view_layer=context.view_layer):
        raise ValueError("Hidden support is excluded; choose a visible physical support")
    if support.get("astra_role") in {"surface_art", "transport_envelope", "volume_domain"}:
        raise ValueError("Surface artwork or a transport/volume envelope is not a physical support")
    materials = [slot.material for slot in support.material_slots if slot.material]
    def volume_only(mat):
        if not mat.use_nodes or not mat.node_tree:
            return False
        outputs = [n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output]
        return bool(outputs) and all(n.inputs["Volume"].is_linked and not n.inputs["Surface"].is_linked for n in outputs)
    if materials and all(volume_only(mat) for mat in materials):
        raise ValueError("A volume-only mesh envelope is not a physical support")
    context.view_layer.update()
    deps = context.evaluated_depsgraph_get()
    verts, faces = evaluated_mesh(support, deps)
    if not verts or not faces or not all(math.isfinite(x) for v in verts for x in v):
        raise ValueError("Support has no usable finite evaluated triangles")
    tree = BVHTree.FromPolygons(verts, faces, all_triangles=True, epsilon=0.0)
    unit = context.scene.unit_settings.scale_length
    top = max(v.z for v in verts)
    bottom = min(v.z for v in verts)
    rows = []
    for obj in sorted(targets, key=lambda o: o.name):
        if obj == support or obj.type != "MESH":
            continue
        vs, _ = evaluated_mesh(obj, deps)
        if not vs or not all(math.isfinite(x) for v in vs for x in v):
            rows.append({"object": obj.name, "status": "no_finite_vertices"})
            continue
        z = min(v.z for v in vs)
        # This is intentionally a stated horizontal bottom band, not an anatomical sole detector.
        points = [v for v in vs if v.z <= z + .003 / unit]
        if len(points) > max_samples:
            points = [points[round(i * (len(points) - 1) / (max_samples - 1))] for i in range(max_samples)]
        samples = []
        for point in points:
            origin_z = max(point.z, top) + 1.0 / unit
            hit, normal, index, distance = tree.ray_cast(Vector((point.x, point.y, origin_z)),
                Vector((0, 0, -1)), origin_z - bottom + 1.0 / unit)
            samples.append({"target_point_world": list(point), "support_triangle": index,
                            "support_hit_world": list(hit) if hit is not None else None,
                            "signed_vertical_gap_m": (point.z - hit.z) * unit if hit is not None else None})
        rows.append({"object": obj.name, "status": "sampled", "samples": samples})
    return {"schema_version": "1.0.0", "kind": "explicit_support_samples",
            "support": support.name, "support_role": support.get("astra_role", "user_selected_physical_support"),
            "sample_rule": "At most 128 evaluated vertices within 3 mm of each object's world-Z minimum",
            "objects": rows, "acceptance": "not_determined",
            "limitations": ["Vertical finite samples only; not full underside coverage or structural certification.",
                "Negative gap means support top is above a sample, not automatically a visual defect.",
                "No ray hit is a miss, never an assumed ground height.",
                "Check actual support material, visibility, contact pixels, clearance and intentional overlap separately."]}
