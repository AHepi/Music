# What this file does: opens a finished village scene inside Blender and counts
# which surface treatments it really uses (normal maps, bump, displacement,
# dirt, grime, moss, weeds, wear, damage and so on), then writes the counts to
# a JSON file named on the command line after "--".
import bpy
import json
import sys

output_path = sys.argv[sys.argv.index("--") + 1]

word_groups = {
    "dirt_or_mud": ["dirt", "mud", "soil", "earth", "dust"],
    "grime_or_stain": ["grime", "stain", "soot", "drip", "streak"],
    "moss_or_lichen": ["moss", "lichen", "algae"],
    "weeds_grass_flowers": ["weed", "grass", "fern", "flower", "nettle", "dock", "clover", "tuft"],
    "wear_or_damage": ["wear", "damage", "crack", "broken", "chip", "rot", "worn", "scuff", "split"],
    "wet_or_puddle": ["puddle", "wet", "water"],
    "ruts_and_hoof_prints": ["rut", "hoof", "track", "print"],
    "droppings_straw_leaves_twigs": ["dung", "straw", "hay", "leaf", "leaves", "twig", "pebble", "stone"],
}


def node_types_in_tree(node_tree, seen_trees=None):
    """Collect every node type in a material, looking inside node groups too."""
    if seen_trees is None:
        seen_trees = set()
    found_types = []
    if node_tree is None or node_tree.name in seen_trees:
        return found_types
    seen_trees.add(node_tree.name)
    for node in node_tree.nodes:
        found_types.append(node.bl_idname)
        if node.bl_idname == "ShaderNodeGeometry":
            for output_socket in node.outputs:
                if output_socket.name == "Pointiness" and output_socket.is_linked:
                    found_types.append("uses_pointiness_for_edges")
        if getattr(node, "node_tree", None) is not None:
            found_types.extend(node_types_in_tree(node.node_tree, seen_trees))
    return found_types


def material_uses_displacement(material):
    output_node = None
    for node in material.node_tree.nodes:
        if node.bl_idname == "ShaderNodeOutputMaterial":
            output_node = node
    if output_node is None:
        return False
    displacement_socket = output_node.inputs.get("Displacement")
    return bool(displacement_socket and displacement_socket.is_linked)


used_materials = set()
for scene_object in bpy.data.objects:
    for material_slot in getattr(scene_object, "material_slots", []):
        if material_slot.material is not None:
            used_materials.add(material_slot.material.name)

material_rows = []
for material in bpy.data.materials:
    if not material.use_nodes or material.node_tree is None:
        continue
    node_types = node_types_in_tree(material.node_tree)
    material_rows.append({
        "name": material.name,
        "in_use": material.name in used_materials,
        "normal_map": "ShaderNodeNormalMap" in node_types,
        "bump": "ShaderNodeBump" in node_types,
        "displacement_into_output": material_uses_displacement(material),
        "true_displacement_setting": getattr(material, "displacement_method", "") in ("DISPLACEMENT", "BOTH"),
        "image_files": node_types.count("ShaderNodeTexImage"),
        "noise_patterns": sum(node_types.count(kind) for kind in (
            "ShaderNodeTexNoise", "ShaderNodeTexVoronoi", "ShaderNodeTexWave",
            "ShaderNodeTexMusgrave", "ShaderNodeTexGabor", "ShaderNodeTexBrick")),
        "edge_wear_by_corners": ("uses_pointiness_for_edges" in node_types
                                  or "ShaderNodeAmbientOcclusion" in node_types
                                  or "ShaderNodeBevel" in node_types),
        "colour_variation_per_object": "ShaderNodeObjectInfo" in node_types,
        "painted_attributes": "ShaderNodeAttribute" in node_types or "ShaderNodeVertexColor" in node_types,
    })

in_use_rows = [row for row in material_rows if row["in_use"]]

modifier_counts = {}
for scene_object in bpy.data.objects:
    for modifier in getattr(scene_object, "modifiers", []):
        modifier_counts[modifier.type] = modifier_counts.get(modifier.type, 0) + 1

depsgraph = bpy.context.evaluated_depsgraph_get()
triangle_total = 0
instance_total = 0
for object_instance in depsgraph.object_instances:
    if object_instance.is_instance:
        instance_total += 1
for evaluated_object in [scene_object.evaluated_get(depsgraph) for scene_object in bpy.data.objects if scene_object.type == "MESH"]:
    mesh = evaluated_object.data
    if mesh is not None:
        triangle_total += sum(len(polygon.vertices) - 2 for polygon in mesh.polygons)

all_names = [name.lower() for name in
             [o.name for o in bpy.data.objects] + [m.name for m in bpy.data.materials]
             + [c.name for c in bpy.data.collections] + [n.name for n in bpy.data.node_groups]]
word_group_hits = {}
for group_name, words in word_groups.items():
    word_group_hits[group_name] = sorted({name for name in all_names if any(word in name for word in words)})[:25]

scene = bpy.context.scene
summary = {
    "renderer": scene.render.engine,
    "objects": len(bpy.data.objects),
    "mesh_objects": sum(1 for o in bpy.data.objects if o.type == "MESH"),
    "materials_in_use": len(in_use_rows),
    "materials_with_normal_map": sum(row["normal_map"] for row in in_use_rows),
    "materials_with_bump": sum(row["bump"] for row in in_use_rows),
    "materials_with_displacement": sum(row["displacement_into_output"] for row in in_use_rows),
    "materials_with_true_displacement_setting": sum(row["true_displacement_setting"] for row in in_use_rows),
    "materials_with_image_files": sum(1 for row in in_use_rows if row["image_files"] > 0),
    "materials_with_edge_wear_by_corners": sum(row["edge_wear_by_corners"] for row in in_use_rows),
    "materials_with_colour_variation_per_object": sum(row["colour_variation_per_object"] for row in in_use_rows),
    "materials_with_painted_attributes": sum(row["painted_attributes"] for row in in_use_rows),
    "images_loaded": len(bpy.data.images),
    "modifier_counts": modifier_counts,
    "particle_systems": sum(len(o.particle_systems) for o in bpy.data.objects if hasattr(o, "particle_systems")),
    "instances_after_scatter": instance_total,
    "triangles_before_instances": triangle_total,
    "names_matching_treatments": word_group_hits,
    "materials": material_rows,
}
with open(output_path, "w") as output_file:
    json.dump(summary, output_file, indent=1)
print("COUNT_DONE", output_path)
