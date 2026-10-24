#!/usr/bin/env bash
# What this does: re-runs check_shot.py (current version) on every facts folder in verify-new, and the good frame without a picture.
set -u
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks
V=$S/verify-new
cd /home/user/work/paper-pop-up-film-kit
md5sum paper-film/tools/check_shot.py
python3 paper-film/tools/check_shot.py --check examples/notice-corner/shot-check.json --facts $S/composed-end --out $V/composed-end-nopicture-report > /dev/null
for n in h-board-further i-barrel-bottom-left i2-barrel-4m-further-up j-wide-view-75 j2-wide-view-after-fix k-lamp-post-touches-board l-drum-far-back m-lamp-post-across-notice n-camera-turned-left-2deg; do
  python3 paper-film/tools/check_shot.py --check examples/notice-corner/shot-check.json --facts $V/$n --out $V/$n-report > /dev/null 2> $V/$n-report.err
  echo "$n: $(sed -n 3p $V/$n-report/report.md | cut -d, -f1) | first: $(sed -n '/## Fix first/{n;n;p}' $V/$n-report/report.md | cut -c1-140)"
done
md5sum paper-film/tools/check_shot.py
