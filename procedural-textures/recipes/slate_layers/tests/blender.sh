#!/bin/bash
# What this does: runs Blender headless on 2 threads with a script (the way every test here is started).
# Use: tests/blender.sh SCRIPT.py -- ARGS...
exec /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python "$@"
