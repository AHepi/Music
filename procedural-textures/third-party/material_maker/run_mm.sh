#!/bin/bash
# Plain note: runs Material Maker 1.7 (Godot) headless on this machine inside a virtual screen (Xvfb),
# using the software Vulkan driver "lavapipe" (so no graphics card is needed). It keeps all of Material Maker's
# settings inside the sandbox folder (fake HOME) and unsets the network proxy so the program cannot reach the internet.
# Usage: run_mm.sh <arguments for material_maker, e.g. --export-material -t Blender -o OUTDIR file.ptex>
B=proc-work/third-party/material_maker
export HOME=$B/home XDG_CONFIG_HOME=$B/home/.config XDG_DATA_HOME=$B/home/.local/share XDG_CACHE_HOME=$B/home/.cache
export VK_DRIVER_FILES=$B/lavapipe/lvp_icd_local.json VK_ICD_FILENAMES=$B/lavapipe/lvp_icd_local.json
export LP_NUM_THREADS=${LP_NUM_THREADS:-3}
unset HTTPS_PROXY HTTP_PROXY https_proxy http_proxy
exec xvfb-run -a -s "-screen 0 1280x1024x24 +extension GLX +render" $B/app/material_maker_1_7_linux/material_maker.x86_64 --audio-driver Dummy --no-header $MM_EXTRA_ARGS "$@"
