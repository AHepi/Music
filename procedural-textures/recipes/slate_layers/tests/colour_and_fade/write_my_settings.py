# What this file does (plain words): writes the settings of COLOUR AND FADE (every control with its default value, named
# 'colour_and_fade.<control>') into settings_colour_and_fade.json, in the same form as recipe/settings.json, so the person who finishes the
# recipe can merge them, and so lib/description_audit.py can check that they are only a short list of numbers (not a picture).
# Run inside Blender: tests/blender.sh tests/colour_and_fade/write_my_settings.py
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'layers')))
import layer_interface as li  # noqa: E402
import colour_and_fade  # noqa: E402

settings = {}
for control in li.common_controls(colour_and_fade.DEFAULT_SEED) + list(colour_and_fade.CONTROLS):
    settings[li.setting_name(colour_and_fade.LAYER_KEY, control.key)] = control.default
with open(os.path.join(HERE, 'settings_colour_and_fade.json'), 'w') as handle:
    json.dump(settings, handle, indent=1)
print('wrote', len(settings), 'settings')
