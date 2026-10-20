# What this does: draws ONE picture that puts the six builds' "ladders" side by side: how much each description size bought.
# Left panel: edge skill against the reference (dot for dot; lib/pixel_compare.py). Right panel: the same-kind score (lib/texture_compare.py).
# Across: the description size in bytes (a log scale: each step to the right is ten times bigger), with the S / M / L size limits marked.
# Every number is read from recipes/<surface>/final_report.json (and, for gravel's sampled tiles, the sizes of variations/descriptions/*.json).
#   filled circles joined by a line = descriptions that write down THIS reference's elements or trace its patches, in order of size;
#   hollow squares = procedural descriptions (rules + measured statistics + a seed, no tracing) fitted to the reference;
#   diamonds (right panel only) = the average of the eight NEW tiles made from sampled descriptions (their edge skill against the reference is
#   about 0 by design, so they are left off the left panel).
# Also writes ladder_chart_numbers.json with every point drawn. Plain Python (numpy, PIL): python3 -I ladder_chart.py
import glob
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
RECIPES = os.path.join(PROC, 'recipes')
OUT = os.path.join(PROC, 'cookbook', 'pictures', 'descriptions-six-ladders-chart.png')
SURFACES = ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel']
DIAMOND_LABELS = {'slate': (5300, 0.765, 'left'), 'brick': (12500, 0.70, 'right'), 'wood': (3500, 0.626, 'left'),
                  'metal': (4600, 0.569, 'left'), 'gravel': (2000, 0.403, 'left'), 'mud': (14000, 0.47, 'right')}
COLOURS = {'brick': '#2a78d6', 'slate': '#eb6834', 'wood': '#1baf7a', 'metal': '#eda100', 'mud': '#e87ba4', 'gravel': '#008300'}  # fixed order


def report(surface):
    return json.load(open(os.path.join(RECIPES, surface, 'final_report.json')))


def collect():
    """For each surface: main ladder points (bytes, edge skill, same-kind, name), procedural points, and the sampled tiles' average."""
    data = {}
    r = report('brick')
    rows = {row['tag']: row for row in r['rate_distortion']}
    main = [rows[t] for t in ('R0', 'R1', 'S', 'M', 'M+ (200 KB ellipses)', 'L-ellipses (376 KB)', 'L')]
    tiles = r['variation']['tiles']
    data['brick'] = {'main': [(x['description_bytes'], x['edge_skill_2px'], x['texture_overall'], x['tag']) for x in main], 'procedural': [],
                     'sampled': (sum(t['description_bytes'] for t in tiles) / len(tiles), r['variation']['texture_overall_mean'])}
    r = report('slate')
    c = r['classes']
    main = ['S0_layout_only', 'M_trace_tiny', 'M_trace_small', 'M_trace_coarse', 'L_trace_small', 'L_trace_medium', 'L_trace_fine']
    tiles = list(r['variations']['tiles'].values())
    data['slate'] = {'main': [(c[k]['bytes'], c[k]['edge_skill_2px'], c[k]['texture_compare_overall_as_baked'], k) for k in main],
                     'procedural': [(c[k]['bytes'], c[k]['edge_skill_2px'], c[k]['texture_compare_overall_as_baked'], k) for k in ('S1_layout_stamps', 'S2_stamps_grain')],
                     'sampled': (sum(t['description_bytes'] for t in tiles) / len(tiles), r['variations']['texture_overall_mean'])}
    r = report('wood')
    c = r['classes']
    main = ['S0_layout_only', 'M1_trace_20k', 'M2_trace_40k', 'M3_trace_62k', 'L1_trace_150k', 'L2_trace_300k', 'L3_trace_480k']
    rows = r['variation']['rows']
    data['wood'] = {'main': [(c[k]['bytes'], c[k]['edge_skill_2px'], c[k]['texture_compare_overall'], k) for k in main],
                    'procedural': [(c['S1_layout_paint_grain']['bytes'], c['S1_layout_paint_grain']['edge_skill_2px'], c['S1_layout_paint_grain']['texture_compare_overall'], 'S1')],
                    'sampled': (sum(t['description_bytes'] for t in rows) / len(rows), r['variation']['texture_compare_mean'])}
    r = report('metal')
    c = r['rate_distortion']
    main = ['layerA', 'layerB', 'S0', 'R16k', 'R32k', 'M', 'R128k', 'R256k', 'L']
    tiles = [r['variation'][str(i)] for i in range(1, 9)]
    data['metal'] = {'main': [(c[k]['description_bytes'], c[k]['edge_skill'], c[k]['texture_compare_overall'], k) for k in main],
                     'procedural': [(c['S']['description_bytes'], c['S']['edge_skill'], c['S']['texture_compare_overall'], 'S')],
                     'sampled': (sum(t['description_bytes'] for t in tiles) / 8, sum(t['texture_overall'] for t in tiles) / 8)}
    r = report('mud')
    c = r['mud']
    main = ['R0_flat_ground', 'R1_plus_puddle_outlines', 'R2_plus_40_big_stones', 'R3_plus_ruts', 'M_puddle_tones_stone_faces',
            'L2_traced_ground_2000_patches', 'L_traced_ground_5000_patches', 'L_final_traced_ground_plus_corrections']
    tiles = list(r['variation']['summary']['tiles'].values())
    data['mud'] = {'main': [(c[k]['description_bytes'], c[k]['edge_skill_2px'], c[k]['texture_compare_overall'], k) for k in main],
                   'procedural': [(c['S_layout_ruts_clods']['description_bytes'], c['S_layout_ruts_clods']['edge_skill_2px'], c['S_layout_ruts_clods']['texture_compare_overall'], 'S')],
                   'sampled': (sum(t['bytes'] for t in tiles) / len(tiles), r['variation']['summary']['kind_score_mean'])}
    r = report('gravel')
    c = {row['class_name']: row for row in r['classes']}
    main = sorted(['M_a600_s120', 'T_k24_a250', 'T_k24_a100', 'T_k24_a50', 'L_a250_s12', 'L_a100_s8'], key=lambda k: c[k]['description_kb'])
    sizes = [os.path.getsize(p) for p in sorted(glob.glob(os.path.join(RECIPES, 'gravel', 'variations', 'descriptions', 'sample_*.json')))]
    tiles = list(r['variation']['tiles'].values())
    data['gravel'] = {'main': [(c[k]['description_kb'] * 1024, c[k]['edge_skill'], c[k]['texture_compare_as_baked'], k) for k in main],
                      'procedural': [(c['S_v4']['description_kb'] * 1024, c['S_v4']['edge_skill'], c['S_v4']['texture_compare_as_baked'], 'S_v4')],
                      'sampled': (sum(sizes) / len(sizes), sum(t['texture_overall'] for t in tiles) / len(tiles))}
    return data


def draw(data):
    scale = 2                                   # draw twice as big, then shrink: smooth edges
    width, height = 1500 * scale, 700 * scale
    image = Image.new('RGB', (width, height), '#fcfcfb')
    pen = ImageDraw.Draw(image)
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    bold_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font = lambda size, bold=False: ImageFont.truetype(bold_path if bold else font_path, size * scale)
    ink, muted, grid = '#1f1f1e', '#6b6a64', '#e4e3df'
    pen.text((24 * scale, 14 * scale), 'What each description size bought: the six builds side by side', fill=ink, font=font(22, True))
    pen.text((24 * scale, 44 * scale), 'Across: description size in bytes (each grid step = 10 x bigger). Filled circles + line = describes or traces THIS reference;'
             ' hollow squares = procedural (rules + statistics); diamonds = average of 8 NEW tiles.', fill=muted, font=font(13))
    x_low, x_high = math.log10(300), math.log10(700000)
    panels = [('Dot for dot: edge skill against the reference', 1, (0.0, 0.8), 70, 'left'),
              ('Same kind of surface: same-kind score', 2, (0.0, 0.9), 790, 'right')]
    numbers = {}
    for title, index, (y_low, y_high), left, side in panels:
        top, bottom, plot_width = 122 * scale, 640 * scale, 560 * scale
        x0 = left * scale
        to_x = lambda b: x0 + (math.log10(b) - x_low) / (x_high - x_low) * plot_width
        to_y = lambda v: bottom - (v - y_low) / (y_high - y_low) * (bottom - top)
        pen.text((x0, 72 * scale), title, fill=ink, font=font(15, True))
        for v in [round(y_low + 0.1 * i, 1) for i in range(int(round((y_high - y_low) / 0.1)) + 1)]:
            pen.line([(x0, to_y(v)), (x0 + plot_width, to_y(v))], fill=grid, width=scale)
            pen.text((x0 - 34 * scale, to_y(v) - 8 * scale), f'{v:.1f}', fill=muted, font=font(11))
        for b, text in ((1000, '1 KB'), (10000, '10 KB'), (100000, '100 KB')):
            pen.line([(to_x(b), top), (to_x(b), bottom)], fill=grid, width=scale)
            pen.text((to_x(b) - 14 * scale, bottom + 6 * scale), text, fill=muted, font=font(11))
        for b, text in ((8192, 'S | M  (8 KB)'), (65536, 'M | L  (64 KB)'), (524288, 'L limit (512 KB)')):
            for y in range(top, bottom, 10 * scale):
                pen.line([(to_x(b), y), (to_x(b), y + 5 * scale)], fill='#a9a8a1', width=scale)
            pen.text((to_x(b) - 30 * scale, top - 15 * scale), text, fill=muted, font=font(10))
        if side == 'left':
            for v, text in ((0.30, 'tier "layout" needs 0.30'), (0.55, 'tier "close" needs 0.55')):
                pen.line([(x0, to_y(v)), (x0 + plot_width, to_y(v))], fill='#8f8e87', width=scale)
                pen.text((x0 + 6 * scale, to_y(v) - 17 * scale), text, fill=muted, font=font(11))
        else:
            pen.rectangle([(x0, to_y(0.50)), (x0 + plot_width, to_y(0.16))], fill='#efeeea')
            for v in (0.16, 0.50):
                pen.line([(x0, to_y(v)), (x0 + plot_width, to_y(v))], fill='#c9c8c2', width=scale)
            pen.text((x0 + 6 * scale, to_y(0.50) + 3 * scale), 'band: other real surfaces scored 0.16 to 0.50',
                     fill=muted, font=font(11))
            pen.text((x0 + 6 * scale, to_y(0.50) + 18 * scale), '(brick and mud self-tests)', fill=muted, font=font(11))
        pen.line([(x0, top), (x0, bottom), (x0 + plot_width, bottom)], fill='#8f8e87', width=scale)
        ends = []
        for surface in SURFACES:
            colour = COLOURS[surface]
            key = 'edge' if side == 'left' else 'kind'
            pick = (lambda p: p[1]) if side == 'left' else (lambda p: p[2])
            points = [(to_x(p[0]), to_y(pick(p))) for p in data[surface]['main']]
            pen.line(points, fill=colour, width=2 * scale)
            for (px, py) in points:
                pen.ellipse([(px - 5 * scale, py - 5 * scale), (px + 5 * scale, py + 5 * scale)], fill=colour, outline='#fcfcfb', width=2 * scale)
            for p in data[surface]['procedural']:
                px, py = to_x(p[0]), to_y(pick(p))
                pen.rectangle([(px - 6 * scale, py - 6 * scale), (px + 6 * scale, py + 6 * scale)], fill='#fcfcfb', outline=colour, width=3 * scale)
            if side == 'right':
                b, v = data[surface]['sampled']
                px, py = to_x(b), to_y(v)
                pen.polygon([(px, py - 9 * scale), (px + 9 * scale, py), (px, py + 9 * scale), (px - 9 * scale, py)], fill=colour, outline=ink)
                label_at = DIAMOND_LABELS[surface]                     # (bytes, score, 'left' or 'right') where the name goes
                text = f'{surface}: new tiles'
                text_width = pen.textlength(text, font=font(11))
                tx, ty = to_x(label_at[0]), to_y(label_at[1])
                if label_at[2] == 'left':
                    tx -= text_width
                if (label_at[0], label_at[1]) != (b, v):
                    pen.line([(px, py), (tx + (text_width if label_at[2] == 'left' else 0), ty)], fill=colour, width=scale)
                pen.text((tx, ty - 7 * scale), text, fill=ink, font=font(11))
            ends.append([points[-1][1], surface, points[-1]])
            numbers.setdefault(surface, {})[key] = {'main': [(round(p[0]), pick(p), p[3]) for p in data[surface]['main']],
                                                    'procedural': [(round(p[0]), pick(p), p[3]) for p in data[surface]['procedural']]}
            if side == 'right':
                numbers[surface]['sampled_average_bytes_and_score'] = [round(data[surface]['sampled'][0]), round(data[surface]['sampled'][1], 3)]
        ends.sort()                                   # direct labels in a column right of the plot, pushed apart so they never overlap
        gap = 20 * scale
        for i in range(1, len(ends)):
            ends[i][0] = max(ends[i][0], ends[i - 1][0] + gap)
        for label_y, surface, (px, py) in ends:
            lx = x0 + plot_width + 14 * scale
            pen.line([(px + 6 * scale, py), (lx - 4 * scale, label_y)], fill=COLOURS[surface], width=scale)
            pen.text((lx, label_y - 9 * scale), surface, fill=ink, font=font(13, True))
    image = image.resize((width // scale, height // scale), Image.LANCZOS)
    image.save(OUT, optimize=True)
    with open(os.path.join(HERE, 'ladder_chart_numbers.json'), 'w') as handle:
        json.dump(numbers, handle, indent=1)
    print(OUT, os.path.getsize(OUT), 'bytes')


draw(collect())
