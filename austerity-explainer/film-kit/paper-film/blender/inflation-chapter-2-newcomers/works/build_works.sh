#!/usr/bin/env bash
# What this does: builds "The Works" for chapter 2 (plan 34, part 1 "A. The Works") in order, into the Works' own
# folder (assets/models/inflation-chapter-2-newcomers/works), never beside the pit village's notice corner:
#   1. the lane: pit-village/build_street.py with the Works' settings (a short level lane, 6 m carriageway, 2.2 m
#      pavements, four cottages a side, no colliery) as works-lane.blend, the base the assembly and the shot checker
#      open. The lane's own .glb and camera file are removed again: the Works' export below holds the lane.
#   2. the assembly and the film's files: assemble_works.py --export (the set in parts, the own surfaces, the four view
#      cameras and works-shot.json)
#   3. when asked (--plates FOLDER): the plates (assemble_works.py's PLATES) as PNG into FOLDER, then each as a JPEG (quality 95) beside the
#      film's files; the render log is kept as FOLDER/plates.log (look in it for "Shadow buffer full" and "Could not
#      allocate shadow atlas")
# The factories and the far town are built before this by build_factories.py and build_far_town.py.
# Use (from the kit's top folder; a virtual screen is needed for the plates: Xvfb :96 -screen 0 1920x1080x24 &):
#   paper-film/blender/inflation-chapter-2-newcomers/works/build_works.sh [--replace] [--plates FOLDER]
# --replace lets it write over a lane that is already there (without it, it stops rather than overwrite).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
kit=$(cd "$here/../../../.." && pwd)
works="$kit/assets/models/inflation-chapter-2-newcomers/works"
BLENDER=${BLENDER:-/home/user/work/blender-app/blender-5.2.2-linux-x64/blender}
replace=""; plates=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --replace) replace="--replace"; shift ;;
    --plates) plates=$(cd "$(dirname "$2")" && pwd)/$(basename "$2"); shift 2 ;;
    *) echo "build_works.sh: unknown setting $1"; exit 1 ;;
  esac
done
# 1. the lane (the settings are the same as LANE_SETTINGS in assemble_works.py)
"$BLENDER" -b --python "$kit/paper-film/blender/pit-village/build_street.py" -- --out "$works" --name works-lane $replace \
  --colliery off --carriageway 6 --pavement 2.2 --length 22 --behind 0 --slope 0 --cottages 4
rm -f "$works/works-lane.glb" "$works/works-lane-camera.json"
# 2. the assembly and the film's files
DISPLAY=${DISPLAY:-:96} "$BLENDER" -b "$works/works-lane.blend" --python "$here/assemble_works.py" -- --export
# 3. the plates
if [[ -n $plates ]]; then
  mkdir -p "$plates"
  DISPLAY=${DISPLAY:-:96} "$BLENDER" -b "$works/works-lane.blend" --python "$here/assemble_works.py" -- --plates "$plates" > "$plates/plates.log" 2>&1
  grep -n "Shadow buffer full\|Could not allocate shadow atlas" "$plates/plates.log" && echo "build_works.sh: shadow faults in the plates' log" || true
  for picture in "$plates"/works-*-plate.png; do
    python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=95)" \
      "$picture" "$works/$(basename "${picture%.png}").jpg"
  done
fi
echo "build_works.sh: done ($works)"
