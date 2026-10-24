# What this does: a script hook for the variations tests: it scales the sun's strength by args["sun"] (1 = as saved), so the whole picture gets lighter or darker.
import bpy


def apply(variation):
    factor = float(variation['args'].get('sun', 1.0))
    for light in bpy.data.lights:
        if light.type == 'SUN':
            light.energy = light.energy * factor
