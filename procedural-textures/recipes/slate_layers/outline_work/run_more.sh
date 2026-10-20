#!/bin/bash
# runs the last slow pictures one after the other: the five looks, the resolution check and the 2 x 2 area
cd "$(dirname "$0")"
( time python3 -I looks.py ) > logs/looks.log 2>&1
( time python3 -I resolution_check.py ) > logs/resolution.log 2>&1
( time python3 -I two_by_two.py ) > logs/two_by_two.log 2>&1
echo DONE > logs/run_more_done.txt
