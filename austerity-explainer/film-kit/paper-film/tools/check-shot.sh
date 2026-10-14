#!/usr/bin/env bash
# What this does: checks a shot's composition in one go (log 31). It dresses the scene with the shot's
# own script, measures it in Blender (shot_facts.py: flat colour pictures of every named prop, the exact
# camera and where the street's lines meet; about 15 seconds), then writes the report and the marked
# picture (check_shot.py): what breaks the composing rules, how far it is from the reference picture,
# and what to change, in metres.
# Use (from the kit's top folder):
#   paper-film/tools/check-shot.sh SHOT_SCRIPT CHECK_FILE OUT_FOLDER [FINISHED_PICTURE] [-- extra Blender options]
# For example:
#   paper-film/tools/check-shot.sh paper-film/blender/pit-village/assemble_notice_corner.py \
#       examples/notice-corner/shot-check.json /tmp/check-corner composed.png -- --view end
# A finished picture (an EEVEE still or a filmed frame of the same view) adds the light rules; give the log
# Blender wrote while rendering it as RENDER_LOG=... to catch render faults (false shadows when it ran out
# of shadow memory).
# Extra Blender options after "--" go to the shot script and shot_facts.py, for example
#   --view end, or a trial camera: --camera-at 3.0,17.8,3.2 --yaw 6.9 --fov 60.4
# Needs Blender (BLENDER, default the kit's usual place) and a virtual screen (DISPLAY, default :96).
# The scene file the shot script dresses is BLEND (default the pit village street).
set -euo pipefail
shot_script=$1; check_file=$2; out=$3; shift 3
picture=""
if [[ $# -gt 0 && $1 != "--" ]]; then picture=$1; shift; fi
[[ $# -gt 0 && $1 == "--" ]] && shift
BLENDER=${BLENDER:-/home/user/work/blender-app/blender-5.2.2-linux-x64/blender}
here=$(cd "$(dirname "$0")" && pwd)
kit=$(cd "$here/../.." && pwd)
mkdir -p "$out"
BLEND=${BLEND:-$kit/assets/models/pit-village/street.blend}
DISPLAY=${DISPLAY:-:96} "$BLENDER" -b "$BLEND" \
  --python "$shot_script" --python "$kit/paper-film/blender/shot_facts.py" -- \
  --check "$check_file" --facts "$out/facts" "$@" > "$out/blender.log" 2>&1 \
  || { echo "check-shot: Blender failed; see $out/blender.log"; exit 1; }
python3 "$here/check_shot.py" --check "$check_file" --facts "$out/facts" ${picture:+--picture "$picture"} ${RENDER_LOG:+--render-log "$RENDER_LOG"} \
  --out "$out" --title "$(basename "$out")"
echo "check-shot: report $out/report.md, marked picture $out/marked.jpg"
