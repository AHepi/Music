#!/bin/bash
# verifier: bake descriptions in a fresh Blender process each, into verify/bake_<name>
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
for name in "$@"; do
  /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python ../generator/mud_generator.py -- desc/$name.json bake_$name --size 1254 --samples 8 > bake_$name.log 2>&1
  echo "done $name $(date +%T)" >> bake_progress.log
done
echo ALL_DONE >> bake_progress.log
