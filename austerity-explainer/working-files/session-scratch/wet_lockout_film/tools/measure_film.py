"""What this file does (plain words): measures a finished clip frame by frame, small (270 x 480), to find flicker and jumps: for every frame the average brightness of the
whole picture and of its lower half, and the change from the one before. Reports the biggest changes, any frame whose brightness jumps away from both its neighbours (flicker), the
steadiest and busiest stretches, and writes numbers/film_NAME.json. Run: python3 -I measure_film.py CLIP.mp4 NAME
"""
import json, os, subprocess, sys
import numpy as np
clip, name = sys.argv[1], sys.argv[2]
w, h = 270, 480
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', clip, '-vf', f'scale={w}:{h}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32) / 255
luma = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
whole, lower = luma.mean(axis=(1, 2)), luma[:, h // 2:].mean(axis=(1, 2))
change = np.abs(np.diff(luma, axis=0)).mean(axis=(1, 2))           # change[i]: frame i -> i + 1
second = whole[1:-1] - 0.5 * (whole[:-2] + whole[2:])               # flicker: a frame away from both neighbours
out = {'frames': int(len(f)), 'mean_brightness': float(whole.mean()),
       'change_between_frames_median': float(np.median(change)), 'change_between_frames_largest': float(change.max()), 'largest_change_into_frame': int(change.argmax() + 1),
       'flicker_largest_(frame_away_from_both_neighbours)': float(np.abs(second).max()), 'flicker_frame': int(np.abs(second).argmax() + 1),
       'flicker_median': float(np.median(np.abs(second)))}
seconds = {}
for s in range(12):
    a, b = s * 30, min((s + 1) * 30, len(f))
    seconds[str(s)] = {'whole': float(whole[a:b].mean()), 'lower_half': float(lower[a:b].mean()), 'change_median': float(np.median(change[a:max(a + 1, b - 1)]))}
out['by_second'] = seconds
top = np.argsort(change)[::-1][:6]
out['six_biggest_changes'] = [{'into_frame': int(i + 1), 'second': round((i + 1) / 30, 2), 'change': float(change[i])} for i in top]
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'numbers'), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'numbers', f'film_{name}.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'by_second'}, indent=1))
np.save(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'numbers', f'film_{name}_whole.npy'), whole)
np.save(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'numbers', f'film_{name}_change.npy'), change)
