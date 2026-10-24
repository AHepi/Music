"""What this does: applies the film owner's rule for which renderer draws a place: Cycles for views where lamps, windows, lanterns or fires are
lit (it looks far better there, and the owner said it is worth the cost), EEVEE when they are off (it is fine and quick). It looks at the open
scene and returns the choice with the reasons, so the rule is applied the same way every time and a person can read why.
The rule: Cycles when any visible lamp that is not the sun has energy above 0; or any visible object uses a material that really glows
(emission strength above 0 with a colour that is not black); or an object has the glow role. Otherwise EEVEE (a daylight sun alone is EEVEE).
It needs Blender (bpy). A concrete example: a scene with a point lamp inside a lantern gives {'engine': 'CYCLES', 'reasons': ['lamp "lantern lamp"
(point, 50 W) is on']}.
"""
import bpy

from .. import names, scene_read


def lit_lamps():
    found = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'LIGHT' or obj.hide_render:
            continue
        try:
            if not obj.visible_get():
                continue
        except RuntimeError:
            continue
        light = obj.data
        if light.type != 'SUN' and light.energy > 0:
            found.append(f'lamp "{obj.name}" ({light.type.lower()}, {light.energy:g} W) is on')
    return found


def glowing_materials():
    found, seen = [], set()
    for obj in scene_read.mesh_objects(only_visible=True):
        for slot in obj.material_slots:
            material = slot.material
            if material is None or material.name in seen or material.node_tree is None:
                continue
            seen.add(material.name)
            for node in material.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    strength, colour = node.inputs['Emission Strength'], node.inputs['Emission Color']
                    if strength.links or (strength.default_value > 0 and (colour.links or max(colour.default_value[:3]) > 0)):
                        found.append(f'material "{material.name}" glows (on "{obj.name}")')
                        break
                elif node.type == 'EMISSION':
                    strength, colour = node.inputs['Strength'], node.inputs['Color']
                    if strength.default_value > 0 and (colour.links or max(colour.default_value[:3]) > 0) and node.outputs['Emission'].links:
                        found.append(f'material "{material.name}" glows (on "{obj.name}")')
                        break
    return found


def glow_role_objects():
    return [f'object "{o.name}" has the glow role' for o in scene_read.mesh_objects(only_visible=True) if o.get(names.ROLE) == 'never.glow']


def renderer_for_scene():
    """{'engine': 'CYCLES' | 'EEVEE', 'reasons': [...]} by the film owner's rule (see the note at the top)."""
    reasons = lit_lamps() + glowing_materials() + glow_role_objects()
    if reasons:
        return {'engine': 'CYCLES', 'reasons': reasons}
    return {'engine': 'EEVEE', 'reasons': ['nothing is lit: no lamp but the sun, no glowing material, no glow object (EEVEE is fine when the lights are off)']}
