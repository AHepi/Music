#!/bin/sh
# What this does: runs every test with the Python that has bpy (the bpy module, or Blender's own Python), shows each
# test's PASS lines or its error, and fails if any test fails (by the test's own exit code, not by what it prints).
# Use:  sh tests/run_tests.sh            or   BLENDER=/path/to/blender sh tests/run_tests.sh
cd "$(dirname "$0")/.." || exit 1
status=0
for test in tests/test_roles.py tests/test_measure.py tests/test_look_stage.py tests/test_dressing.py tests/test_shore_and_timber.py tests/test_scans.py; do
  if [ -n "$BLENDER" ]; then
    output=$("$BLENDER" -b --python-exit-code 1 --python "$test" 2>&1); code=$?
  else
    output=$(python3 "$test" 2>&1); code=$?
  fi
  if [ "$code" -eq 0 ] && echo "$output" | grep -q "PASS"; then
    echo "$output" | grep "PASS"
  else
    echo "FAIL $test (exit $code)"
    echo "$output" | grep -E "Error|assert|Traceback" | tail -5
    status=1
  fi
done
exit $status
