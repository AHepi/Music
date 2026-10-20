#!/bin/bash
# verifier: second bake queue (variation tile, half-tile shift, 512 resolution, area 2508) - fresh Blender process each, no bytecode written
cd "$(dirname "$0")"
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
run() { # description out size extra...
  d=$1; o=$2; s=$3; shift 3
  $B -b --disable-autoexec -t 2 --python run_gen.py -- $d $o --size $s --samples 8 "$@" > $o.log 2>&1
  echo "done $o $(date +%T)" >> bake2_progress.log
}
rm -f bake2_progress.log
run resampled/description_103.json var_103 1254
run resampled/description_101.json var_101 1254
run resampled/description_101.json var_101_shift 1254 --shift 0.5 0.5
run resampled/description_101.json var_101_512 512
run resampled/description_area_2508.json area_2508 2508
echo ALL_DONE >> bake2_progress.log
