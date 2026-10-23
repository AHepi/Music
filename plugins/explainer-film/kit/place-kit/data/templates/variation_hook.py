"""What this does: a TEMPLATE for a VARIATION SCRIPT HOOK, the small Python file that lets `explainer-film-place variations` try a change that is not a wear dial: a gate that leans, a tree with
more branches, boards that are wider. Copy it, rename it (hooks/gate_lean.py), change STAGE_FILE and the line marked CHANGE, and name it in the variations file:
    {"name": "lean-8", "script": "hooks/gate_lean.py", "args": {"lean_degrees": 8}, "ranges": {"lean_degrees": [0, 20]}}
Where it runs: inside Blender, on the saved finished scene, freshly opened for this variation (a hook always gets a fresh scene, and the scene is never saved). The tool calls apply(variation)
with variation = {"name": "lean-8", "args": {"lean_degrees": 8}, "set": {}}. Put the number the hook reads in "args", and its range in "ranges", so the tool can tell BEFORE drawing whether two
variations are far enough apart (without a range, two numbers count as different when they are 25 percent of the larger one apart).
The usual pattern: the hook calls YOUR OWN STAGE FILE again with other numbers. A stage file is idempotent (it forgets what it made, then makes it again), so apply(options) with
{"lean_degrees": 8} rebuilds only your part with that lean. After a hook the worker always reopens the scene, so nothing leaks into the next variation.
On a rented card only the hook file travels, so a hook that needs your stage file must find it on the card: put the stage file beside the hook in a folder you upload once (`rent upload`), or paste what
the hook needs into the hook itself, or draw this batch with --where local (tiny scenes only).
A concrete example: the hook below, with STAGE_FILE = ".../stage_lock_gate.py" and a stage file that reads options.get("lean_degrees", 0), draws the gate leaning 8 degrees for the variation lean-8.
"""
import importlib.util
import os

STAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stage_example_part.py')      # CHANGE: the stage file of the part you are trying


def apply(variation):
    """Runs inside Blender. Rebuilds the part with the variation's numbers."""
    numbers = dict(variation.get('args') or {})           # for example {"lean_degrees": 8}
    spec = importlib.util.spec_from_file_location('stage_to_try', STAGE_FILE)
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    stage.apply(numbers)                                  # the stage file reads what it needs with options.get(name, default)
