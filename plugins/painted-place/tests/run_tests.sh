#!/bin/sh
# What this does: runs every test of the brief kit and its store with the Python that has the bpy module, shows each
# test's PASS lines or its error, and fails if any test fails (by the test's own exit code, not by what it prints).
# Use:  sh tests/run_tests.sh          (from the plugin folder or anywhere)
cd "$(dirname "$0")/.." || exit 1
status=0
for test in tests/test_measure.py tests/test_store_materials.py tests/test_store_photographed.py tests/test_store_parts.py tests/test_store_tools.py tests/test_store_ground.py tests/test_store_farm_tools.py tests/test_store_street_ground.py tests/test_store_street_fronts.py tests/test_store_curved_road.py tests/test_store_wall.py tests/test_store_frames.py tests/test_copy_case.py tests/test_store_rules.py; do
  output=$(python3 "$test" 2>&1); code=$?
  if [ "$code" -eq 0 ] && echo "$output" | grep -q "^PASS"; then
    echo "$output" | grep -E "^(PASS|note)"
  else
    echo "FAIL $test (exit $code)"
    echo "$output" | grep -E "Error|assert|Traceback|^note" | tail -6
    status=1
  fi
done
if [ "$status" -eq 0 ]; then echo "ALL PASSED"; else echo "SOME FAILED"; fi
exit $status
