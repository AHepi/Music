# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# It puts the WETNESS layer (wetness_layer.py) onto the materials of the pit village street, in a COPY of the street opened in Blender (never the film
# project's own file). It also holds the small helpers the street tests share: the cameras (the film's main camera, the two other plate cameras, two close
# cameras) and the render settings.
#
# Which materials get the layer, and with what settings, is the table MATERIALS below (taken from the build plan, section 6 of the study):
#   street_setts (the road, a third of the main view)     Poly Haven's own roughness and height pictures, porosity 0.6, wet roughness 0.3, puddles gather toward
#                                                         the gutters (Lowness grows from the crown of the road to the kerbs)
#   pavement_flags                                        same, wet roughness 0.45 and a calmer relief (or the flagstones look gritty), fewer puddles
#   channel_stones, kerb_stone                            the gutter is always wet (Wetness x 1.15), lowness 1
#   cottage_brick, cottage_stone (the walls)              measured in the wall's OWN coordinates: wet band at the foot, streaks under every window sill
#                                                         and the eaves (made from the street builder's own window numbers, FACADE_LAYOUTS etc.), wet roughness 0.45
#   colliery_brick, dressed_stone, dark_dressed_stone     porosity 0.7 / 0.5; measured in the world
#   roof_slate                                            porosity 0.3, wet roughness 0.25 (a sheen; roofs are 1 % of the main view)
#   colliery_yard                                         porosity 0.7
# Nothing is replaced by a texture recipe (the plan says: only the road setts could be, as a second step, after a painter test).
#
# ROUND 2 (what the checker found): the settings below were changed as follows (the reasons are in the recipe note, section "Round 2"):
#   road and pavements: a SMOOTHED copy of the relief picture for the wet state (cure for EEVEE speckle), flatter relief, pavement flags back to a lower wet roughness;
#   walls: no extra shine (Specular Boost 0, no coat), wet roughness 0.9, the same as dry (a wet wall is darker, not glossier: tested, 0.75 made the lamp-lit base brighter), strong darkening (porosity 1.0, darkest 0.2), and the wet band measured from the
#   cottage FLOOR in the cottage's own coordinates and made 0.9 m tall (round 1 measured from the pavement, so the dressed-stone plinth hid it).
#
# Use (inside Blender, with the street copy open):
#     import apply_wetness_to_set as aw
#     aw.apply(wetness=0.85, puddles=0.5)         # puts the layer on and sets the state
#     aw.set_state(wetness=1.0, puddles=0.8)      # changes the state of every layer already on (heavier rain)
#     aw.set_state(wetness=0.0, puddles=0.0)      # dry again, but with Poly Haven's real roughness and height pictures (the "new materials, dry" look)
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import wetness_layer as wl  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..'))
TEX = os.path.join('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet', 'set_copy', 'polyhaven_maps') + os.sep
SLOPE = math.tan(math.radians(4.0))      # the street's rise per metre (build_street.py: SLOPE_DEGREES = 4)
# wall geometry copied from build_street.py (GROUND_WINDOW, UPPER_WINDOW, FACADE_LAYOUTS, EAVES_HEIGHT, COTTAGE_WIDTH): in the cottage's own coordinates
GROUND_WINDOW = dict(width=1.05, height=1.55, sill=0.85)
UPPER_WINDOW = dict(width=0.95, height=1.35, sill=3.55)
FACADE_LAYOUTS = {'door_left': dict(door=-1.15, window=0.95, upper=(-1.15, 0.95)), 'door_right': dict(door=1.15, window=-0.95, upper=(1.15, -0.95))}
EAVES_HEIGHT, HALF_WIDTH = 6.0, 2.25
WALL_FOOT_OFFSET = -(HALF_WIDTH * SLOPE + 0.15)          # the cottage floor stands 0.15 above the pavement at the uphill end of the house (build_street.py)

# name: rough picture, height picture, porosity, wet roughness, extras
MATERIALS = {
    'street_setts': dict(rough='square_cobblestone_rough.jpg', height='square_cobblestone_displacement.jpg', smooth_normal='square_cobblestone_normal_smooth_4.png',
                         porosity=0.6, wet_roughness=0.3, lowness='road', relief_flatten=0.7),
    'pavement_flags': dict(rough='large_grey_tiles_rough.jpg', height='large_grey_tiles_displacement.jpg', smooth_normal='large_grey_tiles_normal_smooth_2.png',
                           porosity=0.55, wet_roughness=0.35, lowness='pavement', relief_flatten=1.0, puddle_bias=0.22),
    'channel_stones': dict(porosity=0.5, wet_roughness=0.3, lowness=1.0, wetness_scale=1.15),
    'kerb_stone': dict(porosity=0.5, wet_roughness=0.35, lowness=0.3, wetness_scale=1.05),
    'cottage_brick': dict(rough='red_brick_rough.jpg', height='red_brick_displacement.jpg', porosity=1.0, darkest=0.2, wet_roughness=0.9, specular_boost=0.0, film_coat=0.0,
                          wall_band=0.9, wall='left_row'),
    'cottage_stone': dict(rough='stone_brick_wall_001_rough.jpg', height='stone_brick_wall_001_displacement.jpg', porosity=1.0, darkest=0.2, wet_roughness=0.9, specular_boost=0.0,
                          film_coat=0.0, wall_band=0.9, wall='right_row'),
    'colliery_brick': dict(porosity=0.7, wet_roughness=0.5, specular_boost=0.0, film_coat=0.05),
    'dressed_stone': dict(porosity=0.8, darkest=0.3, wet_roughness=0.6, ground_offset=0.13, specular_boost=0.0, film_coat=0.0, wall_band=0.6),
    'dark_dressed_stone': dict(porosity=0.8, darkest=0.3, wet_roughness=0.6, ground_offset=0.13, specular_boost=0.0, film_coat=0.0, wall_band=0.6),
    'roof_slate': dict(porosity=0.3, wet_roughness=0.4, specular_boost=0.05, film_coat=0.05),
    'colliery_yard': dict(porosity=0.7, wet_roughness=0.4),
}
# Round 1 had a separate "cure" for EEVEE flagstones; round 2 builds it into MATERIALS (relief flatten 1.0, smoothed relief picture). Kept for old scripts.
PAVEMENT_FOR_EEVEE = dict(relief_flatten=1.0, wet_roughness=0.35)
APPLIED = {}      # material name (or variant name) -> (group node, settings)


# ------------------------------------------------------------------------------------------------------------------------------- cameras
def make_camera(name, location, look_at=None, quaternion_wxyz=None, fov_vertical=40.0):
    scene = bpy.context.scene
    data = bpy.data.cameras.new(name)
    data.sensor_fit = 'VERTICAL'
    data.angle_y = math.radians(fov_vertical)
    camera = bpy.data.objects.new(name, data)
    scene.collection.objects.link(camera)
    camera.location = Vector(location)
    if quaternion_wxyz is not None:
        camera.rotation_mode = 'QUATERNION'
        camera.rotation_quaternion = quaternion_wxyz
    else:
        camera.rotation_euler = (Vector(look_at) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    return camera


def cameras():
    """The cameras the street tests use. 'main' is the film's own main camera (as it is in the file)."""
    result = {'main': bpy.context.scene.camera}
    result['lockout'] = make_camera('lockout_plate', (-1.0, 1.2, 1.69709), quaternion_wxyz=(0.65516, 0.753675, -0.039498, -0.034335), fov_vertical=44.0)
    result['notice'] = make_camera('notice_plate', (2.99313, 16.35381, 3.18819), quaternion_wxyz=(0.705836, 0.705836, 0.042367, 0.042367), fov_vertical=64.4)
    result['close_road'] = make_camera('close_road', (0.5, 6.0, 1.0), look_at=(0.0, 11.0, 0.45), fov_vertical=38.0)
    # standing in the road, looking at the foot of the right-hand wall beside the first gas lamp (post at x 3.03, y 11)
    result['wall_lamp'] = make_camera('wall_lamp', (1.3, 7.6, 1.05), look_at=(4.0, 11.3, 0.7), fov_vertical=40.0)
    return result


# ------------------------------------------------------------------------------------------------------------------------------- render
def cycles_settings(scene, width, height, samples):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 6
    scene.cycles.glossy_bounces = 4
    scene.cycles.sample_clamp_indirect = 8.0
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'


def mask_settings(scene, width, height):
    """One-sample 'raw numbers' pictures: no colour look, no noise filter, black world (what a mask picture needs)."""
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.pixel_filter_type = 'BOX'
    scene.cycles.filter_width = 1.0
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.dither_intensity = 0.0
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '16'
    scene.view_settings.view_transform = 'Raw'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    background = scene.world.node_tree.nodes['Background']
    background.inputs['Color'].default_value = (0, 0, 0, 1)
    background.inputs['Strength'].default_value = 0.0


# ------------------------------------------------------------------------------------------------------------------------------- the layer on the street
def _lowness_from_x(tree, start, end, invert=False):
    """A socket that goes 0 -> 1 as |x| (across the street) goes from start to end metres."""
    geometry = tree.nodes.new('ShaderNodeNewGeometry')
    split = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(geometry.outputs['Position'], split.inputs[0])
    absolute = tree.nodes.new('ShaderNodeMath')
    absolute.operation = 'ABSOLUTE'
    tree.links.new(split.outputs['X'], absolute.inputs[0])
    ramp = tree.nodes.new('ShaderNodeMapRange')
    ramp.interpolation_type = 'SMOOTHSTEP'
    ramp.inputs['From Min'].default_value, ramp.inputs['From Max'].default_value = start, end
    if invert:
        ramp.inputs['To Min'].default_value, ramp.inputs['To Max'].default_value = 1.0, 0.0
    tree.links.new(absolute.outputs[0], ramp.inputs['Value'])
    return ramp.outputs['Result']


def drip_sources(layout_name):
    """(centre, half width, top, length) of every rain streak source of a cottage front: each window sill, and the eaves."""
    layout = FACADE_LAYOUTS[layout_name]
    sources = [(layout['window'], GROUND_WINDOW['width'] / 2 + 0.15, GROUND_WINDOW['sill'] - 0.1, 0.7)]
    for upper_y in layout['upper']:
        sources.append((upper_y, UPPER_WINDOW['width'] / 2 + 0.15, UPPER_WINDOW['sill'] - 0.1, 1.0))
    sources.append((-1.0, 1.0, EAVES_HEIGHT - 0.25, 1.3))       # the eaves: two wide sources with a gap between
    sources.append((1.3, 0.8, EAVES_HEIGHT - 0.25, 1.3))
    return sources


def _image(name):
    image = bpy.data.images.load(TEX + name, check_existing=True)
    return image


def apply(wetness=0.85, puddles=0.5, only=None, seed=3.0, **overrides):
    """Puts the layer on every material of MATERIALS (or only those named) and sets the state. overrides: group settings for every material,
    e.g. puddle_roughness=0.08."""
    for name, spec in MATERIALS.items():
        if only and name not in only:
            continue
        base = bpy.data.materials[name]
        variants = [(base, None)]
        if spec.get('wall'):
            # the walls: one copy of the material per facade layout (the streaks sit under that layout's windows), the plain one stays for the chimneys
            for layout_name in FACADE_LAYOUTS:
                variant = base.copy()
                variant.name = f'{name}_{layout_name}'
                variants.append((variant, layout_name))
                for mesh in bpy.data.meshes:
                    if mesh.name == f'cottage_shell_{name}_{layout_name}_walls':
                        for index, slot_material in enumerate(mesh.materials):
                            if slot_material == base:
                                mesh.materials[index] = variant
        for material, layout_name in variants:
            tree = material.node_tree
            kwargs = dict(porosity=spec['porosity'], wet_roughness=spec['wet_roughness'], seed=seed, ground_offset=spec.get('ground_offset', 0.0),
                          relief_flatten=spec.get('relief_flatten', 0.35), puddle_bias=spec.get('puddle_bias', 0.0), darkest=spec.get('darkest', 0.45),
                          specular_boost=spec.get('specular_boost', 0.25), film_coat=spec.get('film_coat', 0.3), wall_band=spec.get('wall_band', 0.45),
                          smooth_normal_image=_image(spec['smooth_normal']) if spec.get('smooth_normal') else None)
            lowness = None
            if spec.get('lowness') == 'road':
                lowness = _lowness_from_x(tree, 0.6, 2.1)
            elif spec.get('lowness') == 'pavement':
                lowness = _lowness_from_x(tree, 2.7, 4.4, invert=True)        # water gathers toward the kerb, where the pavement falls to
            position = drip = None
            if spec.get('wall') and layout_name:
                coords = tree.nodes.new('ShaderNodeTexCoord')
                position = coords.outputs['Object']
                drip = wl.drip_chain(tree, position, drip_sources(layout_name), seed=seed)
                # round 2: measured from the cottage FLOOR (local z = 0), which is flat across one house: no slope, no offset
                kwargs.update(ground_slope=0.0, ground_offset=0.0)
            kwargs.update(overrides)
            node = wl.add_wetness_to_material(material, wetness=0.0, puddles=0.0, rough_image=_image(spec['rough']) if spec.get('rough') else None,
                                              height_image=_image(spec['height']) if spec.get('height') else None, lowness=lowness, position=position, drip=drip,
                                              **kwargs)
            if isinstance(spec.get('lowness'), float):
                node.inputs['Lowness'].default_value = spec['lowness']
            APPLIED[material.name] = (node, spec)
    set_state(wetness, puddles)


def set_state(wetness, puddles):
    for name, (node, spec) in APPLIED.items():
        node.inputs['Wetness'].default_value = min(1.0, wetness * spec.get('wetness_scale', 1.0))
        node.inputs['Puddles'].default_value = puddles * spec.get('puddle_scale', 1.0) if puddles > 0 else 0.0
