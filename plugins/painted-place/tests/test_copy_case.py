"""
What this file does: checks the kit works as a builder gets it: a copy of the whole brief folder somewhere else. In a
fresh Python that uses only the copy, it places two parts, puts a store material on a ground of its own, lays a walkway
and a puddle on it and prepares for drawing; then checks that every picture in the scene was found, all of them inside
the copy, none in the original folder.
    python3 tests/test_copy_case.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import BRIEF, check  # noqa: E402

SCRIPT = r'''
import os, sys
COPY = sys.argv[1]
sys.path.insert(0, os.path.join(COPY, 'store', 'tools'))
import bpy
import store, lay_walkway, puddle
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=10.0)
ground = bpy.context.object
store.use_material(ground, 'SURFACE • mud_forest', ground=0.0)
store.add_part('barrel', location=(1.0, 2.0, 0.0), seed=2)
store.add_part('bell_tent', location=(-2.5, 3.0, 0.0), turn=40)
lay_walkway.lay([(0.0, -4.0, 0.0), (0.4, 0.0, 0.0), (0.0, 4.0, 0.0)], ground=ground, seed=1)
puddle.make((1.5, -1.0, 0.0), size=(1.2, 0.7), ground=ground, seed=1)
store.prepare_for_render(scene)
for image in bpy.data.images:
    if image.source == 'FILE' and image.packed_file is None and image.filepath:
        path = os.path.realpath(bpy.path.abspath(image.filepath))
        print('PICTURE', 'found' if os.path.exists(path) else 'missing', path)
print('STORE AT', os.path.realpath(store.STORE))
'''


def main():
    folder = tempfile.mkdtemp(prefix='kit-copy-')
    copy = os.path.join(folder, 'brief')
    try:
        shutil.copytree(BRIEF, copy, ignore=shutil.ignore_patterns('__pycache__', '*.blend1'))
        script = os.path.join(folder, 'use_the_copy.py')
        open(script, 'w').write(SCRIPT)
        result = subprocess.run([sys.executable, script, copy], capture_output=True, text=True, timeout=900, cwd=folder)
        check(result.returncode == 0, 'the copy case failed:\n' + result.stderr[-1500:])
        lines = result.stdout.splitlines()
        pictures = [line for line in lines if line.startswith('PICTURE ')]
        check(pictures, 'the copy case loaded no pictures at all')
        missing = [line for line in pictures if line.startswith('PICTURE missing')]
        check(not missing, 'pictures missing in the copy: %s' % missing[:3])
        original = os.path.realpath(BRIEF)
        outside = [line for line in pictures if original in line]
        check(not outside, 'pictures read from the original folder, not the copy: %s' % outside[:3])
        check(any(line.startswith('STORE AT ' + os.path.realpath(copy)) for line in lines), 'the store loaded from somewhere else')
        print('PASS test_copy_case: a copy of the brief folder works on its own (%d pictures found, all inside the copy)' % len(pictures))
    finally:
        shutil.rmtree(folder, ignore_errors=True)


if __name__ == '__main__':
    main()
