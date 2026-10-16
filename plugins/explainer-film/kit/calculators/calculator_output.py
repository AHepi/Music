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

And every calculator starts the same way, so a missing or broken input file is answered in one plain sentence (exit 2),
never with a Python error dump, and a report piped into `head` stops quietly:
    from calculator_output import run_main, read_json
    data = read_json(path, 'the place facts file', 'python3 calculators/place_facts.py from-shot-facts ...')
    if __name__ == '__main__':
        sys.exit(run_main(main, 'plan_lights'))
"""
import gzip
import json
import os
import signal
import sys
import traceback

INPUT_PROBLEM_EXIT = 2


class InputProblem(SystemExit):
    """A given input that is missing or unreadable: stops the tool with a plain sentence and exit 2."""
    def __init__(self, words):
        super().__init__(INPUT_PROBLEM_EXIT)
        self.words = words


def read_json(path, what_it_is='an input', made_by=''):
    """A JSON file (gzip too, by its .gz name). A missing, empty or broken file stops the tool with a plain sentence that
    names the file, what it should be and what makes it (exit 2)."""
    tail = f' Make it with: {made_by}' if made_by else ''
    try:
        opener = gzip.open if str(path).endswith('.gz') else open
        with opener(path, 'rt') as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise InputProblem(f'{path} is not there (it should be {what_it_is}).{tail}')
    except IsADirectoryError:
        raise InputProblem(f'{path} is a folder, not a file (it should be {what_it_is}).{tail}')
    except json.JSONDecodeError as error:
        raise InputProblem(f'{path} is not valid JSON (line {error.lineno}, column {error.colno}: {error.msg}); it should be {what_it_is}.{tail}')
    except (UnicodeDecodeError, EOFError, OSError) as error:
        raise InputProblem(f'{path} cannot be read ({error}); it should be {what_it_is}.{tail}')


def _file_in_traceback(trace):
    """The file a failing read was reading, found in the failing frames (an open handle's name, or a path)."""
    for frame, _ in reversed(list(traceback.walk_tb(trace))):
        for name in ('fp', 'handle', 'f', 'file', 'stream'):
            value = frame.f_locals.get(name)
            if hasattr(value, 'name') and isinstance(value.name, str):
                return value.name
        for name in ('path', 'filename', 'file_path'):
            value = frame.f_locals.get(name)
            if isinstance(value, str) and value:
                return value
    return None


def _where(trace):
    last = list(traceback.walk_tb(trace))[-1][0] if trace else None
    return f'{os.path.basename(last.f_code.co_filename)} line {last.f_lineno}' if last else 'unknown'


def run_main(main, name):
    """Runs a calculator's main(). A missing, empty or broken input file stops with one plain sentence on the error stream
    and exit 2 (the preflight reads 2 as "an input is missing or unusable"); a report piped into head stops quietly."""
    if hasattr(signal, 'SIGPIPE'):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    try:
        code = main()
        return code if isinstance(code, int) else 0
    except InputProblem as problem:
        print(f'{name}: {problem.words}', file=sys.stderr)
        return INPUT_PROBLEM_EXIT
    except FileNotFoundError as error:
        print(f'{name}: the file {error.filename} is not there. Check the path, or make the file first (see {name} --help).', file=sys.stderr)
        return INPUT_PROBLEM_EXIT
    except IsADirectoryError as error:
        print(f'{name}: {error.filename} is a folder; a file was expected there (see {name} --help).', file=sys.stderr)
        return INPUT_PROBLEM_EXIT
    except json.JSONDecodeError as error:
        found = _file_in_traceback(error.__traceback__) or 'an input file'
        print(f'{name}: {found} is not valid JSON (line {error.lineno}, column {error.colno}: {error.msg}). Make it again with the tool '
              f'that writes it, or mend it by hand (see {name} --help).', file=sys.stderr)
        return INPUT_PROBLEM_EXIT
    except (UnicodeDecodeError, EOFError, gzip.BadGzipFile) as error:
        found = _file_in_traceback(error.__traceback__) or 'an input file'
        print(f'{name}: {found} cannot be read as text or JSON ({error}).', file=sys.stderr)
        return INPUT_PROBLEM_EXIT
    except (KeyError, AttributeError, TypeError) as error:
        if type(error).__name__ == 'MissingSetting':     # the settings table lacks a key the tool reads
            print(f'{name}: the settings file: {error}', file=sys.stderr)
            return INPUT_PROBLEM_EXIT
        # a valid JSON file of the wrong kind: a missing key, or a list or text where an object was expected
        if not isinstance(error, KeyError) and not any(w in str(error) for w in ("'list' object", "'str' object")):
            raise
        words = f'a needed field {error} is missing' if isinstance(error, KeyError) else f'a field holds the wrong kind of value ({error})'
        print(f'{name}: stopped: {words} (at {_where(error.__traceback__)}). An input file is probably not the kind this tool reads '
              f'(see {name} --help for each input\'s format); if it is, this is a fault in the tool: report it with the command.', file=sys.stderr)
        return INPUT_PROBLEM_EXIT


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
