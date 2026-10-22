"""What this does: the file Blender runs for every `explainer-film-place` verb that works on a scene (the launcher starts it with
`blender -b --disable-autoexec --python blender_run.py -- VERB options`). It puts the kit on Python's path, reads the verb and its options with the
same parser the launcher uses (place_kit/cli.py), runs the verb (place_kit/commands.py), prints plain lines starting PASS, LOOK or FAIL, and ends the
Blender process with the verb's exit code: 0 pass, 1 fail, 2 an input is missing or unusable. A mistake in the kit itself is printed as FAIL with the
last lines of the error and ends with exit 1, so a gate that depends on it fails closed. This file only works inside Blender.
"""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
for folder in (HERE, os.path.join(KIT, 'calculators')):
    if folder not in sys.path:
        sys.path.insert(0, folder)


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    from place_kit import cli
    parser = cli.build_parser()
    parsed = parser.parse_args(arguments)
    from place_kit import commands
    try:
        code = commands.run_verb(parsed)
    except commands.InputMissing as problem:
        print(f'FAIL {problem}')
        code = 2
    except Exception as problem:   # noqa: BLE001 - a fault inside the kit must fail closed, with its last lines shown
        tail = traceback.format_exc().strip().splitlines()[-6:]
        print(f'FAIL the kit stopped with an error while running {parsed.verb}: {problem}')
        print('\n'.join(tail))
        code = 1
    sys.stdout.flush()
    sys.exit(int(code or 0))


main()
