"""What this does: reads the film's house numbers from kit/film-settings.json (the one table every calculator and tool
shares), so no tool keeps its own copy of a number that could drift apart from the others.

Every number in film-settings.json is an entry like
    {"value": 1080, "unit": "pixels", "kind": "measured" | "judged" | "invented", "source": "where it came from"}
grouped in sections by area ("frame", "sound", "timing", ...). A section may hold groups of entries inside it.
Keys are written with dots: "frame.width_pixels", "shot_kind_profiles.crowd.rules.rule3_story_box".
    measured  the project measured it (a recording, a render, a bill); change it only by measuring again
    judged    a person or a helper chose it by looking; change it only after looking again
    invented  nobody has tested it yet; treat it as a starting point and say so when you use it

Use from Python (a calculator in this folder):
    from settings import load_settings
    settings = load_settings()                        # kit/film-settings.json, or FILM_SETTINGS, or a path you give
    width = settings.value('frame.width_pixels')      # 1080; a missing key stops with a clear message
    settings.used_lines()                             # plain lines naming every value read so far (put them in reports)
Use from the command line:
    python3 settings.py show [SECTION]       every entry (or one section), with its unit, kind and source
    python3 settings.py get KEY [--json]     one entry
    python3 settings.py check                checks that every entry has a value, unit, kind and source (exit 1 if not)
    python3 settings.py sections             the section names
    python3 settings.py profile crowd dark_subject    the composing rules a view of those kinds of shot is held to
    --settings PATH  reads another settings file (also: environment variable FILM_SETTINGS)
From Python, resolve_profile(settings, ['crowd', 'dark_subject']) gives the same rules as a dict.

A builder adding a calculator adds its own section to film-settings.json (an "about" line, then entries); it must not
change another section's numbers without saying so in its report.
"""
import argparse
import difflib
import json
import os
import sys

KINDS = ('measured', 'judged', 'invented')
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(os.path.dirname(HERE), 'film-settings.json')


class MissingSetting(KeyError):
    """A key that film-settings.json does not have."""

    def __str__(self):
        return self.args[0] if self.args else 'missing setting'


def is_entry(node):
    return isinstance(node, dict) and 'value' in node


def is_note_key(key):
    return key.startswith('about') or key.startswith('_') or key.endswith('_note') or key in ('how_to_read', 'entry_format', 'kinds')


def walk_entries(node, prefix=''):
    """Every (dotted key, entry) under a node, in file order."""
    if not isinstance(node, dict):
        return
    for key, child in node.items():
        if is_note_key(key):
            continue
        dotted = f'{prefix}.{key}' if prefix else key
        if is_entry(child):
            yield dotted, child
        elif isinstance(child, dict):
            yield from walk_entries(child, dotted)


class Settings:
    """The settings table, plus a record of which values a calculator read (for its report)."""

    def __init__(self, data, path):
        self.data = data
        self.path = path
        self.used = {}

    def node(self, key):
        """The dict or entry at a dotted key; stops with a clear message if it is not there."""
        current = self.data
        walked = []
        for part in key.split('.'):
            if not isinstance(current, dict) or part not in current:
                where = '.'.join(walked) or 'the top level'
                choices = [k for k in current.keys() if not is_note_key(k)] if isinstance(current, dict) else []
                close = difflib.get_close_matches(part, choices, n=3)
                hint = f' Did you mean {", ".join(repr(".".join(walked + [c])) for c in close)}?' if close else ''
                raise MissingSetting(f'film-settings.json has no "{key}" ("{part}" is not in {where}).{hint} '
                                     f'(file: {self.path}). Add it with a value, unit, kind and source, or fix the name.')
            current = current[part]
            walked.append(part)
        return current

    def entry(self, key):
        found = self.node(key)
        if not is_entry(found):
            raise MissingSetting(f'film-settings.json: "{key}" is a section or group, not a single number '
                                 f'(it holds: {", ".join(k for k in found if not is_note_key(k))}). (file: {self.path})')
        self.used[key] = found
        return found

    def value(self, key):
        return self.entry(key)['value']

    def section(self, key):
        """A whole section or group as {dotted key: entry}; every entry in it counts as used."""
        found = self.node(key)
        entries = dict(walk_entries(found, key)) if not is_entry(found) else {key: found}
        self.used.update(entries)
        return entries

    def has(self, key):
        try:
            self.node(key)
            return True
        except MissingSetting:
            return False

    def used_lines(self):
        """One plain line per value read: 'frame.width_pixels = 1080 pixels (judged)'."""
        return [f'{key} = {describe_value(e)} ({e.get("kind", "kind not given")})' for key, e in self.used.items()]

    def used_json(self):
        return {key: {'value': e['value'], 'unit': e.get('unit'), 'kind': e.get('kind')} for key, e in self.used.items()}


def describe_value(entry):
    value, unit = entry.get('value'), entry.get('unit') or ''
    text = json.dumps(value) if isinstance(value, (list, dict)) else str(value)
    return f'{text} {unit}'.strip()


def load_settings(path=None):
    """Reads film-settings.json: the path given, else the FILM_SETTINGS environment variable, else kit/film-settings.json."""
    path = path or os.environ.get('FILM_SETTINGS') or DEFAULT_PATH
    if not os.path.exists(path):
        raise SystemExit(f'settings: no settings file at {path} (give --settings PATH or set FILM_SETTINGS)')
    try:
        with open(path) as handle:
            data = json.load(handle)
    except json.JSONDecodeError as problem:
        raise SystemExit(f'settings: {path} is not valid JSON: {problem}')
    return Settings(data, path)


LOOSEST = {'max': max, 'min': min}


def loosest_of(entries):
    """The loosest of several kinds' versions of one rule (see shot_kind_profiles.about_combining)."""
    off = [(kind, e) for kind, e in entries if not e.get('applies', True)]
    if off:
        kind, chosen = off[-1]
        return dict(chosen, from_kinds=[k for k, _ in off])
    limit_type = entries[-1][1].get('limit_type')
    values = [e['value'] for _, e in entries]
    chosen = dict(entries[-1][1])
    if limit_type in LOOSEST and all(isinstance(v, (int, float)) for v in values):
        best = LOOSEST[limit_type](values)
        chosen = dict(next(e for _, e in entries if e['value'] == best))
    elif limit_type == 'range' and all(isinstance(v, list) for v in values):
        chosen['value'] = [min(v[0] for v in values), max(v[1] for v in values)]
    elif limit_type == 'box_max' and all(isinstance(v, list) for v in values):
        chosen['value'] = [max(v[0] for v in values), max(v[1] for v in values)]
    elif len(entries) > 1:
        chosen['note'] = (chosen.get('note', '') + f' Several kinds change this rule; the last named ({entries[-1][0]}) is used.').strip()
    chosen['from_kinds'] = [k for k, _ in entries]
    return chosen


def resolve_profile(settings, kinds):
    """The composing rules a view is held to, for its kinds of shot (place facts "kind_of_shot"): still_life's rules,
    changed by every other named kind, the loosest version winning. Returns {rule: entry with "from_kinds"}."""
    profiles = settings.node('shot_kind_profiles')
    known = [k for k, v in profiles.items() if isinstance(v, dict) and 'rules' in v]
    kinds = list(kinds) or ['still_life']
    for kind in kinds:
        if kind not in known:
            raise MissingSetting(f'film-settings.json has no shot kind "{kind}" (known kinds: {", ".join(known)}). (file: {settings.path})')
    base = profiles['still_life']['rules']
    resolved = {}
    names = list(base) + [r for k in kinds for r in profiles[k]['rules'] if r not in base]
    for rule_id in dict.fromkeys(names):
        if is_note_key(rule_id):
            continue
        changes = [(k, profiles[k]['rules'][rule_id]) for k in kinds if k != 'still_life' and rule_id in profiles[k]['rules']]
        if changes:
            resolved[rule_id] = loosest_of(changes)
            for k, _ in changes:
                settings.used[f'shot_kind_profiles.{k}.rules.{rule_id}'] = profiles[k]['rules'][rule_id]
        else:
            resolved[rule_id] = dict(base[rule_id], from_kinds=['still_life'])
            settings.used[f'shot_kind_profiles.still_life.rules.{rule_id}'] = base[rule_id]
    return resolved


def judge(rule_entry, measured):
    """Judges a measured number against one resolved rule: 'off' (the kind of shot switches it off), 'pass', 'fail', or
    'not a number rule' (a rule judged another way). measured: a number, or [width, height] for a box rule."""
    if not rule_entry.get('applies', True):
        return 'off'
    limit, kind = rule_entry.get('value'), rule_entry.get('limit_type')
    try:
        if kind == 'max':
            return 'pass' if measured <= limit else 'fail'
        if kind == 'min':
            return 'pass' if measured >= limit else 'fail'
        if kind == 'range':
            return 'pass' if limit[0] <= measured <= limit[1] else 'fail'
        if kind == 'box_max':
            return 'pass' if measured[0] <= limit[0] and measured[1] <= limit[1] else 'fail'
    except TypeError:
        pass
    return 'not a number rule'


def problems_in(data):
    """Plain-words problems with the table: entries without unit, kind or source, or with an unknown kind."""
    found = []
    for key, entry in walk_entries(data):
        for field in ('unit', 'kind', 'source'):
            if field not in entry or entry[field] in (None, ''):
                found.append(f'{key}: no "{field}"')
        if entry.get('kind') not in KINDS:
            found.append(f'{key}: kind "{entry.get("kind")}" is not one of {", ".join(KINDS)}')
    for key, child in data.items():
        if not is_note_key(key) and isinstance(child, dict) and not is_entry(child) and 'about' not in child:
            found.append(f'section "{key}" has no "about" line saying what it holds')
    return found


def main():
    parser = argparse.ArgumentParser(description='Reads and checks film-settings.json, the table of house numbers every '
                                                 'calculator shares (see the note at the top of this file).')
    parser.add_argument('what', choices=['show', 'get', 'check', 'sections', 'profile'],
                        help='show [SECTION], get KEY, check, sections, profile KIND [KIND ...] (the rules a view of those kinds is held to)')
    parser.add_argument('key', nargs='*', help='a section (show), a dotted key (get) or kinds of shot (profile)')
    parser.add_argument('--settings', help='the settings file (default: kit/film-settings.json or FILM_SETTINGS)')
    parser.add_argument('--json', action='store_true', help='print JSON instead of plain lines')
    args = parser.parse_args()
    settings = load_settings(args.settings)
    kinds = args.key
    args.key = args.key[0] if args.key else None
    try:
        if args.what == 'profile':
            resolved = resolve_profile(settings, kinds)
            if args.json:
                print(json.dumps(resolved, indent=1))
            else:
                print(f'Rules for a view of kind {" + ".join(kinds or ["still_life"])}:')
                for rule_id, entry in resolved.items():
                    if entry.get('applies', True):
                        text = f'{describe_value(entry)}'
                    else:
                        text = 'off' + (f' (instead: {entry["replaced_by"]})' if entry.get('replaced_by') else '')
                    print(f'  {rule_id}: {text}  [{entry.get("kind")}, from {", ".join(entry["from_kinds"])}]')
        elif args.what == 'sections':
            names = [k for k in settings.data if not is_note_key(k) and isinstance(settings.data[k], dict)]
            print(json.dumps(names) if args.json else '\n'.join(names))
        elif args.what == 'get':
            if not args.key:
                parser.error('get needs a KEY, for example frame.width_pixels')
            entry = settings.entry(args.key)
            print(json.dumps(entry, indent=1) if args.json else
                  f'{args.key} = {describe_value(entry)}\n  kind: {entry.get("kind")}\n  source: {entry.get("source")}')
        elif args.what == 'show':
            entries = dict(walk_entries(settings.node(args.key), args.key)) if args.key else dict(walk_entries(settings.data))
            if args.json:
                print(json.dumps(entries, indent=1))
            else:
                for key, entry in entries.items():
                    print(f'{key} = {describe_value(entry)}  [{entry.get("kind")}]  {entry.get("source")}')
        elif args.what == 'check':
            found = problems_in(settings.data)
            count = sum(1 for _ in walk_entries(settings.data))
            kinds = {k: sum(1 for _, e in walk_entries(settings.data) if e.get('kind') == k) for k in KINDS}
            print(f'{settings.path}: {count} entries ({", ".join(f"{n} {k}" for k, n in kinds.items())}); '
                  f'{len(found)} problem(s)')
            for line in found:
                print('  ' + line)
            sys.exit(1 if found else 0)
    except MissingSetting as problem:
        raise SystemExit(f'settings: {problem}')


if __name__ == '__main__':
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    from calculator_output import run_main
    sys.exit(run_main(main, 'settings'))
