#!/bin/bash
# What this does (plain words): bakes ONE description file into texture pictures with Blender in the background (no window), CPU only, 2 threads.
# Use: bake_one.sh DESCRIPTION.json OUT_FOLDER [size] [samples]
HERE="$(cd "$(dirname "$0")" && pwd)"
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python "$HERE/mud_generator.py" -- "$1" "$2" --size "${3:-1254}" --samples "${4:-8}"
