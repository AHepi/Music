"""What this does: compares two scene fingerprints against OWNERSHIP, so builders working at the same time can be told apart: who changed what they do not own. ownership.json says which
objects, collections and materials belong to which owner, what is frozen (the cameras, lights, world, render settings, the ground) and the contracts between two owners. Given the owner whose
stage just ran (the actor), these are VIOLATIONS: an object or material of another owner changed or removed, a new object with no place_owner, an existing node group changed, frozen state
changed, a name that is not the actor's. The ONE exception is the owner named in ownership.json under frozen.set_by (the ground part, which is built first): it makes the view cameras, the lights,
the world and the render settings, and from then on they are frozen for everyone else (a camera or light it makes needs no place_owner). Without set_by nobody may change them. These are WARNINGS: new ".001" names (a copy made by accident). Without an actor only the actor-free violations are found. Plain Python (no Blender),
so it is tested with made-up fingerprints.
A concrete example: diff(start, end, owners, actor='huts') says "huts changed the object 'road' owned by 'roads_and_ground'" when the road's mesh hash differs.
"""
import json
import re
import sys


def owner_of(name, entry, owners_spec):
    """The owner of an object: its place_owner, else the first owner whose collections, name patterns or materials fit."""
    if entry.get('owner'):
        return entry['owner']
    for owner, spec in (owners_spec.get('owners') or {}).items():
        if any(c in (spec.get('collections') or []) or any(re.search(p, c) for p in spec.get('collections') or []) for c in entry.get('collections', [])):
            return owner
        if any(re.search(p, name) for p in spec.get('objects') or []):
            return owner
        if any(slot and any(slot.startswith(p) for p in spec.get('materials') or []) for slot in entry.get('slots', [])):
            return owner
    return None


def material_owner(name, owners_spec):
    for owner, spec in (owners_spec.get('owners') or {}).items():
        if any(name.startswith(p) for p in spec.get('materials') or []):
            return owner
    return None


def diff(start, end, owners_spec, actor=None):
    """The changes between two fingerprints and what they violate (see the note at the top). Returns a dict with added, changed, deleted (object names), violations, warnings."""
    added = sorted(set(end['objects']) - set(start['objects']))
    deleted = sorted(set(start['objects']) - set(end['objects']))
    changed = sorted(n for n in set(start['objects']) & set(end['objects']) if start['objects'][n] != end['objects'][n])
    violations, warnings = [], []
    frozen_spec = owners_spec.get('frozen') or {}
    setter = bool(actor and frozen_spec.get('set_by') and actor == frozen_spec['set_by'])      # the ground part sets up cameras, lights, world and render settings
    for name in added:
        entry = end['objects'][name]
        if setter and entry.get('type') in ('CAMERA', 'LIGHT'):
            continue
        if not entry.get('owner') and not entry.get('made'):
            violations.append(f'a new object "{name}" has no place_owner (every object a builder makes must say whose it is)')
        elif actor and entry.get('owner') and entry['owner'] != actor and not entry.get('made'):
            violations.append(f'{actor} made the object "{name}" but marked it as {entry["owner"]}\'s')
        if re.search(r'\.\d{3}$', name):
            warnings.append(f'the new object "{name}" has a copy number in its name (a copy made by accident?)')
    for name in changed:
        who = owner_of(name, start['objects'][name], owners_spec)
        if actor and who and who != actor:
            violations.append(f'{actor} changed the object "{name}", which {who} owns')
        elif actor and not who and not start['objects'][name].get('made'):
            violations.append(f'{actor} changed the object "{name}", which nobody owns')
    for name in deleted:
        who = owner_of(name, start['objects'][name], owners_spec)
        if actor and who and who != actor and not start['objects'][name].get('made'):
            violations.append(f'{actor} removed the object "{name}", which {who} owns')
    for name, digest in start['materials'].items():
        if name in end['materials'] and end['materials'][name] != digest:
            who = material_owner(name, owners_spec)
            if actor and who and who != actor:
                violations.append(f'{actor} changed the material "{name}", which {who} owns')
            elif actor and not who:
                violations.append(f'{actor} changed the shared material "{name}" (copy it and change the copy)')
    for name in sorted(set(start['materials']) - set(end['materials'])):
        if actor:
            violations.append(f'{actor} removed the material "{name}"')
    for name, digest in start['node_groups'].items():
        if name in end['node_groups'] and end['node_groups'][name] != digest:
            violations.append(f'the existing node group "{name}" changed (copy it and change the copy)')
    for name in sorted(set(end['materials']) - set(start['materials'])) + sorted(set(end['node_groups']) - set(start['node_groups'])):
        if re.search(r'\.\d{3}$', name):
            warnings.append(f'the new name "{name}" has a copy number')
    for key in ('render', 'cycles', 'view', 'camera', 'world'):
        flag = {'render': 'render', 'cycles': 'render', 'view': 'render', 'camera': 'cameras', 'world': 'world'}[key]
        if frozen_spec.get(flag, True) and not setter and start['frozen'].get(key) != end['frozen'].get(key):
            violations.append(f'the frozen {key} settings changed (only the part named in frozen.set_by of ownership.json may set them up)')
    if frozen_spec.get('lights', True) and not setter and start['frozen'].get('lights') != end['frozen'].get('lights'):
        violations.append('the lights changed (they are frozen; only the part named in frozen.set_by of ownership.json may set them up)')
    return {'added': added, 'changed': changed, 'deleted': deleted, 'violations': violations, 'warnings': warnings, 'actor': actor}


def main_command(parsed):
    """`explainer-film-place ownership-diff --start A.json --end B.json --owners ownership.json [--actor NAME]` (plain Python)."""
    missing = [(flag, value) for flag, value in (('--start', parsed.start), ('--end', parsed.end)) if not value]
    if missing:
        print('explainer-film-place ownership-diff: give --start FINGERPRINT.json and --end FINGERPRINT.json (explainer-film-place fingerprint --out FILE makes one)', file=sys.stderr)
        return 2
    try:
        start, end = json.load(open(parsed.start)), json.load(open(parsed.end))
        owners = json.load(open(parsed.owners)) if parsed.owners else {}
    except (OSError, ValueError) as problem:
        print(f'explainer-film-place ownership-diff: cannot read an input ({problem})', file=sys.stderr)
        return 2
    result = diff(start, end, owners, actor=getattr(parsed, 'actor', None))
    for line in result['violations']:
        print(f'FAIL {line}')
    for line in result['warnings']:
        print(f'LOOK {line}')
    print(f'{"FAIL" if result["violations"] else "PASS"} ownership: {len(result["added"])} added, {len(result["changed"])} changed, {len(result["deleted"])} deleted; {len(result["violations"])} violation(s), {len(result["warnings"])} warning(s)')
    if parsed.out:
        with open(parsed.out, 'w') as handle:
            json.dump(result, handle, indent=1)
    return 1 if result['violations'] else 0
