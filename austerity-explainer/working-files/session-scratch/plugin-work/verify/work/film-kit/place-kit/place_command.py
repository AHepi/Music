"""What this does: the plain-Python launcher behind `explainer-film-place`. It reads the verb and its options (the list is in place_kit/cli.py), runs
the plain verbs itself (check-presets, ownership-diff, measure, crops, rent, --verbs) and starts Blender in the background for every verb that works
on a scene: it finds Blender (the --blender option, then the BLENDER environment variable, then machine-settings.env beside the kit, then the PATH),
runs `blender -b --disable-autoexec --python-exit-code 1 SCENE.blend --python blender_run.py -- VERB options`, and hands back Blender's output and exit
code (0 pass, 1 fail, 2 an input is missing or unusable). A verb that may draw with EEVEE (render, normals-test) is started under xvfb-run -a when that
exists and no screen is set, because EEVEE needs a screen on a machine without a graphics card (set PLACE_NO_XVFB=1 to switch that off).
It refuses a verb that needs a scene when the scene file is missing, with one plain sentence naming the file and how to make one.

A concrete example: python3 place_command.py finish --scene place.blend --settings place-settings.json --save-as place-finished.blend
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from place_kit import cli  # noqa: E402

EXIT_FAIL, EXIT_MISSING = 1, 2


def find_blender(explicit=None, kit_root=None):
    """The Blender program: the option, BLENDER, machine-settings.env (KEY=value lines beside the kit), then the PATH. None when not found."""
    candidates = [explicit, os.environ.get('BLENDER')]
    settings_file = os.path.join(kit_root or os.path.dirname(HERE), 'machine-settings.env')
    if os.path.exists(settings_file):
        for line in open(settings_file, encoding='utf-8'):
            line = line.strip()
            if line.startswith('BLENDER=') and not line.startswith('#'):
                candidates.append(line.split('=', 1)[1].strip())
    candidates.append(shutil.which('blender'))
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def wants_screen(verb):
    return verb in cli.SCREEN_VERBS and not os.environ.get('DISPLAY') and not os.environ.get('PLACE_NO_XVFB') and shutil.which('xvfb-run') is not None


def blender_command(blender, scene, verb, verb_args, with_screen=False):
    """The full command list that runs one verb inside Blender."""
    command = [blender, '-b', '--disable-autoexec', '--python-exit-code', '1']
    if scene:
        command.append(scene)
    command += ['--python', os.path.join(HERE, 'blender_run.py'), '--', verb] + verb_args
    if with_screen:
        command = ['xvfb-run', '-a'] + command
    return command


def needs_scene_file(parsed):
    """A render job names its own scene, and a combine of stage files builds on whatever scene they make; every other scene verb needs --scene."""
    if parsed.verb == 'render':
        return False
    if parsed.verb == 'combine':
        return not getattr(parsed, 'stages', None)
    return True


def send_render_to_a_card(parsed):
    """For `render`: the exit code when the job went to a rented card, or None when it is drawn here (a plain LOOK line says why when finals stay local)."""
    from place_kit.render import client
    where, reason = client.choose_where(parsed.where, parsed.finals)
    if where == 'rented':
        return client.render_command(parsed)
    if parsed.where == 'auto' and parsed.finals:
        print('LOOK ' + reason)
    return None


def run_blender_verb(parsed, raw_args):
    verb = parsed.verb
    scene = parsed.scene
    kit_root = os.path.abspath(parsed.kit) if parsed.kit else (os.environ.get('EXPLAINER_FILM_KIT') or os.path.dirname(HERE))
    if verb == 'render':
        rented = send_render_to_a_card(parsed)
        if rented is not None:
            return rented
    if needs_scene_file(parsed) and not scene:
        print(f'explainer-film-place {verb}: give the scene with --scene FILE.blend (the place you built and saved). To try the kit on a tiny demo, run: '
              f'python3 {os.path.join(os.path.dirname(HERE), "calculators", "tests", "fixtures", "place", "make_hut_scene.py")} --help', file=sys.stderr)
        return EXIT_MISSING
    if scene and not os.path.exists(scene):
        print(f'explainer-film-place {verb}: the scene file {scene} is not there. Save the place from Blender first (File > Save As, or bpy.ops.wm.save_as_mainfile), '
              'then give its path with --scene.', file=sys.stderr)
        return EXIT_MISSING
    blender = find_blender(parsed.blender, kit_root)
    if not blender:
        print(f'explainer-film-place {verb}: Blender was not found. Install Blender 5.2 or newer and give its path with --blender, the BLENDER variable, or a BLENDER= line in '
              'machine-settings.env (explainer-film-setup writes one), or put blender on the PATH.', file=sys.stderr)
        return EXIT_MISSING
    environment = dict(os.environ, EXPLAINER_FILM_KIT=kit_root)
    command = blender_command(blender, os.path.abspath(scene) if scene else None, verb, raw_args, wants_screen(verb))
    run = subprocess.run(command, env=environment, capture_output=True, text=True)
    lines = [line for line in run.stdout.splitlines() if not _is_blender_noise(line)]
    sys.stdout.write('\n'.join(lines) + ('\n' if lines else ''))
    if run.stderr.strip():
        error_lines = [line for line in run.stderr.splitlines() if not _is_blender_noise(line)]
        if error_lines:
            sys.stderr.write('\n'.join(error_lines) + '\n')
    return run.returncode


BLENDER_LOG_LINE = re.compile(r'^\d\d:\d\d\.\d+\s+\w+\s+\|')


def _is_blender_noise(line):
    """Blender's own startup and log lines (not the kit's PASS, LOOK and FAIL lines)."""
    return bool(BLENDER_LOG_LINE.match(line)) or line.startswith(('Blender 5', 'Blender 4', 'Read blend', 'Blender quit', 'Warning: Unable', 'Color management:', 'Info: Deleted', 'Fra:', 'Saved:'))


def run_plain_verb(parsed, raw_args):
    verb = parsed.verb
    if verb == 'check-presets':
        import check_presets
        return check_presets.main(['--kit-root', os.path.abspath(parsed.kit)] if parsed.kit else [])
    if verb == 'ownership-diff':
        from place_kit.checks import ownership
        return ownership.main_command(parsed)
    if verb == 'measure':
        return run_calculator('picture_measures.py', measure_arguments(parsed, raw_args))
    if verb == 'crops':
        return run_calculator('picture_measures.py', crops_arguments(parsed))
    if verb == 'rent':
        from place_kit.render import client
        return client.main_command(parsed)
    print(f'explainer-film-place: the verb {verb} is not available here', file=sys.stderr)
    return EXIT_MISSING


def calculators_folder(parsed=None):
    kit = os.path.abspath(parsed.kit) if parsed is not None and getattr(parsed, 'kit', None) else os.path.dirname(HERE)
    return os.path.join(kit, 'calculators')


def run_calculator(name, arguments):
    tool = os.path.join(calculators_folder(), name)
    if not os.path.exists(tool):
        print(f'explainer-film-place: the kit has no calculators/{name}', file=sys.stderr)
        return EXIT_MISSING
    return subprocess.run([sys.executable, '-I', '-B', tool] + arguments).returncode


def measure_arguments(parsed, raw_args):
    pictures = list(parsed.pictures or [])
    if parsed.make_guard:
        arguments = ['make-guard'] + pictures[:1]
        if parsed.out:
            arguments += ['--out', parsed.out]
        return arguments
    arguments = ['check' if parsed.guard else 'measure'] + pictures
    for flag, value in (('--guard', parsed.guard), ('--regions', parsed.regions), ('--id-map', parsed.id_map), ('--id-colours', parsed.id_colours), ('--previous', parsed.previous),
                        ('--out', parsed.out), ('--report', parsed.report)):
        if value:
            arguments += [flag, value]
    if parsed.json:
        arguments.append('--json')
    return arguments


def crops_arguments(parsed):
    arguments = ['crops', parsed.picture or '']
    if parsed.boxes:
        arguments += ['--boxes'] + parsed.boxes
    for flag, value in (('--previous', parsed.previous), ('--out-folder', parsed.out_folder)):
        if value:
            arguments += [flag, value]
    return arguments


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = cli.build_parser()
    if '--verbs' in argv:
        print('\n'.join(cli.VERBS))
        return 0
    if not argv or argv[0] in ('-h', '--help') and len(argv) == 1:
        parser.print_help()
        return 0
    parsed = parser.parse_args(argv)
    if not parsed.verb:
        parser.print_help()
        return EXIT_MISSING
    spec = cli.VERBS[parsed.verb]
    # the arguments after the verb are passed on unchanged to the code inside Blender
    verb_index = argv.index(parsed.verb)
    raw_args = argv[verb_index + 1:]
    if spec['blender']:
        return run_blender_verb(parsed, raw_args)
    return run_plain_verb(parsed, raw_args)


if __name__ == '__main__':
    sys.exit(main())
