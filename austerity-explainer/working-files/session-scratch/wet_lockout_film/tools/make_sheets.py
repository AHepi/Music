"""What this file does (plain words): turns a finished clip into the pictures used to look at every frame of it, in a work folder:
  small/NNN.jpg     every frame (000 to 359) at 180 x 320, kept only until the contact sheets are made
  sheets/all_frames_N.jpg   contact sheets of EVERY frame, 10 across and 6 down (60 frames a sheet), each frame labelled with its number and second
  full/t_SS.SS.jpg  full-size (1080 x 1920) frames every half second (0.0 to 11.5, and the last frame)
  first/NNN.jpg     full-size frames, one by one, for a stretch of frames asked for (default 60 to 105: the first 1.5 seconds of the camera move)
Run: python3 -I make_sheets.py CLIP.mp4 WORKFOLDER [FIRST_FRAME LAST_FRAME]
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
clip, work = sys.argv[1], sys.argv[2]
a, b = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (60, 105)
for d in ('small', 'sheets', 'full', 'first'): os.makedirs(os.path.join(work, d), exist_ok=True)
# small frames, every one
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', clip, '-vf', 'scale=180:320:flags=area', '-q:v', '3', '-start_number', '0', os.path.join(work, 'small', '%03d.jpg')], check=True)
frames = sorted(f for f in os.listdir(os.path.join(work, 'small')) if f.endswith('.jpg'))
print(len(frames), 'small frames')
font = ImageFont.load_default()
per = 60
for s in range(0, len(frames), per):
    sheet = Image.new('RGB', (10 * 180, 6 * 320), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    for i, f in enumerate(frames[s:s + per]):
        x, y = (i % 10) * 180, (i // 10) * 320
        sheet.paste(Image.open(os.path.join(work, 'small', f)), (x, y))
        n = int(f[:3]); draw.rectangle([x, y, x + 62, y + 11], fill=(0, 0, 0)); draw.text((x + 2, y), f'{n:03d} {n / 30:5.2f}s', fill=(255, 255, 0), font=font)
    sheet.save(os.path.join(work, 'sheets', f'all_frames_{s // per + 1}.jpg'), quality=88)
# full-size frames every half second
n_frames = len(frames)
for k in range(0, 24):
    t = k * 0.5
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', clip, '-vf', f'select=eq(n\\,{int(round(t * 30))})', '-frames:v', '1', '-q:v', '2', os.path.join(work, 'full', f't_{t:05.2f}.jpg')], check=True)
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', clip, '-vf', f'select=eq(n\\,{n_frames - 1})', '-frames:v', '1', '-q:v', '2', os.path.join(work, 'full', 'last_frame.jpg')], check=True)
# full-size frames one by one for a stretch
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', clip, '-vf', f'select=between(n\\,{a}\\,{b})', '-vsync', '0', '-q:v', '2', '-start_number', str(a), os.path.join(work, 'first', '%03d.jpg')], check=True)
print('done')
