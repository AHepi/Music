# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE DIAL SHEET: one picture that shows what each main dial of the four ground layers does. Every row is one dial, drawn three times on the same close view with ONLY that layer
# in (off = the dial at its lowest, the layer's own default, and high = the top of the dial's range), so a person can see what turning it does.
#     python3 -I ground/sheet_ground.py SET_ID LOOK OUT_JPG [WORK_FOLDER] [--scene SCENE_ID] [--draw]
# The rows come from the set's ground section ("dial_sheet": [{layer, dial, camera, light, state, label, values?}]); a row without "values" uses the dial's lowest value, its default and
# its highest value from the dial table. Without a "dial_sheet" in the set, each layer's first three own dials are shown on the set's default camera.
# --draw  draws the pictures on the rented machine through harness/remote.py (the one allowed client); without it the pictures already in WORK_FOLDER are sheeted.
# The sheet is a JPG under 400 KB (harness/sheets.py steps the quality down).
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import dials, settings as settings_module  # noqa: E402
from harness import remote, sheets  # noqa: E402
from ground import dials_ground, ground_names as gc  # noqa: E402

SKIP = {'amount', 'seed', 'inflate_limit', 'fade_start', 'fade_end', 'wet_follow', 'show_part', 'near_only', 'max_contrast', 'dull', 'inflate_limit'}


def rows_for(settings, section):
    rows = list(section.get('dial_sheet', []))
    if rows:
        return rows
    camera = (settings.get('test_set') or {}).get('close_views', ['main'])[0]
    out = []
    for layer in gc.LAYER_KEYS:
        spec = dials.TABLE.layers.get(layer)
        names = [n for n in spec.names() if n not in SKIP][:3] if spec else []
        out += [dict(layer=layer, dial=n, camera=camera) for n in names]
    return out


def values_for(row):
    if row.get('values'):
        return list(row['values'])
    spec = dials.TABLE.layers[row['layer']].row(row['dial'])
    return [spec['lo'], spec['default'], spec['hi']]


def job_list(settings, rows, look_of, size):
    ts = settings.get('test_set') or {}
    jobs = []
    for i, row in enumerate(rows):
        for j, v in enumerate(values_for(row)):
            camera = row['camera']
            plate = next((p for p in ts.get('plates', []) if p[0] == camera), None)
            jobs.append(dict(name=f'dial_{i:02d}_{j}', camera=camera, light=row.get('light', plate[1] if plate else 'A'), state=row.get('state', plate[2] if plate else 'wet'), look=look_of(row['layer']),
                             view='beauty', size=list(size), group='dial', dials={row['layer']: {row['dial']: v}}))
    return jobs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--') and not sys.argv[i + 1].startswith('--')}
    set_id, look, out_jpg = args[0], args[1], args[2]
    work = args[3] if len(args) > 3 else os.path.join(os.path.dirname(out_jpg), 'dial_sheet_work')
    scene_id = opts.get('--scene') or settings_module.load_set(set_id).scenes[0]['id']
    settings = settings_module.load_set(set_id)
    dials_ground.ensure()
    section = gc.ground_section(settings)
    rows = rows_for(settings, section)
    size = (480, 360, 16)
    os.makedirs(work, exist_ok=True)
    if '--draw' in sys.argv:
        jobs = job_list(settings, rows, lambda layer: f'kit:{layer}', size)
        spec = dict(set=set_id, scene=scene_id, pack=True, feature_dirs=list(settings.get('feature_report_dirs', [])), jobs=jobs)
        job_file = os.path.join(work, 'jobs.json')
        json.dump(spec, open(job_file, 'w'), indent=1)
        print(remote.run_batch(settings.scene(scene_id)['file'], [job_file], f'/workspace/wk_out/ground_dialsheet_{set_id}', os.path.join(work, 'out')), flush=True)
    items = []
    for i, row in enumerate(rows):
        for j, v in enumerate(values_for(row)):
            path = next((os.path.join(work, 'out', f'dial_{i:02d}_{j}{ext}') for ext in ('.jpg', '.png') if os.path.exists(os.path.join(work, 'out', f'dial_{i:02d}_{j}{ext}'))), None)
            if path is None:
                continue
            label = (row.get('label') or f'{row["layer"]}: {row["dial"]}') if j == 0 else ''
            items.append((path, f'{label}  {v:g}'.strip() if j == 0 else f'{v:g}'))
    print(sheets.contact_sheet(items, out_jpg, columns=3, cell_width=300, title='What each main ground dial does: lowest | default | highest (only that layer in)'))


if __name__ == '__main__':
    main()
