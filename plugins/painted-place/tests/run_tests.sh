#!/bin/sh
# What this does: runs every test with the Python that has bpy (the bpy module, or Blender's own Python).
# Use:  sh tests/run_tests.sh            or   BLENDER=/path/to/blender sh tests/run_tests.sh
cd "$(dirname "$0")/.." || exit 1
status=0
for test in tests/test_roles.py tests/test_measure.py tests/test_look_stage.py; do
  if [ -n "$BLENDER" ]; then "$BLENDER" -b --python "$test" 2>&1 | grep -E "PASS|Error|assert" || status=1
  else python3 "$test" 2>&1 | grep -E "PASS|Error|assert" || status=1; fi
done
exit $status
