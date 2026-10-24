"""What this does: the shared way every calculator in this folder ends: it prints a short report in plain words, names
the film-settings.json values it used, and writes the same result as JSON when asked. Keeping this in one place means
every calculator's output looks the same and always says which house numbers it rests on.

Use inside a calculator:
    from calculator_output import add_output_options, finish
    parser = argparse.ArgumentParser(...); add_output_options(parser)      # adds --json, --out FILE, --report FILE, --settings FILE
    ...
    finish('frame_geometry reach', result_dict, report_lines, settings, args)
--json      print the JSON result instead of the plain report
--out FILE  also write the JSON result to FILE
--report FILE  also write the plain report to FILE
"""
import json
import os


def add_output_options(parser):
    parser.add_argument('--json', action='store_true', help='print the result as JSON instead of plain lines')
    parser.add_argument('--out', help='also write the JSON result to this file')
    parser.add_argument('--report', help='also write the plain-words report to this file')
    parser.add_argument('--settings', help='the settings file (default: kit/film-settings.json, or the FILM_SETTINGS environment variable)')
    return parser


def finish(calculator, result, lines, settings, args=None):
    """Prints the report (or JSON), names the settings used, writes --out and --report. Returns the full result."""
    full = dict(result)
    full['calculator'] = calculator
    full['settings_file'] = settings.path
    full['settings_used'] = settings.used_json()
    text_lines = list(lines) + ['', 'Settings used (film-settings.json):']
    text_lines += ['  ' + line for line in settings.used_lines()] or ['  none']
    text = '\n'.join(text_lines)
    as_json = bool(args and getattr(args, 'json', False))
    print(json.dumps(full, indent=1) if as_json else text)
    if args is not None and getattr(args, 'out', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, 'w') as handle:
            json.dump(full, handle, indent=1)
    if args is not None and getattr(args, 'report', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, 'w') as handle:
            handle.write(text + '\n')
    return full
