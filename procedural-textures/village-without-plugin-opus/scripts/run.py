"""Entry helpers executed inside Blender through the MCP tool.

Usage from the MCP execute tool:
    exec(open(SRC + '/run.py').read()); result = step('ground')
"""
import sys
import importlib
import time

SRC = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-control-opus/src"
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def _reload(*names):
    mods = []
    for n in names:
        if n in sys.modules:
            mods.append(importlib.reload(sys.modules[n]))
        else:
            mods.append(importlib.import_module(n))
    return mods
