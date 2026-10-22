"""The weathering kit's core: settings, roles, dials, seeds, hook, adapters, chain, public API (kit.py).
Everything here is generic: a set's names, numbers and looks live in sets/<set>.json and presets/*.json, never in code."""
import os
import sys

KIT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.dont_write_bytecode = True
