#!/usr/bin/env bash
# What this does: the round 4 steps after the plates (scratch): the plates as JPEGs beside the film's files, film-size
# previews of every view and state, the shot checker on each with its picture and render log, the plate-camera
# outlines, the state pictures and the behind picture.
set -euo pipefail
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round4-set
KIT=/home/user/Music/austerity-explainer/film-kit
W=$KIT/assets/models/inflation-chapter-2-newcomers/works
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $KIT
step=${1:-all}
if [[ $step == all || $step == jpeg ]]; then
  for picture in $S/plates/works-*-plate.png; do
    python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=95)" "$picture" "$W/$(basename "${picture%.png}").jpg"
  done
fi
if [[ $step == all || $step == previews ]]; then
  mkdir -p $S/film-size
  DISPLAY=:96 $B -b $W/works-lane.blend --python paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py -- \
    --previews $S/film-size --preview-width 1080 --samples 12 > $S/film-size/previews.log 2>&1
fi
if [[ $step == all || $step == check ]]; then
  for pair in "w3:quiet:w3:w3-quiet" "w1:quiet:w1:w1-quiet" "w1:working:w1:w1-working" "w2:quiet:w2:w2-quiet" "w2:slowed:w2-slowed:w2-slowed" "w4:w4:w4:w4-w4"; do
    IFS=: read view state check picture <<< "$pair"
    BLEND=$W/works-lane.blend RENDER_LOG=$S/film-size/previews.log paper-film/tools/check-shot.sh paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py \
      examples/inflation-chapter-2-newcomers/works-$check-shot-check.json $S/final/$picture $S/film-size/$picture.png -- --view $view --state $state > $S/final/$picture.out 2>&1 || true
    echo "$picture: $(sed -n 3p $S/final/$picture/report.md)"
  done
fi
if [[ $step == all || $step == platefacts ]]; then
  BLEND=$W/works-lane.blend paper-film/tools/check-shot.sh paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py \
    examples/inflation-chapter-2-newcomers/works-w1-shot-check.json $S/state/w1-plate-facts -- --view w1 --state quiet --camera-at -3.7,9.0,1.835 --yaw 0 --fov 64.4 > $S/state/w1-plate-facts.out 2>&1 || true
  BLEND=$W/works-lane.blend paper-film/tools/check-shot.sh paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py \
    examples/inflation-chapter-2-newcomers/works-w2-slowed-shot-check.json $S/state/w2-plate-facts -- --view w2 --state slowed --camera-at 3.7,9.0,1.835 --yaw 0 --fov 64.4 > $S/state/w2-plate-facts.out 2>&1 || true
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
