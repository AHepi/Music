# What this does: draws the Works' continuity sheet (plan 34, "How the two factories stay the same", point 9): one
# picture of each Works view side by side, and under each what the shot checker measured in that view, so a helper can
# check at a glance that the views agree:
#   - No. 1 is on the left of No. 2 wherever both show (their chimneys' and gates' places across the frame)
#   - the chimneys: one round chimney for No. 1, two square ones for No. 2 (how many of each show, and where)
#   - the gate boards: which shows, and where
#   - the men: how many waiting men show in the view (7 at No. 1 when quiet, none when working, none at No. 2 when flat
#     out, 8 when slowed)
# It also writes continuity.json with the same numbers and a list of anything that disagrees.
# It reads, for each view, a small picture (assemble_works.py --previews) and the measurements the shot checker made of
# the same view and state (the facts folder of paper-film/tools/check-shot.sh: ids.png, the flat-colour picture in which
# each group has its own colour, and facts.json).
# Run (plain Python with Pillow and numpy; no Blender):
#   python3 make_works_continuity_sheet.py OUT_FOLDER LABEL=PICTURE.png:FACTS_FOLDER [LABEL=...] ...
# for example  "W3 quiet=previews/w3-quiet.png:check/w3/facts"  "W1 quiet=previews/w1-quiet.png:check/w1/facts"

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_FILE = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD_FILE = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
CELL_WIDTH, CELL_HEIGHT = 405, 720           # each view's picture on the sheet (the film's 9:16)
TEXT_HEIGHT = 330
MARGIN = 18
# how many pixels of a group must show (on the checker's 1080 x 1920 picture) for it to count as seen
SEEN_PIXELS = 150


def font(size, bold=False):
    try:
        return ImageFont.truetype(BOLD_FILE if bold else FONT_FILE, size)
    except OSError:
        return ImageFont.load_default()


def measure(facts_folder):
    """What shows in one view: each group's visible pixels and their middle across the frame (0 left, 1 right)."""
    with open(os.path.join(facts_folder, 'facts.json')) as handle:
        facts = json.load(handle)
    ids = np.asarray(Image.open(os.path.join(facts_folder, 'ids.png')).convert('RGB')).astype(np.int16)
    width = ids.shape[1]
    seen = {}
    for name, group in facts['groups'].items():
        colour = np.array(group['colour'], dtype=np.int16)
        mask = np.all(np.abs(ids - colour) <= 2, axis=2)
        count = int(mask.sum())
        across = float(np.nonzero(mask)[1].mean() / width) if count else None
        seen[name] = {'pixels': count, 'across': round(across, 3) if across is not None else None}
    return facts, seen


def describe(label, facts, seen):
    """Plain lines for the sheet, and the disagreements found."""
    lines, faults = [], []
    def shows(name):
        return name in seen and seen[name]['pixels'] >= SEEN_PIXELS
    men = sorted(name for name in seen if name.startswith('man '))
    men_seen = [name for name in men if shows(name)]
    lines.append(f'Men waiting in view: {len(men_seen)}' + (f' (of {len(men)} placed in this state)' if men else ''))
    chimney_1 = seen.get('no-1 chimney')
    chimney_2 = seen.get('no-2 chimneys')
    if chimney_1 and shows('no-1 chimney'):
        lines.append(f'No. 1\'s round chimney at {chimney_1["across"]:.2f} across')
    if chimney_2 and shows('no-2 chimneys'):
        lines.append(f'No. 2\'s square chimneys at {chimney_2["across"]:.2f} across')
    if chimney_1 and chimney_2 and shows('no-1 chimney') and shows('no-2 chimneys'):
        if chimney_1['across'] < chimney_2['across']:
            lines.append('No. 1 is left of No. 2: yes')
        else:
            lines.append('No. 1 is left of No. 2: NO')
            faults.append(f'{label}: No. 1\'s chimney is not left of No. 2\'s')
    if not (shows('no-1 chimney') or shows('no-2 chimneys')):
        lines.append('No chimney in view (they stand behind the camera)')
    for name in sorted(seen):
        if 'board' in name and shows(name):
            lines.append(f'{name.capitalize()} at {seen[name]["across"]:.2f} across')
    gates = [name for name in seen if 'gate' in name and 'board' not in name and 'lamp' not in name]
    for name in gates:
        if shows(name):
            lines.append(f'{name.capitalize()} at {seen[name]["across"]:.2f} across')
    meet = facts.get('lines_meet')
    if isinstance(meet, dict):          # one meeting point for each direction named in the check file
        meet = meet.get('lane') or next(iter(meet.values()), None)
    if meet:
        lines.append(f'Lines meet at {meet[0]:.2f} across, {meet[1]:.2f} down')
    camera = facts.get('camera', {})
    if camera:
        lines.append(f'Camera at x {camera["at"][0]:.2f}, y {camera["at"][1]:.2f}, eye {camera["at"][2]:.2f} m; '
                     f'turn {camera.get("turn_degrees", 0):.0f}, tilt {camera.get("tilt_degrees", 0):.0f}')
    return lines, faults, len(men_seen)


def main():
    out = os.path.abspath(sys.argv[1])
    entries = []
    for argument in sys.argv[2:]:
        label, rest = argument.split('=', 1)
        picture, facts_folder = rest.rsplit(':', 1)
        entries.append((label, picture, facts_folder))
    os.makedirs(out, exist_ok=True)
    sheet = Image.new('RGB', (MARGIN + len(entries) * (CELL_WIDTH + MARGIN), 70 + CELL_HEIGHT + TEXT_HEIGHT + MARGIN), (24, 24, 26))
    draw = ImageDraw.Draw(sheet)
    draw.text((MARGIN, 18), 'The Works: continuity sheet (one picture of each view; numbers from the shot checker)', fill=(235, 235, 235), font=font(24, True))
    report = {'views': {}, 'faults': []}
    for index, (label, picture, facts_folder) in enumerate(entries):
        left = MARGIN + index * (CELL_WIDTH + MARGIN)
        image = Image.open(picture).convert('RGB').resize((CELL_WIDTH, CELL_HEIGHT), Image.LANCZOS)
        sheet.paste(image, (left, 70))
        facts, seen = measure(facts_folder)
        lines, faults, men = describe(label, facts, seen)
        report['views'][label] = {'picture': picture, 'facts': facts_folder, 'men_seen': men, 'seen': seen, 'lines': lines}
        report['faults'] += faults
        y = 70 + CELL_HEIGHT + 10
        draw.text((left, y), label, fill=(255, 214, 120), font=font(20, True))
        y += 30
        for line in lines:
            words, row = line.split(' '), ''
            for word in words:
                trial = (row + ' ' + word).strip()
                if draw.textlength(trial, font=font(14)) > CELL_WIDTH:
                    draw.text((left, y), row, fill=(225, 225, 225), font=font(14))
                    y += 19
                    row = word
                else:
                    row = trial
            draw.text((left, y), row, fill=(225, 225, 225), font=font(14))
            y += 21
    sheet.save(os.path.join(out, 'works-continuity-sheet.png'))
    with open(os.path.join(out, 'continuity.json'), 'w') as handle:
        json.dump(report, handle, indent=1)
    print('continuity sheet:', os.path.join(out, 'works-continuity-sheet.png'))
    print('disagreements:', report['faults'] or 'none')


main()
