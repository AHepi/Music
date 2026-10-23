"""Dependency-free regression checks for the coal-mine design fixes.

Run with: python3 -m unittest discover -s tests -p 'test_design_regressions.py'
These checks cover layout and wiring. Final appearance still needs a Blender render with the user's texture folder.
"""
import ast
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / 'modules' / 'engine_house.py'


def parse(path):
    return ast.parse(path.read_text(encoding='utf-8'), filename=str(path))


def function_node(tree, name):
    return next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)


def assigned_literal(tree, function_name, target_name):
    function = function_node(tree, function_name)
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(isinstance(name, ast.Name) and name.id == target_name
                                               for target in node.targets for name in ast.walk(target)):
            return ast.literal_eval(node.value)
    raise AssertionError(f'{function_name} does not assign {target_name}')


def overlaps(a, b, margin=0.0):
    """Two (min_x, max_x, min_y, max_y) rectangles, with a required safety margin."""
    return not (a[1] + margin <= b[0] or b[1] + margin <= a[0] or a[3] + margin <= b[2] or b[3] + margin <= a[2])


FOOTING_HALF_SIZE = 0.65
FOOTINGS = [
    (x - FOOTING_HALF_SIZE, x + FOOTING_HALF_SIZE, y - FOOTING_HALF_SIZE, y + FOOTING_HALF_SIZE)
    for x in (-3.1, 3.1) for y in (-6.1, -0.7)
]


class DesignRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = parse(ENGINE_PATH)

    def test_all_changed_python_is_syntactically_valid(self):
        paths = [ROOT / 'assemble_mine.py', ROOT / 'lib' / 'mine_common.py', *sorted((ROOT / 'modules').glob('*.py'))]
        for path in paths:
            with self.subTest(path=path.name):
                parse(path)

    def test_crate_clears_front_left_footing(self):
        # The two values share one tuple assignment, so read it directly to keep the check independent of Blender.
        x, y = assigned_literal(self.engine, 'add_crate', 'along_centre')
        width, depth, _ = assigned_literal(self.engine, 'add_crate', 'width')
        crate = (x - width / 2, x + width / 2, y - depth / 2, y + depth / 2)
        self.assertFalse(any(overlaps(crate, footing, margin=0.05) for footing in FOOTINGS))

    def test_leaning_planks_clear_both_front_footings(self):
        piles = assigned_literal(self.engine, 'add_leaning_planks', 'piles')
        for pile in piles:
            for along_top, foot_out, _, sideways in pile:
                x, y = along_top + sideways, -foot_out
                plank = (x - 0.108, x + 0.108, y - 0.03, y + 0.03)
                self.assertFalse(any(overlaps(plank, footing, margin=0.02) for footing in FOOTINGS),
                                 f'plank at {(x, y)} intersects a footing')

    def test_ground_offcuts_clear_front_footings(self):
        function = function_node(self.engine, 'add_leaning_planks')
        loop = next(node for node in ast.walk(function) if isinstance(node, ast.For)
                    and isinstance(node.target, ast.Tuple) and any(isinstance(item, ast.Name) and item.id == 'yaw' for item in node.target.elts))
        for along, out, yaw in ast.literal_eval(loop.iter):
            extent_x = 0.5 * abs(math.cos(yaw)) + 0.1 * abs(math.sin(yaw))
            extent_y = 0.5 * abs(math.sin(yaw)) + 0.1 * abs(math.cos(yaw))
            offcut = (along - extent_x, along + extent_x, -out - extent_y, -out + extent_y)
            self.assertFalse(any(overlaps(offcut, footing, margin=0.02) for footing in FOOTINGS),
                             f'offcut at {(along, -out)} intersects a footing')

    def test_close_coal_and_dressed_stone_have_edge_softening(self):
        source = (ROOT / 'assemble_mine.py').read_text(encoding='utf-8')
        self.assertIn("('Coal in carts', 0.009, 28.0)", source)
        self.assertIn("('Engine house stone', 0.012, 35.0)", source)
        self.assertIn("('Headframe footings', 0.018, 35.0)", source)
        self.assertIn("obj.modifiers.new('Soft worn edges', 'BEVEL')", source)

    def test_interior_practical_lights_are_in_assembled_scene(self):
        source = (ROOT / 'assemble_mine.py').read_text(encoding='utf-8')
        self.assertIn("bpy.data.lights.new(name, 'AREA')", source)
        self.assertIn("add_engine_house_interior_lights()", source)
        self.assertIn("Engine house doorway bounce", source)

    def test_physical_sky_is_default_and_painted_sky_remains_optional(self):
        source = (ROOT / 'assemble_mine.py').read_text(encoding='utf-8')
        self.assertIn("os.environ.get('MINE_SKY_MODE', 'physical')", source)
        self.assertIn("sky.sky_type = 'MULTIPLE_SCATTERING'", source)
        self.assertIn("== 'painted':", source)


if __name__ == '__main__':
    unittest.main()
