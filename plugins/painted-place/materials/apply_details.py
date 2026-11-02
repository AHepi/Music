"""
What this file does:
Puts the details onto a dressed place in one call: puddles and gutter water, damp wall feet and soot stains,
rust under iron, moss and weeds at wall feet and kerbs, leaves and litter in the gutters, fallen stone flakes.
Every position comes from the place's own roles (walls, kerbs, roads, iron), none from a settings file.

    blender -b --python apply_details.py -- --scene DRESSED.blend --save-as DETAILED.blend [--wet 1.0] [--grime 1.0] [--growth 1.0] [--litter 1.0] [--report details.json]
    python3 apply_details.py --scene ... --save-as ...      (with the bpy module installed)

The amounts are dials from 0 (none) to about 2 (twice the street). Run it after apply_by_role.py and before
the look stage. Running it again first removes what it added before. Nothing in the scene's shapes or
materials is changed; the details are separate objects named "DETAIL • ...".
"""

import argparse
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apply_by_role  # noqa: E402
import lay_details  # noqa: E402

NEEDED = {
    'water': 'PUDDLE • shallow transparent reflective film',
    'grime': 'GRIME • dark damp organic residue',
    'soot': 'Damp • fine dark soot',
    'rust': 'RUST • rain-aged iron',
    'moss': 'MOSS • subdued olive crevices',
    'stone': 'STONE • worn honey-grey architectural dressings',
    'paper': 'PAPER • aged torn fragments',
}
GREENS = ['Weed • rain olive', 'Weed • dark ivy', 'Weed • yellowed seed blades']
LEAVES = ['Fallen leaf • peat brown', 'Fallen leaf • ochre']


def detail_materials():
    names = sorted(set(NEEDED.values()) | set(GREENS) | set(LEAVES))
    by_name = apply_by_role.append_materials(names)
    materials = {key: by_name[name] for key, name in NEEDED.items()}
    materials['greens'] = [by_name[n] for n in GREENS]
    materials['leaves'] = [by_name[n] for n in LEAVES]
    return materials


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Put the details onto a dressed place.')
    parser.add_argument('--scene', required=True)
    parser.add_argument('--save-as', required=True)
    parser.add_argument('--wet', type=float, default=1.0, help='puddles and gutter water')
    parser.add_argument('--grime', type=float, default=1.0, help='damp feet, soot and run-off stains, rust under iron')
    parser.add_argument('--growth', type=float, default=1.0, help='moss and weeds')
    parser.add_argument('--litter', type=float, default=1.0, help='leaves, fragments, fallen flakes')
    parser.add_argument('--report')
    args = parser.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.scene))
    scene = bpy.context.scene
    materials = detail_materials()
    report = lay_details.lay_details(scene, materials, apply_by_role.role_from_name,
                                     wet=args.wet, grime=args.grime, growth_amount=args.growth, litter_amount=args.litter)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save_as))
    print(json.dumps(report, indent=2))
    if args.report:
        with open(args.report, 'w') as handle:
            json.dump(report, handle, indent=2)


if __name__ == '__main__':
    main()
