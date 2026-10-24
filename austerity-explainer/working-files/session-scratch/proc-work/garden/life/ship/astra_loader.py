# What this does: loads the Astra Painted Workbench add-on straight from its unpacked folder (no installing), so a
# Blender script can call its API. Use: from astra_loader import load_astra; astra = load_astra(FOLDER)
import importlib.util, sys

def load_astra(folder):
    name = 'astra_painted_workbench'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, folder + '/__init__.py', submodule_search_locations=[folder])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    import astra_painted_workbench.runtime.api as api
    return api


def apply_blender_52_shim(api):
    """The add-on was qualified on Blender 5.1.x and writes geometry-nodes modifier inputs with mod[identifier] = value.
    Blender 5.2 moved them to mod.properties.inputs.<identifier>.value. This replaces only that one writer for the roof
    and stone builders; nothing in the add-on's files is edited."""
    import bpy
    from astra_painted_workbench.runtime.vendor.courtyard_tools import api as ct

    def write_controls(obj, values):
        mod = ct._modifier(obj)
        sockets = {s.name: s.identifier for s in mod.node_group.interface.items_tree
                   if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
        for name, value in values.items():
            getattr(mod.properties.inputs, sockets[name]).value = value
        obj.update_tag(refresh={'DATA'})

    if 'properties' not in bpy.types.NodesModifier.bl_rna.properties:
        return False          # Blender 5.1 and earlier: the add-on's own writer works
    ct._write_controls = write_controls
    return True
