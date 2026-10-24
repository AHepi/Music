"""What this does: reads the camera's place for every frame (render-paper-film.mjs SCENE --camera FILE.json 1) and,
for pages 3 to 5 of chapter 2 for newcomers, lists each shot: where the camera stands at its first and last frame,
how far it travels, which way it faces (the angle between its aim and straight up the lane, and the most the aim
changes in the shot), its lens and focus, and whether a held shot moves at all. This proves the rule "cameras never
turn": a slide may travel, but the aim must never change.
Use: python3 -I camera_facing.py CAMERA.json [FROM_SECONDS=47.37] [TO_SECONDS=123.47]
"""
import json
import math
import sys

data = json.load(open(sys.argv[1]))
start = float(sys.argv[2]) if len(sys.argv) > 2 else 47.37
end = float(sys.argv[3]) if len(sys.argv) > 3 else 123.47
samples = [s for s in data['samples'] if start <= s['t'] <= end]


def aim(s):
    d = [b - a for a, b in zip(s['position'], s['target'])]
    n = math.sqrt(sum(v * v for v in d))
    return [v / n for v in d]


def angle(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))))


UP_THE_LANE = [0, 0, -1]   # three.js is (x, z, -y): Blender's +y (up the lane) is three.js -z
shots = []
for s in samples:
    if not shots or shots[-1]['name'] != s['shot']: shots.append({'name': s['shot'], 'samples': []})
    shots[-1]['samples'].append(s)
for shot in shots:
    ss = shot['samples']
    first, last = ss[0], ss[-1]
    aims = [aim(s) for s in ss]
    turn = max(angle(aims[0], a) for a in aims)
    facing = angle(aims[0], UP_THE_LANE)
    travel = math.dist(first['position'], last['position'])
    moving = [s['t'] for a, s in zip(ss, ss[1:]) if math.dist(a['position'], s['position']) > 1e-6]
    lenses = sorted({s['fov'] for s in ss})
    print(f"{shot['name']}: {first['t']:.2f}-{last['t']:.2f} s, {len(ss)} frames; from {[round(v, 3) for v in first['position']]} "
          f"to {[round(v, 3) for v in last['position']]} ({travel:.3f} m); aim {facing:.4f} degrees off straight up the lane, "
          f"turns at most {turn:.4f} degrees; lens {lenses}; "
          + (f"moves from {moving[0]:.2f} to {moving[-1]:.2f} s" if moving else 'never moves'))
print(f'all {len(samples)} frames from {start} to {end} s: the aim turns at most '
      f'{max(angle(aim(samples[0]), aim(s)) for s in samples):.4f} degrees from the first frame')
