#!/usr/bin/env bash
# re-check every helper's facts folder with the snapshot of the current check_shot.py (no Blender)
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks
V=$S/verify-review; K=/home/user/work/paper-pop-up-film-kit
CHK=$K/examples/notice-corner/shot-check.json
mkdir -p $V/out
run() { # name facts check [extra]
  name=$1; facts=$2; chk=$3; shift 3
  python3 $V/check_shot.snapshot.py --check $chk --facts $facts --out $V/out/$name "$@" > /dev/null 2> $V/out/$name.err
  echo "$name exit $?"
}
for f in a-fix1 c-control-lantern-over-chair-no-lowering c-fix-lantern c-fix-middles composed-end-fix composed-end-fix-then-lantern-advice composed-end-turn-alternative d-control-camera-only d-fix f-fix f-fix2-next; do run vf-$f $S/verify-follow/$f $CHK; done
for f in h-board-further i-barrel-bottom-left i2-barrel-4m-further-up j-wide-view-75 j2-wide-view-after-fix k-lamp-post-touches-board l-drum-far-back m-lamp-post-across-notice n-camera-turned-left-2deg; do run vn-$f $S/verify-new/$f $CHK; done
for f in h-board-further k-lamp-post-touches-board l-drum-far-back m-lamp-post-across-notice; do run vn-noref-$f $S/verify-new/$f $S/verify-new/shot-check-noref.json; done
run vn-noref-composed-end $S/composed-end $S/verify-new/shot-check-noref.json
for f in m-sunk-2 m-pail-cut-bottom m-rolled m-pail-just-out; do run vc-$f $S/verify-code/$f $CHK; done
run vc-m-landscape $S/verify-code/m-landscape $S/verify-code/chk-landscape.json
run vc-nolines $S/verify-code/f-nolines $S/verify-code/chk-nolines.json
run vc-nosolo $S/verify-code/f-nosolo $CHK
run vc-tilted-ghost $S/verify-code/f-tilted-ghost $CHK
run vc-highref $S/composed-end $S/verify-code/chk-highref.json
run vc-vp-off $S/composed-end $S/verify-code/chk-vp-off.json
run vc-title-pixels $S/composed-end $S/verify-code/chk-title-pixels.json
run vc-title-empty $S/composed-end $S/verify-code/chk-title-empty.json
run vc-nosubject $S/composed-end $S/verify-code/chk-nosubject.json
run vc-allexcluded $S/composed-end $S/verify-code/chk-allexcluded.json
run vc-badpic $S/composed-end $CHK --picture $S/does-not-exist.png
run vc-warm-near $S/composed-end $CHK --picture $S/verify-code/warm-only-near-story.png
run vr-slide-right-0.14 $S/verify-reading/slide-right-0.14 $CHK
run old-picture $S/composed-end $CHK --picture $S/../composed-end.png
run ce-pic2 $S/composed-end $CHK --picture $S/../composed-end-2.png
echo ALL DONE
