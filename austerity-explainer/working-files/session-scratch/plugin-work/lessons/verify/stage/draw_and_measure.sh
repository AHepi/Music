#!/bin/bash
# What this does: the verify step's own tiny check of the stage toe. It draws, once each, the lockout test at 5 s with the
# plugin's NEW stage and look (toe 1, vignette 0.25), with the new stage but toe 0 (vignette 0.25), and with the OLD stage and look
# (from git HEAD: no toe, vignette 0.3); and the graphics test at 3 s with the old and the new stage. Then it measures the share of
# near-black dots (all three channels under 8 of 255) and the mean brightness of the bottom third, and compares the two graphics
# test stills dot for dot. Writes only inside this folder.
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/lessons/verify/stage
cd "$S" || exit 2
mkdir -p "$S/pictures"
for job in "new lockout-test 5" "toe0 lockout-test 5" "old lockout-test 5" "new graphics-test 3" "old graphics-test 3"; do
  set -- $job
  out="$S/tmp-$1-$2"; rm -rf "$out"; mkdir -p "$out"
  start=$(date +%s)
  node "kit-$1/paper-film/tools/render-paper-film.mjs" "$2" "$out" --stills "$3" > "$S/log-$1-$2.txt" 2>&1
  f=$(ls "$out"/still-*.jpg 2>/dev/null | head -1)
  if [ -n "$f" ]; then mv "$f" "$S/pictures/$1-$2.jpg"; echo "$1 $2 drawn in $(( $(date +%s) - start )) s"; else echo "$1 $2 FAILED (see log-$1-$2.txt)"; fi
  rm -rf "$out"
done
python3 - "$S/pictures" <<'EOF'
import sys, os
import numpy as np
from PIL import Image
folder = sys.argv[1]
def load(name):
    path = os.path.join(folder, name)
    return np.asarray(Image.open(path).convert('RGB')).astype(int) if os.path.exists(path) else None
for name in ('new-lockout-test.jpg', 'toe0-lockout-test.jpg', 'old-lockout-test.jpg'):
    a = load(name)
    if a is None:
        print(name, 'missing'); continue
    near_black = (a.max(axis=2) < 8).mean()
    bottom = a[2 * a.shape[0] // 3:].mean()
    print(f'{name}: {a.shape[1]} x {a.shape[0]}, near-black dots {near_black:.2%}, bottom third mean level {bottom:.1f}, whole mean {a.mean():.1f}')
old, new = load('old-graphics-test.jpg'), load('new-graphics-test.jpg')
if old is not None and new is not None:
    diff = np.abs(old - new).max(axis=2)
    print(f'graphics test old against new: {(diff > 0).mean():.4%} of dots differ, largest {diff.max()} levels')
EOF
