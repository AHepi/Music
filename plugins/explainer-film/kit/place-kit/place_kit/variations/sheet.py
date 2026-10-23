"""What this does: makes ONE labelled CONTACT SHEET of a variations batch: the baseline first, then every variation with its small picture(s), its name, its settings in plain words and its
measures (value range, detail energy, colour shift, saturation shift, squint score against the baseline), a flag under any variation that came out nearly the same as another or does not show
in these cameras, and at the bottom the card seconds the batch used. One JPG, kept under place_render.preview_download_kilobytes_max (400 KB): the quality and then the size are lowered until it fits.
Plain Python with Pillow; no Blender needed.

A concrete example: a batch of 10 variations through 2 cameras is a sheet of 11 cells (3 across), each with two pictures side by side and four short lines of text under them.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFont

from .. import house_numbers as numbers
from . import keys

BACKGROUND, TEXT, QUIET, WARN, RULE = (246, 244, 239), (28, 28, 30), (92, 92, 98), (176, 58, 30), (214, 210, 200)


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:          # an old Pillow without sizes: the small default font
        return ImageFont.load_default()


def wrap(draw, text, face, width, max_lines):
    """The text broken into at most max_lines lines no wider than width pixels (the last line ends in ... when text is left)."""
    words, lines, line = str(text).split(), [], ''
    for word in words:
        trial = (line + ' ' + word).strip()
        if draw.textlength(trial, font=face) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines[-1] and draw.textlength(lines[-1] + '...', font=face) > width:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + '...'
    return lines


def measure_lines(result, baseline, target):
    """The two short lines of numbers under a picture, from the average over the cameras."""
    average = result.get('average') or {}
    if not average:
        return ['no picture to measure']
    first = f'range {average["p5"]:.2f}-{average["p95"]:.2f} ({average["range"]:.2f})   detail {average["detail"]:.1f}'
    if baseline is not None and result['name'] != 'baseline':
        first += f' ({average["detail_change"]:+.1f})'
        second = f'colour shift {average["colour_shift"]:.1f}   sat {average["saturation_shift"]:+.3f}   squint {average["squint"]:.3f}' + ('  (under the target)' if average['squint'] < target else '')
    else:
        second = f'saturation {average["mean_saturation"]:.3f}   (the others are measured against this)'
    return [first, second]


def make_sheet(path, results, cameras, meta, thumbnail_width=None, max_kilobytes=None):
    """Writes the contact sheet to path (a .jpg). results: the baseline first, each with 'name', 'set', 'args', 'script', 'pictures' (each with an absolute 'path'), 'average', 'flags' (list of text),
    'ok'. meta: {'change', 'scene', 'engine', 'size', 'dropped': [text], 'pair_lines': [text], 'card_lines': [text], 'legend': True}. Returns {'path', 'bytes', 'quality', 'scale', 'width', 'height'}."""
    tw = int(thumbnail_width or numbers.value('place_variations.sheet_thumbnail_width_pixels'))
    limit = int((max_kilobytes or numbers.value('place_render.preview_download_kilobytes_max')) * 1024)
    target = float(numbers.value('place_measures.squint_target'))
    camera_names = list(cameras) or sorted({p['camera'] for r in results for p in r.get('pictures', [])})
    cams = max(1, len(camera_names))
    ratio = 0.667
    for result in results:
        for picture in result.get('pictures', []):
            if picture.get('ok') and picture.get('path') and os.path.exists(picture['path']):
                with Image.open(picture['path']) as opened:
                    ratio = opened.height / opened.width
                break
    th = int(tw * ratio)
    gap, margin = 6, 14
    cell_w = cams * tw + (cams - 1) * gap
    columns = 4 if cams == 1 else 3 if cams == 2 else 2
    rows = -(-len(results) // columns)
    big, mid, small = font(20), font(15), font(13)
    sheet_w = margin + columns * (cell_w + margin)
    probe = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    baseline = results[0] if results and results[0]['name'] == 'baseline' else None
    # the text under each picture: (line, face, colour), worked out first so every row is as tall as its tallest cell
    cells = []
    for index, result in enumerate(results):
        flags = result.get('flags') or []
        label = 'baseline (the saved scene)' if result['name'] == 'baseline' else f'#{index} {result["name"]}'
        block = [(label, mid, WARN if flags or not result.get('ok', True) else TEXT)]
        settings_text = 'the saved scene as it is' if result['name'] == 'baseline' else keys.describe_variation(result, limit=4)
        block += [(line, small, QUIET) for line in wrap(probe, settings_text, small, cell_w, 2)]
        for line in measure_lines(result, baseline, target):
            block += [(piece, small, TEXT) for piece in wrap(probe, line, small, cell_w, 2)]
        for flag in flags[:3]:
            block += [(line, small, WARN) for line in wrap(probe, flag, small, cell_w, 2)]
        if not result.get('ok', True):
            block += [(line, small, WARN) for line in wrap(probe, 'FAILED: ' + ' '.join(result.get('notes') or ['it was not drawn']), small, cell_w, 2)]
        cells.append(block)
    line_h = {mid: 20, small: 16}
    heights = [sum(line_h[face] for _, face, _ in block) + 6 for block in cells]
    row_text = [max(heights[r * columns:(r + 1) * columns]) for r in range(rows)]
    header = [(f'{meta.get("change", "variations")}', big, TEXT),
              (f'{len(results) - 1} variation(s) and the baseline; scene {meta.get("scene", "")}; {meta.get("engine", "")} {meta.get("size", "")}; cameras: {", ".join(camera_names) or "the scene camera"}', mid, QUIET)]
    notes = [(line, small, WARN) for line in (meta.get('dropped') or [])] + [(line, small, WARN) for line in (meta.get('pair_lines') or [])]
    footer = [(line, small, TEXT) for line in (meta.get('card_lines') or [])] + ([(line, small, QUIET) for line in LEGEND] if meta.get('legend', True) else [])
    inner = sheet_w - 2 * margin
    wrapped_notes = [(line, face, colour) for text, face, colour in notes for line in wrap(probe, text, face, inner, 3)]
    wrapped_footer = [(line, face, colour) for text, face, colour in footer for line in wrap(probe, text, face, inner, 4)]
    header_h = 34 + 22 + margin
    notes_h = (len(wrapped_notes) * 17 + 6) if wrapped_notes else 0
    footer_h = len(wrapped_footer) * 17 + margin * 2
    sheet_h = header_h + notes_h + sum(th + h + margin for h in row_text) + footer_h
    image = Image.new('RGB', (sheet_w, sheet_h), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((margin, margin), header[0][0], font=header[0][1], fill=header[0][2])
    draw.text((margin, margin + 28), header[1][0][:260], font=header[1][1], fill=header[1][2])
    y = header_h
    for line, face, colour in wrapped_notes:
        draw.text((margin, y), line, font=face, fill=colour)
        y += 17
    y += 6 if wrapped_notes else 0
    row_top = [y]
    for height in row_text:
        row_top.append(row_top[-1] + th + height + margin)
    for index, result in enumerate(results):
        column, row = index % columns, index // columns
        x0, y0 = margin + column * (cell_w + margin), row_top[row]
        pictures = {p['camera']: p for p in result.get('pictures', []) if p.get('ok') and p.get('path') and os.path.exists(p['path'])}
        for slot, camera in enumerate(camera_names or [None]):
            picture = pictures.get(camera) if camera is not None else (next(iter(pictures.values())) if pictures else None)
            box = (x0 + slot * (tw + gap), y0)
            if picture is None:
                draw.rectangle([box[0], box[1], box[0] + tw, box[1] + th], outline=WARN, width=2)
                draw.text((box[0] + 8, box[1] + th // 2 - 8), 'no picture', font=mid, fill=WARN)
            else:
                with Image.open(picture['path']) as opened:
                    image.paste(opened.convert('RGB').resize((tw, th), Image.LANCZOS), box)
        ty = y0 + th + 4
        for line, face, colour in cells[index]:
            draw.text((x0, ty), line, font=face, fill=colour)
            ty += line_h[face]
    y_footer = row_top[-1]
    draw.line([margin, y_footer, sheet_w - margin, y_footer], fill=RULE, width=1)
    ty = y_footer + 8
    for line, face, colour in wrapped_footer:
        draw.text((margin, ty), line, font=face, fill=colour)
        ty += 17
    return _save_under_limit(image, path, limit)


LEGEND = ['range = the 5th to 95th percentile of luminance (and the gap); detail = fine contrast (and its change from the baseline); colour shift = how far the average colour moved from the baseline '
          '(0 = the same, about 2 is the least a person sees); sat = change in average saturation; squint = how well the big shapes and light hold against the baseline (1.000 = the same; the house target is 0.92). '
          'Every number is the average over the cameras; each camera\'s own numbers are in the result file.']


def _save_under_limit(image, path, limit):
    """Saves as JPEG under `limit` bytes: the quality goes down first (82 to 55), then the size by a tenth at a time (never under half)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    scale = 1.0
    while True:
        shown = image if scale == 1.0 else image.resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
        for quality in (82, 76, 70, 64, 58, 52):
            buffer = io.BytesIO()
            shown.save(buffer, 'JPEG', quality=quality, optimize=True)
            if buffer.tell() <= limit:
                with open(path, 'wb') as handle:
                    handle.write(buffer.getvalue())
                return {'path': path, 'bytes': buffer.tell(), 'quality': quality, 'scale': round(scale, 2), 'width': shown.width, 'height': shown.height}
        scale -= 0.1
        if scale < 0.5:
            buffer = io.BytesIO()
            shown.save(buffer, 'JPEG', quality=50, optimize=True)
            with open(path, 'wb') as handle:
                handle.write(buffer.getvalue())
            return {'path': path, 'bytes': buffer.tell(), 'quality': 50, 'scale': round(scale + 0.1, 2), 'width': shown.width, 'height': shown.height, 'over_limit': True}
