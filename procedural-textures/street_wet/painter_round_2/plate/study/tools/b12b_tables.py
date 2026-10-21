# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Turns the study's measurement files (work/r01 ... work/r08, measurements.json) into the tables of the study note, as text in Markdown, so that no number in the note is typed by hand.
# Plain Python. Used by b13_write_note.py; run alone it prints every table.
import json
import os

WORK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work'))


def store(folder):
    path = os.path.join(WORK, folder, 'measurements.json')
    return json.load(open(path)) if os.path.exists(path) else {}


def cells(entry):
    if entry is None:
        return ['-'] * 3
    if entry['contrast'] is None:
        return ['n/a'] * 3
    return [f"{entry['contrast']:.2f}", f"{entry['delta']:.3f}", f"{entry['seen']:.2f}"]


def table(rows, bands=('near', 'middle'), road=True, header_first='picture'):
    """rows: list of (label, measurement dict or None). Markdown table: brightness of the road, then contrast / delta / seen for each band."""
    head = [header_first] + (['road'] if road else [])
    sub = ['', ''] if road else ['']
    for b in bands:
        head += [f'{b} contrast', f'{b} delta', f'{b} seen']
    lines = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join(['---'] + ['---:'] * (len(head) - 1)) + '|']
    for label, r in rows:
        row = [label] + ([f"{r['road_mean']:.3f}" if r else '-'] if road else [])
        for b in bands:
            row += cells(r[b] if r else None)
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)


def get(folder_store, name):
    return folder_store.get(name)


def baseline_table():
    r1 = store('r01')
    order = []
    for cam, lights in (('main', [('A', ['dry', 'wet', 'heavy']), ('C', ['dry', 'wet']), ('D', ['dry', 'wet']), ('E', ['dry', 'wet', 'heavy'])]),
                        ('close', [('A', ['dry', 'wet', 'heavy']), ('C', ['wet']), ('D', ['wet']), ('E', ['wet'])]),
                        ('lockout', [('A', ['dry', 'wet', 'heavy']), ('C', ['wet']), ('D', ['wet']), ('E', ['wet'])])):
        for light, states in lights:
            for st in states:
                name = f'{cam}_{light}_{st}'
                label = f"{cam} {'B' if (cam == 'lockout' and light == 'A') else light} {st}"
                order.append((label, r1.get(name)))
    return table(order)


def diagnosis_table():
    r1 = store('r01')
    rows = [('dry, as the film has it', 'close_A_dry'), ('wet, round 2 (the problem)', 'close_A_wet'),
            ('wet, all shine taken off (colour darkening only)', 'close_A_wet_dull_wet'), ('wet, roughness 0.9 (film and boost kept)', 'close_A_wet_rough09'),
            ('wet, no water film and no extra shine (roughness 0.3 kept)', 'close_A_wet_no_film'),
            ('wet, relief strength 3 (was 1.4)', 'close_A_wet_normal3'), ('wet, relief strength 6', 'close_A_wet_normal6'),
            ('wet, relief not flattened (Relief Flatten 0, Grain Fill 0)', 'close_A_wet_relief_kept'), ('wet, relief picture removed', 'close_A_wet_normal_off'),
            ('wet, stone tops stay drier (Dry Tops 1.0)', 'close_A_wet_drytops1'), ('wet, no puddles (dial 0)', 'close_A_wet_nopuddles'),
            ('wet, colour picture made flat', 'close_A_wet_colour_flat'), ('DRY, colour picture made flat', 'close_A_dry_colour_flat'), ('DRY, relief picture removed', 'close_A_dry_normal_off')]
    return table([(label, r1.get(name)) for label, name in rows])


def diagnosis_main_table():
    r1 = store('r01')
    rows = [('dry', 'main_A_dry'), ('wet (the problem)', 'main_A_wet'), ('wet, all shine taken off', 'main_A_wet_dull_wet'), ('wet, no film and no extra shine', 'main_A_wet_no_film'),
            ('wet, relief strength 3', 'main_A_wet_normal3'), ('wet, relief not flattened', 'main_A_wet_relief_kept'), ('wet, relief picture removed', 'main_A_wet_normal_off'),
            ('wet, colour picture made flat', 'main_A_wet_colour_flat'), ('DRY, colour picture made flat', 'main_A_dry_colour_flat')]
    return table([(label, r1.get(name)) for label, name in rows])


def solutions_close_table():
    r1, r2, r4, r6 = store('r01'), store('r02'), store('r04'), store('r06')
    r8 = store('r08')
    rows = [('wet, round 2 (the problem)', r1.get('close_A_wet')), ('dry, as the film has it', r1.get('close_A_dry')),
            ('joint picture, colour only (0.45)', r2.get('close_A_wet_joint_a')), ('joint picture first try "b" (colour 0.45, dull, ragged picture)', r2.get('close_A_wet_joint_b')),
            ('joint picture first try "c" (strong)', r2.get('close_A_wet_joint_c')), ('soft picture soft3 (colour 0.8, spec x0.6, coat x0.5)', r4.get('close_A_wet_soft3')),
            ('soft picture soft1 (0.7, x0.5, x0.35)', r4.get('close_A_wet_soft1')), ('soft picture soft2 (0.6, x0.35, x0.25)', r4.get('close_A_wet_soft2')),
            ('closed picture mild1 (0.85, x0.65, x0.55)', r6.get('close_A_wet_mild1')), ('closed picture mild2 (0.9, x0.75, x0.7)', r6.get('close_A_wet_mild2')),
            ('mild1 with texture filter 16', r8.get('close_A_wet_mild1_aniso16b')),
            ('real geometry, soft groove 2.5 cm', r4.get('close_A_wet_geometry')), ('real geometry, sharp groove 2 cm', r4.get('close_A_wet_geometry_sharp')),
            ('sharp geometry + soft2 picture', r4.get('close_A_wet_combo_soft2_geosharp')), ('mild1 + shallow geometry 8 mm', r8.get('close_A_wet_mild1_geo8'))]
    return table(rows, bands=('near', 'middle', 'far'))


def solutions_main_table():
    r1, r6, r8 = store('r01'), store('r06'), store('r08')
    rows = [('wet, round 2 (the problem)', r1.get('main_A_wet')), ('dry, as the film has it', r1.get('main_A_dry')),
            ('mild1', r6.get('main_A_wet_mild1')), ('mild2', r6.get('main_A_wet_mild2')), ('mild1 + shallow geometry 8 mm (y 3 to 18 m)', r8.get('main_A_wet_mild1_geo8')),
            ('AT 1080 x 1920: wet, round 2', r8.get('big_A_wet')), ('AT 1080 x 1920: wet, mild1', r8.get('big_A_wet_mild1'))]
    return table(rows, bands=('near', 'middle', 'far'))


if __name__ == '__main__':
    for fn in (baseline_table, diagnosis_table, diagnosis_main_table, solutions_close_table, solutions_main_table):
        print('##', fn.__name__)
        print(fn())
        print()
