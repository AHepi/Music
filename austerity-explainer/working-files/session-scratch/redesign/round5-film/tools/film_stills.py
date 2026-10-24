"""What this does: takes full-size stills out of the filmed pages (not drawn again: what is really in the film), one
at each moment listed in a moments file, and names each still-SECONDS.jpg by its chapter time, so sheet.py can lay them
side by side with their notes. A moment's still is the first filmed frame at or after that moment (the first frame
that shows a thing coming in on its word); a moment written as "f1234" is that chapter frame exactly.
Use: python3 -I film_stills.py FILM.mp4 FIRST_CHAPTER_FRAME MOMENTS.json OUT_FOLDER
  MOMENTS.json: {"55.10": "the cut to W1", "f1738": "the slide's first frame", ...}; writes OUT_FOLDER/notes.json
  (the notes keyed by each still's chapter time, for sheet.py)
"""
import json
import math
import os
import subprocess
import sys

film, first, moments_file, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
FPS = 30
os.makedirs(out, exist_ok=True)
moments = json.load(open(moments_file))
wanted = {}
for key, note in moments.items():
    frame = int(key[1:]) if key.startswith('f') else math.ceil(float(key) * FPS - 1e-6)
    wanted.setdefault(frame, []).append(note)
frames = sorted(wanted)
count = int(subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_packets',
                            '-of', 'csv=p=0', film], capture_output=True, text=True, check=True).stdout.strip())
inside = [f for f in frames if 0 <= f - first < count]
for f in frames:
    if f not in inside: print(f'chapter frame {f} is outside the film (frames {first} to {first + count - 1})')
# one pass through the film, keeping only the wanted frames, in order
select = '+'.join(f'eq(n\\,{f - first})' for f in inside)
pattern = os.path.join(out, 'pick-%04d.jpg')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', film, '-vf', f"select='{select}'", '-fps_mode', 'passthrough', '-q:v', '2', pattern], check=True)
notes = {}
for i, f in enumerate(inside):
    name = f'{f / FPS:.2f}'
    os.replace(os.path.join(out, f'pick-{i + 1:04d}.jpg'), os.path.join(out, f'still-{name}.jpg'))
    notes[name] = ' / '.join(wanted[f])
json.dump(notes, open(os.path.join(out, 'notes.json'), 'w'), indent=1)
print(f'{len(inside)} stills in {out}')
