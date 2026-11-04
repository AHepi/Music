"""
What this file does: checks the store's materials (brief/store/materials/Materials.blend): every material comes in by
name, every photograph it uses is found on the shelf, every material says what it is, the surface materials carry their
dials and sit darkened into the look, and the made materials that read numbers from a mesh name the numbers the tools
write.
    python3 tests/test_store_materials.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import store  # noqa: E402


def attribute_names(material):
    return {n.attribute_name for n in material.node_tree.nodes if n.type == 'ATTRIBUTE'}


def main():
    fresh_scene()
    names = store.names('materials')
    check(len(names) >= 79, 'only %d materials in the store' % len(names))
    surfaces = [n for n in names if n.startswith('SURFACE • ')]
    made = [n for n in names if n.startswith('MADE • ')]
    check(len(surfaces) >= 23, 'only %d surface materials' % len(surfaces))
    for name in names:
        material = store.material(name)
        check(material is not None and material.name == name, 'material %r did not come in by name' % name)
        check(material.get('store_what'), 'material %r does not say what it is (store_what)' % name)
    for image in bpy.data.images:
        if image.source == 'FILE' and image.packed_file is None and image.filepath:
            check(os.path.exists(bpy.path.abspath(image.filepath)), 'picture not found: %s' % image.filepath)
    for name in surfaces:
        nodes = bpy.data.materials[name].node_tree.nodes
        check('Weather' in nodes and 'Picture size' in nodes, '%s has lost its Weather or Picture size dials' % name)
        darken = nodes['Weather'].inputs['Darken'].default_value
        check(0.3 <= darken <= 1.0, '%s: Darken %.2f is outside 0.3 to 1' % (name, darken))
        check(bpy.data.materials[name].get('store_size_m'), '%s does not record its real size' % name)
    check('shallow' in attribute_names(bpy.data.materials['MADE • puddle water']), 'puddle water no longer reads shallow')
    check('dry' in attribute_names(bpy.data.materials['MADE • wet ground film']), 'wet ground film no longer reads dry')
    check('fade' in attribute_names(bpy.data.materials['MADE • rust stain']), 'rust stain no longer reads fade')
    for kind in ('soot', 'damp', 'rust', 'mud', 'coal dust', 'ash'):
        check('fade' in attribute_names(bpy.data.materials['MADE • stain ' + kind]), 'stain %s does not read fade' % kind)
    walkway = attribute_names(bpy.data.materials['MADE • walkway boards'])
    check({'board_tone', 'across', 'wear', 'wet', 'mud'} <= walkway, 'walkway boards read %s' % sorted(walkway))
    check('board_tone' in attribute_names(bpy.data.materials['MADE • weathered boards, peeling paint']), 'weathered boards no longer read board_tone')
    print('PASS test_store_materials: %d materials come in by name (%d surfaces, %d made), every picture found, every one described'
          % (len(names), len(surfaces), len(made)))


if __name__ == '__main__':
    main()
