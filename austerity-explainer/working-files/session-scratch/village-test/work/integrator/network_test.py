# What this does: asks, from inside Blender's own Python on a rented card, whether the card can reach the free Poly Haven file list
# (the plugin's own download function, with its own agent name). Prints one line.
import sys
sys.path.insert(0, sys.argv[-1])
from place_kit.surfaces import scans
try:
    files = scans.polyhaven_file_list('brown_mud', timeout=20)
    print('NETWORK_OK', list(files)[:3])
except Exception as problem:
    print('NETWORK_FAILED', repr(problem)[:200])
