#!/bin/bash
# What this does (plain words): runs all the slow checks of the OUTLINE AND SHADOW layer one after the other (so the shared computer is not
# overloaded): the half-tile test, the independence test, the debug views, the before/after pictures, the sweep strips and the timing.
# Use: bash run_all.sh            Logs go to logs/.
cd "$(dirname "$0")"
while pgrep -f "bake_harness.py.*stack_bake_1254_layer_off" > /dev/null; do sleep 15; done
( time python3 -I half_tile_test.py 384 ../tests/outline_half_tile ) > logs/half_tile.log 2>&1
( time python3 -I independence_test.py 384 ../tests/outline_independence ) > logs/independence.log 2>&1
( time python3 -I debug_views.py 768 ) > logs/debug_views.log 2>&1
( time python3 -I before_after.py 1254 500 ) > logs/before_after.log 2>&1
( time python3 -I make_sweeps.py ) > logs/sweeps.log 2>&1
( time python3 -I time_it.py 768 ) > logs/time_it.log 2>&1
echo ALL DONE > logs/run_all_done.txt
