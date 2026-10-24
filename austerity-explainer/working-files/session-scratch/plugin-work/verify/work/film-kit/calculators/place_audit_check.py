"""What this does: JUDGES a place audit. The audit (place-audit.json, written by `explainer-film-place audit`) holds only
FACTS about a Blender scene (which material has which treatment, which object floats, how big a door is); this tool turns
those facts into pass, look or fail using the house numbers in kit/film-settings.json (the place_* sections). Keeping the
facts and the verdict apart means every threshold is in one table and this tool needs no Blender and no numpy.

A concrete example: a flat hut (three plain-colour boxes) gives an audit in which every material lacks normal_map,
roughness_variation, colour_variation, dirt, grime, weathering, wetness and the rest; this tool prints
    FAIL place: treatments [PK wall.plaster / plaster_lime] missing normal_map, roughness_variation, colour_variation, dirt, ...
and exits 1. After `explainer-film-place finish` the same hut's audit passes (exit 0), with LOOK lines for things a person
should read.

Verbs:
  check AUDIT.json [--blend FILE.blend] [--place-settings FILE] [--facts FILE] [--allow-quick]
        judges the audit (the checks are listed below). --blend makes a changed scene file a failure (a stale audit).
  fresh FRESH_CHECK.json [--audit AUDIT.json]
        judges a fresh checker's result (the shape is in the fresh-checkers guide): a claim that does not hold fails unless it is
        accepted; a missing was_blind or not_tested is a look.
  compare BEFORE.json AFTER.json
        which treatments appeared or vanished per material and per object between two audits.
Checks (each finding is pass, warn (printed LOOK), fail, or known (a treatment switched off on purpose, with its reason)):
  place: quick output, place: stale audit, place: roles, place: treatments, place: layer amounts, place: off reasons,
  place: normal maps, place: uv, place: displacement, place: construction, place: scale, place: plain boxes,
  place: shape damage, place: ground relief, place: keep-out, place: budgets, place: light, place: renderer.
Plain lines start with PASS, LOOK, FAIL or KNOWN. Exit: 0 pass (read the LOOK lines), 1 fail, 2 an input is missing or unusable.
"""
import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish, run_main, read_json, InputProblem  # noqa: E402

KIT_ROOT = os.path.dirname(HERE)
MAX_NAMES = 6                    # names listed in one finding
LAYERS = ('dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'edge_wear', 'moss_and_algae', 'rust', 'rubbish')
OBJECT_LEVEL_TREATMENTS = ('bevelled_edges', 'shape_damage')


def finding(verdict, check, where, text, fix=''):
    return {'verdict': verdict, 'check': check, 'where': where, 'text': text, 'fix': fix}


def names_text(names, limit=MAX_NAMES):
    names = list(names)
    shown = ', '.join(str(n) for n in names[:limit])
    return shown + (f' and {len(names) - limit} more' if len(names) > limit else '')


def sha1_of_file(path):
    digest = hashlib.sha1()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


class Judge:
    """One audit, the house numbers, and the findings so far."""

    def __init__(self, audit, settings, blend=None, allow_quick=False, facts=None, skip_freshness=False):
        self.skip_freshness = skip_freshness
        self.audit = audit
        self.settings = settings
        self.blend = blend
        self.allow_quick = allow_quick
        self.facts = {f['id']: f for f in (facts or [])}
        self.findings = []

    def number(self, key):
        return self.settings.value(key)

    def add(self, verdict, check, where, text, fix=''):
        self.findings.append(finding(verdict, check, where, text, fix))

    def run_all(self):
        for step in (self.quick_output, self.stale, self.roles, self.treatments, self.layer_amounts, self.off_reasons, self.normal_maps, self.uv,
                     self.displacement, self.construction, self.scale, self.plain_boxes, self.shape_damage, self.ground_relief, self.keep_out,
                     self.budgets, self.light, self.renderer):
            step()
        return self.findings

    # ---- the checks
    def quick_output(self):
        audit = self.audit
        if audit.get('quick'):
            if self.allow_quick:
                self.add('warn', 'place: quick output', 'the audit', 'the place was finished with --quick (trial sizes: maps '
                         f'{audit.get("map_size_pixels")} px, masks {audit.get("mask", {}).get("cell_metres")} m); allowed here, but it is not a final.')
            elif not self.number('place_audit.quick_allowed_for_final'):
                self.add('fail', 'place: quick output', 'the audit', 'the place was finished with --quick (trial sizes), which is for trials only: maps '
                         f'{audit.get("map_size_pixels")} px and masks of {audit.get("mask", {}).get("cell_metres")} m.',
                         'finish the place again without --quick (explainer-film-place finish ...), or pass --allow-quick for a trial run.')
        else:
            minimum = self.number('place_surfaces.normal_map_size_min_pixels')
            size = audit.get('map_size_pixels')
            if isinstance(size, (int, float)) and size < minimum:
                self.add('fail', 'place: quick output', 'the audit', f'the normal maps are {size} px a side; a final needs at least {minimum} px.',
                         'finish again with --map-size 1024 or more.')
        if not audit.get('quick'):
            self.add('pass', 'place: quick output', 'the audit', 'not a quick trial')

    def stale(self):
        if self.skip_freshness:
            return            # the caller (the preflight) makes this check itself
        audit = self.audit
        recorded = audit.get('scene_sha1')
        if not self.blend:
            self.add('warn', 'place: stale audit', 'the audit', 'not checked: the scene file was not given (--blend FILE.blend), so a changed scene would not be noticed.',
                     'give --blend with the finished scene file.')
            return
        if not os.path.exists(self.blend):
            raise InputProblem(f'{self.blend} is not there (it should be the scene file the audit was made from). Make the audit again with: explainer-film-place audit --scene {self.blend}')
        if not recorded:
            self.add('fail', 'place: stale audit', self.blend, 'the audit records no scene_sha1, so it cannot be tied to this scene file.',
                     'make the audit again: explainer-film-place audit --scene SCENE.blend (do not edit the audit by hand).')
            return
        now = sha1_of_file(self.blend)
        if now != recorded:
            self.add('fail', 'place: stale audit', self.blend, f'the scene file changed after the audit was made (audit {recorded[:8]}, file {now[:8]}). The audit says nothing about this file.',
                     'run explainer-film-place audit on the saved file again, then this check.')
        else:
            self.add('pass', 'place: stale audit', self.blend, 'the audit was made from this exact scene file')

    def roles(self):
        roles = self.audit.get('roles', {})
        unknown = roles.get('unknown', [])
        allowed = self.number('place_audit.unknown_role_objects_allowed')
        total = max(1, self.audit.get('counts', {}).get('objects_visible', 0) or 1)
        if len(unknown) > allowed:
            self.add('fail', 'place: roles', names_text(unknown), f'{len(unknown)} object(s) have no role, so nothing is known about what they need.',
                     'run explainer-film-place roles; add a role rule to place-settings.json or set the object\'s place_role property (a never rule for helpers).')
        fallback = roles.get('fallback', [])
        if fallback:
            share = len(fallback) / total
            verdict = 'fail' if share > self.number('place_audit.fallback_role_share_fail') else 'warn'
            self.add(verdict, 'place: roles', names_text(fallback),
                     f'{len(fallback)} of {total} object(s) got only a fallback role ({share:.0%}): the kit guessed from their materials.',
                     'give them a real role: a role rule in place-settings.json, or the place_role property.')
        if not unknown and not fallback:
            self.add('pass', 'place: roles', 'every object', f'every visible object has a role ({sum(roles.get("by_role", {}).values())} objects)')

    def treatments(self):
        missing_allowed = self.number('place_audit.required_treatments_missing_allowed')
        bad = 0
        for material in self.audit.get('materials', []):
            if material.get('role', '').startswith('never.'):
                continue
            required, wanted = [], []
            for key, info in material.get('treatments', {}).items():
                if info.get('has'):
                    continue
                if key in material.get('off_with_reason', {}):
                    continue
                if key in OBJECT_LEVEL_TREATMENTS:
                    continue          # judged per object below
                if info.get('required'):
                    required.append(key)
                elif info.get('wanted'):
                    wanted.append(key)
            if len(required) > missing_allowed:
                bad += 1
                self.add('fail', 'place: treatments', material['name'], f'role {material.get("role")}: missing {", ".join(required)}.',
                         'run explainer-film-place finish (or the verb that makes it: surfaces, age, grow, damage); do not lower the requirement.')
            if wanted:
                self.add('warn', 'place: treatments', material['name'], f'role {material.get("role")}: wanted but missing {", ".join(wanted)}.',
                         'worth adding; not required.')
        per_object = {}
        for obj in self.audit.get('objects', []):
            if obj.get('exempt') or str(obj.get('role', '')).startswith('never.'):
                continue
            for key in obj.get('missing', []):
                if key in OBJECT_LEVEL_TREATMENTS:
                    per_object.setdefault(key, []).append(obj['name'])
        for key, objects in per_object.items():
            bad += 1
            fix = {'bevelled_edges': 'run explainer-film-place surfaces (it bevels with hardened normals)', 'shape_damage': 'run explainer-film-place damage'}[key]
            self.add('fail', 'place: treatments', names_text(objects), f'{len(objects)} object(s) lack {key}.', fix)
        scatter_bad = []
        for key in ('plants', 'litter_pieces'):
            for material in self.audit.get('materials', []):
                info = material.get('treatments', {}).get(key)
                if info and info.get('required') and not info.get('has') and key not in material.get('off_with_reason', {}):
                    scatter_bad.append((key, material['name']))
        for key in sorted({k for k, _ in scatter_bad}):
            names = [m for k, m in scatter_bad if k == key]
            bad += 1
            self.add('fail', 'place: treatments', names_text(names), f'no {key.replace("_", " ")} on the ground ({len(names)} ground material(s)).', 'run explainer-film-place grow.')
        if not bad:
            self.add('pass', 'place: treatments', 'every material', 'every required treatment is there')

    def layer_amounts(self):
        look = self.audit.get('look') or 'lived_in'
        state = self.audit.get('state') or 'dry'
        floors = {k: v['value'] for k, v in self.settings.section('place_audit.layer_amount_floor_by_look').items()}
        floor_of = lambda look_id: floors.get(f'place_audit.layer_amount_floor_by_look.{look_id}', 0.25)   # noqa: E731
        silent, tiny = {}, {}
        for obj in self.audit.get('objects', []):
            if obj.get('exempt') or str(obj.get('role', '')).startswith('never.'):
                continue
            offs = set(obj.get('layers_off', []))
            for layer in obj.get('layer_amounts_missing', []):
                if layer in offs:
                    continue
                silent.setdefault((layer, obj.get('role')), []).append(obj['name'])
            for layer, amount in (obj.get('layer_amounts') or {}).items():
                if layer in offs:
                    continue
                if layer == 'wetness' and state == 'dry':
                    continue
                if look == 'kept' and layer in ('moss_and_algae', 'rubbish') and amount == 0:
                    continue
                if amount < floor_of(obj.get('look') or look) - 1e-9:
                    tiny.setdefault((layer, obj.get('role')), []).append((obj['name'], amount))
        by_role_silent, by_role_tiny = {}, {}
        for (layer, role), objects in silent.items():
            by_role_silent.setdefault(role, {})[layer] = objects
        for (layer, role), items in tiny.items():
            by_role_tiny.setdefault(role, {})[layer] = items
        for role, layers in sorted(by_role_silent.items()):
            every = sorted({n for objects in layers.values() for n in objects})
            self.add('fail', 'place: layer amounts', role, f'{len(every)} object(s) ({names_text(every)}) have no pk_<layer>_amount property for {", ".join(sorted(layers))}, so those layers silently read 0 on them.',
                     'run explainer-film-place age (it writes the amounts), or write pk_<layer>_amount on the object.')
        for role, layers in sorted(by_role_tiny.items()):
            parts = []
            for layer, items in sorted(layers.items()):
                amounts = sorted({round(a, 3) for _, a in items})
                parts.append(f'{layer} at {amounts}' + (' (an amount of 0 needs an off entry with a reason)' if 0.0 in amounts else ''))
            every = sorted({n for items in layers.values() for n, _ in items})
            self.add('fail', 'place: layer amounts', role, f'{len(every)} object(s) ({names_text(every)}) carry a layer below its floor for the look "{look}": ' + '; '.join(parts) + '.',
                     'raise the amounts (the look sets them), or add an off entry with a reason in place-settings.json.')
        if not silent and not tiny:
            self.add('pass', 'place: layer amounts', 'every object', 'every layer amount is there and above its floor (state "' + state + '")')

    def off_reasons(self):
        off = self.audit.get('off', {}) or {}
        entries = off.get('entries', [])
        allowed = set(off.get('allowed_ids', []))
        minimum_letters = 15
        for entry in entries:
            layer = entry.get('layer') or entry.get('treatment')
            reason = (entry.get('reason') or '').strip()
            roles = ', '.join(entry.get('roles') or ['all roles'])
            if len(reason) < minimum_letters:
                self.add('fail', 'place: off reasons', f'{layer} off for {roles}', 'switched off with no real reason (a reason of at least 15 letters is needed).',
                         'write why in the off entry of place-settings.json, or turn the treatment on.')
                continue
            if entry.get('reason_id') in allowed:
                self.add('known', 'place: off reasons', f'{layer} off for {roles}', f'KNOWN: {reason} (the place type allows this)')
            else:
                self.add('warn', 'place: off reasons', f'{layer} off for {roles}', f'switched off: {reason}. The reason is not one the place type lists as allowed; a person should read it.',
                         'if it is right, have it accepted (who, date) in the preflight plan.')
        share = off.get('share')
        if isinstance(share, (int, float)) and share > self.number('place_audit.off_share_max'):
            self.add('warn', 'place: off reasons', 'the settings', f'{share:.0%} of the required treatment-and-role pairs are switched off (more than {self.number("place_audit.off_share_max"):.0%}).',
                     'turn some back on: a place that skips most of the pass is not finished.')
        if not entries:
            self.add('pass', 'place: off reasons', 'the settings', 'nothing is switched off')

    def normal_maps(self):
        maps = self.audit.get('normal_maps', {}) or {}
        minimum = self.number('place_surfaces.normal_map_size_min_pixels')
        correlation_min = self.number('place_surfaces.normal_direction_correlation_min')
        blue_min = self.number('place_surfaces.normal_blue_mean_min')
        band = self.number('place_surfaces.normal_red_green_mean_band')
        bad = 0
        quick = bool(self.audit.get('quick'))
        for image in maps.get('images', []):
            name = image.get('name')
            size = image.get('size') or [0, 0]
            problems, looks = [], []
            if image.get('colourspace') and image['colourspace'] != 'Non-Color':
                problems.append(f'colour space {image["colourspace"]} (a normal map must be Non-Color)')
            if not quick and image.get('made_by_kit') and min(size or [0]) < minimum:
                problems.append(f'only {size[0]} x {size[1]} px (at least {minimum})')
            rgb = image.get('mean_rgb')
            if rgb:
                if rgb[2] < blue_min:
                    problems.append(f'mean blue {rgb[2]:.2f} (a flat normal map is about 1; at least {blue_min})')
                if not (band[0] <= rgb[0] <= band[1] and band[0] <= rgb[1] <= band[1]):
                    problems.append(f'mean red {rgb[0]:.2f} / green {rgb[1]:.2f} are not centred ({band[0]} to {band[1]})')
            if image.get('convention') == 'directx':
                problems.append('a DirectX normal map (green points down); use the OpenGL version')
            direction = image.get('direction') or {}
            for axis in ('x', 'y'):
                state = direction.get(axis)
                if isinstance(state, (int, float)):
                    if state < correlation_min:
                        problems.append(f'direction {axis}: correlation {state:+.2f} with its own height (at least {correlation_min:+.2f}): the map points the wrong way')
                elif state == 'fail':
                    problems.append(f'direction {axis} fails')
            if direction and all(direction.get(a) in ('not informative', None) for a in ('x', 'y')) and direction.get('method') not in ('name', 'height'):
                looks.append('direction could not be proved (no slope to read, or no paired height picture)')
            elif not direction:
                (looks if quick else problems).append('direction was not tested')
            if problems:
                bad += 1
                self.add('fail', 'place: normal maps', name, '; '.join(problems), 'make the map again with explainer-film-place surfaces (OpenGL, Non-Color, 1024 px or more), or fix the import (nor_gl file, Non-Color).')
            elif looks:
                self.add('warn', 'place: normal maps', name, '; '.join(looks), 'run explainer-film-place normals-test for the image, or use a nor_gl file.')
        test_light = maps.get('test_light')
        if test_light is None:
            self.add('warn' if quick else 'fail', 'place: normal maps', 'the test light', 'the end-to-end test light (a bump on a plane lit from two sides) was not run.',
                     'run explainer-film-place normals-test (finish does it unless --quick).')
        elif test_light.get('verdict') != 'pass':
            bad += 1
            self.add('fail', 'place: normal maps', 'the test light', f'the test light says the Normal Map set-up reads the wrong way or does nothing: {test_light.get("detail", "")}',
                     'check UV Map -> Mapping -> Image (Non-Color) -> Normal Map (Tangent) -> Principled Normal, and the green channel.')
        for material in self.audit.get('materials', []):
            info = (material.get('treatments', {}).get('normal_map') or {})
            detail = info.get('detail') or {}
            if not info.get('has') or not detail:
                continue
            problems = []
            if detail.get('reaches_normal') is False:
                problems.append('the Normal Map node does not reach the Principled Normal')
            if detail.get('space') and detail['space'] != 'TANGENT':
                problems.append(f'space {detail["space"]} (Tangent is needed so the map follows the surface)')
            if detail.get('uv_map') in (None, '') and detail.get('has_uv_node') is False:
                problems.append('no UV map named in the Normal Map node')
            limit = self.number('place_surfaces.bump_leftover_strength_max')
            if (detail.get('bump_leftover') or 0) > limit:
                problems.append(f'a leftover Bump of strength {detail["bump_leftover"]} not fed by the Normal Map (at most {limit})')
            more = self.number('place_surfaces.normal_maps_per_material_max')
            if (detail.get('images') or 0) > more:
                problems.append(f'{detail["images"]} normal pictures in one material (at most {more})')
            if problems:
                bad += 1
                self.add('fail', 'place: normal maps', material['name'], '; '.join(problems), 'run explainer-film-place surfaces again on this material.')
        if not bad and maps.get('images') is not None:
            self.add('pass', 'place: normal maps', 'every normal map', f'{len(maps.get("images", []))} normal map(s): Non-Color, tangent, wired, pointing the right way')

    def uv(self):
        bad, mirrored = [], []
        limit = self.number('place_surfaces.uv_mirrored_face_share_max')
        for obj in self.audit.get('objects', []):
            if obj.get('exempt') or str(obj.get('role', '')).startswith('never.'):
                continue
            uv = obj.get('uv') or {}
            if obj.get('needs_uv', True) and obj.get('has_normal_map') and not uv.get('has'):
                bad.append(obj['name'])
            elif uv.get('mirrored_share', 0) > limit:
                mirrored.append(obj['name'])
        if bad:
            self.add('fail', 'place: uv', names_text(bad), f'{len(bad)} object(s) under a normal-mapped material have no UV layer, so the map cannot sit on them.', 'run explainer-film-place surfaces (it writes UVs first).')
        if mirrored:
            self.add('warn', 'place: uv', names_text(mirrored), f'{len(mirrored)} object(s) have more than {limit:.0%} mirrored UV faces (the normal map reads the wrong way on them).', 'unwrap them again without mirroring.')
        if not bad and not mirrored:
            self.add('pass', 'place: uv', 'every object', 'every normal-mapped object has UVs, none mirrored beyond the limit')

    def displacement(self):
        data = self.audit.get('displacement') or {}
        problems = []
        for material in self.audit.get('materials', []):
            info = (material.get('treatments', {}).get('displacement') or {})
            if not info.get('required'):
                continue
            if material.get('role', '') and 'displacement' in material.get('off_with_reason', {}):
                continue
            detail = info.get('detail') or {}
            if not info.get('has'):
                problems.append(f'{material["name"]}: no displacement (role {material.get("role")} needs it)')
                continue
            if detail.get('method') not in ('DISPLACEMENT', 'BOTH'):
                problems.append(f'{material["name"]}: the material is on "{detail.get("method")}" (a Displacement node does nothing on Bump Only)')
            if not (detail.get('depth_metres') or 0) > 0:
                problems.append(f'{material["name"]}: depth 0 metres')
            if detail.get('mesh') == 'coarse':
                problems.append(f'{material["name"]}: the mesh is too coarse to show displacement (a flat plane)')
        for name in data.get('too_coarse', []):
            problems.append(f'{name}: coarse mesh under a displacement material')
        if problems:
            self.add('fail', 'place: displacement', names_text(sorted(set(p.split(":")[0] for p in problems))), '; '.join(problems[:MAX_NAMES]),
                     'run explainer-film-place surfaces (it sets the method and grades or subdivides the mesh); roads: explainer-film-place roads.')
        else:
            self.add('pass', 'place: displacement', 'the displacement materials', 'displacement is set where the role needs it, on a mesh that can show it')

    def construction(self):
        floating, hung, short, span, inside_out, coplanar, buried, no_floor, not_carried = [], [], [], [], [], [], [], [], []
        seat = []
        float_mm = self.number('place_construction.float_gap_millimetres_fail')
        for obj in self.audit.get('objects', []):
            c = obj.get('construction')
            if not c or obj.get('exempt') or str(obj.get('role', '')).startswith('never.'):
                continue
            if c.get('floating') or (c.get('gap_mm') or 0) > float_mm and c.get('carried') is False:
                floating.append(obj['name'])
            elif c.get('carried') is False:
                not_carried.append(obj['name'])
            if c.get('hung') and not c.get('hang_allowed'):
                hung.append(obj['name'])
            if (c.get('short_by_mm') or 0) > float_mm:
                short.append(obj['name'])
            max_span = c.get('max_span_m')
            if c.get('span_max_m') and max_span and c['span_max_m'] > max_span + 1e-9:
                span.append(f'{obj["name"]} ({c["span_max_m"]:.2f} m)')
            if c.get('inside_out'):
                inside_out.append(obj['name'])
            if c.get('coplanar_faces'):
                coplanar.append(obj['name'])
            if c.get('buried_light'):
                buried.append(obj['name'])
            gap = c.get('opening_floor_gap_m')
            if gap is not None and gap > self.number('place_construction.doorway_floor_gap_metres_max'):
                no_floor.append(f'{obj["name"]} ({gap:.2f} m)')
            seat_error = c.get('seat_error_m')
            if seat_error is not None and abs(seat_error) > self.number('place_construction.ground_seat_metres_tolerance') and c.get('needs_ground'):
                seat.append(f'{obj["name"]} ({seat_error:+.2f} m)')
        fixes = {
            'floating': 'move it onto a support or add one (a post under the beam, a footing under the post); seat things with seat_on_ground',
            'hung': 'something must carry it from below, or give the role may_hang',
            'short': 'lengthen the post or lower the beam so they meet',
            'span': 'add a support under the long span (no plank spans more than about 1.4 m)',
            'inside_out': 'flip the normals (a negative-volume closed part is inside out)',
            'coplanar': 'move one of two overlapping faces by a millimetre or delete one',
            'buried': 'move the light out of the solid',
            'no_floor': 'add a floor or step behind the doorway',
            'seat': 'seat it again: pk.seat_on_ground(obj), or run explainer-film-place finish (it seats parts again after the ground changes)',
        }
        groups = (('floating', floating, 'floats: nothing carries it (gap over {mm} mm)'), ('hung', hung, 'hangs from above with no carrier below and its role may not hang'),
                  ('short', short, 'stops short of what it should meet'), ('span', span, 'has a free span longer than its role allows'),
                  ('inside_out', inside_out, 'is a closed part turned inside out'), ('coplanar', coplanar, 'has overlapping faces in the same plane (they will flicker)'),
                  ('buried', buried, 'has a light inside a solid'), ('no_floor', no_floor, 'is a doorway or opening with no floor close below its sill'),
                  ('seat', seat, 'is not seated on the ground'))
        any_bad = False
        for key, items, words in groups:
            if items:
                any_bad = True
                self.add('fail', 'place: construction', names_text(items), f'{len(items)} part(s) {words.format(mm=float_mm)}.', fixes[key])
        if not_carried:
            any_bad = True
            self.add('fail', 'place: construction', names_text(not_carried), f'{len(not_carried)} part(s) are not carried from the ground up.', fixes['floating'])
        if not any_bad:
            checked = sum(1 for o in self.audit.get('objects', []) if o.get('construction'))
            self.add('pass', 'place: construction', 'every part', f'{checked} part(s) carried from the ground up; nothing floats; scattered pieces are left out on purpose')

    def effective_fact(self, entry):
        fact = self.facts.get(entry.get('fact'))
        if fact:
            return fact['min'], fact['max'], fact.get('confidence', entry.get('confidence'))
        return entry['min'], entry['max'], entry.get('confidence')

    def scale(self):
        warn_factor = self.number('place_scale.warn_factor')
        fail_factor = self.number('place_scale.fail_factor')
        fails, warns = [], []
        judged = 0
        for obj in self.audit.get('objects', []):
            if obj.get('exempt'):
                continue
            for entry in obj.get('scale') or []:
                if entry.get('value') is None:
                    continue
                judged += 1
                low, high, confidence = self.effective_fact(entry)
                value = entry['value']
                where = f'{obj["name"]}: {entry.get("dimension")}'
                text = f'{where} is {value:.2f} {entry.get("unit", "m")}; {entry.get("fact")} says {low} to {high} ({confidence})'
                if value < low / fail_factor or value > high * fail_factor:
                    (warns if confidence == 'guess' else fails).append(text)
                elif value < low / warn_factor or value > high * warn_factor:
                    warns.append(text)
        if fails:
            self.add('fail', 'place: scale', names_text([t.split(' is ')[0] for t in fails]), '; '.join(fails[:MAX_NAMES]) + '.',
                     'resize it to a believable real-world size (the facts table is data/real_world_facts.json plus the place\'s own facts).')
        if warns:
            self.add('warn', 'place: scale', names_text([t.split(' is ')[0] for t in warns]), '; '.join(warns[:MAX_NAMES]) + '.', 'check the size; a weak or guessed fact may be wrong for this place.')
        if not fails and not warns:
            self.add('pass', 'place: scale', 'every sized object', f'{judged} size(s) fit the real-world facts')

    def plain_boxes(self):
        objects = [o for o in self.audit.get('objects', []) if not o.get('exempt') and not str(o.get('role', '')).startswith('never.') and o.get('geometry')]
        if not objects:
            return
        boxes = [o['name'] for o in objects if o['geometry'].get('plain_box') and not o['geometry'].get('bevel')]
        share = len(boxes) / len(objects)
        limit = self.number('place_audit.plain_box_share_max')
        if share > limit:
            self.add('fail', 'place: plain boxes', names_text(boxes), f'{share:.0%} of the objects are plain sharp-edged boxes (at most {limit:.0%}).',
                     'run explainer-film-place surfaces (bevels) and damage; shape the parts (chamfers, uneven boards).')
        else:
            self.add('pass', 'place: plain boxes', 'the objects', f'{share:.0%} plain boxes (at most {limit:.0%})')

    def shape_damage(self):
        siblings = self.audit.get('siblings') or {}
        minimum = self.number('place_wear.shape_sibling_min_count')
        limit = self.number('place_wear.shape_sibling_copy_share_max')
        bad = []
        for role, info in siblings.items():
            if info.get('count', 0) >= minimum and info.get('copies_share', 0) > limit and not info.get('all_damaged'):
                bad.append(f'{role} ({info["count"]} objects, {info["copies_share"]:.0%} exact copies)')
        if bad:
            self.add('fail', 'place: shape damage', names_text(bad), 'siblings of one role are exact copies: no two parts alike.', 'run explainer-film-place damage (it bends, chips and varies each part).')
        elif siblings:
            self.add('pass', 'place: shape damage', 'siblings', 'no role has most of its objects as exact copies')

    def ground_relief(self):
        roads = self.audit.get('roads') or []
        minimum = self.number('place_wear.ground_relief_metres_min')
        bad = []
        for road in roads:
            if road.get('ground_objects') is not None and not road.get('ground_objects'):
                bad.append(f'{road.get("name")}: no ground object carries the road')
            elif (road.get('relief_m') or 0) < minimum or road.get('ruts_found') is False:
                bad.append(f'{road.get("name")}: relief {road.get("relief_m", 0):.3f} m (at least {minimum} m), ruts found: {road.get("ruts_found")}')
        if bad:
            self.add('fail', 'place: ground relief', names_text(bad), '; '.join(bad[:MAX_NAMES]), 'run explainer-film-place roads (it grades the ground and shapes ruts, banks and hoof prints).')
        elif roads:
            self.add('pass', 'place: ground relief', 'the roads', f'{len(roads)} road(s) have real relief and ruts')

    def keep_out(self):
        bad = []
        for group in (self.audit.get('scatter') or {}).get('groups', []):
            for key, words in (('in_keepout', 'inside a keep-out'), ('in_puddle', 'in a puddle'), ('on_crown', 'on the crown of a lane'),
                               ('on_wheel_track', 'on a wheel track'), ('within_5cm_of_litter', 'within 5 cm of litter')):
                if (group.get(key) or 0) > 0:
                    bad.append(f'{group.get("name")}: {group[key]} {words}')
        if bad:
            self.add('fail', 'place: keep-out', names_text(bad), '; '.join(bad[:MAX_NAMES]) + ' (all must be 0).',
                     'run explainer-film-place grow again (its gates are exact), or move the keep-out shapes in place-settings.json.')
        elif (self.audit.get('scatter') or {}).get('groups'):
            self.add('pass', 'place: keep-out', 'the scattered pieces', 'no plant or litter on a wheel track, a crown, a puddle or a keep-out')

    def budgets(self):
        counts = self.audit.get('counts', {})
        problems = []
        if counts.get('triangles', 0) > self.number('place_audit.triangles_total_max'):
            problems.append(f'{counts["triangles"]:,} triangles (at most {self.number("place_audit.triangles_total_max"):,})')
        per_owner = self.number('place_audit.triangles_per_builder_max')
        for owner, triangles in (counts.get('triangles_by_owner') or {}).items():
            if triangles > per_owner:
                problems.append(f'owner {owner}: {triangles:,} triangles (at most {per_owner:,})')
        if counts.get('scatter_pieces', 0) > self.number('place_audit.scatter_pieces_max'):
            problems.append(f'{counts["scatter_pieces"]:,} scattered pieces (at most {self.number("place_audit.scatter_pieces_max"):,})')
        mask = self.audit.get('mask') or {}
        if mask.get('seconds') and mask['seconds'] > self.number('place_wear.plan_mask_time_budget_seconds'):
            self.add('warn', 'place: budgets', 'the plan masks', f'making the masks took {mask["seconds"]:.0f} s (budget {self.number("place_wear.plan_mask_time_budget_seconds")} s).', 'use a larger cell (--mask-cell-metres) or --quick.')
        if problems:
            self.add('fail', 'place: budgets', 'the scene', '; '.join(problems) + '.', 'thin out the scatter or simplify meshes; a card draws about 1.5 million triangles per builder comfortably.')
        else:
            self.add('pass', 'place: budgets', 'the scene', 'triangles and scattered pieces are within the budgets')

    def light(self):
        light = self.audit.get('light')
        if light is None:
            return
        if not light.get('any_light'):
            self.add('fail', 'place: light', 'the scene', 'the scene has no light (no sun, lamp, emissive surface or lit world): it renders black.', 'run explainer-film-place light.')
        elif light.get('clip_share') is not None and light['clip_share'] > self.number('place_light.clip_share_max'):
            self.add('warn', 'place: light', 'the first picture', f'{light["clip_share"]:.1%} of the picture is clipped to white (more than {self.number("place_light.clip_share_max"):.1%}).', 'lower the sun or the exposure.')
        else:
            self.add('pass', 'place: light', 'the scene', 'the scene has light')

    def renderer(self):
        info = self.audit.get('renderer')
        if not info:
            return
        decision, chosen = info.get('decision'), (info.get('settings_choice') or 'auto').lower()
        if decision == 'CYCLES' and chosen == 'eevee':
            self.add('fail', 'place: renderer', 'the settings', 'lamps, windows or fires are lit here, so the rule is Cycles, but the settings say eevee. Reasons: ' + names_text(info.get('reasons', [])) + '.',
                     'set "renderer": "auto" (or "cycles") in place-settings.json; draw with explainer-film-place render.')
        elif decision == 'EEVEE' and chosen == 'cycles':
            self.add('warn', 'place: renderer', 'the settings', 'nothing is lit, so EEVEE would do; the settings ask for Cycles (slower and dearer).', 'set "renderer": "auto".')
        else:
            self.add('pass', 'place: renderer', 'the scene', f'renderer {decision}: ' + names_text(info.get('reasons', ['nothing is lit'])))


def verdict_of(findings):
    verdicts = {f['verdict'] for f in findings}
    return 'fail' if 'fail' in verdicts else 'warn' if 'warn' in verdicts else 'pass'


def plain_lines(findings, header):
    lines = [header]
    word = {'fail': 'FAIL', 'warn': 'LOOK', 'pass': 'PASS', 'known': 'KNOWN'}
    for f in findings:
        line = f'{word[f["verdict"]]} {f["check"]} [{f["where"]}]: {f["text"]}'
        if f.get('fix') and f['verdict'] in ('fail', 'warn'):
            line += f'  Fix: {f["fix"]}'
        lines.append(line)
    return lines


# ---------------------------------------------------------------- check
def command_check(args, settings):
    audit = read_json(args.audit, 'the place audit', 'explainer-film-place audit --scene SCENE.blend --settings place-settings.json --out place-audit.json (finish writes one too)')
    if not isinstance(audit, dict) or audit.get('audit_version') != 1:
        raise InputProblem(f'{args.audit} is not a place audit (audit_version 1). Make one with: explainer-film-place audit --scene SCENE.blend --out place-audit.json')
    facts = []
    if args.facts:
        data = read_json(args.facts, 'the place\'s own facts file', 'plan/real-world-facts.json (the planner writes it; the format is in data/real_world_facts.json)')
        facts = data.get('facts', data) if isinstance(data, dict) else data
    judge = Judge(audit, settings, blend=args.blend, allow_quick=args.allow_quick, facts=facts, skip_freshness=args.skip_freshness)
    findings = judge.run_all()
    verdict = verdict_of(findings)
    counts = {v: sum(1 for f in findings if f['verdict'] == v) for v in ('fail', 'warn', 'known', 'pass')}
    header = f'Place audit of {audit.get("place", "the place")} ({audit.get("look")}, {audit.get("state")}): {verdict.upper()}. {counts["fail"]} to fix, {counts["warn"]} to look at, {counts["known"]} known (switched off on purpose), {counts["pass"]} passed.'
    lines = plain_lines(findings, header)
    if verdict == 'fail':
        lines.append('The place is not finished: do not draw, render or paint it until these pass.')
    result = {'about': 'The judge of one place audit. Facts are in the audit; the verdict and every threshold are here and in film-settings.json (place_* sections).',
              'verdict': verdict, 'place': audit.get('place'), 'audit_file': os.path.abspath(args.audit), 'checks': findings}
    finish('place_audit_check check', result, lines, settings, args)
    return 1 if verdict == 'fail' else 0


# ---------------------------------------------------------------- fresh
CHECKER_FIELDS = ('mode', 'was_blind', 'art_style_kept', 'lived_in', 'construction_makes_sense', 'claims_checked', 'problems', 'not_tested')


def command_fresh(args, settings):
    data = read_json(args.fresh_check, 'a fresh checker\'s result', 'the place-checker agent (workflow build-a-place, phase Check) returns it; the shape is in the fresh-checkers guide')
    if not isinstance(data, dict):
        raise InputProblem(f'{args.fresh_check} must be one JSON object (a checker\'s result).')
    findings = []
    missing = [k for k in CHECKER_FIELDS if k not in data]
    if 'was_blind' not in data:
        findings.append(finding('warn', 'place: fresh checker', 'was_blind', 'the checker did not say whether it was blind to the feature list.', 'ask it to say so.'))
    if 'not_tested' not in data or data.get('not_tested') in (None,):
        findings.append(finding('warn', 'place: fresh checker', 'not_tested', 'the checker did not say what it did not test.', 'ask it to list what it did not test.'))
    other_missing = [k for k in missing if k not in ('was_blind', 'not_tested')]
    if other_missing:
        findings.append(finding('warn', 'place: fresh checker', 'shape', f'the result lacks {", ".join(other_missing)}.', 'the shape is in the fresh-checkers guide.'))
    for index, claim in enumerate(data.get('claims_checked') or [], start=1):
        text = claim.get('claim', f'claim {index}')
        if claim.get('holds') is False:
            findings.append(finding('fail', 'place: fresh checker', f'claim {index}', f'a claim does not hold: "{text}". Evidence: {claim.get("evidence", "none given")}',
                                    'correct the claim or fix the scene, then check again with a different fresh checker.'))
        elif claim.get('holds') is True and not claim.get('evidence'):
            findings.append(finding('warn', 'place: fresh checker', f'claim {index}', f'"{text}" holds, but the checker gave no evidence.', 'ask for the number or the picture.'))
    for key in ('art_style_kept', 'lived_in', 'construction_makes_sense'):
        value = data.get(key)
        if value == 'no':
            findings.append(finding('fail', 'place: fresh checker', key, f'the checker says {key.replace("_", " ")}: no.', 'see its problems list.'))
        elif value == 'nearly':
            findings.append(finding('warn', 'place: fresh checker', key, f'the checker says {key.replace("_", " ")}: nearly.', 'see its problems list.'))
    for problem in data.get('problems') or []:
        if problem.get('severity') == 'must fix':
            findings.append(finding('fail', 'place: fresh checker', problem.get('where', ''), f'must fix: {problem.get("what")}', problem.get('cheapest_fix', '')))
        elif problem.get('severity') == 'should fix':
            findings.append(finding('warn', 'place: fresh checker', problem.get('where', ''), f'should fix: {problem.get("what")}', problem.get('cheapest_fix', '')))
    if args.audit:
        audit = read_json(args.audit, 'the place audit', 'explainer-film-place audit --scene SCENE.blend --out place-audit.json')
        if data.get('audit_scene_sha1') and audit.get('scene_sha1') and data['audit_scene_sha1'] != audit['scene_sha1']:
            findings.append(finding('fail', 'place: fresh checker', 'the scene', 'the checker looked at a different scene file than the audit describes.', 'check the current file.'))
    if not findings:
        findings.append(finding('pass', 'place: fresh checker', data.get('mode', 'checker'), 'every claim holds, the checker named what it did not test, and found nothing to fix'))
    verdict = verdict_of(findings)
    lines = plain_lines(findings, f'Fresh checker ({data.get("mode", "?")}, blind: {data.get("was_blind", "not said")}): {verdict.upper()}.')
    finish('place_audit_check fresh', {'about': 'The judge of a fresh checker\'s result.', 'verdict': verdict, 'checks': findings}, lines, settings, args)
    return 1 if verdict == 'fail' else 0


# ---------------------------------------------------------------- compare
def treatment_sets(audit):
    result = {}
    for material in audit.get('materials', []):
        result[('material', material['name'])] = {k for k, v in material.get('treatments', {}).items() if v.get('has')}
    for obj in audit.get('objects', []):
        result[('object', obj['name'])] = {k for k in ('uv', 'carried') if (obj.get(k) or {}) and (obj.get(k) if not isinstance(obj.get(k), dict) else obj[k].get('has'))}
        result[('object', obj['name'])] |= {f'layer:{k}' for k, v in (obj.get('layer_amounts') or {}).items() if v}
    return result


def command_compare(args, settings):
    before = read_json(args.before, 'the earlier place audit', 'explainer-film-place audit --out before.json')
    after = read_json(args.after, 'the later place audit', 'explainer-film-place audit --out after.json')
    first, second = treatment_sets(before), treatment_sets(after)
    findings = []
    for key in sorted(set(first) | set(second)):
        kind, name = key
        gained = sorted(second.get(key, set()) - first.get(key, set()))
        lost = sorted(first.get(key, set()) - second.get(key, set()))
        if key not in first:
            findings.append(finding('pass', 'place: compare', name, f'new {kind}: has {", ".join(sorted(second[key])) or "nothing yet"}'))
        elif key not in second:
            findings.append(finding('warn', 'place: compare', name, f'the {kind} is gone'))
        else:
            if gained:
                findings.append(finding('pass', 'place: compare', name, f'gained {", ".join(gained)}'))
            if lost:
                findings.append(finding('fail', 'place: compare', name, f'LOST {", ".join(lost)} (a treatment vanished between the two audits)'))
    if not findings:
        findings.append(finding('pass', 'place: compare', 'both audits', 'no object or material changed its treatments'))
    verdict = verdict_of(findings)
    lines = plain_lines(findings, f'Compared two audits: {verdict.upper()}.')
    finish('place_audit_check compare', {'about': 'What appeared and vanished between two audits.', 'verdict': verdict, 'checks': findings}, lines, settings, args)
    return 1 if verdict == 'fail' else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Judges a place audit (facts from Blender) with the house numbers: pass, look or fail; also judges a fresh checker\'s result and compares two audits. See the note at the top of this file.')
    commands = parser.add_subparsers(dest='command', required=True)
    p = add_output_options(commands.add_parser('check', help='judge an audit'))
    p.add_argument('audit', help='place-audit.json')
    p.add_argument('--blend', help='the scene file the audit was made from (a changed file makes the audit stale)')
    p.add_argument('--place-settings', dest='place_settings', help='the place settings (read for notes; the audit already holds what it needs)')
    p.add_argument('--facts', help='the place\'s own real-world facts (replaces the ranges of facts with the same id)')
    p.add_argument('--allow-quick', dest='allow_quick', action='store_true', help='accept an audit made with --quick (a trial), as a look')
    p.add_argument('--skip-freshness', dest='skip_freshness', action='store_true', help='leave out the stale-audit check (the preflight makes it itself)')
    p = add_output_options(commands.add_parser('fresh', help='judge a fresh checker\'s result'))
    p.add_argument('fresh_check', help='the checker\'s result JSON')
    p.add_argument('--audit', help='the audit it looked at')
    p = add_output_options(commands.add_parser('compare', help='compare two audits'))
    p.add_argument('before')
    p.add_argument('after')
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    return {'check': command_check, 'fresh': command_fresh, 'compare': command_compare}[args.command](args, settings)


if __name__ == '__main__':
    sys.exit(run_main(main, 'place_audit_check'))
