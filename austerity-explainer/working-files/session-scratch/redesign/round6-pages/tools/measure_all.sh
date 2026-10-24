#!/bin/bash
# What this does: runs round 6's measurements on a folder of stills drawn by moments.sh (pages 3 to 5 of chapter 2 for
# newcomers): the drums' letters, the gate boards' letters and the gate lamps (letters.py); the fire either side of the
# cut on "go" (fire_measure.py); how much No. 2's doorway, windows and the stone round them brighten on "busy", and how
# dark the people at work stay (region_change.py, boxes worked out from where the doorway is on the W2 plate frame);
# and where the brightest pixels are in W1 (bright_share.py, the gate and its board).
# Use: bash measure_all.sh STILLS_FOLDER
set -u
d="$1"
T=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round6-pages/tools
J=/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/works/works-shot.json
echo "== letters and lamps, W1 (62.4, 67.5, 73.5) and W2 (88.5)"
python3 -I $T/letters.py $J w1 composed $d/still-62.40.jpg $d/still-67.50.jpg $d/still-73.50.jpg
python3 -I $T/letters.py $J w2 composed $d/still-88.50.jpg
echo "== the fire either side of \"go\" (66.9 before, 67.5 and 68.5 after)"
python3 -I $T/fire_measure.py $J w1 composed $d/still-66.90.jpg $d/still-67.50.jpg $d/still-68.50.jpg
echo "== \"busy\" (79.0 before; boxes from the W2 plate frame)"
boxes=$(python3 -I - "$J" <<'EOF'
import json, math, sys
shot = json.load(open(sys.argv[1]))
cam = shot['views']['w2']['plate']; t = math.tan(math.radians(shot.get('film_fov_degrees', 60.4) / 2))
def f(x, y, z):
    a = y - cam[1]
    return 540 + 540 * (x - cam[0]) / (a * t * 0.5625), 960 - 960 * (z - cam[2]) / (a * t)
dx, dy, _ = shot['doorway_feet']['no-2']   # 1 m in front of the doorway's middle
wall = dy + 1.0
l, top = f(dx - 1.5, wall, 3.6); r, b = f(dx + 1.5, wall, 0.2)
wl, wt = f(dx - 1.6, wall, 7.2); wr, wb = f(dx + 1.6, wall, 4.0)
sl, st = f(dx - 2.6, wall, 7.6); sr, sb = f(dx + 2.6, wall, 3.6)
print(f'windows:{int(wl)},{int(wt)},{int(wr)},{int(wb)} doorway:{int(l)},{int(top)},{int(r)},{int(b)} stone:{int(sl)},{int(st)},{int(sr)},{int(sb)}')
EOF
)
echo "boxes: $boxes"
python3 -I $T/region_change.py $boxes $d/still-79.00.jpg $d/still-79.40.jpg $d/still-79.80.jpg $d/still-80.20.jpg $d/still-80.60.jpg $d/still-81.30.jpg
echo "== the brightest pixels in W1 (62.4): the gate box from its hinges, the ground to 4.6 m"
box=$(python3 -I - "$J" <<'EOF'
import json, math, sys
shot = json.load(open(sys.argv[1]))
cam = shot['views']['w1']['composed']; t = math.tan(math.radians(shot.get('film_fov_degrees', 60.4) / 2))
g = shot['gates']['no-1']; (lx, ly, _), (rx, _, _) = g['hinges']['left'], g['hinges']['right']
def f(x, y, z):
    a = y - cam[1]
    return 0.5 + 0.5 * (x - cam[0]) / (a * t * 0.5625), 0.5 - 0.5 * (z - cam[2]) / (a * t)
x0, y0 = f(lx, ly, 4.6); x1, y1 = f(rx, ly, 0.0)
print(f'{x0:.3f} {y0:.3f} {x1:.3f} {y1:.3f}')
EOF
)
python3 -I $T/bright_share.py $d/still-62.40.jpg $box "W1 62.4 gate box $box"
