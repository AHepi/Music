"""What this does: proves that the normal maps in a scene point the right way, in two ways that need no human eye.
  1. For every normal map the kit made, the map's own pixels are compared with the height picture it was made from (kept in the scene next to
     it): the red channel's slope must agree with the height's slope along +U and the green channel's along +V (correlation at least +0.25;
     a flipped green channel reads about -1). An axis with almost no slope is reported "not informative" instead of failing (a plank map has
     almost no slope across the grain), so a good map is never failed for being flat on one side.
  2. One end-to-end TEST LIGHT: a flat plane with one round bump (made the kit's own way and wired with the kit's own nodes) is drawn with
     Cycles on the CPU under a low sun from +X and then from +Y; the side facing the light must be brighter. A deliberately flipped copy must
     read the other way, which proves the test is not blind. It runs in a scene of its own and leaves the open scene untouched.
Maps the kit did not make (imported pictures) cannot be proved this way: their convention is read from the file name (nor_gl is OpenGL, nor_dx
is DirectX and fails) or from a declared image property pk_convention; the report says which.
Needs Blender (bpy) and numpy; the test light draws a few tiny pictures (96 x 96) and takes a few seconds.
"""
import math
import os
import tempfile

import numpy as np

import bpy
from mathutils import Vector

from .. import house_numbers
from ..surfaces import heights, normals
from . import material_inspect


def unique_normal_images(only_visible_materials=True):
    """{image name: image} for every picture that feeds a Normal Map node in any material that is used."""
    found = {}
    for material in bpy.data.materials:
        if material.node_tree is None or material.users == 0:
            continue
        for node in material.node_tree.nodes:
            if node.type == 'NORMAL_MAP':
                for source in material_inspect.upstream_nodes(node.inputs['Color']):
                    if source.type == 'TEX_IMAGE' and source.image is not None:
                        found[source.image.name] = source.image
    return found


def convention_of(image):
    declared = image.get('pk_convention')
    if declared in ('opengl', 'directx'):
        return declared, 'declared' if not image.get('pk_made') else 'made by the kit'
    lowered = image.name.lower() + ' ' + (image.filepath or '').lower()
    if 'nor_dx' in lowered or 'directx' in lowered or '_dx' in lowered:
        return 'directx', 'file name'
    if 'nor_gl' in lowered or 'opengl' in lowered or '_gl' in lowered:
        return 'opengl', 'file name'
    return 'unknown', 'none'


def height_partner(image):
    """The height picture a kit-made normal map came from (pk_<surface>_nor goes with pk_<surface>_height), or None."""
    if image.name.endswith('_nor'):
        return bpy.data.images.get(image.name[:-4] + '_height')
    return None


def image_facts(image):
    array = normals.image_to_array(image)
    convention, how = convention_of(image)
    facts = {'name': image.name, 'size': [int(image.size[0]), int(image.size[1])], 'colourspace': image.colorspace_settings.name,
             'mean_rgb': normals.mean_rgb(array[..., :3]), 'convention': convention, 'convention_from': how, 'made_by_kit': bool(image.get('pk_made')), 'direction': {}}
    partner = height_partner(image)
    if partner is not None and tuple(partner.size) == tuple(image.size):
        height = normals.image_to_array(partner)[..., 0]
        correlation = normals.direction_correlation(array[..., :3], height)
        facts['direction'] = dict(correlation, method='height')
        limit = house_numbers.value('place_surfaces.normal_direction_correlation_min')
        informative = [v for v in correlation.values() if isinstance(v, float)]
        facts['verdict'] = 'fail' if any(v < limit for v in informative) else 'pass'
    elif convention in ('opengl', 'directx'):
        facts['direction'] = {'x': 'not informative', 'y': 'not informative', 'method': 'name'}
        facts['verdict'] = 'fail' if convention == 'directx' else 'pass'
    else:
        facts['verdict'] = 'not run'
    return facts


def _luminance(pixels, size, box):
    rows, cols = size
    array = np.array(pixels, dtype=np.float32).reshape(rows, cols, 4)[..., :3].mean(axis=2)
    r0, r1, c0, c1 = box
    return float(array[r0:r1, c0:c1].mean())


def test_normal_maps(size=96, samples=24, out_dir=None):
    """The end-to-end test light (see the note at the top). Returns {'verdict': 'pass'|'fail', 'detail': {...}, 'line': text}. It makes a scene
    of its own, draws with Cycles on the CPU and removes everything it made."""
    out_dir = out_dir or tempfile.mkdtemp(prefix='pk_nrmtest_')
    previous_scene = bpy.context.window.scene if bpy.context.window else bpy.context.scene
    test = bpy.data.scenes.new('pk_normal_test')
    made_images, made_materials, made_objects = [], [], []
    detail = {}
    try:
        test.render.engine = 'CYCLES'
        test.cycles.device = 'CPU'
        test.cycles.samples = samples
        test.cycles.use_denoising = False
        test.render.resolution_x = test.render.resolution_y = size
        test.render.resolution_percentage = 100
        test.view_settings.view_transform = 'Standard'
        test.world = bpy.data.worlds.new('pk_normal_test_world')
        test.world.color = (0, 0, 0)
        plane_mesh = bpy.data.meshes.new('pk_normal_test_plane')
        plane_mesh.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
        plane_mesh.uv_layers.new(name='UVMap')
        uv = plane_mesh.uv_layers[0]
        for loop, coord in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop.uv = coord
        plane = bpy.data.objects.new('pk_normal_test_plane', plane_mesh)
        test.collection.objects.link(plane)
        made_objects.append(plane)
        camera_data = bpy.data.cameras.new('pk_normal_test_cam')
        camera_data.type = 'ORTHO'
        camera_data.ortho_scale = 2.0
        camera = bpy.data.objects.new('pk_normal_test_cam', camera_data)
        camera.location = (0, 0, 5)
        test.collection.objects.link(camera)
        test.camera = camera
        made_objects.append(camera)
        sun_data = bpy.data.lights.new('pk_normal_test_sun', 'SUN')
        sun_data.energy = 4.0
        sun = bpy.data.objects.new('pk_normal_test_sun', sun_data)
        test.collection.objects.link(sun)
        made_objects.append(sun)
        n = 256
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        height = np.exp(-(((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (n * 0.18) ** 2))       # one soft round bump, white = high, rows from the top
        height = heights.calibrate_height(height, 30.0)
        reads = {}
        for flipped in (False, True):
            normal = normals.height_to_normal(height, strength=1.0, tile=False)
            if flipped:
                normal = normals.flip_green(normal)
            image = normals.make_normal_image('pk_normal_test_' + ('flipped' if flipped else 'ok'), normal)
            made_images.append(image)
            material = bpy.data.materials.new('pk_normal_test_material')
            material.use_nodes = True
            made_materials.append(material)
            principled = material.node_tree.nodes['Principled BSDF']
            principled.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1.0)
            principled.inputs['Roughness'].default_value = 1.0
            normals.add_normal_map_nodes(material, image, 'UVMap', strength=1.0, principled=principled)
            plane.data.materials.clear()
            plane.data.materials.append(material)
            for label, azimuth in (('+X', 0.0), ('+Y', 90.0)):
                elevation = math.radians(30.0)
                heading = Vector((-math.cos(math.radians(azimuth)) * math.cos(elevation), -math.sin(math.radians(azimuth)) * math.cos(elevation), -math.sin(elevation)))
                sun.rotation_euler = heading.to_track_quat('-Z', 'Y').to_euler()
                path = os.path.join(out_dir, f'normal_test_{"flipped" if flipped else "ok"}_{label[1]}.png')
                test.render.filepath = path
                bpy.ops.render.render(write_still=True, scene=test.name)
                loaded = bpy.data.images.load(path)
                pixels = np.array(loaded.pixels[:], dtype=np.float32)
                bpy.data.images.remove(loaded)
                rows = cols = size
                array = pixels.reshape(rows, cols, 4)[..., :3].mean(axis=2)          # rows from the BOTTOM: a higher row is +Y
                centre, width = size // 2, size // 6
                if label == '+X':
                    lit = float(array[centre - width:centre + width, centre + width // 2:centre + width + width // 2].mean())
                    dark = float(array[centre - width:centre + width, centre - width - width // 2:centre - width // 2].mean())
                else:
                    lit = float(array[centre + width // 2:centre + width + width // 2, centre - width:centre + width].mean())
                    dark = float(array[centre - width - width // 2:centre - width // 2, centre - width:centre + width].mean())
                reads[('flipped' if flipped else 'ok', label)] = (lit, dark, lit > dark * 1.05)
        ok = reads[('ok', '+X')][2] and reads[('ok', '+Y')][2]
        control_fails = not reads[('flipped', '+Y')][2]
        detail = {f'{k[0]} {k[1]}': {'lit_side': round(v[0], 4), 'dark_side': round(v[1], 4), 'lit_is_brighter': v[2]} for k, v in reads.items()}
        line = ('NORMAL_DIRECTION %s (sun from +X: %.3f vs %.3f; sun from +Y: %.3f vs %.3f; the flipped-green control reads the other way: %s)'
                % ('PASS' if (ok and control_fails) else 'FAIL', reads[('ok', '+X')][0], reads[('ok', '+X')][1], reads[('ok', '+Y')][0], reads[('ok', '+Y')][1], control_fails))
        return {'verdict': 'pass' if (ok and control_fails) else 'fail', 'detail': detail, 'line': line, 'control_fails': control_fails}
    finally:
        for obj in made_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        for material in made_materials:
            bpy.data.materials.remove(material)
        for image in made_images:
            bpy.data.images.remove(image)
        for block in list(bpy.data.meshes):
            if block.name.startswith('pk_normal_test') and block.users == 0:
                bpy.data.meshes.remove(block)
        for block in list(bpy.data.cameras):
            if block.name.startswith('pk_normal_test') and block.users == 0:
                bpy.data.cameras.remove(block)
        for block in list(bpy.data.lights):
            if block.name.startswith('pk_normal_test') and block.users == 0:
                bpy.data.lights.remove(block)
        world = test.world
        bpy.data.scenes.remove(test)
        if world is not None and world.users == 0:
            bpy.data.worlds.remove(world)


def normal_map_facts(run_light=True, size=96, samples=24):
    """What the audit stores under normal_maps: every unique normal image with its checks, and the test light (None when it is not run)."""
    images = [image_facts(image) for image in unique_normal_images().values()]
    light = test_normal_maps(size=size, samples=samples) if run_light else None
    return {'images': images, 'test_light': light}
