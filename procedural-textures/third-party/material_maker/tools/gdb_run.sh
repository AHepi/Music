#!/bin/bash
# Plain note: runs Material Maker under the debugger gdb to find out where it crashes. Usage: gdb_run.sh GRAPH.ptex OUT_DIR LOGFILE
B=proc-work/third-party/material_maker
export HOME=$B/home XDG_CONFIG_HOME=$B/home/.config XDG_DATA_HOME=$B/home/.local/share XDG_CACHE_HOME=$B/home/.cache VK_DRIVER_FILES=$B/lavapipe/lvp_icd_local.json VK_ICD_FILENAMES=$B/lavapipe/lvp_icd_local.json LP_NUM_THREADS=3
unset HTTPS_PROXY HTTP_PROXY https_proxy http_proxy
timeout 100 xvfb-run -a -s "-screen 0 1280x1024x24 +extension GLX +render" gdb -batch -ex "set pagination off" -ex "handle SIGUSR1 nostop noprint" -ex "handle SIGPIPE nostop noprint" -ex run -ex "bt 30" -ex "thread apply all bt 8" --args $B/app/material_maker_1_7_linux/material_maker.x86_64 --audio-driver Dummy --no-header --export-material -t Blender -o "$2" "$1" > "$3" 2>&1
