#!/usr/bin/env bash
# What this does: checks a shot's composition in one go (log 31). It dresses the scene with the shot's
# own script, measures it in Blender (shot_facts.py: flat colour pictures of every named prop, the exact
# camera and where the street's lines meet; about 15 seconds), then writes the report and the marked
# picture (check_shot.py): what breaks the composing rules, how far it is from the reference picture,
# and what to change, in metres.
# Use (from the kit's top folder):
#   paper-film/tools/check-shot.sh SHOT_SCRIPT CHECK_FILE OUT_FOLDER [FINISHED_PICTURE] [-- extra Blender options]
# For example:
#   BLEND=assets/models/pit-village/street.blend paper-film/tools/check-shot.sh paper-film/blender/pit-village/assemble_notice_corner.py \
#       examples/notice-corner/shot-check.json paper-film/out/check-corner composed.png -- --view end
# A finished picture (an EEVEE still or a filmed frame of the same view) adds the light rules; give the log
# Blender wrote while rendering it as RENDER_LOG=... to catch render faults (false shadows when it ran out
# of shadow memory).
# Extra Blender options after "--" go to the shot script and shot_facts.py, for example
#   --view end, or a trial camera: --camera-at 3.0,17.8,3.2 --yaw 6.9 --fov 60.4
# Needs Blender and a virtual screen: BLENDER (the Blender program) and BLENDER_DISPLAY (default :96, the virtual
# screen started with "Xvfb :96 -screen 0 1920x1080x24 &") come from the environment, or else from the kit's
# machine-settings.env, which explainer-film-setup writes; if neither names Blender, the blender on the PATH is used.
# BLEND is the scene file the shot script dresses, and must be given: for the notice corner
#   BLEND=assets/models/pit-village/street.blend paper-film/tools/check-shot.sh ...
# or BLEND=none when the shot script builds its own scene from an empty one.
# (Plugin kit: the film kit's copy defaults BLENDER to one machine's folder and BLEND to the pit village street.)
set -euo pipefail
shot_script=$1; check_file=$2; out=$3; shift 3
picture=""
if [[ $# -gt 0 && $1 != "--" ]]; then picture=$1; shift; fi
[[ $# -gt 0 && $1 == "--" ]] && shift
here=$(cd "$(dirname "$0")" && pwd)
kit=$(cd "$here/../.." && pwd)
# this machine's settings (written by explainer-film-setup); a setting already in the environment wins
if [[ -f "$kit/machine-settings.env" ]]; then
  while IFS='=' read -r key value; do
    [[ $key =~ ^[A-Z_][A-Z0-9_]*$ ]] || continue
    [[ -n ${!key:-} ]] || export "$key=$value"
  done < "$kit/machine-settings.env"
fi
BLENDER=${BLENDER:-$(command -v blender || true)}
[[ -n $BLENDER && -x $BLENDER ]] || { echo "check-shot: Blender not found: set BLENDER=/path/to/blender (or run explainer-film-setup)"; exit 2; }
[[ -n ${BLEND:-} ]] || { echo "check-shot: say which scene file the shot script dresses: BLEND=path/to/place.blend (BLEND=none if it builds its own scene)"; exit 2; }
blend_file=()
if [[ $BLEND != none ]]; then
  [[ -f $BLEND ]] || { echo "check-shot: no scene file at BLEND=$BLEND"; exit 2; }
  blend_file=("$BLEND")
fi
mkdir -p "$out"
DISPLAY=${BLENDER_DISPLAY:-${DISPLAY:-:96}} "$BLENDER" -b ${blend_file[@]+"${blend_file[@]}"} \
  --python "$shot_script" --python "$kit/paper-film/blender/shot_facts.py" -- \
  --check "$check_file" --facts "$out/facts" "$@" > "$out/blender.log" 2>&1 \
  || { echo "check-shot: Blender failed; see $out/blender.log"; exit 1; }
python3 "$here/check_shot.py" --check "$check_file" --facts "$out/facts" ${picture:+--picture "$picture"} ${RENDER_LOG:+--render-log "$RENDER_LOG"} \
  --out "$out" --title "$(basename "$out")"
echo "check-shot: report $out/report.md, marked picture $out/marked.jpg"
