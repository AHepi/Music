#!/usr/bin/env bash
# What this does: the round 6 steps after the plates (scratch): the plates as JPEGs beside the film's files, the
# plate-camera outlines (the shot checker's per-prop pictures at each plate camera), the state pictures, the behind
# picture and page 12's windows-only picture. The plate cameras are read from works-shot.json.
# Use: after_plates.sh [all|jpeg|platefacts|state]
set -uo pipefail
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round6-set
KIT=/home/user/Music/austerity-explainer/film-kit
W=$KIT/assets/models/inflation-chapter-2-newcomers/works
A=paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py
E=examples/inflation-chapter-2-newcomers
cd $KIT
step=${1:-all}
if [[ $step == all || $step == jpeg ]]; then
  for picture in $S/plates/works-*-plate.png; do
    python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=95)" "$picture" "$W/$(basename "${picture%.png}").jpg"
  done
fi
spot() { python3 -c "import json,sys; v=json.load(open('$W/works-shot.json'))['views'][sys.argv[1]]['plate']; print(','.join(str(x) for x in v))" "$1"; }
facts() {   # name check view state
  BLEND=$W/works-lane.blend paper-film/tools/check-shot.sh $A $2 $S/state/$1 -- --view $3 --state $4 --camera-at $(spot $3) --yaw 0 --fov 64.4 > $S/state/$1.out 2>&1 || echo "facts $1 failed"
}
if [[ $step == all || $step == platefacts ]]; then
  mkdir -p $S/state
  facts w1-plate-facts $E/works-w1-shot-check.json w1 quiet
  facts w2-plate-facts $E/works-w2-slowed-shot-check.json w2 slowed
  facts w3-plate-facts $E/works-w3-shot-check.json w3 quiet
  facts w2-windows-facts $S/tools/w2-windows-check.json w2 slowed
fi
if [[ $step == all || $step == state ]]; then
  T=paper-film/tools/make_state_picture.py
  MEN1=("man 1" "man 2" "man 3" "man 4" "man 5" "man 6" "man 7")
  MEN2=("man 1" "man 2" "man 3" "man 4" "man 5" "man 6" "man 7" "man 8")
  make() {   # main helper out mask facts look log men...
    local main=$1 helper=$2 out=$3 mask=$4 facts=$5 look=$6 log=$7; shift 7
    python3 -I $T $W/$main $W/$helper $W/$main $W/$helper $W/$out $W/$mask --outlines $S/state/$facts/facts "$@" --look $S/state/$look > $S/state/$log 2>&1 || echo "state $out failed"
  }
  make works-w1-plate.jpg works-w1-men-gone-plate.jpg works-w1-men-gone-state.png works-w1-men-gone-mask.png w1-plate-facts w1-men-gone-look.jpg w1-men-gone.log "${MEN1[@]}"
  make works-w1-plate.jpg works-w1-working-plate.jpg works-w1-working-state.png works-w1-working-mask.png w1-plate-facts w1-working-look.jpg w1-working.log "${MEN1[@]}"
  make works-w1-plate.jpg works-w1-behind-plate.jpg works-w1-behind.png works-w1-behind-mask.png w1-plate-facts w1-behind-look.jpg w1-behind.log "${MEN1[@]}"
  make works-w2-plate.jpg works-w2-slowed-plate.jpg works-w2-slowed-state.png works-w2-slowed-mask.png w2-plate-facts w2-slowed-look.jpg w2-slowed.log "${MEN2[@]}"
  make works-w3-plate.jpg works-w3-working-plate.jpg works-w3-working-state.png works-w3-working-mask.png w3-plate-facts w3-working-look.jpg w3-working.log "${MEN1[@]}"
  # page 12's windows-only picture: the windows' change only, kept clear of the men and the lathe man (round 5 W4 helper's way)
  python3 -I $S/tools/windows_mask.py $W/works-w2-plate.jpg $W/works-w2-slowed-plate.jpg $S/state/w2-windows-facts/facts $S/state/windows-change.png $S/state/windows-change-look.jpg > $S/state/windows-mask.log 2>&1
  python3 -I $T $W/works-w2-plate.jpg $W/works-w2-slowed-plate.jpg $W/works-w2-plate.jpg $W/works-w2-slowed-plate.jpg \
    $W/works-w2-slowed-windows-state.png $W/works-w2-slowed-windows-mask.png --mask $S/state/windows-change.png --threshold 999 --faint 999 \
    --look $S/state/w2-slowed-windows-look.jpg > $S/state/w2-slowed-windows.log 2>&1 || echo "windows picture failed"
  for f in w1-men-gone w1-working w1-behind w2-slowed w3-working w2-slowed-windows; do echo "$f: $(grep "used:\|largest difference" $S/state/$f.log | tr '\n' ' ')"; done
fi
