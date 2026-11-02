"""
What this file does:
Opens a saved Blender scene, drops the look stage onto it with the dials given, draws one small picture and
writes the dials used next to it, so a fix pass changes one number and runs again.

    blender -b --python render_small.py -- --scene PLACE.blend --out PICTURE.png [dials]
    python3 render_small.py --scene PLACE.blend --out PICTURE.png [dials]        (with the bpy module installed)

Dials (all optional):
    --width 540 --height 960      picture size (the film is 1080 x 1920; small pictures for the loop)
    --samples 32                  more is smoother and slower
    --exposure 0.5                the street's number; the coal mine needed 1.0
    --window-light 1.0            strength of the lights at glowing windows; the coal mine needed 2.0
    --lamp-light 1.0              strength of the gas-lamp lights; a narrow lane with four lamps wanted 0.6
    --sky-light 1.0               strength of the blue sky lights; raise it when a place goes amber all over
    --amber-reflection 1.0        the warm off-frame light beside the camera; 0 turns it off
    --fire-light 1.0              strength of a fire's or flame's light, separate from the lamps
    --haze 1.0                    thickness of the haze; raise it when far things should turn paler and bluer
    --max-glow-lights 48          how many glowing patches get a real light (every lamp always does)
    --painterly 0.28              how much of the paint filter is mixed in (0 none, 1 all)
    --rain                        fine slanted rain
    --person-camera               set the camera like a standing person (32 mm, eye 1.65 m)
    --keep-lights                 keep the scene's own lights lit as well
    --keep-world                  keep the scene's own sky
    --no-haze                     no haze
    --save-as LOOKED.blend        also save the scene with the look applied (the look can be removed again)

Nothing in the scene's shapes or materials is changed. The scene file on disk is not changed unless --save-as names it.
"""

import argparse
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import look_stage  # noqa: E402


def parse(argv):
    parser = argparse.ArgumentParser(description='Draw one small picture of a scene with the look stage.')
    parser.add_argument('--scene', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--width', type=int, default=540)
    parser.add_argument('--height', type=int, default=960)
    parser.add_argument('--samples', type=int, default=32)
    parser.add_argument('--exposure', type=float, default=0.5)
    parser.add_argument('--window-light', type=float, default=1.0)
    parser.add_argument('--lamp-light', type=float, default=1.0, help='strength of the gas-lamp lights (1.0 = the street)')
    parser.add_argument('--sky-light', type=float, default=1.0, help='strength of the blue sky lights (1.0 = the street)')
    parser.add_argument('--amber-reflection', type=float, default=1.0, help='the warm off-frame light beside the camera (0 = none)')
    parser.add_argument('--fire-light', type=float, default=1.0, help='strength of the light a fire, flame or brazier gives (separate from lamps)')
    parser.add_argument('--haze', type=float, default=1.0, help='thickness of the haze (1.0 = the street; 2.0 twice as thick; 0.5 half)')
    parser.add_argument('--max-glow-lights', type=int, default=48)
    parser.add_argument('--painterly', type=float, default=0.28)
    parser.add_argument('--rain', action='store_true')
    parser.add_argument('--person-camera', action='store_true')
    parser.add_argument('--keep-lights', action='store_true')
    parser.add_argument('--keep-world', action='store_true')
    parser.add_argument('--no-haze', action='store_true')
    parser.add_argument('--save-as')
    return parser.parse_args(argv)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parse(argv)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.scene))
    scene = bpy.context.scene
    if scene.camera is None:
        raise SystemExit('the scene has no camera; place one first (the look stage lights the camera side)')
    report = look_stage.apply_look(
        scene,
        keep_scene_lights=args.keep_lights,
        replace_world=not args.keep_world,
        haze=not args.no_haze,
        rain=args.rain,
        camera_like_a_person=args.person_camera,
        samples=args.samples,
        resolution=(args.width, args.height),
        max_glow_lights=args.max_glow_lights,
        painterly_mix=args.painterly,
        exposure=args.exposure,
        window_light_scale=args.window_light,
        lamp_light_scale=args.lamp_light,
        sky_light_scale=args.sky_light,
        amber_reflection=args.amber_reflection,
        fire_light_scale=args.fire_light,
        haze_scale=args.haze,
    )
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    scene.render.filepath = out
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds = round(time.time() - started, 1)
    dials = {k: v for k, v in vars(args).items() if k not in ('scene', 'out', 'save_as')}
    record = {'scene': os.path.abspath(args.scene), 'picture': out, 'seconds': seconds, 'dials': dials,
              'look_stage': {k: v for k, v in report.items() if k != 'added_objects'}}
    with open(os.path.splitext(out)[0] + ' - dials.json', 'w') as handle:
        json.dump(record, handle, indent=2, default=str)
    if args.save_as:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save_as))
    print(f'drew {out} in {seconds} s; glowing patches found {report.get("glow_patches_found", 0)}, lights added {report.get("glow_lights_added", 0)}')


if __name__ == '__main__':
    main()
