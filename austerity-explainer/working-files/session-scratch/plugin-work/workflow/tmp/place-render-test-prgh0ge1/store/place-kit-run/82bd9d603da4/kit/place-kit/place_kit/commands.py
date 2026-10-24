"""What this does: one small function per verb of `explainer-film-place`, running inside Blender. Each calls the kit's public pieces in the right
order and prints plain lines (PASS, LOOK, FAIL) so a model or a person can read the result. `finish` does the whole pass in the fixed order:
roles, ground regrade and roads (then parts that stood on the old ground are seated again), surfaces, damage as shape, wear (plan masks first), growth,
light, picture size, then save, reopen the saved file and audit it; running it twice gives the same scene. No Blender-only name is imported at the top, so
`--help` and the settings checks work in plain Python.

A concrete example, inside Blender: commands.finish_place(settings, look='neglected', state='damp', save_as='village-finished.blend') returns
{'audit': {...}, 'judged': {'exit': 0, 'lines': [...]}, 'steps': [...]} .
"""
import json
import os
import sys
import time

from . import names, settings_file


class InputMissing(Exception):
    """A needed input is missing or unusable: the verb ends with exit 2 and this plain sentence."""


# ------------------------------------------------------------------ settings
def settings_path_for(parsed):
    if parsed.settings:
        return os.path.abspath(parsed.settings)
    import bpy
    base = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
    return os.path.join(base, 'place-settings.json')


def read_settings(path=None, create_if_missing=False, place=None, place_type=None):
    """Loads the settings file, merged on top of its place type's defaults. A missing file is drafted from the open scene (and written when
    create_if_missing is true), so a plain request without any settings still works: the draft lists what it could not classify."""
    import bpy
    from . import scene_read
    if path and os.path.exists(path):
        loaded = settings_file.load(path)
        data = settings_file.merged(loaded.data)
        owners = data.get('owners')
        if isinstance(owners, str):
            owner_path = owners if os.path.isabs(owners) else os.path.join(os.path.dirname(path), owners)
            data['owners'] = settings_file.read_json(owner_path).get('owners', {})
        problems = settings_file.validate(data)
        if problems:
            raise InputMissing(f'{path} has problems: ' + '; '.join(problems[:6]))
        return settings_file.Settings(data, path)
    scene_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0] if bpy.data.filepath else 'place'
    draft, report = settings_file.draft(scene_read.scene_facts(only_visible=True), place or scene_name, place_type or 'generic')
    data = settings_file.merged(draft)
    if create_if_missing and path:
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(draft, handle, indent=1)
        print(f'LOOK there was no settings file, so one was drafted and written: {path} ({len(report["guessed"])} role(s) guessed from names, {len(report["unknown"])} object(s) unclassified). Edit it, then run again.')
    return settings_file.Settings(data, path if path and os.path.exists(path) else None)


def new_settings(scene=None, place='place', place_type='generic', out_path=None):
    """Drafts a settings dict from the open scene (see settings_file.draft); returns (dict, report) and writes out_path when given."""
    from . import scene_read
    draft, report = settings_file.draft(scene_read.scene_facts(only_visible=True), place, place_type)
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as handle:
            json.dump(draft, handle, indent=1)
    return draft, report


# ------------------------------------------------------------------ roles
def tag_roles(settings, write=True, fallback=False):
    """Gives every visible mesh object one role. write=True stores it as the object's place_role (so it stays); fallback=True gives an object
    nothing matched a guessed role (from its material names, else prop.generic), marks it pk_fallback_role and lists it, so a fallback is never silent.
    Returns {'by_role': {...}, 'unknown': [names], 'fallback': [names], 'by_object': {...}}."""
    from . import roles as roles_module, scene_read
    table = settings_file.roles_table()
    objects = scene_read.mesh_objects(only_visible=True)
    facts = [scene_read.object_facts(o) for o in objects]
    tagged = roles_module.tag_objects(facts, settings.rules_dict(), table)
    unknown, fell_back = [], []
    for obj, fact in zip(objects, facts):
        info = tagged['by_object'][obj.name]
        owner = settings.owner_of(fact)
        if owner and names.OWNER not in obj.keys() and write:
            obj[names.OWNER] = owner
        if info['role'] is None:
            if fallback:
                guess = roles_module.fallback_for_unknown(fact, table)
                obj[names.ROLE] = guess
                obj['pk_fallback_role'] = 1
                tagged['by_role'][guess] = tagged['by_role'].get(guess, 0) + 1
                info['role'] = guess
                info['slot_roles'] = [guess] * max(1, len(fact['materials']))
                fell_back.append(obj.name)
            else:
                unknown.append(obj.name)
            continue
        if write and names.ROLE not in obj.keys():
            obj[names.ROLE] = info['role']
        if obj.get('pk_fallback_role'):
            fell_back.append(obj.name)
    return {'by_role': tagged['by_role'], 'unknown': unknown, 'fallback': sorted(set(fell_back)), 'by_object': tagged['by_object']}


# ------------------------------------------------------------------ the passes (each calls a module and returns a short report)
def give_surfaces(settings, owner=None, map_size=None, quick=False, maps_folder=None):
    from .surfaces import materials
    return materials.give_surfaces(settings, owner=owner, map_size=map_size, quick=quick, maps_folder=maps_folder)


def shape_roads(settings):
    from .surfaces import roads
    return roads.shape_roads(settings)


def damage_objects(settings, owner=None, amount=None):
    from .surfaces import damage
    return damage.damage_objects(settings, owner=owner, amount=amount)


def grow_things(settings, owner=None, density=None):
    from .growth import scatter
    return scatter.grow_things(settings, owner=owner, density=density)


def light_place(settings, sun_only=False):
    from . import light
    return light.light_place(settings, sun_only=sun_only)


# ------------------------------------------------------------------ saving
def save_scene(parsed):
    """Saves to --save-as (never over the input unless --overwrite). Returns the path saved, or None when the verb did not ask to save."""
    import bpy
    source = bpy.data.filepath
    target = parsed.save_as
    if not target and parsed.overwrite:
        target = source
    if not target:
        raise InputMissing('this verb changes the scene, so say where to save it: --save-as OUT.blend (the input scene is never overwritten without --overwrite).')
    target = os.path.abspath(target)
    if source and os.path.samefile(source, target) if os.path.exists(target) and source else False:
        if not parsed.overwrite:
            raise InputMissing(f'--save-as {target} is the input scene itself; give another file name, or add --overwrite if you mean it.')
    os.makedirs(os.path.dirname(target), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=target, compress=True)
    return target


def reopen(path):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)


# ------------------------------------------------------------------ finish
def finish_place(settings, look=None, state=None, quick=False, map_size=None, owner=None, parsed=None, save_as=None, audit=True, maps_folder=None):
    """The whole pass in its fixed order (see the note at the top). Returns {'steps': [...], 'audit': dict or None, 'judged': {...}, 'saved': path}."""
    import bpy
    from . import parts, run_record, scene_read
    from .wear import door, masks
    started = time.time()
    steps = []

    def note(title, report, line=None):
        steps.append({'step': title, 'report': report})
        if line:
            print(line)

    if look:
        settings.data['look'] = look
    if state:
        settings.data['state'] = state
    settings.data.setdefault('look', 'lived_in')
    tagged = tag_roles(settings, write=True, fallback=True)
    note('roles', {'by_role': tagged['by_role'], 'fallback': tagged['fallback']},
         f'PASS roles: {sum(tagged["by_role"].values())} object(s), {len(tagged["by_role"])} role(s)' + (f'; LOOK {len(tagged["fallback"])} object(s) got only a fallback role: {", ".join(tagged["fallback"][:6])}' if tagged['fallback'] else ''))
    parts.refresh_ground()
    road_report = shape_roads(settings)
    note('roads', road_report, f'PASS roads: {road_report.get("summary", "")}')
    moved = parts.reseat_on_ground()
    if moved:
        print(f'PASS parts: {len(moved)} object(s) seated again after the ground changed')
    surface_report = give_surfaces(settings, owner=owner, map_size=map_size, quick=quick, maps_folder=maps_folder)
    note('surfaces', surface_report, f'PASS surfaces: {surface_report.get("summary", "")}')
    damage_report = damage_objects(settings, owner=owner)
    note('damage', damage_report, f'PASS damage: {damage_report.get("summary", "")}')
    plan, plan_record = masks.build_plan_masks(settings, quick=quick, only_owner=owner)
    masks.write_plan_images(plan)
    masks.forget_loaded()
    note('plan masks', plan_record, f'PASS plan masks: {plan_record["cells"][0]} x {plan_record["cells"][1]} cells of {plan_record["cell_metres"]:.2f} m in {plan_record["seconds"]} s ({plan_record["source"]})')
    wear = door.age_place(settings, look=look, state=state, owner=owner)
    note('wear', wear.report(), f'PASS wear: layers {", ".join(wear.report().get("layers_in", []))} in {wear.report().get("materials", 0)} material(s)')
    grow_report = grow_things(settings, owner=owner)
    note('growth', grow_report, f'PASS growth: {grow_report.get("summary", "")}')
    light_report = light_place(settings)
    note('light', light_report, f'PASS light: {light_report.get("summary", "")}')
    picture = settings.picture
    if picture.get('camera') and picture.get('height_pixels'):
        door.set_picture_size(picture['camera'], picture['height_pixels'])
    record = run_record.write(quick=bool(quick), map_size_pixels=surface_report.get('map_size_pixels'), mask=plan_record, masks_from='part_only' if owner else 'whole_scene',
                              look=settings.look_id, state=settings.state, finished=True, picture={'camera': picture.get('camera'), 'height_pixels': picture.get('height_pixels'), 'set': bool(picture.get('camera'))})
    result = {'steps': steps, 'audit': None, 'judged': None, 'saved': None, 'seconds': round(time.time() - started, 1), 'record': record}
    if parsed is not None or save_as:
        if save_as:
            saved = os.path.abspath(save_as)
            os.makedirs(os.path.dirname(saved), exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=saved, compress=True)
        else:
            saved = save_scene(parsed)
        result['saved'] = saved
        print(f'PASS saved: {saved}')
        if audit:
            reopen(saved)
            result.update(run_audit_on_open_file(settings, owner=owner))
    return result


def run_audit_on_open_file(settings, owner=None, out_path=None, run_light_test=True, allow_quick=False, facts_path=None):
    """Audits the file that is open (it must be saved), judges it, prints the judge's lines. Returns {'audit': ..., 'judged': {'exit': n, 'lines': [...]}}."""
    import bpy
    from .checks import scene_audit
    audit_path = out_path or os.path.join(os.path.dirname(bpy.data.filepath), 'place-audit.json')
    audit = scene_audit.audit_place(settings, audit_path, run_light_test=run_light_test, facts_path=facts_path, owner=owner)
    code, text = scene_audit.judge_audit(audit_path, blend=bpy.data.filepath, allow_quick=allow_quick, facts_path=facts_path)
    lines = text.splitlines()
    for line in lines:
        if line.startswith(('PASS', 'LOOK', 'FAIL', 'KNOWN', 'Place audit', 'The place')):
            print(line)
    print(f'PASS audit written: {audit_path}')
    stage = 'explainer-film-preflight place --place-audit ' + audit_path + ' --blend ' + bpy.data.filepath
    print(f'NEXT run: {stage}')
    return {'audit': audit, 'judged': {'exit': code, 'lines': lines}, 'audit_path': audit_path}


def finish_part(settings, owner, quick=True, parsed=None, save_as=None, look=None, state=None):
    """A part builder's version: only that owner's objects get surfaces, damage, wear and growth; the plan masks come from that part alone."""
    return finish_place(settings, look=look, state=state, quick=quick, owner=owner, parsed=parsed, save_as=save_as)


# ------------------------------------------------------------------ the verbs, called by blender_run.py
def print_json_if_asked(parsed, payload):
    if parsed.out:
        os.makedirs(os.path.dirname(os.path.abspath(parsed.out)) or '.', exist_ok=True)
        with open(parsed.out, 'w', encoding='utf-8') as handle:
            json.dump(payload, handle, indent=1, default=_json_default)
    if parsed.json:
        print(json.dumps(payload, indent=1, default=_json_default))


def _json_default(value):
    try:
        import numpy as np
        if isinstance(value, (np.floating, np.integer)):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    except ImportError:
        pass
    if isinstance(value, set):
        return sorted(value)
    return str(value)


def run_verb(parsed):
    """Runs the verb in `parsed` (from cli.build_parser) and returns its exit code (0 pass, 1 fail, 2 input missing)."""
    verb = parsed.verb
    handler = VERB_HANDLERS.get(verb)
    if handler is None:
        raise InputMissing(f'the verb {verb} cannot run inside Blender')
    return handler(parsed)


def verb_new_settings(parsed):
    path = parsed.out or settings_path_for(parsed)
    draft, report = new_settings(place=parsed.place, place_type=parsed.place_type, out_path=path)
    print(f'PASS settings drafted: {path}')
    for name, (role, how) in sorted(report['guessed'].items())[:40]:
        print(f'PASS {name}: {role} ({how})')
    for item in report['unknown']:
        print(f'LOOK {item["name"]}: no role guessed. {item["fix"]}')
    print(f'{len(report["guessed"])} role(s) guessed, {len(report["unknown"])} unclassified, owners: {", ".join(report["owners"]) or "none"}')
    return 0


def verb_roles(parsed):
    settings = read_settings(settings_path_for(parsed), place=None)
    tagged = tag_roles(settings, write=parsed.write)
    for role, count in sorted(tagged['by_role'].items()):
        print(f'PASS {role}: {count} object(s)')
    for name in tagged['unknown']:
        print(f'FAIL {name}: no role. Add a role rule to place-settings.json (for example {{"role": "prop.wood", "match": {{"names": ["^{name}$"]}}}}), or set the object\'s place_role property, or add a never rule if it is a helper.')
    if parsed.write:
        save_scene(parsed)
    print_json_if_asked(parsed, {'by_role': tagged['by_role'], 'unknown': tagged['unknown']})
    return 1 if tagged['unknown'] else 0


def verb_simple_pass(parsed, function, title):
    settings = read_settings(settings_path_for(parsed), create_if_missing=True)
    tag_roles(settings, write=True, fallback=True)
    report = function(settings)
    print(f'PASS {title}: {report.get("summary", "")}')
    saved = save_scene(parsed)
    print(f'PASS saved: {saved}')
    print_json_if_asked(parsed, report)
    return 0


def verb_surfaces(parsed):
    settings = read_settings(settings_path_for(parsed), create_if_missing=True)
    tag_roles(settings, write=True, fallback=True)
    report = give_surfaces(settings, owner=parsed.owner, map_size=parsed.map_size, quick=parsed.quick, maps_folder=parsed.maps_folder)
    print(f'PASS surfaces: {report.get("summary", "")}')
    for line in report.get('looks', []):
        print(f'LOOK {line}')
    print(f'PASS saved: {save_scene(parsed)}')
    print_json_if_asked(parsed, report)
    return 0


def verb_roads(parsed):
    return verb_simple_pass(parsed, shape_roads, 'roads')


def verb_damage(parsed):
    settings = read_settings(settings_path_for(parsed), create_if_missing=True)
    tag_roles(settings, write=True, fallback=True)
    report = damage_objects(settings, owner=parsed.owner, amount=parsed.amount)
    print(f'PASS damage: {report.get("summary", "")}')
    print(f'PASS saved: {save_scene(parsed)}')
    print_json_if_asked(parsed, report)
    return 0


def verb_age(parsed):
    from .wear import door, masks
    settings = read_settings(settings_path_for(parsed), create_if_missing=True)
    tag_roles(settings, write=True, fallback=True)
    plan, record = masks.build_plan_masks(settings, quick=parsed.quick, cell=parsed.mask_cell, only_owner=parsed.owner)
    masks.write_plan_images(plan)
    masks.forget_loaded()
    wear = door.age_place(settings, look=parsed.look, state=parsed.state, owner=parsed.owner, layers=(parsed.layers.split(',') if parsed.layers else None),
                          layers_off=(parsed.layers_off.split(',') if parsed.layers_off else None), master=parsed.master)
    report = wear.report()
    print(f'PASS wear: layers {", ".join(report.get("layers_in", []))} in {report.get("materials", 0)} material(s); plan masks {record["cells"][0]} x {record["cells"][1]} in {record["seconds"]} s')
    print(f'PASS saved: {save_scene(parsed)}')
    print_json_if_asked(parsed, report)
    return 0


def verb_grow(parsed):
    settings = read_settings(settings_path_for(parsed), create_if_missing=True)
    tag_roles(settings, write=True, fallback=True)
    report = grow_things(settings, owner=parsed.owner, density=parsed.density)
    print(f'PASS growth: {report.get("summary", "")}')
    print(f'PASS saved: {save_scene(parsed)}')
    print_json_if_asked(parsed, report)
    return 0


def verb_light(parsed):
    settings = read_settings(settings_path_for(parsed))
    report = light_place(settings, sun_only=parsed.sun_only)
    print(f'PASS light: {report.get("summary", "")}')
    print(f'PASS saved: {save_scene(parsed)}')
    return 0


def verb_finish(parsed):
    settings = read_settings(settings_path_for(parsed), create_if_missing=True)
    result = finish_place(settings, look=parsed.look, state=parsed.state, quick=parsed.quick, map_size=parsed.map_size, parsed=parsed, audit=not parsed.no_audit)
    print_json_if_asked(parsed, {'steps': result['steps'], 'saved': result['saved'], 'judged': result.get('judged')})
    if result.get('judged') is None:
        return 0
    return result['judged']['exit']


def verb_finish_part(parsed):
    if not parsed.owner:
        raise InputMissing('finish-part needs --owner NAME (the part builder\'s name)')
    settings = read_settings(settings_path_for(parsed), create_if_missing=True)
    result = finish_part(settings, parsed.owner, quick=True if not parsed.quick else True, parsed=parsed, look=parsed.look, state=parsed.state)
    print_json_if_asked(parsed, {'steps': result['steps'], 'saved': result['saved'], 'judged': result.get('judged')})
    return result['judged']['exit'] if result.get('judged') else 0


def verb_construction(parsed):
    from .checks import construction
    settings = read_settings(settings_path_for(parsed))
    tag_roles(settings, write=False)
    result = construction.check_construction(settings, owner=parsed.owner, out_path=parsed.out)
    bad = {k: v for k, v in result['objects'].items() if v.get('floating') or v.get('inside_out') or v.get('coplanar_faces') or (v.get('short_by_mm') or 0) > 5 or v.get('buried_light')
           or (v.get('hung') and not v.get('hang_allowed')) or (v.get('opening_floor_gap_m') or 0) > 0.30 or (v.get('max_span_m') and v.get('span_max_m', 0) > v['max_span_m'])}
    for name, fact in sorted(bad.items()):
        reasons = [word for key, word in (('floating', f'floats (gap {fact.get("gap_mm")} mm)'), ('inside_out', 'inside out'), ('coplanar_faces', 'twin faces flicker'),
                                          ('buried_light', 'light inside a solid')) if fact.get(key)]
        if (fact.get('short_by_mm') or 0) > 5:
            reasons.append(f'stops short by {fact["short_by_mm"]} mm')
        if fact.get('hung') and not fact.get('hang_allowed'):
            reasons.append('hangs from above')
        if (fact.get('opening_floor_gap_m') or 0) > 0.30:
            reasons.append(f'no floor under the doorway ({fact["opening_floor_gap_m"]} m)')
        if fact.get('max_span_m') and fact.get('span_max_m', 0) > fact['max_span_m']:
            reasons.append(f'free span {fact["span_max_m"]} m (at most {fact["max_span_m"]} m)')
        print(f'FAIL {name}: ' + '; '.join(reasons))
    summary = result['summary']
    print(f'{"FAIL" if bad else "PASS"} construction: {summary["objects_checked"]} object(s), {summary["parts_checked"]} part(s) checked, {summary["carried"]} carried; {len(bad)} problem object(s); {summary["scatter_exempt"]} scattered piece(s) exempt on purpose')
    print_json_if_asked(parsed, result)
    return 1 if bad else 0


def verb_normals_test(parsed):
    from .checks import normals_test
    facts = normals_test.normal_map_facts(run_light=True, size=parsed.size, samples=parsed.samples)
    failed = False
    for image in facts['images']:
        verdict = image.get('verdict')
        direction = image.get('direction', {})
        text = f'{image["name"]}: {image["size"][0]} x {image["size"][1]}, {image["colourspace"]}, direction {direction}'
        print(('FAIL ' if verdict == 'fail' else 'LOOK ' if verdict == 'not run' else 'PASS ') + text)
        failed = failed or verdict == 'fail'
    light = facts['test_light']
    print(('PASS ' if light['verdict'] == 'pass' else 'FAIL ') + light['line'])
    failed = failed or light['verdict'] != 'pass'
    print_json_if_asked(parsed, facts)
    return 1 if failed else 0


def verb_audit(parsed):
    import bpy
    settings = read_settings(settings_path_for(parsed))
    tag_roles(settings, write=False)
    if parsed.no_judge:
        from .checks import scene_audit
        out = parsed.out or os.path.join(os.path.dirname(bpy.data.filepath), 'place-audit.json')
        scene_audit.audit_place(settings, out, facts_path=parsed.facts, owner=parsed.owner)
        print(f'PASS audit written: {out} (not judged)')
        return 0
    result = run_audit_on_open_file(settings, owner=parsed.owner, out_path=parsed.out, allow_quick=parsed.allow_quick, facts_path=parsed.facts)
    return result['judged']['exit']


def verb_undo(parsed):
    from .undo import undo_finish
    report = undo_finish()
    print(f'PASS undo: {report.get("summary", "")}')
    print(f'PASS saved: {save_scene(parsed)}')
    return 0


def verb_fingerprint(parsed):
    from .checks import fingerprint
    data = fingerprint.fingerprint_scene()
    print(f'PASS fingerprint: {len(data["objects"])} object(s), {len(data["materials"])} material(s), {len(data["collections"])} collection(s)')
    print_json_if_asked(parsed, data)
    return 0


def verb_combine(parsed):
    from .checks import combine
    if not parsed.stages:
        raise InputMissing('combine needs --stages stage_a.py stage_b.py ... (each stage file has apply(options))')
    for path in parsed.stages:
        if not os.path.exists(path):
            raise InputMissing(f'the stage file {path} is not there')
    owners = settings_file.read_json(parsed.owners) if parsed.owners else {}
    try:
        options = json.loads(parsed.options) if parsed.options else {}
    except ValueError as problem:
        raise InputMissing(f'--options must be a JSON object such as \'{{"seed": 3}}\' ({problem})')
    stages = [os.path.abspath(path) for path in parsed.stages]
    try:
        report = combine.combine_both(stages, owners, options) if parsed.order == 'both' else combine.combine_stages(stages, owners, parsed.order, options)
    except ValueError as problem:
        raise InputMissing(str(problem))
    report.pop('_final', None)
    for stage in report['stages']:
        print(('FAIL ' if stage['violations'] else 'PASS ') + f'{stage["name"]}: {stage["added"]} added, {stage["changed"]} changed, {stage["deleted"]} deleted in {stage["seconds"]} s'
              + (f'; {len(stage["violations"])} violation(s)' if stage['violations'] else ''))
        for violation in stage['violations'][:10]:
            print(f'FAIL   {violation}')
    failed = bool(report['violations']) or not report['idempotent'] or report.get('order_independent') is False
    print(f'{"FAIL" if report["violations"] else "PASS"} combine ({report["order"]} order): {len(report["violations"])} violation(s)')
    print(('PASS' if report['idempotent'] else 'FAIL') + ' idempotent: ' + ('running the stages again gives the same scene' if report['idempotent'] else 'running the stages a second time changed the scene: a stage must remove what it made before making it again'))
    if 'order_independent' in report:
        print(('PASS' if report['order_independent'] else 'FAIL') + ' order: ' + ('plain and reverse order give the same scene' if report['order_independent'] else 'plain and reverse order give different scenes: a stage relies on what an earlier stage made'))
    if parsed.save_as or parsed.overwrite:
        print(f'PASS saved: {save_scene(parsed)}')
    print_json_if_asked(parsed, report)
    return 1 if failed else 0


def verb_renderer_for(parsed):
    from .render import renderer_choice
    decision = renderer_choice.renderer_for_scene()
    print(decision['engine'])
    for reason in decision['reasons']:
        print(f'PASS {reason}')
    print_json_if_asked(parsed, decision)
    return 0


def verb_render(parsed):
    from .render import render_job
    return render_job.run_command(parsed)


VERB_HANDLERS = {
    'new-settings': verb_new_settings, 'roles': verb_roles, 'surfaces': verb_surfaces, 'roads': verb_roads, 'damage': verb_damage, 'age': verb_age, 'grow': verb_grow,
    'light': verb_light, 'finish': verb_finish, 'finish-part': verb_finish_part, 'construction': verb_construction, 'normals-test': verb_normals_test, 'audit': verb_audit,
    'undo': verb_undo, 'combine': verb_combine, 'fingerprint': verb_fingerprint, 'renderer-for': verb_renderer_for, 'render': verb_render,
}
