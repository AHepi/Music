# Integrator: runs the kit's own measuring scripts for one round (kit pictures against the before pictures) and writes one JSON and a short text.
#   python3 -I measure_all.py ROUND_DIR [--base BASE_DIR] [--kit KIT_DIR_NAME] [--look sooty_1926] [--only p1,p2,p3,p4,p5,p7]
# ROUND_DIR holds <kit>/<scene>/... ; BASE_DIR holds <base>/<scene>/... (default: the first round's base). Results: ROUND_DIR/measures_<kit>.json
import json
import os
import sys

KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.join(KIT, 'harness'))
import numpy as np  # noqa: E402
import coverage  # noqa: E402
import measure_common as mc  # noqa: E402
import measure_joints  # noqa: E402
import measure_mush  # noqa: E402
import measure_period  # noqa: E402
import measure_readable  # noqa: E402
import measure_time  # noqa: E402
import measure_wet  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = ('street', 'lockout')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    round_dir = os.path.abspath(args[0])
    base_dir = os.path.abspath(opts.get('--base', os.path.join(HERE, 'r1', 'base')))
    kit_name = opts.get('--kit', 'kit')
    look_name = opts.get('--look', 'sooty_1926')
    only = set(opts['--only'].split(',')) if '--only' in opts else {'p1', 'p2', 'p3', 'p4', 'p5', 'p7'}
    settings = mc.load_set('pit_village_street')
    look = json.load(open(os.path.join(KIT, 'presets', look_name + '.json')))
    kit_dirs = [os.path.join(round_dir, kit_name, s) for s in SCENES]
    base_dirs = [os.path.join(base_dir, s) for s in SCENES]
    out = {'round': round_dir, 'kit': kit_name, 'base': base_dir}
    cache = os.path.join(base_dir, 'base_measures.json')
    base_cached = json.load(open(cache)) if os.path.exists(cache) else {}

    if 'p1' in only:
        if 'joints' not in base_cached:
            base_cached['joints'] = measure_joints.run(settings, base_dirs)
            json.dump(base_cached, open(cache, 'w'))
        res = measure_joints.run(settings, kit_dirs + base_dirs)          # the joint, puddle and rubbish pictures are drawn once, in the base folders
        out['p1'] = dict(summary=res['summary'], verdict=measure_joints.compare_with_base(res, base_cached['joints']), base_summary=base_cached['joints']['summary'])
        out['p1']['pictures'] = {n: dict(near=e['official']['near'], middle=e['official']['middle'], passed=e['official']['passed'], reasons=e['official']['reasons'], all_dots=e['all_dots']['passed'],
                                         without_kit=e['without_kit']['passed'], kit_share=e['official'].get('kit_share'))
                                 for n, e in res['pictures'].items() if 'official' in e}
    if 'p2' in only:
        if 'wet' not in base_cached:
            base_cached['wet'] = measure_wet.run(settings, base_dirs)
            json.dump(base_cached, open(cache, 'w'))
        res = measure_wet.run(settings, kit_dirs + base_dirs, base_cached['wet'])
        ok, fails = measure_wet.judge(res, base_cached['wet'])
        elem_class = {'soot': 'walls', 'runoff': 'walls', 'foot': 'walls', 'steps': 'trims', 'iron': 'iron', 'dirt': 'road', 'groundcracks': 'road', 'groundmoss': 'road'}
        adjusted = {}
        for key, value in res['element_wet_dry'].items():
            layer, picture = key.split(':', 1)
            cls = elem_class.get(layer)
            ratio = res['wet_to_dry'].get(picture, {}).get(cls) if cls else None
            if ratio:
                adjusted[key] = round(value / ratio, 3)
        out['p2'] = dict(ok=ok, failures=fails, element_wet_dry_over_class=adjusted, wet_to_dry=res['wet_to_dry'], base_wet_to_dry=base_cached['wet']['wet_to_dry'], puddle_cover=res['puddle_cover'], speckle=res['speckle'],
                         element_wet_dry=res['element_wet_dry'], highlight={n: e.get('highlight_share') for n, e in res['pictures'].items() if 'highlight_share' in e})
    if 'p3' in only:
        elements = {}
        for folder in kit_dirs:
            r = measure_readable.run(settings, folder, look)
            for tag, e in r['elements'].items():
                if 'skipped' not in e:
                    elements[tag] = e
        out['p3'] = dict(elements={t: {k: v for k, v in e.items()} for t, e in elements.items()})
    if 'p4' in only:
        out['p4'] = {}
        for scene, kf, bf in zip(SCENES, kit_dirs, base_dirs):
            try:
                out['p4'][scene] = measure_period.run(settings, kf, bf, look)
            except Exception as error:     # a scene without some pictures
                out['p4'][scene] = dict(error=str(error))
    if 'p5' in only:
        out['p5'] = {}
        classes = mc.classes(settings)
        for camera, light, state, scene_id, w, h in mc.plate_list(settings):
            name = f'plate_{camera}_{light}_{state}'
            kf = os.path.join(round_dir, kit_name, scene_id)
            bf = os.path.join(base_dir, scene_id)
            if not (mc.pic(kf, name) and mc.pic(bf, name)):
                out['p5'][name] = dict(missing=True)
                continue
            cp, dp = mc.pic(bf, f'class_{camera}_{w}x{h}'), mc.pic(bf, f'depth_{camera}_{w}x{h}')
            cmap, depth = mc.read_class(cp), mc.read_depth(dp)
            Lk, Lb = mc.read_lum(mc.pic(kf, name)), mc.read_lum(mc.pic(bf, name))
            r = measure_mush.compare(Lk, Lb, cmap, depth, classes)
            out['p5'][name] = dict(ok=r['ok'], failures=r['failures'], plate_mean_ratio=r['plate_mean_ratio'],
                                   classes={c: {k: v for k, v in e.items() if k in ('m1_darkened_third', 'm2_under_010_rise', 'm3_mean_ratio', 'm4_spread_ratio', 'm5_band_ratios')} for c, e in r['classes'].items()})
    if 'p7' in only:
        out['p7'] = {}
        for scene, kf, bf in zip(SCENES, kit_dirs, base_dirs):
            now = measure_time.summarise(measure_time.load_runs([kf]))
            then = measure_time.summarise(measure_time.load_runs([bf]))
            ok, fails = measure_time.judge(now, then)
            out['p7'][scene] = dict(ok=ok, failures=fails, now={k: v for k, v in now.items() if k != 'best'}, base={k: v for k, v in then.items() if k != 'best'})
    path = os.path.join(round_dir, f'measures_{kit_name}.json')
    json.dump(out, open(path, 'w'), indent=1, default=str)
    print('written', path)
    summary(out)


def summary(out):
    if 'p1' in out:
        s, v = out['p1']['summary'], out['p1']['verdict']
        print(f"P1 official {s['official']['passed']}/{s['official']['of']} (base {out['p1']['base_summary']['official']['passed']}), all dots {s['all_dots']['passed']}, without kit {s['without_kit']['passed']}, harsh grid {s['harsh_grid']}, failing {s['official']['failing']}, broke {v['broke']}, ok {v['ok']}")
    if 'p2' in out:
        print(f"P2 ok {out['p2']['ok']} failures {len(out['p2']['failures'])}")
        for f in out['p2']['failures'][:14]:
            print('   ', f)
    if 'p3' in out:
        for tag, e in out['p3']['elements'].items():
            print(f"P3 {tag[:60]:60s} marks {e['marks']:4d} good {e['good']:3d} ({(e['share_good'] or 0):.0%}) lost {(e['share_lost'] or 0):.0%} crushed {(e['share_crushed'] or 0):.0%} {'PASS' if e['passed'] else 'FAIL'}")
    if 'p5' in out:
        for name, e in out['p5'].items():
            if e.get('missing'):
                continue
            print(f"P5 {name} plate mean ratio {e['plate_mean_ratio']} ok {e['ok']}")
            for f in e['failures'][:12]:
                print('     ', f)
    if 'p7' in out:
        for scene, e in out['p7'].items():
            print(f"P7 {scene}: plates {e['now']['plate_best_total']} s vs base {e['base']['plate_best_total']} s; first picture {e['now']['first_picture_seconds']} vs {e['base']['first_picture_seconds']}; pieces {e['now']['pieces_max']} vs {e['base']['pieces_max']} -> {e['failures']}")
    if 'p4' in out:
        for scene, e in out['p4'].items():
            if 'error' in e:
                print('P4', scene, 'error', e['error'])
                continue
            print('P4', scene, 'forbidden', e['forbidden']['passed'], 'caps', e['caps']['passed'], 'hue', {k: v['ok'] for k, v in e['hue'].items()})


if __name__ == '__main__':
    main()
