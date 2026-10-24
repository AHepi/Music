#!/usr/bin/env bash
# What this does: the round 5 steps after the plates (scratch): the plates as JPEGs beside the film's files, the
# plate-camera outlines of the men (the shot checker's per-prop pictures at each plate camera), the state pictures and
# the behind picture. The plate cameras are read from works-shot.json (written by the export).
# Use: after_plates.sh [all|jpeg|platefacts|state]
set -euo pipefail
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round5-set
KIT=/home/user/Music/austerity-explainer/film-kit
W=$KIT/assets/models/inflation-chapter-2-newcomers/works
cd $KIT
step=${1:-all}
if [[ $step == all || $step == jpeg ]]; then
  for picture in $S/plates/works-*-plate.png; do
    python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=95)" "$picture" "$W/$(basename "${picture%.png}").jpg"
  done
fi
spot() { python3 -c "import json,sys; v=json.load(open('$W/works-shot.json'))['views'][sys.argv[1]]['plate']; print(','.join(str(x) for x in v))" "$1"; }
if [[ $step == all || $step == platefacts ]]; then
  mkdir -p $S/state
  BLEND=$W/works-lane.blend paper-film/tools/check-shot.sh paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py \
    examples/inflation-chapter-2-newcomers/works-w1-shot-check.json $S/state/w1-plate-facts -- --view w1 --state quiet --camera-at $(spot w1) --yaw 0 --fov 64.4 > $S/state/w1-plate-facts.out 2>&1 || true
  BLEND=$W/works-lane.blend paper-film/tools/check-shot.sh paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py \
    examples/inflation-chapter-2-newcomers/works-w2-slowed-shot-check.json $S/state/w2-plate-facts -- --view w2 --state slowed --camera-at $(spot w2) --yaw 0 --fov 64.4 > $S/state/w2-plate-facts.out 2>&1 || true
fi
if [[ $step == all || $step == state ]]; then
  T=paper-film/tools/make_state_picture.py
  MEN1=("man 1" "man 2" "man 3" "man 4" "man 5" "man 6" "man 7")
  MEN2=("man 1" "man 2" "man 3" "man 4" "man 5" "man 6" "man 7" "man 8")
  python3 -I $T $W/works-w1-plate.jpg $W/works-w1-men-gone-plate.jpg $W/works-w1-plate.jpg $W/works-w1-men-gone-plate.jpg \
    $W/works-w1-men-gone-state.png $W/works-w1-men-gone-mask.png --outlines $S/state/w1-plate-facts/facts "${MEN1[@]}" --look $S/state/w1-men-gone-look.jpg > $S/state/w1-men-gone.log 2>&1
  python3 -I $T $W/works-w1-plate.jpg $W/works-w1-working-plate.jpg $W/works-w1-plate.jpg $W/works-w1-working-plate.jpg \
    $W/works-w1-working-state.png $W/works-w1-working-mask.png --outlines $S/state/w1-plate-facts/facts "${MEN1[@]}" --look $S/state/w1-working-look.jpg > $S/state/w1-working.log 2>&1
  python3 -I $T $W/works-w1-plate.jpg $W/works-w1-behind-plate.jpg $W/works-w1-plate.jpg $W/works-w1-behind-plate.jpg \
    $W/works-w1-behind.png $W/works-w1-behind-mask.png --outlines $S/state/w1-plate-facts/facts "${MEN1[@]}" --look $S/state/w1-behind-look.jpg > $S/state/w1-behind.log 2>&1
  python3 -I $T $W/works-w2-plate.jpg $W/works-w2-slowed-plate.jpg $W/works-w2-plate.jpg $W/works-w2-slowed-plate.jpg \
    $W/works-w2-slowed-state.png $W/works-w2-slowed-mask.png --outlines $S/state/w2-plate-facts/facts "${MEN2[@]}" --look $S/state/w2-slowed-look.jpg > $S/state/w2-slowed.log 2>&1
  for f in w1-men-gone w1-working w1-behind w2-slowed; do echo "$f: $(grep -i "covers\|largest\|mask" $S/state/$f.log | tail -2 | tr '\n' ' ')"; done
fi
