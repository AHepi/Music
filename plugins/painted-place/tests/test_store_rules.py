"""
What this file does: checks the store's one rule, that nothing in it places itself: no part or tool reads the camera,
surveys the scene, or looks objects up by name to decide where things go; tools work only on what the caller passes.
It reads the code itself (the parsed Python), not its comments; only command lines (names the user types) and the
loader's preparing calls are exempt, and the check is first tested on snippets it must catch. It also checks that Store.md's catalogue is up to date
with the parts', tools' and materials' own descriptions.
    python3 tests/test_store_rules.py
"""
import ast
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import STORE, TOOLS, check  # noqa: E402

SKIP_FILES = {'card.py', 'catalogue.py'}       # they make their own scenes and cameras to draw the store's cards
SKIP_FUNCTIONS = {'main', 'prepare_for_render', 'fit_stone_pictures', 'names', '_merge_copies'}   # command lines (names the user types) and the loader's own book-keeping


class Offences(ast.NodeVisitor):
    """Finds the ways code could look round the scene to decide where things go."""

    def __init__(self):
        self.found = []
        self.function = []

    def visit_FunctionDef(self, node):
        self.function.append(node.name)
        self.generic_visit(node)
        self.function.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def skipping(self):
        return any(name in SKIP_FUNCTIONS for name in self.function)

    def note(self, node, what):
        if not self.skipping():
            self.found.append('%s (line %d)' % (what, node.lineno))

    @staticmethod
    def is_objects_list(node):
        """bpy.data.objects, scene.objects, view_layer.objects, anything.selected_objects / visible_objects."""
        if isinstance(node, ast.Attribute):
            if node.attr in ('selected_objects', 'visible_objects', 'selectable_objects'):
                return True
            if node.attr == 'objects':
                holder = node.value
                name = holder.attr if isinstance(holder, ast.Attribute) else (holder.id if isinstance(holder, ast.Name) else '')
                return name in ('data', 'scene', 'view_layer')
        return False

    def visit_Attribute(self, node):
        if node.attr == 'camera':
            self.note(node, 'reads a camera')
        if node.attr in ('selected_objects', 'visible_objects', 'selectable_objects'):
            self.note(node, 'reads the selection')
        if node.attr == 'objects' and self.is_objects_list(node):
            holder = node.value
            name = holder.attr if isinstance(holder, ast.Attribute) else getattr(holder, 'id', '')
            if name in ('scene', 'view_layer'):
                self.note(node, 'walks every object in the scene')
        self.generic_visit(node)

    def visit_For(self, node):
        if self.is_objects_list(node.iter):
            self.note(node, 'loops over every object')
        self.generic_visit(node)

    def visit_comprehension(self, node):
        if self.is_objects_list(node.iter):
            self.note(node.iter, 'loops over every object')
        self.generic_visit(node)

    def visit_Call(self, node):
        function = node.func
        if isinstance(function, ast.Name) and function.id == 'getattr' and len(node.args) > 1 \
                and isinstance(node.args[1], ast.Constant) and node.args[1].value == 'camera':
            self.note(node, 'reads a camera')
        if isinstance(function, ast.Attribute) and function.attr == 'get' and self.is_objects_list(function.value):
            self.note(node, 'looks an object up by name')
        self.generic_visit(node)

    def visit_Subscript(self, node):
        if self.is_objects_list(node.value) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            self.note(node, 'looks an object up by name')
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if 'survey' in alias.name or 'apply_by_role' in alias.name or alias.name.startswith('lay_details'):
                self.note(node, 'imports the old dressing')

    visit_ImportFrom = visit_Import


def offences(path):
    finder = Offences()
    finder.visit(ast.parse(open(path, encoding='utf-8').read(), filename=path))
    return finder.found


def self_check():
    """The checker must catch each of these (a test of the test)."""
    caught = 0
    snippets = ['for o in bpy.data.objects: pass', "wall = bpy.data.objects.get('Wall')", "wall = bpy.data.objects['Wall']",
                'things = [o for o in scene.objects]', 'x = bpy.context.view_layer.objects', 'x = bpy.context.selected_objects',
                "c = getattr(scene, 'camera')", 'c = scene.camera', 'import survey']
    for snippet in snippets:
        finder = Offences()
        finder.visit(ast.parse(snippet))
        check(finder.found, 'the rule check misses: %s' % snippet)
        caught += 1
    finder = Offences()
    finder.visit(ast.parse("obj = bpy.data.objects.new('boards', mesh)\ncollection.objects.link(obj)"))
    check(not finder.found, 'the rule check flags making a new object: %s' % finder.found)
    return caught


def main():
    print('PASS the rule check catches every way of looking round the scene it is given (%d cases), and not making things' % self_check())
    checked = 0
    for folder in (TOOLS, os.path.join(STORE, 'parts', 'src')):
        for name in sorted(os.listdir(folder)):
            if not name.endswith('.py') or name in SKIP_FILES:
                continue
            problems = offences(os.path.join(folder, name))
            check(not problems, '%s: %s' % (name, '; '.join(problems)))
            checked += 1
    print('PASS no part or tool reads the camera, surveys the scene or walks its objects (%d files)' % checked)
    result = subprocess.run([sys.executable, os.path.join(TOOLS, 'catalogue.py'), '--check'], capture_output=True, text=True, timeout=600)
    check(result.returncode == 0, "Store.md's catalogue is out of date: run python3 store/tools/catalogue.py\n" + result.stdout[-400:] + result.stderr[-400:])
    print("PASS Store.md's catalogue matches the store")
    print('PASS test_store_rules')


if __name__ == '__main__':
    main()
